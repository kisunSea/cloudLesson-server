from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer
from rest_framework_jwt.authentication import JSONWebTokenAuthentication


class JWTokenAuth(BaseAuthentication):
    """验证接收自客户端的JWT签证
    """

    def authenticate(self, request):
        token = request.META.get('HTTP_TOKEN')
        valid_data = VerifyJSONWebTokenSerializer().validate({'token': token})

        user = valid_data['user']
        if user:
            return (user, None)

        return exceptions.AuthenticationFailed('用户认证失败...')
