from rest_framework import serializers

from areas.models import Areas


class AreasSerialzer(serializers.ModelSerializer):
    """省级数据序列化器"""

    class Meta:
        model = Areas # 指定模型
        fields = ('id','name')  # 指定字段


class SubAreasSerialzer(serializers.ModelSerializer):
    """返回市级区级查询数据"""

    # ⼦集样式跟AreaSerializer⼀一样
    subs = AreasSerialzer(many=True,read_only=True)

    class Meta:
        model = Areas
        fields = ('id','name','subs')



