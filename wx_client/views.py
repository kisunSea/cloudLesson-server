from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as rest_status
from wx_client import serializers
import uuid
from utils import JWTHandler
from wx_api import WxAPIAccess
from teaching_helper import glog
import encryption
from wx_client import models

_logger = glog.get_logger(__name__)


class UserRegister(APIView):
    """class for registering

    :remark:
        * this View can't bind ` authentication_classes`
    """
    authentication_classes = []

    def __init__(self, *args, **kwargs):
        super(UserRegister, self).__init__(*args, **kwargs)
        glog.APIViewCatchException(self, logger=_logger).decorate()

    def post(self, request, **_):

        code = request.data.get('code', '')
        user_info = request.data.get('user_info', '')
        return self.register_logic(code, user_info)

    @staticmethod
    def register_logic(code, user_info: dict):
        """handle the process of registering

        :param code: random code, use it to get session_key and unique open_id
        :param user_info: WeChat UserInfo
        :return: Response
        """

        # get session_key and open_id

        _, openid = WxAPIAccess.auth_keys(code)
        if not openid:
            return Response({'r': 0, 'errmsg': '登录态创建失败'})

        encrypted_code = encryption.sha256(openid)
        u_uuid = uuid.uuid4().hex
        _logger.info('UserRegister -> `encrypted_code`: {}'.format(encrypted_code))
        user = models.UserProfile.objects.filter(encrypted_code=encrypted_code).first()

        # 用户是第一次登陆
        if not user:
            user_info.update({'encrypted_code': encrypted_code, 'u_uuid': u_uuid})
            serializer = serializers.UserProfileSerializer(data=user_info)
            if not serializer.is_valid(True):
                return Response({'r': 0, 'errmsg': '注册失败'})

            user = models.UserProfile.objects.create(**serializer.data)
            _logger.info('create user `<UserProfile:{}>` successfully...'.format(user.nickName))

        # 签发JWToken
        payload = JWTHandler.jwt_payload_handler(user)
        token = JWTHandler.jwt_encode_handler(payload)
        return Response({'r': 0, 'data': token})


class UserInfoView(APIView):
    """User information handler

    # GET     get user information
    # PUT     update user information
    # DELETE  cancel/delete user information
    """

    def get(self, request, *args, **kwargs):
        pass

    def put(self, request, *args, **kwargs):
        pass

    def delete(self, request, *args, **kwargs):
        pass


class FaceProxy(APIView):
    """ storage encrypted face-img date which be from WeChat in server
    """

    def post(self, request, **_):
        raw_data = request.data.get('base64_data', '')
        if not raw_data:
            return Response({'r': 1, 'errmsg': '人像数据效验失败...'})

        print(raw_data)
        return Response({'r': 0, 'errmsg': '人脸录入成功'})