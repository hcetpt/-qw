.. include:: <isonum.txt>

============
简介
============

:版权: |copy| 1999-2001 Vojtech Pavlik <vojtech@ucw.cz> - 赞助商：SuSE

架构
============

输入子系统是一组驱动程序的集合，旨在支持Linux下的所有输入设备。大多数驱动位于`drivers/input`中，虽然也有相当一部分位于`drivers/hid`和`drivers/platform`。
输入子系统的内核是输入模块，该模块必须在其他任何输入模块之前加载——它作为两个模块组之间通信的方式：

设备驱动程序
--------------

这些模块与硬件（例如通过USB）进行通信，并向输入模块提供事件（按键、鼠标移动等）。

事件处理程序
--------------

这些模块从输入核心获取事件，并通过各种接口将它们传递到需要的地方——例如，将按键事件传递给内核，通过模拟PS/2接口将鼠标移动传递给GPM和X等。

简单使用
============

对于最常见的配置，即一个USB鼠标和一个USB键盘，您需要加载以下模块（或将其编译进内核）：

```
input
mousedev
usbcore
uhci_hcd 或 ohci_hcd 或 ehci_hcd
usbhid
hid_generic
```

在此之后，USB键盘会立即工作，而USB鼠标将以主设备号13，次设备号63的形式作为一个字符设备可用：

```
crw-r--r--   1 root     root      13,  63 Mar 28 22:45 mice
```

这个设备通常由系统自动创建。手动创建它的命令如下：

```
cd /dev
mkdir input
mknod input/mice c 13 63
```

之后，您需要指向GPM（文本模式下的鼠标剪切工具）和XFree来使用该设备——GPM应该像这样调用：

```
gpm -t ps2 -m /dev/input/mice
```

在X中：

```conf
Section "Pointer"
    Protocol    "ImPS/2"
    Device      "/dev/input/mice"
    ZAxisMapping 4 5
EndSection
```

完成上述所有步骤后，您就可以使用您的USB鼠标和键盘了。

详细描述
====================

事件处理程序
--------------

事件处理程序根据需要将来自设备的事件分发到用户空间和内核消费者。

evdev
~~~~~

`evdev` 是通用的输入事件接口。它将内核生成的事件直接传递给程序，并附带时间戳。事件代码在所有架构上都是相同的，并且与硬件无关。
这是用户空间消费用户输入的首选接口，鼓励所有客户端使用它。
有关API的说明，请参阅 :ref:`event-interface`。
设备位于 `/dev/input` 中：

```
crw-r--r--   1 root     root      13,  64 Apr  1 10:49 event0
crw-r--r--   1 root     root      13,  65 Apr  1 10:50 event1
crw-r--r--   1 root     root      13,  66 Apr  1 10:50 event2
crw-r--r--   1 root     root      13,  67 Apr  1 10:50 event3
...
```

次设备号有两个范围：64至95为静态遗留范围。如果系统中有超过32个输入设备，则会创建以256开始的附加evdev节点。
``keyboard`` 是内核中的输入处理器，是 VT 代码的一部分。它处理键盘按键，并为 VT 控制台处理用户输入。

mousedev
``mousedev`` 是一个用于使那些使用鼠标输入的传统程序能够正常工作的补丁。它可以接收来自鼠标或数位板的事件，并向用户空间提供一个 PS/2 风格（类似于 `/dev/psaux`）的鼠标设备。
在 `/dev/input` 中的 mousedev 设备如下所示：

```
crw-r--r--   1 root     root      13,  32 Mar 28 22:45 mouse0
crw-r--r--   1 root     root      13,  33 Mar 29 00:41 mouse1
crw-r--r--   1 root     root      13,  34 Mar 29 00:41 mouse2
crw-r--r--   1 root     root      13,  35 Apr  1 10:50 mouse3
...
...
crw-r--r--   1 root     root      13,  62 Apr  1 10:50 mouse30
crw-r--r--   1 root     root      13,  63 Apr  1 10:50 mice
```

每个 `mouse` 设备对应单个鼠标或数位板，除了最后一个 `mice`。这个单一字符设备由所有鼠标和数位板共享，即使没有任何设备连接时，该设备仍然存在。这对于热插拔 USB 鼠标非常有用，这样旧的程序即使没有鼠标连接也可以打开该设备。

内核配置中的 `CONFIG_INPUT_MOUSEDEV_SCREEN_XY` 是屏幕大小（以像素为单位），适用于 XFree86。如果你想要在 X 环境中使用数位板，这是必需的，因为其移动通过虚拟 PS/2 鼠标发送给 X，因此需要进行相应的缩放。如果只使用鼠标，则这些值不会被使用。

