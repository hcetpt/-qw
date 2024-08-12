========================
NFC 核心的 HCI 后端
========================

- 作者：Eric Lapuyade，Samuel Ortiz
- 联系方式：eric.lapuyade@intel.com，samuel.ortiz@intel.com

概述
-------

HCI 层实现了大部分 ETSI TS 102 622 V10.2.0 规范。它使编写基于 HCI 的 NFC 驱动程序变得简单。HCI 层作为 NFC 核心后端运行，实现了一个抽象的 NFC 设备，并将 NFC 核心 API 转换为 HCI 命令和事件。

HCI
---

HCI 作为 NFC 设备注册到 NFC 核心中。来自用户空间的请求通过 netlink 套接字路由到 NFC 核心，然后再到 HCI。从这里开始，这些请求被转换为一系列发送到主机控制器（芯片）中的 HCI 层的 HCI 命令。命令可以同步执行（发送上下文阻塞等待响应）或异步执行（响应从 HCI 接收上下文返回）。
HCI 事件也可以从主机控制器接收。它们将被处理，并且需要时会将转换后的信息转发给 NFC 核心。有钩子可以让 HCI 驱动程序处理专有的事件或覆盖标准行为。
HCI 使用两个执行上下文：

- 一个用于执行命令：nfc_hci_msg_tx_work()。在任何时刻只能执行一个命令。
- 一个用于分发接收到的事件和命令：nfc_hci_msg_rx_work()。

HCI 会话初始化
--------------------------

会话初始化是 HCI 标准的一部分，不幸的是必须支持专有的门。这就是为什么驱动程序会传递一个必须包含在会话中的专有门列表。HCI 将确保当设置 hci 设备时所有这些门都有管道连接。
如果芯片支持预打开的门和伪静态管道，驱动程序可以将这些信息传递给 HCI 核心。

HCI 门和管道
-------------------

一个门定义了可以找到某项服务的“端口”。为了访问一项服务，必须创建一条通往该门的管道并打开它。在这个实现中，管道是完全隐藏的。公共 API 只知道门。
这与驱动程序需要向专有门发送命令而无需知道连接的管道是一致的。

驱动程序接口
----------------

一个驱动程序通常分为两部分编写：物理链路管理和 HCI 管理。这使得维护一个可以通过多种物理接口（如 i2c、spi 等）连接的芯片驱动程序更加容易。

HCI 管理
--------------

驱动程序通常会向 HCI 注册自己并提供以下入口点：

```c
  struct nfc_hci_ops {
	int (*open)(struct nfc_hci_dev *hdev); // 打开硬件
	void (*close)(struct nfc_hci_dev *hdev); // 关闭硬件
	int (*hci_ready) (struct nfc_hci_dev *hdev);
	int (*xmit) (struct nfc_hci_dev *hdev, struct sk_buff *skb);
	int (*start_poll) (struct nfc_hci_dev *hdev,
			   u32 im_protocols, u32 tm_protocols);
	int (*dep_link_up)(struct nfc_hci_dev *hdev, struct nfc_target *target,
			   u8 comm_mode, u8 *gb, size_t gb_len);
	int (*dep_link_down)(struct nfc_hci_dev *hdev);
	int (*target_from_gate) (struct nfc_hci_dev *hdev, u8 gate,
				 struct nfc_target *target);
	int (*complete_target_discovered) (struct nfc_hci_dev *hdev, u8 gate,
					   struct nfc_target *target);
	int (*im_transceive) (struct nfc_hci_dev *hdev,
			      struct nfc_target *target, struct sk_buff *skb,
			      data_exchange_cb_t cb, void *cb_context);
	int (*tm_send)(struct nfc_hci_dev *hdev, struct sk_buff *skb);
	int (*check_presence)(struct nfc_hci_dev *hdev,
			      struct nfc_target *target);
	int (*event_received)(struct nfc_hci_dev *hdev, u8 gate, u8 event,
			      struct sk_buff *skb);
  };
```

