# fast-python-worker
白嫖免费的反向代理 feieryun.cn

## 使用方法
1. 安装 python
    - [python 官网](https://www.python.org/)

2. 安装 requests 库
    ```bash
    pip install requests
    ```
3. 【可选】修改 环境变量
    ```
    FPW_HOST = 'xxxxx.28820.com' # xxxxx为自定义域名前缀
    ```
4. 运行 main.py ~~
    ```bash
    python main.py
    ```

## 简介
本程序使用了 HTTP 长轮询技术 连接到 飞儿云平台，将本地的 WEB 服务传输到公网，从而实现远程访问本地服务。

你可以自定义转发的域名前缀，例如：`xxxxx`，这样就可以通过 `xxxxx.28820.com` 来访问本地的服务。如果未设置环境变量 `FPW_HOST`，则默认自动生成作为域名前缀，如：`moon-flower-snake-red-apple.28820.com`。

飞儿云的免费反向代理服务特点：
1. 每个用户每天没有使用次数和流量限制
2. 可以自定义域名前缀
3. 目前只支持 HTTP 协议中的多种请求方式
   1. 包括但不限于：GET、POST、PUT、DELETE、HEAD、OPTIONS、PATCH、TRACE
4. 支持 HTTPS 协议

## 服务原理
下面是本程序的工作原理，如果你想自己实现一个类似的程序，可以参考这个原理。

代码使用的是 python，但是原理是通用的。

FPW: Fast Python Worker / Feieryun PHP Worker

1. 发起 POST 请求到飞儿云的API，创建失败将返回错误信息，创建成功将会保持连接，直到有访客访问这个域名。
   
    1. POST请求的内容为：
        ```python
        url = 'https://' + FPW_HOST + '/'
        header = {
            'fpw-host': FPW_HOST,
            'fpw-token': FPW_TOKEN,
            'user-agent': 'php-worker-v1',
            'content-type': 'application/octet-stream'
        }
        body = ''
        ```
    
    2. 发起请求
        ```python
        r = requests.post(url, headers=header, data=body)
        ```
    
    3. 如果此时有访客访问这个域名，刚才发起的 POST 请求将会返回访客的请求信息，包括请求头和请求体。
   
     - 访客的请求头将会以json格式在飞儿云响应头`fpw-header`中返回
        ```
        forward_header = json.loads(r.headers["fpw-header"])
        ```

     - 访客的请求体将会以二进制数据在飞儿云响应体中返回
        ```
        forward_body = r.content
        ```

     - 访客的请求将被分配一个唯一的 `fpw-id`，这个 `fpw-id` 将会在后续的回复请求中被使用，用于标识这个请求
        ```
        fpw_id = r.headers["fpw-id"]
        ```

     - 访客请求的IP地址，请求地址和请求方法将会在飞儿云响应头 `fpw-ip`， `fpw-url` 和 `fpw-method` 中返回
        ```
        user_ip = r.headers["fpw-ip"]
        forward_url = r.headers["fpw-url"]
        forward_method = r.headers["fpw-method"]
        ```

2. 将访客的请求信息转发到本地的服务
    ```
    r = requests.request(forward_method, forward_url, headers=fpw_header, data=fpw_body)
    ```

3. 将本地服务的响应信息转发到飞儿云
将本地服务的响应头和响应体分别放到飞儿云的请求头和请求体中，发送给飞儿云
    ```python
    url = 'https://' + FPW_HOST + '/'
    header = {
        'fpw-host': FPW_HOST,
        'fpw-token': FPW_TOKEN,

        'fpw-id': fpw_id, # 用于标识这个请求
        'fpw-status' = r.status_code, # 本地服务的响应状态码
        'fpw-header' = r.headers, # 本地服务的响应头

        'user-agent': 'php-worker-v1',
        'content-type': 'application/octet-stream'
    }
    body = r.content # 本地服务的响应体
    ```
4. 飞儿云将会将这个请求的响应信息发送给访客，并且这个请求将被挂起，直到有新的访客访问这个域名。

5. 重复 1.3 - 4 步骤，直到程序退出。