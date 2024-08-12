### 编写USB设备驱动程序

==========================

#### 作者：Greg Kroah-Hartman

**简介**
============

Linux 的 USB 子系统从最初的 2.2.7 内核版本仅支持两种类型的设备（鼠标和键盘），发展到 2.4 内核版本时已能支持超过 20 种不同类型的设备。目前，Linux 几乎支持所有标准的 USB 类型设备（如键盘、鼠标、调制解调器、打印机和扬声器）以及越来越多的厂商特定设备（例如 USB 转串行转换器、数码相机、以太网设备和 MP3 播放器）。要获取当前支持的所有 USB 设备的完整列表，请参阅“资源”部分。
剩余未在 Linux 上得到支持的 USB 设备类型几乎都是厂商特定的设备。每个厂商都会选择实现一种自定义协议来与它们的设备通信，因此通常需要创建一个定制的驱动程序。一些厂商会公开它们的 USB 协议并协助开发 Linux 驱动程序，而其他厂商则不会公布这些协议，开发者被迫进行逆向工程。请参阅“资源”部分获取一些有用的逆向工程工具链接。
由于每种不同的协议都需要创建一个新的驱动程序，我编写了一个通用的 USB 驱动程序框架，其设计灵感来源于内核源代码树中的 `pci-skeleton.c` 文件，许多 PCI 网络驱动程序都是基于该文件构建的。这个 USB 框架可以在内核源代码树的 `drivers/usb/usb-skeleton.c` 中找到。在本文中，我将介绍该骨架驱动程序的基础知识，解释各个组件，并说明如何根据您的具体设备对其进行定制。

**Linux USB 基础**
================

如果您打算编写 Linux USB 驱动程序，请务必熟悉 USB 协议规范。您可以在 USB 官方网站上找到该规范以及许多其他有用文档（参见“资源”部分）。关于 Linux USB 子系统的优秀入门资料可以在 USB 工作设备列表中找到（参见“资源”部分）。它详细介绍了 Linux USB 子系统的结构，并向读者介绍了 USB urb（USB 请求块）的概念，这对于理解 USB 驱动程序至关重要。
Linux USB 驱动程序首先需要向 Linux USB 子系统注册自身，并提供有关所支持设备的信息以及当支持的设备插入或移除系统时应调用的函数。所有这些信息都通过 `usb_driver` 结构传递给 USB 子系统。骨架驱动程序声明了一个 `usb_driver` 结构如下：

    static struct usb_driver skel_driver = {
	    .name        = "skeleton",
	    .probe       = skel_probe,
	    .disconnect  = skel_disconnect,
	    .suspend     = skel_suspend,
	    .resume      = skel_resume,
	    .pre_reset   = skel_pre_reset,
	    .post_reset  = skel_post_reset,
	    .id_table    = skel_table,
	    .supports_autosuspend = 1,
    };

变量 `name` 是描述驱动程序的字符串。它用于打印到系统日志的信息消息中。`probe` 和 `disconnect` 函数指针在匹配 `id_table` 变量中的信息的设备被检测到或移除时被调用。
`fops` 和 `minor` 变量是可选的。大多数 USB 驱动程序会接入另一个内核子系统，如 SCSI、网络或 TTY 子系统。这类驱动程序会向其他内核子系统注册自身，并且用户空间交互通过该接口提供。但对于没有对应内核子系统的设备，如 MP3 播放器或扫描仪，则需要一种与用户空间交互的方法。USB 子系统提供了一种注册次要设备编号和一组 `file_operations` 函数指针的方式，从而实现了这种用户空间交互。骨架驱动程序需要这种接口，因此它提供了起始次要编号和指向其 `file_operations` 函数的指针。
然后通过调用 `usb_register()` 将 USB 驱动程序注册，这通常在驱动程序的初始化函数中完成，如下所示：

    static int __init usb_skel_init(void)
    {
	    int result;

	    /* 向 USB 子系统注册此驱动程序 */
	    result = usb_register(&skel_driver);
	    if (result < 0) {
		    pr_err("usb_register 对于 %s 驱动程序失败。错误号：%d\n", skel_driver.name, result);
		    return -1;
	    }

	    return 0;
    }
    module_init(usb_skel_init);

