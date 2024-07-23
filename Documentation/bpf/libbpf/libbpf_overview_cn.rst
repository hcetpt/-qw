SPDX 许可证标识符：GPL-2.0

=================
libbpf 概览
=================

libbpf 是一个基于 C 语言的库，包含一个 BPF 加载器，能够加载编译后的 BPF 目标文件，并准备和将其加载到 Linux 内核中。libbpf 承担了加载、验证和将 BPF 程序连接到各种内核钩子的繁重工作，使 BPF 应用开发者可以专注于 BPF 程序的正确性和性能。
以下是 libbpf 支持的高级功能：

* 提供用户空间程序与 BPF 程序交互的高级和低级 API。低级 API 包括所有 bpf 系统调用功能的封装，当用户需要更精细控制用户空间与 BPF 程序之间的交互时，这非常有用。
* 全面支持由 bpftool 生成的 BPF 对象骨架。骨架文件简化了用户空间程序访问全局变量和与 BPF 程序协同工作的过程。
* 提供 BPF 侧 API，包括 BPF 辅助定义、BPF 映射支持和跟踪辅助，使开发者能够简化 BPF 代码编写。
* 支持 BPF CO-RE 机制，使 BPF 开发者能够编写可移植的 BPF 程序，这些程序可以在不同内核版本上一次编译，到处运行。

本文档将深入探讨上述概念，提供对 libbpf 能力和优势的深入了解，以及它如何帮助你高效地开发 BPF 应用程序。

BPF 应用生命周期与 libbpf API
==================================

BPF 应用程序由一个或多个 BPF 程序（无论是协作还是完全独立的）、BPF 映射和全局变量组成。全局变量在所有 BPF 程序之间共享，使它们能够在一组共同数据上协同工作。libbpf 提供了用户空间程序可以使用的 API 来操纵 BPF 程序，触发 BPF 应用程序生命周期的不同阶段。

以下是对 BPF 生命周期每个阶段的简要概述：

* **打开阶段**：在此阶段，libbpf 解析 BPF 目标文件并发现 BPF 映射、BPF 程序和全局变量。在 BPF 应用被打开后，用户空间应用可以在所有实体创建和加载之前进行额外调整（如必要时设置 BPF 程序类型；预设全局变量的初始值等）。
* **加载阶段**：在加载阶段，libbpf 创建 BPF 映射，解析各种重定位，并验证和将 BPF 程序加载到内核中。此时，libbpf 验证 BPF 应用的所有部分并将 BPF 程序加载到内核中，但尚未执行任何 BPF 程序。在加载阶段之后，可以设置初始 BPF 映射状态，而不会与 BPF 程序代码执行产生竞争。
* **绑定阶段**：在此阶段，libbpf将BPF程序绑定到各种BPF挂钩点（例如，跟踪点、kprobes、cgroup挂钩、网络数据包处理管道等）。在这个阶段，BPF程序执行有用的工作，如处理数据包，或更新可以从用户空间读取的BPF映射和全局变量。
* **拆解阶段**：在拆解阶段，libbpf卸载并从内核中解除BPF程序。BPF映射被销毁，BPF应用程序使用的所有资源都被释放。

BPF对象骨架文件
=================

BPF骨架是与BPF对象一起工作的libbpf API的替代接口。骨架代码抽象化了通用的libbpf API，极大地简化了从用户空间操纵BPF程序的代码。骨架代码包括BPF目标文件的字节码表示，简化了分发你的BPF代码的过程。有了嵌入式BPF字节码，就无需额外部署任何文件与你的应用程序二进制文件一同。

你可以通过将BPF对象传递给bpftool来为特定的目标文件生成骨架头文件（.skel.h）。生成的BPF骨架提供了以下对应于BPF生命周期的自定义函数，每个函数都以前缀具体的对象名称：

* `<name>__open()` – 创建并打开BPF应用（`<name>`代表具体bpf对象名称）
* `<name>__load()` – 实例化、加载和验证BPF应用的部分
* `<name>__attach()` – 绑定所有可自动绑定的BPF程序（这是可选的，你可以直接使用libbpf API获得更多的控制）
* `<name>__destroy()` – 解除所有BPF程序，并释放所有使用的资源

使用骨架代码是处理BPF程序的推荐方式。请记住，BPF骨架提供了对底层BPF对象的访问，因此无论使用通用libbpf API可以做什么，在使用BPF骨架时仍然可以做。这是一个附加的便利特性，没有系统调用，也没有繁琐的代码。

使用骨架文件的其他优势
-----------------------------

* BPF骨架为用户空间程序提供了一个与BPF全局变量交互的接口。骨架代码将全局变量作为结构体映射到用户空间。该结构体接口允许用户空间程序在BPF加载阶段前初始化BPF程序，并在之后从用户空间获取和更新数据。
* `skel.h`文件通过列出可用的映射、程序等反映了目标文件的结构。BPF骨架提供了对所有BPF映射和BPF程序的直接访问，作为结构体字段。这消除了使用`bpf_object_find_map_by_name()`和`bpf_object_find_program_by_name()`API进行基于字符串查找的需要，减少了由于BPF源代码和用户空间代码不同步导致的错误。
* 目标文件的嵌入式字节码表示确保骨架和BPF目标文件始终保持同步。

