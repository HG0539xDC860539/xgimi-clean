# 02 —— 固件离线解包

> **EN abstract:** How to unpack XGIMI's official USB recovery image (`.bin`) offline down to system/vendor partitions, and what the 2023 firmware revealed about ADB properties (network ADB used to be on by default).


极米官方"USB 强刷包"（如 `XGIMI_IRONMAN_XK03U.bin`）是一个
**头部 ASCII 脚本 + 裸数据**的容器，由 MBoot 在强刷时解释执行。

## 结构

```
0x0000  #-------------USB Upgrade Bin Info--------------  (ASCII 脚本头)
        # Device : ironman
        # Build TIME : 2023-07-21 19:27:21
        ...
        # File Partition: set_partition      ← 分区表
        mmc create system 0x36B00000
        ...
        # File Partition: mboot              ← 每个分区: filepartload <addr> $(UpgradeImage) <偏移> <大小>
        filepartload 0x28A00000 $(UpgradeImage) 0x4000 0x24000
        mmc write.boot ...
        # File Partition: system             ← sparse 分段写入
        filepartload ... 0x2f3e000 0x946937c
        sparse_write mmc 0x28A00000 system $(filesize)
        ...
        % <- this is end of script symbol
数据区按脚本中的偏移排布
```

## 关键坑：system/vendor 是"分段 sparse"

每个分段的 sparse header 中 `total_blks` 都等于**完整分区大小**，
未覆盖区域用 `DON'T CARE` 块跳过。因此：

- ❌ 直接把各段 `simg2img` 后拼接 → 得到 N 倍大小的错误镜像
- ✅ 必须按块游标合并（本仓库 `tools/parse_upgrade_bin.py merge` 已实现）

每段 header 还有 12 字节 chunk 头（type/res/size + 4 字节额外字段）。

## 常用命令

```bash
# 列出分区与完整性
python tools/parse_upgrade_bin.py list XGIMI_IRONMAN_XK03U.bin

# 提取 boot (Android boot image, 可 unpack ramdisk)
python tools/parse_upgrade_bin.py extract XGIMI_IRONMAN_XK03U.bin boot boot.img

# 合并 system / vendor 为 ext4
python tools/parse_upgrade_bin.py merge XGIMI_IRONMAN_XK03U.bin system system.img
python tools/parse_upgrade_bin.py merge XGIMI_IRONMAN_XK03U.bin vendor vendor.img

# 浏览 ext4 (WSL: debugfs, 无需挂载)
debugfs -R "ls -p /priv-app" vendor.img
debugfs -R "cat /build.prop" system.img
```

## 值得注意的发现

- `vendor/build.prop`（2023 版）：
  ```properties
  service.adb.tcp.port=5555
  persist.adb.tcp.port=5555
  persist.service.adb.enable=1
  ro.adb.secure=0        # 被 ramdisk prop.default(ro.adb.secure=1) 覆盖
  persist.sys.usb.config=none
  ```
- bootargs：`androidboot.selinux=permissive`（**平台全局 SELinux 宽容**）
- 升级脚本 `set_config` 段里有 `setenv verify n`（未验证重打包可行性）
- vendor 分区是广告全家桶所在（`/vendor/priv-app/XgimiAdService` 等）
