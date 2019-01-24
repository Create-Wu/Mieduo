from django.db import models

# Create your models here.
from meiduo_mall.utils.mobile import BaseModel
from users.models import User


class OAuthQQUser(BaseModel):
    """QQ登录用户数据"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name
