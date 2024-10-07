SPDX 许可证标识符: GPL-2.0+

====================
Xilinx SD-FEC 驱动程序
====================

概述
========

此驱动程序支持用于 Zynq |Ultrascale+ (TM)| RFSoC 的 SD-FEC 集成块。
.. |Ultrascale+ (TM)| unicode:: Ultrascale+ U+2122
   .. 带有商标符号

有关 SD-FEC 核心功能的完整描述，请参阅 `SD-FEC 产品指南 (PG256) <https://www.xilinx.com/cgi-bin/docs/ipdoc?c=sd_fec;v=latest;d=pg256-sdfec-integrated-block.pdf>`_

此驱动程序支持以下功能：

  - 获取集成块的配置和状态信息
  - 配置 LDPC 码
  - 配置 Turbo 解码
  - 监控错误

SD-FEC 驱动程序缺失的功能、已知问题及限制如下：

  - 每次仅允许一个文件句柄打开驱动程序实例
  - SD-FEC 集成块的复位不由该驱动程序控制
  - 不支持共享 LDPC 码表循环

设备树条目描述在：
`linux-xlnx/Documentation/devicetree/bindings/misc/xlnx,sd-fec.yaml <https://github.com/Xilinx/linux-xlnx/blob/master/Documentation/devicetree/bindings/misc/xlnx%2Csd-fec.yaml>`_

操作模式
------------------

驱动程序与 SD-FEC 核心以两种操作模式工作：

  - 运行时配置
  - 可编程逻辑 (PL) 初始化

运行时配置
~~~~~~~~~~~~~~~~~~~~~~

对于运行时配置，驱动程序的作用是使软件应用程序能够执行以下操作：

	- 加载 Turbo 解码或 LDPC 编码或解码的配置参数
	- 激活 SD-FEC 核心
	- 监控 SD-FEC 核心的错误
	- 获取 SD-FEC 核心的状态和配置

可编程逻辑 (PL) 初始化
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

对于 PL 初始化，支持逻辑加载 Turbo 解码或 LDPC 编码或解码的配置参数。驱动程序的作用是使软件应用程序能够执行以下操作：

	- 激活 SD-FEC 核心
	- 监控 SD-FEC 核心的错误
	- 获取 SD-FEC 核心的状态和配置

驱动结构
================

驱动程序提供了一个平台设备，其中提供了 `probe` 和 `remove` 操作：
- probe: 使用设备树条目更新配置寄存器，并确定核心当前激活状态（例如，核心是否被旁路或已启动）
驱动程序定义了以下驱动文件操作以提供用户应用程序接口：

  - open: 实现每个 SD-FEC 实例一次只能打开一个文件描述符的限制
  - release: 允许在当前文件描述符关闭后打开另一个文件描述符
  - poll: 提供监控 SD-FEC 错误事件的方法
  - unlocked_ioctl: 提供以下 ioctl 命令，使应用程序能够配置 SD-FEC 核心：

		- :c:macro:`XSDFEC_START_DEV`
		- :c:macro:`XSDFEC_STOP_DEV`
		- :c:macro:`XSDFEC_GET_STATUS`
		- :c:macro:`XSDFEC_SET_IRQ`
		- :c:macro:`XSDFEC_SET_TURBO`
		- :c:macro:`XSDFEC_ADD_LDPC_CODE_PARAMS`
		- :c:macro:`XSDFEC_GET_CONFIG`
		- :c:macro:`XSDFEC_SET_ORDER`
		- :c:macro:`XSDFEC_SET_BYPASS`
		- :c:macro:`XSDFEC_IS_ACTIVE`
		- :c:macro:`XSDFEC_CLEAR_STATS`
		- :c:macro:`XSDFEC_SET_DEFAULT_CONFIG`

驱动使用
============

概述
--------

打开驱动程序后，用户应确定需要执行哪些操作来配置和激活 SD-FEC 核心并确定驱动程序的配置。
以下概述了用户应执行的操作流程：

  - 确定配置
  - 如果未按预期配置，则设置顺序
  - 设置 Turbo 解码、LPDC 编码或解码参数，具体取决于 SD-FEC 核心如何配置以及 SD-FEC 是否未为 PL 初始化配置
  - 如果尚未启用，则启用中断
  - 如果需要，则旁路 SD-FEC 核心
  - 如果尚未启动，则启动 SD-FEC 核心
  - 获取 SD-FEC 核心状态
  - 监控中断
  - 停止 SD-FEC 核心

