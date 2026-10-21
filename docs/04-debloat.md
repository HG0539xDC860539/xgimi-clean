# 04 —— 净化清单

> **EN abstract:** The de-bloat list: what we uninstall (`--user 0`, reversible), what we disable, and the hardware services you must NOT touch (keystone, ToF autofocus, HDMI player, MStar input stack), cross-checked against the overseas XGIMI DO-NOT-DISABLE lists in the cleanyourtv project.


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

> 想要"零信息流"桌面可另装 Projectivity Launcher / Emotn UI 等，
> 步骤（以 Emotn UI 为例）：
> ```bash
> adb shell cmd package set-home-activity <包名>/<主Activity>   # 设为首选
> adb shell pm disable-user --user 0 com.xgimi.home              # GMUI会把HOME键指回自家桌面，需禁用
> adb reboot
> ```
> 实测 NEW Z6X v12.15.214：禁用后开机直达第三方桌面，系统自带 FallbackHome 兜底，
> 随时可 `pm enable com.xgimi.home` 换回。

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
