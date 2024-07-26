翻译为中文：

.. include:: <isonum.txt>

===================================
DPAA2 DPIO（数据路径I/O）概述
===================================

:版权所有: |copy| 2016-2018 NXP

本文档提供了Freescale DPAA2 DPIO驱动程序的概述。

简介
============

DPAA2 DPIO（数据路径I/O）是一个硬件对象，它提供了向网络接口和其他加速器发送和接收帧的接口。DPIO还为网络接口提供硬件缓冲池管理。
本文档提供了Linux DPIO驱动程序、其子组件及其API的概述。
请参阅
Documentation/networking/device_drivers/ethernet/freescale/dpaa2/overview.rst
以了解DPAA2及其在Linux中的通用DPAA2驱动架构的一般概述。

驱动程序概述
---------------

DPIO驱动程序绑定到fsl-mc总线上发现的DPIO对象，并提供了以下服务：

  A. 允许其他驱动程序，如以太网驱动程序，为其相应的对象发送和接收帧
  B. 允许驱动程序注册回调函数，当队列或通道上有数据可用时进行通知
  C. 允许驱动程序管理硬件缓冲池

Linux DPIO驱动程序主要由三个部分组成：
   DPIO对象驱动程序——管理DPIO对象的fsl-mc驱动程序

   DPIO服务——为其他Linux驱动程序提供服务的API

   QBman门户接口——发送门户命令并获取响应

下面的图示展示了DPIO驱动程序组件与其他DPAA2 Linux驱动程序组件之间的关系：

                                                   +------------+
                                                   | 操作系统网络 |
                                                   |   栈    |
                 +------------+                    +------------+
                 | 分配器  |. . . . . . .       |  以太网  |
                 |(DPMCP,DPBP)|                    |   (DPNI)   |
                 +-.----------+                    +---+---+----+
                  .          .                         ^   |
                 .            .           <数据可用, |   |<发送,接收>
                .              .           确认> |   | 
    +-------------+             .                      |   |
    | DPRC驱动程序 |              .    +--------+ +------------+
    |   (DPRC)    |               . . |DPIO对象| |DPIO服务|
    +----------+--+                   | 驱动程序 |-|  (DPIO)    |
               |                      +--------+ +------+-----+
               |<设备添加/移除>                 +------|-----+
               |                                 |   QBman    |
          +----+--------------+                  | 门户i/f |
          |   MC-bus驱动程序   |                  +------------+
          |                   |                     |
          | /soc/fsl-mc       |                     |
          +-------------------+                     |
                                                    |
 =========================================|=========|========================
                                        +-+--DPIO---|-----------+
                                        |           |           |
                                        |        QBman Portal   |
                                        +-----------------------+

==================================================================

DPIO对象驱动程序 (dpio-driver.c)
----------------------------------

   DPIO驱动程序组件在fsl-mc总线上注册以处理类型为“dpio”的对象。probe()的实现负责DPIO的基本初始化，包括映射DPIO区域（QBman软件门户）和初始化中断以及注册中断处理程序。DPIO驱动程序将探测到的DPIO注册给DPIO服务。
DPIO服务  (dpio-service.c, dpaa2-io.h)
------------------------------------------

   DPIO服务组件为DPAA2驱动程序（如以太网驱动程序）提供队列、通知和缓冲区管理服务。一个系统通常会为每个CPU分配1个DPIO对象，以便所有CPU上可以同时执行队列操作。
通知处理
      dpaa2_io_service_register()

      dpaa2_io_service_deregister()

      dpaa2_io_service_rearm()

队列操作
      dpaa2_io_service_pull_fq()

      dpaa2_io_service_pull_channel()

      dpaa2_io_service_enqueue_fq()

      dpaa2_io_service_enqueue_qd()

      dpaa2_io_store_create()

      dpaa2_io_store_destroy()

      dpaa2_io_store_next()

缓冲池管理
      dpaa2_io_service_release()

      dpaa2_io_service_acquire()

QBman门户接口 (qbman-portal.c)
---------------------------------------

   QBman门户组件提供了用于低级别硬件操作的API，例如：

      - 初始化Qman软件门户
      - 构建和发送门户命令
      - 门户中断配置和处理

QBman门户API不对其他驱动程序公开，仅被DPIO服务使用。
其他 (dpaa2-fd.h, dpaa2-global.h)
----------------------------------

   帧描述符和分散/聚集定义以及用于操纵它们的API在dpaa2-fd.h中定义。
接收结果结构体和解析API在dpaa2-global.h中定义。
