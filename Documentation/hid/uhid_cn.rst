===============================================
UHID - 用户空间 I/O 驱动程序对 HID 子系统的支持
===============================================

UHID 允许用户空间实现 HID 传输驱动程序。请参阅 hid-transport.rst 以了解 HID 传输驱动程序的介绍。本文档大量依赖于其中声明的定义。
通过 UHID，用户空间传输驱动程序可以为连接到用户空间控制总线的每个设备创建内核 hid 设备。UHID API 定义了内核与用户空间之间提供的 I/O 事件及其反向流程。
在 ./samples/uhid/uhid-example.c 中有一个示例用户空间应用程序。

UHID API
--------

UHID 通过一个字符杂项设备访问。次要编号是动态分配的，因此您需要依赖 udev（或类似工具）来创建设备节点。默认情况下这是 /dev/uhid。
如果您的 HID I/O 驱动程序检测到新设备并且希望将该设备注册到 HID 子系统，则需要为要注册的每个设备打开一次 /dev/uhid。之后的所有通信都通过读取(read())或写入(write())“struct uhid_event”对象完成。非阻塞操作可以通过设置 O_NONBLOCK 来实现：

```c
  struct uhid_event {
        __u32 type;
        union {
                struct uhid_create2_req create2;
                struct uhid_output_req output;
                struct uhid_input2_req input2;
                ...
        } u;
  };
```

"type" 字段包含事件的 ID。根据 ID 的不同，会发送不同的有效负载。您不能将单个事件拆分到多次读取或写入操作中。单个事件必须作为一个整体发送。此外，每次读取或写入只能发送一个事件。待处理的数据将被忽略。
如果您希望在单个系统调用中处理多个事件，请使用带有 readv()/writev() 的向量 I/O。
"type" 字段定义了有效负载。对于每种类型，在联合 "u" 中都有一个相应的有效负载结构（除了空的有效负载）。此有效负载包含管理和/或设备数据。
首先应该做的是发送一个 UHID_CREATE2 事件。这将会注册设备。UHID 将会响应一个 UHID_START 事件。现在您可以开始向 UHID 发送数据并从 UHID 读取数据。但是，除非 UHID 发送 UHID_OPEN 事件，否则内部连接的 HID 设备驱动程序没有用户连接。
也就是说，如果没有接收到 UHID_OPEN 事件，您可以将设备置于休眠状态。如果接收到 UHID_OPEN 事件，您应该开始 I/O 操作。如果最后一个用户关闭了 HID 设备，您将接收到一个 UHID_CLOSE 事件。这可能会再次跟随一个 UHID_OPEN 事件等。无需在用户空间中执行引用计数。也就是说，您永远不会在没有 UHID_CLOSE 事件的情况下接收到多个 UHID_OPEN 事件。HID 子系统会为您执行引用计数。
你可以选择忽略 UHID_OPEN/UHID_CLOSE。即使设备可能没有用户，I/O 操作仍然是允许的。

如果你想通过中断通道向 HID 子系统发送数据，你需要发送一个带有原始数据负载的 HID_INPUT2 事件。如果内核想要通过中断通道向设备发送数据，你会读取一个 UHID_OUTPUT 事件。

目前控制通道上的数据请求仅限于 GET_REPORT 和 SET_REPORT（到目前为止控制通道上还没有定义其他数据报告）。这些请求总是同步的。这意味着内核会发送 UHID_GET_REPORT 和 UHID_SET_REPORT 事件，并要求你将它们通过控制通道转发给设备。一旦设备响应，你必须通过 UHID_GET_REPORT_REPLY 和 UHID_SET_REPORT_REPLY 将响应转发给内核。在此过程中，内核会在一定时间内阻塞内部驱动程序执行（超时时间是硬编码的）。

如果你的设备断开连接，你应该发送一个 UHID_DESTROY 事件。这将注销设备。你现在可以再次发送 UHID_CREATE2 来注册一个新的设备。

如果你关闭文件描述符（fd），设备会自动被注销并内部销毁。

write()
-------
`write()` 允许你修改设备的状态并向内核输入数据。内核会立即解析事件，如果事件 ID 不受支持，它会返回 -EOPNOTSUPP。如果负载无效，则返回 -EINVAL，否则返回读取的数据量，表示请求处理成功。O_NONBLOCK 对 `write()` 没有影响，因为写操作总是以非阻塞方式立即处理。未来的请求可能会使用 O_NONBLOCK。

UHID_CREATE2：
  这个事件创建内部 HID 设备。在你将这个事件发送给内核之前，无法进行任何 I/O 操作。负载类型为 `struct uhid_create2_req`，包含关于你的设备的信息。现在你可以开始 I/O 操作了。

