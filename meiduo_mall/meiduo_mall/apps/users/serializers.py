from rest_framework import serializers
import re
from django_redis import get_redis_connection
from rest_framework_jwt.serializers import User
from rest_framework_jwt.serializers import api_settings



class CreateUserSerializer(serializers.ModelSerializer):
    """
    创建序列化器
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
        mobile = User
        fiedls = ['username','mobile','id','email','email_atcive']