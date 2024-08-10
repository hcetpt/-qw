SPDX 许可证标识符: GPL-2.0

===========================================
用户空间块设备驱动程序 (ublk 驱动程序)
===========================================

概述
========

ublk 是一个通用框架，用于从用户空间实现块设备逻辑。其背后的动机是将虚拟块驱动程序移至用户空间，例如 loop、nbd 和类似的驱动程序可以非常有帮助。它有助于实现新的虚拟块设备，如 ublk-qcow2（已经有一些尝试在内核中实现 qcow2 驱动程序）。用户空间块设备具有吸引力的原因包括：

- 可以用多种编程语言编写
- 可以使用内核中不可用的库
- 可以用应用程序开发者熟悉的工具进行调试
- 出现崩溃时不会导致内核恐慌
- 错误可能比内核代码中的错误具有更低的安全影响
- 可以独立于内核安装和更新
- 可以方便地用用户指定的参数/设置来模拟块设备以供测试/调试目的

ublk 块设备（`/dev/ublkb*`）由 ublk 驱动程序添加。对设备上的任何 I/O 请求都会转发到 ublk 用户空间程序。为了方便起见，在本文档中，“ublk 服务器”是指通用 ublk 用户空间程序。“ublksrv”[#userspace]_ 是其中一个实现。它提供了 `libublksrv` [＃userspace_lib]_ 库，以便于开发特定的用户块设备，同时也包含了像 loop 和 null 这样的通用类型块设备。Richard W.M. Jones 根据 `libublksrv` [＃userspace_lib]_ 编写了用户空间的 nbd 设备 `nbdublk` [＃userspace_nbdublk]_。当 I/O 在用户空间处理完毕后，结果会反馈给驱动程序，从而完成请求周期。这样，所有特定的 I/O 处理逻辑完全由用户空间完成，例如 loop 的 I/O 处理、NBD 的 I/O 通信或 qcow2 的 I/O 映射。
``/dev/ublkb*`` 由基于blk-mq请求的驱动程序驱动。每个请求都会分配一个队列宽度唯一的标签。ublk服务器也为每个IO分配唯一的标签，这些标签与``/dev/ublkb*``的IO一一对应。
IO请求转发和IO处理结果提交都是通过``io_uring``穿透命令完成的；这就是为什么ublk也是一种基于io_uring的块驱动程序。已经观察到使用io_uring穿透命令可以提供比块IO更好的IOPS；因此ublk是用户空间块设备的一种高性能实现：不仅IO请求通信是通过io_uring完成的，而且ublk服务器首选的IO处理方式也是基于io_uring的。
ublk提供了控制接口来设置/获取ublk块设备参数
该接口可扩展且与kabi兼容：基本上可以通过该接口设置/获取任何ublk请求队列的参数或ublk通用功能参数。因此，ublk是一个通用的用户空间块设备框架。
例如，很容易从用户空间设置带有指定块参数的ublk设备
使用ublk
========

ublk需要用户空间的ublk服务器来处理实际的块设备逻辑
以下是使用``ublksrv``提供基于ublk的循环设备的例子：
- 添加一个设备::
     
     ublk add -t loop -f ublk-loop.img
     
- 使用xfs格式化，然后使用它::
     
     mkfs.xfs /dev/ublkb0
     mount /dev/ublkb0 /mnt
     # 进行任意操作。所有IO都由io_uring处理
     ..
     umount /mnt
     
- 列出带有信息的设备::
     
     ublk list
     
- 删除设备::
     
     ublk del -a
     ublk del -n $ublk_dev_id
     
有关详细用法，请参阅``ublksrv``的README文件 [#userspace_readme]_
设计
=====

控制平面
---------

ublk驱动程序提供全局杂项设备节点（``/dev/ublk-control``），用于借助几种控制命令管理和控制ublk设备：

- ``UBLK_CMD_ADD_DEV``

  添加一个ublk字符设备（``/dev/ublkc*``），该设备与ublk服务器进行IO命令通信。基本设备信息会随此命令一起发送。它设置了UAPI结构``ublksrv_ctrl_dev_info``，例如``nr_hw_queues``、``queue_depth``和最大IO请求缓冲区大小，这些信息会与驱动程序协商后反馈给服务器。
当这条命令完成时，基本的设备信息变为不可更改。
- ``UBLK_CMD_SET_PARAMS`` / ``UBLK_CMD_GET_PARAMS``

  设置或获取设备参数，这些参数可以是通用特性的相关参数，也可以是请求队列限制的相关参数，但不能是I/O逻辑的具体参数，因为驱动程序不处理任何I/O逻辑。此命令必须在发送``UBLK_CMD_START_DEV``之前发送。
- ``UBLK_CMD_START_DEV``

  在服务器准备好用户空间资源（如为每个队列创建pthread和io_uring以处理ublk I/O）之后，发送此命令给驱动程序以便分配并暴露``/dev/ublkb*``。通过``UBLK_CMD_SET_PARAMS``设置的参数将应用于设备的创建。
- ``UBLK_CMD_STOP_DEV``

  暂停``/dev/ublkb*``上的I/O操作并移除该设备。当此命令返回时，ublk服务器将释放资源（例如销毁每个队列的pthread与io_uring）。
- ``UBLK_CMD_DEL_DEV``

  移除``/dev/ublkc*``。当此命令返回时，已分配的ublk设备编号可以被重新使用。
- ``UBLK_CMD_GET_QUEUE_AFFINITY``

  当添加``/dev/ublkc``时，驱动程序会创建块层标签集，这样就可以获取每个队列的亲和性信息。服务器发送``UBLK_CMD_GET_QUEUE_AFFINITY``来检索队列亲和性信息。它可以高效地设置每个队列上下文，例如绑定亲和CPU与I/O pthread，并尝试在I/O线程上下文中分配缓冲区。
- ``UBLK_CMD_GET_DEV_INFO``

  用于通过``ublksrv_ctrl_dev_info``检索设备信息。服务器有责任在用户空间中保存特定于I/O目标的信息。
- ``UBLK_CMD_GET_DEV_INFO2``
  与``UBLK_CMD_GET_DEV_INFO``具有相同的目的，但是ublk服务器必须为内核提供``/dev/ublkc*``字符设备的路径来进行权限检查，此命令是为了支持非特权ublk设备而添加的，并且与``UBLK_F_UNPRIVILEGED_DEV``一起引入。
只有请求设备的所有者才能检索设备信息。
如何处理用户空间/内核兼容性：

  1) 如果内核能够处理``UBLK_F_UNPRIVILEGED_DEV``

    如果ublk服务器支持``UBLK_F_UNPRIVILEGED_DEV``：

    ublk服务器应发送``UBLK_CMD_GET_DEV_INFO2``，无论何时非特权应用程序需要查询当前用户拥有的设备，当应用程序不知道是否设置了``UBLK_F_UNPRIVILEGED_DEV``时（因为能力信息是无状态的），并且应用程序应该始终通过``UBLK_CMD_GET_DEV_INFO2``来检索它。

    如果ublk服务器不支持``UBLK_F_UNPRIVILEGED_DEV``：

    始终向内核发送``UBLK_CMD_GET_DEV_INFO``，并且用户无法使用``UBLK_F_UNPRIVILEGED_DEV``的功能。

  2) 如果内核不能处理``UBLK_F_UNPRIVILEGED_DEV``

    如果ublk服务器支持``UBLK_F_UNPRIVILEGED_DEV``：

    首先尝试``UBLK_CMD_GET_DEV_INFO2``，将会失败，然后鉴于``UBLK_F_UNPRIVILEGED_DEV``不能设置的情况下，需要重试``UBLK_CMD_GET_DEV_INFO``。

    如果ublk服务器不支持``UBLK_F_UNPRIVILEGED_DEV``：

    始终向内核发送``UBLK_CMD_GET_DEV_INFO``，并且用户无法使用``UBLK_F_UNPRIVILEGED_DEV``的功能。

