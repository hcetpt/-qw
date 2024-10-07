SPDX 许可证标识符: GPL-2.0

===============================
Linux LAPB 模块接口
===============================

版本 1.3

Jonathan Naylor 1996年12月29日

修改（Henner Eisen，2000年10月29日）：data_indication() 的返回值类型为 int

LAPB 模块将是一个单独编译的模块，供任何需要 LAPB 服务的 Linux 操作系统部分使用。本文档定义了该模块的接口及其提供的服务。在此上下文中，“模块”一词并不意味着 LAPB 模块是单独加载的模块，尽管它可以是。此处使用的“模块”一词采用其更标准的含义。

接口
----

LAPB 模块的接口包括调用模块的函数、从模块回调以指示重要状态变化以及用于获取和设置模块信息的结构体。

结构体
------

最重要的结构体可能是用于存储接收和发送数据的 skbuff 结构体，但本文档不涉及此内容。
两个特定于 LAPB 的结构体是 LAPB 初始化结构体和 LAPB 参数结构体。这些将在标准头文件 `<linux/lapb.h>` 中定义。头文件 `<net/lapb.h>` 是 LAPB 模块内部使用的，不应被其他部分使用。

LAPB 初始化结构体
-------------------

此结构体仅在调用 lapb_register 时使用（见下文）。
它包含需要 LAPB 模块服务的设备驱动程序的信息：

```c
struct lapb_register_struct {
    void (*connect_confirmation)(int token, int reason);
    void (*connect_indication)(int token, int reason);
    void (*disconnect_confirmation)(int token, int reason);
    void (*disconnect_indication)(int token, int reason);
    int (*data_indication)(int token, struct sk_buff *skb);
    void (*data_transmit)(int token, struct sk_buff *skb);
};
```

此结构体中的每个成员对应设备驱动程序中的一个函数，当 LAPB 模块中发生特定事件时会调用这些函数。这些将在下面详细描述。如果不需要某个回调（注意！），则可以替换为 NULL。

LAPB 参数结构体
------------------

此结构体与 lapb_getparms 和 lapb_setparms 函数一起使用（见下文）。它们用于允许设备驱动程序获取和设置给定连接的 LAPB 实现的操作参数：

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

T1 和 T2 是协议定时参数，单位为 100 毫秒。N2 是在宣布链路失败之前的最大尝试次数。
窗口大小是允许远程端未确认的数据包的最大数量，对于标准 LAPB 链接，窗口大小的值在 1 到 7 之间；对于扩展 LAPB 链接，窗口大小的值在 1 到 127 之间。
mode 变量是一个位字段，目前用于设置三个值。位字段的含义如下：

======  =================================================
位	含义
======  =================================================
0	LAPB 操作模式（0=LAPB_STANDARD 1=LAPB_EXTENDED）
======  =================================================
1	[SM]LP操作 (0=LAPB_SLP 1=LAPB_MLP)
2	DTE/DCE操作 (0=LAPB_DTE 1=LAPB_DCE)
3-31	保留，必须为0
======  =================================================

扩展的LAPB操作表示使用扩展的序列号，从而允许更大的窗口大小，默认是标准的LAPB操作。
MLP操作与SLP操作相同，只是LAPB使用的地址不同以指示操作模式，默认是单链路程序。DCE和DTE操作之间的区别在于（i）用于命令和响应的地址，以及（ii）当DCE未连接时，它会在T1期间不设置轮询地发送DM。大写常量名称将在公共LAPB头文件中定义。

功能
---------
LAPB模块提供了一系列函数入口点：
::

    int lapb_register(void *token, struct lapb_register_struct);

在使用LAPB模块之前必须调用此函数。如果调用成功，则返回LAPB_OK。token必须是由设备驱动程序生成的独特标识符，以便唯一识别LAPB链路的实例。在所有回调中，该token将由LAPB模块返回，并且在设备驱动程序对LAPB模块的所有调用中都使用它。
对于单个设备驱动程序中的多个LAPB链路，必须多次调用lapb_register。lapb_register_struct的格式如上所示。返回值如下：

=============		=============================
LAPB_OK			LAPB注册成功
LAPB_BADTOKEN		token已注册
LAPB_NOMEM		内存不足
=============		=============================

::

    int lapb_unregister(void *token);

这会释放与LAPB链路相关的所有资源。任何当前的LAPB链路将被放弃，不再传递进一步的消息。在此调用之后，token的值对任何LAPB函数调用都不再有效。有效的返回值如下：

