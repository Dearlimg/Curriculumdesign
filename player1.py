from client.client import QuoridorClient


def main():
    client = QuoridorClient(
        server_url="http://127.0.0.1:5071",
        # server_url="http://127.0.0.1:5100",
        name="Joker",
        password="123"
    )

    client.run()

if __name__ == "__main__":
    main()