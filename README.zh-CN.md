# XGIMI Clean —— 极米投影仪去广告 / Root 工具包

[简体中文](README.zh-CN.md) | [English](README.md)

> 适用机型：极米 **NEW Z6X**（IRONMAN / XK03U / m7221 平台，GMUI）
> 理论兼容：同平台同年代的 Z6X Pro / Z7X / H 系列等 GMUI 机型（未逐一验证）
> 原则：**不动系统分区、不刷机、全部操作可逆**，保留官方最新固件与界面

<p align="center"><img src="docs/img/new-z6x.jpg" width="720" alt="极米 NEW Z6X 实机"></p>

---

## 这是什么

极米 GMUI 系统内置了完整的广告与遥测体系（广告服务、氛围壁纸、屏保广告、活动弹窗、数据上报），
且新版固件阉割了用户侧的 ADB 开关、系统也没有开发者模式入口。

本项目提供一条**纯局域网 / U 盘**的净化路线：

1. 利用系统内置的售后 SSH 机制（`xgimi_ssh` 服务）拿到 **root 任意命令执行**
2. 写入你自己的 ADB 授权密钥，让 `adb connect` 直接可用
3. 用 `pm uninstall --user 0` 卸载广告组件（可随时恢复）
4. 全量备份当前固件分区，随时可完整还原

```
U盘装一个终端 App（10 秒）
        │
        ▼
写入 /data/ssh/authorized_keys + setprop   ← g 脚本
        │
        ▼
xgimi_ssh.sh (root) 启动 sshd                ← 系统自己的售后逻辑
        │
        ▼
params + ProxyCommand = root 维护命令        ← p2/p3 协助脚本
        │
        ▼
ADB 授权 ✓ → pm uninstall 广告全家桶 ✓ → 固件备份 ✓
```

## 目录结构

```
docs/        完整技术文档（设备盘点、固件解包、root机制、净化清单、备份恢复）
tools/       固件解析、端口扫描等辅助脚本
scripts/     g / p2 / p3 / p4 生成器（make_scripts.py 一键生成，写入你自己的密钥）
post/        净化、备份、恢复脚本 + 广告域名屏蔽清单
```

## 快速开始

### 0. 准备
- 一台与投影仪同网段的电脑（装有 Python 3、adb）
- 一只 U 盘
- 两个 APK 都在本仓库 [`third_party/`](third_party/) 目录：
  - **TermOne Plus**（GPL-3.0）—— 终端模拟器，无需联网初始化
  - **Z7X-ADB 开启器**（MIT）—— 让 adbd 监听 5555

### 1. 生成你自己的维护脚本
```bash
python scripts/make_scripts.py
# 自动生成 ssh 密钥对（若无）并产出 scripts/out/{g,p2,p3,p4}
# 同时生成 scripts/out/serve/ 目录，内含全部待下发文件
```

### 2. 起本地 HTTP 服务（供投影仪拉取脚本）
```bash
cd scripts/out/serve
python -m http.server 8000 --bind 0.0.0.0   # 记下你电脑的 IP，下文称 <PC_IP>
```

### 3. 投影仪上安装并打开 TermOne Plus（U 盘安装）

### 4. 开启网络 ADB（Z7X-ADB 开启器）
安装 `third_party/Z7X-ADB-v1.1.0.apk`（U 盘安装后打开运行一次）。
> 本步骤给出 `persist.adb.tcp.port=5555` 等属性，使 adbd 监听 5555。
> 此时 `adb connect <IP>:5555` 会显示 `unauthorized`——正常，下一步解决。

### 5. 完成 root 授权（在 TermOne 里执行）
```sh
busybox wget -O g http://<PC_IP>:8000/g;sh g      # 启动厂商 root sshd
busybox wget -O p2 http://<PC_IP>:8000/p2;sh p2   # 以 root 执行维护脚本
busybox wget -O p3 http://<PC_IP>:8000/p3;sh p3   # adb 授权 + 块设备可读
```
看到 `p3 done` 后，电脑上：
```bash
adb connect <投影仪IP>:5555     # 这次是 device（已授权）
```

