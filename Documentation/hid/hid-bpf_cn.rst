### SPDX 许可证标识符: GPL-2.0

#### 
HID-BPF
#### 

HID（Human Interface Device，人机接口设备）是一种用于输入设备的标准协议，但某些设备可能需要定制化的调整，传统上是通过内核驱动程序修复来实现的。而使用eBPF的能力可以加速开发，并为现有的HID接口增加新的功能。

### 目录
- [本地]
- [深度: 2]


### 何时以及为何使用HID-BPF
在以下情况下，使用HID-BPF比传统的内核驱动程序修复更优：

#### 摇杆的死区
- 假设你有一个使用了一段时间的摇杆，它可能会在其中立点附近晃动。这通常会在应用层面通过为特定轴添加“死区”来过滤。
- 使用HID-BPF，我们可以在内核中直接应用这种过滤，这样当输入控制器上没有其他活动时，用户空间就不会被唤醒。
- 当然，由于这个死区是针对特定设备的，我们无法为所有相同类型的摇杆创建一个通用的修复方案。为这种需求添加一个自定义的内核API（例如，通过添加一个sysfs条目）并不能保证这个新API会被广泛采用和维护。
- HID-BPF允许用户空间程序加载其自身，确保只有在有用户的情况下才会加载自定义API。

#### 报告描述符的简单修正
- 在HID树中，一半的驱动程序只对报告描述符中的一个键或一个字节进行修正。这些修正都需要内核补丁以及随后的版本合并，这对用户来说是一个漫长且痛苦的过程。
- 我们可以通过提供eBPF程序来减轻这种负担。一旦这样的程序被用户验证后，我们可以将源代码嵌入到内核树中，并直接加载eBPF程序，而不是为此加载一个特定的内核模块。

#### 添加需要新内核API的新功能
- 例如，Universal Stylus Interface (USI) 笔就需要一个新的内核API，因为它们引入了当前HID和输入堆栈不支持的新通信通道。
- 而不是使用hidraw或者创建新的sysfs条目或ioctl命令，我们可以依赖eBPF让内核API由消费者控制，同时避免每次事件发生时唤醒用户空间所导致的性能影响。

**注：**eBPF程序的分发及其在内核中的集成目前尚未完全实现。
将一个设备转换为其他东西并从用户空间进行控制
-------------------------------------------------

内核对于HID项到evdev位的映射相对静态。
它无法决定动态地将某个给定设备转变成其他东西，因为它缺乏必要的上下文信息，并且任何此类转换都无法被用户空间撤销（甚至发现）。
然而，对于某些设备而言，这种静态定义设备的方式几乎毫无用处。例如，Microsoft Surface Dial是一个带有触觉反馈的按钮，在当前环境下几乎无法有效使用。
通过eBPF，用户空间可以将该设备转换为鼠标，并将旋转事件转换为滚轮事件。此外，用户空间程序可以根据上下文设置或取消触觉反馈。例如，如果屏幕上有菜单可见，我们可能需要每15度有一个触觉点击。但在网页滚动时，当设备以最高分辨率发出事件时，用户体验会更好。

防火墙
------

如果我们想要阻止其他用户访问设备的某个特定功能呢？（想象一下可能存在故障的固件更新入口点）

通过eBPF，我们可以拦截发送给设备的所有HID命令，并选择是否验证它们。
这也允许在用户空间和内核/BPF程序之间同步状态，因为我们能够拦截所有传入的命令。

跟踪
------

最后一个用途是跟踪事件以及利用BPF进行汇总和分析所能做的所有有趣的事情。
目前，跟踪依赖于hidraw。除了几个问题外，这种方式工作得很好：

1. 如果驱动程序没有导出hidraw节点，我们就无法进行跟踪（在这方面，eBPF将是“全能模式”，因此可能会引起一些关注）
2. hidraw无法捕捉其他进程对设备的请求，这意味着我们需要在内核中添加打印语句来理解发生了什么情况。

HID-BPF的高级视图
==================

HID-BPF背后的主要思想是在字节数组级别工作。
因此，HID报告及其描述符的所有解析必须在加载eBPF程序的用户空间组件中实现。
例如，在上述的死亡区域摇杆中，需要知道数据流中的哪些字段应被设置为`0`，这需要用户空间来计算。
由此得出的一个推论是，HID-BPF并不了解内核中存在的其他子系统。*你不能直接通过eBPF从输入API发出输入事件*。
当一个BPF程序需要发出输入事件时，它需要与HID协议进行通信，并依赖HID内核处理将HID数据转换为输入事件。

