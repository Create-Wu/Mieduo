from rest_framework import serializers
import re
from django_redis import get_redis_connection
from rest_framework_jwt.serializers import User
from rest_framework_jwt.serializers import api_settings
from celery_tasks.email.tasks import send_verify_email
from goods.models import SKU
from users import constants
from users.models import Address


class CreateUserSerializer(serializers.ModelSerializer):
    """
    创建注册序列化器
    """
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='登录状态',read_only=True)



    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'sms_code', 'password2', 'mobile', 'allow','token')
        extra_kwargs = {
            'username': {
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }

            },
            'password': {
                'write_only': True,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }

        }

    #  validate ：校验方法： 下划线后面写字段，说明对单个字段验证
    def validate_mobile(self, mobile):
        """验证手机号码"""

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            raise serializers.ValidationError('手机号格式错误')

        return mobile

    def validate_allow(self, allow):
        """验证协议"""

        if allow != "true":
            raise serializers.ValidationError('未通过协议')

        return allow

    def validate(self, data):

        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码输入不一致')
        # 判断短信验证码

        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)

        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信')

        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validated_date):
        """
        创建用户
        :param validated_date:
        :return:
        """

        # 移除数据库模型中不存在的属性

        del validated_date['password2']
        del validated_date['sms_code']
        del validated_date['allow']
        user = User.objects.create(**validated_date)

        # 调用django的认证系统加密密码
        user.set_password(validated_date['password'])
        user.save()

        # 补充生成记录登录状态的token（固定写法）
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """用户信息序列化器"""

    class Meta:
        model = User
        fields = ['username','mobile','id','email','email_active']


class EmailSerializer(serializers.ModelSerializer):
    """邮箱序列化器"""

    class Meta:
        model = User
        fields = ('id', 'email')
        extra_kwages = {

            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        email = validated_data['email']  # 创建实例对象
        instance.email = email
        instance.save()


        # 生成邮箱激活url
        verify_url = instance.generate_verify_email_url()

        # 在此地发送邮箱
        send_verify_email.delay(email,verify_url)



        return instance


class UserAdderssSerialzier(serializers.ModelSerializer):
    """用户地址序列化器"""

    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID',required=True)
    city_id = serializers.IntegerField(label='市ID',required=True)
    district_id =serializers.IntegerField(label ='区ID',required=True)



    class Meta:
        model = Address
        # exclude： 排除
        exclude =('user','is_deleted','create_time','update_time')

    def validate_mobel(self,value):
        """
        验证手机号
        :param value:
        :return:
        """
        if not re.match(r'^1[3-9]\d{9}$',value):
            raise serializers.ValidationError('手机格式错误')

        return value


    def create(self,validated_data):
        """保存"""

        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)




class  AddressTitleSerializer(serializers.ModelSerializer):
    """地址标题"""

    class Meta:
        model = Address
        fields = ('title')


class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """
    添加用户浏览历史序列化器
    """
    sku_id = serializers.IntegerField(label="商品SKU编号", min_value=1)

    def validate_sku_id(self, value):
        """
        检验sku_id是否存在
        """
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('该商品不存在')
        return value

    def create(self, validated_data):
        """
        保存
        """
        user_id = self.context['request'].user.id
        sku_id = validated_data['sku_id']

        redis_conn = get_redis_connection("history")
        pl = redis_conn.pipeline()

        # 移除已经存在的本商品浏览记录
        pl.lrem("history_%s" % user_id, 0, sku_id)
        # 添加新的浏览记录
        pl.lpush("history_%s" % user_id, sku_id)
        # 只保存最多5条记录
        pl.ltrim("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT-1)

        pl.execute()

        return validated_data