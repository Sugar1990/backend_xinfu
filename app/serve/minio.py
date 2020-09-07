from minio import Minio
from minio.error import ResponseError
import base64
import io
import os
from datetime import timedelta

from ..conf import MINIO_SERVER_IP, MINIO_PORT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY


class MinioClient(object):
    _instance = None
    PREFIX_CUSTOMER = 'customer'
    PREFIX_DOCTOR = 'doctor'

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
            # 服务为HTTP时secure使用False，服务为HTTPs时secure使用Ture。否则会报urllib3.exceptions.MaxRetryError: Max retries exceeded with url:
            cls._instance.minio_client = Minio('{}:{}'.format(MINIO_SERVER_IP, MINIO_PORT), access_key=MINIO_ACCESS_KEY,
                                               secret_key=MINIO_SECRET_KEY, secure=False)

        return cls._instance

    def __init__(self):
        pass

    def get_bucket_name(self, uid):
        return "customer{0}".format(uid)

    def get_minio_path(self, path, name):
        return os.path.join(path, name)

    # 传uid，没有bucket，创建
    def check_bucket(self, uid):
        bucket_name = self.get_bucket_name(uid)
        if not self.exist_bucket(bucket_name):
            self.create_bucket(bucket_name)

    def create_bucket(self, bucket_name):
        try:
            self.minio_client.make_bucket(bucket_name)
        except ResponseError as err:
            print('Minio Error:', err)

    def exist_bucket(self, bucket_name):
        try:
            return self.minio_client.bucket_exists(bucket_name)
        except ResponseError as err:
            print('Minio Error:', err)

    def upload(self, uid, path, name, file_base64):
        '''
        :param uid: get_bucket_name之后获得bucket_name
        :param path: 文件在bucket下对根目录的全路径
        :param name: 文件名称（文件名.ext)
        :param file_base64:
        :return:
        '''
        res = ''
        bucket_name = self.get_bucket_name(uid)
        if not self.exist_bucket(bucket_name):
            self.create_bucket(bucket_name)
        try:
            base64_str = MinioClient.cut_base64str_header(file_base64)
            file_data = base64.b64decode(base64_str)
            file_size = int(MinioClient.base64file_size(base64_str))
            file_buffered_reader = io.BytesIO(file_data)
            minio_path = self.get_minio_path(path, name)
            res = self.minio_client.put_object(bucket_name, minio_path, file_buffered_reader, file_size)
        except ResponseError as err:
            print('Minio Error:', err)
        finally:
            return res, minio_path

    def file_upload(self, uid, save_name, file_path):
        '''
        :param uid: get_bucket_name之后获得bucket_name
        :param save_name: 文件在bucket下对根目录的全路径
        :param file_path: 文件本地路径，上传到服务器（文件名.ext)
        :return:
        '''
        res = ''
        bucket_name = self.get_bucket_name(uid)
        if not self.exist_bucket(bucket_name):
            self.create_bucket(bucket_name)
        try:
            # save_name = os.path.join(bucket_name, save_name)
            print("file_upload:", save_name, file_path)

            with open(file_path, 'rb') as file_data:
                print("file_data", file_data, flush=True)
                file_size = os.stat(file_path).st_size
                print("file_size", file_size, flush=True)
                res = self.minio_client.put_object(bucket_name, save_name, file_data,
                                      file_size, 'application/octet-stream',
                                      None, None, None,
                                      5 * 1024 * 1024)
                print("put:", res, flush=True)

            # res = self.minio_client.fput_object(bucket_name, save_name, file_path)
            print("file_upload:", res, flush=True)
        except ResponseError as err:
            print('Minio Error:', err)
        finally:
            return res

    def get_url(self, uid, file_path):
        # presigned get object URL for object name, expires in 2 days.
        try:
            bucket_name = self.get_bucket_name(uid)
            return self.minio_client.presigned_get_object(bucket_name, file_path, expires=timedelta(days=2))
        # Response error is still possible since internally presigned does get bucket location.
        except ResponseError as err:
            print('Minio Error:', err)

    @staticmethod
    def cut_base64str_header(base64str):
        try:
            # 检索头部关键词位置
            pos = base64str.find(";base64,")
            # 去头部，从pos + 8 到末尾
            if pos > -1:
                base64str = base64str[pos + 8:]
            return base64str

        except Exception as e:
            print('cut_base64str_header Error:', str(e))

    # 暂时没有用到
    @staticmethod
    def base64file_size(base64str):
        """
         * @功能  精确计算base64字符串文件大小（单位：B）
         * @注意  base64字符串(不含data:audio/wav;base64,文件头)
        """
        try:
            # 1.获取base64字符串长度(不含data:audio/wav;base64,文件头)
            size0 = len(base64str)

            # 2.获取字符串的尾巴的最后10个字符，用于判断尾巴是否有等号，正常生成的base64文件'等号'不会超过4个
            tail = base64str[-10:]

            # 3.找到等号，把等号也去掉,(等号其实是空的意思,不能算在文件大小里面)
            equal_index = tail.find("=")
            if equal_index > 0:
                size0 = size0 - (10 - equal_index)

            # 4.计算后得到的文件流大小，单位为字节
            return size0 - (size0 / 8) * 2

        except Exception as e:
            print('base64file_size Error:', str(e))

    def test(self):
        with open('url.txt', 'w') as f:
            f.write(self.get_url('temppage3', '690c45eb8a1d3ac5fbf4de9d12eef51b7a8998032b97cf-KBChBD.png'))
