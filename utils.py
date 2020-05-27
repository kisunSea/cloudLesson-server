import datetime
import threading

import jwt
from rest_framework.response import Response
from MyQR import myqr

from teaching_helper import glog
from teaching_helper import gdata

_logger = glog.get_logger(__name__)


# functions


def jwt_get_secret_key(_):
    from django.conf import settings
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

    def generate_qr_code(self, code, path=gdata.LESSON_QR_CODE_PATH):
        """生成二维码
        """
        self.is_successful = True
        try:
            assert isinstance(code, str), '无法生成二维码'
            myqr.run(words=code,
                     version=9,
                     save_name='{}.png'.format(code),
                     save_dir=path)
        except (AssertionError, Exception) as e:
            _logger.warning('generate_qr_code, error:{}'.format(e), exc_info=True)
            self.is_successful = False


class DictResponse(Response):
    """字典响应

    :remark:
        固定返回值(Response)对象的data格式
        * data: 操作成功后返回的值
        * errmsg: 出错后的错误提示
        * r: 操作是否成功，0代表成功，1代表失败
    """

    def __init__(self, r=1, errmsg='', data='', **kwargs):
        ret = dict(r=r, errmsg=errmsg, data=data)
        kwargs['data'] = ret
        super(DictResponse, self).__init__(**kwargs)


class LoginQRItem(object):
    def __init__(self, effective_time, is_success, user_id, qr_path):
        self.effective_time = effective_time
        self.is_success = is_success
        self.user_id = user_id
        self.qr_path = qr_path

    def __repr__(self):
        return '<LoginQRItem(effective_time={}, is_success={}, user_id={}, qr_path={})>'.format(self.effective_time,
                                                                                                self.is_success,
                                                                                                self.user_id,
                                                                                                self.qr_path)
