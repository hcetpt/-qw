.. SPDX 许可证标识符: GPL-2.0 或 GFDL-1.1-no-invariants-or-later

.. _lirc_dev_intro:

************
简介
************

LIRC 代表 Linux 红外线遥控。LIRC 设备接口是一种双向传输原始红外数据和解码扫描码数据的接口，用于用户空间与内核空间之间的通信。本质上，它只是一个字符设备（/dev/lircX，其中 X = 0, 1, 2, ...），并且定义了多个标准的 `struct file_operations`。在传输原始红外数据和解码扫描码的过程中，关键的文件操作有读、写和 ioctl。此外，还可以将一个 BPF 程序附加到 LIRC 设备以解码原始红外数据为扫描码。

当驱动程序注册到 LIRC 时，dmesg 的输出示例：

.. code-block:: none

    $ dmesg | grep lirc_dev
    rc rc0: lirc_dev: 驱动程序 mceusb 在 minor = 0 注册，原始红外接收器，原始红外发射器

对于一个字符设备，您应该看到如下输出：

.. code-block:: none

    $ ls -l /dev/lirc*
    crw-rw---- 1 root root 248, 0 Jul 2 22:20 /dev/lirc0

请注意，`v4l-utils <https://git.linuxtv.org/v4l-utils.git/>`_ 包含了用于处理 LIRC 设备的工具：

- ir-ctl：可以接收原始红外信号并发送红外信号，以及查询 LIRC 设备的功能。
- ir-keytable：可以加载键映射；允许您设置 IR 内核协议；加载 BPF 红外解码器并测试红外解码。一些 BPF 红外解码器也已提供。

.. _lirc_modes:

**********
LIRC 模式
**********

LIRC 支持接收和发送红外码的一些模式，如以下表格所示：

.. _lirc-mode-scancode:
.. _lirc-scancode-flag-toggle:
.. _lirc-scancode-flag-repeat:

``LIRC_MODE_SCANCODE``

此模式用于发送和接收红外信号。
对于发送（即发送），创建一个 `struct lirc_scancode`，并将期望的扫描码设置在 `scancode` 成员中，将 `rc_proto` 设置为 :ref:`红外协议 <Remote_controllers_Protocols>`，其他所有成员设置为 0。将该结构写入 LIRC 设备。
对于接收，从 LIRC 设备读取 `struct lirc_scancode`。`scancode` 字段将被设置为接收到的扫描码，并且 `rc_proto` 中将设置 :ref:`红外协议 <Remote_controllers_Protocols>`。如果扫描码映射到一个有效的键码，则将其设置在 `keycode` 字段中，否则设置为 `KEY_RESERVED`。
`flags` 可以设置 `LIRC_SCANCODE_FLAG_TOGGLE`，如果在支持该特性的协议（例如 rc-5 和 rc-6）中设置了切换位，或者设置 `LIRC_SCANCODE_FLAG_REPEAT`，对于支持该特性的协议（例如 NEC）接收到重复信号时。
在Sanyo和NEC协议中，如果你按住遥控器上的按钮，而不是重复整个扫描码（scancode），遥控器会发送一个较短的消息，其中不包含扫描码，仅表示按钮被按住，称为“重复”（repeat）。当接收到这个消息时，会设置`LIRC_SCANCODE_FLAG_REPEAT`标志，并重复扫描码和按键码。

在NEC协议中，无法区分“按住按钮”与“反复按下同一个按钮”。RC-5和RC-6协议具有一个切换位（toggle bit）：

当按钮被释放并再次按下时，切换位会被反转。
如果切换位被设置，则设置`LIRC_SCANCODE_FLAG_TOGGLE`标志。
时间戳字段（`timestamp`）填充了解码扫描码时的时间纳秒（使用`CLOCK_MONOTONIC`）。

.. _lirc-mode-mode2:

`LIRC_MODE_MODE2`

驱动程序向用户空间返回一系列脉冲和空隙代码，作为一系列u32值。
这种模式仅用于红外接收。
高8位确定包类型，低24位为有效载荷。使用`LIRC_VALUE()`宏获取有效载荷，而`LIRC_MODE2()`宏将给出类型，具体如下：

`LIRC_MODE2_PULSE`

表示红外信号的存在时间（以微秒计），也称为“闪烁”（flash）。
`LIRC_MODE2_SPACE`

表示红外信号的缺失时间（以微秒计），也称为“间隔”（gap）。
`LIRC_MODE2_FREQUENCY`

如果通过`:ref:`lirc_set_measure_carrier_mode`启用了载波频率测量，则此包提供载波频率（以赫兹计）。
``LIRC_MODE2_TIMEOUT``

当使用 :ref:`lirc_set_rec_timeout` 设置的超时时间到期（由于未检测到红外信号）时，将发送此数据包，并附带无红外信号的微秒数。

``LIRC_MODE2_OVERFLOW``

表示红外接收器遇到了溢出情况，部分红外数据丢失。在此之后的红外数据应该是正确的。实际值并不重要，但内核将其设置为 0xffffff，以兼容 lircd。

.. _lirc-mode-pulse:

``LIRC_MODE_PULSE``

在脉冲模式下，一系列脉冲/间隔整数值通过 :ref:`lirc-write` 写入 lirc 设备。这些值是交替的脉冲和间隔长度，单位为微秒。第一个和最后一个条目必须是脉冲，因此条目的数量必须是奇数。
这种模式仅用于红外发送。

*************************************
LIRC_MODE_SCANCODE 使用的数据类型
*************************************

.. kernel-doc:: include/uapi/linux/lirc.h
    :identifiers: lirc_scancode rc_proto

********************
基于 BPF 的红外解码器
********************

内核支持解码最常见的 :ref:`红外协议 <Remote_controllers_Protocols>`，但也有很多不支持的协议。为了支持这些协议，可以加载一个 BPF 程序来完成解码。这只能在支持读取原始红外数据的 LIRC 设备上进行。
首先，使用 `bpf(2)`_ 系统调用并传入 ``BPF_LOAD_PROG`` 参数，加载类型为 ``BPF_PROG_TYPE_LIRC_MODE2`` 的程序。一旦附加到 LIRC 设备上，该程序将在每个脉冲、间隔或超时事件时被调用。BPF 程序的上下文是指向一个无符号整数的指针，这是 :ref:`LIRC_MODE_MODE2 <lirc-mode-mode2>` 的值。当程序解码了扫描码后，可以通过 BPF 函数 ``bpf_rc_keydown()`` 或 ``bpf_rc_repeat()`` 提交。鼠标或指针移动可以通过 ``bpf_rc_pointer_rel()`` 报告。
一旦获得了 ``BPF_PROG_TYPE_LIRC_MODE2`` BPF 程序的文件描述符，就可以使用 `bpf(2)`_ 系统调用将其附加到 LIRC 设备上。目标必须是 LIRC 设备的文件描述符，且附加类型必须是 ``BPF_LIRC_MODE2``。单个 LIRC 设备上同时最多可以附加 64 个 BPF 程序。

.. _bpf(2): http://man7.org/linux/man-pages/man2/bpf.2.html
