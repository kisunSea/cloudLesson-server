from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from fdfs_client.client import Fdfs_client

from teaching_helper import glog

_logger = glog.get_logger(__name__)


@deconstructible
class FastDFSStorage(Storage):
    def __init__(self, base_url=None, client_conf=None):
        """
        初始化
        :param base_url: 用于构造图片完整路径使用，图片服务器的域名
        :param client_conf: FastDFS客户端配置文件的路径
        """
        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

    def save(self, name, content, max_length=None):
        """
        在FastDFS中保存文件
        :param name: 传入的文件名
        :param content: 文件内容
        :param max_length: 限制上传大小
        :return: 保存到数据库中的FastDFS的文件名
        """
        # {
        # 'Local file name': '/home/python/1.jpg',
        # 'Storage IP': '192.168.189.133',
        # 'Remote file_id': 'group1/M00/00/00/wKi9hVz-Pm-Ab2WUAAOTipWhnKM344.jpg',
        # 'Group name': 'group1',
        # 'Status': 'Upload successfully.',
        # 'Uploaded size': '228.00KB'
        # }

        suffix = name.split('.')[-1]
        client = Fdfs_client(self.client_conf)
        ret = client.upload_by_buffer(content.read(), file_ext_name=suffix)
        if "success" not in ret.get("Status"):
            raise Exception("upload file failed")
        file_name = ret.get("Remote file_id")
        _logger.info('upload file `{}` by fdfs_client, status:{}'.format(file_name.decode(), ret.get("Status")))
        return file_name

    def url(self, name):
        """
        返回文件的完整URL路径
        :param name: 数据库中保存的文件名
        :return: 完整的URL
        """
        name = name.decode() if isinstance(name, bytes) else str(name)
        return self.base_url + name

    def exists(self, name):
        """
        判断文件是否存在，FastDFS可以自行解决文件的重名问题
        所以此处返回False，告诉Django上传的都是新文件
        :param name:  文件名
        :return: False
        """
        return False

    def path(self, name):
        """
        Return a local filesystem path where the file can be retrieved using
        Python's built-in open() function. Storage systems that can't be
        accessed using open() should *not* implement this method.
        """
        pass

        # The following methods form the public API for storage systems, but with
        # no default implementations. Subclasses must implement *all* of these.

    def delete(self, name):
        """
        Delete the specified file from the storage system.
        """
        pass

    def listdir(self, path):
        """
        List the contents of the specified path. Return a 2-tuple of lists:
        the first item being directories, the second item being files.
        """
        pass

    def size(self, name):
        """
        Return the total size, in bytes, of the file specified by name.
        """
        pass

    def get_accessed_time(self, name):
        """
        Return the last accessed time (as a datetime) of the file specified by
        name. The datetime will be timezone-aware if USE_TZ=True.
        """
        pass

    def get_created_time(self, name):
        """
        Return the creation time (as a datetime) of the file specified by name.
        The datetime will be timezone-aware if USE_TZ=True.
        """
        pass

    def get_modified_time(self, name):
        """
        Return the last modified time (as a datetime) of the file specified by
        name. The datetime will be timezone-aware if USE_TZ=True.
        """
        pass


fc = FastDFSStorage()