UHID_DESTROY：
  这个事件销毁内部 HID 设备。不再接受进一步的 I/O 操作。仍然可能有一些待处理的消息可以通过 `read()` 接收，但不能再向内核发送 UHID_INPUT 事件。
你可以通过再次发送 `UHID_CREATE2` 来创建一个新的设备。无需重新打开字符设备。

`UHID_INPUT2`：
  在向内核发送输入之前，你必须先发送 `UHID_CREATE2`！此事件包含数据负载。这是你从设备的中断通道读取的原始数据。内核将解析HID报告。

`UHID_GET_REPORT_REPLY`：
  如果你收到一个 `UHID_GET_REPORT` 请求，你必须用这个请求来回应。
  你必须将请求中的 "id" 字段复制到答案中。如果未发生错误，则将 "err" 字段设置为0；如果发生I/O错误，则将其设置为EIO。
  如果 "err" 是0，则你应该用 `GET_REPORT` 请求的结果填充答案的缓冲区，并相应地设置 "size" 字段。

`UHID_SET_REPORT_REPLY`：
  这是 `UHID_GET_REPORT_REPLY` 的 `SET_REPORT` 版本。与 `GET_REPORT` 不同，`SET_REPORT` 永远不会返回数据缓冲区，因此只需正确设置 "id" 和 "err" 字段即可。

`read()`：
  `read()` 将返回一个排队的输出报告。对于这些报告无需进行任何反应，但你应该根据需要处理它们。

`UHID_START`：
  当HID设备启动时会发送此事件。将其视为对 `UHID_CREATE2` 的响应。这总是第一个被发送的事件。请注意，此事件可能不会在 `write(UHID_CREATE2)` 返回后立即可用。
  设备驱动程序可能需要延迟设置。
  此事件包含类型为 `uhid_start_req` 的负载。"dev_flags" 字段描述了设备的特殊行为。定义了以下标志：

      - `UHID_DEV_NUMBERED_FEATURE_REPORTS`
      - `UHID_DEV_NUMBERED_OUTPUT_REPORTS`
      - `UHID_DEV_NUMBERED_INPUT_REPORTS`

  每个标志定义了给定报告类型是否使用编号报告。如果某种类型的报告使用编号报告，则内核发送的所有消息已经以报告号作为前缀。否则，内核不会添加任何前缀。
对于用户空间发送到内核的消息，你必须根据这些标志调整前缀。

UHID_STOP：
  当HID设备停止时会发送此消息。将其视为对UHID_DESTROY的响应。
  如果你没有通过UHID_DESTROY销毁你的设备，但内核发送了UHID_STOP事件，通常可以忽略这个事件。这意味着内核重新加载/更改了加载在你的HID设备上的设备驱动程序（或发生了其他维护操作）。
  你可以安全地忽略任何UHID_STOP事件。

UHID_OPEN：
  当HID设备被打开时会发送此消息。也就是说，其他进程读取了HID设备提供的数据。你可以忽略这个事件，但对于电源管理是有用的。只要你还没有收到这个事件，实际上就没有其他进程读取你的数据，因此无需向内核发送UHID_INPUT2事件。

UHID_CLOSE：
  当没有其他进程读取HID数据时会发送此消息。它是UHID_OPEN的对应事件，你也可以忽略这个事件。

UHID_OUTPUT：
  如果HID设备驱动程序希望通过中断通道向I/O设备发送原始数据，则会发送此消息。你应该读取有效载荷并将其转发给设备。有效载荷类型为“struct uhid_output_req”。
  即使你尚未收到UHID_OPEN，也可能接收到此消息。

UHID_GET_REPORT：
  如果内核驱动程序希望在控制通道上执行GET_REPORT请求（如HID规范中所述），则会发送此事件。报告类型和报告编号可在有效载荷中获取。
  内核会对GET_REPORT请求进行序列化处理，因此不会同时有两个请求。但是，如果你未能通过UHID_GET_REPORT_REPLY进行响应，请求可能会默默地超时。
一旦你读取了一个 `GET_REPORT` 请求，你应该将其转发给 HID 设备，并记住请求负载中的 "id" 字段。一旦你的 HID 设备响应了 `GET_REPORT`（或失败），你必须使用相同的 "id" 向内核发送一个 `UHID_GET_REPORT_REPLY`。如果请求已经超时，内核会默默地忽略该响应。"id" 字段从不重复使用，因此不会发生冲突。

`UHID_SET_REPORT`：
这是 `UHID_GET_REPORT` 的 `SET_REPORT` 等价操作。收到请求后，你应该向你的 HID 设备发送一个 `SET_REPORT` 请求。一旦设备回应，你必须通过 `UHID_SET_REPORT_REPLY` 告知内核。
对于 `UHID_GET_REPORT` 的限制同样适用于 `UHID_SET_REPORT`。

编写于 2012 年，David Herrmann <dh.herrmann@gmail.com>
