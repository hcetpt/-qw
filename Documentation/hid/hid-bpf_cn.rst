SPDX 许可证标识符: GPL-2.0

=======
HID-BPF
=======

HID 是一种用于输入设备的标准协议，但某些设备可能需要自定义调整，传统上是通过内核驱动程序修复来完成的。使用 eBPF 能力可以加快开发速度，并为现有的 HID 接口添加新功能。
.. contents::
    :local:
    :depth: 2

何时（及为何）使用 HID-BPF
============================

在以下情况下，使用 HID-BPF 比标准内核驱动程序修复更好：

游戏杆的死区
-------------

假设你有一个逐渐变旧的游戏杆，它通常会在其中性点附近抖动。这通常通过在应用程序级别为该特定轴添加一个“死区”来进行过滤。
使用 HID-BPF，我们可以在内核中直接应用这种过滤，这样当输入控制器没有其他活动时，用户空间不会被唤醒。
当然，由于这个死区是针对特定设备的，我们无法为所有相同的游戏杆创建一个通用修复方案。为这种情况添加一个自定义内核 API（例如，通过添加一个 sysfs 条目）并不能保证这个新的内核 API 会被广泛采用和维护。
HID-BPF 允许用户空间程序加载程序本身，确保只有在有用户的情况下才会加载自定义 API。

报告描述符的简单修正
-------------------

在 HID 树中，一半的驱动程序仅修正报告描述符中的一个键或一个字节。这些修正都需要内核补丁，并且需要将补丁合并到发布版本中，这对用户来说是一个漫长而痛苦的过程。
我们可以通过提供一个 eBPF 程序来减轻这一负担。一旦这样的程序经过用户验证，我们可以将源代码嵌入内核树中，并直接加载 eBPF 程序，而不是为它加载一个特定的内核模块。
注意：eBPF 程序的分发及其在内核中的包含尚未完全实现。

添加需要新内核 API 的新功能
------------------------------

一个这样的功能示例是 Universal Stylus Interface (USI) 笔。基本上，USI 笔需要一个新的内核 API，因为存在我们的 HID 和输入堆栈不支持的新通信通道。
与其使用 hidraw 或创建新的 sysfs 条目或 ioctl，我们可以依赖 eBPF 来使内核 API 受消费者控制，并避免每次有事件发生时唤醒用户空间带来的性能影响。
将设备转换为其他形式并从用户空间进行控制
----------------------------------------------

内核对HID项到evdev位的映射相对静态，无法决定动态地将某个给定设备转换为其他东西，因为它缺乏所需的上下文，并且任何这样的转换都无法被用户空间撤销（甚至发现）。然而，对于某些设备而言，这种静态定义方式使其变得几乎无用。例如，微软Surface Dial是一个带有触觉反馈的按钮，在目前的情况下几乎不可用。

通过eBPF，用户空间可以将该设备转换为鼠标，并将旋转事件转换为滚轮事件。此外，用户空间程序可以根据上下文设置或取消触觉反馈。例如，如果屏幕上显示了一个菜单，我们可能需要每15度提供一次触觉点击。但在网页滚动时，用户在设备以最高分辨率发出事件时体验更好。

防火墙
------

如果我们想阻止其他用户访问设备的某个特定功能怎么办？（假设可能存在一个有问题的固件更新入口）

借助eBPF，我们可以拦截发送给设备的所有HID命令，并选择是否验证这些命令。这也有助于同步用户空间与内核/BPF程序之间的状态，因为我们能够拦截所有传入的命令。

追踪
-----

最后一个用途是追踪事件以及我们利用BPF进行总结和分析的所有有趣操作。目前，追踪依赖于hidraw。尽管它工作良好，但存在几个问题：

1. 如果驱动程序没有导出hidraw节点，我们就无法进行追踪（eBPF在这方面将是“神级模式”，因此可能会引起一些关注）。
2. hidraw无法捕获其他进程对设备的请求，这意味着我们需要在内核中添加printk来理解正在发生的事情。

