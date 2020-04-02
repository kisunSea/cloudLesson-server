import jwt
from django.utils.translation import ugettext as _
from rest_framework import serializers

from teaching_helper import gdata
from utils import JWTHandler
from wx_client import models as wx_m


class JWTVerificationSerializer(serializers.Serializer):
    """
    Abstract serializer used for verifying and refreshing JWTs.
    """
    token = serializers.CharField()

    def validate(self, attrs):

        token = attrs['token']

        payload = self._check_payload(token=token)
        user = self._check_user(payload=payload)

        print(payload, token)

        return {
            'token': token,
            'user': user
        }

    def _check_payload(self, token):
        # Check payload valid (based off of JSONWebTokenAuthentication,
        # may want to refactor)
        _self = self
        try:
            payload = JWTHandler.jwt_decode_handler(token)
        except jwt.ExpiredSignature:
            msg = _('Signature has expired.')
            raise serializers.ValidationError(msg)
        except jwt.DecodeError:
            msg = _('Error decoding signature.')
            raise serializers.ValidationError(msg)

        return payload

    def _check_user(self, payload):
        _self = self
        username = JWTHandler.jwt_get_username_from_payload_handler(payload)

        if not username:
            msg = _('Invalid payload.')
            raise serializers.ValidationError(msg)

        # Make sure user exists
        try:
            user = wx_m.UserProfile.objects.filter(nickName=username).first()
        except wx_m.UserProfile.DoesNotExist:
            msg = _("User doesn't exist.")
            raise serializers.ValidationError(msg)

        if not user.is_active:
            msg = _('User account is disabled.')
            raise serializers.ValidationError(msg)

        return user


class UserProfileSerializer(serializers.Serializer):

    gender = serializers.ChoiceField(choices=gdata.GENDER_CHOICES, default=gdata.UNKNOWN)
    nickName = serializers.CharField(required=True, max_length=32)
    encrypted_code = serializers.CharField(required=True, max_length=128)
    country = serializers.CharField(max_length=32, default='', required=False)
    province = serializers.CharField(max_length=32, required=False)
    city = serializers.CharField(max_length=32, required=False)
    tel = serializers.CharField(max_length=11, required=False)
    avatarUrl = serializers.URLField(required=True)
    # email address will be just saved when it verified
    email = serializers.EmailField(required=False)

    # school of the user will saved as '北京大学' (university code instead)
    university = serializers.CharField(max_length=32, default='', required=False)

    # rss_method just supports email up to now
    rss_method = serializers.ChoiceField(choices=gdata.RSS_CHOICES, default=gdata.UNBIND_RSS, required=False)

    def validate(self, attrs):
        pass
