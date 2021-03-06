from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import serializers, status, mixins
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_jwt.views import ObtainJSONWebToken

from carts.utils import merge_cart_cookie_to_redis
from goods.models import SKU
from goods.serializer import SKUSerializer
from users import constants
from users.models import User
from users.serializers import CreateUserSerializer, UserDetailSerializer, EmailSerializer, UserAdderssSerialzier, \
    AddressTitleSerializer, AddUserBrowsingHistorySerializer


# Create your views here.



class UserAuthorizeView(ObtainJSONWebToken):
    """
    用户登录，认证(重写账号密码登录视图)
    """
    def post(self, request, *args, **kwargs):
        # 调用父类的方法，获取drf jwt扩展默认的认证用户处理结果
        response = super(UserAuthorizeView,self).post(request, *args, **kwargs)

        # 仿照drf jwt扩展对于用户登录的认证方式，判断用户是否认证登录成功
        # 如果用户登录认证成功，则合并购物车
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            merge_cart_cookie_to_redis(request, user, response)

        return response



# 用户注册
class UserView(CreateAPIView):
    """
      用户注册，调用序列化器
    """
    serializer_class = CreateUserSerializer


# 查看用户名是否存在
class UesrnameCountView(APIView):
    """
    用户名数量

    """

    def get(self, request, username):
        """
        获取指定用户名数量
        :param requsest:
        :param username:
        :return:
        """
        count = User.objects.filter(username=username).count()

        data = {
            "username": username,
            "count": count
        }
        return Response(data, )


# 查看账号是否存在
class Moebile(APIView):
    """
    手机号数量

    """

    def get(self, request, mobile):
        """
        获取指定手机号数量
        :param request:
        :param mobile: 手机号
        :return:
        """
        #  count: 计数
        count = User.objects.filter(mobile=mobile).count()

        data = {
            "mobile": mobile,
            "count": count
        }
        return Response(data, )


# 个人中心用户信息
class UerDetailView(RetrieveAPIView):
    serializer_class = UserDetailSerializer  # 指定序列化器
    permission_classes = [IsAuthenticated]  # DRF中的权限认证 ：已认证（登录）用户可访问

    def get_object(self):
        return self.request.user


# 保存用户邮箱
class EmailView(UpdateAPIView):
    """
    保存用户邮箱
    """

    permission_classes = [IsAuthenticated]
    serializer_class = EmailSerializer

    def get_object(self, *args, **kwargs):
        return self.request.user


# 激活邮箱
class VerifyEmail(APIView):

    def get(self, request):
        #  1. 获取前token 查询参数
        token = request.query.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)

        # 2.解密token获取user
        user = User.check_verify_email_token(token)
        if not user:
            return Response({'message': '无效的token'}, status=status.HTTP_400_BAD_REQUEST)

        # 修改邮箱验证的状态
        user.email_active = True
        user.save()

        return Response({'message': 'ok'})


# 地址
class AddressViewSet(mixins.CreateModelMixin,mixins.UpdateModelMixin, GenericViewSet):
    """用户地址新增与修改"""

    # 指定序列化器
    serializer_class = UserAdderssSerialzier
    # 指定权限
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    # GET/addresses
    def list(self, request, *args, **kwargs):
        """用户列表地址数据"""

        queryset = self.get_queryset()
        serializers= self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,  # 常量
            'addresses': serializers.data

        })

    #   POST /addresses/
    def create(self, request, *args, **kwargs):
        """保存用户地址数据"""

        # 检查地址数量不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存数量超过上限'}, status=status.HTTP_400_BAD_REQUEST)

        # 直接保存新增,返回201
        return super().create(request, *args, **kwargs)

    # delete /addresses/<pk>/
    def destroy(self, request, *args, **kwargs):
        """处理删除"""

        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # put/addresses/pk/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """设置默认地址"""

        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'ok'}, status=status.HTTP_200_OK)

    # put/addresses/pk/title/
    # 需要请求参数
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """修改标题"""

        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class UserBrowsingHistoryView(CreateAPIView):
    """
    用户浏览历史记录
    """
    serializer_class = AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取
        """
        user_id = request.user.id

        redis_conn = get_redis_connection("history")
        history = redis_conn.lrange("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)
        skus = []
        # 为了保持查询出的顺序与用户的浏览历史保存顺序一致
        for sku_id in history:
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)

        s = SKUSerializer(skus, many=True)
        return Response(s.data)