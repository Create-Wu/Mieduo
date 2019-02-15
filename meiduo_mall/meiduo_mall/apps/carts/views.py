import base64
import pickle
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
# Create your views here.
from carts import constants
from carts.serialziers import CartSerializer, CartSKUSerializer, CartDeleteSerializer, CartSelectedSerializer
from django_redis import get_redis_connection

from goods.models import SKU


class CartView(APIView):

    def perform_authentication(self, request):
        """重写perform_authentication方法
            不在进入视图时开始验证，延后验证
        """
        pass

    def post(self, request):
        """添加购物车"""

        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')
        # 创建响应对象
        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        try:
            #  对用户进行验证
            user = request.user
            """用户登录购物车数据存到redis数据库中"""
            # 创建redis数据库对象
            redis_conn = get_redis_connection('cart')
            # 使用管道避免对redis进行多次重复操作
            pl = redis_conn.pipeline()
            # 把数据以哈希类型保存
            pl.hincrby('cart_%d' % user.id, sku_id, count)
            # 判断商品勾选状态，以set无序集合保存
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)
            pl.execute()
        except:
            # 用户未登录状态，保存购物车到cookie中

            # 获取cookie，判断cookie中是否有添加商品
            cart_cookie = request.COOKIES.get('carts')
            if cart_cookie:

                # 把python中的字符串改成字典
                """
                          {
                              “sku_id_1”: {
                                          “selected”:  True,
                                          “count”: 1
                                          },
                              “sku_id_2”: {
                                          “selected”:  True,
                                          “count": 1
                                          }
                          }
                          """
                # 将字符串转成bytes类型字符串
                cart_cookie_base = cart_cookie.encode()

                # 将bytes类型字符串转成bytes类型的ascii码值
                cart_ascii_bytes = base64.b64decode(cart_cookie_base)
                # 将bytes类型的ascii码值转成字典
                cart_dict = pickle.loads(cart_ascii_bytes)
            else:
                cart_dict = {}

            # 如果重复添加同样的商品做增量处理
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 把字典转成字符串
            cart_ascii_bytes = pickle.dumps(cart_dict)
            cart_cookie_base = base64.b64encode(cart_ascii_bytes)
            cart_str = cart_cookie_base.decode()
            #  创建新cookie,设置有效期
            response.set_cookie('carts', cart_str)

        return response

    def get(self, request):
        """查询购物车"""
        try:
            # 如果获取到user说明是已登录用户(操作redis数据库)
            user = request.user
        except:
            user = None

        else:
            redis_conn = get_redis_connection('cart')

            # 获取hash数据 {sku_id16: 1, sku_id2: 2}
            cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)
            # 获取set数据
            selected_ids = redis_conn.smembers('selected_%d' % user.id)

            # 把redis的购物车数据转换成和cookie购物车数据格式一样
            # 定义一个用来转换数据格式的大字典
            cart_dict = {}


            for sku_id_bytes in cart_redis_dict:
                cart_dict[int(sku_id_bytes)] = {
                    'count': int(cart_redis_dict[sku_id_bytes]),
                    'selected': sku_id_bytes in selected_ids
                }

        # 未登录
        if not user:
            # 判断是否有购物车cookie数据
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 将数据转换成字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))


            else:
                cart_dict = {}

        # 无论是否有用户，都要序列化输出
        # 获取购物车中所有商品的sku模型
        skus = SKU.objects.filter(id__in=cart_dict.keys())

        # 遍历skus查询集,给里面的每个sku模型追加两个属性
        for sku in skus:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']
        # 创建序列化器进行序列化操作

        serializer = CartSKUSerializer(skus, many=True)

        return Response(serializer.data)

    def put(self, request):
        """修改购物车"""
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        response = Response(serializer.data)
        try:
            user = request.user

        except:
            user = None
        else:
            # 已登录用户操作redis购物车数据
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 创建redis连接对象 hash 字典: {sku_id_16: 2, sku_id_2: 1}
            # 勾选状态 set集合中 {sku_id_16, sku_id_2}
            # 修改指定sku_id的购买数据 把hash字典中指定sku_id的value覆盖掉
            pl.hset('cart_%d' % user.id, sku_id, count)
            # 修改商品状态
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)
            else:
                pl.srem('selected_%d' % user.id, sku_id)
            pl.execute()

        if not user:
            cart_str =request.COOKIES.get('carts')
            if cart_str:
                # 字符串转字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

                if sku_id in cart_dict: # 判断当前要修改的sku_id在cookie字典中是否存在
                    # 直接覆盖商品的数据及勾选状态
                    cart_dict[sku_id]={
                        'count':count,
                        'selected':selected
                    }
                # 字典转字符串
                cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('carts',cart_str)
        return response
    def delete(self, request):
        """删除购物车"""
        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data('sku_id')

        response = Response(status=status.HTTP_204_NO_CONTENT)
        try:
            user = request.user
        except:
            user = None
        else:
             # 已登录的用户操作redis购物车数据库
             redis_connn = get_redis_connection('cart')
             # 使用管道方法
             pl = redis_connn.pipeline()
             # 把本次要删除的sku_id从hash字典中移除
             pl.hdel('cart_%d'% user.id, sku_id)
             # 把本次要删除的sku_id从set集合中移除
             pl.srem('selected_%d' % user.id,sku_id)
             # 执行管道
             pl.execute()
        if not user:
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 字典变字符串
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

                # 把要删除的sku_id从cart_dict字典中移除
                if sku_id in cart_dict:
                    del cart_dict[sku_id]
                if len(cart_dict.keys()):# if成立给cookie字典中还有商品
                    # 把cart_dict 转换成 cart_str
                    cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                    # 设置cookie
                    response.set_cookie("carts",cart_str)
                else:
                    response.delete_cookie('carts')  # 如果cookie购物车数据已经全部删除,就把cookie移除
        return response


class CartSelectedView(APIView):
    """购物车全选"""

    # 延后认证
    def perform_authentication(self, request):
        pass

    def put(self,request):


        serializer =CartSelectedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data['selected']

        response =Response(serializer.data)

        try:
            user = request.user
        except:
            user = None
        else:
            redis_conn = get_redis_connection('cart')
            # 获取hash字典
            cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)

            if selected:
                # 如果是全选把所有sku_id添加到set集合中
                redis_conn.sadd('selected_%d' % user.id, *cart_redis_dict.keys())
            else:
                # 如果取消全选把所有sku_id从set集合中移除
                redis_conn.srem('selected_%d' % user.id, *cart_redis_dict.keys())

        if not user:
            cart_str = request.COOKIES.get('carts')
            # 把cart_str 转换成cart_dict
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
                # for sku_id, sku_id_dict in cart_dict.items():
                # 遍历cookie字典
                for sku_id in cart_dict:
                    # 取出每个sku_id对应的小字典
                    sku_id_dict = cart_dict[sku_id]
                    # 是全选把selected全部改为True否则改为False
                    sku_id_dict['selected'] = selected

                # 把cart_dict 转换成 cart_str
                cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                # 设置cookie
                response.set_cookie('carts', cart_str)

        return response