```rst
.. include:: <isonum.txt>

===================================
DPAA2 DPIO（数据路径I/O）概述
===================================

:版权: |copy| 2016-2018 NXP

本文档提供了Freescale DPAA2 DPIO驱动的概述。

介绍
============

DPAA2 DPIO（数据路径I/O）是一个硬件对象，提供接口用于在网络接口和其他加速器之间入队和出队帧。DPIO还为网络接口提供硬件缓冲池管理。
本文档提供了Linux DPIO驱动及其子组件和API的概述。
请参阅`Documentation/networking/device_drivers/ethernet/freescale/dpaa2/overview.rst`以了解DPAA2及其在Linux中的通用架构的一般概述。

驱动概述
---------------

DPIO驱动绑定到fsl-mc总线上发现的DPIO对象，并提供以下服务：

  A. 允许其他驱动（如以太网驱动）为其各自的对象入队和出队帧
  B. 允许驱动注册回调函数，在队列或通道上有数据可用时进行通知
  C. 允许驱动管理硬件缓冲池

Linux DPIO驱动由三个主要组件组成：
   DPIO对象驱动——管理DPIO对象的fsl-mc驱动

   DPIO服务——为其他Linux驱动提供服务的API

   QBman门户接口——发送门户命令并获取响应

```
         fsl-mc          其他
          总线           驱动
           |               |
       +---+----+   +------+-----+
       |DPIO obj|   |DPIO service|
       | driver |---|  (DPIO)    |
       +--------+   +------+-----+
                            |
                     +------+-----+
                     |    QBman   |
                     | portal i/f |
                     +------------+
                            |
                         硬件
```

下图展示了DPIO驱动组件与其他DPAA2 Linux驱动组件的关系：

```
                                                  +------------+
                                                  | OS Network |
                                                  |   Stack    |
                 +------------+                    +------------+
                 | Allocator  |. . . . . . .       |  Ethernet  |
                 |(DPMCP,DPBP)|                    |   (DPNI)   |
                 +-.----------+                    +---+---+----+
                  .          .                         ^   |
                 .            .           <data avail, |   |<enqueue,
                .              .           tx confirm> |   | dequeue>
    +-------------+             .                      |   |
    | DPRC driver |              .    +--------+ +------------+
    |   (DPRC)    |               . . |DPIO obj| |DPIO service|
    +----------+--+                   | driver |-|  (DPIO)    |
               |                      +--------+ +------+-----+
               |<dev add/remove>                 +------|-----+
               |                                 |   QBman    |
          +----+--------------+                  | portal i/f |
          |   MC-bus driver   |                  +------------+
          |                   |                     |
          | /soc/fsl-mc       |                     |
          +-------------------+                     |
                                                    |
 =========================================|=========|========================
                                        +-+--DPIO---|-----------+
                                        |           |           |
                                        |        QBman Portal   |
                                        +-----------------------+
```

==========================================================================

DPIO对象驱动（dpio-driver.c）
----------------------------------

   dpio-driver组件注册到fsl-mc总线以处理类型为“dpio”的对象。probe()实现负责基本初始化DPIO，包括映射DPIO区域（QBman软件门户）、初始化中断并注册中断处理程序。dpio-driver将探测到的DPIO注册到dpio-service中。

DPIO服务（dpio-service.c, dpaa2-io.h）
------------------------------------------

   dpio服务组件为DPAA2驱动（如以太网驱动）提供队列、通知和缓冲管理服务。系统通常会为每个CPU分配一个DPIO对象，以便所有CPU可以同时执行队列操作。

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

QBman门户接口（qbman-portal.c）
---------------------------------------

   qbman-portal组件提供API以进行低级别的硬件操作，例如：

      - 初始化Qman软件门户
      - 构建和发送门户命令
      - 配置和处理门户中断

   qbman-portal API不对其他驱动公开，仅由dpio-service使用。

其他（dpaa2-fd.h, dpaa2-global.h）
----------------------------------

   帧描述符和散集定义以及用于操纵它们的API定义在dpaa2-fd.h中。
   出队结果结构和解析API定义在dpaa2-global.h中。
```