- ``UBLK_CMD_START_USER_RECOVERY``

  如果启用了``UBLK_F_USER_RECOVERY``特性，则此命令有效。此命令在接受旧进程退出后、ublk设备被静止以及``/dev/ublkc*``被释放之后被接受。用户应在启动重新打开``/dev/ublkc*``的新进程之前发送此命令。当此命令返回时，ublk设备已准备好供新进程使用。
- `UBLK_CMD_END_USER_RECOVERY`

  当启用`UBLK_F_USER_RECOVERY`特性时，此命令有效。此命令可在ublk设备静默后，并且一个新的进程已打开`/dev/ublkc*`并使所有ublk队列准备好之后被接受。当此命令返回时，ublk设备解除静默状态，新的I/O请求被传递给新进程。
- 用户恢复功能描述

  为用户恢复新增了两个特性：`UBLK_F_USER_RECOVERY`和`UBLK_F_USER_RECOVERY_REISSUE`。
  设置`UBLK_F_USER_RECOVERY`后，在一个ubq_daemon（ublk服务器的I/O处理器）死亡后，ublk在整个恢复阶段不会删除`/dev/ublkb*`，并且保留ublk设备ID。由ublk服务器负责根据自身知识恢复设备上下文。
  尚未向用户空间发出的请求将被重新排队。已经向用户空间发出的请求将被中止。
  设置`UBLK_F_USER_RECOVERY_REISSUE`后，在一个ubq_daemon（ublk服务器的I/O处理器）死亡后，与`UBLK_F_USER_RECOVERY`相反，已经向用户空间发出的请求将被重新排队，并在处理完`UBLK_CMD_END_USER_RECOVERY`命令后重新发送到新进程。
  `UBLK_F_USER_RECOVERY_REISSUE`专为能够容忍双重写入的后端设计，因为驱动程序可能会两次发出相同的I/O请求。对于只读文件系统或虚拟机后端可能有用。
- 非特权ublk设备支持通过传递`UBLK_F_UNPRIVILEGED_DEV`标志来实现。
  一旦设置了该标志，所有控制命令都可以由非特权用户发送。除了`UBLK_CMD_ADD_DEV`命令外，对于其他所有控制命令，ublk驱动程序会在指定的字符设备（`/dev/ublkc*`）上进行权限检查，为此，需要在来自ublk服务器的这些命令的有效载荷中提供字符设备的路径。这样，ublk设备成为容器感知的，一个容器中创建的设备只能在这个容器内部进行控制/访问。
