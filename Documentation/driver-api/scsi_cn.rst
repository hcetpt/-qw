=====  
SCSI接口指南  
=====  

:作者: James Bottomley  
:作者: Rob Landley  

简介  
============  

协议与总线  
---------------  

曾经，小型计算机系统接口（SCSI）定义了一种并行I/O总线及一套数据协议，用于将各种外围设备（如磁盘驱动器、磁带驱动器、调制解调器、打印机、扫描仪、光驱、测试设备和医疗设备）连接到主机。尽管旧式的并行（快速/宽/超高速）SCSI总线已基本不再使用，但SCSI命令集比以往任何时候都更广泛地应用于通过多种不同的总线与设备通信。  
`SCSI协议 <https://www.t10.org/scsi-3.htm>`__ 是一种大端序的对等包交换协议。SCSI命令长度为6、10、12或16字节，并通常后跟关联的数据负载。  
SCSI命令可以在几乎任何类型的总线上传输，并且是USB、SATA、SAS、光纤通道、火线和ATAPI设备中存储设备默认采用的协议。SCSI数据包还经常通过Infiniband、  
TCP/IP (`iSCSI <https://en.wikipedia.org/wiki/ISCSI>`__)，甚至是`并行端口 <http://cyberelk.net/tim/parport/parscsi.html>`__ 进行交换。  

Linux SCSI子系统的架构设计  
----------------------------------  

SCSI子系统采用了三层设计，包括上层、中层和下层。每一项涉及SCSI子系统的操作（例如从磁盘读取一个扇区）都会用到这三层中的每个层级的一个驱动程序：一个上层驱动程序、一个下层驱动程序以及SCSI中层。  

SCSI上层  
================  

上层通过提供设备节点来支持用户空间与内核之间的接口。  
sd (SCSI磁盘)  
--------------  
sd (sd_mod.o)  
sr (SCSI CD-ROM)  
----------------  
sr (sr_mod.o)  
st (SCSI磁带)  
--------------  
st (st.o)  
sg (通用SCSI)  
-----------------  
sg (sg.o)  
ch (SCSI介质更换器)  
----------------------  
ch (ch.c)  

SCSI中层  
==============  

SCSI中层实现  
-----------------  

include/scsi/scsi_device.h  
~~~~~~~~~~~~~~~~~~~~~~~~~~~  

.. kernel-doc:: include/scsi/scsi_device.h  
   :internal:  

drivers/scsi/scsi.c  
~~~~~~~~~~~~~~~~~~~  

SCSI中层的主要文件
### drivers/scsi/scsi.c
~~~
.. kernel-doc:: drivers/scsi/scsi.c
   :export:
~~~

### drivers/scsi/scsicam.c
~~~
drivers/scsi/scsicam.c
~~~~~~~~~~~~~~~~~~~~~~

通用访问方法 (`SCSI Common Access Method <http://www.t10.org/ftp/t10/drafts/cam/cam-r12b.pdf>`__) 支持函数，用于处理 HDIO_GETGEO 等操作。
.. kernel-doc:: drivers/scsi/scsicam.c
   :export:
~~~

### drivers/scsi/scsi_error.c
~~~
drivers/scsi/scsi_error.c
~~~~~~~~~~~~~~~~~~~~~~~~~~

通用 SCSI 错误/超时处理例程
.. kernel-doc:: drivers/scsi/scsi_error.c
   :export:
~~~

### drivers/scsi/scsi_devinfo.c
~~~
drivers/scsi/scsi_devinfo.c
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

管理 scsi_dev_info_list，该列表追踪黑名单和白名单中的设备
.. kernel-doc:: drivers/scsi/scsi_devinfo.c
   :internal:
~~~

### drivers/scsi/scsi_ioctl.c
~~~
drivers/scsi/scsi_ioctl.c
~~~~~~~~~~~~~~~~~~~~~~~~~~

处理 SCSI 设备的 ioctl() 调用
.. kernel-doc:: drivers/scsi/scsi_ioctl.c
   :export:
~~~

### drivers/scsi/scsi_lib.c
~~~
drivers/scsi/scsi_lib.c
~~~~~~~~~~~~~~~~~~~~~~~~

SCSI 队列库
.. kernel-doc:: drivers/scsi/scsi_lib.c
   :export:
~~~

### drivers/scsi/scsi_lib_dma.c
~~~
drivers/scsi/scsi_lib_dma.c
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

依赖 DMA 的 SCSI 库函数（映射和取消映射分散/聚集列表）
.. kernel-doc:: drivers/scsi/scsi_lib_dma.c
   :export:
~~~

### drivers/scsi/scsi_proc.c
~~~
drivers/scsi/scsi_proc.c
~~~~~~~~~~~~~~~~~~~~~~~~~

此文件中的函数提供了 PROC 文件系统与 SCSI 设备驱动程序之间的接口。主要用于调试、统计以及直接向低级驱动程序传递信息。例如，用于管理 `/proc/scsi/*`。
.. kernel-doc:: drivers/scsi/scsi_proc.c
   :internal:
~~~

### drivers/scsi/scsi_netlink.c
~~~
drivers/scsi/scsi_netlink.c
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

通过 netlink 向用户空间提供来自传输层的异步事件的基础架构，所有传输层都使用单一的 NETLINK_SCSITRANSPORT 协议。更多详情请参见 `原始补丁提交 <https://lore.kernel.org/linux-scsi/1155070439.6275.5.camel@localhost.localdomain/>`__。
.. kernel-doc:: drivers/scsi/scsi_netlink.c
   :internal:
~~~

### drivers/scsi/scsi_scan.c
~~~
drivers/scsi/scsi_scan.c
~~~~~~~~~~~~~~~~~~~~~~~~~

