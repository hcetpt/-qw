Xilinx Zynq MPSoC EEMI 文档
=============================

Xilinx Zynq MPSoC 固件接口
-----------------------------
`zynqmp-firmware` 节点描述了与平台固件的接口。ZynqMP 具有一个与安全固件通信的接口。固件驱动程序提供了一个与固件 API 交互的接口。任何希望与平台管理控制器（PMC）通信的驱动程序都可以使用这些接口 API。

嵌入式能源管理接口 (EEMI)
------------------------------
嵌入式能源管理接口用于使在芯片或设备上的不同处理集群上运行的软件组件能够与设备上的电源管理控制器 (PMC) 进行通信，以发出或响应电源管理请求。
任何想要使用 EEMI API 与 PMC 通信的驱动程序都应使用为每个功能提供的函数。

IOCTL
------
IOCTL API 用于设备控制和配置。这不是系统 IOCTL，而是 EEMI API。此 API 可由主控方用于控制任何特定于设备的配置。IOCTL 定义可以是平台特有的。此 API 还管理共享设备配置。
以下 IOCTL ID 对于设备控制有效：
- IOCTL_SET_PLL_FRAC_MODE	8
- IOCTL_GET_PLL_FRAC_MODE	9
- IOCTL_SET_PLL_FRAC_DATA	10
- IOCTL_GET_PLL_FRAC_DATA	11

有关 IOCTL 特定参数和其他 EEMI API 的详细信息，请参阅 EEMI API 指南 [0]。

参考文献
---------
[0] 嵌入式能源管理接口 (EEMI) API 指南：
    https://www.xilinx.com/support/documentation/user_guides/ug1200-eemi-api.pdf
