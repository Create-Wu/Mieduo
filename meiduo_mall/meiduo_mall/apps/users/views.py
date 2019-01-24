from django.shortcuts import render
from rest_framework import serializers
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from users.serializers import CreateUserSerializer
# Create your views here.



class UserView(CreateAPIView):
    """
      用户注册，调用序列化器
    """
    serializer_class = CreateUserSerializer




# 查看用户名和账号是否存在
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
        return Response(data,)


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
        return Response(data,)

