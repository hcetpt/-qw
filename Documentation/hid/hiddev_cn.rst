人类界面设备的维护与使用
================================

介绍
============

除了用于普通输入类型的HID（Human Interface Device）设备外，USB还使用人类界面设备协议来处理一些并非真正的人机接口，但具有类似通信需求的设备。两个主要的例子是电源设备（特别是不间断电源）和高端显示器上的监控控制。

为了支持这些不同的需求，Linux USB系统为HID事件提供了两个独立的接口：
* 输入子系统，将HID事件转换为普通输入设备接口（如键盘、鼠标和游戏杆），并提供标准化的事件接口——详见Documentation/input/input.rst。
* hiddev接口，提供相对原始的HID事件。

一个由设备产生的HID事件的数据流大致如下所示：

```
usb.c ---> hid-core.c  ----> hid-input.c ----> [keyboard/mouse/joystick/event]
                         |
                         |
                          --> hiddev.c ----> POWER / MONITOR CONTROL
```

此外，其他子系统（除USB之外）也有可能向输入子系统发送事件，但这些事件对HID设备接口没有影响。

使用HID设备接口
====================

hiddev接口是一个字符接口，使用标准的USB主设备号，次设备号从96开始到111结束。因此，你需要执行以下命令：

```
mknod /dev/usb/hiddev0 c 180 96
mknod /dev/usb/hiddev1 c 180 97
mknod /dev/usb/hiddev2 c 180 98
mknod /dev/usb/hiddev3 c 180 99
mknod /dev/usb/hiddev4 c 180 100
mknod /dev/usb/hiddev5 c 180 101
mknod /dev/usb/hiddev6 c 180 102
mknod /dev/usb/hiddev7 c 180 103
mknod /dev/usb/hiddev8 c 180 104
mknod /dev/usb/hiddev9 c 180 105
mknod /dev/usb/hiddev10 c 180 106
mknod /dev/usb/hiddev11 c 180 107
mknod /dev/usb/hiddev12 c 180 108
mknod /dev/usb/hiddev13 c 180 109
mknod /dev/usb/hiddev14 c 180 110
mknod /dev/usb/hiddev15 c 180 111
```

这样你就可以将你的hiddev兼容用户空间程序指向正确的设备接口，并且一切都会正常工作。

当然，前提是你要有一个hiddev兼容的用户空间程序。如果你需要编写一个，请继续阅读。

HIDDEV API
==============

本描述应与HID规范一起阅读，该规范可以从https://www.usb.org免费获取，并在http://www.linux-usb.org方便地链接。

hiddev API使用了一个读取（read）接口和一组ioctl调用。

HID设备通过称为“报告”的数据包与主机计算机交换数据。每个报告分为多个“字段”，每个字段可以包含一个或多个“用途”。在hid-core中，每个用途都有一个单独的带符号32位值。

### read()函数

这是事件接口。当HID设备的状态发生变化时，它会执行一个中断传输，其中包含一个包含变化值的报告。hid-core.c模块解析报告，并返回给hiddev.c模块报告中发生变化的各个用途。在基本模式下，hiddev会使用以下结构向读者提供这些用途的变化：

```c
struct hiddev_event {
    unsigned hid;
    signed int value;
};
```

这个结构包含状态变化的HID用途标识符及其变化后的值。请注意，该结构定义在<linux/hiddev.h>中，还包含一些其他有用的宏定义和结构。HID用途标识符是由HID用途页左移16位与用途代码进行或运算得到的组合值。可以通过下面描述的HIDIOCSFLAG ioctl调用来修改read()函数的行为。

### ioctl()函数

这是控制接口。有几种控制选项：

HIDIOCGVERSION
  - int (只读)

 获取hiddev驱动程序的版本号。

HIDIOCAPPLICATION
  - 无参数

此ioctl调用返回与HID设备关联的HID应用程序用途。ioctl()的第三个参数指定了要获取的应用程序索引。当设备有多个应用程序集合时，这非常有用。如果索引无效（大于或等于设备的应用程序集合数量），ioctl会返回-1。你可以预先从hiddev_devinfo结构的num_applications字段中了解设备有多少个应用程序集合。
HIDIOCGCOLLECTIONINFO  
- struct hiddev_collection_info（读/写）

