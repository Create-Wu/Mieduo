from rest_framework.routers import DefaultRouter

from . import views
from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token

urlpatterns=[


    # 查看用户名和账号是否存在
    url(r'usernames/(?P<username>\w{5,20})/count/$',views.UesrnameCountView.as_view()),
    # 查看账号是否存在
    url(r'mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.Moebile.as_view()),
    #用户注册
    url(r'^users/$',views.UserView.as_view()),
    #  qq登录
    url(r'^authorizations/$',obtain_jwt_token),

    #个人中心信息显示
    url(r'^user/$',views.UerDetailView.as_view()),

    # 保存用户邮箱
    url(r'^email',views.EmailView.as_view()),

    #激活邮箱验证
    url(r'^email/verification/$',views.VerifyEmail.as_view()),

]
#  用户地址路由器
router = DefaultRouter()
router.register(r'addresses',views.AddressViewSet,base_name='addresses')
# 增删改查，设置标题，设置默认地址
urlpatterns += router.urls

