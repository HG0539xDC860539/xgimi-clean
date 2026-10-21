#!/usr/bin/env bash
# debloat.sh —— 极米 NEW Z6X 广告组件卸载 (全部可恢复)
# debloat.sh — remove the ad components on an XGIMI NEW Z6X (all reversible)
# 用法 / Usage: bash debloat.sh <投影仪IP|projector IP>:5555
set -e
DEV="${1:?用法 / usage: bash debloat.sh <IP>:5555}"
adb connect "$DEV" || true
[ "$(adb devices | grep -c "$DEV.*device$")" -ge 1 ] || { echo "设备未授权/未连接 / device not authorised or connected"; exit 1; }

echo "== 广告组件卸载 (--user 0, 可恢复) / removing ad components (--user 0, reversible) =="
for p in \
  com.xgimi.adservice \
  com.xgimi.atmosphere \
  com.xgimi.screensaver \
  com.xgimi.datareporter \
  com.xgimi.activitypage
do
  echo "--- $p"
  adb -s "$DEV" shell "pm uninstall --user 0 $p" || true
done

echo "== 禁用系统升级 (防 OTA 回滚广告; 恢复: pm enable com.xgimi.upgrade) / disabling OTA updater (re-enable with: pm enable com.xgimi.upgrade) =="
adb -s "$DEV" shell "pm disable-user --user 0 com.xgimi.upgrade" || true

echo "== 完成. 验证 / done. verify: =="
adb -s "$DEV" shell "pm list packages --user 0 | grep -E 'adservice|atmosphere|screensaver|datareporter|activitypage' || echo '广告组件已全部移除 / ad components all removed'"
