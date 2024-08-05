== 相干加速器接口（CXL） ==

简介
====

    相干加速器接口旨在允许加速器（如FPGA和其他设备）与POWER系统进行相干连接。这些设备需要遵循相干加速器接口架构（CAIA）。
    IBM将其称为相干加速器处理器接口或CAPI。在内核中，为了避免与ISDN CAPI子系统的混淆，它被称为CXL。
    在此上下文中，“相干”意味着加速器和CPU都可以直接访问系统内存，并且具有相同的有效地址。

硬件概述
========

    ::

         POWER8/9             FPGA
       +----------+        +---------+
       |          |        |         |
       |   CPU    |        |   AFU   |
       |          |        |         |
       |          |        |         |
       |          |        |         |
       +----------+        +---------+
       |   PHB    |        |         |
       |   +------+        |   PSL   |
       |   | CAPP |<------>|         |
       +---+------+  PCIE  +---------+

    POWER8/9芯片包含一个相干连接处理器代理（CAPP）单元，它是PCIe主机桥接器（PHB）的一部分。这个单元由Linux通过调用OPAL进行管理。Linux并不直接编程CAPP。
    FPGA（或相干连接的设备）由两部分组成：
    POWER服务层（PSL）和加速功能单元（AFU）。AFU用于在PSL背后实现特定的功能。PSL提供了包括内存地址转换在内的服务，以使每个AFU可以直接访问用户空间的内存。
    AFU是加速器的核心部分（例如压缩、加密等功能）。内核对AFU的功能一无所知。只有用户空间会直接与AFU交互。
    PSL提供了AFU所需的地址转换和中断服务。这是内核与其交互的部分。例如，如果AFU需要读取某个有效地址的数据，它会将该地址发送给PSL，PSL然后进行地址转换，从内存中获取数据并返回给AFU。如果PSL遇到地址转换失败的情况，它会向内核发出中断，内核处理此故障。故障处理的上下文基于拥有该加速功能的所有者。
- POWER8及其PSL版本8符合CAIA版本1.0标准。
- POWER9及其PSL版本9符合CAIA版本2.0标准。
此PSL版本9提供了新功能，例如：

    * 与P9芯片上的nest MMU进行交互
* 原生DMA支持
* 支持发送ASB_Notify消息以唤醒主机线程
* 支持原子操作
* 等等
带有PSL9的卡无法在POWER8系统上工作，而带有PSL8的卡则无法在POWER9系统上工作。
AFU模式
=======

    AFU支持两种编程模式：专用模式和AFU定向模式。AFU可能支持这两种模式中的一种或两种。
使用专用模式时，仅支持一个MMU上下文。在这种模式下，一次只有一个用户空间进程可以使用加速器。
使用AFU定向模式时，最多可支持16K个同时的上下文。这意味着最多有16K个同时的用户空间应用程序可以使用加速器（尽管特定的AFU可能支持较少）。在这种模式下，AFU会在其每个请求中发送一个16位的上下文ID。这告诉PSL哪个上下文与每个操作相关联。如果PSL无法转换某个操作，该ID也可以被内核访问，以便确定与操作相关的用户空间上下文。
MMIO空间
========

    加速器的一部分MMIO空间可以直接从AFU映射到用户空间。可以映射整个空间，也可以只映射每个上下文的部分空间。硬件具有自描述特性，因此内核可以确定每个上下文部分的偏移量和大小。
中断
==========

AFU 可能会生成原本发往用户空间的中断。这些中断由内核作为硬件中断接收，并通过下面将要介绍的读取系统调用传递给用户空间。
数据存储故障和错误中断由内核驱动程序处理。
工作元素描述符 (WED)
=============================

启动上下文时，向 AFU 传递一个 64 位参数 WED。其格式取决于 AFU，因此内核并不知道它代表什么内容。通常，这将是工作队列或状态块的有效地址，AFU 和用户空间可以通过它们共享控制和状态信息。
用户 API
========

1. AFU 字符设备
^^^^^^^^^^^^^^^^^^^^^^^^

对于以 AFU 指导模式运行的 AFU，将创建两个字符设备文件。/dev/cxl/afu0.0m 对应于主上下文，而 /dev/cxl/afu0.0s 对应于从上下文。主上下文可以访问 AFU 提供的完整 MMIO 空间。从上下文只能访问 AFU 为每个进程提供的 MMIO 空间。
对于以专用进程模式运行的 AFU，驱动程序将为每个 AFU 创建一个名为 /dev/cxl/afu0.0d 的单一字符设备。这将具有访问 AFU 提供的整个 MMIO 空间的能力（类似于 AFU 指导模式下的主上下文）。
下面描述的类型定义在 include/uapi/misc/cxl.h 中。

