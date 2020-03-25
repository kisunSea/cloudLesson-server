from django.contrib.auth.models import AbstractUser
from django.db import models

from teaching_helper import gdata


class UserProfile(AbstractUser):
    """user profile

    this class include user normal information
    """

    # unique identification
    u_uuid = models.UUIDField(max_length=36, null=True)
    gender = models.IntegerField(choices=gdata.GENDER_CHOICES, default=gdata.UNKNOWN)
    username = models.CharField(max_length=32, default='')
    country = models.CharField(max_length=32, default='')
    province = models.CharField(max_length=32, null=True, blank=True, default='')
    city = models.CharField(max_length=32, null=True, blank=True, default='')
    tel = models.CharField(max_length=11, default='')
    register_time = models.DateTimeField(auto_now=True, null=False, blank=False)
    avatarUrl = models.URLField(blank=True, null=True)

    # encrypted field, this field reference openId, secret_key ext.
    encrypted_code = models.CharField(max_length=128, unique=True, blank=False, null=False)

    # email address will be just saved when it verified
    email = models.EmailField(blank=True, null=True, default='')

    # school of the user will saved as '北京大学' (university code instead)
    university = models.CharField(max_length=32, default='')

    # rss_method just supports email up to now
    rss_method = models.CharField(verbose_name='消息订阅方式', max_length=32, choices=gdata.RSS_CHOICES,
                                  default=gdata.UNBIND_RSS)

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'


class FeatureForSignIn(models.Model):
    """this Model class will save data which used in signing
    """
    face_token = models.CharField(verbose_name='人脸特征密文', max_length=256, unique=True)

    # the mac of BlueTooth is not unique
    blue_tooth_mac = models.CharField(verbose_name='蓝牙Mac地址', max_length=64)
    record_time = models.DateTimeField(verbose_name='记录时间', auto_now_add=True)

    class Meta:
        verbose_name = 'user feature'
