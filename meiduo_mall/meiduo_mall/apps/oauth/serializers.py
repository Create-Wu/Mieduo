from django_redis import get_redis_connection
from rest_framework import serializers

from oauth.models import OAuthQQUser
from oauth.utils import check_save_user_token
from users.models import User


class QQAuthUserSerializer(serializers.Serializer):
    """QQ登录创建用户序列化器"""

    access_token = serializers.CharField(label='操作认证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    def validate(self, data):
        # 检验access_token
        access_token = data['access_token']
        # 获取身份凭证
        openid = check_save_user_token(access_token)  # 取出解密的openid
        if not openid:
            raise serializers.ValidationError('openid无效')
        # 把解密后的openid保存到反序列化的大字典中以备后期绑定用户使用
        data['access_token'] = openid

        # 验证短信验证码是否争取
        redis_conn = get_redis_connection('verify_codes')
        # 获取当前手机号
        mobile = data['mobile']

        real_sms_code = redis_conn.get('sms_%s' % mobile)
        # 获取前段传来的验证码
        sms_code = data['sms_code']
        if real_sms_code.decode() != sms_code:  # 从redis中取出来的是bytes类型
            raise serializers.ValidationError('验证码不正确')

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果出现异常说明是新用户
            pass
        else:
            # 表示次手机号是已注册过的用户
            if not user.check_password(data.get('password')):
                raise serializers.ValidationError('已存在用户，但密码不正确')
            else:
                data['user'] = user
        return data

    def create(self, validated_data):
        """创建用户"""
        # 获取检验用户
        user = validated_data.get('user')

        if not user:
            user = User.objects.create_user(
                username=validated_data['mobile'],
                password=validated_data['password'],
                mobile=validated_data['mobile'],
            )

        # 将User和openid绑定  ! 注意缩进！！！！
        OAuthQQUser.objects.create(
            user=user,
            openid=validated_data.get('access_token')
        )
        return user
