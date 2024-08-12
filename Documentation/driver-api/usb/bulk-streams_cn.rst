### 背景

在USB 3.0规范中增加了批量端点流。流允许设备驱动程序对批量端点进行过载，以便可以一次排队多个传输。流在《通用串行总线3.0规范》的第4.4.6.4节和8.12.1.4节中定义，该规范可在 https://www.usb.org/developers/docs/ 获取。使用流来排队多个SCSI命令的USB附加SCSI协议可以在T10网站（https://t10.org/）上找到。

### 设备侧影响

一旦将缓冲区排队到流环中，就通过另一个端点的带外机制通知设备，该流ID的数据已准备好。然后设备告诉主机它想启动哪个“流”。主机也可以在没有设备请求的情况下发起一个流的传输，但设备可以拒绝这个传输。设备可以在任何时候切换流。

### 驱动程序影响

```c
int usb_alloc_streams(struct usb_interface *interface,
                      struct usb_host_endpoint **eps, unsigned int num_eps,
                      unsigned int num_streams, gfp_t mem_flags);
```

设备驱动程序将调用此API来请求主机控制器驱动程序分配内存，这样驱动程序就可以使用最多num_streams个流ID。它们必须传递一个需要设置相同流ID的`usb_host_endpoint`数组。这是为了确保UASP驱动程序能够在双向命令序列中为批量输入和输出端点使用相同的流ID。
返回值是一个错误条件（如果其中一个端点不支持流或xHCI驱动程序内存不足），或者是主机控制器为此端点分配的流数量。xHCI主机控制器硬件声明了它可以支持多少流ID，每个超速设备上的批量端点都会说明它可以处理多少流ID。因此，驱动程序应该能够应对被分配少于请求的流ID的情况。

**注意：** 如果你为作为参数传入的任何端点排队了URB，请不要调用此函数。不要调用此函数请求少于两个流。

驱动程序仅允许在未调用`usb_free_streams()`的情况下为同一端点调用此API一次。这对于xHCI主机控制器驱动程序来说是一种简化，并且将来可能会发生变化。

### 选择新的流ID使用

流ID 0是保留的，不应用于与设备通信。如果`usb_alloc_streams()`返回N，则可以使用流1至N。
要为特定流排队URB，请设置`urb->stream_id`值。如果端点不支持流，则会返回错误。

请注意，如果xHCI驱动程序支持次级流ID，那么需要添加新的API来选择下一个流ID。
清理
=====

如果一个驱动程序希望停止使用流与设备进行通信，它应该调用：

```c
void usb_free_streams(struct usb_interface *interface,
		struct usb_host_endpoint **eps, unsigned int num_eps,
		gfp_t mem_flags);
```

当驱动程序释放接口时，所有的流ID都将被取消分配，以确保不支持流的驱动程序能够使用该端点。
