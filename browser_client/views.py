import time
import uuid
import os
import collections
from urllib.parse import urljoin

from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login, logout
from django.http import JsonResponse, FileResponse, Http404
from teaching_helper import glog
from teaching_helper import gdata
from wx_client.components.authentication import LoginRequire
from django.conf import settings

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


class LoginView(View):
    """Web端登录视图

    :remark:
    1. 该接口所有用户（不校验用户的登录态）均可以访问
    2. 仅处理用户的登录逻辑
    """
    #
    # def __init__(self, **kwargs):
    #     super(LoginView, self).__init__(**kwargs)
    #     glog.APIViewCatchException(self, _logger).decorate()

    def get(self, request, **_):
        """登录界面
        """
        _ = self
        qr_uid = uuid.uuid4().hex
        qr_generator = utils.QRCodeHelper.qr_code_helper()
        qr_generator.generate_qr_code(qr_uid, path=gdata.LOGIN_QR_CODE_PATH)
        now_timestamp = time.time()
        qr_url = urljoin(gdata.HTTP_DOMAIN + '/images/loginqr/',
                         '{}.png'.format(qr_uid)) if qr_generator.is_successful else ''
        login_qr_obj = utils.LoginQRItem(now_timestamp, False, None, qr_url)
        with gdata.LOGIN_QR_CODE_CACHE_LOCK:
            gdata.LOGIN_QR_CODE_CACHE[qr_uid] = login_qr_obj

        page_data = {'login_qr_addr': qr_url, 'auth_key': qr_uid}
        return render(request, 'login_index.html', context=page_data)

    def post(self, request, **_):
        """效验用户是否登陆成功，若成功则跳转界面并将session存储在浏览器.
        """
        try:
            login_id = request.POST.get('random_code')
            with gdata.LOGIN_QR_CODE_CACHE_LOCK:
                qr_code_cache = gdata.LOGIN_QR_CODE_CACHE

            login_record = qr_code_cache.get(login_id)  # type: utils.LoginQRItem
            _logger.debug('login authenticator item: {}'.format(login_record))
            if not login_record:
                return JsonResponse({'url': '', 'errmsg': '请刷新页面并重新尝试'})
            if login_record and login_record.user_id is None:
                return JsonResponse({'url': '', 'errmsg': '请打开微信扫码'})

            login(request, User(id=login_record.user_id))
            del qr_code_cache[login_id]
            return JsonResponse({'url': urljoin(gdata.HTTP_DOMAIN, 'api/v1/browser_client/index'), 'errmsg': ''})
        except (ValueError, Exception) as e:
            _logger.warning('效验登录态失败: {}'.format(e), exc_info=True)


class UploadFile(View):

    def get(self, request, **_):
        user = request.user

        return render(request, 'upload_index.html')

    def post(self, request, **_):
        pass


class ExitLogin(View):
    def get(self, request, **_):
        logout(request)
        return redirect(settings.LOGIN_URL)


class ExamTemplateDownload(View):

    def get(self, request, **_):
        """下载试卷Excel模板文件"""
        _ = request
        try:
            response = FileResponse(open(gdata.EXAM_TEMPLATE_PATH, 'r'))
            response['content_type'] = "application/octet-stream"
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(gdata.EXAM_TEMPLATE_PATH)
            return response
        except Exception as err:
            _logger.warning('Failed to download examination: {}'.format(err), exc_info=True)
            raise Http404




