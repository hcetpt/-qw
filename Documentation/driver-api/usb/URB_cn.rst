USB 请求块 (URB)
~~~~~~~~~~~~~~~~~~~~~~~

:修订日期: 2000年12月5日
:再次修订: 2002年7月6日
:再次修订: 2005年9月19日
:再次修订: 2017年3月29日

.. note::

    USB 子系统现在有一个相当大的部分位于 :ref:`usb-hostside-api` 部分，
    这部分内容是从当前源代码生成的。
    本特定文档文件并不完整，可能没有更新到最新版本；除非快速概览外，
    不应依赖它。

基本概念或“什么是URB？”
==================================

新驱动程序的基本思想是消息传递，该消息本身被称为 USB 请求块 (URB)。

- URB 包含执行任何 USB 交易所需的所有相关信息，并将数据和状态返回。
- 执行一个 URB 本质上是一个异步操作，即 :c:func:`usb_submit_urb` 调用在成功排队所请求的操作后立即返回。
- 可以通过 :c:func:`usb_unlink_urb` 在任何时候取消单个URB的数据传输。
- 每个URB都有一个完成处理器，在操作成功完成或被取消后被调用。URB还包含一个上下文指针，用于向完成处理器传递信息。
- 设备的每个端点逻辑上支持一个请求队列。
  您可以填充该队列，以便 USB 硬件仍然可以向端点传输数据，而您的驱动程序处理另一个完成。
  这最大限度地利用了 USB 带宽，并且在使用周期性传输模式时支持数据无缝流式传输到（或从）设备。
### URB 结构

`struct urb` 中的一些字段如下：

```c
struct urb
{
  // (IN) device 和 pipe 指定端点队列
  struct usb_device *dev;         // 指向关联的 USB 设备
  unsigned int pipe;              // 端点信息

  unsigned int transfer_flags;    // URB_ISO_ASAP, URB_SHORT_NOT_OK 等
  // (IN) 所有 URB 都需要完成例程
  void *context;                  // 完成例程的上下文
  usb_complete_t complete;        // 指向完成例程的指针

  // (OUT) 每次完成后的状态
  int status;                     // 返回的状态

  // (IN) 用于数据传输的缓冲区
  void *transfer_buffer;          // 关联的数据缓冲区
  u32 transfer_buffer_length;     // 数据缓冲区长度
  int number_of_packets;          // iso_frame_desc 的大小

  // (OUT) 有时仅使用了 CTRL/BULK/INTR 转移缓冲区的一部分
  u32 actual_length;              // 实际数据缓冲区长度

  // (IN) 设置 CTRL 的设置阶段（传递一个 struct usb_ctrlrequest）
  unsigned char *setup_packet;    // 设置包（仅控制）

  // 仅适用于周期性传输（ISO，中断）
    // (IN/OUT) 如果未设置 URB_ISO_ASAP，则设置 start_frame
  int start_frame;                // 开始帧
  int interval;                   // 检测间隔

    // ISO 专用：数据包仅为“尽力而为”；每个数据包都可能出现错误
  int error_count;                // 错误数量
  struct usb_iso_packet_descriptor iso_frame_desc[0];
};
```

您的驱动程序必须根据其声明的接口中的适当端点描述符创建 “pipe” 值。

### 如何获取一个 URB？

通过调用 `usb_alloc_urb` 来分配 URB：

```c
struct urb *usb_alloc_urb(int isoframes, int mem_flags)
```

返回值是指向已分配 URB 的指针，如果分配失败则返回 0。参数 `isoframes` 指定了您要调度的等时传输帧的数量。对于 CTRL/BULK/INT，使用 0。参数 `mem_flags` 包含标准内存分配标志，允许您控制（包括但不限于）底层代码是否可以阻塞。

要释放 URB，请使用 `usb_free_urb`：

```c
void usb_free_urb(struct urb *urb)
```

您可以释放已经提交但尚未在完成回调中返回给您的 URB。当它不再被使用时，它将自动被取消分配。

### 必须填写哪些内容？

根据交易类型的不同，在 `linux/usb.h` 中定义了一些内联函数来简化初始化过程，例如 `usb_fill_control_urb`、`usb_fill_bulk_urb` 和 `usb_fill_int_urb`。通常情况下，它们需要 USB 设备指针、管道（来自 usb.h 的常用格式）、转移缓冲区、期望的转移长度、完成处理程序及其上下文。查看现有的一些驱动程序以了解它们是如何使用的。

#### 标志：

- 对于 ISO，有两种启动行为：指定开始帧或尽快（ASAP）。
- 对于 ASAP，在 `transfer_flags` 中设置 `URB_ISO_ASAP`。
- 如果不能容忍短数据包，则在 `transfer_flags` 中设置 `URB_SHORT_NOT_OK`。

### 如何提交一个 URB？

只需调用 `usb_submit_urb`：

```c
int usb_submit_urb(struct urb *urb, int mem_flags)
```

参数 `mem_flags`（如 `GFP_ATOMIC`）控制内存分配，例如当内存紧张时，较低层是否可以阻塞。
这段文档主要描述了USB请求块对象（URB）的提交、取消及完成处理程序的相关细节。下面是翻译后的中文内容：

---

URB 在提交后会立即返回，返回的状态码为0（请求已排队）或者某些错误码，这些错误码通常由以下情况引起：

- 内存不足（`-ENOMEM`）
- 设备未连接（`-ENODEV`）
- 端点停滞（`-EPIPE`）
- 排队的等时传输过多（`-EAGAIN`）
- 请求的等时帧数过多（`-EFBIG`）
- 无效的中断间隔（`-EINVAL`）
- 对于中断传输，一个包以上（`-EINVAL`）

