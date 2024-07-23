UHID - 用户空间I/O驱动程序对HID子系统的支持
=============================================

UHID允许用户空间实现HID传输驱动程序。请参阅hid-transport.rst以了解HID传输驱动程序的介绍。本文档大量依赖于在那里声明的定义。
通过UHID，用户空间的传输驱动程序可以为连接到用户空间控制总线上的每个设备创建内核hid设备。UHID API定义了从内核到用户空间以及反之的I/O事件。
在./samples/uhid/uhid-example.c中有一个用户空间应用程序的例子。

UHID API
--------

UHID通过一个字符杂项设备访问。次设备号是动态分配的，因此你需要依赖udev（或类似工具）来创建设备节点。默认情况下这是/dev/uhid。
如果您的HID I/O驱动程序检测到新设备，并且您想将此设备注册到HID子系统，那么对于您要注册的每个设备，您需要打开一次/dev/uhid。所有进一步的通信都是通过读取(read())或写入(write())“struct uhid_event”对象完成的。非阻塞操作可以通过设置O_NONBLOCK来支持::

  struct uhid_event {
        __u32 type;
        union {
                struct uhid_create2_req create2;
                struct uhid_output_req output;
                struct uhid_input2_req input2;
                ..
        } u;
  };

"type"字段包含事件的ID。根据ID的不同，会发送不同的有效载荷。你不能将单个事件分割到多个读取(read)或写入(write)调用中。单个事件必须作为一个整体发送。此外，每次读取(read)或写入(write)只能发送一个事件。待处理的数据会被忽略。
如果你想在一个系统调用中处理多个事件，那么使用readv()/writev()的向量I/O。
"type"字段定义了有效载荷。对于每种类型，在union "u"中都有一个相应的有效载荷结构（除了空的有效载荷）。这个有效载荷包含管理和/或设备数据。
首先你应该发送一个UHID_CREATE2事件。这将注册设备。UHID将响应一个UHID_START事件。你现在可以开始向UHID发送数据和从UHID读取数据。但是，除非UHID发送UHID_OPEN事件，否则内部附加的HID设备驱动程序没有用户连接。
也就是说，除非你接收到UHID_OPEN事件，否则你可能让设备进入睡眠状态。如果你接收到UHID_OPEN事件，你应该开始I/O操作。如果最后一个用户关闭HID设备，你将接收到一个UHID_CLOSE事件。这可能随后再次接收到UHID_OPEN事件等等。没有必要在用户空间执行引用计数。也就是说，你永远不会在没有UHID_CLOSE事件的情况下接收到多个UHID_OPEN事件。HID子系统为你进行引用计数。
你可能决定忽略UHID_OPEN/UHID_CLOSE事件，尽管如此，即使设备可能没有用户，I/O操作仍然是允许的。
如果你想通过中断通道向HID子系统发送数据，你可以发送一个带有原始数据负载的HID_INPUT2事件。如果内核想要通过中断通道向设备发送数据，你将读取一个UHID_OUTPUT事件。
目前，控制通道上的数据请求仅限于GET_REPORT和SET_REPORT（到目前为止，控制通道上尚未定义其他数据报告）。这些请求总是同步的。这意味着，内核发送UHID_GET_REPORT和UHID_SET_REPORT事件，并要求你将它们转发到设备的控制通道上。一旦设备响应，你必须通过UHID_GET_REPORT_REPLY和UHID_SET_REPORT_REPLY将响应转发给内核。在这样的往返过程中，内核会在内部阻止驱动程序执行（超时时间由硬编码设定）。
如果你的设备断开连接，你应该发送一个UHID_DESTROY事件。这将注销该设备。你现在可以再次发送UHID_CREATE2来注册一个新的设备。
如果你关闭文件描述符(fd)，设备将自动被注销并在内部销毁。

write()函数：
-------
write()函数允许你修改设备的状态并输入数据进入内核。内核会立即解析事件，如果事件ID不受支持，它将返回-EOPNOTSUPP。如果有效载荷无效，则返回-EINVAL，否则，返回读取的数据量，表明请求已成功处理。O_NONBLOCK不会影响write()，因为写入总是以非阻塞方式立即处理。然而，未来的请求可能会利用O_NONBLOCK。

UHID_CREATE2：
  这个事件创建内部的HID设备。在你将此事件发送给内核之前，无法进行任何I/O操作。payload类型为struct uhid_create2_req，其中包含关于你的设备的信息。现在你可以开始I/O操作了。