### 6. 净化
```bash
bash post/debloat.sh <投影仪IP>:5555          # 卸载广告组件 + 禁用OTA
bash post/backup_fw.sh <投影仪IP>:5555        # 全量固件备份（强烈建议先做）
```

### 7.（推荐）安装永久 root 触发器
```sh
busybox wget -O p4 http://<PC_IP>:8000/p4;sh p4   # TermOne 里执行
```
之后任何时候：`adb shell "echo '你的命令' > /data/local/tmp/rc.sh; setprop pc.root.go 1"` 即可以 root 执行。

## 卸载了什么

| 包名 | 作用 | 处置 |
|---|---|---|
| com.xgimi.adservice | 广告服务主程序 | 卸载 |
| com.xgimi.atmosphere | 氛围/音乐墙广告 | 卸载 |
| com.xgimi.screensaver | 屏保广告 | 卸载 |
| com.xgimi.datareporter | 数据遥测上报 | 卸载 |
| com.xgimi.activitypage | 活动页/弹窗广告 | 卸载 |
| com.xgimi.upgrade | 系统升级（防OTA回滚） | 禁用（可逆） |

全部为 `--user 0` 级别，恢复命令见 `post/restore.sh`。

## 技术原理（简版，详见 docs/）

- **root 机制**：GMUI 固件预装了厂商售后维护服务 `/vendor/bin/xgimi_ssh.sh`——
  `service xgimi_ssh`（init.xgimi.rc，**root**、`oneshot`）执行该脚本；
  脚本读取属性 `xgimi.remoteDebug.on`，为 `true` 时启动 root sshd，
  并执行 `/system/bin/ssh $(cat /data/ssh/params)`。
  `/data/ssh` 目录为 **0777**，任何 App 可写 `params`；
  于是 `params = -oProxyCommand=/data/ssh/p 127.0.0.1` 令 root 的 ssh 客户端
  在连接前执行设备所有者准备的维护脚本 → **以 root 权限执行维护命令**。
- **ADB 授权**：root 执行 `echo <adbkey.pub> >> /data/misc/adb/adb_keys`。
- 原版固件中 USB/网络 ADB 本就是售后依赖通道（vendor/build.prop 含
  `persist.adb.tcp.port=5555`），仅新版移除了用户侧开关。

## 常见问题

**为什么装了 Z7X-ADB、ADB 显示已开启，连上却还是 unauthorized？**
Z7X-ADB 只让 adbd 开始监听；本机 adbd 运行在安全模式（ro.adb.secure=1），
需要你的公钥写入 /data/misc/adb/adb_keys，而 GMUI 没有授权弹窗、该文件仅 root 可写。
g/p2 脚本就是借 xgimi_ssh root 服务把你的公钥写进去，从里面开门。
详见 [docs/06-faq.md](docs/06-faq.md)。

## 风险与免责声明

- 本项目所有能力均来自设备厂商在固件中**预装并预留**的调试/售后维护接口
  （xgimi_ssh 服务、调试属性、工程菜单等），本项目不包含、也不提供任何
  绕过厂商安全设计的代码；全部操作在**设备所有者本人授权**下进行
- 仅适用于**你自己的设备**。未经设备所有者授权对他人设备进行操作
  可能违反《网络安全法》《刑法》等相关法律法规
- 去除预装组件可能违反厂商服务条款，可能影响保修，请自行评估
- 所有系统级操作前请先运行 `post/backup_fw.sh` 做全量备份
- `pm uninstall --user 0` 均可用 `cmd package install-existing` 恢复；
  `com.xgimi.upgrade` 禁用后若需OTA升级先 `pm enable`
- 请勿将本项目用于盗版、规避付费等用途

## 致谢

- [code-ant/z7x-adb](https://github.com/code-ant/z7x-adb) —— ADB 属性开启思路与开启器 APK
- [TermOne Plus](https://f-droid.org/en/packages/com.termoneplus/)（F-Droid）
- 所有折腾过极米设备的 ZNDS / 投影网 前辈

## License

MIT