当驱动程序从系统中卸载时，需要使用 `usb_deregister()` 函数注销自身：

    static void __exit usb_skel_exit(void)
    {
	    /* 从 USB 子系统注销此驱动程序 */
	    usb_deregister(&skel_driver);
    }
    module_exit(usb_skel_exit);

为了使 Linux 热插拔系统能够在设备插入时自动加载驱动程序，您需要创建一个 `MODULE_DEVICE_TABLE`。以下代码告诉热插拔脚本此模块支持具有特定厂商和产品 ID 的单个设备：

    /* 与此驱动程序兼容的设备表 */
    static struct usb_device_id skel_table[] = {
	    { USB_DEVICE(USB_SKEL_VENDOR_ID, USB_SKEL_PRODUCT_ID) },
	    { }                      /* 终止项 */
    };
    MODULE_DEVICE_TABLE(usb, skel_table);

对于支持整个 USB 设备类别的驱动程序，还有其他宏可用于描述 `usb_device_id` 结构体。更多相关信息，请参阅 `usb.h`（参见“资源”部分）。

**设备操作**
================

当与 USB 核心注册的设备 ID 模式匹配的设备插入 USB 总线时，将调用 `probe` 函数。将 `usb_device` 结构体、接口编号和接口 ID 传递给该函数：

    static int skel_probe(struct usb_interface *interface,
	const struct usb_device_id *id)

此时驱动程序需要验证此设备是否确实是它可以接受的设备。如果是，则返回 0；如果不是，或者在初始化过程中发生任何错误，则从 `probe` 函数返回错误码（例如 `-ENOMEM` 或 `-ENODEV`）。
在骨架驱动程序中，我们确定哪些端点被标记为批量输入（bulk-in）和批量输出（bulk-out）。我们创建缓冲区来保存将要发送和从设备接收的数据，并初始化一个USB urb用于向设备写入数据。
相反，当设备从USB总线移除时，会调用断开函数并传入设备指针。驱动程序需要清理此时分配的所有私有数据，并关闭仍在USB系统中的任何待处理的urb。

现在设备已经连接到系统中，并且驱动程序已经与该设备绑定，用户程序尝试与设备通信时，传递给USB子系统的:c:type:`file_operations`结构体中的任何函数都将被调用。首先被调用的函数是`open`，因为程序试图打开设备进行I/O操作。我们会增加私有的使用计数，并在文件结构中保存指向我们内部结构的指针。这样做是为了让后续对文件操作的调用能够使驱动程序确定用户正在访问哪个设备。所有这些通过以下代码实现：

    /* 增加设备的使用计数 */
    kref_get(&dev->kref);

    /* 在文件的私有结构中保存我们的对象 */
    file->private_data = dev;

在`open`函数被调用后，读取和写入函数将被调用来从设备接收和发送数据。在`skel_write`函数中，我们接收到用户想要发送到设备的一些数据及其大小。函数根据它所创建的写入urb的大小（这个大小取决于设备的批量输出端点的大小）确定可以发送多少数据。然后，它将数据从用户空间复制到内核空间，设置urb指向数据，并将urb提交给USB子系统。这可以在下面的代码中看到：

    /* 我们只能写入一个urb能容纳的最大数据量 */
    size_t writesize = min_t(size_t, count, MAX_TRANSFER);

    /* 将数据从用户空间复制到我们的urb中 */
    copy_from_user(buf, user_buffer, writesize);

    /* 设置我们的urb */
    usb_fill_bulk_urb(urb,
		      dev->udev,
		      usb_sndbulkpipe(dev->udev, dev->bulk_out_endpointAddr),
		      buf,
		      writesize,
		      skel_write_bulk_callback,
		      dev);

    /* 通过批量端口发送数据 */
    retval = usb_submit_urb(urb, GFP_KERNEL);
    if (retval) {
	    dev_err(&dev->interface->dev,
                "%s - failed submitting write urb, error %d\n",
                __func__, retval);
    }

