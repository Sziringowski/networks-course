import socket
import threading
import os
import time

PROXY_HOST = "127.0.0.1"  # слушаем все доступные интерфейсы
PROXY_PORT = 8888       # порт для прокси-сервера

# Включать ли кэширование:
ENABLE_CACHE = True

# Папка для кеша
CACHE_FOLDER = "lab04/cache"

# Файл журнала
LOG_FILE = "lab04/proxy.log"

# Файл с "чёрным списком"
BLACKLIST_FILE = "lab04/blacklist.txt"

# Прочитаем чёрный список доменов/URL
def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return []
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

BLACKLIST = load_blacklist()

# Запись в лог
def write_log(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")
    print(message)

# Простой генератор ключа для кэширования
def cache_key(host, path):
    """
    Формируем имя файла-ключа для кэша.
    Упрощённо: заменяем недопустимые символы в пути.
    """
    key = f"{host}_{path}"
    return key.replace("/", "_").replace(":", "_").replace("?", "_")

# Сохранение в кэш
def save_to_cache(host, path, data):
    if not ENABLE_CACHE:
        return
    if not os.path.exists(CACHE_FOLDER):
        os.makedirs(CACHE_FOLDER)

    key = cache_key(host, path)
    cache_file = os.path.join(CACHE_FOLDER, key)
    with open(cache_file, "wb") as f:
        f.write(data)

# Получение из кэша (или None, если нет)
def load_from_cache(host, path):
    if not ENABLE_CACHE:
        return None
    key = cache_key(host, path)
    cache_file = os.path.join(CACHE_FOLDER, key)
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return f.read()
    return None

def is_blocked(url):
    """
    Проверяем, содержится ли домен или часть URL в чёрном списке.
    Можно усложнить логику парсинга домена, но для примера спроецируем через простую проверку подстроки.
    """
    for blocked_item in BLACKLIST:
        if blocked_item.lower() in url.lower():
            return True
    return False

def parse_request(request_data):
    """
    Простейший парсер первой строки заголовка HTTP: METHOD PATH VERSION
    Возвращаем метод, url/path и версию протокола.
    """
    lines = request_data.split(b"\r\n")
    request_line = lines[0].decode()
    parts = request_line.split()
    if len(parts) == 3:
        method, full_path, version = parts
    else:
        # В случае каких-то кривых запросов
        method = "GET"
        full_path = "/"
        version = "HTTP/1.1"

    # Выделим хост и реальный путь, если запрос сделан в виде http://host/... 
    # или просто /path, когда браузер уже настроен на прокси.
    host = None
    path = full_path

    # Иногда запрос приходит как http://www.example.com/...
    if full_path.startswith("http://"):
        # убираем http://
        without_http = full_path[7:]  
        # разбираем на хост + путь
        idx = without_http.find("/")
        if idx != -1:
            host = without_http[:idx]
            path = without_http[idx:]  # включая слеш
        else:
            host = without_http
            path = "/"
    else:
        # Иначе ищем заголовок "Host:"
        for line in lines[1:]:
            line_str = line.decode()
            if line_str.lower().startswith("host:"):
                # host: www.example.com
                host = line_str.split(":", 1)[1].strip()
                break

    if not host:
        # fallback
        host = "127.0.0.1"

    return method, host, path, version

def handle_client_connection(client_socket, client_address):
    try:
        # Считаем первые данные от клиента (заголовок)
        request = b""
        client_socket.settimeout(2)
        try:
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                request += chunk
                if b"\r\n\r\n" in request:
                    # достигли конца HTTP-заголовков
                    break
        except socket.timeout:
            pass

        if not request:
            client_socket.close()
            return

        method, host, path, version = parse_request(request)

        url_log = f"{method} http://{host}{path}"
        # Проверяем чёрный список
        if is_blocked(f"{host}{path}"):
            msg = ("HTTP/1.1 403 Forbidden\r\n"
                   "Content-Type: text/html\r\n"
                   "Connection: close\r\n\r\n"
                   "<html><body><h1>403 Forbidden</h1><p>Blocked by proxy.</p></body></html>")
            client_socket.sendall(msg.encode("utf-8"))
            client_socket.close()
            write_log(f"[BLOCKED] {url_log}")
            return

        if method not in ("GET", "POST"):
            # Для упрощённого варианта запрещаем все методы, кроме GET/POST
            msg = ("HTTP/1.1 501 Not Implemented\r\n"
                   "Content-Type: text/html\r\n"
                   "Connection: close\r\n\r\n"
                   "<html><body><h1>501 Not Implemented</h1></body></html>")
            client_socket.sendall(msg.encode("utf-8"))
            client_socket.close()
            write_log(f"[501 Not Implemented] {url_log}")
            return

        # Проверяем, есть ли в кэше (только для GET)
        if method == "GET":
            cached_data = load_from_cache(host, path)
            if cached_data is not None:
                # Отправляем из кэша
                try:
                    client_socket.sendall(cached_data)
                    client_socket.close()
                    write_log(f"[CACHE HIT] {url_log}")
                    return
                except:
                    pass

        # Если не отправили из кэша, скачиваем с сервера
        # Определяем host и порт (если указан)
        if ":" in host:
            split_host = host.split(":")
            real_host = split_host[0]
            try:
                real_port = int(split_host[1])
            except ValueError:
                real_port = 80
        else:
            real_host = host
            real_port = 80

        # Подключаемся к реальному серверу
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((real_host, real_port))

        # Восстанавливаем заголовок запроса и отсылаем реальному серверу
        modified_request = request
        # Убедимся, что "Connection: close" или "Connection: keep-alive" корректно выставлены по необходимости
        # (для учебного примера оставим как есть)
        server_socket.sendall(modified_request)

        # Считываем ответ от реального сервера
        response_data = b""
        server_socket.settimeout(5)
        try:
            while True:
                chunk = server_socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
        except socket.timeout:
            pass

        server_socket.close()

        # Записываем ответ в кэш (для GET)
        if method == "GET" and response_data:
            save_to_cache(host, path, response_data)

        # Отправляем ответ клиенту
        client_socket.sendall(response_data)
        client_socket.close()

        # Логируем результат
        # Поищем в ответе статус-код (например, "HTTP/1.1 200 OK")
        status_line = b""
        if response_data.startswith(b"HTTP/"):
            first_line = response_data.split(b"\r\n", 1)[0]
            status_line = first_line
        write_log(f"[OK] {url_log} => {status_line.decode(errors='ignore')}")
    except Exception as e:
        # Обработка ошибок
        err_msg = ("HTTP/1.1 500 Internal Server Error\r\n"
                   "Content-Type: text/html\r\n"
                   "Connection: close\r\n\r\n"
                   f"<html><body><h1>500 Internal Server Error</h1><p>{e}</p></body></html>")
        try:
            client_socket.sendall(err_msg.encode("utf-8"))
        except:
            pass
        client_socket.close()
        write_log(f"[ERROR] {str(e)}")

def start_proxy_server():
    # Создаём сокет и слушаем входящие подключения
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_socket.bind((PROXY_HOST, PROXY_PORT))
    proxy_socket.listen(100)
    print(f"Proxy server listening on {PROXY_HOST}:{PROXY_PORT}")

    while True:
        client_conn, client_addr = proxy_socket.accept()
        # Обрабатываем клиентов в отдельных потоках
        t = threading.Thread(target=handle_client_connection, args=(client_conn, client_addr))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    start_proxy_server()
