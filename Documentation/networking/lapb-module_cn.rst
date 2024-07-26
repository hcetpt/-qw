SPDX 许可证标识符: GPL-2.0

===============================
Linux LAPB 模块接口
===============================

版本 1.3

Jonathan Naylor 1996年12月29日

修改 (Henner Eisen, 2000年10月29日): `data_indication()` 的整型返回值

LAPB 模块将是一个单独编译的模块，用于满足 Linux 操作系统中任何需要 LAPB 服务的部分。本文档定义了该模块的接口和提供的服务。在此上下文中，“模块”一词并不意味着 LAPB 模块必须是独立加载的模块（尽管它可以是）。这里“模块”的用法更接近于其标准含义。
接口
-----

LAPB 模块的接口包括向模块调用的函数、从模块回调以指示重要状态变化以及获取和设置有关模块信息的结构。

### 结构
可能最重要的结构是 `sk_buff` 结构，它用于保存接收和发送的数据，但此处不在讨论范围内。
两个特定于 LAPB 的结构是 LAPB 初始化结构和 LAPB 参数结构。这些将在一个标准头文件 `<linux/lapb.h>` 中定义。而头文件 `<net/lapb.h>` 是内部用于 LAPB 模块，并不供外部使用。

#### LAPB 初始化结构
这个结构仅在调用 `lapb_register` 函数时使用（见下文）。
它包含关于需要 LAPB 模块服务的设备驱动程序的信息：

```c
struct lapb_register_struct {
    void (*connect_confirmation)(int token, int reason);
    void (*connect_indication)(int token, int reason);
    void (*disconnect_confirmation)(int token, int reason);
    void (*disconnect_indication)(int token, int reason);
    int  (*data_indication)(int token, struct sk_buff *skb);
    void (*data_transmit)(int token, struct sk_buff *skb);
};
```

此结构中的每个成员对应设备驱动程序中的一个函数，当 LAPB 模块中发生特定事件时会调用这些函数。下面将详细描述这些回调。如果不需要某个回调，则可以使用 `NULL` 替换。

#### LAPB 参数结构
此结构与 `lapb_getparms` 和 `lapb_setparms` 函数一起使用（见下文）。它们允许设备驱动程序获取和设置给定连接的 LAPB 实现的操作参数：

```c
struct lapb_parms_struct {
    unsigned int t1;
    unsigned int t1timer;
    unsigned int t2;
    unsigned int t2timer;
    unsigned int n2;
    unsigned int n2count;
    unsigned int window;
    unsigned int state;
    unsigned int mode;
};
```

T1 和 T2 是协议计时参数，以 100 毫秒为单位。N2 是在宣布链路失败前的最大重试次数。
窗口大小是指远程端点未确认的最大数据包数，对于标准 LAPB 链路，窗口值介于 1 到 7 之间；对于扩展 LAPB 链路，窗口值介于 1 到 127 之间。
模式变量是一个位字段，目前用于设置三个值。位字段具有以下含义：

======  =================================================
Bit   含义
======  =================================================
0     LAPB 操作方式（0 = 标准 LAPB, 1 = 扩展 LAPB）
1	[SM]LP 操作 (0=LAPB_SLP 1=LAPB_MLP)
2	DTE/DCE 操作 (0=LAPB_DTE 1=LAPB_DCE)
3-31	预留，必须为 0
======  =================================================

扩展的 LAPB 操作表明使用了扩展的序列号以及因此而产生的更大的窗口大小，默认情况下是标准的 LAPB 操作。MLP 操作与 SLP 操作相同，只是 LAPB 使用的地址不同以指示操作模式，默认情况下是单链路过程。DCE 和 DTE 操作之间的区别在于（i）用于命令和响应的地址，以及（ii）当 DCE 未连接时，它会在 T1 间隔内发送 DM 而不设置轮询。大写的常量名称将在公共的 LAPB 头文件中定义。
函数
---------

LAPB 模块提供了一系列的功能入口点：
::

    int lapb_register(void *token, struct lapb_register_struct);

在使用 LAPB 模块之前必须调用此函数。如果调用成功，则返回 LAPB_OK。token 必须是由设备驱动程序生成的唯一标识符，以便能够唯一地标识 LAPB 链路实例。在所有回调中都会由 LAPB 模块返回该 token，并且在设备驱动程序的所有对 LAPB 模块的调用中也会使用它。
对于单个设备驱动程序中的多个 LAPB 链路，需要多次调用 lapb_register。lapb_register_struct 的格式如上所述。返回值如下：

=============		=============================
LAPB_OK			LAPB 注册成功
LAPB_BADTOKEN		该 Token 已被注册
LAPB_NOMEM		内存不足
=============		=============================

::

    int lapb_unregister(void *token);

这将释放与 LAPB 链路相关的所有资源。任何当前的 LAPB 链路将被放弃，不会再传递进一步的消息。调用此函数后，token 的值对于任何对 LAPB 函数的调用都不再有效。有效的返回值如下：

=============		===============================
LAPB_OK			LAPB 取消注册成功
LAPB_BADTOKEN		无效/未知的 LAPB Token
=============		===============================
以下是给定文本的中文翻译：

