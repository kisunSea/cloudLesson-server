import time
import uuid
import collections
from urllib.parse import urljoin

from django.views import View
from django.shortcuts import render
from django.contrib.auth import get_user_model, login, logout
from teaching_helper import glog
from teaching_helper import gdata
from wx_client.components.authentication import LoginRequire

import utils
from utils import DictResponse

_logger = glog.get_logger(__name__)
User = get_user_model()


class HandleExceptionView(View):
    """自动捕捉视图逻辑中出现的各种异常

    使用该视图模板能做什么？
    1. 捕捉视图异常
    2. 输出至日志
    """

    def __init__(self, *args, **kwargs):
        super(HandleExceptionView, self).__init__(*args, **kwargs)
        glog.APIViewCatchException(self, _logger).decorate()


class LoginRequiredView(HandleExceptionView, LoginRequire):
    """限制登录后的用户才能访问的视图

    使用该视图模板能做什么？
    1. 捕捉视图异常
    2. 输出至日志
    3. 用户必须已经登录
    """
    pass


class LoginView(HandleExceptionView):
    """Web端登录视图

    :remark:
    1. 该接口所有用户（不校验用户的登录态）均可以访问
    2. 仅处理用户的登录逻辑
    """

    def __init__(self, **kwargs):
        super(LoginView, self).__init__(**kwargs)
        glog.APIViewCatchException(self, _logger).decorate()

    def get(self, request, **_):
        """登录界面
        """
        _ = self
        LoginQRItem = collections.namedtuple(gdata.LOGIN_QR_CLS_NAME,
                                             ['effective_time',
                                              'is_success',
                                              'user_id',
                                              'qr_path'])

        qr_uid = uuid.uuid4().hex
        qr_generator = utils.QRCodeHelper.qr_code_helper()
        qr_generator.generate_qr_code(qr_uid, path=gdata.LOGIN_QR_CODE_PATH)
        now_timestamp = time.time()
        qr_url = urljoin(gdata.HTTP_DOMAIN + '/images/qrcode/',
                         '{}.png'.format(qr_uid)) if qr_generator.is_successful else ''
        login_qr_obj = LoginQRItem(now_timestamp, False, None, qr_url)
        with gdata.LOGIN_QR_CODE_CACHE_LOCK:
            gdata.LOGIN_QR_CODE_CACHE[qr_uid] = login_qr_obj

        page_data = {
            'login_qr_addr': qr_url,
        }
        return render(request, 'login.html', context=page_data)

    def post(self, request, **_):
        """效验用户是否登陆成功，若成功则跳转界面并将session存储在浏览器.
        """
        login_id = request.POST.get('random_code')
        with gdata.LOGIN_QR_CODE_CACHE_LOCK:
            qr_code_cache = gdata.LOGIN_QR_CODE_CACHE

        login_record = qr_code_cache.get(login_id)
        if not login_record:
            return DictResponse(errmsg='登录失败')

        login(request, User(id=login_record.user_id))
        del qr_code_cache[login_id]
        return DictResponse(r=1, data='登陆成功')


class UploadFile(LoginRequiredView):

    def post(self, request, **_):
        pass
