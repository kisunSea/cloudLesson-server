from django.views import View
from django.shortcuts import render
from teaching_helper import glog
from wx_client.components.authentication import LoginRequire

_logger = glog.get_logger(__name__)


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

    def get(self, request, **_):
        """登录界面
        """
        _ = self

        return render(request, 'login.html')

    def post(self, request, **_):
        pass

    def put(self, request, **_):
        pass


class UploadFile(LoginRequiredView):

    def post(self, request, **_):
        pass
