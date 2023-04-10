import json
import requests
import multiprocessing
import time
import os
import random

from requests.utils import CaseInsensitiveDict


def gen_perfix():
    dic = [
        ['moon', 'sun', 'star', 'earth', 'mars', 'jupiter', 'saturn',
            'uranus', 'neptune', 'pluto', 'mercury', 'venus'],
        ['river', 'house', 'tree', 'flower', 'grass',
            'cloud', 'rain', 'snow', 'wind'],
        ['cat', 'dog', 'bird', 'fish', 'pig', 'cow', 'horse', 'sheep',
         'monkey', 'mouse', 'rabbit', 'tiger', 'dragon', 'snake'],
        ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'black',
            'white', 'gray', 'brown', 'pink', 'gold', 'silver'],
        ['apple', 'banana', 'watermelon', 'pear', 'grape', 'pineapple', 'strawberry', 'cherry', 'mango', 'lemon', 'lime',
            'coconut', 'peach', 'melon', 'plum', 'kiwi', 'tomato', 'avocado', 'eggplant', 'potato', 'carrot', 'corn', 'pepper',
            'broccoli', 'mushroom', 'onion', 'garlic', 'ginger', 'cucumber', 'lettuce', 'spinach', 'cabbage', 'peas', 'bean',
            'sweetpotato', 'chestnut', 'walnut', 'almond', 'hazelnut', 'cashew', 'pecan', 'pistachio']
    ]
    perfix = ''
    for i in range(5):
        perfix += dic[i][random.randint(0, len(dic[i])-1)] + \
            ('-' if i < 4 else '')
    return perfix


if os.getenv('FPW_HOST') == None:
    host = gen_perfix()
    host = host + '.28820.com'
    FPW_url = 'https://' + host + '/'
    FPW_host = host
    FPW_token = '21a018194adc44e7'
else:
    FPW_url = 'https://' + os.getenv('FPW_HOST') + '/'
    FPW_host = os.getenv('FPW_HOST')
    FPW_token = '21a018194adc44e7'


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
        r = requests.get(
            'http://127.0.0.1'+req['url'], headers=req['header'], allow_redirects=False)
        return html(r.status_code, r.headers, r.content)
    elif req['method'] == 'POST':
        r = requests.post('http://127.0.0.1' +
                          req['url'], headers=req['header'], data=req['body'], allow_redirects=False)
        return html(r.status_code, r.headers, r.text)
    else:
        data = 'Method not allowed'
    return html(400, {}, data)


def fetch_request(args):
    index, FPW_url, FPW_host, FPW_token = args['index'], args['url'], args['host'], args['token']
    time.sleep(index)

    header = {
        'fpw-host': FPW_host,
        'fpw-token': FPW_token,
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
            r = session.post(FPW_url, timeout=180, headers=header,
                             data=response['body'] if response != None else None)
            if r.status_code == 200:
                response = None  # 重置
                req = None  # 重置

            # 获取请求信息
            fpw_rid = r.headers["fpw-rid"]
            forward_header = json.loads(r.headers["fpw-header"])

            forward_url = r.headers["fpw-url"]
            forward_method = r.headers["fpw-method"]
            user_ip = r.headers["fpw-ip"] if "fpw-ip" in r.headers else forward_header["x-forwarded-for"]
            print("%s [%s] > %s" % (user_ip, forward_method, forward_url))
            req = {
                'method': forward_method,
                'url': forward_url,
                'header': forward_header,
                'body': r.content,
                'ip': user_ip,
                'fpw_rid': fpw_rid
            }

            response = process(req)  # 处理请求

        except requests.exceptions.ConnectionError:
            print('Process %d > Reconning...' % index, flush=True)
            continue
        except Exception as e:
            print('Error: %s' % e)
            continue


if __name__ == '__main__':
    print('Start...')
    pool = multiprocessing.Pool(processes=10)
    for i in range(10):
        config = {
            'index': i,
            'url': FPW_url,
            'host': FPW_host,
            'token': FPW_token
        }
        pool.apply_async(fetch_request, (config,))
    print('Sccessfully start, run on %s' % FPW_url)
    time.sleep(100)
    pool.close()
    pool.join()
