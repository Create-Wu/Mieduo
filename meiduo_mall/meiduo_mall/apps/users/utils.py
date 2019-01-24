import re

from django.contrib.auth.backends import ModelBackend

from .models import User


def jwt_response_payload_handler(token, user=None, request=None):
    """
    重写jwt登录认证方法的响应体
    :param token:
    :param user:
    :param request:
    :return:
    """

    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }


#多账号登录
def get_user_by_account(account):
    """
    根据账号获取user对象

    :param account:  账号，可以是用户名，也可以是手机号
    :return: user对象或者None
    """

    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            # 账号为手机号
            user = User.objects.get(mobile=account)
        else:
            # 账号为用户名
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None

    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """
    自定义用户名和手机号认证

    """

    #  调用上面的方法，判断输入的username，获取到user对象(通过手机号或用户名动态查询user)
    def authenticate(self, request, username=None, password=None, **kwargs):
        """

       :param request:   本次登录请求对象
       :param username: 用户名/手机号
       :param password: 密码
       :return: 要么返回查到的user/None
        """
        user = get_user_by_account(username)
        if user is not None and user.check_password(password):
            return user
