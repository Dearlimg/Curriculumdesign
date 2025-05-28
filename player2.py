from client.client import QuoridorClient


def main():
    client = QuoridorClient(
        server_url="http://192.168.83.201:5071",
        # server_url="http://127.0.0.1:5100",
        name="BatMan",
        password="123"
    )

    client.run()

if __name__ == "__main__":
    main()