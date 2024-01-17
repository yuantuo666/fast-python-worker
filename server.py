import tornado.ioloop
import tornado.web
import json
import time
import random
import asyncio
import concurrent.futures as Executor

# 全局请求队列
request_queue = asyncio.Queue()
response_queue = asyncio.Queue()

online_server = []

response_futures = {}

class ServerClientHandler(tornado.web.RequestHandler):
    async def prepare(self):
        if "fpw-host" not in self.request.headers.keys() or "fpw-token" not in self.request.headers.keys():
            self.set_status(403)
            self.write("Forbidden")
            self.finish()
            return
        
        online_server.append({
            "host": self.request.headers["fpw-host"],
            "token": self.request.headers["fpw-token"],
            "ip": self.request.remote_ip,
        })
    
    async def on_connection_close(self) -> None:
        online_server.pop(0)
        return super().on_connection_close()

    async def post(self):
        # 处理服务器客户端的POST请求
        print("> new online_server for", self.request.headers["fpw-host"], len(online_server))
        if "fpw-status" in self.request.headers.keys():
            response_data = {
                "rid": self.request.headers["fpw-rid"],
                "http_code": self.request.headers["fpw-status"],
                "headers": json.loads(self.request.headers["fpw-header"]),
                "body": self.request.body,
            }
            
            feature = response_futures.get(response_data["rid"])
            if feature:
                feature.set_result(response_data)
                del response_futures[response_data["rid"]]
            else:
                print("No feature found")

        # 等待并获取用户客户端的请求
        try:
            user_request = await asyncio.wait_for(request_queue.get(), timeout=180)
        except asyncio.TimeoutError:
            print("TimeoutError")
            online_server.pop(0)
            return
        self.set_status(200)
        self.set_header("fpw-rid", user_request["rid"])
        self.set_header("fpw-header", json.dumps(user_request["headers"]))
        self.set_header("fpw-url", user_request["url"])
        self.set_header("fpw-method", user_request["method"])
        self.set_header("fpw-ip", user_request["ip"])
        self.write(user_request["body"])
        self.finish()
        online_server.pop(0)


class ClientHandler(tornado.web.RequestHandler):
    async def prepare(self):
        print("> online_server:", len(online_server))
        if len(online_server) == 0:
            self.set_status(500)
            self.write("No server available")
            self.finish()
            return
        
        self.rid = "%s-%s" % (int(time.time() * 1000), random.randint(100000, 999999))

        # 处理用户客户端的任意请求
        request_data = {
            "rid": self.rid,
            "method": self.request.method,
            "url": self.request.uri,
            "headers": dict(self.request.headers),
            "body": self.request.body,
            "ip": self.request.remote_ip, # 用户客户端的IP地址
        }
        await request_queue.put(request_data)

    async def get(self, path):
        # 等待服务器客户端的响应
        print("> rid:", self.rid)
        feature = asyncio.Future()
        response_futures[self.rid] = feature
        response = await feature
        self.set_status(int(response["http_code"]))
        for key, value in response["headers"].items():
            self.set_header(key, value)
        self.write(response["body"])
        self.finish()

    async def post(self, path):
        # 等待服务器客户端的响应
        response = await response_queue.get()
        self.write(response)
        self.finish()


def make_app():
    return tornado.web.Application(
        [
            (r"/server-client", ServerClientHandler),
            (r"/(.*)", ClientHandler),
        ]
    )

if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()
