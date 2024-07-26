### libbpf 概览

libbpf是一个基于C语言的库，包含一个BPF加载器，该加载器可以接收编译后的BPF目标文件，并准备和将其加载到Linux内核中。libbpf承担了加载、验证以及将BPF程序附加到各种内核钩子上的繁重工作，从而使BPF应用程序开发者能够专注于BPF程序的正确性和性能。以下是libbpf支持的主要高级功能：

* 提供用于用户空间程序与BPF程序交互的高级和低级API。低级API封装了所有bpf系统调用的功能，这对于需要更精细控制用户空间与BPF程序之间交互的用户非常有用。
* 提供对bpftool生成的BPF对象骨架的整体支持。骨架文件简化了用户空间程序访问全局变量及处理BPF程序的过程。
* 提供BPF侧API，包括BPF辅助函数定义、BPF映射支持以及追踪辅助工具，使开发者能够简化BPF代码的编写。
* 支持BPF CO-RE机制，使BPF开发者能够编写可移植的BPF程序，这些程序可以在不同版本的内核上编译一次并运行。
本文档将深入探讨上述概念，提供对libbpf能力和优势的更深入了解，以及它如何帮助您高效地开发BPF应用程序。

### BPF应用程序生命周期与libbpf API

BPF应用程序由一个或多个BPF程序（可以是协同工作的也可以是完全独立的）、BPF映射以及全局变量组成。全局变量在所有BPF程序间共享，使得它们能够在共同的数据集上合作。libbpf提供了用户空间程序可以使用的API来操纵BPF程序，触发BPF应用程序生命周期的不同阶段。

下面简要概述BPF生命周期中的每个阶段：

* **打开阶段**：在这个阶段，libbpf解析BPF目标文件并发现BPF映射、BPF程序和全局变量。打开BPF应用后，用户空间的应用程序可以进行额外的调整（如必要时设置BPF程序类型；为全局变量预设初始值等），然后再创建和加载所有的实体。
* **加载阶段**：在加载阶段，libbpf创建BPF映射、解析各种重定位，并验证和将BPF程序加载到内核中。此时，libbpf会验证BPF应用程序的所有部分并将BPF程序加载到内核中，但尚未执行任何BPF程序。加载阶段之后，可以设置初始的BPF映射状态而不会与BPF程序代码执行产生竞争。
### *附件阶段*：在此阶段，libbpf将BPF程序附加到各种BPF挂钩点（例如，跟踪点、kprobes、cgroup挂钩、网络数据包处理管道等）。在此阶段，BPF程序执行有用的工作，如处理数据包或更新可以从用户空间读取的BPF映射和全局变量。

### *拆除阶段*：在拆除阶段，libbpf卸载并从内核中分离BPF程序。BPF映射被销毁，并且所有由BPF应用程序使用的资源都被释放。

#### BPF对象骨架文件

BPF骨架是与BPF对象一起工作的libbpf API的一个替代接口。骨架代码抽象化了通用的libbpf API，极大地简化了从用户空间操纵BPF程序的代码。骨架代码包括BPF对象文件的字节码表示，简化了分发您的BPF代码的过程。有了嵌入的BPF字节码，就不需要额外的文件与您的应用程序二进制文件一起部署。

您可以使用bpftool将特定的BPF对象传递给它来生成骨架头文件（`.skel.h`）。生成的BPF骨架提供了以下自定义函数，这些函数对应于BPF生命周期的不同阶段，每个函数都以前缀为特定对象名称：

- `<name>__open()` – 创建并打开BPF应用（`<name>`代表具体的BPF对象名称）
- `<name>__load()` – 实例化、加载并验证BPF应用的各个部分
- `<name>__attach()` – 附加所有自动可附加的BPF程序（这是可选的，您也可以直接使用libbpf API来获得更多的控制）
- `<name>__destroy()` – 分离所有BPF程序并释放所有已使用的资源

使用骨架代码是处理BPF程序推荐的方式。请注意，BPF骨架提供了对底层BPF对象的访问，因此无论使用通用的libbpf API能做什么，在使用BPF骨架时仍然可以做到。这是一个附加的便利特性，无需系统调用，也无需复杂的代码。

#### 使用骨架文件的其他优势

- BPF骨架提供了一个接口，使用户空间程序能够与BPF全局变量一起工作。骨架代码将全局变量作为结构体映射到用户空间。这种结构体接口允许用户空间程序在BPF加载阶段之前初始化BPF程序，并在之后从用户空间获取和更新数据。
- `skel.h` 文件通过列出可用的映射、程序等反映了对象文件的结构。BPF骨架直接提供了对所有BPF映射和BPF程序作为结构体字段的访问。这消除了使用基于字符串查找的 `bpf_object_find_map_by_name()` 和 `bpf_object_find_program_by_name()` API的需求，减少了由于BPF源代码和用户空间代码不同步而产生的错误。
- 嵌入的对象文件字节码表示确保骨架和BPF对象文件始终同步。

#### BPF辅助函数