mousedev 将根据读取数据的程序的需求生成 PS/2、ImPS/2（Microsoft IntelliMouse）或 ExplorerPS/2（IntelliMouse Explorer）协议。你可以将 GPM 和 X 设置为其中任何一种。如果你想使用 USB 鼠标的滚轮，需要 ImPS/2；如果你想使用额外的按钮（最多 5 个），则需要 ExplorerPS/2。

joydev
``joydev`` 实现了 Linux 游戏杆 API 的 v0.x 和 v1.x 版本。详情请参见 :ref:`joystick-api`。
一旦连接了任何游戏杆，就可以在 `/dev/input` 中访问它：

```
crw-r--r--   1 root     root      13,   0 Apr  1 10:50 js0
crw-r--r--   1 root     root      13,   1 Apr  1 10:50 js1
crw-r--r--   1 root     root      13,   2 Apr  1 10:50 js2
crw-r--r--   1 root     root      13,   3 Apr  1 10:50 js3
...
```

以此类推，直到 js31，在传统范围内，如果有更多的游戏杆设备，则会有主设备号超过 256 的附加节点。
设备驱动程序
--------------

设备驱动程序是生成事件的模块。

hid-generic
~~~~~~~~~~~

`hid-generic` 是整个驱动程序套件中最大且最复杂的驱动之一。它处理所有HID（Human Interface Device，人机接口设备）设备，由于这类设备种类繁多，并且USB HID规范并不简单，因此该驱动程序需要如此庞大。目前，它支持USB鼠标、游戏杆、游戏手柄、方向盘、键盘、轨迹球和数字化仪。

然而，USB还使用HID来控制显示器、扬声器、不间断电源（UPS）、液晶屏及其他多种用途。显示器和扬声器的控制相对容易添加到hid/input接口，但对于UPS和液晶屏来说并不适用。为此，设计了hiddev接口。更多相关信息，请参阅`Documentation/hid/hiddev.rst`。

`usbhid` 模块的使用非常简单，无需任何参数即可自动检测一切。当插入HID设备时，它会适当地检测到该设备。然而，由于设备种类繁多，您可能会遇到某些设备无法正常工作的情况。如果出现这种情况，请在`hid-core.c`文件的开头定义`DEBUG`宏，并将系统日志跟踪信息发送给我。

usbmouse
~~~~~~~~

对于嵌入式系统、带有错误HID描述符的鼠标或其他不适合使用大型`usbhid`驱动的情况，可以使用`usbmouse`驱动程序。它仅处理USB鼠标，并采用更简单的HIDBP协议。这也意味着这些鼠标必须支持这种更简单的协议。并非所有鼠标都支持。如果您没有特别的理由使用此模块，请选择`usbhid`。

usbkbd
~~~~~~

与`usbmouse`类似，此模块通过简化的HIDBP协议与键盘通信。它的体积较小，但不支持任何额外的特殊按键。如果没有特别的原因，请使用`usbhid`。
### psmouse

这是一个适用于所有使用PS/2协议的指针设备的驱动程序，包括Synaptics和ALPS触摸板、Intellimouse Explorer设备、Logitech PS/2鼠标等。

### atkbd

这是一个适用于PS/2（AT）键盘的驱动程序。

### iforce

这是一个适用于I-Force操纵杆和方向盘的驱动程序，支持通过USB和RS232接口。现在它还包括力反馈支持，尽管Immersion Corp.认为该协议是商业秘密，并且不愿意透露任何信息。

### 验证是否工作

在键盘上敲几个键就足以检查键盘是否工作并且正确连接到内核键盘驱动程序。
执行`cat /dev/input/mouse0`（主设备号13，次设备号32）可以验证鼠标是否也被模拟；如果你移动鼠标，应该会看到字符出现。
你可以使用`jstest`工具来测试操纵杆模拟功能，该工具包含在操纵杆包中（参见 :ref:`joystick-doc`）。
你可以使用`evtest`工具来测试事件设备。
.. _event-interface:

### 事件接口

你可以对`/dev/input/eventX`设备进行阻塞读取和非阻塞读取，也可以使用select()。每次读取时你都会得到一个完整的输入事件数量。它们的布局如下：

```c
struct input_event {
    struct timeval time;
    unsigned short type;
    unsigned short code;
    unsigned int value;
};
```

`time` 是时间戳，表示事件发生的时间。
`type` 例如EV_REL表示相对运动，EV_KEY表示按键或释放。更多类型定义在`include/uapi/linux/input-event-codes.h`中。
``code`` 是事件代码，例如 REL_X 或 KEY_BACKSPACE，完整列表可以在 include/uapi/linux/input-event-codes.h 中找到。
``value`` 是事件携带的值。对于 EV_REL，它是相对变化值；对于 EV_ABS（如操纵杆等），它是绝对新值；对于 EV_KEY，释放时为 0，按键时为 1，自动重复时为 2。

更多关于各种事件代码的信息，请参见 :ref:`input-event-codes`。
