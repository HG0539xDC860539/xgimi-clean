# 04 —— 净化清单

> **EN abstract:** The de-bloat list: what we uninstall (`--user 0`, reversible), what we disable, the hardware services you must NOT touch (keystone, ToF autofocus, HDMI player, MStar input stack, cross-checked against the overseas XGIMI DO-NOT-DISABLE lists in the cleanyourtv project), plus the tested third-party-launcher swap (EMOTN UI, `com.oversea.aslauncher`) and how to switch back to the stock GMUI home.


## 卸载（`pm uninstall --user 0`，可用 `cmd package install-existing --user 0` 恢复）

| 包名 | 作用 | 广告相关证据 |
|---|---|---|
| `com.xgimi.adservice` | 广告服务主程序 | API: `adapi.xgimi.com/api/v1/ad/`，请求 WRITE_SECURE_SETTINGS |
| `com.xgimi.atmosphere` | 氛围/音乐墙 | 资源域 `static.t.xgimi.com/ossWeb/` |
| `com.xgimi.screensaver` | 屏保广告 | 广告位下载 + umeng 遥测 |
| `com.xgimi.datareporter` | 数据遥测 | 全量行为上报 |
| `com.xgimi.activitypage` | 活动页/弹窗 | 开机弹窗、节日活动推广 |

## 禁用（可 `pm enable` 恢复）

| 包名 | 理由 |
|---|---|
| `com.xgimi.upgrade` | 系统升级。禁用以防 OTA 把广告装回来；想升级时先 enable |

## 保留（动了会坏功能，别乱删）

`com.xgimi.home`（桌面）、`com.xgimi.systemui / xgimiframeworkui / windowsystem`（UI）、
`com.xgimi.xgimiservice / gmservice / manager / vcontrol / config / msgcenter`（系统服务）、
`com.xgimi.filemanager`（文件管理）、`com.xgimi.wirelessscreen`（投屏）、
`com.xgimi.skin* / inuiserver`（皮肤主题）、`com.xgimi.autokst / tof`（校正）、
`com.xgimi.user / account / transfer`、语音/蓝牙/投屏相关全家。

以下硬件服务已对照 cleanyourtv 海外极米机型的 DO-NOT-DISABLE 清单交叉核实，
在本机（真机包快照）确认存在，**同样不要动**：

| 包名 | 作用 | 动了会怎样 |
|---|---|---|
| `com.xgimi.xhplayer` | HDMI 输入播放器 + 游戏模式 | HDMI 源无法打开 |
| `com.xgimi.xrmservice` | 画质/声音自适应、亮度增强 | 画质调校失效 |
| `com.xgimi.soundermodeservice` | 音筒/蓝牙音箱模式 | 音筒模式失效 |
| `com.xgimi.controllerconnection` | 遥控器配对 | 新遥控配不上 |
| `com.xgimi.newbluetoothota` | 蓝牙固件 OTA | 遥控器固件无法升级 |
| `com.xgimi.bootwizard` | 首启向导 | 恢复出厂卡引导 |
| `com.mstar.tv.service` / `com.mstar.tvsetting` / `com.mstar.tv` / `com.mstar.android.providers.tv` | MStar 通道/热键/菜单/TV Provider（GMUI 上替代海外 `tvinput`/`misckey` 的角色） | HDMI 通道、遥控热键、设置菜单损坏 |

> 海外版（Android TV/Google TV 机型）参考：`cleanyourtv` 仓库 `examples/xgimi-*/debloat.txt`。

## 第三方桌面（实测 EMOTN UI，包名 `com.oversea.aslauncher`）

想要"零信息流"桌面可另装第三方启动器（EMOTN UI / Projectivity Launcher 等）。实测流程：

```bash
# 1) U盘/应用市场安装 EMOTN UI，打开一次
# 2) 设为首选桌面（组件名可用下方查询命令确认）
adb shell dumpsys package com.oversea.aslauncher | grep -B2 'android.intent.category.HOME'
adb shell cmd package set-home-activity <包名>/<主Activity>
# 3) GMUI 会把 HOME 键指回自家桌面，需禁用官方桌面
adb shell pm disable-user --user 0 com.xgimi.home
adb reboot
```

> 实测 NEW Z6X v12.15.214：禁用后开机直达第三方桌面，系统自带 FallbackHome 兜底。

## 复原 GMUI 官方桌面

第三方桌面用腻了随时换回，完全可逆：

```bash
adb shell pm enable com.xgimi.home            # 1) 重新启用官方桌面
adb shell cmd package set-home-activity \
  com.xgimi.home/com.xgimi.module.cellview.home.ui.HomeActivity   # 2) 设回首选（v12.15.214 实测组件）
adb reboot                                    # 3) 重启生效
```

> - 只做第 1 步 + 重启通常也够：GMUI 会自己把 HOME 键夺回（当初禁它就是因为这个）。
> - 若其他固件版本组件名不同：`adb shell cmd package resolve-activity --brief -c android.intent.category.HOME` 查当前首选；
>   或 `pm enable` 后按 HOME，在弹出的选择器里选"极米桌面"并勾"始终"。
> - 想彻底移除 EMOTN UI：`adb shell pm uninstall --user 0 com.oversea.aslauncher`
>   （同样可用 `cmd package install-existing --user 0` 恢复）。
> - 一键操作：`bash post/restore.sh <IP>:5555 home`。

## 进阶清单（实测可再释放 ~200MB，均为出厂预装）

| 包名 | 内存 | 说明 |
|---|---|---|
| `com.ktcp.tvvideo` | ~83MB(含daemon) | 预装视频 App，常驻守护进程 |
| `com.hunantv.license` | ~54MB | 芒果牌照 SDK，含 logcat 采集子进程 |
| `com.xiaodianshi.tv.yst` | ~50MB | 预装视频 App |
| `com.jd.smart.tv.sdk` | ~8MB | 京东智能 SDK（推送通道） |
| `com.xgimi.remote` | ~7MB | RemoteDebug 调试 App 常驻（可能被拉起，禁用即可） |

> 保留：`com.xgimi.miracast`（进程名 com.huawei.connection，系统级 Miracast 投屏，
> 约 10MB，是实际功能）；`com.xgimi.duertts`（语音 TTS，遥控器语音需要）。

## 网络层（可选）

路由器 DNS 屏蔽 `post/ad_domains.txt` 中的域名，双保险。
