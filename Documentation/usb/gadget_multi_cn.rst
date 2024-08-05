==============================
多功能复合小工具
==============================

概述
========

多功能复合小工具（或 g_multi）是一种复合小工具，它充分利用了复合框架来提供一个……多功能小工具。在标准配置下，它提供了一个单一的USB配置，包括RNDIS[1]（即以太网）、USB CDC[2] ACM（即串行）和USB大容量存储功能。
可以通过Kconfig选项开启CDC ECM（以太网）功能，并可以关闭RNDIS。如果两者都启用，则该小工具有两种配置——一种带有RNDIS，另一种带有CDC ECM[3]。
请注意，如果您使用非标准配置（即启用CDC ECM），您可能需要更改供应商和/或产品ID。
主机驱动程序
============

要利用这个小工具，您需要让它在主机端工作——否则无法期望通过该小工具实现任何功能。正如人们所预料的那样，需要执行的操作因系统而异。
Linux主机驱动程序
------------------

由于该小工具使用的是标准复合框架，并且对Linux主机而言表现为这样的框架，因此在Linux主机端不需要任何额外的驱动程序。所有功能都由为此开发的相应驱动程序处理。
对于具有两个配置设置的RNDIS配置作为第一个配置的情况也是如此。Linux主机将使用第二个CDC ECM配置，这在Linux下应该表现得更好。
Windows主机驱动程序
-------------------

为了让该小工具在Windows下工作，必须满足以下两个条件：

检测为复合小工具
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

首先，Windows需要将该小工具识别为USB复合小工具，而这本身有一些条件[4]。如果这些条件得到满足，Windows会让USB通用父驱动程序[5]处理该设备，然后尝试为每个单独接口匹配驱动程序（大致如此，不深入过多细节）。
好消息是：您不必担心大多数条件！

唯一需要担心的是，该小工具必须有一个单一的配置，所以除非您创建一个合适的INF文件并提交它，否则同时具有RNDIS和CDC ECM的双重配置的小工具将无法工作！

为每个功能安装驱动程序
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

另一个更棘手的事情是让Windows为每个单独的功能安装驱动程序。
对于大量存储来说，这很简单，因为Windows会检测到这是一个实现了USB大量存储类的接口，并选择合适的驱动程序。
对于RNDIS和CDC ACM来说事情就变得复杂一些。
RNDIS
....
为了让Windows为gadget中的第一个功能选择RNDIS驱动程序，你需要使用与本文档一起提供的[[文件:linux.inf]]文件。它将Windows的RNDIS驱动程序“绑定”到了gadget的第一个接口上。
请注意，在测试过程中，当RNDIS不是第一个接口时，我们遇到了一些问题[6]。除非你正试图开发自己的gadget，否则你不必担心这个问题，请注意这个bug。
CDC ACM
......
同样地，提供了[[文件:linux-cdc-acm.inf]]用于CDC ACM。
自定义gadget
.....................
如果你打算修改g_multi gadget，请注意重新排列功能显然会改变每个功能的接口编号。结果是，提供的INF文件将无法工作，因为它们在内部硬编码了接口编号（不过更改这些编号并不难[7]）。
这也意味着，在对g_multi进行实验并更改提供的功能之后，应该更改gadget的供应商ID和/或产品ID，以避免与其他定制的gadget或原始gadget发生冲突。
未能遵守上述指示可能会让你在疑惑为何事情没有如预期那样进行数小时后才意识到Windows已经缓存了一些驱动程序信息，从而导致脑损伤（换用不同的USB端口有时会有帮助，此外你可以尝试使用USBDeview[8]来移除那些幽灵设备）。
INF文件测试
..........
提供的INF文件已在Windows XP SP3、Windows Vista以及Windows 7的所有32位版本上进行了测试。这些文件在64位版本上也应该可以正常工作。但在Windows XP SP2之前的版本上很可能无法正常运行。
其他系统
-------------

目前尚未对任何其他系统的驱动程序进行过测试。
考虑到MacOS基于BSD而BSD是开源的，我们相信它应该能够直接运行（注：我并不确定这是否可行）。
对于更为特殊的操作系统，我了解得更少。
欢迎进行任何测试及提供驱动程序！

作者
=======

本文档由Michal Nazarewicz撰写（[[mailto:mina86@mina86.com]]）。INF文件是在Marek Szyprowski（[[mailto:m.szyprowski@samsung.com]]）和Xiaofan Chen（[[mailto:xiaofanc@gmail.com]]）的支持下，基于MS RNDIS模板[9]、Microchip的CDC ACM INF文件以及David Brownell（[[mailto:dbrownell@users.sourceforge.net]]）原始INF文件的基础上开发的。
脚注
=========

[1] 远程网络驱动接口规范，
[[https://msdn.microsoft.com/en-us/library/ee484414.aspx]]
[2] 通信设备类抽象控制模型，该USB类以及其他USB类的规格可以在
[[http://www.usb.org/developers/devclass_docs/]] 找到
[3] CDC以太网控制模型
Here's the translation into Chinese:

[4] [[https://msdn.microsoft.com/en-us/library/ff537109(v=VS.85).aspx]]

[5] [[https://msdn.microsoft.com/en-us/library/ff539234(v=VS.85).aspx]]

[6] 用更委婉的话来说，就是Windows未能对任何用户输入做出响应。
[7] 您可能会觉得[[http://www.cygnal.org/ubb/Forum9/HTML/001050.html]]很有用。
[8] https://www.nirsoft.net/utils/usb_devices_view.html

[9] [[https://msdn.microsoft.com/en-us/library/ff570620.aspx]]
