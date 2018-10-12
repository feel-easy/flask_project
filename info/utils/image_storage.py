import oss2, os
from info import config


def storage(data, file_name):
    try:
        auth = oss2.Auth(config.access_key_id, config.access_key_secret)
        bucket = oss2.Bucket(auth, config.endpoint, config.bucket_name)
        result = bucket.put_object(file_name, data)
        # HTTP返回码。
        # print('http status: {0}'.format(result.status))
        # # 请求ID。请求ID是请求的唯一标识，强烈建议在程序日志中添加此参数。
        # print('request_id: {0}'.format(result.request_id))
        # # ETag是put_object方法返回值特有的属性。
        # print('ETag: {0}'.format(result.etag))
        # # HTTP响应头部。
        # print('date: {0}'.format(result.headers['date']))

    except Exception as e:
        raise e;

    if result.status != 200:
        raise Exception("上传图片失败")
    return file_name + '_sty1'


if __name__ == '__main__':
    file = input('请输入文件路径')
    with open(file, 'rb') as f:
        storage(f.read(), file)
