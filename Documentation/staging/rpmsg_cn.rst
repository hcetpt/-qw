远程处理器消息传递 (rpmsg) 框架
============================================

.. note::

  本文档描述了 rpmsg 总线及其驱动程序的编写方法。
  要了解如何为新平台添加 rpmsg 支持，请参阅 `remoteproc.txt`（同样位于 `Documentation/` 目录下）。

介绍
============

现代 SoC 通常在非对称多处理 (AMP) 配置中使用异构远程处理器设备，这些设备可能运行不同的操作系统实例，无论是 Linux 还是其他实时操作系统。
例如，OMAP4 包含两个 Cortex-A9 核心、两个 Cortex-M3 核心和一个 C64x+ DSP。
通常情况下，双 Cortex-A9 在 SMP 配置中运行 Linux，而其他三个核心（两个 M3 核心和一个 DSP）各自运行自己的实时操作系统 (RTOS) 实例。
通常，AMP 配置下的远程处理器使用专用的 DSP 编解码器和多媒体硬件加速器，因此常用于卸载主应用处理器上的 CPU 密集型多媒体任务。
这些远程处理器也可以用来控制延迟敏感的传感器、驱动随机硬件模块，或者在主 CPU 空闲时执行后台任务。
这些远程处理器的用户可以是用户空间应用程序（例如，与远程 OMX 组件通信的多媒体框架）或内核驱动程序（控制只有远程处理器才能访问的硬件，代表远程处理器预留内核控制资源等）。
rpmsg 是一种基于 virtio 的消息总线，允许内核驱动程序与系统中的远程处理器进行通信。反过来，驱动程序可以提供适当的用户空间接口（如果需要的话）。
当编写暴露 rpmsg 通信到用户空间的驱动程序时，请注意远程处理器可能直接访问系统的物理内存和其他敏感硬件资源（例如，在 OMAP4 上，远程核心和硬件加速器可能直接访问物理内存、GPIO 银行、DMA 控制器、I2C 总线、GPTimer、邮箱设备、硬件自旋锁等）。此外，这些远程处理器可能运行实时操作系统，其中每个任务都可以访问整个内存/设备。为了最小化恶意（或有缺陷的）用户空间代码利用远程漏洞并接管系统的风险，通常希望限制用户空间只能在特定的 rpmsg 通道（见下面定义）上发送消息，并尽可能减少其对消息内容的控制。
每个 RPMsg 设备都是一个与远程处理器通信的通道（因此 RPMsg 设备被称为通道）。这些通道通过一个文本名称来标识，并且具有一个本地（"源"）RPMsg 地址和一个远程（"目标"）RPMsg 地址。

当一个驱动程序开始监听一个通道时，其接收回调会绑定到一个唯一的 RPMsg 本地地址（一个 32 位整数）。这样，当接收到的消息到达时，RPMsg 核心根据其目标地址将消息分发给相应的驱动程序（这是通过调用驱动程序的接收处理函数并传递接收到的消息的有效载荷来完成的）。

用户 API
========

::

  int rpmsg_send(struct rpmsg_endpoint *ept, void *data, int len);

从给定的端点向远程处理器发送一条消息。
调用者应指定端点、要发送的数据及其长度（以字节为单位）。该消息将在指定端点的通道上发送，即其源地址和目标地址字段将分别设置为端点的源地址和其父通道的目标地址。
如果没有可用的发送缓冲区，该函数将阻塞直到有缓冲区可用（即直到远程处理器消耗一个发送缓冲区并将它放回 virtio 的已使用描述符环），或者超时时间为 15 秒。如果发生后者，则返回 -ERESTARTSYS。
该函数目前只能在进程上下文中调用。
成功时返回 0，失败时返回适当的错误值。

::

  int rpmsg_sendto(struct rpmsg_endpoint *ept, void *data, int len, u32 dst);

从给定的端点向远程处理器发送一条消息，目标地址由调用者提供。
调用者应指定端点、要发送的数据、其长度（以字节为单位）以及显式的目标地址。
然后，该消息将使用端点的源地址和用户提供的目标地址发送到该端点所属通道的远程处理器（因此通道的目标地址将被忽略）。
```c
int rpmsg_send_offchannel(struct rpmsg_endpoint *ept, u32 src, u32 dst,
						  void *data, int len);
```

