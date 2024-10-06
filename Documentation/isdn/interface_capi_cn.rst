=========================================
内核CAPI接口到硬件驱动程序
=========================================

1. 概览
===========

根据CAPI 2.0规范：
COMMON-ISDN-API（CAPI）是一种应用程序编程接口标准，用于访问连接到基本速率接口（BRI）和主速率接口（PRI）的ISDN设备。
内核CAPI作为CAPI应用程序与CAPI硬件驱动程序之间的调度层。硬件驱动程序通过注册ISDN设备（在CAPI术语中称为控制器）到内核CAPI，表明它们已准备好为CAPI应用程序提供服务。CAPI应用程序也需向内核CAPI注册，并请求与某个CAPI设备关联。内核CAPI随后将应用程序注册分派给一个可用设备，并转发给相应的硬件驱动程序。内核CAPI负责在应用程序和硬件驱动程序之间双向转发CAPI消息。
CAPI消息的格式和语义在CAPI 2.0标准中有详细规定。
该标准可从https://www.capi.org免费获取。

2. 驱动程序和设备注册
========================

CAPI驱动程序必须通过调用内核CAPI函数attach_capi_ctr()并传入指向struct capi_ctr的指针来注册其控制的每个ISDN设备到内核CAPI，才能使用这些设备。此结构体必须包含驱动程序和控制器的名称以及一些回调函数指针，内核CAPI会使用这些指针与驱动程序通信。可以通过调用detach_capi_ctr()函数并传入相同的struct capi_ctr指针来撤销注册。
在设备实际可用之前，驱动程序必须填写设备信息字段'manu'、'version'、'profile'和'serial'，并通过调用capi_ctr_ready()信号表明设备已准备好。
如果设备因任何原因变得不可用（关机、断开连接等），驱动程序需要调用capi_ctr_down()。这将阻止内核CAPI进一步调用回调函数。

3. 应用程序注册与通信
============================

内核CAPI通过调用硬件驱动程序的register_appl()回调函数将应用程序的注册请求（对CAPI操作CAPI_REGISTER的调用）转发给适当的硬件驱动程序。内核CAPI会分配一个唯一的应用程序ID（ApplID，u16）并连同应用程序提供的参数结构一起传递给register_appl()。这类似于对普通文件或字符设备执行的open()操作。
在成功返回register_appl()之后，应用程序可以通过调用send_message()回调函数将CAPI消息传递给设备的驱动程序。相反地，驱动程序可以调用内核CAPI的capi_ctr_handle_message()函数，将接收到的CAPI消息传递给内核CAPI以转发给应用程序，并指定其ApplID。
取消注册请求（CAPI 操作 CAPI_RELEASE）从应用程序转发为对 release_appl() 回调函数的调用，传递与 register_appl() 相同的 ApplID。在从 release_appl() 返回后，将不再为该应用程序传递任何 CAPI 消息。

4. 数据结构
===========

4.1 结构体 struct capi_driver
------------------------------

此结构体描述了一个内核 CAPI 驱动程序本身。它用于 register_capi_driver() 和 unregister_capi_driver() 函数中，并包含以下非私有字段，所有这些字段都应在调用 register_capi_driver() 之前由驱动程序设置：

``char name[32]``
	驱动程序名称，作为以零结尾的 ASCII 字符串
``char revision[32]``
	驱动程序版本号，作为以零结尾的 ASCII 字符串

4.2 结构体 struct capi_ctr
------------------------------

此结构体描述了由内核 CAPI 驱动程序处理的一个 ISDN 设备（控制器）。通过 attach_capi_ctr() 函数注册后，它会被传递给所有特定控制器的下层接口和回调函数，以标识要操作的控制器。
它包含以下非私有字段：

要由驱动程序在调用 attach_capi_ctr() 之前设置：
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``struct module *owner``
	指向拥有设备的驱动模块的指针

``void *driverdata``
	指向驱动程序特定数据的不透明指针，内核 CAPI 不会触及

``char name[32]``
	控制器名称，作为以零结尾的 ASCII 字符串

``char *driver_name``
	驱动程序名称，作为以零结尾的 ASCII 字符串

