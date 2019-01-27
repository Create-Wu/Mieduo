from django.shortcuts import render
from rest_framework_extensions.cache.mixins import CacheResponseMixin
# Create your views here.
from rest_framework.viewsets import ReadOnlyModelViewSet

from areas.models import Areas
from . import serialzers


class AreasViewSet(ReadOnlyModelViewSet):
    """省市区视图集：提供单个对象和列表数据"""

    # 区域信息不分页
    pagination_class = None

    # 指定省级数据和子集数据序列化器
    def get_serializer_class(self):

        if self.action == 'list':
           return serialzers.AreasSerialzer
        else:
            return serialzers.SubAreasSerialzer



    # 指定查询集： 数据来源
    def get_queryset(self):
        """根据action选择返回的查询集"""
        if self.action == 'list':
            return Areas.objects.filter(parent=None)  # 返回省级数据 无父级：parent=None
        else:
            return Areas.objects.all()


