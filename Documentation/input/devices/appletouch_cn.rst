```markdown
.. include:: <isonum.txt>

----------------------------------
苹果触控板驱动（appletouch）
----------------------------------

:版权: |copy| 2005 Stelian Pop <stelian@popies.net>

appletouch 是一个针对2005年2月和10月之后的苹果铝制Powerbook中USB触控板的Linux内核驱动。此驱动源自Johannes Berg的appletrackpad驱动程序 [#f1]_，但已经进行了改进：

    * appletouch 是一个完整的内核驱动，不需要用户空间程序
    * appletouch 可以与X11的synaptics驱动接口，以便实现触控板加速、滚动等功能

感谢Johannes Berg逆向工程了触控板协议，Frank Arnold进一步改进，以及Alex Harper提供了关于触控板传感器内部工作原理的一些额外信息。Michael Hanselmann添加了对2005年10月型号的支持。
使用方法
-----

为了在基本模式下使用触控板，请编译驱动并加载模块。系统将检测到一个新的输入设备，并且可以从 /dev/input/mice 读取鼠标数据（使用gpm或X11）。

在X11中，可以配置触控板使用synaptics X11驱动，这样会提供额外的功能，如加速、滚动、双指点击模拟中键、三指点击模拟右键等。为此，请确保使用的是synaptics驱动的较新版本（测试过0.14.2版本，可从 [#f2]_ 获取），并在X11配置文件中配置一个新的输入设备（下面是一个示例）。更多配置参见synaptics驱动文档：

```plaintext
Section "InputDevice"
    Identifier      "Synaptics Touchpad"
    Driver          "synaptics"
    Option          "SendCoreEvents"        "true"
    Option          "Device"                "/dev/input/mice"
    Option          "Protocol"              "auto-dev"
    Option		"LeftEdge"		"0"
    Option		"RightEdge"		"850"
    Option		"TopEdge"		"0"
    Option		"BottomEdge"		"645"
    Option		"MinSpeed"		"0.4"
    Option		"MaxSpeed"		"1"
    Option		"AccelFactor"		"0.02"
    Option		"FingerLow"		"0"
    Option		"FingerHigh"		"30"
    Option		"MaxTapMove"		"20"
    Option		"MaxTapTime"		"100"
    Option		"HorizScrollDelta"	"0"
    Option		"VertScrollDelta"	"30"
    Option		"SHMConfig"		"on"
EndSection

Section "ServerLayout"
    ..
    InputDevice	"Mouse"
    InputDevice	"Synaptics Touchpad"
    ..
EndSection
```

噪声问题
-------------

触控板传感器对温度非常敏感，在温度变化时会产生大量噪声。特别是在首次启动笔记本电脑时尤为明显。

appletouch驱动试图处理这种噪声并自动适应，但这并不完美。如果手指移动无法识别，请尝试重新加载驱动。

可以通过 'debug' 模块参数激活调试。值为0表示不进行任何调试，1表示跟踪无效样本，2表示完全跟踪（每个样本都被跟踪）：

```plaintext
modprobe appletouch debug=1
```

或者：

```plaintext
echo "1" > /sys/module/appletouch/parameters/debug
```

.. 链接:

.. [#f1] http://johannes.sipsolutions.net/PowerBook/touchpad/

.. [#f2] `<http://web.archive.org/web/*/http://web.telia.com/~u89404340/touchpad/index.html>`_
```
