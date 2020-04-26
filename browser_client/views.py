from django.views import View
from django.shortcuts import render

# Create your views here.

class LoginView(View):

    def get(self, request, **_):
        """登录界面
        """

        return render(request, 'login.html')
