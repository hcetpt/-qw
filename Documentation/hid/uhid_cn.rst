UHID - 用户空间 I/O 驱动程序对 HID 子系统的支持
======================================================

UHID 允许用户空间实现 HID 传输驱动程序。请参阅 `hid-transport.rst` 以了解 HID 传输驱动程序的介绍。本文档大量依赖于其中声明的定义。
借助 UHID，用户空间传输驱动程序可以为连接到用户空间控制总线的每个设备创建内核 hid 设备。UHID API 定义了从内核到用户空间以及相反方向提供的 I/O 事件。
在 ./samples/uhid/uhid-example.c 中有一个用户空间应用程序示例。

UHID API
------------

UHID 通过一个字符杂项设备进行访问。次要数字是动态分配的，因此您需要依赖 udev（或类似工具）来创建设备节点。
默认情况下这是 `/dev/uhid`。
如果您的 HID I/O 驱动程序检测到了新设备，并且想要将此设备注册到 HID 子系统，则需要为要注册的每个设备打开一次 `/dev/uhid`。之后的所有通信都是通过读取或写入 "struct uhid_event" 对象完成的。支持非阻塞操作，设置 `O_NONBLOCK` 即可：
```c
  struct uhid_event {
        __u32 type;
        union {
                struct uhid_create2_req create2;
                struct uhid_output_req output;
                struct uhid_input2_req input2;
                // ...
        } u;
  };
```
"type" 字段包含事件的 ID。根据 ID 的不同，发送不同的有效载荷。您不能将单个事件拆分为多次读取或写入操作。单个事件必须作为一个整体发送。此外，每次读取或写入只能发送一个事件。挂起的数据将被忽略。
如果您想在一个系统调用中处理多个事件，请使用带有 readv()/writev() 的向量 I/O。
"type" 字段定义了有效载荷。对于每种类型，在联合 "u" 中都有一种对应的有效载荷结构（除了空的有效载荷）。此有效载荷包含管理和/或设备数据。
首先，您应该发送一个 UHID_CREATE2 事件。这将注册该设备。UHID 将会响应一个 UHID_START 事件。现在您可以开始向 UHID 发送数据并从中读取数据。但是，除非 UHID 发送 UHID_OPEN 事件，否则内部附带的 HID 设备驱动程序将没有用户连接。
也就是说，在接收到 UHID_OPEN 事件之前，您可以将您的设备置于睡眠状态。如果接收到 UHID_OPEN 事件，则应开始 I/O 操作。当最后一个用户关闭 HID 设备时，您将接收到 UHID_CLOSE 事件。这可能随后再次出现 UHID_OPEN 事件等。无需在用户空间执行引用计数。也就是说，您永远不会接收到多个 UHID_OPEN 事件而没有 UHID_CLOSE 事件。HID 子系统为您执行引用计数。
您可以选择忽略UHID_OPEN/UHID_CLOSE事件。即使设备可能没有用户，I/O操作仍然是允许的。
如果您希望通过中断通道向HID子系统发送数据，您需要发送一个HID_INPUT2事件，并附带原始数据负载。如果内核希望通过中断通道向设备发送数据，则您会读取到一个UHID_OUTPUT事件。
目前控制通道上的数据请求仅限于GET_REPORT和SET_REPORT（目前为止在控制通道上尚未定义其他数据报告）。这些请求总是同步的。这意味着内核会发送UHID_GET_REPORT和UHID_SET_REPORT事件，并要求您将它们转发给设备的控制通道。一旦设备响应，您必须通过UHID_GET_REPORT_REPLY和UHID_SET_REPORT_REPLY将响应转发给内核。
在此类往返期间，内核会在内部阻止驱动程序执行（超时时间是硬编码的）。
如果您的设备断开连接，您应该发送一个UHID_DESTROY事件。这将注销该设备。现在您可以再次发送UHID_CREATE2来注册一个新的设备。
如果您关闭文件描述符(fd)，则设备会被自动注销并内部销毁。
write()
------
write()允许您修改设备的状态并向内核输入数据。内核会立即解析事件。如果事件ID不受支持，它将返回-EOPNOTSUPP。如果负载无效，则返回-EINVAL；否则，返回已读取的数据量，且请求成功处理。O_NONBLOCK不会影响write()，因为写操作总是以非阻塞方式立即处理。不过，未来的请求可能会利用O_NONBLOCK。

UHID_CREATE2：
  此事件创建内部HID设备。在您向内核发送此事件之前，无法进行任何I/O操作。负载类型为struct uhid_create2_req，包含关于您的设备的信息。现在您可以开始I/O操作了。

UHID_DESTROY：
  此事件销毁内部HID设备。不再接受进一步的I/O操作。可能还有一些待处理的消息可以通过read()接收，但不能再向内核发送UHID_INPUT事件。