当使用`:c:func:`usb_fill_bulk_urb`函数填充好urb后，我们将其完成回调设置为我们自己的`skel_write_bulk_callback`函数。当urb由USB子系统处理完毕时，会调用此回调函数。此回调函数是在中断上下文中调用的，因此必须小心不要在此时做太多处理。我们的`skel_write_bulk_callback`实现仅仅报告urb是否成功完成，然后返回。

读取函数与写入函数的工作方式有所不同：我们不使用urb从设备传输数据到驱动程序。相反，我们调用`:c:func:`usb_bulk_msg`函数，它可以用于在不需要创建urbs和处理urb完成回调函数的情况下发送或接收来自设备的数据。我们调用`:c:func:`usb_bulk_msg`函数，给它一个缓冲区来存放从设备接收的任何数据以及超时值。如果在超时期限内没有从设备接收到数据，则函数将失败并返回错误消息。这可以从下面的代码中看出：

    /* 立即进行批量读取以获取设备数据 */
    retval = usb_bulk_msg (skel->dev,
			   usb_rcvbulkpipe (skel->dev,
			   skel->bulk_in_endpointAddr),
			   skel->bulk_in_buffer,
			   skel->bulk_in_size,
			   &count, 5000);
    /* 如果读取成功，将数据复制到用户空间 */
    if (!retval) {
	    if (copy_to_user (buffer, skel->bulk_in_buffer, count))
		    retval = -EFAULT;
	    else
		    retval = count;
    }

`:c:func:`usb_bulk_msg`函数对于执行单次读取或写入设备非常有用；然而，如果你需要持续地读取或写入设备，建议设置自己的urbs并将它们提交给USB子系统。

当用户程序释放了用于与设备通信的文件句柄时，驱动程序中的释放函数将被调用。在这个函数中，我们减少私有的使用计数并等待可能存在的待处理写入：

    /* 减少设备的使用计数 */
    --skel->open_count;

USB驱动程序需要解决的一个更困难的问题之一是USB设备可能随时从系统中移除，即使某个程序当前正在与之通信。它需要能够停止任何正在进行的读取和写入，并通知用户空间程序设备已不再存在。下面的代码（`skel_delete`函数）是一个如何实现这一点的例子：

    static inline void skel_delete (struct usb_skel *dev)
    {
	kfree (dev->bulk_in_buffer);
	if (dev->bulk_out_buffer != NULL)
	    usb_free_coherent (dev->udev, dev->bulk_out_size,
		dev->bulk_out_buffer,
		dev->write_urb->transfer_dma);
	usb_free_urb (dev->write_urb);
	kfree (dev);
    }

如果一个程序当前有一个打开的设备句柄，我们将重置`device_present`标志。对于每个期望设备存在的读取、写入、释放以及其他函数，驱动程序首先检查这个标志以确定设备是否仍然存在。如果没有，它会释放设备已消失的信息，并向用户空间程序返回`-ENODEV`错误。当最终调用释放函数时，它会确定是否有设备，如果没有，则执行`skel_disconnect`函数通常会在设备上没有打开文件时执行的清理工作（参见列表5）。

### 同步数据

这个USB骨架驱动程序没有包含向或从设备发送中断或同步数据的示例。中断数据几乎完全像批量数据那样发送，只是有几个小的例外。
同步数据则以不同的方式工作，持续的数据流被发送到或从设备。音频和视频摄像头驱动程序是非常好的处理同步数据的例子，如果你也需要这样做的话，它们将非常有用。

### 结论

编写Linux USB设备驱动程序并不是一项艰巨的任务，正如USB骨架驱动程序所示。这个驱动程序结合其他现有的USB驱动程序，应该能提供足够的例子帮助初学者在最短的时间内创建一个工作的驱动程序。linux-usb邮件列表存档也包含大量有用的信息。

### 资源

- Linux USB项目: http://www.linux-usb.org/
- Linux Hotplug项目: http://linux-hotplug.sourceforge.net/
- linux-usb邮件列表存档: https://lore.kernel.org/linux-usb/
- Linux USB设备驱动程序编程指南: https://lmu.web.psi.ch/docu/manuals/software_manuals/linux_sl/usb_linux_programming_guide.pdf
- USB主页: https://www.usb.org