``int (*load_firmware)(struct capi_ctr *ctrlr, capiloaddata *ldata)``
	（可选）指向一个回调函数的指针，用于向设备发送固件和配置数据

	函数可以在操作完成前返回
	完成必须通过调用 capi_ctr_ready() 来信号通知
	返回值：成功时返回 0，出错时返回错误代码
	在进程上下文中调用
``void (*reset_ctr)(struct capi_ctr *ctrlr)``
	（可选）指向一个回调函数的指针，用于停止设备并释放所有已注册的应用程序

	函数可以在操作完成前返回
	完成必须通过调用 capi_ctr_down() 来信号通知
	在进程上下文中调用
``void (*register_appl)(struct capi_ctr *ctrlr, u16 applid, capi_register_params *rparam)``
	指向回调函数的指针，用于向设备注册应用程序

	内核 CAPI 对这些函数的调用进行了序列化，以确保任何时候只有一个这样的调用是活动的
``void (*release_appl)(struct capi_ctr *ctrlr, u16 applid)``
	指向回调函数的指针，用于向设备取消注册应用程序

	内核 CAPI 对这些函数的调用进行了序列化，以确保任何时候只有一个这样的调用是活动的
```u16  (*send_message)(struct capi_ctr *ctrlr, struct sk_buff *skb)```
指向一个回调函数，用于向设备发送 CAPI 消息。

返回值：CAPI 错误代码

如果该方法返回 0（CAPI_NOERROR），则驱动程序已接管 skb，调用者不再能够访问它。如果返回非零（错误）值，则 skb 的所有权返回给调用者，调用者可以重新使用或释放它。
返回值仅用于指示在接收或排队消息时出现的问题。在实际处理消息期间发生的错误应通过适当的回复消息来指示。
可以在进程上下文或中断上下文中调用此函数。
此函数调用不由内核 CAPI 序列化，即必须准备好被重新进入。

```char *(*procinfo)(struct capi_ctr *ctrlr)```
指向一个回调函数，返回设备在 CAPI 控制器信息表中的条目，/proc/capi/controller。

注意：
除 send_message() 外的回调函数永远不会在中断上下文中调用。
在调用 capi_ctr_ready() 之前需要填写以下内容：

```
u8 manu[CAPI_MANUFACTURER_LEN]
```
返回值为 CAPI_GET_MANUFACTURER。

```
capi_version version
```
返回值为 CAPI_GET_VERSION。

```
capi_profile profile
```
返回值为 CAPI_GET_PROFILE。

```
u8 serial[CAPI_SERIAL_LEN]
```
返回值为 CAPI_GET_SERIAL。

### 4.3 SKBs

CAPI 消息通过 send_message() 和 capi_ctr_handle_message() 在内核 CAPI 和驱动程序之间传递，存储在套接字缓冲区（skb）的数据部分中。每个 skb 包含一个根据 CAPI 2.0 标准编码的 CAPI 消息。
对于数据传输消息 DATA_B3_REQ 和 DATA_B3_IND，实际的有效负载数据紧随 CAPI 消息本身之后在同一 skb 中。
Data 和 Data64 参数不用于处理。可以通过将 CAPI 消息的长度字段设置为 22 而不是 30 来省略 Data64 参数。

### 4.4 _cmsg 结构体
-----------------------

（在 <linux/isdn/capiutil.h> 中声明）

_cmsg 结构体以易于访问的形式存储 CAPI 2.0 消息的内容。它包含所有可能的 CAPI 2.0 参数成员，包括 Additional Info 和 B Protocol 结构参数的子参数，但以下情况除外：

* 第二个呼叫方号码（CONNECT_IND）

* Data64（DATA_B3_REQ 和 DATA_B3_IND）

* 发送完成（Additional Info 的子参数，CONNECT_REQ 和 INFO_REQ）

* 全局配置（B Protocol 的子参数，CONNECT_REQ、CONNECT_RESP 和 SELECT_B_PROTOCOL_REQ）

只有当前正在处理的消息类型中出现的参数才实际使用。未使用的成员应设置为零。
成员名称与其代表的 CAPI 2.0 标准参数名称相同。请参阅 <linux/isdn/capiutil.h> 获取确切的拼写。成员数据类型如下：

