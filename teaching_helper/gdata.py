# coding: utf-8
import threading

"""
提供除内置settings外的全局常量
"""

HTTP_DOMAIN = 'http://134.175.27.71'
DEFAULT_LESSON_IMG = 'http://134.175.27.71/images/lesson_type_computer.jpg'
LESSON_QR_CODE_PATH = r'/home/ubuntu/static_files/images/qrcode'
LOGIN_QR_CODE_PATH = r'/home/ubuntu/static_files/images/loginqr'

# WeChat api for registering

WX_AUTH_API = 'https://api.weixin.qq.com/sns/jscode2session' \
              '?appid={appid}' \
              '&secret={secret}' \
              '&js_code={js_code}' \
              '&grant_type=authorization_code'

# necessary keys when use aip

APP_ID = '18992489'
API_KEY = 'FbnvhKhocQAZ2qjL7z3C3vHF'
SECRET_KEY = '7GG8RO5PmE3GGGAAXjAPCRnDp5x6zM6q'

AIP_KWARGS = {
    'app_id': APP_ID,
    'api_key': API_KEY,
    'secret_key': SECRET_KEY,
}

AIP_CLIENT_ARGS = {
    'image_type': 'BASE64',
    'options': {
        'face_field': "beauty,age,faceshape,expression,gender,glasses",
        'max_face_num': 1,
        'liveness_control': 'HIGN',
    }
}

REST_HTTP_METHODS = (
    'GET',
    'PUT',
    'POST',
    'HEAD',
    'OPTIONS',
    'DELETE',
)

# ---------------------------------------------
# wx_client.models相关

# user genders type
# refer to wx_client.UserProfile

MALE = 0
FEMALE = 1
UNKNOWN = 2

GENDER_CHOICES = (
    (MALE, '男性'),
    (FEMALE, '女性'),
    (UNKNOWN, '未知')
)

# RSS method

RSS_EMAIL = 'email'
UNBIND_RSS = ''

RSS_CHOICES = (
    (RSS_EMAIL, '邮箱'),
    (UNBIND_RSS, '未开启RSS'),
)

# 学科门类

OTHER_SUBJECT = '00'
PHILOSOPHY = '01'
ECONOMICS = '02'
LAW = '03'
PEDAGOGY = '04'
LITERATURE = '05'
HISTORY = '06'
NEO_CONFUCIANISM = '07'
ENGINEERING = '08'
AGRONOMY = '09'
MEDICINE = '10'
MANAGEMENT = '12'
ART = '13'

LESSON_CLS_CHOICE = (
    (PHILOSOPHY, '哲学类'),
    (ECONOMICS, '经济学类'),
    (LAW, '法学类'),
    (PEDAGOGY, '教育学类'),
    (LITERATURE, '文学类'),
    (HISTORY, '历史学类'),
    (NEO_CONFUCIANISM, '理学类'),
    (ENGINEERING, '工学类'),
    (AGRONOMY, '农学类'),
    (MEDICINE, '医学类'),
    (MANAGEMENT, '管理学类'),
    (ART, '艺术学类'),
    (OTHER_SUBJECT, '其他学科类'),
)

PRE_TERM = 1
LAST_TERM = 2

TERM_CHOICE = (
    (PRE_TERM, '第一学期'),
    (LAST_TERM, '第二学期'),
)

LESSON_CODE_LENGTH = 7

RESOURCE_TYPE_IMG = 1
RESOURCE_TYPE_EXAMINATION = 2
RESOURCE_TYPE_DOC = 3
RESOURCE_TYPE_VOICE = 4
RESOURCE_TYPE_VIDEO = 5
RESOURCE_TYPE_OTHER = 6

RESOURCE_TYPES_CHOICES = (
    (RESOURCE_TYPE_IMG, '图片'),
    (RESOURCE_TYPE_EXAMINATION, '试卷'),
    (RESOURCE_TYPE_DOC, '文档'),
    (RESOURCE_TYPE_VOICE, '音频'),
    (RESOURCE_TYPE_VIDEO, '视频'),
    (RESOURCE_TYPE_OTHER, '其他'),
)

DIFFICULTY_UNKNOWN = 0
DIFFICULTY_SIMPLE = 1
DIFFICULTY_MIDDLE = 2
DIFFICULTY_COMPLEX = 3

DIFFICULTY_LEVEL = (
    (DIFFICULTY_UNKNOWN, '未知'),
    (DIFFICULTY_SIMPLE, '简单'),
    (DIFFICULTY_MIDDLE, '中等'),
    (DIFFICULTY_COMPLEX, '困难'),
)


EVENT_SIGN = 'sign_in'
EVENT_DISCUSS = 'discuss'
EVENT_TEST = 'examination'
EVENT_TASK = 'task'
EVENT_NOTICE = 'notice'
EVENT_CALL = 'call'
EVENT_OTHER = 'other'

TEACHING_TRACK_EVENT_CHOICE = (
    (EVENT_SIGN, '签到'),
    (EVENT_DISCUSS, '讨论'),
    (EVENT_CALL, '随机点名'),
    (EVENT_TEST, '课堂测试'),
    (EVENT_TASK, '任务'),
    (EVENT_NOTICE, '通知'),
    (EVENT_OTHER, '其他'),
)

EVENT_STATUS_TO_SHELF = '未开始'
EVENT_STATUS_ON_SHELF = '进行中'
EVENT_STATUS_OFF_SHELF = '已结束'


LESSON_CODE_NUM = 10000
LESSON_CODE_LEN = 7


# ------------缓存区------------------

# 扫码登录缓存
# 元素结构：
# {
#     'uuid': NamedTuple(effective_time=起效时间, is_success=是否成功, user_id=None, qr_path=None)
# }
LOGIN_QR_EXPIRED_SECS = 5 * 60 * 60
LOGIN_QR_CLS_NAME = 'LoginQRItem'
LOGIN_QR_CODE_CACHE = dict()
LOGIN_QR_CODE_CACHE_LOCK = threading.Lock()
