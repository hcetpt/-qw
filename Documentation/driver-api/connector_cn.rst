### SPDX 许可证标识符: GPL-2.0

#### 内核连接器

##### 内核连接器 —— 基于 netlink 的用户空间<->内核空间易于使用的通信模块
连接器驱动程序使得使用基于 netlink 的网络连接各种代理变得简单。必须注册一个回调函数和一个标识符，当驱动程序接收到带有适当标识符的特殊 netlink 消息时，将调用相应的回调函数。
从用户空间的角度来看，操作非常直接：

- socket();
- bind();
- send();
- recv();

但如果内核空间想要利用这种连接的全部功能，驱动程序编写者必须创建特殊的套接字，并了解如何处理 struct sk_buff 等等……连接器驱动程序允许任何内核空间代理以一种显著更简单的方式使用基于 netlink 的网络进行进程间通信：

```c
int cn_add_callback(const struct cb_id *id, char *name, void (*callback) (struct cn_msg *, struct netlink_skb_parms *));
void cn_netlink_send_mult(struct cn_msg *msg, u16 len, u32 portid, u32 __group, int gfp_mask);
void cn_netlink_send(struct cn_msg *msg, u32 portid, u32 __group, int gfp_mask);
```

```c
struct cb_id
{
    __u32 idx;
    __u32 val;
};
```

`idx` 和 `val` 是唯一的标识符，必须在 connector.h 头文件中为内核使用注册。`void (*callback) (void *)` 是一个回调函数，当带有上述 `idx.val` 的消息被连接器核心接收时将被调用。该函数的参数必须解引用为 `struct cn_msg *`：

```c
struct cn_msg
{
    struct cb_id id;

    __u32 seq;
    __u32 ack;

    __u16 len;       /* 下面数据的长度 */
    __u16 flags;
    __u8 data[0];
};
```

### 连接器接口

#### 内核文档：include/linux/connector.h

**注释：**
当注册新的回调用户时，连接器核心会为用户分配一个与其 `id.idx` 相等的 netlink 组。

### 协议描述

当前框架提供了一个具有固定头部的传输层。推荐使用的协议是这样的：

`msg->seq` 和 `msg->ack` 用于确定消息的血统。当发送消息时，使用本地唯一的序列号和随机确认号。序列号也可以复制到 `nlmsghdr->nlmsg_seq` 中。
序列号随每条消息发送而递增。
如果期望对消息有回复，则收到的消息中的序列号必须与原始消息相同，而确认号必须是原始消息序列号+1。
如果我们接收到的消息序列号不等于我们期望的值，则它是一个新消息。如果我们接收到的消息序列号与我们期望的相同，但其确认号不等于原始消息序列号+1，则它也是一个新消息。
显然，协议头部包含上面的 `id`。
连接器允许以下形式的事件通知：内核驱动程序或用户空间进程可以要求连接器在选定的 `id` 被打开或关闭（注册或注销其回调）时通知它。这是通过向连接器驱动程序发送一个特殊命令来完成的（它也以 `id={-1, -1}` 注册自身）。
### 使用示例

可以在`cn_test.c`模块中找到这种使用的示例，该模块使用连接器请求通知并发送消息。

### 可靠性

Netlink本身不是一个可靠的协议。这意味着由于内存压力或进程接收队列溢出，消息可能会丢失，因此警告调用者必须做好准备。这就是为什么`struct cn_msg`（主连接器的消息头）包含`u32 seq`和`u32 ack`字段的原因。

### 用户空间使用

2.6.14版有一个新的Netlink套接字实现，默认情况下不允许用户向除了1以外的Netlink组发送数据。
因此，如果你想使用一个Netlink套接字（例如使用连接器）与不同的组号，用户空间的应用程序必须首先订阅那个组。这可以通过以下伪代码实现：

```c
s = socket(PF_NETLINK, SOCK_DGRAM, NETLINK_CONNECTOR);

l_local.nl_family = AF_NETLINK;
l_local.nl_groups = 12345;
l_local.nl_pid = 0;

if (bind(s, (struct sockaddr *)&l_local, sizeof(struct sockaddr_nl)) == -1) {
	perror("bind");
	close(s);
	return -1;
}

{
	int on = l_local.nl_groups;
	setsockopt(s, 270, 1, &on, sizeof(on));
}
```

其中上面的270是`SOL_NETLINK`，而1是一个`NETLINK_ADD_MEMBERSHIP`套接字选项。要取消多播订阅，应该使用`NETLINK_DROP_MEMBERSHIP`参数调用上述套接字选项，该参数定义为0。

2.6.14 Netlink代码仅允许选择小于或等于最大组号的组，这个最大组号是在`netlink_kernel_create()`时使用的。
在连接器的情况下，它是`CN_NETLINK_USERS + 0xf`，所以如果你想使用12345这样的组号，你必须将`CN_NETLINK_USERS`增加到那个数字。
额外的0xf个数字分配给非内核用户使用。

由于这个限制，现在组号0xffffffff不工作，因此不能添加/移除连接器的组通知，但据我所知，只有`cn_test.c`测试模块使用了它。

Netlink领域的某些工作仍在进行中，因此在2.6.15版本期间可能会发生变化，如果发生这种情况，文档将会更新以适应那个内核版本。

### 代码示例

连接器测试模块和用户空间的示例代码可以在`samples/connector/`目录下找到。为了构建这些代码，需要启用`CONFIG_CONNECTOR`和`CONFIG_SAMPLES`配置项。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
