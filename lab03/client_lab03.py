import socket
import sys

def main():
    if len(sys.argv) != 4:
        print("Usage: python client.py <server_host> <server_port> <filename>")
        sys.exit(1)

    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]

    # Создаем TCP-сокет
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Подключаемся к серверу
        client_socket.connect((server_host, server_port))
        print(f"Connected to {server_host} on port {server_port}")

        # Формируем HTTP-запрос
        http_request = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}\r\n\r\n"
        client_socket.sendall(http_request.encode())

        # Получаем ответ от сервера
        response = b""
        while True:
            part = client_socket.recv(4096)
            if not part:
                break
            response += part

        # Декодируем ответ в строку
        print(response.decode())

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