以下文件操作均支持在从设备和主设备上使用：
用户空间库 libcxl 可在此处获取：

   https://github.com/ibm-capi/libcxl

该库提供了对这个内核 API 的 C 语言接口。
open
----

打开设备并分配一个文件描述符，用于后续 API 调用。
专用模式下的 AFU 只有一个上下文，并且只允许打开一次设备。
AFU 指导模式下的 AFU 可以有多个上下文，设备可以为每个可用的上下文打开一次。
当所有可用的上下文都被分配后，打开调用将失败并返回 -ENOSPC。
注意：
    每个上下文都需要分配IRQ，这可能会限制可以创建的上下文数量，因此也限制了设备可以被打开的次数。POWER8 CAPP支持2040个IRQ，其中3个由内核使用，因此剩下2037个。如果每个上下文需要1个IRQ，则只能分配2037个上下文。如果每个上下文需要4个IRQ，则只能分配2037/4=509个上下文。

ioctl
-----

    CXL_IOCTL_START_WORK:
        启动AFU上下文，并将其与当前进程关联起来。一旦此ioctl成功执行，映射到此进程的所有内存都可以通过相同的有效地址被这个AFU上下文访问。不需要额外的调用来映射或取消映射内存。随着用户空间分配和释放内存，AFU内存上下文将会更新。此ioctl在AFU上下文启动完成后返回。
接受指向struct cxl_ioctl_start_work结构体指针

            ::

                struct cxl_ioctl_start_work {
                        __u64 flags;
                        __u64 work_element_descriptor;
                        __u64 amr;
                        __s16 num_interrupts;
                        __s16 reserved1;
                        __s32 reserved2;
                        __u64 reserved3;
                        __u64 reserved4;
                        __u64 reserved5;
                        __u64 reserved6;
                };

            flags:
                指示结构体中哪些可选字段是有效的
work_element_descriptor:
                工作元素描述符（WED）是一个64位参数，由AFU定义。通常这是指向一个AFU特定结构的有效地址，该结构描述要执行的工作内容
amr:
                权限掩码寄存器（AMR），与powerpc中的AMR相同。当flags中指定相应的CXL_START_WORK_AMR值时，此字段才由内核使用。如果没有指定，内核将使用默认值0
num_interrupts:
                需要请求的用户空间中断的数量。当flags中指定相应的CXL_START_WORK_NUM_IRQS值时，此字段才由内核使用。如果没有指定，将分配AFU所需的最小数量。最小和最大数量可以从sysfs获取
保留字段：
                用于ABI填充及未来的扩展

    CXL_IOCTL_GET_PROCESS_ELEMENT:
        获取当前上下文ID，也称为进程元素。该值作为__u32类型从内核返回。
### mmap
一个AFU可能有一个MMIO空间，用于方便与AFU的通信。如果存在这样的空间，可以通过mmap访问MMIO空间。这个区域的大小和内容取决于特定的AFU。该大小可以通过sysfs发现。
在AFU定向模式下，主上下文被允许映射所有的MMIO空间，而从属上下文仅被允许映射与该上下文相关联的进程MMIO空间。在专用进程模式下，整个MMIO空间始终可以被映射。
此mmap调用必须在START_WORK ioctl之后进行。
访问MMIO空间时应谨慎行事。POWER8仅支持32位和64位访问。此外，AFU将采用特定的字节序设计，因此所有MMIO访问都应该考虑字节序（推荐使用endian(3)变体如：le64toh(), be64toh()等）。这些字节序问题同样适用于WED可能描述的共享内存队列。

### 读取
从AFU读取事件。如果没有待处理的事件则阻塞（除非提供O_NONBLOCK）。在发生不可恢复错误或卡被移除的情况下返回-EIO。
read()总是返回事件的整数倍。
传递给read()的缓冲区至少需要4K字节。
读取的结果是一个包含一个或多个事件的缓冲区，每个事件都是类型为struct cxl_event的不同大小：

        struct cxl_event {
                struct cxl_event_header header;
                union {
                        struct cxl_event_afu_interrupt irq;
                        struct cxl_event_data_storage fault;
                        struct cxl_event_afu_error afu_error;
                };
        };

`struct cxl_event_header`定义为

    struct cxl_event_header {
            __u16 type;
            __u16 size;
            __u16 process_element;
            __u16 reserved1;
    };

