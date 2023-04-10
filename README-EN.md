# Fast-Python-Worker

[English](README-EN.md) | [简体中文](README.md)

## Introduction
**FPW**: **F**ast **P**ython **W**orker / **F**eieryun **P**HP **W**orker

This program uses HTTP long polling technology to connect to Feieryun platform, transmitting the local web service to the public network, thus achieving remote access to the local service.

By default, it will forward request from visitor to the local service `http://127.0.0.1/<url>`. If you want to modify this default address, you can modify the code to implement it.

You can customize the domain name prefix to forward, for example: `xxxxx`, so you can access the local service through `xxxxx.28820.com`. If the environment variable `FPW_HOST` is not set, it will be generated as the domain name prefix by default, such as `moon-flower-snake-red-apple.28820.com`.

Features:

1. No usage times and traffic restrictions

2. Customizable domain name prefix

3. Currently supports multiple request methods in the HTTP protocol
   1. Including but not limited to: GET, POST, PUT, DELETE, HEAD, OPTIONS, PATCH, TRACE
   2. WebSocket protocol is not supported currently
   
4. Supports HTTPS

5. Currently using Cloudflare CDN, may use other CDN acceleration in the future

## Usage
1. Install Python
    - [Python Official Website](https://www.python.org/)

2. Install requests library
    ```bash
    pip install requests
    ```

3. [Optional] Modify environment variables
    ```
    FPW_HOST = 'xxxxx.28820.com' # xxxxx is the custom domain name prefix
    ```

4. Run main.py ~~
    ```bash
    python main.py
    ```

5. Open your site ~~

## How it works?
If you want to implement a similar program by yourself, you can refer to this section.

The code uses Python, but the principle is universal.

1. Send a POST request to Feieryun's API, if the creation fails, an error message will be returned, and if it succeeds, the connection will be kept until a visitor visits this domain name.
   
    1. The content of the POST request is:
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
    
    2. Send the request
        ```python
        r = requests.post(url, headers=header, data=body)
        ```
    
    3. If a visitor visits this domain name at this time, the POST request that was just sent will return the visitor's request information, including the request header and request body.
   
     - The visitor's request header will be returned in JSON format in the Feieryun response header `fpw-header`
        ```
        forward_header = json.loads(r.headers["fpw-header"])
        ```

     - The visitor's request body will be returned in binary data in the Feieryun response body
        ```
        forward_body = r.content
        ```

     - The visitor's request will be assigned a unique `fpw-id`, which will be used in subsequent reply requests to identify the request
        ```
        fpw_id = r.headers["fpw-id"]
        ```

     - The visitor's request IP address, request address, and request method will be returned in the Feieryun response header `fpw-ip`, `fpw-url`, and `fpw-method`
        ```
        user_ip = r.headers["fpw-ip"]
        forward_url = r.headers["fpw-url"]
        forward_method = r.headers["fpw-method"]
        ```

2. Forward the visitor's request information to the local service
    ```
    r = requests.request(forward_method, forward_url, headers=fpw_header, data=fpw_body)
    ```

3. Forward the response information of the local service to Feieryun
    Put the response header and response body of the local service into     the Feieryun request header and request body respectively, and send     them to Feieryun
    ```python
    url = 'https://' + FPW_HOST + '/'
    header = {
        'fpw-host': FPW_HOST,
        'fpw-token': FPW_TOKEN,

        'fpw-id': fpw_id, # Used to identify this request
        'fpw-status' = r.status_code, # Response status code of the  local service
        'fpw-header' = r.headers, # Response header of the local service

        'user-agent': 'php-worker-v1',
        'content-type': 'application/octet-stream'
    }
    body = r.content # Response body of the local service
    ```
4. Feieryun will send the response information of this request to the visitor, and this request will be suspended until a new visitor visits this domain name.

5. Repeat steps 1.3 - 4 until the program exits.
   
**Note: The POST request connection may be disconnected, in which case you need to resend the POST request. If there is no online worker, accessing the domain name will return the default Feieryun page.**