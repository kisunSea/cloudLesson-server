import jwt
from django.utils.translation import ugettext as _
from rest_framework import serializers

from teaching_helper import gdata
from teaching_helper import glog
from utils import JWTHandler
from wx_client import models
from wx_client import models as wx_m

_logger = glog.get_logger(__name__)


class JWTVerificationSerializer(serializers.Serializer):
    """
    Abstract serializer used for verifying and refreshing JWTs.
    """
    token = serializers.CharField()

    def validate(self, attrs):

        token = attrs['token']

        payload = self._check_payload(token=token)
        user = self._check_user(payload=payload)

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

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class UserProfileSerializer(serializers.Serializer):
    u_uuid = serializers.UUIDField(required=True)
    gender = serializers.ChoiceField(choices=gdata.GENDER_CHOICES, default=gdata.UNKNOWN)
    nickName = serializers.CharField(required=True, max_length=32)
    encrypted_code = serializers.CharField(required=True, max_length=128)
    country = serializers.CharField(max_length=32, default='', required=False)
    province = serializers.CharField(max_length=32, required=False)
    city = serializers.CharField(max_length=32, required=False, allow_blank=True)
    tel = serializers.CharField(max_length=11, required=False, allow_blank=True)
    avatarUrl = serializers.URLField(required=True)
    # email address will be just saved when it verified
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)

    # school of the user will saved as '北京大学' (university code instead)
    university = serializers.CharField(max_length=32, default='', required=False, allow_null=True, allow_blank=True)

    # rss_method just supports email up to now
    rss_method = serializers.ChoiceField(choices=gdata.RSS_CHOICES, default=gdata.UNBIND_RSS, required=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class FeatureForSignInSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FeatureForSignIn
        fields = ('face_token', 'base64_face')

    def update(self, instance, validated_data):
        super(FeatureForSignInSerializer, self).update(instance, validated_data)

    def create(self, validated_data):
        super(FeatureForSignInSerializer, self).create(validated_data)


class LessonSerializer(serializers.ModelSerializer):
    """
    uuid = models.UUIDField(unique=True)
    teacher = models.ForeignKey(UserProfile, related_name='teaching_lessons', on_delete=models.PROTECT)
    lesson_code = models.CharField(max_length=gdata.LESSON_CODE_LENGTH)
    lesson_cls = models.CharField(max_length=2, choices=gdata.LESSON_CLS_CHOICE, default=gdata.OTHER_SUBJECT)
    create_time = models.DateTimeField(auto_created=True)
    finish_time = models.DateTimeField(default=None, null=True)
    qr_code = models.URLField(verbose_name='班课二维码地址', max_length=64)
    academic_year = models.CharField(default=str(datetime.now().year), max_length=len(str(datetime.now().year)))
    term = models.IntegerField(choices=gdata.TERM_CHOICE, default=gdata.PRE_TERM)
    is_delete = models.BooleanField(default=False)
    student = models.ManyToManyField(UserProfile, related_name='listening_lessons')
    """

    teacher_id = serializers.IntegerField(required=True)

    class Meta:
        model = models.Lesson
        fields = (
            'teacher_id',
            'lesson_code',
            'lesson_cls',
            'qr_code',
            'academic_year',
            'term',
            'desc',
            'lesson_name',
        )
        depth = 1


class LessonInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Lesson
        fields = '__all__'
        depth = 1


class SayingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Saying
        fields = '__all__'
        depth = 1


class SayingPOSTSerializer(serializers.ModelSerializer):
    publisher_id = serializers.IntegerField(required=True)

    class Meta:
        model = models.Saying
        fields = (
            'publisher_id',
            'content',
            'related_files',
            'ext_info',
        )
        depth = 1
