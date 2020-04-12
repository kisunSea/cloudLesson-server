from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from wx_client import serializers


class JWTokenAuth(BaseAuthentication):
    """验证接收自客户端的JWT签证
    """

    def authenticate(self, request):
        token = request.data.get('token')
        if not token:
            token = request.query_params.get('token')
        valid_data = serializers.JWTVerificationSerializer().validate({'token': token})

        user = valid_data['user']
        if user:
            return (user, None)

        return exceptions.AuthenticationFailed('login failed!')