UHID_DESTROY：
  这个事件销毁内部的HID设备。不再接受进一步的I/O操作。可能还有一些待处理的消息，你可以通过read()接收，但是不能再向内核发送UHID_INPUT事件。
你可以通过再次发送 UHID_CREATE2 来创建一个新的设备。无需重新打开字符设备。

UHID_INPUT2：
在向内核发送输入前，你必须发送 UHID_CREATE2！此事件包含数据负载。这是从你的设备中断通道读取的原始数据。内核将解析HID报告。

UHID_GET_REPORT_REPLY：
如果你收到 UHID_GET_REPORT 请求，你必须用这个请求进行回应。
你必须从请求中复制 "id" 字段到回答中。如果没有错误发生，则将 "err" 字段设置为0；如果发生I/O错误，则将其设置为EIO。
如果 "err" 是0，那么你应该用GET_REPORT请求的结果填充回答的缓冲区，并相应地设置 "size"。

UHID_SET_REPORT_REPLY：
这是 UHID_GET_REPORT_REPLY 的 SET_REPORT 等效项。与GET_REPORT不同，SET_REPORT永远不会返回数据缓冲区，因此，正确设置 "id" 和 "err" 字段就足够了。

read()函数
-----------------
read()函数会返回一个排队的输出报告。对于它们无需任何反应，但你应该根据需要处理它们。

UHID_START：
当HID设备启动时发送此消息。可将其视为对 UHID_CREATE2 的响应。这总是发送的第一个事件。请注意，在write(UHID_CREATE2)返回后，此事件可能不会立即可用。
设备驱动程序可能需要延迟设置。
此事件包含uhid_start_req类型的负载。“dev_flags”字段描述了设备的特殊行为。定义了以下标志：

- UHID_DEV_NUMBERED_FEATURE_REPORTS
- UHID_DEV_NUMBERED_OUTPUT_REPORTS
- UHID_DEV_NUMBERED_INPUT_REPORTS

每个这些标志定义了给定报告类型是否使用编号报告。如果某类型使用编号报告，则内核发来的所有消息已经以报告号作为前缀。否则，内核不会添加前缀。
对于用户空间发送到内核的消息，你必须根据这些标志调整前缀。

UHID_STOP：
当HID设备停止时会发送此消息。将其视为对UHID_DESTROY的响应。
如果你没有通过UHID_DESTROY销毁你的设备，但是内核发送了一个UHID_STOP事件，这通常应该被忽略。这意味着内核重新加载/更改了加载在你的HID设备上的设备驱动（或其他维护动作发生）。
你通常可以安全地忽略任何UHID_STOP事件。

UHID_OPEN：
当HID设备被打开时会发送此消息。也就是说，HID设备提供的数据被其他进程读取。你可以忽略这个事件，但它对于电源管理很有用。只要你还未收到此事件，实际上就没有其他进程读取你的数据，因此无需向内核发送UHID_INPUT2事件。

UHID_CLOSE：
当不再有进程读取HID数据时会发送此消息。它是UHID_OPEN的对应物，你也可以忽略这个事件。

UHID_OUTPUT：
如果HID设备驱动程序想要通过中断通道向I/O设备发送原始数据，则会发送此消息。你应该读取有效负载并将其转发给设备。有效负载类型为“struct uhid_output_req”。
即使你尚未收到UHID_OPEN，这也可能会收到。

UHID_GET_REPORT：
如果内核驱动程序想要在控制通道上执行GET_REPORT请求（如HID规范中所述），则会发送此事件。报告类型和报告编号可在有效负载中获取。
内核会串行化GET_REPORT请求，因此永远不会有两个并行的请求。但是，如果你未能以UHID_GET_REPORT_REPLY响应，该请求可能静默超时。
一旦你读取到一个GET_REPORT请求，你应该将其转发给HID设备，并记住负载中的"id"字段。一旦你的HID设备响应了GET_REPORT（或者如果它失败了），你必须使用与请求中完全相同的"id"向内核发送UHID_GET_REPORT_REPLY。如果请求已经超时，内核将默默地忽略响应。"id"字段永远不会被重复使用，因此不会发生冲突。

UHID_SET_REPORT：
这是UHID_GET_REPORT的SET_REPORT等价操作。在接收到它时，你应该向你的HID设备发送一个SET_REPORT请求。一旦它回复，你必须通过UHID_SET_REPORT_REPLY通知内核。
对于UHID_GET_REPORT的相同限制同样适用。

编写于2012年，David Herrmann <dh.herrmann@gmail.com>
