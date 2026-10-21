# 06 —— FAQ

> **EN abstract:** FAQ — why `adb connect` stays `unauthorized` even after the ADB opener (secure adbd, root-only key file, no consent dialog), and how the g/p2/p3 scripts get your key in.


## Q1: 装了 Z7X-ADB、ADB 已开启（5555 端口也通了），为什么 `adb connect` 还是 `unauthorized`？

**Z7X-ADB 只让 adbd "开始监听"，不解决 "身份授权"。**

ADB 连接有两道门：

```
第1道：adbd 是否监听 5555        ← Z7X-ADB 的 setprop 解决
第2道：adbd 是否认识你的电脑     ← 卡在这里
```

本机 boot ramdisk 的 `prop.default` 里有 `ro.adb.secure=1`
（vendor/build.prop 里的 `ro.adb.secure=0` 无效——`ro.*` 属性先到先得，
ramdisk 最先加载），因此 adbd 运行在安全模式下：
电脑的 ADB 公钥必须已写入设备的 `/data/misc/adb/adb_keys`，
否则一律 `unauthorized`。

标准 Android 会弹出"允许 USB 调试吗？"对话框，点确定即写入公钥；
**GMUI 定制的系统 UI 没有实现这个对话框**（实测各种触发均不弹），
公钥无法通过常规途径写入 → 一直 unauthorized。

而 `adb_keys` 仅 root/system 可写 → 无 shell 则无 root，无 root 则写不了
adb_keys，死循环。

**本项目的 g/p2/p3 脚本就是破环**：借厂商预留的 `xgimi_ssh` 维护服务
（ProxyCommand 机制）以 root 身份把**你的** adb 公钥写进 `adb_keys`，
从设备内部完成授权。

> Z7X 高亮版原教程"开了就能连"，因为那台设备 adbd 不在安全模式
> （或其 SystemUI 会弹授权窗）。NEW Z6X 新固件收紧了，必须补授权环节。

## Q2: 为什么不直接刷 2023 老固件？（里面 ADB 默认开）

可以，但代价是：清空全部数据 + 界面回退到旧版 + 强刷有变砖风险。
本项目路线不碰系统分区、保留最新固件与界面、全部可逆。

## Q3: 工厂菜单里有没有 ADB 开关？

`MiniTvFactory` 确实有含 ADB 开关的二级菜单（`SecondMenuActivity`），
但该机型菜单未暴露入口且 Activity 未导出；其行为也只是启停 adbd，
同样不解决 Q1 的授权问题。

## Q4: 8080 那个调试服务能不能直接完成 root？

不能。它是设置 App 集成的 Android Debug Database，只支持
**sqlite 格式**文件的读写；root 需要执行命令与写文本文件，格式对不上。
它适合信息核对（能读到热点密码等），root 环节走 `xgimi_ssh` 服务更稳。

## Q5: 重启后 ADB 还在吗？

在。`persist.adb.tcp.port=5555` / `persist.sys.usb.config=adb` 是持久属性，
开机 adbd 自动监听；adb_keys 是落盘文件，授权长期有效。
若装了 p4 的 pcroot 服务，块设备权限开机也会自动恢复。

## Q6: 广告会随 OTA 回来吗？

已卸载的包 OTA 全量升级才会回来（增量不会）。我们同时禁用了
`com.xgimi.upgrade`，需要升级时 `pm enable com.xgimi.upgrade` 再检查更新。
路由器过滤 `gmui-api.goss.xgimi.com` 可双保险（见 post/ad_domains.txt）。

## Q7: SSH 为什么连不上？root sshd 不是起来了吗？

该移植版 sshd 对 root 的公钥认证受其内置 getpwnam 判定影响
（账户视为锁定），即便 `StrictModes no` + root 属主密钥 + passwd 解锁
也可能拒绝。不影响使用——root 触发机制（params/ProxyCommand）随时可用，
日常操作走 ADB 即可。

## Q8: 8080 调试服务怎么处理？

设置 App（com.android.newsettings）一运行就会监听 8080（厂商集成的调试组件）。
处置：
```bash
adb shell am force-stop com.android.newsettings   # 端口立即关闭
```
代价：下次在投影仪上打开"设置"它会再次监听。可接受的做法是养成
"用过设置后杀一次"的习惯；或在路由器上限制只有自己的设备可访问它。

## Q9: 后台还有哪些对外连接？

实测净化后剩余：极米系统服务（system uid）到阿里云的 2 条 keepalive、
第三方桌面（Emotn UI）到自己服务器的 1 条。如需阻断可路由器过滤
相应域名，但注意可能影响语音/遥控 App/推送功能。
