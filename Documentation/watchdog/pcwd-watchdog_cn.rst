======================
伯克希尔产品 PC 看门狗卡
======================

最后审核：2007年5月10日

支持 ISA 卡 版本 A 和 C
======================

文档和驱动程序由 Ken Hollis 提供 <kenji@bitgate.com>

PC 看门狗卡提供与 WDT 卡相同类型的功能，但无需 IRQ 即可运行。此外，版本 C 的卡片允许您监控任意 I/O 端口以自动触发卡片进行重置。这样您可以使卡片监控硬盘状态或任何其他需要的信息。
看门狗驱动程序的基本作用是与卡片通信并发送信号给它，以免在正常操作过程中重置您的计算机。
看门狗驱动程序将自动找到您的看门狗卡，并为该卡附加一个运行中的驱动程序。在看门狗驱动程序初始化后，您可以使用 PC 看门狗程序与卡片进行通信。
我建议在文件系统检查（fsck）开始前加入 "watchdog -d" 命令，并在 fsck 结束后立即加入 "watchdog -e -t 1" 命令。（记得在命令末尾加上 "&" 符号使其在后台运行！）

如果您想编写一个与 PC 看门狗驱动程序兼容的程序，只需使用或修改看门狗测试程序：
tools/testing/selftests/watchdog/watchdog-test.c


其他的 IOCTL 功能包括：

WDIOC_GETSUPPORT
	此功能返回卡片本身的支持信息。返回的是 "PCWDS" 结构体，其中包含：

		options = WDIOS_TEMPPANIC
				（此卡片支持温度监测）
		firmware_version = xxxx
				（卡片的固件版本）

WDIOC_GETSTATUS
	此功能返回卡片的状态，其中 WDIOF_* 的各个位被按位与（bitwise-anded）到值中。（注释位于 include/uapi/linux/watchdog.h 中）

WDIOC_GETBOOTSTATUS
	此功能返回启动时报告的卡片状态
WDIOC_GETTEMP
	此功能返回卡片的温度。（您也可以读取 /dev/watchdog 文件，该文件每秒更新一次温度。）

WDIOC_SETOPTIONS
	此功能允许您设置卡片的选项。通过这种方式，您可以启用或禁用卡片
WDIOC_KEEPALIVE
	此功能向卡片发送信号告知其不要重置您的计算机
以上就是全部内容！

 -- Ken Hollis
    (kenji@bitgate.com)
