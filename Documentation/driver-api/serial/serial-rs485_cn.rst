RS485 串行通信
===========================

1. 引言
===============

   EIA-485，也称为 TIA/EIA-485 或 RS-485，是一个定义了驱动器和接收器电气特性的标准，用于平衡数字多点系统中。
该标准在工业自动化通信中被广泛使用，因为它能够在长距离和电噪声环境中有效工作。

2. 硬件相关考虑
==================================

   一些 CPU/UART（例如 Atmel AT91 或 16C950 UART）包含一个内置的半双工模式，能够通过切换 RTS 或 DTR 信号自动控制线路方向。
这可以用来控制外部的半双工硬件，如 RS485 转换器或任何通过 RS232 连接的半双工设备，如某些调制解调器。
对于这些微控制器，Linux 驱动程序应该具备在两种模式下工作的能力，并且应该提供适当的 ioctl（见后文），以允许用户级别从一种模式切换到另一种模式，反之亦然。

3. 内核中已有的数据结构
==================================================

   Linux 内核提供了 `struct serial_rs485` 来处理 RS485 通信。这个数据结构用于设置和配置平台数据中的 RS485 参数以及 ioctl 中的参数。
设备树还可以提供 RS485 启动时参数 [1]_ 。当驱动程序调用 `uart_get_rs485_mode()` 时，串行核心会从设备树提供的值填充 `struct serial_rs485`。
任何既支持 RS232 又支持 RS485 的设备驱动程序都应该实现 `rs485_config` 回调函数，并在 `struct uart_port` 中提供 `rs485_supported`。
串行核心调用 `rs485_config` 来响应 TIOCSRS485 ioctl（见下文）中的设备特定部分。`rs485_config` 回调函数接收一个经过清理的 `struct serial_rs485` 指针。
用户空间提供的 `struct serial_rs485` 在调用 `rs485_config` 之前会被 `rs485_supported` 清理，它指示了驱动程序为 `struct uart_port` 支持哪些 RS485 功能。
TIOCGRS485 ioctl 可用于读取当前配置对应的 `struct serial_rs485`
.. kernel-doc:: include/uapi/linux/serial.h
   :identifiers: serial_rs485 uart_get_rs485_mode

4. 用户级别的使用
========================

   从用户级别，可以通过上述 ioctl 获取/设置 RS485 配置。例如，要设置 RS485，您可以使用以下代码：

	```c
	#include <linux/serial.h>

	/* 包含 RS485 ioctl 的定义：TIOCGRS485 和 TIOCSRS485 */
	#include <sys/ioctl.h>

	/* 打开您的特定设备（例如，/dev/mydevice）：*/
	int fd = open ("/dev/mydevice", O_RDWR);
	if (fd < 0) {
		/* 错误处理。参见 errno。 */
	}

	struct serial_rs485 rs485conf;

	/* 启用 RS485 模式：*/
	rs485conf.flags |= SER_RS485_ENABLED;

	/* 设置发送时 RTS 引脚的逻辑电平为 1：*/
	rs485conf.flags |= SER_RS485_RTS_ON_SEND;
	/* 或者，设置发送时 RTS 引脚的逻辑电平为 0：*/
	rs485conf.flags &= ~(SER_RS485_RTS_ON_SEND);

	/* 设置发送后 RTS 引脚的逻辑电平为 1：*/
	rs485conf.flags |= SER_RS485_RTS_AFTER_SEND;
	/* 或者，设置发送后 RTS 引脚的逻辑电平为 0：*/
	rs485conf.flags &= ~(SER_RS485_RTS_AFTER_SEND);

	/* 如果需要，设置发送前 RTS 延迟：*/
	rs485conf.delay_rts_before_send = ...;

	/* 如果需要，设置发送后 RTS 延迟：*/
	rs485conf.delay_rts_after_send = ...;

	/* 如果您希望即使在发送数据时也能接收数据，请设置此标志 */
	rs485conf.flags |= SER_RS485_RX_DURING_TX;

	if (ioctl (fd, TIOCSRS485, &rs485conf) < 0) {
		/* 错误处理。参见 errno。 */
	}

	/* 在这里使用 read() 和 write() 系统调用... */

	/* 完成后关闭设备：*/
	if (close (fd) < 0) {
		/* 错误处理。参见 errno。 */
	}
	```

5. 多点寻址
========================

   Linux 内核为多点 RS-485 串行通信线提供了寻址模式。寻址模式通过 `struct serial_rs485` 中的 `SER_RS485_ADDRB` 标志启用。
`struct serial_rs485` 具有两个额外的标志和字段来启用接收地址和目标地址。
寻址模式标志：
	- `SER_RS485_ADDRB`：启用寻址模式（同时设置 termios 中的 ADDRB）
- ``SER_RS485_ADDR_RECV``: 启用接收（过滤）地址
- ``SER_RS485_ADDR_DEST``: 设置目标地址
地址字段（通过相应的``SER_RS485_ADDR_*``标志启用）：
    - ``addr_recv``: 接收地址
- ``addr_dest``: 目标地址
一旦设置了接收地址，通信就只能与特定的设备进行，其他对等方将被过滤掉。是否执行过滤取决于接收端。如果未设置``SER_RS485_ADDR_RECV``，接收地址将会被清除。
注意：并非所有支持RS485的设备都支持多点寻址。
6. 参考资料
=============

.. [#DT-bindings] 文档/devicetree/bindings/serial/rs485.txt
