from client.client import QuoridorClient


def main():
    # 创建客户端实例
    client = QuoridorClient(
        server_url="http://127.0.0.1:5100",  # 使用正确的服务器地址
        name="AI_Player1",
        password="password"  # 使用正确的密码
    )
    
    # 运行客户端
    client.run()

if __name__ == "__main__":
    main()