### 内置树中的HID-BPF程序和`udev-hid-bpf`

官方设备修复程序作为源代码随内核一起发布，位于`drivers/hid/bpf/progs`目录下。这样可以在`tools/testing/selftests/hid`中为它们添加自检测试。
然而，这些对象文件的编译并不包含在常规的内核编译过程中，因为它们需要外部工具来加载。目前这个工具是`udev-hid-bpf <https://libevdev.pages.freedesktop.org/udev-hid-bpf/index.html>`_。
为了方便起见，该外部仓库在其自己的`src/bpf/stable`目录中复制了来自`drivers/hid/bpf/progs`的文件。这样可以使发行版无需拉取整个内核源码树即可分发和打包这些HID-BPF修复。`udev-hid-bpf`还具有根据用户运行的内核版本处理多个对象文件的能力。

### 可用的程序类型

HID-BPF是在BPF基础上构建的，这意味着我们使用bpf struct_ops方法来声明我们的程序。
HID-BPF具有以下可用的附加类型：

1. 通过`SEC("struct_ops/hid_device_event")`在libbpf中进行事件处理/过滤
2. 来自用户空间的动作通过`SEC("syscall")`在libbpf中
3. 通过`SEC("struct_ops/hid_rdesc_fixup")`或`SEC("struct_ops.s/hid_rdesc_fixup")`在libbpf中更改报告描述符

一个`hid_device_event`会在接收到设备事件时调用BPF程序。因此我们处于中断上下文中，可以对数据采取行动或通知用户空间。
并且由于我们处于中断上下文中，我们不能向设备发送信息。
一个`syscall`意味着用户空间调用了`BPF_PROG_RUN`系统调用设施。
这次，我们可以执行HID-BPF允许的任何操作，并且与设备进行通信也是被允许的。
最后，“hid_rdesc_fixup”与其他操作不同之处在于，只能存在一个这种类型的BPF程序。这个函数在驱动程序的“probe”阶段被调用，并允许从BPF程序中更改报告描述符。一旦加载了一个“hid_rdesc_fixup”程序，除非插入该程序的程序通过将其固定并关闭指向它的所有文件描述符来允许我们覆盖它，否则不能进行覆盖。
值得注意的是，“hid_rdesc_fixup”可以声明为可睡眠（`SEC("struct_ops.s/hid_rdesc_fixup")`）。

### 开发者API：

#### 可用的HID-BPF `struct_ops`：
```
.. kernel-doc:: include/linux/hid_bpf.h
   :identifiers: hid_bpf_ops
```

#### 程序中可用的用户API数据结构：
```
.. kernel-doc:: include/linux/hid_bpf.h
   :identifiers: hid_bpf_ctx
```

#### 所有HID-BPF `struct_ops`程序中可用的API：
```
.. kernel-doc:: drivers/hid/bpf/hid_bpf_dispatch.c
   :identifiers: hid_bpf_get_data
```

#### 在系统调用HID-BPF程序或可睡眠HID-BPF `struct_ops`程序中可用的API：
```
.. kernel-doc:: drivers/hid/bpf/hid_bpf_dispatch.c
   :identifiers: hid_bpf_hw_request hid_bpf_hw_output_report hid_bpf_input_report hid_bpf_try_input_report hid_bpf_allocate_context hid_bpf_release_context
```

### HID-BPF程序的一般概述

#### 访问附加到上下文的数据

`struct hid_bpf_ctx`没有直接导出`data`字段，要访问这些数据，BPF程序首先需要调用`hid_bpf_get_data`函数。
`offset`可以是任意整数，但`size`需要是编译时已知的常量。
这使得以下操作成为可能：

1. 对于给定的设备，如果我们知道报告长度将始终为某个特定值，我们可以请求`data`指针指向整个报告长度。
内核会确保我们使用了正确的大小和偏移量，而eBPF则会确保代码不会尝试读取或写入边界之外的内容：
```
__u8 *data = hid_bpf_get_data(ctx, 0 /* offset */, 256 /* size */);

if (!data)
    return 0; /* 确保data正确，现在验证器知道我们有256字节可用 */

bpf_printk("hello world: %02x %02x %02x", data[0], data[128], data[255]);
```

2. 如果报告长度是可变的，但是我们知道`X`始终是一个16位整数，那么我们可以只获取指向该值的指针：
```
__u16 *x = hid_bpf_get_data(ctx, offset, sizeof(*x));

if (!x)
    return 0; /* 出现问题 */

*x += 1; /* 将X递增1 */
```

