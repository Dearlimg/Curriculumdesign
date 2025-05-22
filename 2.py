
from client import client
from client.client import QuoridorClient


def main():
    # 创建客户端实例
    client = QuoridorClient(
        server_url="http://localhost:5100",  # 根据实际情况修改服务器地址
        name="AI_Player2",
        password="password",
    )

    # 运行客户端
    client.run()

if __name__ == "__main__":
    main()