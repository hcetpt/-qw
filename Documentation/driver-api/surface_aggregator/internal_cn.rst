SPDX 许可证标识符: GPL-2.0+

.. |ssh_ptl| replace:: :c:type:`struct ssh_ptl <ssh_ptl>`
.. |ssh_ptl_submit| replace:: :c:func:`ssh_ptl_submit`
.. |ssh_ptl_cancel| replace:: :c:func:`ssh_ptl_cancel`
.. |ssh_ptl_shutdown| replace:: :c:func:`ssh_ptl_shutdown`
.. |ssh_ptl_rx_rcvbuf| replace:: :c:func:`ssh_ptl_rx_rcvbuf`
.. |ssh_rtl| replace:: :c:type:`struct ssh_rtl <ssh_rtl>`
.. |ssh_rtl_submit| replace:: :c:func:`ssh_rtl_submit`
.. |ssh_rtl_cancel| replace:: :c:func:`ssh_rtl_cancel`
.. |ssh_rtl_shutdown| replace:: :c:func:`ssh_rtl_shutdown`
.. |ssh_packet| replace:: :c:type:`struct ssh_packet <ssh_packet>`
.. |ssh_packet_get| replace:: :c:func:`ssh_packet_get`
.. |ssh_packet_put| replace:: :c:func:`ssh_packet_put`
.. |ssh_packet_ops| replace:: :c:type:`struct ssh_packet_ops <ssh_packet_ops>`
.. |ssh_packet_base_priority| replace:: :c:type:`enum ssh_packet_base_priority <ssh_packet_base_priority>`
.. |ssh_packet_flags| replace:: :c:type:`enum ssh_packet_flags <ssh_packet_flags>`
.. |SSH_PACKET_PRIORITY| replace:: :c:func:`SSH_PACKET_PRIORITY`
.. |ssh_frame| replace:: :c:type:`struct ssh_frame <ssh_frame>`
.. |ssh_command| replace:: :c:type:`struct ssh_command <ssh_command>`
.. |ssh_request| replace:: :c:type:`struct ssh_request <ssh_request>`
.. |ssh_request_get| replace:: :c:func:`ssh_request_get`
.. |ssh_request_put| replace:: :c:func:`ssh_request_put`
.. |ssh_request_ops| replace:: :c:type:`struct ssh_request_ops <ssh_request_ops>`
.. |ssh_request_init| replace:: :c:func:`ssh_request_init`
.. |ssh_request_flags| replace:: :c:type:`enum ssh_request_flags <ssh_request_flags>`
.. |ssam_controller| replace:: :c:type:`struct ssam_controller <ssam_controller>`
.. |ssam_device| replace:: :c:type:`struct ssam_device <ssam_device>`
.. |ssam_device_driver| replace:: :c:type:`struct ssam_device_driver <ssam_device_driver>`
.. |ssam_client_bind| replace:: :c:func:`ssam_client_bind`
.. |ssam_client_link| replace:: :c:func:`ssam_client_link`
.. |ssam_request_sync| replace:: :c:type:`struct ssam_request_sync <ssam_request_sync>`
.. |ssam_event_registry| replace:: :c:type:`struct ssam_event_registry <ssam_event_registry>`
.. |ssam_event_id| replace:: :c:type:`struct ssam_event_id <ssam_event_id>`
.. |ssam_nf| replace:: :c:type:`struct ssam_nf <ssam_nf>`
.. |ssam_nf_refcount_inc| replace:: :c:func:`ssam_nf_refcount_inc`
.. |ssam_nf_refcount_dec| replace:: :c:func:`ssam_nf_refcount_dec`
.. |ssam_notifier_register| replace:: :c:func:`ssam_notifier_register`
.. |ssam_notifier_unregister| replace:: :c:func:`ssam_notifier_unregister`
.. |ssam_cplt| replace:: :c:type:`struct ssam_cplt <ssam_cplt>`
.. |ssam_event_queue| replace:: :c:type:`struct ssam_event_queue <ssam_event_queue>`
.. |ssam_request_sync_submit| replace:: :c:func:`ssam_request_sync_submit`

=====================
核心驱动程序内部结构
=====================

Surface System Aggregator Module (SSAM) 核心和 Surface 串行集线器 (SSH) 驱动程序的架构概述。有关 API 文档，请参考：