#### HID-BPF程序的影响

对于除了`hid_rdesc_fixup`以外的所有HID-BPF附加类型，可以有多个eBPF程序附加到同一设备上。如果一个HID-BPF `struct_ops`具有`hid_rdesc_fixup`，而另一个已经附加到了设备上，内核在附加`struct_ops`时将返回`-EINVAL`。
除非在附加程序时添加了`BPF_F_BEFORE`标志，否则新程序将被添加到列表的末尾。
`BPF_F_BEFORE`将在列表的开头插入新的程序，这对于追踪很有用，例如我们需要从设备获取未处理的事件。
需要注意的是，如果有多个程序使用`BPF_F_BEFORE`标志，则列表中的第一个实际上是最近加载的那个。
```SEC("struct_ops/hid_device_event")```
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

每当触发匹配的事件时，eBPF 程序会依次被调用，并且它们都在同一个数据缓冲区上工作。
如果一个程序改变了与上下文相关联的数据，下一个程序将会看到修改后的数据，但是它将**完全不知道**原始数据是什么。
一旦所有程序运行完毕并返回`0`或正数值，HID堆栈的其余部分将会基于修改后的数据进行处理，其中最后一个`hid_bpf_ctx`中的`size`字段表示新的数据输入流大小。
如果BPF程序返回负错误值，则该事件会被丢弃，即此事件将不会被HID堆栈处理。客户端（如hidraw、input和LEDs）将**看不到**这个事件。

```SEC("syscall")```
~~~~~~~~~~~~~~~~~~

`syscall`并不绑定到特定设备。为了确定我们正在处理哪个设备，用户空间需要通过其唯一的系统ID来引用该设备（在sysfs路径中的最后4个数字：`/sys/bus/hid/devices/xxxx:yyyy:zzzz:0000`）。
为了获取与设备相关的上下文，程序必须调用`hid_bpf_allocate_context()`来分配上下文，并且必须在返回之前通过`hid_bpf_release_context()`释放它。
一旦获取了上下文，还可以通过`hid_bpf_get_data()`请求指向内核内存的指针。这块内存足够大以支持给定设备的所有输入/输出/特性报告。

```SEC("struct_ops/hid_rdesc_fixup")```
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`hid_rdesc_fixup`程序的工作方式类似于`struct hid_driver`中的`.report_fixup`。
当设备被探测时，内核会将上下文的数据缓冲区设置为报告描述符的内容。与该缓冲区关联的内存大小是`HID_MAX_DESCRIPTOR_SIZE`（目前为4kB）。
eBPF程序可以随意修改数据缓冲区，而内核会使用修改后的内容和大小作为报告描述符。
每当包含有 `SEC("struct_ops/hid_rdesc_fixup")` 程序的 `struct_ops` 被附加（如果之前没有程序被附加），内核会立即断开 HID 设备连接并重新探测。

同样地，当这个 `struct_ops` 被解除时，内核会对设备发出断开命令。

HID-BPF 中没有专门的“解除”机制。一个程序的解除发生在所有指向 HID-BPF `struct_ops` 链接的用户空间文件描述符关闭的时候。

因此，如果我们需要替换报告描述符修复程序，就需要原始报告描述符修复程序的所有者配合。
原始所有者可能会在 bpffs 中固定 `struct_ops` 链接，然后我们可以通过正常的 BPF 操作来替换它。

将 BPF 程序附加到设备
========================

我们现在使用标准的 `struct_ops` 附加方法通过 `bpf_map__attach_struct_ops()` 来实现。
但考虑到我们需要将 `struct_ops` 附加到特定的 HID 设备上，调用者必须在加载程序到内核前设置 `struct_ops` 地图中的 `hid_id`。

`hid_id` 是 HID 设备的唯一系统 ID（即 sysfs 路径中最后四个数字：`/sys/bus/hid/devices/xxxx:yyyy:zzzz:0000`）。

还可以设置 `flags`，其类型为 `enum hid_bpf_attach_flags`。

我们不能依赖 hidraw 将 BPF 程序绑定到 HID 设备。hidraw 是 HID 设备处理过程的一个产物，并不稳定。有些驱动甚至禁用了它，这就会使得在这些设备上（其中获得非 hidraw 的跟踪信息很有趣）失去追踪能力。
另一方面，`hid_id` 在整个 HID 设备生命周期内是稳定的，即使我们更改了它的报告描述符。
鉴于当设备断开/重新连接时hidraw不够稳定，我们建议通过sysfs访问设备的当前报告描述符。
这可以通过路径``/sys/bus/hid/devices/BUS:VID:PID.000N/report_descriptor``作为二进制流获取。
解析报告描述符是BPF程序员或加载eBPF程序的用户空间组件的责任。

