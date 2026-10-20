# 04 —— 净化清单

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
