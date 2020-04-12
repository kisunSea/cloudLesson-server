import uuid
import random
import string
import copy
from urllib.parse import urljoin

from rest_framework.response import Response
from rest_framework.views import APIView

import encryption
import model_access as mc
from teaching_helper import gdata
from teaching_helper import glog
import utils
from wx_api import WxAPIAccess
from wx_client import models
from wx_client import serializers

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
    serializer = serializers.UserProfileSerializer

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
        u_uuid = uuid.uuid4()
        user = mc.QueryUserProfileHelper.query_user_by_encrypted_code(encrypted_code)

        # 用户是第一次登陆
        if not user:
            user_info.update({'encrypted_code': encrypted_code, 'u_uuid': u_uuid})
            _logger.debug('user_info:\t{}'.format(user_info))
            serializer = UserRegister.serializer(data=user_info)
            if not serializer.is_valid():
                _logger.error(
                    "User `{}` failed to login. serializer-data is invalid.".format(user_info.get('nickName', '')))
                return Response({'r': 0, 'errmsg': '注册失败'})

            user = models.UserProfile.objects.create(**serializer.data)
            _logger.info('create user `<UserProfile:{}>` successfully...'.format(user.nickName))

        # 签发JWToken
        payload = utils.JWTHandler.jwt_payload_handler(user)
        token = utils.JWTHandler.jwt_encode_handler(payload)
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
        return Response({'r': 0, 'errmsg': face_record.face_token})

    def post(self, request, **_):
        """新建或更新人像数据
        """
        _ = self
        user = request.user
        serializer = serializers.FeatureForSignInSerializer(data=request.data)
        if not serializer.is_valid():
            _logger.warning('face-data for [UserProfile:{}]: serializer-data is invalid.'.format(user.nickName))
            return Response({'r': 1, 'errmsg': '人像数据录入失败'})

        face_record = mc.QueryFeatureForSignInHelper.query_face_record_by_user(user)
        face_data_dict = serializer.validated_data
        if face_record:
            serializer.update(face_record, face_data_dict)
        else:
            new_face_record = models.FeatureForSignIn(user=user, **face_data_dict)
            new_face_record.save()
        _logger.info('flush the face-data of [UserProfile:{}] to db successfully..'.format(user.nickName))
        return Response({'r': 0, 'errmsg': '人脸录入成功', 'face_token': face_data_dict.get('face_token', '')})


class SubjectsClassifiesView(HandleAPIView):
    """课程分类视图
    """

    authentication_classes = []

    def get(self, request, **_):
        """获取所有的课程分类
        """
        _ = self
        _ = request
        ret_data = [dict(code=code, desc=desc) for code, desc in gdata.LESSON_CLS_CHOICE]
        return Response({'r': 0, 'data': ret_data})


class LessonView(HandleAPIView):
    """课程视图
    """

    serializer = serializers.LessonSerializer
    info_serializer = serializers.LessonInfoSerializer

    def get(self, request, **_):
        """获取我创建/我听的的班课集合
        type: create
        type: listen
        """
        try:
            user = request.user
            teaching_lessons = self.info_serializer(user.teaching_lessons.order_by('-create_time'), many=True).data
            listening_lessons = self.info_serializer(user.listening_lessons.order_by('-create_time'), many=True).data
        except Exception as e:
            _logger.warn('failed to get information of lessons, error:{}'.format(e), exc_info=True)
            return Response({'r': 1, 'errmsg': '查询班课失败'})
        else:
            data = {
                'create': teaching_lessons,
                'listen': listening_lessons,
            }
            return Response({'r': 0, 'errmsg': '', 'data': data})

    def post(self, request, **_):
        """创建班课
        """
        try:
            user = request.user
            lesson_code = models.LessonCode.objects.filter(is_occupied=False).first()
            qr_helper = utils.QRCodeHelper.qr_code_helper()
            qr_helper.generate_lesson_qr_code(lesson_code.code)
            assert qr_helper.is_successful
            qr_url = urljoin(gdata.HTTP_DOMAIN + '/images/qrcode/', '{}.png'.format(lesson_code.code))
            raw_data = copy.deepcopy(request.data)

            raw_data['teacher_id'] = user.id
            raw_data['qr_code'] = qr_url
            raw_data['lesson_code'] = lesson_code.code

            serializer = self.serializer(data=raw_data)
            assert serializer.is_valid()
            serializer.save()
        except (ValueError, Exception) as _:
            _logger.warning('LessonView, failed to create lesson, error:{}'.format(_), exc_info=True)
            return Response({'r': 1, 'errmsg': _})
        else:
            lesson_code.is_occupied = True
            lesson_code.save()
            return Response({'r': 0, 'data': serializer.data})


