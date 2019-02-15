from django.contrib import admin
from . import models
# Register your models here.

# 注册到admin管理站点中
admin.site.register(models.ContentCategory)
admin.site.register(models.Content)