HID-BPF的高层次视图
=====================

HID-BPF的主要思想在于它在字节数组级别上工作。因此，HID报告及其描述符的所有解析必须由加载eBPF程序的用户空间组件实现。
例如，在上述的死区操纵杆中，需要知道数据流中的哪些字段需要设置为“0”，这需要用户空间来计算。由此得出的一个推论是，HID-BPF 不了解内核中可用的其他子系统。*你不能直接通过 eBPF 发出输入事件*

当一个 BPF 程序需要发出输入事件时，它需要与 HID 协议进行通信，并依赖于 HID 内核处理将 HID 数据转换为输入事件。

内核树中的 HID-BPF 程序和 `udev-hid-bpf`
=============================================

官方设备修复程序作为源代码包含在内核树的 `drivers/hid/bpf/progs` 目录中。这允许在 `tools/testing/selftests/hid` 中为它们添加自测用例。
然而，这些对象文件的编译并不包含在一个常规的内核编译过程中，因为它们需要外部工具加载。目前这个工具是 `udev-hid-bpf <https://libevdev.pages.freedesktop.org/udev-hid-bpf/index.html>`_。
为了方便起见，该外部仓库在其自己的 `src/bpf/stable` 目录中复制了来自 `drivers/hid/bpf/progs` 的文件。这样分发版本就不必拉取整个内核源码树来发布和打包这些 HID-BPF 修复。`udev-hid-bpf` 还可以根据用户运行的内核处理多个对象文件。

可用的程序类型
===========================

HID-BPF 是构建在 BPF 之上的，这意味着我们使用 bpf struct_ops 方法来声明我们的程序。
HID-BPF 提供以下几种附着类型：

1. 使用 `SEC("struct_ops/hid_device_event")` 在 libbpf 中进行事件处理/过滤
2. 使用 `SEC("syscall")` 在 libbpf 中处理来自用户空间的操作
3. 使用 `SEC("struct_ops/hid_rdesc_fixup")` 或 `SEC("struct_ops.s/hid_rdesc_fixup")` 在 libbpf 中更改报告描述符

一个 `hid_device_event` 是在从设备接收到事件时调用 BPF 程序。因此我们处于中断上下文（IRQ 上下文），可以对数据进行操作或通知用户空间。
由于我们处于中断上下文，我们不能向设备发送数据。
一个 `syscall` 表示用户空间调用了 `BPF_PROG_RUN` 设施。
这次，我们可以执行HID-BPF允许的任何操作，并且可以与设备通信。
最后，“hid_rdesc_fixup”与其他操作不同，因为只能有一个这种类型的BPF程序。这个程序在驱动程序的“probe”阶段被调用，允许从BPF程序中修改报告描述符。一旦加载了“hid_rdesc_fixup”程序，除非插入该程序的程序通过固定程序并关闭所有指向它的文件描述符来允许我们覆盖它，否则无法覆盖它。
需要注意的是，“hid_rdesc_fixup”可以声明为可睡眠（SEC("struct_ops.s/hid_rdesc_fixup")）。

开发者API：
==========

可用于HID-BPF的“struct_ops”：
-------------------------------------

.. kernel-doc:: include/linux/hid_bpf.h
   :identifiers: hid_bpf_ops

程序中可用的用户API数据结构：
-----------------------------------------------

.. kernel-doc:: include/linux/hid_bpf.h
   :identifiers: hid_bpf_ctx

所有HID-BPF struct_ops程序中可用的API：
----------------------------------------------

.. kernel-doc:: drivers/hid/bpf/hid_bpf_dispatch.c
   :identifiers: hid_bpf_get_data

可在syscall HID-BPF程序或可睡眠HID-BPF struct_ops程序中使用的API：
-------------------------------------------------------------------------------------------------------

.. kernel-doc:: drivers/hid/bpf/hid_bpf_dispatch.c
   :identifiers: hid_bpf_hw_request hid_bpf_hw_output_report hid_bpf_input_report hid_bpf_try_input_report hid_bpf_allocate_context hid_bpf_release_context

