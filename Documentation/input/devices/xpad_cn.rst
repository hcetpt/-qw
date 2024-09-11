=======================================
xpad - 适用于 Xbox 兼容控制器的 Linux USB 驱动
=======================================

此驱动程序支持所有第一方和第三方的 Xbox 兼容控制器。它有着悠久的历史，并且由于 Windows 的 xinput 库使得大多数 PC 游戏都专注于 Xbox 控制器的兼容性，因此得到了广泛的使用。
由于向后兼容性，所有按钮都被报告为数字信号。这仅影响原始 Xbox 控制器。所有后续的控制器型号只有数字面部按钮。
部分 Xbox 360 控制器型号支持震动功能，但原始 Xbox 控制器和 Xbox One 控制器不支持。截至撰写本文时，Xbox One 的震动协议尚未被逆向工程，但在未来可能会得到支持。

注意事项
=====

报告的按钮/轴的数量根据以下三个方面而变化：

- 是否使用已知控制器
- 是否使用已知的跳舞垫
- 如果使用未知设备（未列在下面），你在模块配置中设置的“将方向键映射到按钮而不是轴上”（模块选项 dpad_to_buttons）

如果你将 dpad_to_buttons 设置为 N 并且你正在使用未知设备，该驱动程序会将方向键映射到轴（X/Y）。
如果你将其设置为 Y，则会将方向键映射到按钮，这对于跳舞类游戏的正常运行是必需的。默认值为 Y。
对于已知的跳舞垫，dpad_to_buttons 没有作用。一个错误的提交信息声称 dpad_to_buttons 可以用于强制在已知设备上的行为，这是不正确的。dpad_to_buttons 和 triggers_to_buttons 只影响未知控制器。

普通控制器
------------------

对于普通控制器，方向键被映射为其独立的 X/Y 轴。
joystick-1.2.15 版本中的 jstest 程序（jstest 版本 2.1.0）将报告 8 个轴和 10 个按钮。
所有8个轴都能工作，不过它们的范围都相同（-32768到32767），触发器的零点设置不正确（我不知道这是否是jstest的限制，因为输入设备的设置应该是正确的。我还没有查看jstest本身）。

所有的10个按钮都能工作（在数字模式下）。右侧的六个按钮（A、B、X、Y、黑色、白色）被称作“模拟”按钮，并且以8位无符号数值报告其值，不确定这有什么用途。

我在Quake3中测试了控制器，配置和游戏中的功能都正常。然而，我发现用游戏手柄玩第一人称射击游戏相当困难。效果因人而异。

Xbox 舞蹈垫
--------------

使用已知的舞蹈垫时，jstest会报告6个轴和14个按钮。
对于舞蹈风格的垫子（如redoctane垫），已经进行了多项更改。旧驱动程序会将方向键映射为轴，导致当用户同时按下左右或上下时，驱动程序无法报告，从而使DDR风格的游戏无法游玩。
已知的舞蹈垫会自动将方向键映射为按钮，并且开箱即用。
如果你的舞蹈垫被驱动程序识别但使用的是轴而不是按钮，请参阅第0.3节——未知控制器。

我已经用Stepmania进行了测试，效果非常好。

未知控制器
-------------

如果你有一个未知的Xbox控制器，默认设置下应该可以正常使用。
但是，如果你有一个未列在下面的未知舞蹈垫，除非你在模块配置中将“dpad_to_buttons”设置为1，否则它将无法工作。

USB适配器
=============

所有代别的Xbox控制器通过USB进行通信。
原始的Xbox控制器使用专有连接器，需要适配器
- 无线Xbox 360控制器需要一个“Xbox 360 无线游戏接收器 for Windows”
- 有线Xbox 360控制器使用标准的USB连接器
- Xbox One控制器可以是无线的，但使用的是Wi-Fi Direct，并且尚未得到支持
- Xbox One控制器可以是有线的，并使用标准的Micro-USB连接器

原始Xbox USB适配器
--------------------------

使用此驱动程序与原始的Xbox控制器时，需要一个适配器电缆将专有连接器的引脚转为USB。你可以在线上以较低的价格购买这种适配器电缆，或者自己制作。
制作这样的电缆其实非常简单。控制器本身是一个复合USB设备（一个带有三个端口的集线器，用于两个扩展槽和控制器设备），唯一的区别在于非标准的连接器（5个引脚对标准USB 1.0连接器的4个引脚）。
你只需要在电缆上焊接一个USB连接器，并保持黄色电线不连接。其他引脚在两个连接器上的顺序是一样的，因此没有什么特别之处。关于这些事项的详细信息可以在网上找到([1]_, [2]_, [3]_)。
由于电缆上有一个三通分接头，你甚至不需要切断原来的电缆。你可以购买一根延长电缆并切断它。这样，如果你有一台Xbox的话，你仍然可以使用该控制器。