.. toctree::
   :maxdepth: 2

   内部-API


概述
========

SSAM 核心实现按层次构建，某种程度上遵循了 SSH 协议的结构：

较低级别的数据包传输在 *数据包传输层 (PTL)* 中实现，直接基于内核中的串行设备 (serdev) 基础设施。正如其名称所示，这一层处理数据包传输逻辑，并处理诸如数据包验证、数据包确认（ACK）、数据包重传超时以及将数据包负载转发到较高层等问题。
在此之上是 *请求传输层 (RTL)*。这一层主要围绕命令类型的数据包负载，即从主机发送给 EC 的请求、EC 对这些请求的响应，以及从 EC 发送给主机的事件。
特别是，它区分了事件与请求响应，将响应与相应的请求匹配，并实现了请求超时。
*控制器* 层在此基础上建立，基本上决定了如何处理请求响应，尤其是事件。它提供了一个事件通知系统，处理事件激活/停用，为事件和异步请求完成提供一个工作队列，并且还管理用于构建命令消息（"SEQ", "RQID"）所需的消息计数器。这一层基本上为其他内核驱动程序提供了对 SAM EC 的基本接口。
虽然控制器层已经为其他内核驱动程序提供了一个接口，但客户端 *总线* 扩展了这个接口，通过 |ssam_device| 和 |ssam_device_driver| 提供对原生 SSAM 设备的支持，即那些不在 ACPI 中定义且未作为平台设备实现的设备，简化了客户端设备和客户端驱动程序的管理。
请参考 Documentation/driver-api/surface_aggregator/client.rst 获取有关客户端设备/驱动程序 API 和接口选项的文档，以便其他内核驱动程序使用。建议先熟悉那一章和 Documentation/driver-api/surface_aggregator/ssh.rst，然后再继续阅读下面的架构概述。
数据包传输层
======================

数据包传输层由 |ssh_ptl| 表示，并围绕以下关键概念构建：

数据包
-------

数据包是 SSH 协议的基本传输单元。它们由数据包传输层管理，该层本质上是驱动程序的最低层，并被 SSAM 核心的其他组件构建于其上。
要由 SSAM 核心传输的数据包通过 |ssh_packet| 表示（相反，接收到的核心数据包没有任何特定的结构，并完全通过原始的 |ssh_frame| 进行管理）。
此结构包含在传输层中管理数据包所需的字段，以及指向包含待传输数据的缓冲区（即被 |ssh_frame| 包装的消息）的引用。最值得注意的是，它包含了一个内部引用计数，用于管理其生命周期（可通过 |ssh_packet_get| 和 |ssh_packet_put| 访问）。当此计数器达到零时，通过其 |ssh_packet_ops| 引用提供给数据包的 "release()" 回调函数会被执行，然后可能会释放数据包或其封闭结构（例如 |ssh_request|）。
除了 "release" 回调函数外，|ssh_packet_ops| 引用还提供了 "complete()" 回调函数，当数据包完成时运行，并提供完成状态，即成功时为零，出错时为负的 errno 值。一旦数据包提交给数据包传输层，则始终保证 "complete()" 回调函数在 "release()" 回调函数之前执行，即数据包总会被完成，无论是成功、出错还是因取消而完成，在其被释放之前。
数据包的状态通过其`state`标志（|ssh_packet_flags|）进行管理，这些标志中也包含了数据包的类型。特别是，以下位值得注意：

* `SSH_PACKET_SF_LOCKED_BIT`：当完成（无论是由于错误还是成功）即将发生时，将设置此位。这表示不应再获取该数据包的进一步引用，并且应尽快丢弃任何现有引用。设置此位的过程负责从数据包队列和待处理集合中移除对该数据包的所有引用。
* `SSH_PACKET_SF_COMPLETED_BIT`：此位由运行`complete()`回调的过程设置，并用于确保此回调仅运行一次。
* `SSH_PACKET_SF_QUEUED_BIT`：当数据包被加入到数据包队列时，将设置此位；当它从队列中移除时，则清除此位。
* `SSH_PACKET_SF_PENDING_BIT`：当数据包被添加到待处理集合时，将设置此位；当它从待处理集合中移除时，则清除此位。

### 数据包队列

