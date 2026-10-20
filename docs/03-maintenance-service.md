# 03 —— Root 权限获取机制（厂商维护服务）

## 目标

获取 **root 权限的维护命令执行能力**，然后只做一件事：
把设备所有者自己的 adb 公钥写入 `/data/misc/adb/adb_keys`，
让 `adb connect <IP>:5555` 直接可用
（GMUI 没有授权弹窗，传统"允许USB调试"对话框不存在，见 FAQ Q1）。

全部能力均来自**厂商固件中预装并预留的调试/售后机制**，
由设备所有者在自己的设备上启用。

## 机制分解

### ① adbd 监听：Z7X-ADB 开启器

GMUI 平台 SELinux 宽容（`androidboot.selinux=permissive`），
普通 App 执行 `Runtime.exec("setprop ...")` 即可：

```sh
setprop persist.adb.tcp.port 5555
setprop service.adb.tcp.port 5555
setprop persist.sys.usb.config adb
setprop sys.usb.config adb
setprop ctl.start adbd
```

感谢 [z7x-adb](https://github.com/code-ant/z7x-adb) 项目验证了这一点并提供现成 APK。
此时 `adb connect` 会停在 `unauthorized`（无弹窗可点），继续 ↓

### ② root sshd：厂商预留的售后维护服务

`/vendor/etc/init/hw/init.xgimi.rc`：

```rc
service xgimi_ssh /vendor/bin/xgimi_ssh.sh
    class main
    oneshot
    seclabel u:r:xgimi_ssh:s0      # 未声明 user/group → 以 root 运行
```

`/vendor/bin/xgimi_ssh.sh`（节选）：

```sh
AUTHORIZED_KEYS=/data/ssh/authorized_keys
mkdir /data/ssh; chmod 777 /data/ssh          # 0777！任何 App 可写
...
remotedebug=`getprop xgimi.remoteDebug.on`
case $remotedebug in
true)
/system/bin/sshd -f /system/etc/ssh/sshd_config -D &    # root sshd, :22
/system/bin/ssh $var          # var=$(cat /data/ssh/params)  ← 关键
;;
```

**第一段（g 脚本）**：任何 App 写 `/data/ssh/authorized_keys` + `setprop xgimi.remoteDebug.on true`
+ `setprop ctl.start xgimi_ssh` → root sshd 启动。
但直接使用 App 自写的 authorized_keys 会失败：文件属主是普通 App uid，
sshd StrictModes 校验不过（且 `/data` 属 system 0771 本身就过不了 safe_path）。

### ③ ProxyCommand：以 root 执行维护脚本

`xgimi_ssh.sh` 会执行 `/system/bin/ssh $var`，`$var` 读自 **/data/ssh/params（0777 目录，App 可写）**。
`/data` 分区未挂 noexec（fstab: `noatime,nosuid,nodev`），于是：

```sh
echo '-oProxyCommand=/data/ssh/p 127.0.0.1' > /data/ssh/params
# /data/ssh/p 为我们准备好的维护脚本 (chmod 755)
```

root 的 ssh 客户端在建立连接前会**先执行 ProxyCommand 指向的程序**——
即可以 root 身份运行设备所有者准备的维护脚本。
ssh 连接随后失败没有影响，脚本已执行完毕。

### ④ root 脚本做什么（p2）

```sh
echo '<你的ssh公钥>' > /data/ssh/authorized_keys
chown root:root /data/ssh/authorized_keys; chmod 600 ...
echo '<你的adb公钥>' >> /data/misc/adb/adb_keys        # ← 本项目最终目的
chown system:shell /data/misc/adb/adb_keys; chmod 640 ...
mount -o rw,remount /system                            # 临时解锁 /system 只读
echo 'StrictModes no' >> /system/etc/ssh/sshd_config
killall sshd; /system/bin/sshd -f /system/etc/ssh/sshd_config -D &
```

p3 追加：`/system/etc/passwd`（root 账户解锁，供 sshd getpwnam）+
`chmod 666 /dev/block/mmcblk0*`（供 shell dd 做固件备份）。

> 注：该移植版 sshd 对 root 账户的公钥认证仍可能拒绝（builtin getpwnam 判定锁定），
> 不影响主线——ADB 才是日常通道，root 随时可用 ③ 重新触发。

### ⑤ 持久化（p4，可选）

`/system` 已可写时安装自己的 init 服务：

```rc
# /system/etc/init/pcroot.rc
service pcroot /system/bin/sh /data/local/tmp/rc.sh
    class main
    disabled
on property:pc.root.go=1
    start pcroot
on property:sys.boot_completed=1
    start pcroot        # 开机自动跑 rc.sh（默认内容: chmod 666 块设备）
```

之后 `adb shell` 写 `/data/local/tmp/rc.sh` + `setprop pc.root.go 1` = 随时以 root 执行。

## 流程小结

| 步骤 | 执行者 | 权限 |
|---|---|---|
| 装 TermOne + z7x-adb（U盘） | 设备所有者 | - |
| g | TermOne(App) | App uid |
| p2/p3/p4 部署 | TermOne(App) | App uid |
| root 脚本执行 | xgimi_ssh.sh → ssh -oProxyCommand | **root** |
| adb connect | 电脑 | shell (已授权) |
| pm uninstall 广告 | adb shell | shell |
