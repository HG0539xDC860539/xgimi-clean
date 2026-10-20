#!/usr/bin/env python3
"""scan_ports.py —— 投影仪端口扫描 (TCP 全端口 + 常见 UDP 提示)"""
import socket
import concurrent.futures
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.199.177"


def check(port, timeout=1.5):
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((HOST, port))
        try:
            s.settimeout(0.5)
            data = s.recv(64)
        except Exception:
            data = b""
        s.close()
        return port, data
    except Exception:
        return None


def main():
    print(f"扫描 {HOST} TCP 1-65535 ...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=500) as ex:
        for r in ex.map(check, range(1, 65536)):
            if r:
                results.append(r)
    for port, data in sorted(results):
        print(f"{port:<6}/tcp OPEN  banner={data!r}")
    print("""
提示 (极米 GMUI 常见端口):
  8080/tcp  = 设置App集成的 Android Debug Database 调试服务 (com.android.newsettings, 厂商固件中开启)
  9987/tcp  = 腾讯视频 WebSocket
  5555/tcp  = adbd (未开启时 closed; 用 z7x-adb 开启器)
  22346/udp = 工厂自动化 AutoServer (需 vendor.xgimi.system.serial_debug=1)
""")


if __name__ == "__main__":
    main()
