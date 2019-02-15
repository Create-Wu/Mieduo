from rest_framework import serializers

from goods.models import SKU


class CartSerializer(serializers.Serializer):
    """添加修改购物车序列化器"""
    sku_id = serializers.IntegerField(label='sku_id', min_value=1)
    count = serializers.IntegerField(label='数量', min_value=1)
    selected = serializers.BooleanField(label='是否勾选', default=True)

    def validate(self, value):
        # 检验属性
        try:
            SKU.objects.get(id=value['sku_id'])
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        return value


class CartSKUSerializer(serializers.ModelSerializer):
    """查询购物车"""
    count = serializers.IntegerField(label='商品数量')
    selected = serializers.BooleanField(label='勾选状态')

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'default_image_url', 'count', 'selected']


class CartDeleteSerializer(serializers.Serializer):
    """删除购物车序列化器"""

    sku_id = serializers.IntegerField(label='sku_id',min_value=1)

    def validate(self, value):
        try:
            SKU.objects.get(id = value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')


        return value

class CartSelectedSerializer(serializers.Serializer):
    """全选序列化器"""
    selected = serializers.BooleanField(label='全选')
