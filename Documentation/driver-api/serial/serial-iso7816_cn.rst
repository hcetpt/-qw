=============================
ISO7816 串行通信
=============================

1. 引言
===============

ISO/IEC7816 是一系列规范，定义了集成电路卡（ICC），也称为智能卡。

2. 硬件相关考虑
==================================

一些 CPU/UART（例如 Microchip AT91）包含一种内置模式，能够处理与智能卡的通信。
对于这些微控制器，Linux 驱动程序应具备在两种模式下工作的能力，并且应在用户级别提供适当的 ioctl（参见后文），以允许在这两种模式之间进行切换。

3. 内核中已有的数据结构
==================================================

Linux 内核提供了 `serial_iso7816` 结构（参见 [1]）来处理 ISO7816 通信。此数据结构用于在 ioctl 中设置和配置 ISO7816 参数。
任何能同时作为 RS232 和 ISO7816 工作的设备的驱动程序都应实现 `uart_port` 结构中的 `iso7816_config` 回调函数。当接收到 TIOCGISO7816 和 TIOCSISO7816 ioctl 请求时（参见下文），`serial_core` 会调用 `iso7816_config` 来完成设备特定的部分。`iso7816_config` 回调函数接收一个指向 `serial_iso7816` 结构的指针。

4. 用户级别的使用
========================

从用户级别，可以使用上述 ioctl 获取/设置 ISO7816 配置。例如，要设置 ISO7816，您可以使用以下代码：

```c
#include <linux/serial.h>

// 包含 ISO7816 ioctl 的定义：TIOCSISO7816 和 TIOCGISO7816
#include <sys/ioctl.h>

// 打开您特定的设备（例如：/dev/mydevice）：
int fd = open ("/dev/mydevice", O_RDWR);
if (fd < 0) {
    // 错误处理。参见 errno。
}

struct serial_iso7816 iso7816conf;

// 预留字段需要清零
memset(&iso7816conf, 0, sizeof(iso7816conf));

// 启用 ISO7816 模式:
iso7816conf.flags |= SER_ISO7816_ENABLED;

// 选择协议：
// T=0
iso7816conf.flags |= SER_ISO7816_T(0);
// 或者 T=1
iso7816conf.flags |= SER_ISO7816_T(1);

// 设置监护时间：
iso7816conf.tg = 2;

// 设置时钟频率
iso7816conf.clk = 3571200;

// 设置传输因子：
iso7816conf.sc_fi = 372;
iso7816conf.sc_di = 1;

if (ioctl(fd, TIOCSISO7816, &iso7816conf) < 0) {
    // 错误处理。参见 errno。
}

// 在这里使用 read() 和 write() 系统调用...

// 当操作完成后关闭设备：
if (close (fd) < 0) {
    // 错误处理。参见 errno。
}
```

5. 参考资料
=============

[1]    include/uapi/linux/serial.h
