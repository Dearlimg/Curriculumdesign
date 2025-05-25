from client.client import QuoridorClient


def main():
    client = QuoridorClient(
        server_url="http://192.168.1.102:5071",
        # server_url="http://127.0.0.1:5100",
        name="BatMan",
        password="password"
    )

    client.run()

if __name__ == "__main__":
    main()