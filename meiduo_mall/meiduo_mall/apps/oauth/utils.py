from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData


def generate_save_user_token(openid):
    """
    使用itsdangerous 对原始的openid进行签名加密

    :param openid: 原始的openid
    :return: 签名后的openid
    """
    # 创建序列化器对象，指定秘钥和过期时间（10分钟）
    serializer = Serializer(settings.SECRET_KEY, 600)
    # 准备原始的openid
    data = {'openid': openid}
    # 对openid进行签名，返回签名之后的bytes类型的字符串
    token = serializer.dumps(data)
    # 解码返回
    return token.decode()


def check_save_user_token(openid):
    """对加密的openid进行解密"""
    # 创建序列化器对象
    serializer = Serializer(settings.SECRET_KEY, 600)
    try:
        # 2 调用loads方法数据进行解密
        data = serializer.loads(openid)
    except BadData:
        return None
    else:
        return data.get('openid')