- `open()` 和 `close()` 应当启动和关闭硬件
- `hci_ready()` 是一个可选的入口点，在 hci 会话建立后立即被调用。驱动程序可以使用它来进行需要通过 HCI 命令执行的额外初始化。
- `xmit()` 应该简单地将一帧数据写入物理链路。
- `start_poll()` 是一个可选的入口点，应该将硬件设置为轮询模式。只有当硬件使用专有门或与 HCI 标准略有不同的机制时才需要实现此功能。
- `dep_link_up()` 在检测到 P2P 目标后被调用，以完成使用需要传递回 NFC 核心的硬件参数的 P2P 连接设置。
- `dep_link_down()` 被调用来关闭 P2P 链路。
- `target_from_gate()` 是一个可选的入口点，用于返回对应于专有门的 NFC 协议。
- `complete_target_discovered()` 是一个可选的入口点，允许驱动程序执行必要的专有处理来自动激活已发现的目标。
- `im_transceive()` 如果需要专有的 HCI 命令来向标签发送数据，则必须由驱动程序实现。某些类型的标签可能需要自定义命令，而其他类型则可以通过标准的 HCI 命令进行写入。驱动程序可以检查标签类型，并选择执行专有处理，或者返回 1 来请求标准处理。数据交换命令本身必须异步发送。
- `tm_send()` 在 P2P 连接的情况下被调用来发送数据。
- `check_presence()` 是一个可选的入口点，核心会定期调用它来检查已激活的标签是否仍在范围内。如果不实现这个功能，核心将无法向用户空间推送标签丢失事件。
- `event_received()` 被调用来处理来自芯片的事件。驱动程序可以处理该事件，或者返回 1 来让 HCI 尝试标准处理。

在接收路径上，驱动程序负责使用 `nfc_hci_recv_frame()` 将传入的 HCP 帧推送到 HCI。HCI 将负责重新聚合和处理这些帧。这必须在一个可以睡眠的上下文中完成。
### PHY 管理

物理链路（如 I2C 等）的管理由以下结构定义：

```c
struct nfc_phy_ops {
    int (*write)(void *dev_id, struct sk_buff *skb);
    int (*enable)(void *dev_id);
    void (*disable)(void *dev_id);
};
```

- `enable()`：
  - 打开物理链路（上电），使其准备好传输数据。
- `disable()`：
  - 关闭物理链路。
- `write()`：
  - 向芯片发送一个数据帧。需要注意的是，为了使更高层（例如 LLC 层）能够存储该帧以备重新发送，此函数不得修改 `skb`。它还必须不返回正数结果（成功时返回 0，失败时返回负数）。
  - 来自芯片的数据应直接发送给 `nfc_hci_recv_frame()`。

### LLC

CPU 和芯片之间的通信通常需要某种链路层协议。这些协议被作为模块由 HCI 层进行管理。目前有两种模块：nop（原始传输）和 shdlc。
一个新的 LLC 必须实现以下函数：

```c
struct nfc_llc_ops {
    void *(*init)(struct nfc_hci_dev *hdev, xmit_to_drv_t xmit_to_drv,
                  rcv_to_hci_t rcv_to_hci, int tx_headroom,
                  int tx_tailroom, int *rx_headroom, int *rx_tailroom,
                  llc_failure_t llc_failure);
    void (*deinit)(struct nfc_llc *llc);
    int (*start)(struct nfc_llc *llc);
    int (*stop)(struct nfc_llc *llc);
    void (*rcv_from_drv)(struct nfc_llc *llc, struct sk_buff *skb);
    int (*xmit_from_hci)(struct nfc_llc *llc, struct sk_buff *skb);
};
```

- `init()`：
  - 分配并初始化私有存储空间。
- `deinit()`：
  - 清理工作。
- `start()`：
  - 建立逻辑连接。
- `stop()`：
  - 终止逻辑连接。
- `rcv_from_drv()`：
  - 处理来自芯片的数据，将其传送给 HCI。
- `xmit_from_hci()`：
  - 处理由 HCI 发送的数据，将其传送给芯片。

LLC 必须在使用前通过调用以下函数注册到 NFC：

```c
nfc_llc_register(const char *name, const struct nfc_llc_ops *ops);
```

请注意，LLC 不处理物理链路。因此，对于给定的芯片驱动程序来说，很容易将任何物理链路与任何 LLC 混合使用。

### 包含的驱动程序

包含了一个基于 HCI 的驱动程序，用于通过 I2C 总线连接的 NXP PN544 芯片，并使用 shdlc 协议。

### 执行上下文

执行上下文如下：

- **IRQ 处理器 (IRQH)**：
  - 快速，不能睡眠。将接收到的帧发送到 HCI，然后传递给当前的 LLC。在使用 shdlc 的情况下，该帧会被放入 shdlc 接收队列中。
- **SHDLC 状态机工作者 (SMW)**：
  - 只有当使用 LLC_SHDLC 时：处理 shdlc 收发队列，分发 HCI 命令响应。