提交后，`urb->status` 将变为 `-EINPROGRESS`；然而，除了在你的完成回调函数中，你不应该查看这个值。

对于等时端点，你的完成处理器应当（重新）提交URB到同一个端点，并使用 `URB_ISO_ASAP` 标志和多缓冲机制，以实现无缝的等时流传输。

如何取消已经运行中的URB？
==============================

有两种方式可以取消你已经提交但尚未返回到驱动程序的URB。对于异步取消，调用 `usb_unlink_urb` 函数：

```c
int usb_unlink_urb(struct urb *urb)
```

它将URB从内部列表中移除并释放所有分配的硬件描述符。状态将被改变以反映取消链接操作。请注意，当 `usb_unlink_urb` 返回时，URB通常还没有完成；你仍需等待完成处理器被调用。

为了同步地取消URB，调用 `usb_kill_urb` 函数：

```c
void usb_kill_urb(struct urb *urb)
```

它执行 `usb_unlink_urb` 的所有操作，并且等待直到URB被返回且完成处理器完成执行。此外，它还会标记URB暂时不可用，因此如果完成处理器或其他任何尝试重新提交URB的代码将收到 `-EPERM` 错误。因此你可以确信当 `usb_kill_urb` 返回时，URB完全处于空闲状态。

需要考虑URB的生命周期问题。URB可能随时完成，完成处理器可能会释放URB。如果这发生在 `usb_unlink_urb` 或 `usb_kill_urb` 运行期间，将会导致内存访问违规。驱动程序负责避免这种情况发生，这通常意味着需要某种锁来防止URB在仍在使用时被释放。

另一方面，由于 `usb_unlink_urb` 可能最终调用完成处理器，因此该处理器不能获取在调用 `usb_unlink_urb` 时持有的任何锁。解决这个问题的一般方法是，在持有锁的情况下增加URB的引用计数，然后释放锁并调用 `usb_unlink_urb` 或 `usb_kill_urb`，最后减少URB的引用计数。你可以通过调用 `usb_get_urb` 来增加引用计数：

```c
struct urb *usb_get_urb(struct urb *urb)
```

（忽略返回值；它与参数相同），并通过调用 `usb_free_urb` 减少引用计数。当然，如果没有URB被完成处理器释放的风险，则无需执行上述步骤。

关于完成处理器？
==================

完成处理器的类型如下：

```c
typedef void (*usb_complete_t)(struct urb *);
```

即，它接收触发完成调用的URB。在完成处理器中，你应该检查 `urb->status` 以检测任何USB错误。

由于URB上下文参数包含在URB中，你可以向完成处理器传递信息。

请注意，即使报告了错误（或取消链接），也可能已经发生了数据传输。这是因为USB传输是以包为单位进行的；传输你的1KB缓存可能需要16个包，而其中10个包可能已经在完成调用之前成功传输。

**警告：**

**绝不要在完成处理器中睡眠。**
---
这些通常被称为在原子上下文中被调用。
在当前的内核中，完成处理程序是在禁用了本地中断的情况下运行的，
但将来这种情况会改变，因此不要假设在完成处理程序内部本地IRQ总是被禁用。
如何进行等时（ISO）传输？
======================================

除了批量传输中存在的字段外，对于ISO传输，您还需要设置 `urb->interval` 来说明传输的频率；这通常是每帧一次（对于高速设备来说是每个微帧一次）。
实际使用的间隔将是不大于您指定值的2的幂。您可以使用 `usb_fill_int_urb` 宏来填充大多数ISO传输字段。
对于ISO传输，您还需要为要调度的每个数据包填充一个 `usb_iso_packet_descriptor` 结构体，该结构体由 `usb_alloc_urb` 在URB的末尾分配。
`usb_submit_urb` 调用会修改 `urb->interval` 为实现的间隔值，该值小于或等于请求的间隔值。如果使用了 `URB_ISO_ASAP` 调度，则还会更新 `urb->start_frame`。
对于每一项，您需要指定该帧的数据偏移量（基点是transfer_buffer），以及您希望写入/预期读取的长度。
完成之后，actual_length 包含实际传输的长度，status 包含了该帧ISO传输的结果状态。
允许从帧到帧指定不同的长度（例如，为了音频同步/自适应传输速率）。您也可以使用长度0来跳过一个或多个帧（分段）。
对于调度，您可以选择自己的起始帧或使用 `URB_ISO_ASAP`。如前所述，如果您始终保持至少一个URB排队，并且您的完成处理程序持续（重新）提交后续的URB，那么您将获得平滑的ISO流传输（如果USB带宽利用率允许的话）。
如果你指定了自己的起始帧，请确保它比当前帧提前几帧。如果你正在将 ISO 数据与其它事件流同步，你可能需要这种模型。
如何开始中断（INT）传输？
=============================

中断传输，就像等时传输一样，是周期性的，并且以2的幂（1、2、4 等单位）为间隔发生。对于全速和低速设备，单位是帧；而对于高速设备，则是微帧。
你可以使用 `usb_fill_int_urb` 函数来填充 INT 传输字段。
`usb_submit_urb` 调用会修改 `urb->interval` 为实现的间隔值，该值小于或等于请求的间隔值。
在 Linux 2.6 中，与早期版本不同的是，当中断 URB 完成时并不会自动重启。它们会在完成处理程序被调用时结束，就像其他 URB 一样。如果你想让一个中断 URB 重启，你的完成处理程序必须重新提交它。
