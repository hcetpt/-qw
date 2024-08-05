==================
OpenRISC Linux
==================

这是将Linux移植到OpenRISC系列微处理器的工作；初始的目标架构，具体来说，是32位的OpenRISC 1000系列（或1k）。有关OpenRISC处理器及其持续开发的信息：

	=======		=============================
	网站		https://openrisc.io
	邮件列表	openrisc@lists.librecores.org
	=======		=============================

---------------------------------------------------------------------

OpenRISC工具链和Linux的构建说明
===================================================

为了构建并运行OpenRISC上的Linux，您至少需要一个基础工具链，或许还需要体系结构模拟器。以下是获取这些组件的步骤：
1) 工具链

可以从openrisc.io或我们的GitHub发布页面获得工具链二进制文件。
构建不同工具链的说明可以在openrisc.io找到，或者在Stafford的工具链构建和发布脚本中找到。
==========	=================================================
二进制文件	https://github.com/openrisc/or1k-gcc/releases
工具链		https://openrisc.io/software
构建		https://github.com/stffrdhrn/or1k-toolchain-build
==========	=================================================

2) 构建

像平常一样构建Linux内核：
```
make ARCH=openrisc CROSS_COMPILE="or1k-linux-" defconfig
make ARCH=openrisc CROSS_COMPILE="or1k-linux-"
```

3) 在FPGA上运行（可选）

OpenRISC社区通常使用FuseSoC来管理构建并将SoC编程到FPGA中。以下是在De0 Nano开发板上编程OpenRISC SoC的一个示例。在构建过程中，从FuseSoC IP核心仓库下载FPGA RTL代码，并使用FPGA供应商工具进行构建。使用openocd将二进制文件加载到板上。
```
git clone https://github.com/olofk/fusesoc
cd fusesoc
sudo pip install -e .
fusesoc init
fusesoc build de0_nano
fusesoc pgm de0_nano

openocd -f interface/altera-usb-blaster.cfg \
        -f board/or1k_generic.cfg

telnet localhost 4444
> init
> halt; load_image vmlinux ; reset
```

4) 在模拟器上运行（可选）

QEMU是一个处理器仿真器，我们推荐用于模拟OpenRISC平台。请按照QEMU网站上的OpenRISC指南来在QEMU上运行Linux。您可以自己构建QEMU，但您的Linux发行版很可能提供了支持OpenRISC的二进制包。
=============	======================================================
QEMU OpenRISC	https://wiki.qemu.org/Documentation/Platforms/OpenRISC
=============	======================================================

---------------------------------------------------------------------

术语
===========

在代码中，以下标记被用在符号上来限定更具体或不那么具体的处理器实现的范围：

========= =======================================
OpenRISC: OpenRISC系列的处理器
or1k:     OpenRISC 1000系列的处理器
or1200:   OpenRISC 1200处理器
========= =======================================

---------------------------------------------------------------------

历史
========

2003年11月18日	Matjaz Breskvar (phoenix@bsemi.com)
	对OpenRISC/or32架构进行了Linux的初始移植
所有核心的东西都已经实现，并且看起来可用
2003年12月8日	Matjaz Breskvar (phoenix@bsemi.com)
	TLB缺失处理的完全更改
异常处理的重写  
默认的初始ram磁盘（initrd）中的sash-3.6完全功能版本  
一个大幅度改进的版本，进行了全方位的更改  
10-04-2004   Matjaz Breskvar (phoenix@bsemi.com)  
修复了大量各种地方的错误  
支持以太网，功能性的HTTP和Telnet服务器  
能够运行许多标准Linux应用程序  
26-06-2004   Matjaz Breskvar (phoenix@bsemi.com)  
移植到2.6.x版本  

30-11-2004   Matjaz Breskvar (phoenix@bsemi.com)  
进行了大量的错误修复和增强  
添加了OpenCores帧缓冲驱动程序  
09-10-2010   Jonas Bonn (jonas@southpole.se)  
进行了重大重写，以与上游Linux 2.6.36版本保持一致