HID-BPF程序的一般概述：
======================

访问附加到上下文的数据：
-------------------------------

“struct hid_bpf_ctx”不直接导出“data”字段，要访问它，BPF程序需要首先调用:c:func:`hid_bpf_get_data`。“offset”可以是任何整数，但“size”需要是编译时已知的常量。
这允许以下操作：

1. 对于给定的设备，如果我们知道报告长度将始终为某个特定值，我们可以请求“data”指针指向整个报告长度。内核会确保我们使用正确的大小和偏移量，eBPF会确保代码不会尝试读取或写入边界之外的内容：
   
       __u8 *data = hid_bpf_get_data(ctx, 0 /* offset */, 256 /* size */);

       if (!data)
           return 0; /* 确保data正确，现在验证器知道我们有256字节可用 */

       bpf_printk("hello world: %02x %02x %02x", data[0], data[128], data[255]);

2. 如果报告长度是可变的，但我们知道“X”的值始终是一个16位整数，那么我们可以仅有一个指向该值的指针：
   
       __u16 *x = hid_bpf_get_data(ctx, offset, sizeof(*x));

       if (!x)
           return 0; /* 出现问题 */

       *x += 1; /* 将X递增1 */

HID-BPF程序的效果：
---------------------------

除了:c:func:`hid_rdesc_fixup`之外的所有HID-BPF附着类型，可以将多个eBPF程序附着到同一设备。如果一个HID-BPF struct_ops具有一个“hid_rdesc_fixup”，而另一个已经附着到设备上，则内核将在附着struct_ops时返回`-EINVAL`。
除非在附着程序时添加了`BPF_F_BEFORE`标志，否则新程序将附加到列表的末尾。
`BPF_F_BEFORE`会将新程序插入到列表的开头，这对于追踪很有用，因为我们需要获取未经处理的设备事件。
需要注意的是，如果有多个程序使用`BPF_F_BEFORE`标志，则只有最近加载的那个实际上位于列表的首位。
```SEC("struct_ops/hid_device_event")```
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

每当匹配到一个事件时，eBPF 程序会依次被调用，并且它们会在同一个数据缓冲区上工作。
如果一个程序修改了与上下文关联的数据，下一个程序将看到修改后的数据，但它完全不知道原始数据是什么。
当所有程序运行完毕并返回 `0` 或者一个正数时，HID 栈的其余部分将处理这个修改后的数据，其中最后一个 `hid_bpf_ctx` 的 `size` 字段表示新的输入数据流大小。
如果一个 BPF 程序返回负数错误，则该事件会被丢弃，即此事件不会被 HID 栈处理。客户端（hidraw、input、LEDs）将 **不会** 看到这个事件。

```SEC("syscall")```
~~~~~~~~~~~~~~~~~~

`syscall` 不会绑定到特定设备。为了确定我们正在处理哪个设备，用户空间需要通过其唯一的系统 ID 来引用设备（在 sysfs 路径中的最后四个数字：`/sys/bus/hid/devices/xxxx:yyyy:zzzz:0000`）。
为了获取与设备关联的上下文，程序必须调用 `hid_bpf_allocate_context()` 并在返回前使用 `hid_bpf_release_context()` 释放它。
一旦获取到上下文，还可以通过 `hid_bpf_get_data()` 请求内核内存的指针。这块内存足够大，可以支持给定设备的所有输入/输出/特性报告。

```SEC("struct_ops/hid_rdesc_fixup")```
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`hid_rdesc_fixup` 程序的工作方式类似于 `struct hid_driver` 中的 `.report_fixup`。
当设备被探测时，内核会将上下文的数据缓冲区设置为报告描述符的内容。与此缓冲区关联的内存大小为 `HID_MAX_DESCRIPTOR_SIZE`（目前为 4 kB）。
eBPF 程序可以随意修改数据缓冲区，内核会使用修改后的内容和大小作为报告描述符。
每当包含有 `SEC("struct_ops/hid_rdesc_fixup")` 程序的 `struct_ops` 被附加（如果之前没有附加过程序），内核会立即断开 HID 设备并重新探测。