使用用户提供的源地址和目标地址，将消息发送到远程处理器。

调用者应指定端点、要发送的数据及其长度（以字节为单位），以及明确的源地址和目标地址。消息将被发送到该端点所属通道的远程处理器，但忽略端点的源地址和通道的目标地址（而是使用用户提供的地址）。

如果没有可用的TX缓冲区，函数将阻塞直到有一个TX缓冲区变得可用（即直到远程处理器消耗一个TX缓冲区并将其放回到virtio的已使用描述符环中），或者15秒超时时间到期。如果发生后者，则返回-ERESTARTSYS。

此函数目前只能从进程上下文调用。成功时返回0，失败时返回适当的错误值。

```c
int rpmsg_trysend(struct rpmsg_endpoint *ept, void *data, int len);
```

从给定的端点将消息发送到远程处理器。

如果没有可用的TX缓冲区，函数将阻塞直到有一个TX缓冲区变得可用（即直到远程处理器消耗一个TX缓冲区并将其放回到virtio的已使用描述符环中），或者15秒超时时间到期。如果发生后者，则返回-ERESTARTSYS。

此函数目前只能从进程上下文调用。成功时返回0，失败时返回适当的错误值。
调用者应指定端点、要发送的数据及其长度（以字节为单位）。消息将通过指定端点的通道发送，即其源地址和目标地址字段将分别设置为端点的源地址和其父通道的目标地址。

如果没有可用的发送缓冲区，该函数会立即返回-ENOMEM，而不是等待缓冲区变为可用。

该函数目前只能在进程上下文中调用。成功时返回0，失败时返回适当的错误值。

```
int rpmsg_trysendto(struct rpmsg_endpoint *ept, void *data, int len, u32 dst)
```

从给定的端点向远程处理器发送消息，目的地地址由用户提供。

用户应指定通道、要发送的数据及其长度（以字节为单位），以及一个明确的目标地址。然后，消息将使用通道的源地址和用户提供的目标地址发送到属于该通道的远程处理器（因此通道的目标地址将被忽略）。

如果没有可用的发送缓冲区，该函数会立即返回-ENOMEM，而不是等待缓冲区变为可用。

该函数目前只能在进程上下文中调用。成功时返回0，失败时返回适当的错误值。
```c
// 尝试通过非默认信道发送消息到远程处理器
int rpmsg_trysend_offchannel(struct rpmsg_endpoint *ept, u32 src, u32 dst,
                             void *data, int len);

// 使用用户提供的源地址和目标地址向远程处理器发送消息。
// 用户应指定信道、要发送的数据及其长度（以字节为单位），以及明确的源地址和目标地址。
// 消息将被发送到该信道所属的远程处理器，但会忽略信道的源地址和目标地址（而使用用户提供的地址）。
// 如果没有可用的发送缓冲区，此函数将立即返回-ENOMEM，而不是等待缓冲区可用。
// 此函数目前只能在进程上下文中调用。
// 成功时返回0，失败时返回适当的错误值。

// 创建一个rpmsg端点
struct rpmsg_endpoint *rpmsg_create_ept(struct rpmsg_device *rpdev,
                                        rpmsg_rx_cb_t cb, void *priv,
                                        struct rpmsg_channel_info chinfo);

// 系统中的每个rpmsg地址都绑定到了一个接收回调函数（因此当接收到消息时，它们将由rpmsg总线使用相应的回调处理器进行分发）。
// 这个函数允许驱动程序创建这样的端点，并由此绑定一个回调函数及可能的一些私有数据到一个rpmsg地址（这个地址可以是预先已知的，也可以是动态分配的）。
// 对于简单的rpmsg驱动程序来说，无需调用rpmsg_create_ept，因为当它们被rpmsg总线探测时已经为它们创建了端点（使用它们注册到rpmsg总线时提供的接收回调）。
// 因此对于简单驱动程序来说，一切都应该正常工作：它们已经有了一个端点，其接收回调已经绑定到它们的rpmsg地址，当相关消息到达（即目标地址等于它们rpmsg信道的源地址）时，驱动程序的处理程序会被调用来处理这些消息。
```
话虽如此，更复杂的驱动程序可能确实需要分配额外的rpmsg地址，并将它们绑定到不同的接收回调函数。为了实现这一点，这些驱动程序需要调用此函数。驱动程序应提供其信道（以便新端点可以绑定到与其信道所属的远程处理器相同的处理器），一个接收回调函数，一个可选的私有数据（当接收回调被调用时会返回该数据），以及一个想要与回调绑定的地址。如果addr设置为RPMSG_ADDR_ANY，则rpmsg_create_ept将动态分配一个可用的rpmsg地址（驱动程序应该有一个非常好的理由来说明为什么不总是使用RPMSG_ADDR_ANY）。
成功时返回指向端点的指针，失败时返回NULL。

