from _decimal import Decimal

from django.shortcuts import render
# Create your views here.
from django_redis import get_redis_connection
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from goods.models import SKU
from orders.serializer import CommitOrderSerializer, OrderSettlementSerializer


class OrderSettlementView(CreateAPIView):
    """去结算接口"""
    # 指定权限， IsAuthenticated 已认证
    permission_classes = [IsAuthenticated]

    # 指定序列化器
    # serializer_class = CommitOrderSerializer

    def get(self, request):
        """获取购物车商品"""

        user = request.user

        # 从购物车中获取用户勾选要结算的商品信息
        redis_conn = get_redis_connection('cart')
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        cart_selected = redis_conn.smembers('selected_%s' % user.id)

        cart = {}
        for sku_id in cart_selected:
            # 获取redus中的商品id
            cart[int(sku_id)] = int(redis_cart[sku_id])

        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart.keys())

        for sku in skus:
            #  sku为一个对象,计算cart中商品的数量
            sku.count = cart[int(sku_id)]

        # 运费
        freight = Decimal('10.00')

        # 创建序列化器时 给instance参数可以传递(模型/查询集(many=True) /字典)
        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})
        return Response(serializer.data)


class CommitOrderView(CreateAPIView):
    # 提交订单

    # 指定权限

    permission_classes = [IsAuthenticated]


    # 指定序列化器
    serializer_class = CommitOrderSerializer
    print(1111111111111111)
