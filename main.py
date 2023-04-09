import json
import requests
import multiprocessing
import time
import os

from requests.utils import CaseInsensitiveDict

FPW_URL = 'https://baiduzzzzzz1.28820.com/'
FPW_HOST = 'baiduzzzzzz1.28820.com'
FPW_TOKEN = '21a018194adc44e7'


def build_header(header):
    if isinstance(header, str):
        header = json.loads(header)
    if 'content-type' not in header:
        header['content-type'] = 'text/html; charset=utf-8'
    if isinstance(header, CaseInsensitiveDict):
        header = dict(header)
    return json.dumps(header)


def html(http_code, header, body):
    return {
        'http_code': http_code,
        'header': build_header(header),
        'body': body
    }


def process(req):
    if req['method'] == 'GET':
        r = requests.get('http://127.0.0.1/'+req['url'], headers=req['header'])
        return html(r.status_code, r.headers, r.content)
    elif req['method'] == 'POST':
        print(req['body'])
        r = requests.post('http://127.0.0.1'+req['url'], headers=req['header'], data=req['body'])
        return html(r.status_code, r.headers, r.text)
    data = '你好，世界！<br /> 现在是 %s' % time.time() + \
        '<br />来自 %s 的朋友' % req['ip']+'<br />'
    return html(201, {}, data)


def fetch_request():
    header = {
        'fpw-host': FPW_HOST,
        'fpw-token': FPW_TOKEN,
        'user-agent': 'php-worker-v1',
        'content-type': 'application/octet-stream'
    }

    response = None

    # 创建一个会话对象
    session = requests.Session()
    while True:
        if response != None:
            # 将上次请求的响应信息传递给下次请求
            header['fpw-rid'] = req['fpw_rid']
            header['fpw-status'] = str(response['http_code'])
            header['fpw-header'] = response['header']

        try:
            r = session.post(FPW_URL, timeout=60, headers=header,
                             data=response['body'] if response != None else None)
            if r.status_code == 200:
                response = None  # 重置
                req = None  # 重置

            # 获取请求信息
            fpw_rid = r.headers["fpw-rid"]
            fpw_header = json.loads(r.headers["fpw-header"])
            print(fpw_header["x-forwarded-for"] + " > " + fpw_header["url"])
            req = {
                'method': fpw_header["method"],
                'url': fpw_header["url"],
                'header': fpw_header,
                'body': r.content,
                'ip': fpw_header["x-forwarded-for"],
                'fpw_rid': fpw_rid
            }

            response = process(req)  # 处理请求

        except requests.exceptions.ConnectionError:
            print('Reconning...')
            continue
        except Exception as e:
            print('Error: %s' % e)
            continue


if __name__ == '__main__':
    pool = multiprocessing.Pool(processes=10)
    for i in range(10):
        pool.apply_async(fetch_request, ())
        time.sleep(1)
    pool.close()
    pool.join()