libbpf提供了BPF侧的API，BPF程序可以使用这些API与系统进行交互。BPF辅助函数的定义允许开发人员像使用普通的C函数一样在BPF代码中使用它们。例如，有用于打印调试消息、获取系统启动以来的时间、与BPF映射交互、操作网络数据包等的辅助函数。

有关辅助函数的功能、它们接受的参数以及返回值的完整描述，请参阅 `bpf-helpers <https://man7.org/linux/man-pages/man7/bpf-helpers.7.html>`_ 手册页。

#### BPF CO-RE（一次编译 - 到处运行）

BPF程序在内核空间工作，可以访问内核内存和数据结构。BPF应用程序面临的一个限制是跨不同内核版本和配置的可移植性不足。`BCC <https://github.com/iovisor/bcc/>`_ 是解决BPF可移植性问题的一种方案。然而，它带来了运行时开销和因嵌入编译器而导致的应用程序二进制文件较大。
libbpf通过支持BPF CO-RE概念提高了BPF程序的可移植性。BPF CO-RE将BTF类型信息、libbpf库和编译器结合在一起，生成一个可以在多个内核版本和配置上运行的单一可执行二进制文件。

为了使BPF程序具有可移植性，libbpf依赖于正在运行的内核的BTF类型信息。内核也通过`sysfs`在`/sys/kernel/btf/vmlinux`暴露了这种自描述且权威的BTF信息。
你可以使用以下命令为当前内核生成BTF信息：

```bash
$ bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
```

该命令会生成一个包含所有内核类型（参见[BTF类型](../btf)文档）的`vmlinux.h`头文件，这些类型是当前内核所使用的。在你的BPF程序中包含`vmlinux.h`可以消除对系统范围内的内核头文件的依赖。

libbpf通过查看BPF程序记录的BTF类型和重定位信息，并将它们与由运行中的内核提供的BTF信息（vmlinux）进行匹配，从而实现了BPF程序的可移植性。libbpf解析并匹配所有的类型和字段，并更新必要的偏移量和其他可重定位的数据，以确保BPF程序对于主机上的特定内核能够正确地执行其逻辑功能。因此，BPF CO-RE概念消除了与BPF开发相关的开销，使得开发者能够在不修改代码或不在目标机器上进行运行时源代码编译的情况下编写可移植的BPF应用程序。

下面的代码片段展示了如何使用BPF CO-RE和libbpf读取内核`task_struct`中的`parent`字段。基本的帮助函数`bpf_core_read(dst, sz, src)`以一种可重定位的方式读取`src`指向的字段的`sz`字节到`dst`指向的内存中。
```c
//..
struct task_struct *task = (void *)bpf_get_current_task();
struct task_struct *parent_task;
int err;

err = bpf_core_read(&parent_task, sizeof(void *), &task->parent);
if (err) {
  /* 处理错误 */
}

/* parent_task 包含 task->parent 指针的值 */
```

在这个代码片段中，我们首先使用`bpf_get_current_task()`获取当前`task_struct`的指针。然后使用`bpf_core_read()`将`task`结构体中的`parent`字段读入`parent_task`变量。`bpf_core_read()`类似于`bpf_probe_read_kernel()` BPF帮助函数，不同之处在于它记录了关于需要在目标内核上进行重定位的字段的信息。也就是说，如果由于在`struct task_struct`前面添加了新字段导致`parent`字段的偏移量发生了变化，libbpf将会自动调整实际偏移量到正确的值。

### 开始使用libbpf

可以查看[libbpf-bootstrap](https://github.com/libbpf/libbpf-bootstrap)仓库，里面有一些简单的示例，演示如何使用libbpf构建各种BPF应用程序。

也可以参考[libbpf API文档](https://libbpf.readthedocs.io/en/latest/api.html)。
Libbpf与Rust
===============

如果你正在使用Rust构建BPF应用程序，建议使用`Libbpf-rs <https://github.com/libbpf/libbpf-rs>`_库而不是直接使用bindgen绑定到libbpf。Libbpf-rs用Rust风格的接口封装了libbpf的功能，并提供了libbpf-cargo插件来处理BPF代码的编译和骨架生成。使用Libbpf-rs可以让你更容易地构建BPF应用的用户空间部分。请注意，BPF程序本身仍然需要用纯C语言编写。

libbpf日志记录
==============

默认情况下，libbpf将信息性和警告性消息记录到stderr。这些消息的详细程度可以通过设置环境变量LIBBPF_LOG_LEVEL为warn、info或debug来控制。你可以使用`libbpf_set_print()`设置自定义的日志回调函数。

附加文档
========================

* [程序类型和ELF段](https://libbpf.readthedocs.io/en/latest/program_types.html)
* [API命名约定](https://libbpf.readthedocs.io/en/latest/libbpf_naming_convention.html)
* [构建libbpf](https://libbpf.readthedocs.io/en/latest/libbpf_build.html)
* [API文档约定](https://libbpf.readthedocs.io/en/latest/libbpf_naming_convention.html#api-documentation-convention)
