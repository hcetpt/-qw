这是 Linux ACM（Abstract Control Model）驱动程序版本 0.16 的文档，主要描述了如何使用此驱动程序来支持符合 USB 通信设备类抽象控制模型规范的 USB 调制解调器和 ISDN 终端适配器。

### 版权声明
该驱动程序由 Vojtech Pavlik 开发，并由 SuSE 赞助。遵循 GNU 通用公共许可证（GPLv2 或更高版本）发布，提供源代码以供自由分发和修改，但不提供任何形式的保证。

### 免责声明
该程序按照 GPL 许可证发布，用户可以自由分发和修改。但作者不对该软件的任何问题负责，也不保证其适用于特定目的。用户应确保已获取 GPL 许可证副本，如果未获取，可以从 Free Software Foundation 获取。

### 联系方式
作者 Vojtech Pavlik 可以通过电子邮件 vojtech@suse.cz 或者邮寄地址联系。

### 使用说明
该驱动程序 (`drivers/usb/class/cdc-acm.c`) 支持符合 USB CDC ACM 规范的 USB 调制解调器和 ISDN 终端适配器。以下是一些已知兼容的设备列表：

- 3Com OfficeConnect 56k
- 3Com Voice FaxModem Pro
- 3Com Sportster
- MultiTech MultiModem 56k
- Zoom 2986L FaxModem
- Compaq 56k FaxModem
- ELSA Microlink 56k
- 3Com USR ISDN Pro TA
- SonyEricsson K800i (手机)

要使用这些设备，需要加载 `usbcore.ko`、`uhci-hcd.ko`、`ohci-hcd.ko` 或 `ehci-hcd.ko` 和 `cdc-acm.ko` 模块。

### 验证是否工作
可以通过检查 `/sys/kernel/debug/usb/devices` 来验证设备是否被正确识别。在输出中应该能看到类似下面的信息，表示设备已被正确识别为 ACM 设备，并且使用了 ACM 驱动：

```
D:  Ver= 1.00 Cls=02(comm.) Sub=00 Prot=00 MxPS= 8 #Cfgs=  2
I:  If#= 0 Alt= 0 #EPs= 1 Cls=02(comm.) Sub=02 Prot=01 Driver=acm
I:  If#= 1 Alt= 0 #EPs= 2 Cls=0a(data ) Sub=00 Prot=00 Driver=acm
```

同时，在系统日志中也应该能看到类似下面的日志信息，表示 ACM 驱动成功地识别并接管了设备：

```
usb.c: USB new device connect, assigned device number 2
...
ttyACM0: USB ACM device
...
```

如果一切正常，可以启动 `minicom` 并设置其与 `ttyACM` 设备通信，尝试发送命令 `at`。如果设备响应 `OK`，则表明设备工作正常。
