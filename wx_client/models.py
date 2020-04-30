from datetime import datetime
import json

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from teaching_helper import gdata


class UserProfile(AbstractUser):
    """user profile

    this class include user normal information
    """

    # unique identification
    u_uuid = models.UUIDField(max_length=36, null=True)
    gender = models.IntegerField(choices=gdata.GENDER_CHOICES, default=gdata.UNKNOWN)
    nickName = models.CharField(max_length=32, default='')
    country = models.CharField(max_length=32, default='')
    province = models.CharField(max_length=32, null=True, blank=True, default='')
    city = models.CharField(max_length=32, null=True, blank=True, default='')
    tel = models.CharField(max_length=11, default='', null=True)
    register_time = models.DateTimeField(auto_now=True, null=False, blank=False)
    avatarUrl = models.URLField(blank=True, null=True)

    # encrypted field, this field reference openId, secret_key ext.
    encrypted_code = models.CharField(max_length=128, unique=True, blank=False, null=False)

    # email address will be just saved when it verified
    email = models.EmailField(blank=True, null=True, default='')

    # school of the user will saved as '北京大学' (university code instead)
    university = models.CharField(max_length=32, null=True)

    # rss_method just supports email up to now
    rss_method = models.CharField(verbose_name='消息订阅方式', max_length=32, choices=gdata.RSS_CHOICES,
                                  default=gdata.UNBIND_RSS)

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    # @property
    # def username(self):
    #     return self.u_uuid


class FeatureForSignIn(models.Model):
    """this Model class will save data which used in signing
    """

    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    face_token = models.CharField(verbose_name='人脸特征密文', max_length=132, unique=True)
    base64_face = models.TextField(max_length=10000)
    # the mac of BlueTooth is not unique
    blue_tooth_mac = models.CharField(verbose_name='蓝牙Mac地址', max_length=64)
    record_time = models.DateTimeField(verbose_name='记录时间', auto_now_add=True)

    class Meta:
        verbose_name = 'user feature'


class Lesson(models.Model):
    """班课
    """

    cls_img = models.URLField(default=gdata.DEFAULT_LESSON_IMG)
    teacher = models.ForeignKey(UserProfile, related_name='teaching_lessons', on_delete=models.PROTECT)
    lesson_code = models.CharField(max_length=gdata.LESSON_CODE_LENGTH, db_index=True)
    lesson_name = models.CharField(max_length=32, default='')
    lesson_cls = models.CharField(max_length=2, choices=gdata.LESSON_CLS_CHOICE, default=gdata.OTHER_SUBJECT)
    create_time = models.DateTimeField(auto_created=True, default=timezone.now)
    finish_time = models.DateTimeField(default=None, null=True)
    qr_code = models.URLField(verbose_name='班课二维码地址', max_length=128)
    academic_year = models.CharField(default=str(datetime.now().year), max_length=len(str(datetime.now().year)))
    term = models.IntegerField(choices=gdata.TERM_CHOICE, default=gdata.PRE_TERM)
    is_delete = models.BooleanField(default=False)
    student = models.ManyToManyField(UserProfile, related_name='listening_lessons')
    desc = models.TextField(max_length=128, verbose_name='班课描述', default='')

    @property
    def stu_num(self):
        return self.student.count()


class LessonResource(models.Model):
    """教学资源
    """

    resource_type = models.IntegerField(choices=gdata.RESOURCE_TYPES_CHOICES, default=gdata.RESOURCE_TYPE_OTHER)
    remark = models.CharField(max_length=132, null=True, blank=True)
    pub_time = models.DateTimeField(auto_created=True)
    is_delete = models.BooleanField(default=False)
    lesson = models.ForeignKey(Lesson, related_name='lesson_resources', on_delete=models.PROTECT)
    visibility = models.BooleanField(default=False)

    # ext_info 存储规则
    # 文本类型、试卷类型、其他资源类型互斥
    # {
    #     'text': None
    #     'resource_addr': None,
    #     'examination_id': 1  # 试卷id
    # }
    ext_info = models.TextField()


class Examination(models.Model):
    """试卷
    """

    title = models.CharField(max_length=64, null=False, default='')
    lesson = models.ForeignKey(Lesson, related_name='examinations', on_delete=models.PROTECT)
    create_time = models.DateTimeField(auto_created=True)
    is_delete = models.BooleanField(default=False)


class ExamQuestion(models.Model):
    """试卷题目
    """

    examination = models.ForeignKey(Examination, related_name='all_questions', on_delete=models.PROTECT)
    content = models.CharField(max_length=256, null=True)
    related_point = models.CharField(verbose_name='', max_length=64, null=False, default='')
    related_section = models.CharField(max_length=64, null=False, default='')
    difficulty = models.IntegerField(choices=gdata.DIFFICULTY_LEVEL, default=gdata.DIFFICULTY_UNKNOWN)
    score = models.IntegerField(null=True)
    integral = models.IntegerField(null=False, default=0)
    answer = models.CharField(max_length=256, null=True, default='')

    # 附加图片分为两种，题干图片及解析图片，以json格式存储
    # {
    #   'content_images': None or ['http://img1.png', ]
    #   'answer_images': None or ['http://img1.jpg', 'http://img1.jpg']
    # }
    images = models.TextField(max_length=256, null=None)

    # 选项
    # [
    #   [A, '选项内容1'],
    #   [B, '选项内容2'],
    #   [C, '选项内容3'],
    # ]
    questions = models.TextField(default='[]')


