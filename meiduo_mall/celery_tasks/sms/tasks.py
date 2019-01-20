import logging
from celery_tasks.main import celery_app
from meiduo_mall.libs.yuntongxun.sms import CCP


logger = logging.getLogger('django')

SMS_CODE_TEMP_ID = 1


# 装饰器将send_sms_code装饰为异步任务，并设置别名
@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code, expires):
    """    发送短信异步任务
      :param mobile: ⼿手机号
      :param sms_code: 短信验证码
      :return: None
    """
    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile,[sms_code],SMS_CODE_TEMP_ID)
    except Exception as e:
        logger.error("发送验证短信[异常][ mobile: %s, message: %s ]" % (mobile, e))

    else:
        if result ==0:
            logger.info("发送验证码短信[正常][ mobile: %s ]" % mobile)
        else:
            logger.warning("发送验证码短信[失败][ mobile: %s ]" % mobile)