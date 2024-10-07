SPDX 许可证标识符: GPL-2.0

===========================================================================
Synopsys DesignWare PCIe 交通生成器（也称为 xData）的驱动程序
===========================================================================

支持的芯片:
Synopsys DesignWare PCIe 原型解决方案

数据手册:
非自由获取

作者:
Gustavo Pimentel <gustavo.pimentel@synopsys.com>

描述
-----------

此驱动程序应作为主机端（Root Complex）驱动程序使用，并且包括此 IP 的 Synopsys DesignWare 原型。
dw-xdata-pcie 驱动程序可以用于启用或禁用任一方向上的 PCIe 交通生成器（互斥），并允许分析 PCIe 链路性能。
与该驱动程序的交互是通过模块参数进行的，并且可以在运行时更改。驱动程序将请求的命令状态信息输出到 `/var/log/kern.log` 或 `dmesg`。

示例
-------

写入 TLPs 交通生成 - Root Complex 到 Endpoint 方向
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

生成流量:

```shell
# echo 1 > /sys/class/misc/dw-xdata-pcie.0/write
```

获取链路吞吐量（MB/s）:

```shell
# cat /sys/class/misc/dw-xdata-pcie.0/write
204
```

停止任何方向上的流量:

```shell
# echo 0 > /sys/class/misc/dw-xdata-pcie.0/write
```

读取 TLPs 交通生成 - Endpoint 到 Root Complex 方向
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

生成流量:

```shell
# echo 1 > /sys/class/misc/dw-xdata-pcie.0/read
```

获取链路吞吐量（MB/s）:

```shell
# cat /sys/class/misc/dw-xdata-pcie.0/read
199
```

停止任何方向上的流量:

```shell
# echo 0 > /sys/class/misc/dw-xdata-pcie.0/read
```
