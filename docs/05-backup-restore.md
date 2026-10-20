# 05 —— 备份与恢复

## 备份（root 通道就绪后）

```bash
# p3 已执行（块设备 666）后：
bash post/backup_fw.sh 192.168.199.xxx:5555 ./fw_backup
```

- 20 个分区 gzip 镜像 + GPT 头 + `MANIFEST.txt`
- 强烈建议对关键分区做双端 sha256 校验：

```bash
adb -s <DEV> exec-out "dd if=/dev/block/mmcblk0p5 bs=4096 count=5120 2>/dev/null | busybox sha256sum"
python -c "import gzip,hashlib;h=hashlib.sha256();[h.update(b) for b in iter(lambda: gzip.open('fw_backup/boot.img.gz','rb').read(1048576),b'')];print(h.hexdigest())"
```

## 恢复单个分区（root）

```bash
gunzip -c fw_backup/boot.img.gz | adb shell "dd of=/dev/block/mmcblk0p5 bs=4096"
adb shell setprop ctl.start adbd     # 视分区而定
```

分区与块设备映射见备份目录 `MANIFEST.txt` 或
`ls -la /dev/block/platform/mstar_mci.0/by-name/`。

## 恢复被卸载的应用

见 `post/restore.sh`。

## 回到全新官方状态

- `post/restore.sh <DEV> all` 恢复全部组件
- 移除本项目产生的文件：
  ```bash
  adb shell rm /system/etc/init/pcroot.rc /system/etc/passwd    # p4/p3 的产物(需root)
  adb shell pm uninstall local.z7x.adb   # 卸载 ADB 开启器(会失去开机自启adbd)
  ```
- 或直接走官方路径：设置 → 系统 → 恢复出厂 / 官方 U 盘强刷包

## 完整回滚分区（危险）

若有全分区备份且块设备可写（p4 的 rc.sh 开机 chmod 666）：

```bash
for p in MBOOT:mccblk0p1 recovery:mmcblk0p4 boot:mmcblk0p5 ...; do
  gunzip -c fw_backup/${p%%:*}.img.gz | adb shell "dd of=/dev/block/${p##*:} bs=4096"
done
```

> 写错分区名 = 变砖。不确定就别写，先 `ls -l /dev/block/platform/mstar_mci.0/by-name/` 核对。
