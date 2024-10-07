.. SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

===============
C2 端口支持
===============

(C) 版权所有 2007 Rodolfo Giometti <giometti@enneenne.com>

本程序是自由软件；您可以根据自由软件基金会发布的 GNU 通用公共许可证的条款重新分发和/或修改它；无论是许可证的第 2 版，还是（按您的选择）任何更新版本。
本程序以希望其有用的宗旨发布，
但没有任何保证；甚至没有隐含的关于适销性或适合特定目的的保证。详情请参见 GNU 通用公共许可证。

概述
--------

此驱动程序实现了 Silicon Labs（Silabs）C2 接口在 Linux 中的支持，该接口用于微控制器的在线编程。
通过使用此驱动程序，您可以在没有 EC2 或 EC3 调试适配器的情况下重新编程在线闪存。此解决方案也适用于那些通过特殊 GPIO 引脚连接微控制器的系统。

参考资料
----------

C2 接口的主要参考资料位于 [Silicon Laboratories 网站](https://www.silabs.com)，详见：

- AN127：通过 C2 接口进行闪存编程，位于 [https://www.silabs.com/Support Documents/TechnicalDocs/an127.pdf](https://www.silabs.com/Support Documents/TechnicalDocs/an127.pdf)

- C2 规范，位于 [https://www.silabs.com/pages/DownloadDoc.aspx?FILEURL=Support%20Documents/TechnicalDocs/an127.pdf&src=SearchResults](https://www.silabs.com/pages/DownloadDoc.aspx?FILEURL=Support%20Documents/TechnicalDocs/an127.pdf&src=SearchResults)

然而，它实现了一种两线串行通信协议（位敲击），旨在使低引脚数的 Silicon Labs 设备能够进行在线编程、调试和边界扫描测试。目前此代码仅支持闪存编程，但扩展功能易于添加。

使用驱动程序
----------------

加载驱动程序后，您可以使用 sysfs 支持来获取 C2port 的信息或读写在线闪存：

```bash
# ls /sys/class/c2port/c2port0/
access            flash_block_size  flash_erase       rev_id
dev_id            flash_blocks_num  flash_size        subsystem/
flash_access      flash_data        reset             uevent
```

最初，C2port 访问被禁用，因为您的硬件可能将这些线路与其它设备复用，因此要访问 C2port，您需要执行以下命令：

```bash
# echo 1 > /sys/class/c2port/c2port0/access
```

之后，您应该读取连接的微控制器的设备 ID 和修订版 ID：

```bash
# cat /sys/class/c2port/c2port0/dev_id
8
# cat /sys/class/c2port/c2port0/rev_id
1
```

出于安全原因，在线闪存访问尚未启用，为此您需要执行以下命令：

```bash
# echo 1 > /sys/class/c2port/c2port0/flash_access
```

之后，您可以读取整个闪存内容：

```bash
# cat /sys/class/c2port/c2port0/flash_data > image
```

擦除它：

```bash
# echo 1 > /sys/class/c2port/c2port0/flash_erase
```

并写入它：

```bash
# cat image > /sys/class/c2port/c2port0/flash_data
```

写入后，您需要重置设备以执行新代码：

```bash
# echo 1 > /sys/class/c2port/c2port0/reset
```
