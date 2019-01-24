from django.db import models


class BaseModel(models.Model):
    """ 为模型补充字段"""

    create_time = models.DateTimeField(verbose_name='创建时间',auto_now=True)
    update_time = models.DateTimeField(verbose_name='修改时间',auto_now=True)



    class Meta:
        abstract = True  # 说明是抽象模型类，用于继承使用，数据库迁移时不会创建BaseModel的表


