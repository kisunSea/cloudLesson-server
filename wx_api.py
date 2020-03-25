"""
support:
    * authenticate code and get openId and session_key
"""
import json

from teaching_helper import glog

from teaching_helper import gdata

import requests

_logger = glog.get_logger(__name__)


class WxAPIAccess(object):
    """request method for WeChat Http Api
    """

    @staticmethod
    def auth_keys(code):
        """

        :param code:
        :return:
        """
        data = {
            'appid': 'wx4669cc2551ee1599',
            'secret': 'eb2bbfd05a5ea50a33671c36922af13c',
            'js_code': code,
        }

        wx_auth_url = gdata.WX_AUTH_API.format(**data)
        res = json.loads(requests.get(wx_auth_url).text)
        session_key = res.get('session_key', None)
        open_id = res.get('openid', None)

        return session_key, open_id
