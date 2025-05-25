from client.client import QuoridorClient


def main():
    # 创建客户端实例
    client = QuoridorClient(
        server_url="http://192.168.1.102:5071",  # 使用本地服务器地址
        # server_url="http://127.0.0.1:5100",
        name="AI_Player1",  # 使用正确的玩家名称
        password="password"  # 使用正确的密码
    )
    
    # 运行客户端
    client.run()

if __name__ == "__main__":
    main()