注意：当监控中断时，如果检测到需要复位的关键错误，驱动程序将需要加载默认配置
确定配置
-----------------------

使用 ioctl :c:macro:`XSDFEC_GET_CONFIG` 来确定 SD-FEC 核心的配置
设置顺序
-------------

设置顺序决定了块从输入到输出的顺序变化
设置顺序通过使用 ioctl :c:macro:`XSDFEC_SET_ORDER` 完成

只有满足以下限制条件时才能设置顺序：

	- 结构 :c:type:`xsdfec_status <xsdfec_status>` 中由 ioctl :c:macro:`XSDFEC_GET_STATUS` 填充的 `state` 成员表明 SD-FEC 核心尚未启动

添加 LDPC 码
--------------

以下步骤说明了如何向 SD-FEC 核心添加 LDPC 码：

	- 使用自动生成的参数填充所需 LDPC 码的 :c:type:`struct xsdfec_ldpc_params <xsdfec_ldpc_params>`
	- 设置 LPDC 参数及其在结构 :c:type:`struct xsdfec_ldpc_params <xsdfec_ldpc_params>` 中的 SC、QA 和 LA 表偏移量
	- 在结构 :c:type:`struct xsdfec_ldpc_params <xsdfec_ldpc_params>` 中设置所需的 Code Id 值
	- 使用 ioctl :c:macro:`XSDFEC_ADD_LDPC_CODE_PARAMS` 添加 LPDC 码参数
	- 对于应用的 LPDC 码参数，使用函数 :c:func:`xsdfec_calculate_shared_ldpc_table_entry_size` 计算共享 LPDC 码表的大小。这使用户能够确定共享表的使用情况，以便在选择下一个 LDPC 码参数的表偏移量时可以选择未使用的表区域
- 对每个 LDPC 码参数重复上述步骤
添加LDPC编码只能在满足以下限制的情况下进行：

- 通过ioctl :c:macro:`XSDFEC_GET_CONFIG` 填充的 :c:type:`struct xsdfec_config <xsdfec_config>` 中的 ``code`` 成员表示SD-FEC核心配置为LDPC
- 通过ioctl :c:macro:`XSDFEC_GET_CONFIG` 填充的 :c:type:`struct xsdfec_config <xsdfec_config>` 中的 ``code_wr_protect`` 成员表示未启用写保护
- 通过ioctl :c:macro:`XSDFEC_GET_STATUS` 填充的 :c:type:`struct xsdfec_status <xsdfec_status>` 中的 ``state`` 成员表示SD-FEC核心尚未启动

设置Turbo解码
--------------

配置Turbo解码参数是通过使用ioctl :c:macro:`XSDFEC_SET_TURBO` 并使用自动生成的参数填充 :c:type:`struct xsdfec_turbo <xsdfec_turbo>` 来完成，以设置所需的Turbo编码。添加Turbo解码只能在满足以下限制的情况下进行：

- 通过ioctl :c:macro:`XSDFEC_GET_CONFIG` 填充的 :c:type:`struct xsdfec_config <xsdfec_config>` 中的 ``code`` 成员表示SD-FEC核心配置为TURBO
- 通过ioctl :c:macro:`XSDFEC_GET_STATUS` 填充的 :c:type:`struct xsdfec_status <xsdfec_status>` 中的 ``state`` 成员表示SD-FEC核心尚未启动

启用中断
---------

启用或禁用中断是通过使用ioctl :c:macro:`XSDFEC_SET_IRQ` 来完成的。传递给ioctl的参数 :c:type:`struct xsdfec_irq <xsdfec_irq>` 的成员用于设置和清除不同类别的中断。中断类别受以下控制：

  - ``enable_isr`` 控制 ``tlast`` 中断
  - ``enable_ecc_isr`` 控制ECC中断

如果通过ioctl :c:macro:`XSDFEC_GET_CONFIG` 填充的 :c:type:`struct xsdfec_config <xsdfec_config>` 中的 ``code`` 成员表示SD-FEC核心配置为TURBO，则不需要启用ECC错误

旁路SD-FEC
----------