=============		===============================
LAPB_OK			LAPB注销成功
LAPB_BADTOKEN		无效/未知的LAPB token
=============		===============================
```c
    int lapb_getparms(void *token, struct lapb_parms_struct *parms);

此函数允许设备驱动程序获取当前LAPB变量的值，其中lapb_parms_struct已在上面描述。有效的返回值如下：

=============		=============================
LAPB_OK			LAPB getparms操作成功
LAPB_BADTOKEN		无效或未知的LAPB令牌
=============		=============================

::

    int lapb_setparms(void *token, struct lapb_parms_struct *parms);

此函数允许设备驱动程序设置当前LAPB变量的值，其中lapb_parms_struct已在上面描述。t1timer、t2timer和n2count的值将被忽略，同样地，在已连接状态下更改模式位也会被忽略。错误意味着没有任何值被更改。有效的返回值如下：

=============		=================================================
LAPB_OK			LAPB setparms操作成功
LAPB_BADTOKEN		无效或未知的LAPB令牌
LAPB_INVALUE		其中一个值超出了允许范围
=============		=================================================

::

    int lapb_connect_request(void *token);

使用当前参数设置发起连接请求。有效的返回值如下：

==============		=================================
LAPB_OK			LAPB正在开始连接
LAPB_BADTOKEN		无效或未知的LAPB令牌
LAPB_CONNECTED		LAPB模块已经连接
==============		=================================

::

    int lapb_disconnect_request(void *token);

发起断开连接请求。有效的返回值如下：

=================	===============================
LAPB_OK			LAPB正在开始断开连接
LAPB_BADTOKEN		无效或未知的LAPB令牌
=================	===============================
```
LAPB_NOTCONNECTED LAPB 模块未连接
=================	===============================

::

    int lapb_data_request(void *token, struct sk_buff *skb);

将数据排队以通过链路由 LAPB 模块进行传输。如果调用成功，则该 skbuff 将归 LAPB 模块所有，设备驱动程序不得再次使用。有效的返回值如下：

=================	=============================
LAPB_OK			LAPB 已接受数据
LAPB_BADTOKEN		无效或未知的 LAPB 令牌
LAPB_NOTCONNECTED	LAPB 模块未连接
=================	=============================

::

    int lapb_data_received(void *token, struct sk_buff *skb);

将从设备接收到的数据排队到 LAPB 模块。预期传递给 LAPB 模块的数据中，skb->data 指向 LAPB 数据的起始位置。如果调用成功，则该 skbuff 将归 LAPB 模块所有，设备驱动程序不得再次使用。有效的返回值如下：

=============		===========================
LAPB_OK			LAPB 已接受数据
LAPB_BADTOKEN		无效或未知的 LAPB 令牌
=============		===========================

回调函数
---------

这些回调函数是由设备驱动程序提供的，当发生事件时由 LAPB 模块调用。它们通过 lapb_register 函数（见上文）在 lapb_register_struct 结构体中注册（见上文）。

::

    void (*connect_confirmation)(void *token, int reason);

当通过调用 lapb_connect_request（见上文）请求的连接建立后，此函数由 LAPB 模块调用。reason 的值始终为 LAPB_OK。

::

    void (*connect_indication)(void *token, int reason);

当远程系统建立了链路时，此函数由 LAPB 模块调用。reason 的值始终为 LAPB_OK。
```c
void (*disconnect_confirmation)(void *token, int reason);
```

当设备驱动程序调用 `lapb_disconnect_request`（见上文）后发生事件时，此函数由 LAPB 模块调用。`reason` 参数表示发生了什么情况。在所有情况下，LAPB 链路可以认为已经被终止。`reason` 的值如下：

=================	====================================================
LAPB_OK			LAPB 链路正常终止
LAPB_NOTCONNECTED	远程系统未连接
LAPB_TIMEDOUT		从远程系统在 N2 次尝试内未收到响应
=================	====================================================

```c
void (*disconnect_indication)(void *token, int reason);
```

当链路被远程系统终止或发生其他事件导致链路终止时，此函数由 LAPB 模块调用。这可能作为对 `lapb_connect_request`（见上文）的响应返回，如果远程系统拒绝了请求。`reason` 的值如下：

=================	====================================================
LAPB_OK			远程系统正常终止了 LAPB 链路
LAPB_REFUSED		远程系统拒绝了连接请求
LAPB_NOTCONNECTED	远程系统未连接
LAPB_TIMEDOUT		从远程系统在 N2 次尝试内未收到响应
=================	====================================================

```c
int (*data_indication)(void *token, struct sk_buff *skb);
```

当从远程系统接收到数据并需要传递给协议栈的下一层时，此函数由 LAPB 模块调用。skbuff 归设备驱动程序所有，LAPB 模块将不再对其执行任何操作。`skb->data` 指针指向 LAPB 头之后的第一个字节的数据。如果帧在传递给上层之前被丢弃，则此方法应返回 NET_RX_DROP（在头文件 `include/linux/netdevice.h` 中定义）。

```c
void (*data_transmit)(void *token, struct sk_buff *skb);
```

当设备驱动程序要向远程系统发送数据时，此函数由 LAPB 模块调用。skbuff 归设备驱动程序所有，LAPB 模块将不再对其执行任何操作。
skb->data 指针将指向 LAPB 头部的第一个字节。
