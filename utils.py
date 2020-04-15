import datetime
import threading

import jwt
from django.conf import settings
from MyQR import myqr
from rest_framework.pagination import PageNumberPagination

from teaching_helper import glog
from teaching_helper import gdata

_logger = glog.get_logger(__name__)


# functions


def jwt_get_secret_key(_):
    return settings.SECRET_KEY


# classes


class JWTHandler(object):

    @staticmethod
    def jwt_encode_handler(token):
        key = jwt_get_secret_key(token)
        return jwt.encode(
            token,
            key,
            'HS256'
        ).decode('utf-8')

    @staticmethod
    def jwt_decode_handler(token):
        options = {
            'verify_exp': True,
        }
        # get user from token, BEFORE verification, to get user secret key
        unverified_payload = jwt.decode(token, None, False)
        secret_key = jwt_get_secret_key(unverified_payload)
        return jwt.decode(
            token,
            secret_key,
            True,
            options=options,
            leeway=0,
            audience=None,
            issuer=None,
            algorithms=['HS256', ]
        )

    @staticmethod
    def jwt_get_username_from_payload_handler(payload):
        """
        Override this function if username is formatted differently in payload
        """
        return payload.get('nickname')

    @staticmethod
    def jwt_payload_handler(user):
        payload = {
            'user_id': user.id,
            'nickname': user.nickName,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }

        return payload


class QRCodeHelper(object):
    """生成二维码
    """

    lock = threading.Lock()

    def __init__(self):
        self.is_successful = False

    @staticmethod
    def qr_code_helper():
        with QRCodeHelper.lock:
            if not hasattr(QRCodeHelper, 'ins'):
                setattr(QRCodeHelper, 'ins', QRCodeHelper())
            return getattr(QRCodeHelper, 'ins')

    def generate_lesson_qr_code(self, code):
        """生成二维码
        """
        self.is_successful = True
        try:
            assert isinstance(code, str), '无法生成班课码，无效的类型'
            myqr.run(words=code,
                     version=9,
                     save_name='{}.png'.format(code),
                     save_dir=gdata.LESSON_QR_CODE_PATH)
        except (AssertionError, Exception) as e:
            _logger.warning('generate_lesson_qr_code, error:{}'.format(e), exc_info=True)
            self.is_successful = False


class Paginator(object):
    """分页管理
    """

    class MyPageNumberPagination(PageNumberPagination):
        # 每页显示多少个
        page_size = 3
        # 默认每页显示3个，可以通过传入pager1/?page=2&size=4,改变默认每页显示的个数
        page_size_query_param = "size"
        # 最大页数不超过10
        max_page_size = 30
        # 获取页码数的
        page_query_param = "pno"

    @classmethod
    def num_paginator(cls):
        return cls.MyPageNumberPagination