=========== =================================================================
u8          对于类型为 'byte' 的 CAPI 参数

u16         对于类型为 'word' 的 CAPI 参数

u32         对于类型为 'dword' 的 CAPI 参数

_cstruct    对于类型为 'struct' 的 CAPI 参数
            成员是指向包含 CAPI 编码参数（长度 + 内容）的缓冲区的指针。也可以是 NULL，这表示空（长度为零）参数
```
子参数以编码形式存储在内容部分中。
_cmstruct 是 CAPI 类型为 'struct' 的参数的另一种表示形式（仅用于 'Additional Info' 和 'B Protocol' 参数）。
该表示形式是一个字节，包含以下值之一：
CAPI_DEFAULT：参数为空/不存在
CAPI_COMPOSE：参数存在
子参数值分别存储在相应的 _cmsg 结构成员中。

========== =================================================================

5. 下层接口函数
==================

::

  int attach_capi_ctr(struct capi_ctr *ctrlr)
  int detach_capi_ctr(struct capi_ctr *ctrlr)

向内核 CAPI 注册/注销一个设备（控制器）

::

  void capi_ctr_ready(struct capi_ctr *ctrlr)
  void capi_ctr_down(struct capi_ctr *ctrlr)

指示控制器准备好/未准备好

::

  void capi_ctr_handle_message(struct capi_ctr * ctrlr, u16 applid,
			       struct sk_buff *skb)

将接收到的 CAPI 消息传递给内核 CAPI，以便转发到指定的应用程序

6. 辅助函数和宏
====================

从 CAPI 消息头中提取/设置元素值的宏（来自 <linux/isdn/capiutil.h>）：

======================  =============================   ====================
获取宏		设置宏			元素（类型）
======================  =============================   ====================
CAPIMSG_LEN(m)		CAPIMSG_SETLEN(m, len)		总长度（u16）
CAPIMSG_APPID(m)	CAPIMSG_SETAPPID(m, applid)	应用ID（u16）
CAPIMSG_COMMAND(m)	CAPIMSG_SETCOMMAND(m,cmd)	命令（u8）
CAPIMSG_SUBCOMMAND(m)	CAPIMSG_SETSUBCOMMAND(m, cmd)	子命令（u8）
CAPIMSG_CMD(m)		-				命令 * 256 + 子命令（u16）
CAPIMSG_MSGID(m)	CAPIMSG_SETMSGID(m, msgid)	消息编号（u16）

CAPIMSG_CONTROL(m)	CAPIMSG_SETCONTROL(m, contr)	控制器/PLCI/NCCI（u32）
CAPIMSG_DATALEN(m)	CAPIMSG_SETDATALEN(m, len)	数据长度（u16）
======================  =============================   ====================

处理 _cmsg 结构的库函数（来自 <linux/isdn/capiutil.h>）：

``char *capi_cmd2str(u8 Command, u8 Subcommand)``
返回与给定命令和子命令值对应的 CAPI 2.0 消息名称，作为静态 ASCII 字符串。如果命令/子命令不是 CAPI 2.0 标准定义的一部分，则返回值可能为 NULL。

7. 调试
=========

内核模块 kernelcapi 有一个模块参数 showcapimsgs 来控制模块生成的一些调试输出。这个参数只能在加载模块时通过参数 "showcapimsgs=<n>" 设置，可以是在命令行上或配置文件中使用 modprobe 命令时指定的。
如果 showcapimsgs 的最低位被设置，则 kernelcapi 记录控制器和应用程序的上下事件。
此外，每个注册的 CAPI 控制器都有一个关联的 traceflag 参数来控制如何记录发送到和从控制器发出的 CAPI 消息。当控制器注册时，traceflag 参数初始化为 showcapimsgs 参数的值，但可以通过 MANUFACTURER_REQ 命令 KCAPI_CMD_TRACE 更改。
如果 traceflag 的值非零，则记录 CAPI 消息。
只有当 traceflag 的值大于 2 时，才会记录 DATA_B3 消息。
如果 traceflag 的最低位被设置，仅记录命令/子命令和消息长度。否则，kernelcapi 会记录整个消息的可读表示形式。