class LessonCodeAPIView(HandleAPIView):
    """班课码视图
    """

    authentication_classes = []

    def get(self, request, **_):
        """生成班课码
        """
        _ = self
        _ = request
        _list = list(string.ascii_uppercase + string.digits)

        for _ in range(gdata.LESSON_CODE_NUM):

            while 1:
                cur_code = ''.join(random.sample(_list, gdata.LESSON_CODE_LEN))
                code_obj = models.LessonCode.objects.filter(code=cur_code).first()
                if not code_obj:
                    new_code_obj = models.LessonCode(code=cur_code)
                    new_code_obj.save()
                    break

        return Response({'r': 0, 'data': '生成班课码数据成功...'})


class LessonIndexPageOverview(HandleAPIView):
    """单个课程首页总览
    """

    def get(self, request, **_):
        """
        :return:
        {
            'lesson_info': {
                ...
            }

            'resource_num': 课堂资源数
            'questions_num': 答疑区问题数(已解决数/总数)
            'notice_num': 通知数量
            'teach_schedulers': {
                'all': [
                    {},
                    {},
                    {}
                ],
                'ing': [
                    {},
                    {},
                    {},
                ]
                'to': [
                    {},
                    {},
                    {},
                ],
                'up': [
                    {},
                    {}
                ]
            }
        }
        """
        _ = self
        _type = request.query_params.get('type', 0)  # 0-教师身份， 1-学生身份
        lesson_code = request.query_params.get('lesson_code', '')
        lesson = models.Lesson.objects.filter(lesson_code=lesson_code).first()
        lesson_info = serializers.LessonInfoSerializer(lesson, many=False).data

        lesson_index_info = {
            'lesson_data': lesson_info,
            'resource_num': 0,
            'stu_num': lesson.stu_num,
            'questions_num': '0/0',
            'notice_num': 0,
            'teach_schedulers': {
                'track_all_list': [
                    {
                        'start_time': '2013-01-23 23:00:23',
                        'end_time': '23:20:23',
                        'detail': '测试一下',
                        'status': 0,  # 0 - 已结束，1 - 进行中，2 - 待开始
                        'code': '899b20c069d846e3b3980989dc3925b5',
                    },
                    {
                        'start_time': '2013-01-23 23:00:23',
                        'end_time': '',
                        'detail': '测试一下',
                        'status': 1,  # 0 - 已结束，1 - 进行中，2 - 待开始
                        'code': '899b20c069d846e3b3980989dc3925b5',
                    },
                    {
                        'start_time': '2013-01-23 23:00:23',
                        'end_time': '23:20:23',
                        'detail': '测试一下',
                        'status': 0,  # 0 - 已结束，1 - 进行中，2 - 待开始
                        'code': '899b20c069d846e3b3980989dc3925b5',
                    },
                    {
                        'start_time': '2013-01-23 23:00:23',
                        'end_time': '23:20:23',
                        'detail': '测试一下',
                        'status': 2,  # 0 - 已结束，1 - 进行中，2 - 待开始
                        'code': '899b20c069d846e3b3980989dc3925b5',
                    },
                    {
                        'start_time': '2013-01-23 23:00:23',
                        'end_time': '23:00:23',
                        'detail': '测试一下',
                        'status': 2,  # 0 - 已结束，1 - 进行中，2 - 待开始
                        'code': '899b20c069d846e3b3980989dc3925b5',
                    },
                ],
                'track_active_list': [
                    {
                        'start_time': '2013-01-23 23:00:23',
                        'end_time': '',
                        'detail': '测试一下',
                        'status': 1,  # 0 - 已结束，1 - 进行中，2 - 待开始
                        'code': '899b20c069d846e3b3980989dc3925b5',
                    },
                ],
                'track_deactive_list': [    # remark: 学生身份不提供该类目
                    {
                        'start_time': '2013-01-23 23:00:23',
                        'end_time': '23:20:23',
                        'detail': '测试一下',
                        'status': 2,  # 0 - 已结束，1 - 进行中，2 - 待开始
                        'code': '899b20c069d846e3b3980989dc3925b5',
                    },
                    {
                        'start_time': '2013-01-23 23:00:23',
                        'end_time': '23:00:23',
                        'detail': '测试一下',
                        'status': 2,  # 0 - 已结束，1 - 进行中，2 - 待开始
                        'code': '899b20c069d846e3b3980989dc3925b5',
                    },
                ],
                'track_toactive_list': [
                    {
                        'start_time': '2013-01-23 23:00:23',
                        'end_time': '23:20:23',
                        'detail': '测试一下',
                        'status': 0,  # 0 - 已结束，1 - 进行中，2 - 待开始
                        'code': '899b20c069d846e3b3980989dc3925b5',
                    },
                    {
                        'start_time': '2013-01-23 23:00:23',
                        'end_time': '23:20:23',
                        'detail': '测试一下',
                        'status': 0,  # 0 - 已结束，1 - 进行中，2 - 待开始
                        'code': '899b20c069d846e3b3980989dc3925b5',
                    },
                ]
            }
        }

        return Response({'r': 0, 'data': lesson_index_info, 'errmg': ''})
