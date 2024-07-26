用户空间MAD访问
====================

设备文件
============

  每个InfiniBand设备的每个端口都有一个"umad"设备和一个
  "issm"设备关联。例如，一个双端口HCA将有两个umad设备和两个issm设备，而一个交换机则会有一个每种类型的设备（用于交换机端口0）
创建MAD代理
===================

  可以通过填写struct ib_user_mad_reg_req结构体并调用适当的设备文件上的IB_USER_MAD_REGISTER_AGENT ioctl来创建一个MAD代理。如果注册请求成功，则会在结构体中返回一个32位ID
例如::

    struct ib_user_mad_reg_req req = { /* ... */ };
    int ret = ioctl(fd, IB_USER_MAD_REGISTER_AGENT, (char *) &req);
    if (!ret)
        my_agent = req.id;
    else
        perror("agent register");

  代理可以通过IB_USER_MAD_UNREGISTER_AGENT ioctl进行注销。此外，当文件描述符关闭时，所有通过该描述符注册的代理也将被注销。
2014
       现在提供了一个新的注册ioctl，允许在注册期间提供额外字段
使用此注册调用的用户隐式设置了pkey_index的使用（见下文）
接收MADs
==============

  使用read()接收MADs。接收端现在支持RMPP。传递给read()的缓冲区必须至少为struct ib_user_mad加上256字节。例如：

  如果传递的缓冲区不足以容纳接收到的MAD（RMPP），errno将设置为ENOSPC，并且所需缓冲区长度将设置在mad.length中
对于普通MAD（非RMPP）读取的示例::

    struct ib_user_mad *mad;
    mad = malloc(sizeof *mad + 256);
    ret = read(fd, mad, sizeof *mad + 256);
    if (ret != sizeof mad + 256) {
        perror("read");
        free(mad);
    }

  对于RMPP读取的示例::

    struct ib_user_mad *mad;
    mad = malloc(sizeof *mad + 256);
    ret = read(fd, mad, sizeof *mad + 256);
    if (ret == -ENOSPC)) {
        length = mad->length;
        free(mad);
        mad = malloc(sizeof *mad + length);
        ret = read(fd, mad, sizeof *mad + length);
    }
    if (ret < 0) {
        perror("read");
        free(mad);
    }

  除了实际的MAD内容外，struct ib_user_mad的其他字段也会被填充有关接收到的MAD的信息。例如，远程LID将位于mad->lid中
如果发送超时，将会生成一个接收，其中mad->status设置为ETIMEDOUT。否则，当MAD成功接收后，mad->status将为0
可以使用poll()/select()等待直到可以读取MAD
发送MADs
============

  使用write()发送MADs。发送的代理ID应填入MAD的id字段，目标LID应填入lid字段等。发送端支持RMPP，因此可以发送任意长度的MAD。例如::

    struct ib_user_mad *mad;

    mad = malloc(sizeof *mad + mad_length);

    /* 填充mad->data */

    mad->hdr.id  = my_agent;     /* 来自代理注册的req.id */
    mad->hdr.lid = my_dest;      /* 按网络字节顺序... */
    /* 等等 */

    ret = write(fd, mad, sizeof *mad + mad_length);
    if (ret != sizeof *mad + mad_length)
        perror("write");

交易ID
===============

  使用umad设备的用户可以在交易ID字段的较低32位（即按网络字节顺序排列的字段的最低有效半部分）中使用发送的MAD来匹配请求/响应对。较高32位保留供内核使用，并将在发送MAD之前被重写
P_Key 索引处理
====================

旧的 `ib_umad` 接口不允许为发送的 MAD 设置 P_Key 索引，并且没有提供获取接收的 MAD 的 P_Key 索引的方法。已定义了一个新的 `struct ib_user_mad_hdr` 布局，其中包含一个 `pkey_index` 成员；但是为了保持与旧应用程序的二进制兼容性，除非在使用文件描述符做其他事情之前调用了 `IB_USER_MAD_ENABLE_PKEY` 或 `IB_USER_MAD_REGISTER_AGENT2` 的 ioctl 命令之一，否则不会使用这个新布局。

2008 年 9 月，`IB_USER_MAD_ABI_VERSION` 将增加到 6，`struct ib_user_mad_hdr` 的新布局将默认使用，而 `IB_USER_MAD_ENABLE_PKEY` 的 ioctl 将被移除。

设置 IsSM 能力位
===========================

要为端口设置 IsSM 能力位，只需打开相应的 issm 设备文件。如果 IsSM 位已经设置，则打开调用会阻塞直到该位被清除（或者如果传递给 open() 的 O_NONBLOCK 标志被设置，则立即返回，errno 设置为 EAGAIN）。当 issm 文件关闭时，IsSM 位会被清除。无法对 issm 文件执行读取、写入或其他操作。

/dev 文件
==========

为了使用 udev 自动创建适当的字符设备文件，可以使用如下规则：

```
KERNEL=="umad*", NAME="infiniband/%k"
KERNEL=="issm*", NAME="infiniband/%k"
```

这将创建名为：

```
/dev/infiniband/umad0
/dev/infiniband/issm0
```

的设备节点，针对第一个端口等。可以通过以下文件确定这些设备关联的 InfiniBand 设备和端口：

```
/sys/class/infiniband_mad/umad0/ibdev
/sys/class/infiniband_mad/umad0/port

/sys/class/infiniband_mad/issm0/ibdev
/sys/class/infiniband_mad/issm0/port
```