数据包队列是数据包传输层中的两个基本集合之一。这是一个优先级队列，其中各个数据包的优先级基于数据包类型（主要）和尝试次数（次要）。有关优先级值的更多详细信息，请参阅|SSH_PACKET_PRIORITY|。所有要通过传输层传输的数据包都必须通过|ssh_ptl_submit|提交到这个队列。请注意，这包括由传输层自身发送的控制数据包。在内部，由于超时或EC发送的NAK数据包，数据包可以重新提交到此队列。

### 待处理集合

待处理集合是数据包传输层中的另一个基本集合。它存储已发送但等待EC确认（例如，相应的ACK数据包）的数据包的引用。请注意，如果数据包因数据包确认超时或NAK而重新提交，则可能同时处于待处理状态和排队状态，在这种情况下，数据包不会从待处理集合中移除。

### 发送线程

发送线程负责大部分与数据包传输相关的工作。在每次迭代中，它（等待并）检查队列上的下一个数据包（如果有的话）是否可以传输，并且如果可以，则将其从队列中移除并增加其传输尝试次数计数器。如果该数据包是有序的，即需要EC的ACK，则将数据包添加到待处理集合中。接下来，将数据包的数据提交给serdev子系统。如果在此提交过程中发生错误或超时，发送线程会根据回调的状态值完成数据包。如果数据包是无序的，即不需要EC的ACK，则在发送线程上以成功状态完成数据包。

有序数据包的传输受到同时待处理的数据包数量的限制，即允许多少个数据包同时等待EC的ACK。当前此限制设置为一个（请参阅Documentation/driver-api/surface_aggregator/ssh.rst了解背后的理由）。控制数据包（即ACK和NAK）始终可以传输。
接收线程
---------------
从EC接收到的任何数据都会被放入FIFO缓冲区以供进一步处理。这一处理过程发生在接收线程上。接收线程解析并验证接收到的消息为`|ssh_frame|`及其对应的负载。它准备并提交必要的ACK（在验证错误或无效数据时提交NAK）包作为已接收消息的响应。
该线程还负责进一步的处理，例如通过序列ID将ACK消息与相应的待定包匹配并完成该包，以及在接收到NAK消息时重新提交所有当前待定包（由于NAK而进行的重新提交类似于因超时而进行的重新提交，下面会详细介绍）。需要注意的是，有序包的成功完成总是运行在接收线程上（而任何指示失败的完成则在发生失败的地方运行）。
任何负载数据都会通过回调转发给上一层，即请求传输层。

超时重置器
--------------
包确认超时是一个针对有序包的每包超时，当相应包开始（重新）传输时启动（即每次传输尝试时在发送线程上设置这个超时）。它用于触发包的重新提交，或者当尝试次数超过限制时取消该包。

这个超时是通过一个专用的重置任务来处理的，本质上是一个工作项，在下一个包即将超时时被（重新）安排运行。工作项然后检查待定包集合中是否有超过超时的包，并且如果仍有待处理的包，则重新安排自身到下一个适当的时间点。

如果重置器检测到超时，包将要么被重新提交，如果它还有剩余的尝试次数；要么以`-ETIMEDOUT`的状态完成，如果没有剩余的尝试次数。需要注意的是，这里的重新提交（由接收到NAK触发的情况也一样）意味着包会被添加回队列，其尝试次数现在递增，从而获得更高的优先级。包的超时将在下一次传输尝试之前被禁用，并且包仍然保留在待定集合中。

需要注意的是，由于传输和包确认超时的存在，包传输层总是可以保证进度，即使只是通过让包超时，永远不会完全阻塞。