旁路SD-FEC是通过使用ioctl :c:macro:`XSDFEC_SET_BYPASS` 来完成的。旁路SD-FEC只能在满足以下限制的情况下进行：

- 通过ioctl :c:macro:`XSDFEC_GET_STATUS` 填充的 :c:type:`struct xsdfec_status <xsdfec_status>` 中的 ``state`` 成员表示SD-FEC核心尚未启动

启动SD-FEC核心
---------------

通过使用ioctl :c:macro:`XSDFEC_START_DEV` 启动SD-FEC核心。

获取SD-FEC状态
---------------

通过使用ioctl :c:macro:`XSDFEC_GET_STATUS` 获取设备的SD-FEC状态，该ioctl将填充 :c:type:`struct xsdfec_status <xsdfec_status>` 结构体。

监控中断
------------

- 使用poll系统调用来监控中断。poll系统调用等待中断唤醒它或者在没有中断发生时超时。
- 返回时Poll ``revents`` 将指示状态和/或状态是否已更新
  - ``POLLPRI`` 表示发生严重错误，并且用户应使用 :c:macro:`XSDFEC_GET_STATUS` 和 :c:macro:`XSDFEC_GET_STATS` 进行确认
  - ``POLLRDNORM`` 表示发生非严重错误，并且用户应使用 :c:macro:`XSDFEC_GET_STATS` 进行确认
- 通过使用ioctl :c:macro:`XSDFEC_GET_STATS` 获取统计信息
  - 对于严重错误， :c:type:`struct xsdfec_stats <xsdfec_stats>` 中的 ``isr_err_count`` 或 ``uecc_count`` 成员非零
  - 对于非严重错误， :c:type:`struct xsdfec_stats <xsdfec_stats>` 中的 ``cecc_count`` 成员非零
- 通过使用ioctl :c:macro:`XSDFEC_GET_STATUS` 获取状态
  - 对于严重错误， :c:type:`xsdfec_status <xsdfec_status>` 的 ``state`` 成员将指示需要重置
- 通过使用ioctl :c:macro:`XSDFEC_CLEAR_STATS` 清除统计信息

如果检测到需要重置的严重错误，应用程序需要调用ioctl :c:macro:`XSDFEC_SET_DEFAULT_CONFIG`，在重置之后无需调用ioctl :c:macro:`XSDFEC_STOP_DEV`。

注意：使用poll系统调用可以防止使用 :c:macro:`XSDFEC_GET_STATS` 和 :c:macro:`XSDFEC_GET_STATUS` 忙碌循环

停止SD-FEC核心
---------------

通过使用ioctl :c:macro:`XSDFEC_STOP_DEV` 停止设备。

设置默认配置
--------------

通过使用ioctl :c:macro:`XSDFEC_SET_DEFAULT_CONFIG` 加载默认配置来恢复驱动程序。

限制
-------

用户不应复制SD-FEC设备文件句柄，例如fork()或dup()一个已经创建了SD-FEC文件句柄的过程。

驱动程序IOCTLs
==============

.. c:macro:: XSDFEC_START_DEV
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_START_DEV

.. c:macro:: XSDFEC_STOP_DEV
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_STOP_DEV

.. c:macro:: XSDFEC_GET_STATUS
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_GET_STATUS

.. c:macro:: XSDFEC_SET_IRQ
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_SET_IRQ

.. c:macro:: XSDFEC_SET_TURBO
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_SET_TURBO

.. c:macro:: XSDFEC_ADD_LDPC_CODE_PARAMS
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_ADD_LDPC_CODE_PARAMS

.. c:macro:: XSDFEC_GET_CONFIG
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_GET_CONFIG

.. c:macro:: XSDFEC_SET_ORDER
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_SET_ORDER

.. c:macro:: XSDFEC_SET_BYPASS
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_SET_BYPASS

.. c:macro:: XSDFEC_IS_ACTIVE
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_IS_ACTIVE

.. c:macro:: XSDFEC_CLEAR_STATS
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_CLEAR_STATS

.. c:macro:: XSDFEC_GET_STATS
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_GET_STATS

.. c:macro:: XSDFEC_SET_DEFAULT_CONFIG
.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :doc: XSDFEC_SET_DEFAULT_CONFIG

驱动程序类型定义
==================

.. kernel-doc:: include/uapi/misc/xilinx_sdfec.h
   :internal:
