from wx_client import models as wx_m
from teaching_helper import glog

_logger = glog.get_logger(__name__)


class QueryFeatureForSignInHelper(object):

    @staticmethod
    def query_face_record_by_user(user):
        """查询指定user的人脸数据
        """
        assert isinstance(user, wx_m.UserProfile), '`user` must be instance of UserProfile.'
        face_record = wx_m.FeatureForSignIn.objects.filter(user=user).first()
        if not face_record:
            _logger.warning('Failed to get the face record of [<UserProfile>: {}]'.format(user.nickName))
        return face_record


class QueryUserProfileHelper(object):

    @staticmethod
    def query_user_by_encrypted_code(encrypted_code):
        assert isinstance(encrypted_code, str)
        user = wx_m.UserProfile.objects.filter(encrypted_code=encrypted_code).first()
        if not user:
            _logger.warning('Failed to get object of UserProfile by encrypted_code:{}'.format(encrypted_code))
        return user


class QuerySayingHelper(object):

    @staticmethod
    def query_all_sayings():
        return wx_m.Saying.objects.all()

    @staticmethod
    def query_all_ordered_sayings():
        return wx_m.Saying.objects.order_by('-pub_time').all()

    @staticmethod
    def query_ordered_sayings_by_user(user):
        assert isinstance(user, wx_m.UserProfile)
        return wx_m.Saying.objects.filter(publisher=user).order_by('-pub_time').all()


class QueryLesson(object):

    @staticmethod
    def query_lesson_by_lesson_code(lesson_code):
        return wx_m.Lesson.objects.filter(lesson_code=lesson_code).first()