并发和锁定
----------------
包传输层中有两个主要的锁：一个保护对包队列的访问，另一个保护对待定集合的访问。这些集合只能在各自锁的保护下被访问和修改。如果需要同时访问这两个集合，必须先获取待定锁，然后再获取队列锁，以避免死锁的发生。
除了保护这些集合外，在初始数据包提交后，某些数据包字段只能在特定锁的保护下访问。具体来说，数据包优先级必须仅在持有队列锁时访问，而数据包时间戳则必须仅在持有待处理锁时访问。
数据包传输层的其他部分独立受到保护。状态标志通过原子位操作进行管理，必要时使用内存屏障。对超时清理工作项和过期日期的修改由它们自身的锁保护。
数据包与数据包传输层（`ptl`）之间的引用比较特殊。它要么在上层请求提交时设置，要么如果不存在这样的请求，则在数据包首次提交时设置。一旦设置，其值就不会改变。可能与提交并发运行的函数（例如取消操作）不能依赖于`ptl`引用已被设置。在这种函数中访问`ptl`由`READ_ONCE()`保护，而设置`ptl`则为了对称性同样使用`WRITE_ONCE()`保护。
某些数据包字段可以在不被相应锁保护的情况下读取，特别是优先级和状态用于追踪目的。在这些情况下，适当的访问是通过使用`WRITE_ONCE()`和`READ_ONCE()`来确保的。这种只读访问只允许在陈旧值不关键的情况下进行。
就高层接口而言，数据包提交（|ssh_ptl_submit|）、数据包取消（|ssh_ptl_cancel|）、数据接收（|ssh_ptl_rx_rcvbuf|）以及层关闭（|ssh_ptl_shutdown|）始终可以相互并发执行。需要注意的是，对于同一个数据包，数据包提交不能与自身并发运行。
同样地，关闭和数据接收也不能与自身并发运行（但可以相互并发运行）。

请求传输层
===========

请求传输层通过|ssh_rtl|表示，并基于数据包传输层之上。它处理请求，即主机发送的包含|ssh_command|作为帧负载的SSH数据包。这一层将对请求的响应与事件区分开，后者也是通过|ssh_command|负载由EC发送的。虽然响应在此层中处理，但事件通过相应的回调传递给更高一层，即控制器层。请求传输层围绕以下核心概念构建：

请求
----

请求是带有命令类型负载的数据包，从主机发送到EC以查询数据或触发其上的动作（或两者同时进行）。它们由|ssh_request|表示，该结构封装了底层的|ssh_packet|，其中存储消息数据（即带有命令负载的SSH帧）。需要注意的是所有顶级表示形式（如|ssam_request_sync|）都是基于这个结构构建的。
由于|ssh_request|扩展自|ssh_packet|，因此它的生命周期也由数据包结构内的引用计数器管理（可通过|ssh_request_get|和|ssh_request_put|访问）。一旦计数器归零，请求的|ssh_request_ops|引用中的“释放（release）”回调将被调用。
请求可能有一个可选的响应，该响应同样通过带有命令类型负载的SSH消息（从EC到主机）发送。构造请求的一方需要知道是否期望有响应，并在提供给|ssh_request_init|的请求标志中标记这一点，以便请求传输层能够等待此响应。
与 `ssh_packet` 类似，`ssh_request` 也通过其请求操作引用提供了一个 `complete()` 回调函数，并保证在释放之前完成该回调。一旦通过 `ssh_rtl_submit` 提交至请求传输层，就会确保这一点。对于没有响应的请求，一旦底层数据包被数据包传输层成功发送（即在数据包完成回调中），则认为成功完成。对于有响应的请求，一旦收到响应并通过请求ID匹配到请求（这发生在接收线程上运行的数据包层数据接收回调中），则认为成功完成。如果请求以错误完成，则状态值将设置为相应的（负数）errno 值。

请求的状态同样通过其 `state` 标志 (`ssh_request_flags`) 进行管理，这些标志还编码了请求类型。特别是，以下位值得注意：

* `SSH_REQUEST_SF_LOCKED_BIT`: 当即将完成（无论因错误还是成功）时设置此位。它表明不应再获取更多请求引用，并且应尽快丢弃任何现有引用。设置此位的过程负责从请求队列和待处理集中移除对此请求的所有引用。
* `SSH_REQUEST_SF_COMPLETED_BIT`: 此位由运行 `complete()` 回调的过程设置，并用于确保此回调仅运行一次。
* `SSH_REQUEST_SF_QUEUED_BIT`: 请求排队时设置此位，在出队时清除。
* `SSH_REQUEST_SF_PENDING_BIT`: 添加请求到待处理集时设置此位，在从待处理集中移除时清除。

### 请求队列

请求队列是请求传输层中的两个基本集合之一。与数据包传输层的数据包队列不同，它不是一个优先级队列，而是遵循简单的先来先服务原则。

所有要通过请求传输层发送的请求都必须通过 `ssh_rtl_submit` 提交到这个队列。提交后，请求不得重新提交，并且超时时也不会自动重新提交。相反，请求将以超时错误完成。如果需要，调用者可以创建并提交一个新的请求进行重试，但不应再次提交相同的请求。