- `type`: 定义了事件的类型。类型决定了事件其余部分的结构。这些类型如下所述，并由枚举cxl_event_type定义。
- `size`: 这是事件的大小（以字节为单位），包括struct cxl_event_header。下一个事件的起始位置可以从当前事件的起始位置加上这个偏移量找到。
- `process_element`: 事件的上下文ID。
### 保留字段：
#### 用于未来的扩展和填充
如果事件类型是 `CXL_EVENT_AFU_INTERRUPT`，则事件结构定义为：

```c
struct cxl_event_afu_interrupt {
    __u16 flags;       // 标志
    __u16 irq;         // 被触发的AFU中断编号
    __u32 reserved1;   // 保留字段：用于未来的扩展和填充
};

- **flags**: 这些标志指示此结构中哪些可选字段存在。目前所有字段都是强制性的。
- **irq**: 由AFU发送的IRQ编号。
- **保留字段**: 用于未来的扩展和填充。

如果事件类型是 `CXL_EVENT_DATA_STORAGE`，则事件结构定义为：

```c
struct cxl_event_data_storage {
    __u16 flags;       // 标志
    __u16 reserved1;   // 保留字段
    __u32 reserved2;   // 保留字段
    __u64 addr;        // 地址
    __u64 dsisr;       // 故障类型信息
    __u64 reserved3;   // 保留字段
};

- **flags**: 这些标志指示此结构中哪些可选字段存在。目前所有字段都是强制性的。
- **地址**: AFU尝试访问但未成功访问的地址。有效的访问将由内核透明处理，而无效的访问将生成此事件。
- **dsisr**: 此字段提供故障类型的详细信息。它是地址故障发生时PSL硬件中的DSISR的副本。DSISR的形式如CAIA中所定义。
- **保留字段**: 用于未来的扩展。

如果事件类型是 `CXL_EVENT_AFU_ERROR`，则事件结构定义为：

```c
struct cxl_event_afu_error {
    __u16 flags;       // 标志
    __u16 reserved1;   // 保留字段
    __u32 reserved2;   // 保留字段
    __u64 error;       // 错误状态
};

- **flags**: 这些标志指示此结构中哪些可选字段存在。目前所有字段都是强制性的。
- **error**: 来自AFU的错误状态。由AFU定义。
- **保留字段**: 用于未来的扩展和填充。

### 2. 卡字符设备（仅适用于powerVM客户机）
在powerVM客户机中，为卡创建一个额外的字符设备。该设备仅用于向FPGA加速器写入（刷新）新图像。一旦图像被写入并验证后，设备树会被更新，并且卡将被重置以重新加载更新后的图像。
### 打开 (Open)

打开设备并分配一个文件描述符以供后续的API使用。设备只能打开一次。

### ioctl

CXL_IOCTL_DOWNLOAD_IMAGE / CXL_IOCTL_VALIDATE_IMAGE：
启动并控制新FPGA图像的烧录过程。目前不支持部分重构，因此图像必须包含PSL和AFU(s)的副本。由于图像可能非常大，调用者可能需要将其拆分为较小的部分进行迭代处理。
接收指向`struct cxl_adapter_image`结构体的指针：

```c
struct cxl_adapter_image {
    __u64 flags;
    __u64 data;
    __u64 len_data;
    __u64 len_image;
    __u64 reserved1;
    __u64 reserved2;
    __u64 reserved3;
    __u64 reserved4;
};
```

- `flags`：这些标志表示该结构体中存在哪些可选字段。当前所有字段都是必需的。
- `data`：指向包含要写入卡中的图像部分的缓冲区的指针。
- `len_data`：由`data`指向的缓冲区的大小。
- `len_image`：图像的完整大小。

### Sysfs 类

在`/sys/class/cxl`下添加了一个cxl sysfs类，以方便加速器的枚举和调整。其布局在Documentation/ABI/testing/sysfs-class-cxl中有描述。

### Udev 规则

可以使用以下udev规则来创建一个符号链接，指向任何编程模式下最合适的字符设备（对于专用模式使用afuX.Yd，对于AFU定向模式使用afuX.Ys），因为API对于每个设备几乎相同：

```sh
SUBSYSTEM=="cxl", ATTRS{mode}=="dedicated_process", SYMLINK="cxl/%b"
SUBSYSTEM=="cxl", ATTRS{mode}=="afu_directed", \
                      KERNEL=="afu[0-9]*.[0-9]*s", SYMLINK="cxl/%b"
```