- 数据平面

  ublk服务器需要为每个队列创建IO线程和io_uring以通过io_uring传递方式处理I/O命令。每个队列的IO线程专注于I/O处理，不应处理任何控制和管理任务。
  每个I/O由一个唯一的标签标识，该标签与`/dev/ublkb*`的I/O请求一一对应。
`ublksrv_io_desc` 的 UAPI 结构被定义用于描述来自驱动程序的每个 I/O。在 `/dev/ublkc*` 上提供了一个固定的内存映射区域（数组），用于向服务器导出 I/O 信息，例如 I/O 偏移量、长度、操作/标志和缓冲区地址。每个 `ublksrv_io_desc` 实例都可以通过队列 ID 和 I/O 标签直接索引。

以下 I/O 命令是通过 io_uring 传递命令进行通信的，并且每个命令仅用于转发 I/O 并使用命令数据中指定的 I/O 标签提交结果：

- `UBLK_IO_FETCH_REQ`

  由服务器 I/O 线程发送以获取将要发往 `/dev/ublkb*` 的未来传入 I/O 请求。此命令仅从服务器 I/O 线程向 ublk 驱动程序发送一次，以设置 I/O 转发环境。
- `UBLK_IO_COMMIT_AND_FETCH_REQ`

  当一个 I/O 请求发往 `/dev/ublkb*` 时，驱动程序将该 I/O 的 `ublksrv_io_desc` 存储到指定的映射区域；然后，先前收到的具有该 I/O 标签的 I/O 命令（无论是 `UBLK_IO_FETCH_REQ` 还是 `UBLK_IO_COMMIT_AND_FETCH_REQ`）完成，这样服务器就可以通过 io_uring 获取 I/O 通知。
  在服务器处理完 I/O 后，其结果通过回送 `UBLK_IO_COMMIT_AND_FETCH_REQ` 到驱动程序来提交。一旦 ublkdrv 收到此命令，它会解析结果并完成对 `/dev/ublkb*` 的请求。同时为具有相同 I/O 标签的未来请求设置环境。也就是说，`UBLK_IO_COMMIT_AND_FETCH_REQ` 既用于获取请求又用于提交 I/O 结果。
- `UBLK_IO_NEED_GET_DATA`

  使用 `UBLK_F_NEED_GET_DATA` 时，WRITE 请求将首先不带数据拷贝地发送给 ublk 服务器。然后，ublk 服务器的 I/O 后端接收到请求并可以分配数据缓冲区，并将其地址嵌入这个新的 I/O 命令中。当内核驱动程序接收到命令后，从请求页面到后端缓冲区的数据拷贝完成。最后，后端再次接收带有要写入的数据的请求，从而真正处理请求。
  `UBLK_IO_NEED_GET_DATA` 添加了一个额外的往返和一个 io_uring_enter() 系统调用。任何认为这可能会降低性能的用户都不应该启用 UBLK_F_NEED_GET_DATA。默认情况下，ublk 服务器为每个 I/O 预先分配 I/O 缓冲区。任何新项目都应该尝试使用这个缓冲区与 ublk 驱动程序进行通信。然而，现有的项目可能无法适应或无法消费新的缓冲区接口；这就是为什么添加了这个命令以实现向后兼容性，以便现有项目仍然可以消费现有缓冲区。
- ublk 服务器 I/O 缓冲区与 ublk 块 I/O 请求之间的数据拷贝

  驱动程序需要首先将块 I/O 请求页面复制到服务器缓冲区（页面）中，以便在通知服务器即将进行的 I/O 之前处理 WRITE 操作，这样服务器就可以处理 WRITE 请求。
  当服务器处理 READ 请求并向服务器发送 `UBLK_IO_COMMIT_AND_FETCH_REQ` 时，ublkdrv 需要将服务器缓冲区（页面）读取的内容复制到 I/O 请求页面中。

未来开发
=========

零拷贝
-------

零拷贝是 nbd、fuse 或类似驱动程序的一般要求。Xiaoguang 提到的一个问题是在现有的内存管理接口下，映射到用户空间的页面不能再在内核中重新映射。这会在直接 I/O 发往 `/dev/ublkb*` 时发生。他还报告说，对于大请求（I/O 大小 >= 256 KB），零拷贝可能会带来很大的好处。

参考文献
========

.. [#userspace] https://github.com/ming1/ubdsrv

.. [#userspace_lib] https://github.com/ming1/ubdsrv/tree/master/lib

.. [#userspace_nbdublk] https://gitlab.com/rwmjones/libnbd/-/tree/nbdublk

.. [#userspace_readme] https://github.com/ming1/ubdsrv/blob/master/README

.. [#stefan] https://lore.kernel.org/linux-block/YoOr6jBfgVm8GvWg@stefanha-x1.localdomain/

.. [#xiaoguang] https://lore.kernel.org/linux-block/YoOr6jBfgVm8GvWg@stefanha-x1.localdomain/
