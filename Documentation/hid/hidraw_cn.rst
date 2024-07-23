HIDRAW - 对USB和蓝牙人机界面设备的原始访问

hidraw驱动为USB和蓝牙人机界面设备（HIDs）提供了原始接口。它与hiddev的不同之处在于，发送和接收的报告不会被HID解析器解析，而是未经修改地直接发送到和从设备接收。
如果用户空间应用程序确切知道如何与硬件设备通信，并且能够手动构造HID报告，则应使用hidraw。当为定制的HID设备制作用户空间驱动程序时，这种情况经常发生。
hidraw对于与不符合规范的HID设备通信也很有用，这些设备以与其报告描述符不一致的方式发送和接收数据。由于hiddev会解析通过其发送和接收的报告，并将它们与设备的报告描述符进行对比检查，因此无法使用hiddev与这些不符合规范的设备通信。对于这些不符合规范的设备，hidraw是唯一的选择，除非编写自定义内核驱动程序。
hidraw的一个好处是，其在用户空间应用程序中的使用独立于底层硬件类型。目前，hidraw针对USB和蓝牙实现了支持。未来，随着使用HID规范的新硬件总线类型的开发，hidraw将扩展以添加对这些新总线类型的支持。
hidraw使用动态主号，这意味着应该依赖udev来创建hidraw设备节点。通常，udev会在/dev目录下直接创建设备节点（例如：/dev/hidraw0）。由于此位置取决于发行版和udev规则，应用程序应使用libudev来定位系统上连接的hidraw设备。有关libudev的教程及工作示例，请参阅：

http://www.signal11.us/oss/udev/
https://web.archive.org/web/2019*/www.signal11.us

HIDRAW API

read()
读取()将读取从HID设备接收到的排队报告。在USB设备上，使用read()读取的报告是从设备的INTERRUPT IN端点发送的报告。默认情况下，read()将阻塞直到有可读的报告。可以通过在open()时传递O_NONBLOCK标志或使用fcntl()设置O_NONBLOCK标志使read()变为非阻塞。
在使用编号报告的设备上，返回数据的第一字节将是报告编号；报告数据紧随其后，从第二字节开始。对于不使用编号报告的设备，报告数据将从第一字节开始。

write()
写入()函数将向设备写入报告。对于USB设备，如果设备具有INTERRUPT OUT端点，则报告将在该端点发送。如果没有，报告将通过控制端点使用SET_REPORT传输发送。
传递给write()的缓冲区的第一字节应设置为报告编号。如果设备不使用编号报告，第一字节应设置为0。报告数据本身应从第二字节开始。

ioctl()
hidraw支持以下ioctl：

HIDIOCGRDESCSIZE：
获取报告描述符大小

此ioctl将获取设备的报告描述符的大小。
HIDIOCGRDESC:
获取报告描述符

此ioctl使用hidraw_report_descriptor结构体返回设备的报告描述符。确保将hidraw_report_descriptor结构体的大小字段设置为从HIDIOCGRDESCSIZE返回的大小。

HIDIOCGRAWINFO:
获取原始信息

此ioctl将返回一个包含设备总线类型、供应商ID（VID）和产品ID（PID）的hidraw_devinfo结构体。总线类型可以是以下之一：

- BUS_USB
- BUS_HIL
- BUS_BLUETOOTH
- BUS_VIRTUAL

这些在uapi/linux/input.h中定义。

HIDIOCGRAWNAME(len):
获取原始名称

此ioctl返回一个包含设备供应商和产品字符串的字符串。返回的字符串是Unicode，UTF-8编码。

HIDIOCGRAWPHYS(len):
获取物理地址

此ioctl返回一个代表设备物理地址的字符串。对于USB设备，该字符串包含到设备的物理路径（即USB控制器、集线器、端口等）。对于蓝牙设备，字符串包含设备的硬件（MAC）地址。

HIDIOCSFEATURE(len):
发送特征报告

此ioctl将向设备发送一个特征报告。根据HID规范，特征报告总是通过控制端点发送。将提供的缓冲区的第一个字节设置为报告编号。对于不使用编号报告的设备，将第一个字节设置为0。报告数据从第二个字节开始。确保相应地设置len，使其比报告长度多1（以考虑报告编号）。

HIDIOCGFEATURE(len):
获取特征报告

此ioctl将使用控制端点从设备请求一个特征报告。提供的缓冲区的第一个字节应设置为请求报告的报告编号。对于不使用编号报告的设备，将第一个字节设置为0。返回的报告缓冲区将在第一个字节包含报告编号，后面是设备读取的报告数据。对于不使用编号报告的设备，报告数据将从返回缓冲区的第一个字节开始。

HIDIOCSINPUT(len):
发送输入报告

此ioctl将使用控制端点向设备发送一个输入报告。在大多数情况下，设置设备的输入HID报告没有意义且无效果，但某些设备可能选择使用此方法来设置或重置报告的初始状态。与此报告一起发出的缓冲区格式与HIDIOCSFEATURE相同。
HIDIOCGINPUT(len)：
获取输入报告

此 ioctl（输入/输出控制操作）将使用控制端点从设备请求输入报告。对于大多数存在专门的输入端点用于常规输入报告的设备，这种方式较慢，但它允许主机请求特定报告编号的值。通常情况下，这被用来在应用程序通过常规设备读取接口监听正常报告之前请求设备输入报告的初始状态。使用此报告发出的缓冲区格式与 HIDIOCGFEATURE 的格式相同。

HIDIOCSOUTPUT(len)：
发送输出报告

此 ioctl 将使用控制端点向设备发送输出报告。对于大多数存在专门的输出端点用于常规输出报告的设备，这种方式较慢，但为了完整性而添加。通常情况下，这被用来设置设备输出报告的初始状态，在应用程序通过常规设备写入接口发送更新之前。使用此报告发出的缓冲区格式与 HIDIOCSFEATURE 的格式相同。

HIDIOCGOUTPUT(len)：
获取输出报告

此 ioctl 将使用控制端点从设备请求输出报告。通常情况下，这被用来检索设备输出报告的初始状态，在应用程序根据需要通过 HIDIOCSOUTPUT 请求或常规设备写入接口更新它之前。使用此报告发出的缓冲区格式与 HIDIOCGFEATURE 的格式相同。

示例
-----
在 samples/ 目录下，可以找到 hid-example.c，该文件展示了读取、写入以及 hidraw 的所有 ioctl 的示例。这些代码可以由任何人出于任何目的使用，并且可以作为开发使用 hidraw 的应用程序的起点。

文档作者：

	Alan Ott <alan@signal11.us>，Signal 11 Software
