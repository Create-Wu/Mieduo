from . import views
from django.conf.urls import url

urlpatterns = [

    # qq登录路由
    url(r'qq/authorization/$',views.OAuthURLView.as_view()),

    url(r'qq/user/$',views.QQAuthUserView.as_view())




]