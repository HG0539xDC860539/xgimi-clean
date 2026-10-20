#!/usr/bin/env bash
# restore.sh —— 恢复被卸载/禁用的组件
# 用法: bash restore.sh <投影仪IP>:5555 [all|adservice|atmosphere|screensaver|datareporter|activitypage|upgrade]
set -e
DEV="${1:?用法: bash restore.sh <IP>:5555 [all|组件名]}"
WHAT="${2:-all}"
adb connect "$DEV" || true

restore() { echo "--- 恢复 $1"; adb -s "$DEV" shell "cmd package install-existing --user 0 $1" || echo "  (可能本就不存在)"; }

case "$WHAT" in
  all)
    for p in com.xgimi.adservice com.xgimi.atmosphere com.xgimi.screensaver \
             com.xgimi.datareporter com.xgimi.activitypage; do restore "$p"; done
    echo "--- 重新启用系统升级"
    adb -s "$DEV" shell "pm enable com.xgimi.upgrade" || true
    ;;
  upgrade) adb -s "$DEV" shell "pm enable com.xgimi.upgrade" || true ;;
  *) restore "$WHAT" ;;
esac
echo "== 完成 =="
