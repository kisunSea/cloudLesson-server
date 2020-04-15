import uuid
import random
import string
import copy
from urllib.parse import urljoin

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

import encryption
import model_access as mc
from teaching_helper import gdata
from teaching_helper import glog
import utils
from wx_api import WxAPIAccess
from wx_client import models
from wx_client import serializers
from fdfs_storage import fc

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

        # 用户首次登陆
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
            teaching_lessons = self.info_serializer(user.teaching_lessons.order_by('-create_time').all(),
                                                    many=True).data
            listening_lessons = self.info_serializer(user.listening_lessons.order_by('-create_time').all(),
                                                     many=True).data
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
        except (ValueError, AssertionError, Exception) as _:
            _logger.warning('LessonView, failed to create lesson, error:{}'.format(_), exc_info=True)
            return Response({'r': 1, 'errmsg': _})
        else:
            lesson_code.is_occupied = True
            lesson_code.save()
            return Response({'r': 0, 'data': serializer.data})

    def put(self, request, **_):
        """加入班课
        """
        _ = self
        try:
            lesson = models.Lesson.objects.filter(lesson_code=request.data['lesson_code']).first()
            assert lesson.teacher != request.user, '角色类型错误..'
            lesson.student.add(request.user)
        except KeyError or Exception as e:
            _logger.warning('LessonView put error: {}'.format(e))
            return Response({'r': 1, 'data': '', 'errmsg': e}, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            return Response(status=status.HTTP_200_OK)


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

        # todo 班课首页

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
                'track_deactive_list': [  # remark: 学生身份不提供该类目
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


class FileAPIView(APIView):
    """文件上传
    """

    def get(self, request, **_):
        """下载文件
        """

    def post(self, request, **_):
        """上传文件
        """
        _ = self
        is_multiple = request.data.get('mode', False)
        if not is_multiple:  # WeChat client
            f_mem = request.data.get('file')
            f_name = '{}.jpg'.format(uuid.uuid4().hex)
            fn = fc.save(f_name, f_mem)

            ret = {
                'r': 0,
                'data': {
                    'url': fc.url(fn),
                }
            }
            return Response(ret)
        else:  # todo browser client  支持多文件上传
            pass


class SayView(HandleAPIView):
    """课程说说
    """
    serializer = serializers.SayingPOSTSerializer

    def get(self, request, **_):
        """获取课程说说
        * 推荐
        * 分页
        """
        p = utils.Paginator.num_paginator()
        pq = p.paginate_queryset(models.Saying.objects.all(), request, self)
        ser = self.serializer(instance=pq, many=True)
        return Response({'r': 0, 'errmsg': '', 'data': ser.data})

    def post(self, request, **_):
        """发布说说
        """
        saying = {
            'publisher_id': request.data.user.id,
            'content': request.data.get('content', ''),
            'ext_info': request.data.get('ext_info', '{}'),
            'related_files': request.data.get('related_files', '[]')
        }

        ss = self.serializer(data=saying)
        if not ss.is_valid():
            return Response({'r': 1, 'errmsg': '发布失败', 'data': ''})

        ss.save()
        return Response({'r': 0, 'errmsg': '', 'data': '发布成功'})

    def delete(self, request, **_):
        """删除说说
        """
        _ = self
        s_id = request.data.get('sid')
        models.Saying.objects.filter(id=s_id).delete()
        return Response({'r': 0, 'errmsg': '', 'data': '删除成功'})
