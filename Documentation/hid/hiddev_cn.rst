人类界面设备的照料与喂养
=================================

简介
============

除了用于正常输入类型的HID（Human Interface Device，人类界面设备）设备，USB还使用人类界面设备协议处理那些并非真正的人类接口，但具有类似通信需求的事物。这方面的主要例子是电源设备（尤其是不间断电源供应器）和高端显示器上的监控控制。

为了支持这些不同的要求，Linux USB系统为HID事件提供了两个独立的接口：
* 输入子系统，将HID事件转换为标准输入设备接口（如键盘、鼠标和游戏杆）和标准化事件接口——请参阅Documentation/input/input.rst
* hiddev接口，提供较为原始的HID事件

由设备产生的HID事件的数据流大致如下所示：

```
usb.c ---> hid-core.c  ----> hid-input.c ----> [keyboard/mouse/joystick/event]
                         |
                         |
                          --> hiddev.c ----> POWER / MONITOR CONTROL
```

此外，除USB之外的其他子系统可能也会向输入子系统馈送事件，但这些事件对HID设备接口没有影响。
使用HID设备接口
==============================

hiddev接口是一个使用常规USB主设备号的字符接口，次设备号从96开始至111结束。因此，你需要执行以下命令：

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

因此，你只需要将符合hiddev规范的用户空间程序指向设备正确的接口，一切就能顺利运行。

假设你已经拥有一个符合hiddev规范的用户空间程序。如果你需要编写一个，继续阅读。
HIDDEV API
==============

本描述应与HID规格一起阅读，该规格可从https://www.usb.org免费获取，并在http://www.linux-usb.org方便地链接。
hiddev API使用读取(read())接口和一组ioctl()调用。

HID设备通过称为“报告”的数据包与主机计算机交换数据。每个报告被分为“字段”，每个字段可以有一个或多个“用途”。在hid-core中，这些用途中的每一个都有一个单独的带符号32位值。
read():
-------

这是事件接口。当HID设备的状态改变时，它会执行一个中断传输，其中包含一个包含已更改值的报告。hid-core.c模块解析报告，并返回给hiddev.c报告中发生更改的单个用途。在基本模式下，hiddev将使这些单个用途更改对读者可用，使用如下结构体hiddev_event：

```c
struct hiddev_event {
    unsigned hid;
    signed int value;
};
```

包含状态改变的HID用途标识符及其更改为的值。请注意，该结构定义在<linux/hiddev.h>中，以及一些其他有用的#define和结构体。HID用途标识符是由HID用途页面左移至高阶16位位或用途代码组成。read()函数的行为可以通过下面描述的HIDIOCSFLAG ioctl()进行修改。
ioctl():
--------

这是控制接口。有几种控制方式：

HIDIOCGVERSION
  - int (读取)

从hiddev驱动程序获取版本代码。
HIDIOCAPPLICATION
  - (无参数)

此ioctl调用返回与HID设备关联的HID应用用途。ioctl()的第三个参数指定了要获取的应用程序索引。当设备有多个应用程序集合时，这很有用。如果索引无效（大于或等于该设备具有的应用程序集合数量），ioctl返回-1。你可以事先从hiddev_devinfo结构的num_applications字段了解设备有多少个应用程序集合。
以下是给定内容的中文翻译：

HIDIOCGCOLLECTIONINFO
- 结构体 hiddev_collection_info（读/写）

此操作返回上述信息的超集，不仅提供应用集合，还提供设备拥有的所有集合。它还返回集合在层次结构中所处的级别。用户通过将hiddev_collection_info结构中的index字段设置为要返回的索引来传递信息。ioctl填充其他字段。如果索引大于最后一个集合的索引，ioctl将返回-1，并将errno设置为-EINVAL。
HIDIOCGDEVINFO
- 结构体 hiddev_devinfo（读）

