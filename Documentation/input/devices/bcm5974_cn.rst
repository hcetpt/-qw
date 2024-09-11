.. include:: <isonum.txt>

------------------------
BCM5974 驱动程序 (bcm5974)
------------------------

:版权: |copy| 2008-2009 Henrik Rydberg <rydberg@euromail.se>

USB 初始化和数据包解码是由 Scott Shawcroft 在 touchd 用户空间驱动项目中完成的：

:版权: |copy| 2008 Scott Shawcroft (scott.shawcroft@gmail.com)

BCM5974 驱动程序基于 appletouch 驱动程序：

:版权: |copy| 2001-2004 Greg Kroah-Hartman (greg@kroah.com)
:版权: |copy| 2005 Johannes Berg (johannes@sipsolutions.net)
:版权: |copy| 2005 Stelian Pop (stelian@popies.net)
:版权: |copy| 2005 Frank Arnold (frank@scirocco-5v-turbo.de)
:版权: |copy| 2005 Peter Osterlund (petero2@telia.com)
:版权: |copy| 2005 Michael Hanselmann (linux-kernel@hansmi.ch)
:版权: |copy| 2006 Nicolas Boichat (nicolas@boichat.ch)

该驱动程序增加了对新款 Apple MacBook Air 和 MacBook Pro 笔记本电脑上的多点触控板的支持。它在这些计算机上替换了 appletouch 驱动程序，并且与 Xorg 系统的 synaptics 驱动程序很好地集成。
已知可以在 MacBook Air、MacBook Pro Penryn 以及新款一体式 MacBook 5 和 MacBook Pro 5 上工作。

使用说明
-----

该驱动程序会自动加载支持的 USB 设备 ID，并作为事件设备（/dev/input/event*）和通过 mousedev 驱动程序提供的鼠标（/dev/input/mice）可用。

USB 竞态条件
------------

Apple 多点触控板通过同一个 USB 设备的不同接口报告鼠标和键盘事件。这与 HID 驱动程序产生了竞态条件，如果未被告知其他情况，HID 驱动程序将会发现标准的 HID 鼠标和键盘，并声称拥有整个设备。为了解决这个问题，必须将 USB 产品 ID 列入 HID 驱动程序的 mouse_ignore 列表中。

调试输出
------------

为了便于新硬件版本的开发，可以通过 debug 内核模块参数启用详细的包输出。范围 [1-9] 提供了不同的详细程度。示例（以 root 用户身份执行）：

```sh
echo -n 9 > /sys/module/bcm5974/parameters/debug
tail -f /var/log/debug
echo -n 0 > /sys/module/bcm5974/parameters/debug
```

趣闻
------

该驱动程序是在 2008 年 6 月的 Ubuntu 论坛上开发的 [#f1]_，现在有了一个更永久的家在 bitmath.org [#f2]_

.. 链接

.. [#f1] http://ubuntuforums.org/showthread.php?t=840040
.. [#f2] http://bitmath.org/code/
