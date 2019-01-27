from rest_framework.routers import DefaultRouter
from . import views



# 路由器
router=DefaultRouter()
router.register(r'^areas',views.AreasViewSet, base_name='areas')
urlpatterns = []
urlpatterns += router.urls