### 人类界面设备的维护与使用

#### 引言
除了作为常规输入类型的HID（Human Interface Device，人类界面设备）设备之外，USB还利用人类界面设备协议来处理那些并非真正的人类界面设备、但有着类似通信需求的设备。两个主要的例子是电源设备（特别是不间断电源系统）和高端显示器上的监视器控制功能。
为了支持这些不同的需求，Linux USB系统为HID事件提供了两种独立的接口：
* 输入子系统，它将HID事件转换为标准的输入设备接口（如键盘、鼠标和游戏杆）以及标准化的事件接口——参见`Documentation/input/input.rst`
* `hiddev`接口，提供相对原始的HID事件

一个由设备产生的HID事件的数据流向大致如下所示：

```
usb.c ---> hid-core.c  ----> hid-input.c ----> [keyboard/mouse/joystick/event]
                         |
                         |
                          --> hiddev.c ----> POWER / MONITOR CONTROL
```

此外，除了USB之外的其他子系统也有可能向输入子系统提供事件，但这不会影响到HID设备接口。

#### 使用HID设备接口
`hiddev`接口是一个字符接口，使用标准的USB主设备号，次要设备号从96开始至111结束。因此，你需要执行以下命令：

```sh
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

这样你就可以指向你的设备对应的`hiddev`兼容用户空间程序，一切都会正常工作。
当然，前提是您已经拥有一个`hiddev`兼容的用户空间程序。如果您需要编写一个，请继续阅读。

#### HIDDEV API
本描述应与HID规范一起阅读，该规范可从[https://www.usb.org](https://www.usb.org)免费获取，并方便地链接在[http://www.linux-usb.org](http://www.linux-usb.org)上。
`hiddev` API使用了一个读取接口和一组`ioctl()`调用。

HID设备通过称为“报告”的数据包与主机计算机交换数据。每个报告被分为多个“字段”，每个字段可以有一个或多个“用途”。在`hid-core`中，这些用途中的每一个都有一个单独的带符号32位值。

**read()**
---

这是事件接口。当HID设备的状态发生变化时，它会执行一个包含报告的中断传输，其中包含了变化后的值。`hid-core.c`模块解析这个报告，并返回给`hiddev.c`那些报告中发生变化的用途。在基本模式下，`hiddev`将这些单个用途的变化以`struct hiddev_event`的形式提供给读者：

```c
struct hiddev_event {
    unsigned hid;  // HID用途标识符
    signed int value;  // 变化后的值
};
```

其中包含了状态变化的HID用途标识符及其变化后的值。请注意，该结构定义在`<linux/hiddev.h>`中，其中还包括一些有用的宏定义和其他结构。HID用途标识符是由HID用途页面左移16位与用途代码进行或运算得到的组合。`read()`函数的行为可以通过下面描述的`HIDIOCSFLAG` `ioctl()`调用来修改。

**ioctl()**
--------

这是控制接口。有几个控制命令：

**HIDIOCGVERSION**
  - `int`（读）

获取`hiddev`驱动程序的版本代码。

**HIDIOCAPPLICATION**
  - `无参数`

此`ioctl`调用返回与HID设备相关的HID应用用途。`ioctl()`的第三个参数指定了要获取的应用索引。当设备有多个应用集合时，这非常有用。如果索引无效（大于或等于该设备的应用集合数量），则`ioctl`返回-1。你可以事先从`hiddev_devinfo`结构中的`num_applications`字段得知设备有多少个应用集合。
这些 ioctl (输入/输出控制) 命令用于与 HID (Human Interface Device) 设备进行交互。下面是每个命令的中文翻译及简要说明：

### HIDIOCGCOLLECTIONINFO
- 结构体 `hiddev_collection_info`（读/写）

此 ioctl 返回的信息超出了上述信息，不仅提供了应用程序集合，还提供了设备的所有集合。它还返回了集合在层次结构中的层级。用户需要传递一个 `hiddev_collection_info` 结构体，并设置 `index` 字段为希望返回的索引。ioctl 会填充其他字段。如果索引大于最后一个集合的索引，则 ioctl 返回 `-1` 并将 `errno` 设置为 `-EINVAL`。

### HIDIOCGDEVINFO
- 结构体 `hiddev_devinfo`（读）

获取描述设备的 `hiddev_devinfo` 结构体。

### HIDIOCGSTRING
- 结构体 `hiddev_string_descriptor`（读/写）

从设备获取字符串描述符。调用者必须填写 `index` 字段以指示应返回哪个描述符。

### HIDIOCINITREPORT
- 无参数

指示内核从设备检索所有输入和特性报告值。此时，所有的使用结构都将包含设备的当前值，并随着设备的变化而更新。请注意，通常情况下使用此 ioctl 是不必要的，因为较新版本的内核会在连接时自动从设备初始化报告。

### HIDIOCGNAME
- 字符串（可变长度）

获取设备名称。

### HIDIOCGREPORT
- 结构体 `hiddev_report_info`（写）

指示内核从设备获取特性或输入报告，以便有选择地更新使用结构（与 `INITREPORT` 相比）。

### HIDIOCSREPORT
- 结构体 `hiddev_report_info`（写）

指示内核向设备发送报告。此报告可以通过 `HIDIOCSUSAGE` 调用来由用户填充，以在发送完整报告到设备之前填充报告中的单个使用值。

### HIDIOCGREPORTINFO
- 结构体 `hiddev_report_info`（读/写）

为用户填充 `hiddev_report_info` 结构体。报告通过类型（输入、输出或特性）和 ID 查找，因此这些字段必须由用户填写。ID 可以是绝对的——设备报告的实际报告 ID——也可以是相对的——`HID_REPORT_ID_FIRST` 表示第一个报告，以及 `(HID_REPORT_ID_NEXT | report_id)` 表示在 `report_id` 之后的下一个报告。如果没有关于报告 ID 的先验信息，正确使用此 ioctl 的方法是使用上面的相对 ID 来枚举有效的 ID。当没有更多的下一个 ID 时，ioctl 返回非零值。实际的报告 ID 将被填充到返回的 `hiddev_report_info` 结构体中。

### HIDIOCGFIELDINFO
- 结构体 `hiddev_field_info`（读/写）

在一个 `hiddev_field_info` 结构体中返回与报告相关的字段信息。用户必须在此结构体中填写 `report_id` 和 `report_type`，如上所述。还需要填写 `field_index`，该值应该是一个从 0 到由前一个 `HIDIOCGREPORTINFO` 调用返回的 `maxfield-1` 的数字。

### HIDIOCGUCODE
- 结构体 `hiddev_usage_ref`（读/写）

给定已填写到结构体中的报告类型、报告 ID、字段索引和字段内的索引后，在 `hiddev_usage_ref` 结构体中返回 `usage_code`。
HIDIOCGUSAGE  
- 结构体 hiddev_usage_ref（读/写）

返回 hiddev_usage_ref 结构体中某一用途的值。要检索的用途可以按照上述方式指定，或者用户可以选择填充 report_type 字段并将 report_id 指定为 HID_REPORT_ID_UNKNOWN。在这种情况下，如果找到了与该用途相关的报告和字段信息，则会用这些信息填充 hiddev_usage_ref。

HIDIOCSUSAGE  
- 结构体 hiddev_usage_ref（写）

设置输出报告中某一用途的值。用户像上述那样填充 hiddev_usage_ref 结构体，但还需额外填充 value 字段。

HIDIOGCOLLECTIONINDEX  
- 结构体 hiddev_usage_ref（写）

返回与该用途关联的集合索引。这表明了该用途在集合层次结构中的位置。

HIDIOCGFLAG  
- int（读）
HIDIOCSFLAG  
- int（写）

这些操作分别用于检查和替换影响上述 read() 调用的行为模式标志。标志如下：

    HIDDEV_FLAG_UREF
      - 现在 read() 调用将返回
        struct hiddev_usage_ref 而不是 struct hiddev_event
这是一个较大的结构体，但在设备报告中有多个具有相同用途代码的用途时，此模式有助于解决这种模糊性。

    HIDDEV_FLAG_REPORT
      - 此标志只能与
        HIDDEV_FLAG_UREF 配合使用。设置了此标志后，当设备发送报告时，一个填充了 report_type 和 report_id 的 struct hiddev_usage_ref 将被返回给 read()，但 field_index 设置为 FIELD_INDEX_NONE。这作为设备发送报告的额外通知。
