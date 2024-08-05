# FunctionFS的工作原理

## 概览

从内核的角度来看，FunctionFS仅仅是一个具有某些独特行为的复合功能。只有在用户空间驱动程序通过写入描述符和字符串进行注册之后，它才能被添加到USB配置中（用户空间程序需要提供与内核级复合功能在添加到配置时提供的相同信息）。
这意味着复合初始化函数不能位于`init`部分（即不能使用`__init`标签）。
从用户空间的角度来看，它是一个文件系统，在挂载后会提供一个名为“ep0”的文件。用户空间驱动程序需要向该文件写入描述符和字符串。它不需要担心端点、接口或字符串编号，只需简单地提供描述符，就像该功能是唯一的一个一样（端点和字符串编号从一开始，接口编号从零开始）。FunctionFS会根据需要更改这些内容，并处理不同配置中编号不同的情况。
当描述符和字符串被写入后，“ep#”文件会出现（每个声明的端点一个），用于处理单个端点上的通信。同样，FunctionFS负责处理实际的编号和配置更改（这意味着“ep1”文件实际上可能映射到（例如）端点3，而当配置更改时映射到（例如）端点2）。 “ep0”用于接收事件和处理设置请求。
当所有文件关闭后，该功能会自行禁用。
我还想提到的是，FunctionFS的设计允许多次挂载，因此最终一个gadget可以使用多个FunctionFS功能。设想是每个FunctionFS实例由挂载时使用的设备名称来识别。
可以想象一个gadget拥有以太网、MTP和HID接口，其中最后两个通过FunctionFS实现。在用户空间层面，这将如下所示：

```shell
$ insmod g_ffs.ko idVendor=<ID> iSerialNumber=<string> functions=mtp,hid
$ mkdir /dev/ffs-mtp && mount -t functionfs mtp /dev/ffs-mtp
$ ( cd /dev/ffs-mtp && mtp-daemon ) &
$ mkdir /dev/ffs-hid && mount -t functionfs hid /dev/ffs-hid
$ ( cd /dev/ffs-hid && hid-daemon ) &
```

在内核层面，gadget检查`ffs_data->dev_name`来确定其FunctionFS是否为MTP（“mtp”）或HID（“hid”）设计。
如果没有提供“functions”模块参数，则驱动程序只接受一个任意命名的功能。
当提供了“functions”模块参数时，只接受列表中的功能。特别是，如果“functions”参数的值仅包含一个元素列表，则行为类似于没有提供“functions”参数；但是，只接受指定名称的功能。
只有在所有声明的功能文件系统被挂载并且所有功能的USB描述符都被写入它们各自的“ep0”后，gadget才会注册。
反之，在第一个USB功能关闭其端点后，该小工具（gadget）就会取消注册。

DMABUF接口
==========

FunctionFS还支持一种基于DMABUF的接口，用户空间可以将DMABUF对象（外部创建的）附加到一个端点上，并随后使用它们进行数据传输。
用户空间的应用程序可以利用这个接口在多个接口之间共享DMABUF对象，允许它以零拷贝的方式传输数据，例如在IIO和USB堆栈之间。
作为这个接口的一部分，已经添加了三个新的IOCTL。这三个IOCTL必须在一个数据端点上执行（即不是ep0）。它们分别是：

  * `FUNCTIONFS_DMABUF_ATTACH(int)`
    将由文件描述符标识的DMABUF对象附加到数据端点。成功时返回零，出错时返回负的errno值。
  * `FUNCTIONFS_DMABUF_DETACH(int)`
    将由文件描述符标识的给定DMABUF对象从数据端点上解除。成功时返回零，出错时返回负的errno值。请注意，关闭端点的文件描述符会自动解除所有已附加的DMABUF对象。
  * `FUNCTIONFS_DMABUF_TRANSFER(struct usb_ffs_dmabuf_transfer_req *)`
    将先前附加的DMABUF加入到传输队列中。参数是一个结构体，其中包含DMABUF的文件描述符、要传输的字节大小（这通常对应于DMABUF的大小），以及一个目前未使用的“标志”字段。成功时返回零，出错时返回负的errno值。