```
void rpmsg_destroy_ept(struct rpmsg_endpoint *ept);
```

销毁一个现有的rpmsg端点。用户应提供一个之前通过rpmsg_create_ept()创建的rpmsg端点的指针。

```
int register_rpmsg_driver(struct rpmsg_driver *rpdrv);
```

将一个rpmsg驱动程序注册到rpmsg总线上。用户应提供一个指向rpmsg_driver结构体的指针，其中包含驱动程序的->probe()和->remove()函数、一个接收回调函数以及一个指定此驱动程序感兴趣的信道名称的id_table。

```
void unregister_rpmsg_driver(struct rpmsg_driver *rpdrv);
```

从rpmsg总线中注销一个rpmsg驱动程序。用户应提供一个先前已注册的rpmsg_driver结构体的指针。成功时返回0，在失败时返回适当的错误值。

典型用法
==========

以下是一个简单的rpmsg驱动程序示例，它在probe()时发送一个“hello!”消息，并且每当接收到传入的消息时，将其内容转储到控制台。

```c
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/rpmsg.h>

static void rpmsg_sample_cb(struct rpmsg_channel *rpdev, void *data, int len, void *priv, u32 src)
{
    print_hex_dump(KERN_INFO, "incoming message:", DUMP_PREFIX_NONE, 16, 1, data, len, true);
}

static int rpmsg_sample_probe(struct rpmsg_channel *rpdev)
{
    int err;

    dev_info(&rpdev->dev, "chnl: 0x%x -> 0x%x\n", rpdev->src, rpdev->dst);

    /* 在我们的信道上发送一条消息 */
    err = rpmsg_send(rpdev->ept, "hello!", 6);
    if (err) {
        pr_err("rpmsg_send failed: %d\n", err);
        return err;
    }

    return 0;
}

static void rpmsg_sample_remove(struct rpmsg_channel *rpdev)
{
    dev_info(&rpdev->dev, "rpmsg sample client driver is removed\n");
}

static struct rpmsg_device_id rpmsg_driver_sample_id_table[] = {
    { .name = "rpmsg-client-sample" },
    { },
};
MODULE_DEVICE_TABLE(rpmsg, rpmsg_driver_sample_id_table);

static struct rpmsg_driver rpmsg_sample_client = {
    .drv.name = KBUILD_MODNAME,
    .id_table = rpmsg_driver_sample_id_table,
    .probe = rpmsg_sample_probe,
    .callback = rpmsg_sample_cb,
    .remove = rpmsg_sample_remove,
};
module_rpmsg_driver(rpmsg_sample_client);

.. note::
   一个类似的示例可以在samples/rpmsg/目录下找到。
```
RPMsg 信道分配
=============================

目前我们只支持动态分配 RPMsg 信道。
这只有在远程处理器具有 VIRTIO_RPMSG_F_NS 这一 virtio 设备特性集时才可能。这一特性位意味着远程处理器支持动态名称服务通告消息。
当此特性被启用时，RPMsg 设备（即信道）的创建是完全动态的：远程处理器通过发送一个名称服务消息来宣告远程 RPMsg 服务的存在（该消息包含远程服务的名字和 RPMsg 地址，详见结构体 rpmsg_ns_msg）。
这个消息随后由 RPMsg 总线处理，并动态创建和注册一个 RPMsg 信道（代表远程服务）。
如果/当相关的 RPMsg 驱动被注册后，它将立即被总线探测，并可以开始向远程服务发送消息。
计划还通过 virtio 配置空间来添加静态创建 RPMsg 信道的功能，但这尚未实现。
