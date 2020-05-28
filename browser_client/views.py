import os
import time
import uuid
import json
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render, redirect
from django.views import View

import utils
import model_access
from fdfs_storage import fc
from teaching_helper import gdata
from teaching_helper import glog
from wx_client import models as wx_models
from logic import resource_upload
from wx_client.components.authentication import LoginRequire

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
        _ = self
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
        _ = self
        user = request.user  # type: wx_models.UserProfile
        return render(request, 'upload_index.html', {
            'lessons': [
                {
                    'lesson_code': t.lesson_code,
                    'lesson_name': t.lesson_name,
                    'stu_num': t.stu_num,
                } for t in user.teaching_lessons.all()]
        })

    def post(self, request, **_):
        action = request.POST.get('action')
        if not action:
            f_obj = request.FILES.get('file')
            file_suffix = f_obj.name.split('.')[-1]
            if file_suffix not in gdata.VALID_FILE_SUFFIX:
                return JsonResponse({'file_url': ''})
            assert file_suffix.lower() in gdata.VALID_FILE_SUFFIX, '无效的文件类型，file name: {}'.format(f_obj.name)
            _logger.info('get file from browser. file_obj: <{}>'.format(f_obj.name))
            f_name = '{}.{}'.format(uuid.uuid4().hex, file_suffix)
            fn = fc.save(f_name, f_obj)
            return JsonResponse({'file_url': fc.url(fn), 'file_name': f_obj.name})

        else:
            return self._put(request)


    def _put(self, request, **_):
        """映射文件至数据库操作
        """
        try:
            user = request.user
            file_array =  request.POST.get('files_array')
            resource_type = request.POST.get('resource_type')
            selected_lesson = request.POST.get('selected_lesson')

            _logger.info(
                'flush file information to DB. user:{}, file_array:{}, resource_type:{}, selected_lesson:{}'.format(
                    user,
                    file_array,
                    resource_type,
                    selected_lesson))
            lesson = model_access.QueryLesson.query_lesson_by_lesson_code(selected_lesson)
            assert resource_type in gdata.RESOURCE_TYPES, '无效的课堂资源类型'
            assert lesson, '无效的课堂代码，请刷新页面'

            resource_upload.ResourceStorage.flush_resource_2_db(resource_type, json.loads(file_array), lesson)
            return JsonResponse({'r': 0})
        except Exception as e:
            _logger.warning('upload resource error. error: {}'.format(e), exc_info=True)
            return JsonResponse({'r': 1})


class ExitLogin(View):
    def get(self, request, **_):
        _ = self
        logout(request)
        return redirect(settings.LOGIN_URL)


class ExamTemplateDownload(View):

    def get(self, request, **_):
        """下载试卷Excel模板文件"""
        _ = self
        _ = request
        try:
            response = FileResponse(open(gdata.EXAM_TEMPLATE_PATH, 'r'))
            response['content_type'] = "application/octet-stream"
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(gdata.EXAM_TEMPLATE_PATH)
            return response
        except Exception as err:
            _logger.warning('Failed to download examination: {}'.format(err), exc_info=True)
            raise Http404