此ioctl返回的信息超集不仅包含应用程序集合，还包括设备拥有的所有集合。它还返回了该集合在层次结构中的层级。用户需要传递一个hiddev_collection_info结构，并设置其中的index字段以指定要返回的索引。ioctl会填充其他字段。如果索引大于最后一个集合的索引，则ioctl返回-1并设置errno为-EINVAL。

HIDIOCGDEVINFO  
- struct hiddev_devinfo（读）

获取描述设备的hiddev_devinfo结构。

HIDIOCGSTRING  
- struct hiddev_string_descriptor（读/写）

从设备获取字符串描述符。调用者必须填写"index"字段以指示应返回哪个描述符。

HIDIOCINITREPORT  
- 无

指示内核从设备检索所有输入和特性报告值。此时，所有使用结构将包含设备的当前值，并随着设备的变化而保持更新。请注意，通常情况下使用此ioctl是不必要的，因为较新的内核会在设备连接时自动从设备初始化报告。

HIDIOCGNAME  
- 字符串（可变长度）

获取设备名称。

HIDIOCGREPORT  
- struct hiddev_report_info（写）

指示内核从设备获取特性或输入报告，以便选择性地更新使用结构（与INITREPORT相反）。

HIDIOCSREPORT  
- struct hiddev_report_info（写）

指示内核向设备发送报告。此报告可以通过HIDIOCSUSAGE调用（见下文）来逐个填写报告中的使用值，然后再完整地发送到设备。

HIDIOCGREPORTINFO  
- struct hiddev_report_info（读/写）

为用户填充hiddev_report_info结构。根据类型（输入、输出或特性）和id查找报告，因此这些字段必须由用户填写。id可以是绝对的——设备报告的实际报告id——或者是相对的——HID_REPORT_ID_FIRST表示第一个报告，(HID_REPORT_ID_NEXT | report_id)表示在report_id之后的下一个报告。如果没有关于报告id的先验信息，正确使用此ioctl的方法是使用上述相对id来枚举有效id。当没有更多的下一个id时，ioctl返回非零值。实际的报告id将被填充到返回的hiddev_report_info结构中。

HIDIOCGFIELDINFO  
- struct hiddev_field_info（读/写）

在一个hiddev_field_info结构中返回与报告相关的字段信息。用户必须在此结构中填写report_id和report_type，如上所述。还需要填写field_index，该值应该是一个从0到maxfield-1的数字，该数字来自之前HIDIOCGREPORTINFO调用的结果。

HIDIOCGUCODE  
- struct hiddev_usage_ref（读/写）

给定hiddev_usage_ref结构中的report type、report id、field index以及字段内的索引后，返回hiddev_usage_ref结构中的usage_code。
HIDIOCGUSAGE  
- 结构体 hiddev_usage_ref（读/写）

返回 hiddev_usage_ref 结构体中某个用途的值。要检索的用途可以按照上述方法指定，或者用户可以选择填充 report_type 字段并将 report_id 指定为 HID_REPORT_ID_UNKNOWN。在这种情况下，如果找到了与该用途相关的报告和字段信息，则会填充 hiddev_usage_ref。

HIDIOCSUSAGE  
- 结构体 hiddev_usage_ref（写）

设置输出报告中的某个用途的值。用户按照上述方法填充 hiddev_usage_ref 结构体，但还需额外填充 value 字段。

HIDIOGCOLLECTIONINDEX  
- 结构体 hiddev_usage_ref（写）

返回与该用途关联的集合索引。这表示该用途在集合层次结构中的位置。

HIDIOCGFLAG  
- int（读）

HIDIOCSFLAG  
- int（写）

这两个操作分别用于检查和替换影响上述 read() 调用的模式标志。标志如下：

    HIDDEV_FLAG_UREF
      - read() 调用现在返回的是 struct hiddev_usage_ref 而不是 struct hiddev_event。
这是一个较大的结构体，但在设备报告中有多个具有相同用途代码的用途时，此模式有助于解决这种歧义。

    HIDDEV_FLAG_REPORT
      - 此标志只能与 HIDDEV_FLAG_UREF 结合使用。设置了此标志后，当设备发送报告时，一个填充了 report_type 和 report_id 的 struct hiddev_usage_ref 将被返回给 read()，但 field_index 设置为 FIELD_INDEX_NONE。这作为设备发送报告的附加通知。
