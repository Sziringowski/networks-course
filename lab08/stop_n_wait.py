import socket
import struct
import random
import time
import os

def compute_checksum(data):
    sum = 0
    data = bytes(data)
    if len(data) % 2 != 0:
        data += b'\x00'
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        sum += word
        sum = (sum & 0xffff) + (sum >> 16)
    return ~sum & 0xffff

def verify_checksum(data, checksum):
    sum = checksum
    data = bytes(data)
    if len(data) % 2 != 0:
        data += b'\x00'
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        sum += word
        sum = (sum & 0xffff) + (sum >> 16)
    return sum == 0xffff

def create_data_packet(seq_num, data):
    header = bytes([seq_num])
    header_and_data = header + data
    checksum = compute_checksum(header_and_data)
    packet = struct.pack('!BH', seq_num, checksum) + data
    return packet

def create_ack_packet(ack_num):
    data = bytes([ack_num])
    checksum = compute_checksum(data)
    packet = struct.pack('!BH', ack_num, checksum)
    return packet

def parse_data_packet(packet):
    seq_num = packet[0]
    checksum = struct.unpack_from('!H', packet, 1)[0]
    data = packet[3:]
    header_and_data = packet[0:1] + data
    return seq_num, checksum, data, header_and_data

def parse_ack_packet(packet):
    ack_num = packet[0]
    checksum = struct.unpack_from('!H', packet, 1)[0]
    data = packet[0:1]
    return ack_num, checksum, data

def send_file(filename, sock, address, timeout, packet_loss_prob):
    chunk_size = 128
    with open(filename, 'rb') as f:
        data = f.read()
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    chunks.append(b'')
    current_seq = 0
    for chunk in chunks:
        while True:
            packet = create_data_packet(current_seq, chunk)
            if random.random() < packet_loss_prob:
                print(f"Пакет {current_seq} потерян при отправке")
            else:
                sock.sendto(packet, address)
                print(f"Отправлен пакет {current_seq}")
            
            ack_received = False
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    sock.settimeout(timeout - (time.time() - start_time))
                    ack_packet, _ = sock.recvfrom(65535)
                    ack_num, checksum, ack_data = parse_ack_packet(ack_packet)
                    if verify_checksum(ack_data, checksum) and ack_num == current_seq:
                        print(f"Получен ACK {ack_num}")
                        ack_received = True
                        break
                except socket.timeout:
                    continue
            if ack_received:
                current_seq = 1 - current_seq
                break
            else:
                print(f"Timeout, повторная отправка пакета {current_seq}")

def receive_file(filename, sock, timeout, packet_loss_prob):
    expected_seq = 0
    with open(filename, 'wb') as f:
        while True:
            try:
                sock.settimeout(timeout)
                packet, addr = sock.recvfrom(1024)
                if random.random() < packet_loss_prob:
                    print("Пакет данных потерян при приеме")
                    continue
                seq_num, checksum, data, header_and_data = parse_data_packet(packet)
                if not verify_checksum(header_and_data, checksum):
                    print("Ошибка контрольной суммы, пакет отброшен")
                    continue
                print(f"Получен пакет {seq_num}, ожидался {expected_seq}")
                if seq_num == expected_seq:
                    if len(data) == 0:
                        print("Получен конец передачи")
                        break
                    f.write(data)
                    ack_packet = create_ack_packet(seq_num)
                    if random.random() < packet_loss_prob:
                        print("ACK потерян при отправке")
                    else:
                        sock.sendto(ack_packet, addr)
                        print(f"Отправлен ACK {seq_num}")
                    expected_seq = 1 - expected_seq
                else:
                    ack_packet = create_ack_packet(seq_num)
                    if random.random() < packet_loss_prob:
                        print("Повторный ACK потерян")
                    else:
                        sock.sendto(ack_packet, addr)
                        print(f"Отправлен повторный ACK {seq_num}")
            except socket.timeout:
                print("Таймаут приема, ожидание новых пакетов...")
                continue

def main():
    import sys
    if len(sys.argv) < 2:
        print("Использование:")
        print("Сервер: python lab08/stop_n_wait.py server <port> <folder_to_save>")
        print("Клиент: python lab08/stop_n_wait.py client <server_ip> <port> <fail_to_send>")
        return

    role = sys.argv[1]
    if role == 'server':
        port = int(sys.argv[2])
        save_dir = sys.argv[3]
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', port))
        print(f"Сервер запущен на порту {port}")
        filename = os.path.join(save_dir, 'received_file')
        receive_file(filename, sock, timeout=2, packet_loss_prob=0.3)
        print("Файл успешно получен")
    elif role == 'client':
        server_addr = sys.argv[2]
        server_port = int(sys.argv[3])
        filename = sys.argv[4]
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_file(filename, sock, (server_addr, server_port), timeout=2, packet_loss_prob=0.3)
        print("Файл успешно отправлен")

if __name__ == '__main__':
    main()