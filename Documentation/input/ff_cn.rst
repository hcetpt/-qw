========================
Linux下的力反馈
========================

:作者: Johann Deneux <johann.deneux@gmail.com> 于 2001/04/22
:更新: Anssi Hannula <anssi.hannula@gmail.com> 于 2006/04/09
您可以重新分发此文件。请记得包含shape.svg和interactive.svg文件。

简介
~~~~~~~~~~~~

本文档描述了如何在Linux下使用力反馈设备。目标不是将这些设备简单地作为输入设备来支持（这已经可以实现），而是真正启用力效果的渲染。
本文档仅描述Linux输入接口中的力反馈部分。在继续阅读之前，请先阅读joydev/joystick.rst和input.rst。

用户指南
~~~~~~~~~~~~~~~~~~~~~~~~

要启用力反馈，您需要：

1. 配置内核以使用evdev以及支持您的设备的驱动程序
2. 确保已加载evdev模块，并创建了/dev/input/event*设备文件

在开始之前，请注意，某些设备在初始化阶段可能会剧烈震动。例如，我的“AVB Top Shot Pegasus”就会出现这种情况。
为了停止这种烦人的行为，请将您的操纵杆移动到其极限位置。无论如何，您应该始终用手握住设备，以防万一出现问题导致设备损坏。

如果您有一个串行iforce设备，则需要启动inputattach。详细信息请参见joydev/joystick.rst。
它是否有效？
--------------

有一个名为 `fftest` 的工具，可以让你测试驱动程序：

    % fftest /dev/input/eventXX

给开发者的说明
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

所有交互都是通过事件API进行的。也就是说，你可以使用 ioctl() 和 write() 操作 `/dev/input/eventXX`
此信息可能会发生变化
查询设备功能
----------------------------

```
#include <linux/input.h>
#include <sys/ioctl.h>

#define BITS_TO_LONGS(x) \
	(((x) + 8 * sizeof (unsigned long) - 1) / (8 * sizeof (unsigned long)))
unsigned long features[BITS_TO_LONGS(FF_CNT)];
int ioctl(int file_descriptor, int request, unsigned long *features);
```

"request" 必须是 `EVIOCGBIT(EV_FF, features 数组大小（以字节为单位）)`。

返回设备支持的功能。`features` 是一个位字段，其中包含以下位：

- FF_CONSTANT 可以渲染恒定力效果
- FF_PERIODIC 可以渲染具有以下波形的周期性效果：
  
  - FF_SQUARE 方波
  - FF_TRIANGLE 三角波
  - FF_SINE 正弦波
  - FF_SAW_UP 上升锯齿波
  - FF_SAW_DOWN 下降锯齿波
  - FF_CUSTOM 自定义波形

- FF_RAMP 可以渲染渐变效果
- FF_SPRING 可以模拟弹簧的存在
- FF_FRICTION 可以模拟摩擦力
- FF_DAMPER 可以模拟阻尼效果
- FF_RUMBLE 震动效果
- FF_INERTIA 可以模拟惯性
- FF_GAIN 增益可调
- FF_AUTOCENTER 自动回中可调

.. note::
    
    - 在大多数情况下，你应该使用 FF_PERIODIC 而不是 FF_RUMBLE。所有支持 FF_RUMBLE 的设备也支持 FF_PERIODIC（方波、三角波、正弦波），反之亦然。
- 目前 FF_CUSTOM 的确切语法尚未定义，因为还没有驱动程序支持它。
```
int ioctl(int fd, EVIOCGEFFECTS, int *n);
```

返回设备内存中可以保存的效果数量
上传效果到设备
-------------------------------

```
#include <linux/input.h>
#include <sys/ioctl.h>

int ioctl(int file_descriptor, int request, struct ff_effect *effect);
```

"request" 必须是 `EVIOCSFF`
"effect" 指向一个描述要上传的效果的结构体。效果被上传，但不播放
`effect` 的内容可能会被修改。特别是，其 "id" 字段会被驱动程序设置为唯一的ID。这些数据对于执行某些操作（如移除效果或控制播放）是必需的
用户必须将 "id" 字段设置为 -1，以便告诉驱动程序分配一个新的效果
效果是文件描述符特定的
参见 `<uapi/linux/input.h>` 中对 `ff_effect` 结构的描述。您还可以在 `shape.svg` 和 `interactive.svg` 文件中找到一些示例：

.. kernel-figure:: shape.svg

    形状

.. kernel-figure:: interactive.svg

    交互式

从设备中移除效果
------------------

```
int ioctl(int fd, EVIOCRMFF, effect.id);
```

这为设备内存中的新效果腾出空间。请注意，如果效果正在播放，此操作也会停止该效果。

控制效果的播放
----------------

播放控制通过 `write()` 实现。下面是一个示例：

```
#include <linux/input.h>
#include <unistd.h>

struct input_event play;
struct input_event stop;
struct ff_effect effect;
int fd;
..
fd = open("/dev/input/eventXX", O_RDWR);
..
/* 播放三次 */
play.type = EV_FF;
play.code = effect.id;
play.value = 3;

write(fd, (const void*) &play, sizeof(play));
..
/* 停止一个效果 */
stop.type = EV_FF;
stop.code = effect.id;
stop.value = 0;

write(fd, (const void*) &stop, sizeof(stop));
```

设置增益
------------

并非所有设备的强度都相同。因此，用户应根据所需的效果强度设置增益因子。此设置在访问驱动程序时是持久化的。

```
/* 设置设备的增益
int gain;         /* 在 0 到 100 之间 */
struct input_event ie;      /* 用于与驱动程序通信的结构 */

ie.type = EV_FF;
ie.code = FF_GAIN;
ie.value = 0xFFFFUL * gain / 100;

if (write(fd, &ie, sizeof(ie)) == -1)
    perror("set gain");
```

启用/禁用自动居中
----------------------

在我看来，自动居中功能会干扰效果的渲染，并且我认为它应该是一个取决于游戏类型的效果。但如果您想启用它，可以这样做：

```
int autocenter;       /* 在 0 到 100 之间 */
struct input_event ie;

ie.type = EV_FF;
ie.code = FF_AUTOCENTER;
ie.value = 0xFFFFUL * autocenter / 100;

if (write(fd, &ie, sizeof(ie)) == -1)
    perror("set auto-center");
```

值为 0 表示“无自动居中”。

动态更新效果
----------------

按上传新效果的方式进行，只是将 `id` 字段设置为您想要的效果 ID 而不是 -1。

通常情况下，效果不会被停止和重新启动。但是，根据设备的类型，并非所有参数都可以动态更新。例如，使用 iforce 设备时无法更新效果的方向。在这种情况下，驱动程序会停止效果、上传它并重新启动它。

因此，在效果播放过程中仅当重新启动效果时重播计数为 1 是可接受的情况下，才建议动态更改方向。
关于效果状态的信息
---------------------------------------

每当效果的状态发生变化时，会发送一个事件。事件字段的值和含义如下：

    struct input_event {
    /* 效果状态改变的时间 */
	    struct timeval time;

    /* 设置为 EV_FF_STATUS */
	    unsigned short type;

    /* 包含效果的 ID */
	    unsigned short code;

    /* 指示状态 */
	    unsigned int value;
    };

    FF_STATUS_STOPPED	效果停止播放
    FF_STATUS_PLAYING	效果开始播放

.. note::

    - 状态反馈仅由 iforce 驱动支持。如果您有充分的理由需要使用此功能，请联系
      linux-joystick@atrey.karlin.mff.cuni.cz 或 anssi.hannula@gmail.com，
      以便将此功能的支持添加到其他驱动程序中。