class TeachingEventTracker(models.Model):
    """教学事件跟踪
    """

    SIGN_IN_RELATED = {
        'sign_in': None,
        'discuss': None,
        'examination': None,
        'task': None,
        'notice': None,
        'other': None,
    }

    event_type = models.CharField(max_length=16, choices=gdata.TEACHING_TRACK_EVENT_CHOICE, default=gdata.EVENT_OTHER)
    start_time = models.DateTimeField(null=False, verbose_name='事件开始时间')
    end_time = models.DateTimeField(null=True, verbose_name='事件结束时间')
    join_num = models.IntegerField(default=0, verbose_name='参与人数')
    lesson = models.ForeignKey(Lesson, related_name='lesson_events', on_delete=models.PROTECT)

    # sign_in_related的json字符串，且其中六种类型(key)互斥
    ext_info = models.TextField(max_length=128, null=False, default=json.dumps(SIGN_IN_RELATED))

    @property
    def status(self):
        now_time = datetime.now()
        if now_time > self.start_time:
            if (self.end_time and now_time < self.end_time) or (not self.end_time):
                return gdata.EVENT_STATUS_ON_SHELF
            elif now_time >= self.end_time:
                return gdata.EVENT_STATUS_OFF_SHELF
        else:
            return gdata.EVENT_STATUS_TO_SHELF


class EventSignIn(models.Model):
    """签到事件表
    """
    pass


class SignInTable(models.Model):
    """签到表
    """

    lesson = models.ForeignKey(Lesson, related_name='sign_events', on_delete=models.PROTECT)
    success_time = models.DateTimeField(auto_created=True, verbose_name='签到时间')
    user = models.ForeignKey(UserProfile, on_delete=models.PROTECT)
    distance = models.IntegerField(null=True)

    # @property
    # def full_stu_num(self):
    #     return self.lesson.stu_count


class LessonQuestion(models.Model):
    """课堂答疑 - 问题
    """

    lesson = models.ForeignKey(Lesson, related_name='qas', on_delete=models.PROTECT)
    publisher = models.ForeignKey(UserProfile, related_name='qas', on_delete=models.PROTECT)
    content = models.TextField(max_length=256, null=True)

    # json格式存储
    # ['http://image1.png', 'http://image2.png', 'http://image3.png'...]
    related_images = models.TextField(max_length=128, null=True)


class LessonAnswer(models.Model):
    """课堂答疑 - 回答
    """

    lesson_question = models.ForeignKey(LessonQuestion, related_name='lesson_answers', on_delete=models.PROTECT)
    is_correct = models.BooleanField(default=False)
    content = models.CharField(max_length=256, null=True)

    # json格式存储
    # ['http://image1.png', 'http://image2.png', 'http://image3.png'...]
    related_images = models.TextField(max_length=128, null=True)


class LessonCode(models.Model):
    """班课码

    暂时支持10万个班课码，脚本录入
    """
    code = models.CharField(max_length=16, verbose_name='班课随机码', null=False, db_index=True)
    is_occupied = models.BooleanField(null=False, verbose_name='是否被占用', default=False)


class Saying(models.Model):
    """话题说说
    """
    publisher = models.ForeignKey(UserProfile, related_name='sayings', on_delete=models.CASCADE)
    content = models.TextField(verbose_name='话题内容', max_length=1000)

    # json格式存储
    # ['http://image1.png', 'http://image2.png', 'http://image3.png'...]
    related_files = models.TextField(verbose_name='图片')

    # 目前支持地址信息上传
    # {
    #     'address_info': {
    #         'name': "重庆市渝中区人民政府西北(火药局街)",
    #         'address': "重庆市渝中区火药局街15号",
    #         'latitude': 29.55314,
    #         'longitude': 106.5686
    #     }
    # }
    ext_info = models.TextField(verbose_name='扩展信息', default='{}')
    pub_time = models.DateTimeField(verbose_name='发布时间', auto_created=True, default=timezone.now)
    good_num = models.BigIntegerField(default=0, null=False, blank=False)
    favor_num = models.BigIntegerField(default=0, null=False, blank=False)

    @property
    def images(self):
        return json.loads(self.related_files)

    @property
    def address(self):
        return json.loads(self.ext_info)

    @property
    def comments_num(self):
        return self.saying_comments.count()


class SayingComment(models.Model):
    """话题说说的评论
    """
    parent = models.ForeignKey('SayingComment', verbose_name='父级评论', related_name='child_comments', null=True,
                               blank=True, on_delete=models.CASCADE)
    text = models.TextField(max_length=256, verbose_name='评论内容')
    user = models.ForeignKey(UserProfile, related_name='my_comments', on_delete=models.PROTECT)
    Saying = models.ForeignKey(Saying, related_name='saying_comments', on_delete=models.CASCADE)
    root = models.ForeignKey('SayingComment', verbose_name='根评论',
                             related_name='sub_comments', on_delete=models.CASCADE)
    comment_time = models.DateTimeField(auto_created=True)
    is_delete = models.BooleanField(default=False)