获取描述设备的hiddev_devinfo结构体。
HIDIOCGSTRING
- 结构体 hiddev_string_descriptor（读/写）

从设备获取字符串描述符。调用者必须填写"index"字段以指示应返回哪个描述符。
HIDIOCINITREPORT
- 无

指示内核从设备检索所有输入和特征报告值。此时，所有使用结构都将包含设备的当前值，并在设备更改时保持这些值。请注意，通常情况下，使用此ioctl是不必要的，因为后续内核会在连接时自动从设备初始化报告。
HIDIOCGNAME
- 字符串（可变长度）

获取设备名称。
HIDIOCGREPORT
- 结构体 hiddev_report_info（写）

指示内核从设备获取特征或输入报告，以便有选择地更新使用结构（与INITREPORT对比）。
HIDIOCSREPORT
- 结构体 hiddev_report_info（写）

指示内核向设备发送报告。此报告可以通过HIDIOCSUSAGE调用（如下）由用户填充，在将完整报告发送到设备之前填充报告中的单个使用值。
HIDIOCGREPORTINFO
- 结构体 hiddev_report_info（读/写）

为用户填充hiddev_report_info结构体。根据类型（输入、输出或特征）和id查找报告，因此这些字段必须由用户填充。ID可以是绝对的--设备报告的实际报告id--或者相对的--对于第一个报告为HID_REPORT_ID_FIRST，对于report_id后的下一个报告为(HID_REPORT_ID_NEXT | report_id)。如果没有关于报告id的先验信息，正确使用此ioctl的方法是使用上面的相对ID来枚举有效的ID。当没有更多的下一个ID时，ioctl返回非零值。实际的报告ID被填充到返回的hiddev_report_info结构体中。
HIDIOCGFIELDINFO
- 结构体 hiddev_field_info（读/写）

在hiddev_field_info结构中返回与报告相关的字段信息。用户必须在此结构中填写report_id和report_type，如上所述。还应填写field_index，该值应是从0到maxfield-1的数字，这是从之前的HIDIOCGREPORTINFO调用返回的。
HIDIOCGUCODE
- 结构体 hiddev_usage_ref（读/写）

在hiddev_usage_ref结构中返回usage_code，假设其报告类型、报告id、字段索引以及字段内的索引已经填入该结构体中。
HIDIOCGUSAGE
- 结构体 hiddev_usage_ref（读/写）

返回 hiddev_usage_ref 结构体中某一用途的值。要检索的用途可以按照上述方式指定，或者用户可以选择填充 report_type 字段并将 report_id 指定为 HID_REPORT_ID_UNKNOWN。在这种情况下，如果找到了与该用途相关的报告和字段信息，hiddev_usage_ref 将会被填充。

HIDIOCSUSAGE
- 结构体 hiddev_usage_ref（写）

设置输出报告中某一用途的值。用户像上述那样填充 hiddev_usage_ref 结构体，但还需额外填充 value 字段。

HIDIOGCOLLECTIONINDEX
- 结构体 hiddev_usage_ref（写）

返回与该用途关联的集合索引。这表明了该用途在集合层次结构中的位置。

HIDIOCGFLAG
- int （读）
HIDIOCSFLAG
- int （写）

这些操作分别用于检查和替换影响上述 read() 调用的模式标志。标志如下：

    HIDDEV_FLAG_UREF
      - 现在 read() 调用将返回
        struct hiddev_usage_ref 而不是 struct hiddev_event
这是一个较大的结构体，但在设备报告中有多个具有相同用途代码的用途的情况下，此模式有助于解决此类歧义。
HIDDEV_FLAG_REPORT
      - 此标志只能与
        HIDDEV_FLAG_UREF 配合使用。设置了此标志后，当设备发送报告时，一个填充了 report_type 和 report_id 的 struct hiddev_usage_ref 将被返回给 read()，但 field_index 设置为 FIELD_INDEX_NONE。这作为设备已发送报告的额外通知。
