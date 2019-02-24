from rest_framework.views import APIView
import  random

class ImageCode(APIView):
    """生成图片验证码"""

    def post(self,request):
        # 获取前端的uuid

        image_id = request.ages.get('uuid')


        #生成验证码文字
        code = random.randint(1,9999)
        # name,text,image =