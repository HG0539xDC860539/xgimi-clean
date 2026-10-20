# 01 —— 设备盘点：开放的服务

> 以下梳理均针对**自有设备**进行（设备所有者授权下的配置与排查），
> 目的是了解系统预装了哪些服务、它们提供哪些厂商预留的维护能力。
> 实测对象：极米 NEW Z6X（GMUI v12.15.214，m7221/MStar 平台）；
> 离线参照：2023-07 官方强刷包（GMUI 6.9.102.01，Android 8.0.0）。

## 1. 开放端口（TCP 全端口盘点）

| 端口 | 服务 | 说明 |
|---|---|---|
| 8080 | HTTP | 设置 App（com.android.newsettings）内嵌的 [Android Debug Database](https://github.com/amitshekhariitbhu/Android-Debug-Database) 调试服务，厂商生产固件中处于开启状态 |
| 9987 | WebSocket | 腾讯视频（Java-WebSocket）多屏互动 |
| 12583-12585 | DLNA/UPnP | 投屏渲染 |
| 554 | RTSP | 流服务 |
| 5555 | adbd | 新版固件默认关闭（本文主角） |
| 22346/udp | 工厂自动化 | `AutoServer`（需 `vendor.xgimi.system.serial_debug=1`） |

## 2. 8080 调试服务的接口（厂商集成，生产环境开启）

该服务为设置 App 打包时集成的 Android Debug Database 调试组件：

| 端点 | 能力 |
|---|---|
| `/getDbList`、`/getTableList?database=` | 列出 App 数据库 / SharedPreferences |
| `/getAllDataFromTheTable?tableName=` | 读表 / 读 prefs（需先 getTableList 选中，服务端有状态） |
| `/query?query=<SQL>` | SQL 查询（SELECT / ATTACH / CREATE / INSERT 均可，标识符会被自动加 `[]`） |

- 通过 `ATTACH DATABASE '/sdcard/x.db' AS x` + `CREATE TABLE` 验证了可创建任意路径的 SQLite 文件
- 打开 `/data/system/packages.xml` 报 `not a database` 而非 `permission denied`，
  说明该 App 具备 system 级读取权限
- prefs 中可读到热点 SSID/密码等信息（自有设备排查时请注意妥善保管导出内容）
- 局限：仅支持 sqlite 格式文件；连接为池化，ATTACH 不保证跨请求生效

> 该服务适合信息核对与应急排查；日常维护走更稳定的 `xgimi_ssh` 服务（见 03）。

## 3. 工厂菜单

`设置 → 系统信息 → 长按遥控器【上】键`（H3 系；Z6X 老款为长按【左】键）

入口由 `MiniTvFactory`（com.xgimi.minitvfactory，平台签名、WRITE_SECURE_SETTINGS）提供，
两页：白平衡/老化/陀螺仪/AK 标定等硬件产测项。
其中存在二级菜单 `SecondMenuActivity`（含 ADB/UART/HDMI 调试开关、MstvTool 等），
本机型菜单中未暴露入口且 Activity 未导出，故未采用该路线。

## 4. 广告/遥测域名清单

见 `post/ad_domains.txt`（adapi.xgimi.com、gossapit.xgimi.com、static.t.xgimi.com、
umeng、bugly、hpplay 广告域名等），可在自有路由器上按需过滤。

## 5. 官方升级接口

- 系统升级（com.xgimi.upgrade）：`https://gmui-api.goss.xgimi.com`，
  内含 `SilentInstallApkService`（平台签名 + INSTALL_PACKAGES，静默安装能力）
- 应用商店（com.xgimi.newappmarket）：`https://app.goss.xgimi.com`
