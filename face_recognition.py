"""
face recognition related function

* fetch unique face_token by api from BaiDu
    module: aip
    reference: https://ai.baidu.com/ai-doc/FACE/ek37c1qiz
* check validation of face-image requested，verify this image have common face_token in database.
    reference model: FeatureForSignIn
"""

import base64

from aip import AipFace

from teaching_helper import gdata
from teaching_helper import glog

_logger = glog.get_logger(__name__)

aip_client = AipFace(**gdata.AIP_KWARGS)


# functions


def generate_b64encode_img_data(path):
    """
    :param path: face-image path
    """
    try:

        with open(path, mode='rb') as face_img:
            raw_data = face_img.read()

        b64_ret = base64.b64encode(raw_data)
        return b64_ret.decode()

    except (FileNotFoundError, Exception) as _:
        return None


# classes


class FaceRecognitionAccess(object):

    @staticmethod
    def face_features(face_img_path, options=gdata.AIP_CLIENT_ARGS.get('options')) -> dict:
        """Provides a face data query and gets the face_token of the current face sample image

        rules in request options:
            * reference -> https://ai.baidu.com/ai-doc/FACE/ek37c1qiz#%E4%BA%BA%E8%84%B8%E6%A3%80%E6%B5%8B
        """

        b64encode_data = generate_b64encode_img_data(face_img_path)
        res = aip_client.detect(image=b64encode_data,
                                image_type=gdata.AIP_CLIENT_ARGS.get('image_type'),
                                options=options)

        return res.get('result', None)

    @staticmethod
    def similarity_in_img_list(face_image_paths) -> bool:
        """Comparing two people's faces is consistent

        :param face_image_paths
            Both sets of face image paths, guaranteed to be iterative
        """

        http_args = [
            {
                'image': generate_b64encode_img_data(_path),
                'image_type': gdata.AIP_CLIENT_ARGS.get('image_type'),
            } for _path in face_image_paths]

        return aip_client.match(http_args)
