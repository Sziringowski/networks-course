import os
import sys
import time
import socket
import struct
import select
import math
import threading
from ctypes import windll

class ICMPPinger:
    def __init__(self, target_host):
        self.target_host = target_host
        self.target_ip = socket.gethostbyname(target_host)
        self.sequence = 0
        self.identifier = os.getpid() & 0xFFFF
        self.sent_packets = 0
        self.received_packets = 0
        self.rtt_list = []
        self.running = True
        self.count = 10
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        self.sock.settimeout(1)
        
        self.receiver_thread = threading.Thread(target=self.receive_ping)
        self.receiver_thread.start()

    def _calculate_checksum(self, data):
        sum = 0
        data = bytes(data)
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                word = (data[i] << 8) + data[i + 1]
            else:
                word = (data[i] << 8) + 0
            sum += word
        sum = (sum >> 16) + (sum & 0xffff)
        sum += sum >> 16
        return (~sum) & 0xffff

    def _create_icmp_packet(self):
        timestamp = struct.pack('d', time.time())
        data = timestamp + (b'\x00' * 48)
        header = struct.pack('!BBHHH', 8, 0, 0, self.identifier, self.sequence)
        checksum = self._calculate_checksum(header + data)
        header = struct.pack('!BBHHH', 8, 0, checksum, self.identifier, self.sequence)
        self.sequence += 1
        return header + data

    def _parse_icmp_response(self, packet):
        icmp_header = packet[20:28]
        icmp_type, code, _, received_id, sequence = struct.unpack('!BBHHH', icmp_header)
        
        if icmp_type != 0 or code != 0 or received_id != self.identifier:
            return None
            
        try:
            timestamp = struct.unpack('d', packet[28:36])[0]
            rtt = (time.time() - timestamp) * 1000
            return rtt
        except struct.error:
            return None

    def send_ping(self):
        packet = self._create_icmp_packet()
        try:
            self.sock.sendto(packet, (self.target_ip, 0))
            self.sent_packets += 1
        except socket.error as e:
            print(f"send error {e}")

    def receive_ping(self):
        while self.running:
            try:
                packet, addr = self.sock.recvfrom(1024)
                if addr[0] != self.target_ip:
                    continue
                rtt = self._parse_icmp_response(packet)
                if rtt is not None:
                    self.received_packets += 1
                    self.rtt_list.append(rtt)
                    print(f"host: {self.target_ip}; time: {rtt:.2f} (ms)")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"recieve error: {e}")

    def run(self):
        print(f"PING {self.target_host} ({self.target_ip})")
        try:
            for _ in range(0, self.count):
                self.send_ping()
                time.sleep(1)

            self.running = False
            self.receiver_thread.join()
            self.sock.close()
            
            print("\n--- ping statistics ---")
            if self.sent_packets == 0:
                print("no packages sent")
                return
                
            loss_percent = ((self.sent_packets - self.received_packets) / self.sent_packets) * 100
            print(f"send: {self.sent_packets}, recieved: {self.received_packets}, "
                f"lost: {loss_percent:.2f}%")
            
            if self.received_packets > 0:
                min_rtt = min(self.rtt_list)
                avg_rtt = sum(self.rtt_list) / len(self.rtt_list)
                max_rtt = max(self.rtt_list)
                std_dev = math.sqrt(sum((x - avg_rtt)**2 for x in self.rtt_list)/len(self.rtt_list))
                print(f"RTT (ms): min: {min_rtt:.2f}, mean: {avg_rtt:.2f}, max: {max_rtt:.2f}, std: {std_dev:.2f}")
        except Exception as e:
                print(f"error {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("using: python lab10/ping.py <host>")
        sys.exit(1)
        
    if windll.shell32.IsUserAnAdmin() == 0:
        print("requies admin's rules")
        sys.exit(1)
        
    target = sys.argv[1]
    pinger = ICMPPinger(target)
    pinger.run()