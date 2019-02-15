from django.conf import settings
from django.shortcuts import render
from QQLoginTool.QQtool import OAuthQQ
# Create your views here.
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from carts.utils import merge_cart_cookie_to_redis
from . import serializers
from oauth.models import OAuthQQUser
from oauth.utils import generate_save_user_token

logger = logging.getLogger('django')


class OAuthURLView(APIView):
    """提供QQ登录⻚页⾯面⽹网址"""

    def get(self, request):
        # next表示从哪个⻚页⾯面进⼊入到的登录⻚页⾯面，将来登录成功后，就⾃自动回到那个页面

        next = request.query_params.get('next')
        if not next:
            next = '/'

        # 1.初始化OAuthQQ对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)

        # 2. 获取QQ登录扫码页面，扫码后得到Authorization Code
        login_url = oauth.get_qq_url()
        print(login_url)

        return Response({'login_url': login_url})


class QQAuthUserView(APIView):
    """OAuth2.0用户扫码登录的回调处理理"""

    # # 提取code请求参数
    # # 使⽤用code向QQ服务器器请求access_token
    # # 使⽤用access_token向QQ服务器器请求openid
    # # 使⽤用openid查询该QQ⽤用户是否在美多商城中绑定过⽤用户
    # # 如果openid已绑定美多商城⽤用户，直接⽣生成JWT token，并返回
    # # 如果openid没绑定美多商城⽤用户，创建⽤用户并绑定到openid
    #
    # def get(self, request):
    #
    #     code = request.query_params.get('code')
    #     if not code:
    #         return Response({'message': '没有code'}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
    #                     redirect_uri=settings.QQ_REDIRECT_URI, state=next)
    #
    #     try:
    #         access_token = oauth.get_access_token(code)
    #
    #         openid = oauth.get_open_id(access_token)
    #
    #     except Exception as e:
    #
    #         return Response({'message': 'QQ服务器异常'}, status=status.HTTP_404_NOT_FOUND)
    #
    #     # 使用openid查询该qq用户是否绑定美多商城用户
    #     try:
    #         oauthqquser_model = OAuthQQUser.objects.get(openid=openid)
    #     except OAuthQQUser.DoesNotExist:
    #         # 如果没有，则创建用户响应绑定页面,并绑定openid
    #         access_token_openid = generate_save_user_token(openid)
    #         return Response({'access_token': access_token_openid})
    #     else:
    #         # 如果已绑定则生成jwt token返回进入登录前的页面
    #         jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    #         jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
    #
    #         # 获取oauth_user 关联的user对象
    #         user = oauthqquser_model.user
    #         payload = jwt_payload_handler(user)
    #         token = jwt_encode_handler(payload)
    #
    #         return Response({
    #             'token': token,
    #             'user_id': user.id,
    #             'username': user.username
    #         })
    #
    # def post(self, request):
    #     # 创建序列化对象，进行反序列化
    #
    #     serializer = serializers.QQAuthUserSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     user = serializer.save()
    #
    #     # 手动生成jwt Token
    #     jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 加载生成载荷函数
    #     jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 加载生成token函数
    #     # 获取user对象
    #
    #     payload = jwt_payload_handler(user)  # 生成载荷
    #     token = jwt_encode_handler(payload)  # 根据载荷生成token
    #     return Response({
    #         'token': token,
    #         'username': user.username,
    #         'user_id': user.id
    #     })
    """
       获取QQ用户对应的美多商城用户
    """

    def get(self, request):
        # 1.获取查询参数中的code参数
        code = request.query_params.get('code')
        if not code:
            return Response({'message': '缺少code'}, status=status.HTTP_400_BAD_REQUEST)
        # 1.1 创建qq登录工具对象
        oauthqq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                          client_secret=settings.QQ_CLIENT_SECRET,
                          redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 2.通过code向QQ服务器请求获取access_token
            access_token = oauthqq.get_access_token(code)
            # 3.通过access_token向QQ服务器请求获取openid
            openid = oauthqq.get_open_id(access_token)
        except Exception as error:
            logger.info(error)
            return Response({'message': 'QQ服务器异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            # 4.查询openid是否绑定过美多商城中的用户
            qqauth_model = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果openid没有绑定过美多商城中的用户
            # 把openid进行加密安全处理,再响应给浏览器,让它先帮我们保存一会
            openid_sin = generate_save_user_token(openid)
            return Response({'access_token': openid_sin})

        else:
            # 如果openid已经绑定过美多商城中的用户(生成jwt token直接让它登录成功)
            # 手动生成token

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 加载生成载荷函数
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 加载生成token函数
            # 获取user对象
            user = qqauth_model.user
            payload = jwt_payload_handler(user)  # 生成载荷
            token = jwt_encode_handler(payload)  # 根据载荷生成token

            response = Response({
                'token': token,
                'username': user.username,
                'user_id': user.id
            })
            # 做cookie购物车合并到redis操作
            merge_cart_cookie_to_redis(request, user, response)

            return response