BPF辅助函数
============

libbpf提供了BPF端的API，BPF程序可以使用这些API与系统交互。BPF辅助函数的定义允许开发人员像使用普通的C函数一样在BPF代码中使用它们。例如，有用于打印调试信息、获取系统启动以来的时间、与BPF映射交互、操作网络数据包等的辅助函数。

对于辅助函数的作用、它们接受的参数以及返回值的完整描述，请参阅`bpf-helpers <https://man7.org/linux/man-pages/man7/bpf-helpers.7.html>`_手册页。

BPF CO-RE（编译一次 - 随处运行）
==================================

BPF程序在内核空间工作，具有访问内核内存和数据结构的能力。BPF应用程序面临的一个限制是跨不同内核版本和配置的可移植性缺乏。`BCC <https://github.com/iovisor/bcc/>`_是BPF可移植性的一种解决方案。然而，它带来了运行时开销和由于与应用程序捆绑编译器而产生的较大二进制文件大小。
libbpf通过支持BPF CO-RE概念提高了BPF程序的可移植性。BPF CO-RE将BTF类型信息、libbpf库和编译器结合在一起，生成一个可以在多个内核版本和配置上运行的单一可执行二进制文件。

为了使BPF程序具有可移植性，libbpf依赖于运行时内核的BTF类型信息。内核也通过`sysfs`在`/sys/kernel/btf/vmlinux`中暴露这种自描述的权威BTF信息。
你可以使用以下命令为当前运行的内核生成BTF信息：

```bash
$ bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
```

该命令会生成一个包含所有内核类型（参见[BTF类型](../btf)文档）的`vmlinux.h`头文件，这些类型是当前运行内核所使用的。在你的BPF程序中包含`vmlinux.h`可以消除对系统范围内的内核头文件的依赖。

libbpf通过查看BPF程序记录的BTF类型和重定位信息，并将其与运行时内核提供的BTF信息（vmlinux）匹配来实现BPF程序的可移植性。libbpf解析并匹配所有的类型和字段，并更新必要的偏移量和其他可重定位数据，以确保BPF程序的逻辑在特定主机内核上正确运行。因此，BPF CO-RE概念消除了与BPF开发相关的开销，允许开发者编写无需修改和目标机器上的运行时源代码编译的可移植BPF应用程序。

下面的代码片段展示了如何使用BPF CO-RE和libbpf读取内核`task_struct`中的`parent`字段。基本的辅助函数`bpf_core_read(dst, sz, src)`用于以CO-RE可重定位的方式读取字段，它会从`src`引用的字段中读取`sz`字节到由`dst`指向的内存中。

```c
//...
struct task_struct *task = (void *)bpf_get_current_task();
struct task_struct *parent_task;
int err;

err = bpf_core_read(&parent_task, sizeof(void *), &task->parent);
if (err) {
  /* 处理错误 */
}

/* parent_task 包含 task->parent 指针的值 */
```

在代码片段中，我们首先使用`bpf_get_current_task()`获取当前`task_struct`的指针。然后使用`bpf_core_read()`读取`task`结构体中的`parent`字段到`parent_task`变量中。`bpf_core_read()`与`bpf_probe_read_kernel()` BPF辅助函数类似，不同之处在于它记录了应在目标内核上重定位的字段的信息。例如，如果由于在`struct task_struct`前面添加了新字段导致`parent`字段的偏移量发生了变化，libbpf会自动调整实际偏移量到正确的值。

### 开始使用libbpf

可以查看[libbpf-bootstrap](https://github.com/libbpf/libbpf-bootstrap)仓库，其中包含使用libbpf构建各种BPF应用的简单示例。

还可以参考[libbpf API文档](https://libbpf.readthedocs.io/en/latest/api.html)。
libbpf与Rust
===============

如果你正在使用Rust构建BPF应用程序，建议你使用`Libbpf-rs <https://github.com/libbpf/libbpf-rs>`_库，而不是直接使用bindgen绑定到libbpf。Libbpf-rs将libbpf功能封装在Rust风格的接口中，并提供了libbpf-cargo插件来处理BPF代码的编译和骨架生成。使用Libbpf-rs将使构建BPF应用的用户空间部分更加容易。请注意，BPF程序本身仍然必须用纯C编写。

libbpf日志记录
==============

默认情况下，libbpf将信息性和警告性消息记录到stderr。这些消息的详细程度可以通过设置环境变量LIBBPF_LOG_LEVEL为warn、info或debug来控制。可以使用``libbpf_set_print()``设置自定义的日志回调函数。

额外文档
========================

* `程序类型与ELF段 <https://libbpf.readthedocs.io/en/latest/program_types.html>`_
* `API命名规范 <https://libbpf.readthedocs.io/en/latest/libbpf_naming_convention.html>`_
* `构建libbpf <https://libbpf.readthedocs.io/en/latest/libbpf_build.html>`_
* `API文档规范 <https://libbpf.readthedocs.io/en/latest/libbpf_naming_convention.html#api-documentation-convention>`_