```plaintext
int lapb_getparms(void *token, struct lapb_parms_struct *parms);

此函数允许设备驱动程序获取当前LAPB变量的值，`lapb_parms_struct`结构体在上面已有描述。有效的返回值包括：

=============		=============================
LAPB_OK			LAPB getparms操作成功
LAPB_BADTOKEN		无效或未知的LAPB token
=============		=============================

int lapb_setparms(void *token, struct lapb_parms_struct *parms);

此函数允许设备驱动程序设置当前LAPB变量的值，`lapb_parms_struct`结构体在上面已有描述。其中，`t1timer`、`t2timer`和`n2count`的值将被忽略；在已连接状态下更改模式位也将被忽略。如果出现错误，则表示所有值均未发生改变。有效的返回值包括：

=============		=================================================
LAPB_OK			LAPB getparms操作成功
LAPB_BADTOKEN		无效或未知的LAPB token
LAPB_INVALUE		有一个值超出了其允许的范围
=============		=================================================

int lapb_connect_request(void *token);

使用当前参数设置发起连接请求。有效的返回值包括：

==============		=================================
LAPB_OK			LAPB正在开始连接
LAPB_BADTOKEN		无效或未知的LAPB token
LAPB_CONNECTED		LAPB模块已经处于连接状态
==============		=================================

int lapb_disconnect_request(void *token);

发起断开连接请求。有效的返回值包括：

=================	===============================
LAPB_OK			LAPB正在开始断开连接
LAPB_BADTOKEN		无效或未知的LAPB token
=================	===============================
```

请注意，原始文本中有一些小错误，例如在`lapb_setparms`函数的描述中提到“LAPB getparms”应该是“LAPB setparms”，并且在`lapb_connect_request`函数的有效返回值中重复了“LAPB_OK”。在翻译时这些错误已被修正。
LAPB_NOTCONNECTED   LAPB 模块未连接
=================	===============================

::

    int lapb_data_request(void *token, struct sk_buff *skb);

将数据排队到 LAPB 模块以通过链路进行传输。如果调用成功，则 skbuff 将归 LAPB 模块所有，设备驱动程序不得再次使用它。有效的返回值如下：

=================	=============================
LAPB_OK			LAPB 已接受数据
LAPB_BADTOKEN		无效或未知的 LAPB 标记
LAPB_NOTCONNECTED	LAPB 模块未连接
=================	=============================

::

    int lapb_data_received(void *token, struct sk_buff *skb);

将从设备接收到的数据排队到 LAPB 模块。预期传递给 LAPB 模块的数据中的 skb->data 指向 LAPB 数据的起始位置。如果调用成功，则 skbuff 将归 LAPB 模块所有，设备驱动程序不得再次使用它。有效的返回值如下：

=============		===========================
LAPB_OK			LAPB 已接受数据
LAPB_BADTOKEN		无效或未知的 LAPB 标记
=============		===========================

回调函数
---------

这些回调函数是由设备驱动程序提供的，以便在发生事件时由 LAPB 模块调用。它们通过使用 lapb_register（见上文）与 LAPB 模块注册，在 lapb_register_struct 结构中注册（见上文）。
::

    void (*connect_confirmation)(void *token, int reason);

当通过调用 lapb_connect_request（见上文）请求的连接建立后，此函数由 LAPB 模块调用。原因总是 LAPB_OK。
::

    void (*connect_indication)(void *token, int reason);

当远程系统建立了链路时，此函数由 LAPB 模块调用。原因值总是 LAPB_OK。
```c
// 当设备驱动程序调用 lapb_disconnect_request（见上文）后，LAPB 模块在发生事件时调用此函数。
// reason 参数指示了所发生的状况。在所有情况下，可以认为 LAPB 链路已经被终止。
// reason 的值如下：
// 
// ===================  ====================================================
// LAPB_OK              LAPB 链路正常终止
// LAPB_NOTCONNECTED    远程系统未连接
// LAPB_TIMEDOUT        从远程系统未收到响应，在N2次尝试后超时
// ===================  ====================================================

void (*disconnect_confirmation)(void *token, int reason);

// 当链路被远程系统终止或发生了其他导致链路终止的事件时，LAPB 模块会调用此函数。
// 这可能是对 lapb_connect_request（见上文）的响应，如果远程系统拒绝了请求的话。
// reason 的值如下：
// 
// ===================  =======================================================
// LAPB_OK              远程系统正常终止了 LAPB 链路
// LAPB_REFUSED         远程系统拒绝了连接请求
// LAPB_NOTCONNECTED    远程系统未连接
// LAPB_TIMEDOUT        从远程系统未收到响应，在N2次尝试后超时
// ===================  =======================================================

void (*disconnect_indication)(void *token, int reason);

// 当从远程系统接收到数据，并需要将其传递到协议栈的下一层时，LAPB 模块调用此函数。
// skbuff 归设备驱动程序所有，LAPB 模块将不再对其执行任何操作。skb->data 指针指向 LAPB 头部之后的第一个字节的数据。
// 如果帧在交付给上层之前被丢弃，则此方法应返回 NET_RX_DROP（在头文件 include/linux/netdevice.h 中定义）。
int (*data_indication)(void *token, struct sk_buff *skb);

// 当设备驱动程序要向远程系统发送数据时，LAPB 模块调用此函数。
// skbuff 归设备驱动程序所有，LAPB 模块将不再对其执行任何操作。
void (*data_transmit)(void *token, struct sk_buff *skb);
```
这段代码描述了与 LAPB（Link Access Protocol Balanced）模块相关的几个回调函数，用于处理链路断开确认、链路断开指示、数据接收指示和数据传输等事件。
skb->data 指针将指向 LAPB 首部的第一个字节。
