#!/usr/bin/env bash
# backup_fw.sh —— 全量固件分区备份 (需先完成 p3: 块设备 chmod 666)
# backup_fw.sh — full firmware-partition backup (requires p3 first: block devices chmod 666)
# 用法 / Usage: bash backup_fw.sh <IP>:5555 [输出目录|output dir]
set -e
DEV="${1:?用法 / usage: bash backup_fw.sh <IP>:5555 [output dir]}"
OUT="${2:-./fw_backup_$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$OUT"

# name:device:size_kb   (跳过 cache=p13 / userdata=p22)
PARTS="
gpt_head:mmcblk0:1024
MBOOT:mmcblk0p1:3072
MPOOL:mmcblk0p2:2048
misc:mmcblk0p3:512
recovery:mmcblk0p4:32768
boot:mmcblk0p5:20480
optee:mmcblk0p6:6144
armfw:mmcblk0p7:64
RTPM:mmcblk0p8:256
dtb:mmcblk0p9:1024
frc:mmcblk0p10:1024
cm4:mmcblk0p11:512
system:mmcblk0p12:896000
vendor:mmcblk0p14:1203200
tvservice:mmcblk0p15:184320
tvconfig:mmcblk0p16:25600
tvdatabase:mmcblk0p17:8192
tvcustomer:mmcblk0p18:16384
tvcertificate:mmcblk0p19:8192
xgimidatabase:mmcblk0p20:20480
xgimiconfig:mmcblk0p21:25600
"

adb connect "$DEV" || true
backup() {
  local name=$1 dev=$2 kb=$3
  echo "--- $name ($kb KB) $(date +%H:%M:%S)"
  adb -s "$DEV" exec-out \
    "dd if=/dev/block/$dev bs=4096 count=$((kb/4)) 2>/dev/null | gzip -1" \
    > "$OUT/$name.img.gz"
  echo "    -> $(stat -c %s "$OUT/$name.img.gz") bytes"
}

echo "$PARTS" | grep -v '^$' | while IFS=: read -r n d k; do
  [ -n "$n" ] && backup "$n" "$d" "$k"
done

cat > "$OUT/MANIFEST.txt" << 'EOF'
分区映射 (/dev/block/platform/mstar_mci.0/by-name):
  gpt_head=mmcblk0前1MB(含GPT) MBOOT=p1 MPOOL=p2 misc=p3 recovery=p4
  boot=p5 optee=p6 armfw=p7 RTPM=p8 dtb=p9 frc=p10 cm4=p11
  system=p12 cache=p13(未备份) vendor=p14 tvservice=p15 tvconfig=p16
  tvdatabase=p17 tvcustomer=p18 tvcertificate=p19
  xgimidatabase=p20 xgimiconfig=p21 userdata=p22(未备份)
恢复示例(root):
  gunzip -c boot.img.gz | adb shell "dd of=/dev/block/mmcblk0p5 bs=4096"
EOF

echo "== 备份完成 / backup finished: $OUT =="
du -sh "$OUT"
echo "建议对关键分区做双端 sha256 校验 / recommended: verify sha256 of key partitions on both ends (docs/05-backup-restore.md)"