同样地，当这个 `struct_ops` 被解除时，内核会对设备发出断开命令。

HID-BPF 中没有专门的“解除”机制。程序解除发生在所有指向 HID-BPF `struct_ops` 链接的用户空间文件描述符被关闭的时候。

因此，如果我们需要替换一个报告描述符的修复程序，则需要原始报告描述符修复程序的所有者的配合。

原始所有者可能会在 bpffs 中固定 `struct_ops` 链接，然后我们可以通过正常的 BPF 操作来替换它。

将 BPF 程序附加到设备
=======================

我们现在使用标准的 `struct_ops` 附加机制通过 `bpf_map__attach_struct_ops()` 进行操作。
但由于我们需要将 `struct_ops` 附加到专用的 HID 设备上，调用者必须在加载内核中的程序之前设置 `struct_ops` 地图中的 `hid_id`。
`hid_id` 是 HID 设备的唯一系统 ID（即 sysfs 路径中最后四个数字：`/sys/bus/hid/devices/xxxx:yyyy:zzzz:0000`）。

也可以设置 `flags`，其类型为 `enum hid_bpf_attach_flags`。

我们不能依赖 hidraw 来绑定 BPF 程序到 HID 设备。hidraw 是 HID 设备处理过程中的产物，并且不稳定。有些驱动甚至禁用了它，这样就失去了在这些设备上的追踪能力（在那里获取非 hidraw 的跟踪信息是很有趣的）。

另一方面，`hid_id` 在整个 HID 设备生命周期中是稳定的，即使我们更改了它的报告描述符。
鉴于设备断开/重新连接时 `hidraw` 不稳定，我们建议通过 sysfs 访问设备的当前报告描述符。
这可以通过路径 `/sys/bus/hid/devices/BUS:VID:PID.000N/report_descriptor` 获取到，作为一个二进制流。
解析报告描述符是 BPF 程序员或加载 eBPF 程序的用户空间组件的责任。

一个（几乎）完整的增强型 HID 设备 BPF 示例
============================================

*前言：在大多数情况下，这可以实现为内核驱动程序*

假设我们有一个具有触觉功能的新平板设备，可以模拟用户在其上刮擦的表面。该设备还有一个特定的三位置开关，用于在“铅笔在纸上”、“蜡笔在墙上”和“画笔在画布上”之间切换。为了使事情更好，我们可以通过特征报告控制开关的物理位置。
当然，这个开关依赖于某些用户空间组件来控制设备本身的触觉特性。
过滤事件
---------

第一步是过滤来自设备的事件。由于开关位置实际上包含在笔事件流中，使用 `hidraw` 实现这种过滤意味着每次事件发生都会唤醒用户空间。
这对 libinput 来说是可以接受的，但对于仅对报告中的一个字节感兴趣的外部库来说则不太理想。
为此，我们可以为我们的 BPF 程序创建一个基本框架：

```c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

/* HID 程序需要遵循 GPL 许可 */
char _license[] SEC("license") = "GPL";

/* HID-BPF kfunc API 定义 */
extern __u8 *hid_bpf_get_data(struct hid_bpf_ctx *ctx,
			      unsigned int offset,
			      const size_t __sz) __ksym;

struct {
	__uint(type, BPF_MAP_TYPE_RINGBUF);
	__uint(max_entries, 4096 * 64);
} ringbuf SEC(".maps");

__u8 current_value = 0;

SEC("struct_ops/hid_device_event")
int BPF_PROG(filter_switch, struct hid_bpf_ctx *hid_ctx)
{
	__u8 *data = hid_bpf_get_data(hid_ctx, 0 /* offset */, 192 /* size */);
	__u8 *buf;

	if (!data)
		return 0; /* EPERM 检查 */

	if (current_value != data[152]) {
		buf = bpf_ringbuf_reserve(&ringbuf, 1, 0);
		if (!buf)
			return 0;

		*buf = data[152];

		bpf_ringbuf_commit(buf, 0);

		current_value = data[152];
	}

	return 0;
}

SEC(".struct_ops.link")
struct hid_bpf_ops haptic_tablet = {
	.hid_device_event = (void *)filter_switch,
};
```