扫描主机以确定是否连接了设备。一般扫描/探测算法如下，具体根据设备特定标志、编译选项及全局变量（启动或模块加载时设置）进行调整。对于特定的逻辑单元号 (LUN)，通过 INQUIRY 命令进行扫描；如果 LUN 连接有设备，则为该设备分配并设置 scsi_device。对于给定主机上的每个通道的每个 ID，从扫描 LUN 0 开始。跳过对 LUN 0 扫描无响应的主机。否则，如果 LUN 0 上有设备，则为它分配并设置 scsi_device。如果目标是 SCSI-3 或以上版本，发送 REPORT LUN 命令，并扫描 REPORT LUN 返回的所有 LUN；否则，顺序扫描 LUN 直到达到某个最大值或遇到无法连接设备的 LUN。
.. kernel-doc:: drivers/scsi/scsi_scan.c
   :internal:
~~~

### drivers/scsi/scsi_sysctl.c
~~~
drivers/scsi/scsi_sysctl.c
~~~~~~~~~~~~~~~~~~~~~~~~~~~

设置 sysctl 条目：“/dev/scsi/logging_level” (DEV_SCSI_LOGGING_LEVEL)，用于设置/返回 scsi_logging_level。
~~~
### 驱动程序/scsi/scsi_sysfs.c
~~~~~~~~~~~~~~~~~~~~~~~~~~

SCSI sysfs 接口例程
.. kernel-doc:: drivers/scsi/scsi_sysfs.c
   :export:

### 驱动程序/scsi/hosts.c
~~~~~~~~~~~~~~~~~~~~

中到低层 SCSI 驱动程序接口

.. kernel-doc:: drivers/scsi/hosts.c
   :export:

### 驱动程序/scsi/scsi_common.c
~~~~~~~~~~~~~~~~~~~~~~~~~~

通用支持函数

.. kernel-doc:: drivers/scsi/scsi_common.c
   :export:

### 传输类别
-------------

传输类别是 SCSI 下层驱动程序的服务库，它们在 sysfs 中暴露传输属性。

#### 光纤通道传输
~~~~~~~~~~~~~~~~~~~~~~~

文件 `drivers/scsi/scsi_transport_fc.c` 定义了光纤通道的传输属性。
.. kernel-doc:: drivers/scsi/scsi_transport_fc.c
   :export:

#### iSCSI 传输类别
~~~~~~~~~~~~~~~~~~~~~

文件 `drivers/scsi/scsi_transport_iscsi.c` 定义了 iSCSI 类别的传输属性，该类别通过 TCP/IP 连接发送 SCSI 数据包。
.. kernel-doc:: drivers/scsi/scsi_transport_iscsi.c
   :export:

#### 串行连接 SCSI (SAS) 传输类别
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

文件 `drivers/scsi/scsi_transport_sas.c` 定义了串行连接 SCSI 的传输属性，这是一种面向大型高端系统的 SATA 变体。
SAS 传输类别包含用于处理 SAS 主机总线适配器 (HBA) 的通用代码、在驱动程序模型中对 SAS 拓扑的大致表示以及各种 sysfs 属性，这些属性将拓扑和管理接口暴露给用户空间。
除了基本的 SCSI 核心对象外，此传输类别还引入了两个额外的中间对象：由结构 `sas_phy` 定义的“输出”PHY 在 SAS HBA 或扩展器上，以及由结构 `sas_rphy` 定义的“输入”PHY 在 SAS 扩展器或终端设备上。请注意，这只是软件概念，PHY 和远程 PHY 的底层硬件是完全相同的。
在此代码中没有 SAS 端口的概念，用户可以根据端口标识符属性看到哪些 PHY 形成一个宽端口，该属性对于端口中的所有 PHY 都是相同的。
.. kernel-doc:: drivers/scsi/scsi_transport_sas.c
   :export:

#### SATA 传输类别
~~~~~~~~~~~~~~~~~~~~

SATA 传输由 libata 处理，该模块在这个目录中有自己的文档。

#### 平行 SCSI (SPI) 传输类别
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

文件 `drivers/scsi/scsi_transport_spi.c` 定义了传统 (快速/宽/超) SCSI 总线的传输属性。
```markdown
.. kernel-doc:: drivers/scsi/scsi_transport_spi.c
   :export:

SCSI RDMA (SRP) 传输类
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

文件 `drivers/scsi/scsi_transport_srp.c` 定义了用于通过远程直接内存访问 (RDMA) 的 SCSI 的传输属性。
.. kernel-doc:: drivers/scsi/scsi_transport_srp.c
   :export:

SCSI 下层
================

主机总线适配器传输类型
--------------------------------

许多现代设备控制器使用 SCSI 命令集作为协议，通过各种类型的物理连接与它们的设备进行通信。在 SCSI 术语中，能够承载 SCSI 命令的总线被称为“传输”，而连接到这种总线的控制器被称为“主机总线适配器”（HBA）。
调试传输
~~~~~~~~~~~~~~~

文件 `drivers/scsi/scsi_debug.c` 模拟了一个带有可变数量磁盘（或类似磁盘的设备）的主机适配器，这些设备共享同一块 RAM。它进行了大量的检查以确保我们没有混淆数据块，并且如果发现任何异常情况就会使内核崩溃。
为了更加逼真，模拟的设备具有 SAS 磁盘的传输属性。
更多文档请参阅 http://sg.danny.cz/sg/scsi_debug.html

待办事项
~~~~

并行（快速/宽/超）SCSI、USB、SATA、SAS、光纤通道、火线 (FireWire)、ATAPI 设备、InfiniBand、并行端口、netlink 等。
```
