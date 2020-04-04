from rest_framework.views import APIView
from rest_framework.response import Response
from wx_client import serializers
import uuid
from utils import JWTHandler
from wx_api import WxAPIAccess
from teaching_helper import glog
import encryption
from wx_client import models
import model_access as mc

_logger = glog.get_logger(__name__)


class HandleAPIView(APIView):
    """
    自动为类装饰异常捕捉器
    """

    def __init__(self, *args, **kwargs):
        super(HandleAPIView, self).__init__(*args, **kwargs)
        glog.APIViewCatchException(self, logger=_logger).decorate()


class UserRegister(HandleAPIView):
    """class for registering

    :remark:
        * this View can't bind ` authentication_classes`
    """
    authentication_classes = []

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
        user = mc.QueryUserProfileHelper.query_user_by_encrypted_code(encrypted_code)

        # 用户是第一次登陆
        if not user:
            user_info.update({'encrypted_code': encrypted_code, 'u_uuid': u_uuid})
            serializer = serializers.UserProfileSerializer(data=user_info)
            if not serializer.is_valid():
                _logger.error(f"User `{user_info.get('nickName', '')}` failed to login. serializer-data is invalid.")
                return Response({'r': 0, 'errmsg': '注册失败'})

            user = models.UserProfile.objects.create(**serializer.data)
            _logger.info('create user `<UserProfile:{}>` successfully...'.format(user.nickName))

        # 签发JWToken
        payload = JWTHandler.jwt_payload_handler(user)
        token = JWTHandler.jwt_encode_handler(payload)
        return Response({'r': 0, 'data': token})


class UserInfoView(HandleAPIView):
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


class FaceProxy(HandleAPIView):
    """ storage encrypted face-img date which be from WeChat in server
    """

    def get(self, request, **_):
        """获取是否已录入人像数据
        """
        _ = self
        user = request.user
        face_record = mc.QueryFeatureForSignInHelper.query_face_record_by_user(user)
        if not face_record:
            return Response({'r': 1, 'errmsg': '未上传人像数据'})
        return Response({'r': 0, 'errmsg': f'{face_record.face_token}'})

    def post(self, request, **_):
        """新建或更新人像数据
        """
        _ = self
        user = request.user
        serializer = serializers.FeatureForSignInSerializer(data=request.data)
        if not serializer.is_valid():
            _logger.warning(f'face-data for [UserProfile:{user.nickName}]: serializer-data is invalid.')
            return Response({'r': 1, 'errmsg': '人像数据录入失败'})
        face_record = mc.QueryFeatureForSignInHelper.query_face_record_by_user(user)
        face_data_dict = serializer.validated_data
        if face_record:
            serializer.update(face_record, face_data_dict)
        else:
            new_face_record = models.FeatureForSignIn(user=user, **face_data_dict)
            new_face_record.save()
        _logger.info(f'flush the face-data of [UserProfile:{user.nickName}] to db successfully..')
        return Response({'r': 0, 'errmsg': '人脸录入成功', 'face_token': face_data_dict.get('face_token', '')})
