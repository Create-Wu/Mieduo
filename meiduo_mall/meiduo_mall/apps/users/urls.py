from . import views
from django.conf.urls import url


urlpatterns=[

    url(r'usernames/(?P<username>\w{5,20})/count/$',views.UesrnameCountView.as_view()),


    url(r'mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.Moebile.as_view()),

    url(r'^users/$',views.UserView.as_view())


]