驱动安装
===================

一旦你有了适配器电缆（如果需要的话）并连接了控制器，xpad模块应该会自动加载。要确认这一点，你可以查看`/sys/kernel/debug/usb/devices`。应该会有如下条目：

.. code-block:: none
   :caption: InterAct PowerPad Pro (德国)的信息输出

    T:  Bus=01 Lev=03 Prnt=04 Port=00 Cnt=01 Dev#=  5 Spd=12  MxCh= 0
    D:  Ver= 1.10 Cls=00(>ifc ) Sub=00 Prot=00 MxPS=32 #Cfgs=  1
    P:  Vendor=05fd ProdID=107a Rev= 1.00
    C:* #Ifs= 1 Cfg#= 1 Atr=80 MxPwr=100mA
    I:  If#= 0 Alt= 0 #EPs= 2 Cls=58(unk. ) Sub=42 Prot=00 Driver=(none)
    E:  Ad=81(I) Atr=03(Int.) MxPS=  32 Ivl= 10ms
    E:  Ad=02(O) Atr=03(Int.) MxPS=  32 Ivl= 10ms

.. code-block:: none
   :caption: Redoctane Xbox Dance Pad (美国)的信息输出

    T:  Bus=01 Lev=02 Prnt=09 Port=00 Cnt=01 Dev#= 10 Spd=12  MxCh= 0
    D:  Ver= 1.10 Cls=00(>ifc ) Sub=00 Prot=00 MxPS= 8 #Cfgs=  1
    P:  Vendor=0c12 ProdID=8809 Rev= 0.01
    S:  Product=XBOX DDR
    C:* #Ifs= 1 Cfg#= 1 Atr=80 MxPwr=100mA
    I:  If#= 0 Alt= 0 #EPs= 2 Cls=58(unk. ) Sub=42 Prot=00 Driver=xpad
    E:  Ad=82(I) Atr=03(Int.) MxPS=  32 Ivl=4ms
    E:  Ad=02(O) Atr=03(Int.) MxPS=  32 Ivl=4ms

支持的控制器
=====================

对于支持的控制器及其关联的供应商和产品ID，请参见xpad_device[]数组\[4\]
截至历史版本0.0.6（2006年10月10日），以下设备得到了支持：

- 原始微软Xbox控制器（美国），供应商=0x045e，产品=0x0202
- 较小的微软Xbox控制器（美国），供应商=0x045e，产品=0x0289
- 原始微软Xbox控制器（日本），供应商=0x045e，产品=0x0285
- InterAct PowerPad Pro（德国），供应商=0x05fd，产品=0x107a
- RedOctane Xbox Dance Pad（美国），供应商=0x0c12，产品=0x8809

未识别的Xbox控制器型号应作为通用Xbox控制器工作。未识别的Dance Pad控制器需要设置模块选项'dpad_to_buttons'。
如果你有未识别的控制器，请参阅 0.3 - 未知控制器

手动测试
=================

要测试此驱动程序的功能，你可以使用 'jstest'
例如：

    > modprobe xpad
    > modprobe joydev
    > jstest /dev/js0

如果你使用的是普通控制器，应该会显示一行包含 18 个输入（8 个轴，10 个按钮），并且当你移动摇杆和按下按钮时，其值会发生变化。如果你使用的是舞蹈垫，它应该显示 20 个输入（6 个轴，14 个按钮）。
如果能正常工作？恭喜，你完成了；）

感谢
======

我要感谢 ITO Takayuki 在他的网站上提供了详细的资料：
    http://euc.jp/periphs/xbox-controller.ja.html
他提供的有用信息以及 usb-skeleton 和 iforce 输入驱动（Greg Kroah-Hartmann；Vojtech Pavlik）对快速原型化基本功能帮助很大。

参考文献
==========

.. [1] http://euc.jp/periphs/xbox-controller.ja.html （ITO Takayuki）
.. [2] http://xpad.xbox-scene.com/
.. [3] http://www.markosweb.com/www/xboxhackz.com/
.. [4] https://elixir.bootlin.com/linux/latest/ident/xpad_device

历史编辑
==============

2002-07-16 - Marko Friedemann <mfr@bmx-chemnitz.de>
 - 原始文档

2005-03-19 - Dominic Cerquetti <binary1230@yahoo.com>
 - 添加了关于舞蹈垫的内容，新的方向键到轴的映射

后续更改可以通过以下命令查看：
'git log --follow Documentation/input/devices/xpad.rst'