一个（几乎）完整的增强型HID设备BPF示例
=========================================================

*前言：在大多数情况下，这可以实现为内核驱动*

设想我们有一个新的平板设备，具有模拟用户刮擦表面的触觉功能。该设备还具有一个特定的三位置开关来切换*铅笔在纸上*、*蜡笔在墙上*和*画笔在画布上*的状态。为了使功能更加完善，我们可以通过特征报告控制开关的物理位置。
当然，这个开关依赖于某个用户空间组件来控制设备本身的触觉特性。
过滤事件
----------------

第一步是过滤来自设备的事件。考虑到开关的位置实际上是在笔事件流中报告的，如果使用hidraw实现这种过滤，意味着我们将为每个事件唤醒用户空间。
这对于libinput来说是可以接受的，但对于仅对报告中的一个字节感兴趣的外部库来说就不那么理想了。
为此，我们可以为我们的BPF程序创建一个基本框架::

  #include "vmlinux.h"
  #include <bpf/bpf_helpers.h>
  #include <bpf/bpf_tracing.h>

  /* HID程序需要遵循GPL许可 */
  char _license[] SEC("license") = "GPL";

  /* HID-BPF kfunc API定义 */
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
		return 0; /* EPERM检查 */

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

为了附加`haptic_tablet`，用户空间需要先设置`hid_id`::

  static int attach_filter(struct hid *hid_skel, int hid_id)
  {
  	int err, link_fd;

  	hid_skel->struct_ops.haptic_tablet->hid_id = hid_id;
  	err = hid__load(skel);
  	if (err)
  		return err;

  	link_fd = bpf_map__attach_struct_ops(hid_skel->maps.haptic_tablet);
  	if (!link_fd) {
  		fprintf(stderr, "无法附加HID-BPF程序: %m\n");
  		return -1;
  	}

  	return link_fd; /* 创建的bpf_link的文件描述符 */
  }

现在，我们的用户空间程序可以监听环形缓冲区上的通知，并且只在值改变时被唤醒。
当用户空间程序不再需要监听事件时，只需关闭从函数`attach_filter`返回的bpf link，这将告诉内核从HID设备上卸载程序。
当然，在其他用例中，用户空间程序也可以通过调用函数`bpf_obj_pin`将文件描述符固定到BPF文件系统，就像处理任何bpf_link一样。
控制设备
----------------------

为了能够改变平板设备上的触觉反馈，用户空间程序需要向该设备本身发送一个特性报告(feature report)。
我们不必通过`hidraw`来实现这一点，而是可以创建一个`SEC("syscall")`程序直接与设备通信：

  /* 定义一些额外的HID-BPF kfunc API */
  extern struct hid_bpf_ctx *hid_bpf_allocate_context(unsigned int hid_id) __ksym;
  extern void hid_bpf_release_context(struct hid_bpf_ctx *ctx) __ksym;
  extern int hid_bpf_hw_request(struct hid_bpf_ctx *ctx,
			      __u8* data,
			      size_t len,
			      enum hid_report_type type,
			      enum hid_class_request reqtype) __ksym;

  struct hid_send_haptics_args {
	/* 数据必须从偏移量0开始，以便我们可以直接进行memcpy操作 */
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
		return 0; /* 进行EPERM检查 */

	ret = hid_bpf_hw_request(ctx,
				 args->data,
				 10,
				 HID_FEATURE_REPORT,
				 HID_REQ_SET_REPORT);

	hid_bpf_release_context(ctx);

	return ret;
  }

然后，用户空间需要直接调用这个程序：

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

	args.data[0] = 0x02; /* 设备上特性的报告ID */
	args.data[1] = haptic_value;

	prog_fd = bpf_program__fd(hid_skel->progs.set_haptic);

	err = bpf_prog_test_run_opts(prog_fd, &tattrs);
	return err;
  }

现在，我们的用户空间程序已经知道触觉状态并能对其进行控制。该程序还可以将此状态进一步提供给其他用户空间程序（例如，通过DBus API）。
这里的关键在于我们没有为此创建新的内核API。
这意味着如果我们实现中有bug，我们可以根据需要更改与内核的接口，因为用户空间应用程序负责其自身的使用方式。