### 待处理集

待处理集是请求传输层中的另一个基本集合。该集合存储所有待处理请求的引用，即等待来自EC的响应的请求（类似于数据包传输层的数据包待处理集所做的事情）。

### 发送任务

当有新的请求可供发送时，调度发送任务。该任务检查请求队列中的下一个请求是否可以发送，如果可以，则将其底层数据包提交给数据包传输层。这一检查确保同时只能有一有限数量的请求处于待处理状态，即正在等待响应。如果请求需要响应，在提交其数据包之前，将该请求添加到待处理集中。
### 数据包完成回调

数据包完成回调在请求的基础数据包完成后执行一次。如果出现错误完成，对应的请求将使用此回调中提供的错误值完成。
对于成功完成的数据包，后续处理取决于请求本身：
- 如果请求期望接收响应，则将其标记为已发送，并启动请求超时。
- 如果请求不期望接收响应，则直接以成功状态完成。

### 数据接收回调

数据接收回调用于通知请求传输层有关底层数据包传输层通过数据类型帧接收到的数据。
通常，这预期为命令类型的负载。
- 如果命令的请求ID属于为事件预留的请求ID（从1到`SSH_NUM_EVENTS`，包括两端），则将其转发至请求传输层中注册的事件回调。
- 如果请求ID指示了对某个请求的响应，则查找待处理集合中的相应请求，如果找到且被标记为已发送，则以成功状态完成该请求。

### 超时回收器

请求-响应超时是针对期望接收响应的请求设置的单个请求超时。它用于确保请求不会无限期地等待EC的响应，在基础数据包成功完成后启动。
这个超时类似于数据包传输层上的数据包确认超时，由一个专门的回收任务处理。该任务本质上是一个工作项，当下一个请求即将超时时重新安排运行。然后，该工作项会扫描待处理请求集合，查找已超时的请求，并以`-ETIMEDOUT`作为状态完成这些请求。请求不会自动重新提交。相反，请求的发起者如果需要的话必须构造并提交一个新的请求。
请注意，结合数据包传输和确认超时，该超时保证了请求层始终能够向前推进，即使只是通过数据包超时的方式，而不会完全阻塞。

### 并发与锁定

与数据包传输层类似，请求传输层有两个主要锁：一个保护对请求队列的访问，另一个保护对待处理集合的访问。这些集合只能在其各自的锁下进行访问和修改。
请求传输层的其他部分独立受保护。状态标志（再次）通过原子位操作管理，必要时辅以内存屏障。对超时回收器工作项及其到期日期的修改由其自身的锁保护。
一些请求字段可能在未加锁的情况下被读取，特别是用于追踪的状态字段。在这种情况下，通过使用`WRITE_ONCE()`和`READ_ONCE()`确保了正确的访问。这种只读访问仅在陈旧值不关键的情况下才是允许的。

关于高层接口，请求提交（`|ssh_rtl_submit|`）、请求取消（`|ssh_rtl_cancel|`）以及层关闭（`|ssh_rtl_shutdown|`）都可以相互并发执行。需要注意的是，对于同一个请求，请求提交不能与自身并发运行（并且每个请求只能调用一次）。同样地，关闭操作也不能与自身并发运行。

### 控制器层

控制器层基于请求传输层之上，为客户端驱动提供易于使用的接口。它由`|ssam_controller|`和SSH驱动表示。虽然较低级别的传输层负责传输和处理数据包及请求，但控制器层更多承担管理角色。具体而言，它处理设备初始化、电源管理和事件处理，包括通过完成系统（`|ssam_cplt|`）进行的事件传递和注册。

### 事件注册

通常，一个事件（或者说一类事件）必须由主机明确请求后，EC才会发送该事件（HID输入事件似乎是例外）。这是通过事件启用请求实现的（类似地，一旦不再需要，应该通过事件禁用请求来禁用事件）。
用于启用（或禁用）事件的具体请求是通过事件注册表给出的，即这个事件（可以说）的管辖机构，由`|ssam_event_registry|`表示。作为此请求的参数，需要提供目标类别，以及根据事件注册表的不同，还需要提供事件的实例ID。如果注册表不使用实例ID，则此（可选）实例ID必须为零。目标类别和实例ID共同构成事件ID，由`|ssam_event_id|`表示。简而言之，事件注册表和事件ID都是必需的，以唯一标识某一类事件。

