import socket
import struct
import time
import select
import os
import sys

def checksum(data: bytes) -> int:
    s = 0
    for i in range(0, len(data), 2):
        w = data[i] << 8
        if i+1 < len(data):
            w += data[i+1]
        s += w
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return (~s) & 0xffff

def build_icmp_echo(identifier: int, seq: int) -> bytes:
    header = struct.pack("!BBHHH", 8, 0, 0, identifier, seq)
    payload = struct.pack("!d", time.time())
    chksum = checksum(header + payload)
    return struct.pack("!BBHHH", 8, 0, chksum, identifier, seq) + payload

def parse_icmp_reply(packet: bytes):
    ver_ihl = packet[0]
    ihl = (ver_ihl & 0x0F) * 4
    icmp = packet[ihl:ihl+8]
    if len(icmp) < 8:
        return None
    icmp_type, icmp_code, _, recv_id, recv_seq = struct.unpack("!BBHHH", icmp)

    if icmp_type == 11:
        inner = packet[ihl+8:]
        inner_ver_ihl = inner[0]
        inner_ihl = (inner_ver_ihl & 0x0F) * 4
        icmp_inner = inner[inner_ihl:inner_ihl+8]
        if len(icmp_inner) < 8:
            return None
        _, _, _, orig_id, orig_seq = struct.unpack("!BBHHH", icmp_inner)
        return icmp_type, icmp_code, orig_id, orig_seq

    elif icmp_type == 0:
        return icmp_type, icmp_code, recv_id, recv_seq

    else:
        return None

def traceroute(dest_name: str, max_hops: int = 30, q_per_hop: int = 3, timeout: float = 2.0):
    try:
        dest_addr = socket.gethostbyname(dest_name)
    except socket.gaierror:
        print(f"can't solve {dest_name}")
        return

    print(f"traceroute to {dest_name} [{dest_addr}], max_hops={max_hops}, queries={q_per_hop}, timeout={timeout}s")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except PermissionError:
        print("requiered admin privilegies")
        return

    pid = os.getpid() & 0xFFFF
    seq = 0

    for ttl in range(1, max_hops + 1):
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        send_times = {}
        for i in range(q_per_hop):
            pkt = build_icmp_echo(pid, seq)
            send_times[seq] = time.time()
            sock.sendto(pkt, (dest_addr, 0))
            seq += 1

        addr_list = []
        rtts = []

        time_left = timeout
        while len(rtts) < q_per_hop and time_left > 0:
            start = time.time()
            ready = select.select([sock], [], [], time_left)[0]
            elapsed = time.time() - start
            time_left -= elapsed
            if not ready:
                break
            data, cur_addr = sock.recvfrom(1024)
            parsed = parse_icmp_reply(data)
            if not parsed:
                continue
            icmp_type, icmp_code, orig_id, orig_seq = parsed
            if orig_id != pid or orig_seq not in send_times:
                continue
            rtt = (time.time() - send_times[orig_seq]) * 1000
            addr_list.append(cur_addr[0])
            rtts.append(rtt)

        if addr_list:
            hop_ip = addr_list[0]
            try:
                host = socket.gethostbyaddr(hop_ip)[0]
            except socket.herror:
                host = hop_ip
        else:
            hop_ip = None
            host = "*"

        line = []
        for i in range(len(rtts)):
            line.append(f"{rtts[i]:.1f} (ms)")
        line += ["*"] * (q_per_hop - len(rtts))

        print(f"{ttl:2d}  {host:<40}  {'  '.join(line)}")

        if hop_ip == dest_addr:
            print("arrived to target")
            break

    sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"use: {sys.argv[0]} <host> [max_hops] [queries_per_hop] [timeout]")
        sys.exit(1)
    host = sys.argv[1]
    mh = int(sys.argv[2]) if len(sys.argv) >= 3 else 30
    qp = int(sys.argv[3]) if len(sys.argv) >= 4 else 3
    to = float(sys.argv[4]) if len(sys.argv) >= 5 else 2.0
    traceroute(host, mh, qp, to)