要附加 `haptic_tablet`，用户空间需要先设置 `hid_id`：

```c
static int attach_filter(struct hid *hid_skel, int hid_id)
{
	int err, link_fd;

	hid_skel->struct_ops.haptic_tablet->hid_id = hid_id;
	err = hid__load(skel);
	if (err)
		return err;

	link_fd = bpf_map__attach_struct_ops(hid_skel->maps.haptic_tablet);
	if (!link_fd) {
		fprintf(stderr, "无法附加 HID-BPF 程序: %m\n");
		return -1;
	}

	return link_fd; /* 创建的 bpf_link 的文件描述符 */
}
```

现在，我们的用户空间程序可以监听环形缓冲区上的通知，并且仅在值发生变化时被唤醒。
当用户空间程序不再需要监听事件时，可以关闭从 `attach_filter` 返回的 bpf 链接文件描述符，这将告诉内核从 HID 设备上卸载程序。
当然，在其他用例中，用户空间程序也可以通过调用 `bpf_obj_pin` 将文件描述符固定到 BPF 文件系统，就像任何 bpf_link 一样。
控制设备
----------------------

为了能够改变平板设备的触觉反馈，用户空间程序需要向设备本身发送一个特征报告。
我们不必使用`hidraw`来实现这一点，而是可以创建一个`SEC("syscall")`程序与设备通信：

```c
/* 一些HID-BPF kfunc API定义 */
extern struct hid_bpf_ctx *hid_bpf_allocate_context(unsigned int hid_id) __ksym;
extern void hid_bpf_release_context(struct hid_bpf_ctx *ctx) __ksym;
extern int hid_bpf_hw_request(struct hid_bpf_ctx *ctx,
			      __u8* data,
			      size_t len,
			      enum hid_report_type type,
			      enum hid_class_request reqtype) __ksym;

struct hid_send_haptics_args {
	/* 数据必须从偏移量0开始，以便我们可以将其memcpy进去 */
	__u8 data[10];
	unsigned int hid;
};

SEC("syscall")
int send_haptic(struct hid_send_haptics_args *args)
{
	struct hid_bpf_ctx *ctx;
	int ret = 0;

	ctx = hid_bpf_allocate_context(args->hid);
	if (!ctx)
		return 0; /* EPERM检查 */

	ret = hid_bpf_hw_request(ctx,
				 args->data,
				 10,
				 HID_FEATURE_REPORT,
				 HID_REQ_SET_REPORT);

	hid_bpf_release_context(ctx);

	return ret;
}
```

然后用户空间需要直接调用该程序：

```c
static int set_haptic(struct hid *hid_skel, int hid_id, __u8 haptic_value)
{
	int err, prog_fd;
	int ret = -1;
	struct hid_send_haptics_args args = {
		.hid = hid_id,
	};
	DECLARE_LIBBPF_OPTS(bpf_test_run_opts, tattrs,
		.ctx_in = &args,
		.ctx_size_in = sizeof(args),
	);

	args.data[0] = 0x02; /* 设备上特征报告的ID */
	args.data[1] = haptic_value;

	prog_fd = bpf_program__fd(hid_skel->progs.set_haptic);

	err = bpf_prog_test_run_opts(prog_fd, &tattrs);
	return err;
}
```

现在我们的用户空间程序了解了触觉状态并可以控制它。该程序还可以将此状态进一步提供给其他用户空间程序（例如通过DBus API）。
这里有趣的一点是我们没有为此创建新的内核API。这意味着如果我们实现中存在漏洞，我们可以随意更改与内核的接口，因为用户空间应用程序对其自身使用负责。
