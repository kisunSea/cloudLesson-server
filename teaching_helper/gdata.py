# coding: utf-8

"""
提供除内置settings外的全局常量
"""

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
