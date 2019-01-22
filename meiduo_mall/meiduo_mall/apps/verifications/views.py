import random
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from meiduo_mall.apps.verifications import constants
import logging
# Create your views here.
from meiduo_mall.libs.yuntongxun.sms import CCP
from celery_tasks.sms import tasks as sms_tasks

logger = logging.getLogger('django')  # 创建日志输出对象


class SMSCodeView(APIView):
    """短信验证码
        传入参数：mobile,image_code_id ,text
    """

    def get(self, request, modile):
        # 0.创建连接到redis的数据库对象,     verify_codes ：在配置文件中新建了redis数据库
        redis_conn = get_redis_connection('verify_codes')

        #  1.判断用户在60秒内是否重发短信
        send_flag = redis_conn.get('send_flag_%s' % modile)
        # 2.如果已发送就提前响应，不执行后续代码

        if send_flag:
            return Response({"message": "不可频繁发送短信"}, status=status.HTTP_400_BAD_REQUEST)

        # 3.生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        print(sms_code)
        pl = redis_conn.pipeline()

        # 4.把验证码保存到redis中
        # redis_conn.setex(key,有效时间,value)
        # 4 .1保存短信验证码
        # redis_conn.setex('sms_%s' % modile,constants.SMS_CODE_REDIS_EXPIRES,sms_code )
        # 管道
        pl.setex('sms_%s' % modile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)

        # 4.2保存发送短信验证码标记
        # redis_conn.setex('send_flag_%s' % modile,constants.SEND_SMS_COOE_INTERVAL,1)
        pl.setex('send_flag_%s' % modile, constants.SEND_SMS_COOE_INTERVAL, 1)

        # 执行管道
        pl.execute()
        # 5.使用云通讯发送验证码
        # CCP().send_template_sms(modile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60],1)

        # 用异步发送短信,触发异步任务
        sms_code_expires = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        sms_tasks.send_sms_code.delay(modile, sms_code, sms_code_expires)

        # 6.响应
        return Response({'message': 'ok'})