您可以再次发送 `UHID_CREATE2` 来创建一个新的设备。无需重新打开字符设备。

`UHID_INPUT2`：
  在向内核发送输入之前，您必须发送 `UHID_CREATE2`！此事件包含数据负载。这是从您的设备中断通道读取的原始数据。内核将解析HID报告。

`UHID_GET_REPORT_REPLY`：
  如果您收到 `UHID_GET_REPORT` 请求，则必须用此请求进行回应。
  您必须将请求中的 "id" 字段复制到回答中。如果未发生错误，则将 "err" 字段设置为0；如果发生I/O错误，则将其设置为EIO。
  如果 "err" 为0，则应使用 `GET_REPORT` 请求的结果填充答案的缓冲区，并相应地设置 "size"。

`UHID_SET_REPORT_REPLY`：
  这是 `UHID_GET_REPORT_REPLY` 的 `SET_REPORT` 等效项。与 `GET_REPORT` 不同的是，`SET_REPORT` 从不返回数据缓冲区，因此只需正确设置 "id" 和 "err" 字段即可。

`read()`  
---
`read()` 将返回一个排队输出的报告。对于它们中的任何一个都不需要做出反应，但您应该根据自己的需求来处理。

`UHID_START`：
  当HID设备启动时会发送此消息。可将其视为对 `UHID_CREATE2` 的响应。这始终是发送的第一个事件。请注意，此事件可能不会在 `write(UHID_CREATE2)` 返回后立即可用。
  设备驱动程序可能需要延迟设置。
  此事件包含类型为 `uhid_start_req` 的负载。“dev_flags”字段描述了设备的特殊行为。以下定义了标志：

      - `UHID_DEV_NUMBERED_FEATURE_REPORTS`
      - `UHID_DEV_NUMBERED_OUTPUT_REPORTS`
      - `UHID_DEV_NUMBERED_INPUT_REPORTS`

      每个标志都定义了给定类型的报告是否使用编号报告。如果某类型使用了编号报告，则来自内核的所有消息已将报告号作为前缀。否则，内核不会添加任何前缀。
对于用户空间发送到内核的消息，您必须根据这些标志调整前缀。

`UHID_STOP`：
  当HID设备停止时会发送此消息。可将其视为对`UHID_DESTROY`的响应。
  如果您没有通过`UHID_DESTROY`销毁您的设备，但内核发送了一个`UHID_STOP`事件，这通常可以被忽略。这意味着内核重新加载/更改了加载在您的HID设备上的设备驱动程序（或发生了其他维护操作）。
  您通常可以安全地忽略任何`UHID_STOP`事件。

`UHID_OPEN`：
  当HID设备被打开时会发送此消息。也就是说，HID设备提供的数据被其他进程读取。您可以忽略这个事件，但对于电源管理很有用。只要您还没有收到这个事件，实际上就没有其他进程在读取您的数据，因此没有必要向内核发送`UHID_INPUT2`事件。

`UHID_CLOSE`：
  当不再有进程读取HID数据时会发送此消息。它是`UHID_OPEN`的对应事件，您也可以忽略这个事件。

`UHID_OUTPUT`：
  如果HID设备驱动程序想要通过中断通道向I/O设备发送原始数据，则会发送此消息。您应该读取负载并将数据转发给设备。负载类型为“struct uhid_output_req”。
  即使您尚未收到`UHID_OPEN`，这也可能会接收到。

`UHID_GET_REPORT`：
  如果内核驱动程序想要根据HID规范在控制通道上执行GET_REPORT请求，则会发送此事件。报告类型和报告编号可在负载中找到。
  内核会对GET_REPORT请求进行序列化处理，因此永远不会有两个并行的请求。但是，如果您未能通过`UHID_GET_REPORT_REPLY`作出响应，该请求可能会默默地超时。
一旦你读取了一个 `GET_REPORT` 请求，你应该将其转发给 HID 设备，并记住负载中的 "id" 字段。一旦你的 HID 设备响应了 `GET_REPORT`（或如果它失败了），你必须用与请求中完全相同的 "id" 向内核发送一个 `UHID_GET_REPORT_REPLY`。如果请求已经超时，内核会默默地忽略这个响应。“id”字段永远不会被重复使用，因此不会发生冲突。

`UHID_SET_REPORT`：
这是 `UHID_GET_REPORT` 的 `SET_REPORT` 等效项。收到后，你应该向你的 HID 设备发送一个 `SET_REPORT` 请求。一旦它回复，你必须通过 `UHID_SET_REPORT_REPLY` 告知内核。
对于 `UHID_GET_REPORT` 的相同限制也适用于此。

编写于 2012 年，David Herrmann <dh.herrmann@gmail.com>
