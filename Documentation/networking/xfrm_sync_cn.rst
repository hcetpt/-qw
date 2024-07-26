SPDX 许可证标识符: GPL-2.0

====
XFRM
====

同步补丁的工作基于 Krisztian <hidden@balabit.hu> 及其他人的初始补丁，以及 Jamal <hadi@cyberus.ca> 提供的额外补丁。
同步的目标是能够插入属性并生成事件，以便安全关联（SA）能够在不同机器间安全地迁移，以满足高可用性（HA）需求。
想法是同步安全关联，使得接管机器如果能够访问到这些信息，则能尽可能准确地处理这些安全关联。
我们已经具备了生成安全关联添加/删除/更新事件的能力。
这些补丁增加了同步能力，并确保具有准确的生命字节计数（以确保安全关联的适当衰减）和重放计数器来避免在故障转移时发生重放攻击，同时尽量减少损失。
这样，备份成员可以尽可能保持与活动成员同步。
由于上述各项指标会随着每个接收到的数据包而变化，
可能会产生大量的事件。
为此，我们也增加了一个类似 Nagle 的算法来限制事件的数量。也就是说，我们将设置阈值，例如“如果达到重放序列阈值或者过了10秒，请通知我”。
这些阈值可以通过系统范围内的 sysctl 设置，也可以针对每个安全关联进行更新。
需要同步的项目包括：
- 生命字节计数器
注意：如果假设故障转移机器是预先已知的，则生命时间限制并不重要，因为时间倒计时的衰减不是由数据包到达驱动的。
- 进入和出站方向的重放序列号

1) 消息结构
----------------------
nlmsghdr: aevent_id: 可选-TLVs
净链接消息类型如下：

XFRM_MSG_NEWAE 和 XFRM_MSG_GETAE
XFRM_MSG_GETAE 消息不包含 TLVs（类型长度值结构）
XFRM_MSG_NEWAE 消息至少包含两个 TLVs（如下进一步讨论）
aevent_id 结构看起来像这样：

```c
   struct xfrm_aevent_id {
	     struct xfrm_usersa_id           sa_id;
	     xfrm_address_t                  saddr;
	     __u32                           flags;
	     __u32                           reqid;
   };
```

唯一的安全关联（SA）通过 xfrm_usersa_id、reqid 和 saddr 的组合来标识。
flags 用于指示不同的含义。可能的标志包括：

- `XFRM_AE_RTHR=1`，/* 重播阈值 */
- `XFRM_AE_RVAL=2`，/* 重播值 */
- `XFRM_AE_LVAL=4`，/* 寿命值 */
- `XFRM_AE_ETHR=8`，/* 过期计时器阈值 */
- `XFRM_AE_CR=16`，/* 事件原因是重播更新 */
- `XFRM_AE_CE=32`，/* 事件原因是计时器过期 */
- `XFRM_AE_CU=64`，/* 事件原因是策略更新 */

这些标志如何使用取决于消息的方向（内核 <-> 用户空间）以及原因（配置、查询或事件）。下面在不同的消息中对此进行了描述。
进程 ID（pid）将在净链接中适当地设置以识别方向（0 表示到内核，从内核到用户空间时 pid 等于创建事件的进程 ID）

程序需要订阅多播组 XFRMNLGRP_AEVENTS 以接收这些事件的通知。
2) TLVs 反映了不同的参数：
-----------------------------------

a) 字节值 (XFRMA_LTIME_VAL)

此 TLV 携带自上次事件以来按字节寿命运行/当前的计数器。
b) 重播值 (XFRMA_REPLAY_VAL)

此 TLV 携带自上次事件以来按重播序列运行/当前的计数器。
c) 重播阈值 (XFRMA_REPLAY_THRESH)

此 TLV 携带内核用于触发事件的阈值，当超过重播序列时触发。
d) 过期定时器 (XFRMA_ETIMER_THRESH)

这是一个以毫秒为单位的定时器值，用作Nagle值来限制事件的发送速率。
3) 参数的默认配置：
-------------------------------

默认情况下，除非至少有一个监听器注册以监听多播组 XFRMNLGRP_AEVENTS，否则这些事件应被关闭。
安装安全关联 (SA) 的程序需要指定两个阈值。但是，为了不改变现有的应用程序（如 racoon），我们还提供了这些不同参数的默认阈值。
这两个系统控制 (sysctls)/proc 条目是：

a) /proc/sys/net/core/sysctl_xfrm_aevent_etime
用于提供 XFRMA_ETIMER_THRESH 的默认值，以 100 毫秒的时间增量单位表示。默认值为 10（即 1 秒）。

b) /proc/sys/net/core/sysctl_xfrm_aevent_rseqth
用于提供 XFRMA_REPLAY_THRESH 参数的默认值，以递增的数据包计数表示。默认值为两个数据包。
4) 消息类型：
----------------

a) XFRM_MSG_GETAE 由用户空间向内核发出
XFRM_MSG_GETAE 不携带任何 TLV（类型-长度-值）字段。
响应是一个格式化的 XFRM_MSG_NEWAE，其内容基于 XFRM_MSG_GETAE 请求的内容。
响应将始终包含 XFRMA_LTIME_VAL 和 XFRMA_REPLAY_VAL TLV 字段。
* 如果设置了 XFRM_AE_RTHR 标志，则还会检索 XFRMA_REPLAY_THRESH
* 如果设置了 XFRM_AE_ETHR 标志，则还会检索 XFRMA_ETIMER_THRESH

b) XFRM_MSG_NEWAE 可由用户空间发出进行配置，
   或由内核发出以宣布事件或响应 XFRM_MSG_GETAE
i) 用户空间 → 内核以配置特定的安全关联 (SA)
任何值或阈值参数都可以通过传递相应的TLV来进行更新。
处理完成后会向用户空间的发起者返回一个响应，指示操作成功或失败。
在成功的情况下，还会向所有监听者发送一个带有XFRM_MSG_NEWAE事件的通知，具体如iii)中所述。
ii) 从内核到用户空间的方向上作为对XFRM_MSG_GETAE请求的响应。

响应总会包含XFRMA_LTIME_VAL和XFRMA_REPLAY_VAL这两个TLV。
如果在XFRM_MSG_GETAE消息中明确请求了阈值TLV，则这些阈值TLV也会被包括进来。
iii) 当有人使用XFRM_MSG_NEWAE（如上述i)中所述）为安全关联设置任何值或阈值时，从内核到用户空间报告这一事件。
在这种情况下，将设置XFRM_AE_CU标志来告知用户该变更是因为更新而发生的。
消息总会包含XFRMA_LTIME_VAL和XFRMA_REPLAY_VAL这两个TLV。
iv) 当重放阈值或超时时间被超过时，从内核到用户空间报告这一事件。
在这种情况下，如果重放阈值被超过，则设置XFRM_AE_CR；如果发生超时，则设置XFRM_AE_CE，以此来告知用户发生了什么情况。
请注意，这两个标志是互斥的。
消息总会包含XFRMA_LTIME_VAL和XFRMA_REPLAY_VAL这两种类型的时间长度值（TLVs）。
阈值设置的例外情况
------------------------------

如果您有一个安全关联（SA），它遭受突发性的流量冲击，以至于在某个时间段内计时器阈值到期但没有看到任何数据包，则会出现以下奇怪的行为：
计时器到期后到达的第一个数据包将触发一个超时事件；也就是说，我们不会等待超时周期或达到数据包阈值。这样做是为了简化处理流程并提高效率。
- JHS