需要注意的是，启用事件的请求还必须提供一个额外的*请求ID*参数。此参数不影响所启用事件类别的内容，而是将作为EC发送的此类别中每个事件的请求ID（RQID）。它用于识别事件（因为有限数量的请求ID被预留用于事件中，特别是一到`SSH_NUM_EVENTS`之间），也用于将事件映射到其特定类别。目前，控制器总是将此参数设置为目标类别，该类别在`|ssam_event_id|`中指定。

由于多个客户端驱动可能依赖于相同的（或重叠的）事件类别，并且启用/禁用调用严格是二进制的（即开/关），因此控制器必须管理对这些事件的访问。它是通过引用计数来实现的，在一个基于RB树的映射中存储计数器，其中事件注册表和ID作为键（没有已知的有效事件注册表和事件ID组合列表）。请参阅`|ssam_nf|`、`|ssam_nf_refcount_inc|`和`|ssam_nf_refcount_dec|`了解详情。

这种管理与通知器注册一起通过顶级函数`|ssam_notifier_register|`和`|ssam_notifier_unregister|`实现。

### 事件传递

为了接收事件，客户端驱动必须通过`|ssam_notifier_register|`注册一个事件通知器。这会增加特定事件类别的引用计数（如上一节所述），在EC上启用该类别（如果尚未启用的话），并安装提供的通知器回调。

通知器回调存储在列表中，每个目标类别都有一个（RCU）列表（通过事件ID提供；注意：已知的目标类别数量是固定的）。除了通过事件ID给出的目标类别和实例ID外，没有已知的从事件注册表和事件ID的组合到事件类可以提供的命令数据（目标ID、目标类别、命令ID和实例ID）之间的关联。
请注意，由于通知器的存储方式（或者说必须以这种方式存储），客户端驱动程序可能会接收到它们未请求的事件，并需要处理这些事件。具体来说，默认情况下，它们将接收到同一目标类别的所有事件。为了简化处理这个问题，可以在注册通知器时请求通过目标ID（通过事件注册表提供）和实例ID（通过事件ID提供）对事件进行过滤。这种过滤会在执行通知器时遍历通知器的过程中应用。

所有通知器回调都在一个专用的工作队列上执行，即所谓的完成工作队列。当通过在请求层安装的回调接收到事件（运行在数据包传输层的接收线程上）后，该事件会被放入相应的事件队列（`|ssam_event_queue|`）。从这个事件队列中，该队列的完成工作项（运行在完成工作队列上）将获取事件并执行通知器回调。这样做是为了避免在接收线程上阻塞。

每个目标ID和目标类别的组合都有一个事件队列。这是为了确保对于相同的目标ID和目标类别的事件，通知器回调按顺序执行。不同目标ID和目标类别组合的事件可以并行执行回调。

### 并发与锁定
-----------------------

控制器的大多数并发相关的安全保证是由低级别的请求传输层提供的。除此之外，事件的注册与注销由其自身的锁保护。
对控制器状态的访问由状态锁保护。这个锁是一个读写信号量。读取部分可以用来确保状态在执行依赖于状态保持不变的函数（例如`|ssam_notifier_register|`、`|ssam_notifier_unregister|`、`|ssam_request_sync_submit|`及其衍生函数）期间不会改变，并且如果这些保证不是通过其他方式（例如通过`|ssam_client_bind|`或`|ssam_client_link|`）已经提供的，则使用此锁。写入部分保护任何会改变状态的转换，例如初始化、销毁、挂起和恢复。

控制器状态可以在状态锁之外被只读访问，用于检查是否发生了无效API使用（例如，在`|ssam_request_sync_submit|`中）。请注意，这样的检查并非旨在（也不会）防止所有无效使用情况，而是旨在帮助捕捉这些问题。在这种情况下，通过使用`WRITE_ONCE()`和`READ_ONCE()`来确保适当的变量访问。

假设关于状态不改变的前提条件已满足，所有非初始化和非关闭功能可以相互并发运行。这包括`|ssam_notifier_register|`、`|ssam_notifier_unregister|`、`|ssam_request_sync_submit|`以及基于这些功能的所有其他功能。
