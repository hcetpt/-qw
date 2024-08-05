===========================================================
Intel IXP4xx 网络处理器上的 Linux 发行说明
===========================================================

维护者：Deepak Saxena <dsaxena@plexity.net>
-------------------------------------------------------------------------

1. 概览

Intel 的 IXP4xx 网络处理器是一个高度集成的系统级芯片（SoC），主要针对网络应用，但由于其低成本和低功耗特性，它也在工业控制和其他领域变得非常流行。目前，IXP4xx 家族包括支持不同网络卸载功能（如加密、路由、防火墙等）的多个处理器。IXP46x 家族是更新的版本，支持更高的速度、新的内存与闪存配置以及更多的集成组件，例如片上 I2C 控制器。
有关 CPU 各个版本的更多信息，请参阅：

   http://developer.intel.com/design/network/products/npfamily/ixp4xx.htm

Intel 还曾生产 IXCP1100 CPU，它是 IXP4xx 的一个简化版，去除了大部分网络智能功能。
2. Linux 支持

Linux 当前在 IXP4xx 芯片上支持以下功能：

- 双串行端口
- PCI 接口
- 闪存访问（MTD/JFFS）
- 通过 GPIO 实现 I2C（仅限 IXP42x）
- GPIO 用于输入/输出/中断
  访问函数位于 arch/arm/mach-ixp4xx/include/mach/platform.h
- 定时器（看门狗、操作系统）

以下芯片组件未被 Linux 支持，需要使用 Intel 的专有 CSR 软件：

- USB 设备接口
- 网络接口（HSS、Utopia、NPE 等）
- 网络卸载功能

如果你需要使用上述任何一项功能，你需要从以下网址下载 Intel 的软件：

   http://developer.intel.com/design/network/products/npfamily/ixp425.htm

**请勿向 Linux 邮件列表发布有关专有软件的问题**
有几个网站提供了使用 Intel 软件的指南：

   - http://sourceforge.net/projects/ixp4xx-osdg/
     使用 uClinux 和 Intel 库的开源开发者指南

   - http://gatewaymaker.sourceforge.net/
     使用 IXP425 和 Linux 构建网关的简单一页指南

   - http://ixp425.sourceforge.net/
     依赖于 Intel 库的 IXP425 ATM 设备驱动程序
3. 已知问题/限制

3a. 有限的入站 PCI 窗口

IXP4xx 家族允许高达 256MB 的内存，但 PCI 接口只能向 PCI 总线暴露其中的 64MB。这意味着如果运行的内存大于 64MB，则所有超出可访问范围的 PCI 缓冲区都将通过 arch/arm/common/dmabounce.c 中的例程进行重新定位。
3b. 有限的出站 PCI 窗口

IXP4xx 提供两种访问 PCI 内存空间的方法：

1) 直接映射窗口从 0x48000000 到 0x4bffffff（64MB）
要通过这个空间访问 PCI，我们只需将 BAR 映射到内核中，并可以使用标准的 read[bwl]/write[bwl] 宏。这是首选方法，因为速度快，但它将系统限制在仅 64MB 的 PCI 内存。这可能在使用显卡和其他占用大量内存的设备时出现问题。
2) 如果需要超过 64MB 的内存空间，IXP4xx 可以配置为使用间接寄存器来访问 PCI。这样可以在总线上提供最多 128MB（0x48000000 到 0x4fffffff）的内存。
这种方法的缺点是每次 PCI 访问都需要三次本地寄存器访问加上自旋锁，但在某些情况下性能损失是可以接受的。此外，在这种情况下，你不能 mmap() PCI 设备，因为 PCI 窗口的间接性质。
默认情况下，出于性能原因，使用直接方法。如果你需要更多 PCI 内存，请启用 IXP4XX_INDIRECT_PCI 配置选项。
3c. 将GPIO用作中断

目前，代码仅处理基于电平的GPIO中断。

4. 支持的平台

ADI Engineering Coyote网关参考平台
http://www.adiengineering.com/productsCoyote.html

   ADI Coyote平台是为构建小型住宅/办公网关而设计的参考方案。一个NPE连接到10/100接口，另一个连接到4端口10/100交换机，第三个连接到ADSL接口。此外，它还支持通过SLIC连接的POTs接口。需要注意的是，这些接口目前不被Linux ATM支持。最后，该平台有两个mini-PCI插槽，用于802.11[b/g/a]无线网卡。另外，还有一个IDE端口连接在扩展总线上。
Gateworks Avila网络平台
http://www.gateworks.com/support/overview.php

   Avila平台基本上是一个IXDP425，其4个PCI插槽被替换成了mini-PCI插槽，并且通过扩展总线连接了一个CF IDE接口。
Intel IXDP425开发平台
http://www.intel.com/design/network/products/npfamily/ixdpg425.htm

   这是Intel为IXDP425提供的标准参考平台，也被称为Richfield主板。它包含4个PCI插槽、16MB闪存、两个10/100端口和一个ADSL端口。
Intel IXDP465开发平台
http://www.intel.com/design/network/products/npfamily/ixdp465.htm

   这基本上是一个IXDP425，但使用了IXP465处理器并配备32MB的闪存，而不是16MB。
Intel IXDPG425开发平台

   这基本上是一个ADI Coyote主板，增加了NEC EHCI控制器。该主板的一个问题是mini-PCI插槽只连接了3.3v电源线，因此不能使用带有E100卡的PCI转mini-PCI适配器。因此要实现NFS根文件系统，需要使用CSR或WiFi卡以及一个通过BOOTP获取然后执行NFS根切换的ramdisk。
Motorola PrPMC1100处理器夹层卡
http://www.fountainsys.com

   PrPMC1100基于IXCP1100设计，旨在插入IXP2400/2800系统中作为系统控制器。它仅仅包含一个CPU和板载16MB闪存，需要插入载体板才能正常工作。目前Linux仅支持Motorola PrPMC载体板作为此平台的支持。
5. 待办事项列表

- 添加对Coyote IDE的支持
- 添加对基于边沿的GPIO中断的支持
- 添加对扩展总线上的CF IDE的支持

6. 感谢

IXP4xx的工作得到了Intel公司和MontaVista Software, Inc.的资金支持。
以下人员提供了补丁、评论等贡献：

- Lennerty Buytenhek
- Lutz Jaenicke
- Justin Mayfield
- Robert E. Ranslam

[我知道我遗漏了一些人，请发邮件给我以便添加]

-------------------------------------------------------------------------

最后一次更新：2005年1月4日
