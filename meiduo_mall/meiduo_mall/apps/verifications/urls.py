from . import views
from django.conf.urls import url


urlpatterns =[

    url(r'^sms_codes/(?P<modile>1[3-9]\d{9})/$',views.SMSCodeView.as_view())

]