- **HCI 发送命令工作者 (MSGTXWQ)**：
  - 串行化执行 HCI 命令，在响应超时时完成执行。
### HCI Rx Worker (MSGRXWQ)

- 分发接收到的 HCI 命令或事件。
- 来自用户空间调用的系统调用上下文 (SYSCALL)。

任何从 NFC 核心调用的 HCI 入口点。

### 使用 shdlc 执行 HCI 命令的工作流程
--------------------------------------------------

执行一个 HCI 命令可以使用以下 API 同步地完成：

```c
int nfc_hci_send_cmd (struct nfc_hci_dev *hdev, u8 gate, u8 cmd,
                      const u8 *param, size_t param_len, struct sk_buff **skb)
```

此 API 必须在一个可以睡眠的上下文中被调用。大多数情况下，这将是系统调用上下文。`skb` 将返回接收到的响应结果。

内部执行是异步的。所以这个 API 实际上只是将 HCI 命令入队列，设置一个栈上的本地等待队列，并通过 `wait_event()` 等待命令完成。
等待过程不可中断，因为可以保证在短暂超时后命令会完成。

然后会调度 MSGTXWQ 上下文并调用 `nfc_hci_msg_tx_work()` 函数。
此函数会取出下一个待处理的命令，并将其 HCP 片段发送给底层（这里是 shdlc）。接着它会启动一个定时器，以便在没有收到响应时以超时错误完成命令。

SMW 上下文会被调度并调用 `nfc_shdlc_sm_work()` 函数。
此函数负责 shdlc 的帧收发。它使用驱动程序的发送功能发送帧，并从驱动程序的中断处理程序中接收传入的帧到一个 `skb` 队列中。

SHDLC 信息帧的有效载荷是 HCP 片段。这些片段被聚合形成完整的 HCI 帧，这些帧可以是响应、命令或事件。

- HCI 响应会立即从这个上下文分发出去，以解除等待命令执行的状态。响应处理包括调用由 `nfc_hci_msg_tx_work()` 在发送命令时提供的完成回调。
- 完成回调随后会唤醒系统调用上下文。
也可以使用此API异步执行命令：

```c
static int nfc_hci_execute_cmd_async(struct nfc_hci_dev *hdev, u8 pipe, u8 cmd,
				       const u8 *param, size_t param_len,
				       data_exchange_cb_t cb, void *cb_context)
```

工作流程大致相同，只是API调用会立即返回，并且回调函数会在SMW上下文中以结果的形式被调用。
接收HCI事件或命令的工作流程
------------------------------

HCI命令或事件不会从SMW上下文分发。相反，它们会被排队到HCI的rx_queue中，并且将从HCI的rx工作线程上下文（MSGRXWQ）进行分发。这样做是为了允许命令或事件处理程序也能执行其他命令（例如，从PN544处理NFC_HCI_EVT_TARGET_DISCOVERED事件需要向读卡器A门发送ANY_GET_PARAMETER命令来获取发现的目标的信息）
通常，这样的事件会从MSGRXWQ上下文传播到NFC Core。
错误管理
---------

与NFC Core请求同步发生的错误简单地作为该请求执行的结果返回。这些错误很容易处理。
异步发生的错误（例如，在后台协议处理线程中）必须报告给上层，以免它们不知道底层出现问题并且预期的事件可能永远不会发生。
这些错误的处理方式如下：

- 驱动程序（如pn544）未能传递传入帧：它存储错误以便任何后续对驱动程序的调用都会导致该错误。然后，它通过NULL参数调用标准nfc_shdlc_recv_frame()函数来向上报告问题。shdlc会存储一个EREMOTEIO粘性状态，这将触发SMW也向上报告问题。
- SMW基本上是一个用于处理传入和传出shdlc帧的后台线程。这个线程也会检查shdlc的粘性状态，并在发现由于shdlc内部或更低层出现不可恢复的错误而无法继续运行时向HCI报告。如果问题发生在shdlc连接期间，则通过连接完成通知错误。
- HCI：如果发生内部HCI错误（例如，帧丢失），或者从较低层报告给HCI的错误，HCI将要么使用该错误完成当前正在执行的命令，要么直接通知NFC Core（如果没有命令正在执行）。
- NFC Core：当NFC Core从下面被通知错误且轮询处于活动状态时，它会向用户空间发送一个带有空标签列表的标签发现事件，以告知轮询操作永远无法检测到标签。如果轮询未处于活动状态并且错误是粘性的，则较低层将在下次调用时返回该错误。
