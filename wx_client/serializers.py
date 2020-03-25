from rest_framework import serializers
from teaching_helper import gdata


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
    university = serializers.CharField(max_length=32, default='',required=False)

    # rss_method just supports email up to now
    rss_method = serializers.ChoiceField(choices=gdata.RSS_CHOICES, default=gdata.UNBIND_RSS, required=False)


