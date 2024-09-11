.. include:: <isonum.txt>

.. _joystick-doc:

简介
============

Linux 的摇杆驱动程序支持各种摇杆和类似设备。它是基于一个更大的项目，旨在支持 Linux 中的所有输入设备。
该项目的邮件列表为：

	linux-input@vger.kernel.org

要订阅，请发送 "subscribe linux-input" 到 majordomo@vger.kernel.org
使用
=====

对于基本使用，您只需在内核配置中选择正确的选项即可。
工具
---------

为了测试和其他目的（例如串行设备），有一组工具，如 `jstest`、`jscal` 和 `evtest`，通常以 `joystick`、`input-utils`、`evtest` 等的形式打包。
如果您的摇杆连接到串行端口，则需要 `inputattach` 工具。
设备节点
------------

为了让应用程序能够使用摇杆，应在 `/dev` 目录下创建设备节点。通常系统会自动完成这项工作，但也可以手动完成：

    cd /dev
    rm js*
    mkdir input
    mknod input/js0 c 13 0
    mknod input/js1 c 13 1
    mknod input/js2 c 13 2
    mknod input/js3 c 13 3
    ln -s input/js0 js0
    ln -s input/js1 js1
    ln -s input/js2 js2
    ln -s input/js3 js3

为了与 `inpututils` 进行测试，创建这些节点也很方便：

    mknod input/event0 c 13 64
    mknod input/event1 c 13 65
    mknod input/event2 c 13 66
    mknod input/event3 c 13 67

所需的模块
--------------

为了让所有摇杆驱动程序正常工作，您需要加载或编译内核中的用户空间接口模块：

	modprobe joydev

对于游戏端口摇杆，您还需要加载游戏端口驱动程序：

	modprobe ns558

对于串行端口摇杆，您需要加载串行输入线路纪律模块，并启动 `inputattach` 工具：

	modprobe serport
	inputattach -xxx /dev/tts/X &

此外，您还需要摇杆驱动程序模块本身，通常您将有一个模拟摇杆：

	modprobe analog

对于自动模块加载，可以使用以下命令 - 根据您的需求进行调整：

	alias tty-ldisc-2 serport
	alias char-major-13 input
	above input joydev ns558 analog
	options analog map=gamepad,none,2btn

验证其是否工作
-----------------------

要测试摇杆驱动程序的功能，可以在工具包中使用 `jstest` 程序。运行该程序的方法是：

	jstest /dev/input/js0

它应该显示一条带有摇杆值的行，当您移动摇杆或按下按钮时，这些值会更新。当摇杆位于中心位置时，所有轴都应为零。它们不应自行抖动至其他接近值，在摇杆的任何其他位置也应保持稳定。它们的范围应从 -32767 到 32767。如果满足所有这些条件，则一切正常，您可以玩游戏了。

如果不满足这些条件，可能存在一个问题。尝试校准摇杆，如果仍然不起作用，请阅读本文件的驱动程序部分、故障排除部分以及常见问题解答。
校准
-----------

对于大多数摇杆，您不需要手动校准，因为摇杆应由驱动程序自动校准。但是，对于一些不使用线性电阻的模拟摇杆，或者如果您想要更高的精度，可以使用 `jscal` 程序：

	jscal -c /dev/input/js0

包含在摇杆包中，用于设置比驱动程序自己选择的更好的校正系数。
校准摇杆后，可以使用 `jstest` 命令验证新校准是否满意，如果满意，则可以将校正系数保存到文件中：

	jscal -p /dev/input/js0 > /etc/joystick.cal

并在您的启动脚本中添加执行该文件的行：

	source /etc/joystick.cal

这样，在下次重新启动后，您的摇杆将保持已校准状态。您还可以将 `jscal -p` 行添加到您的关机脚本中。
硬件特定驱动信息
====================

在此部分中描述了每个单独的硬件特定驱动程序。
模拟摇杆
----------------

`analog.c` 驱动程序使用游戏端口的标准模拟输入，因此支持所有标准摇杆和游戏手柄。它使用了一个非常先进的算法，提供了其他任何系统都无法提供的数据精度。
它还支持诸如与CH Flightstick Pro、ThrustMaster FCS或6和8按钮游戏手柄兼容的附加帽和按钮。Saitek Cyborg '数字' 操纵杆也由该驱动程序支持，因为它们基本上是加强版的CHF操纵杆。
然而，只有以下类型可以自动检测：

* 2轴4按钮操纵杆
* 3轴4按钮操纵杆
* 4轴4按钮操纵杆
* Saitek Cyborg '数字' 操纵杆

对于其他类型的操纵杆（更多或更少的轴、帽和按钮），您需要在内核命令行或插入analog模块到内核时指定类型。参数如下：

	analog.map=<type1>,<type2>,<type3>,...

'type' 是下表中定义的操纵杆类型，表示系统中的游戏端口上的操纵杆，从gameport0开始，第二个'type'条目定义gameport1上的操纵杆，以此类推。
========= =====================================================
 Type      含义
	========= =====================================================
 none      该端口上没有模拟操纵杆
 auto      自动检测操纵杆
 2btn      2按钮n轴操纵杆
 y-joy     通过Y线连接的两个2按钮2轴操纵杆
 y-pad     通过Y线连接的两个2按钮2轴游戏手柄
 fcs       Thrustmaster FCS兼容操纵杆
 chf       具有CH Flightstick兼容帽的操纵杆
 fullchf   具有两个帽和6个按钮的CH Flightstick兼容操纵杆
 gamepad   4/6按钮n轴游戏手柄
 gamepad8  8按钮2轴游戏手柄
	========= =====================================================

如果您的操纵杆不符合上述任何类别，您可以使用下表中的位组合来指定类型。除非您确实知道自己在做什么，否则不建议这样做。这并不危险，但也不简单。
==== =========================
 Bit  含义
 ==== =========================
  0   轴X1
  1   轴Y1
  2   轴X2
  3   轴Y2
  4   按钮A
  5   按钮B
  6   按钮C
  7   按钮D
  8   CHF按钮X和Y
  9   CHF帽1
 10   CHF帽2
 11   FCS帽
 12   手柄按钮X
 13   手柄按钮Y
 14   手柄按钮U
 15   手柄按钮V
 16   Saitek F1-F4按钮
 17   Saitek数字模式
 19   游戏手柄
 20   Joy2轴X1
 21   Joy2轴Y1
 22   Joy2轴X2
 23   Joy2轴Y2
 24   Joy2按钮A
 25   Joy2按钮B
 26   Joy2按钮C
 27   Joy2按钮D
 31   Joy2游戏手柄
 ==== =========================

Microsoft SideWinder操纵杆
------------------------------

Microsoft 'Digital Overdrive'协议由sidewinder.c模块支持。所有当前支持的操纵杆：

* Microsoft SideWinder 3D Pro
* Microsoft SideWinder Force Feedback Pro
* Microsoft SideWinder Force Feedback Wheel
* Microsoft SideWinder FreeStyle Pro
* Microsoft SideWinder GamePad（最多四个，串联）
* Microsoft SideWinder Precision Pro
* Microsoft SideWinder Precision Pro USB

均被自动检测，因此无需模块参数。
3D Pro有一个问题。尽管该操纵杆只有8个按钮，但报告了9个按钮。第9个按钮是操纵杆背面的模式切换。然而，移动它会使操纵杆重置，并使其大约三分之一秒内无响应。此外，操纵杆还会重新居中，将这段时间内的位置作为新的中心位置。如果您想使用它，请先考虑清楚。
SideWinder Standard不是数字操纵杆，因此由上述模拟驱动程序支持。

Logitech ADI设备
--------------------

Logitech ADI协议由adi.c模块支持。它应该支持任何使用此协议的Logitech设备。这包括但不限于：

* Logitech CyberMan 2
* Logitech ThunderPad Digital
* Logitech WingMan Extreme Digital
* Logitech WingMan Formula
* Logitech WingMan Interceptor
* Logitech WingMan GamePad
* Logitech WingMan GamePad USB
* Logitech WingMan GamePad Extreme
* Logitech WingMan Extreme Digital 3D

ADI设备被自动检测，并且驱动程序支持在一个游戏端口上使用一个Y线或串联连接的最多两个设备（任意组合）。
Logitech WingMan Joystick、Logitech WingMan Attack、Logitech WingMan Extreme和Logitech WingMan ThunderPad不是数字操纵杆，并由上述模拟驱动程序处理。Logitech WingMan Warrior和Logitech Magellan由下面描述的串行驱动程序支持。Logitech WingMan Force和Logitech WingMan Formula Force由下面描述的I-Force驱动程序支持。Logitech CyberMan尚未得到支持。

Gravis GrIP
-----------

Gravis GrIP协议由grip.c模块支持。目前支持以下设备：

* Gravis GamePad Pro
* Gravis BlackHawk Digital
* Gravis Xterminator
* Gravis Xterminator DualControl

所有这些设备均被自动检测，您甚至可以在一个游戏端口上使用最多两个这些手柄的任意组合，无论是串联还是使用Y线。
GrIP MultiPort 尚未得到支持。Gravis Stinger 是一个串行设备，并且由 stinger 驱动程序支持。其他 Gravis 摇杆则由 analog 驱动程序支持。

FPGaming A3D 和 MadCatz A3D
----------------------------

由 FPGaming 创建的 Assassin 3D 协议，不仅被 FPGaming 自身使用，还授权给了 MadCatz。A3D 设备由 a3d.c 模块支持。目前支持以下设备：

* FPGaming Assassin 3D
* MadCatz Panther
* MadCatz Panther XL

所有这些设备都会自动检测到。由于 Assassin 3D 和 Panther 允许连接模拟摇杆，因此你需要加载 analog 驱动程序来处理连接的摇杆。
轨迹球应能通过 USB mousedev 模块作为普通鼠标工作。请参阅 USB 文档了解如何设置 USB 鼠标。

ThrustMaster DirectConnect (BSP)
--------------------------------

TM DirectConnect (BSP) 协议由 tmdc.c 模块支持。这包括但不限于：

* ThrustMaster Millennium 3D Interceptor
* ThrustMaster 3D Rage Pad
* ThrustMaster Fusion Digital Game Pad

理论上支持但尚未直接支持的设备有：

* ThrustMaster FragMaster
* ThrustMaster Attack Throttle

如果你有这样的设备，请联系我。
TMDC 设备会自动检测，因此不需要向模块传递任何参数。最多可以使用 Y 型电缆将两个 TMDC 设备连接到一个游戏端口上。

Creative Labs Blaster
---------------------

Blaster 协议由 cobra.c 模块支持。仅支持以下设备：

* Creative Blaster GamePad Cobra

最多可以使用 Y 型电缆在单个游戏端口上使用两个这样的设备。

Genius 数字摇杆
------------------------

Genius 数字通信摇杆由 gf2k.c 模块支持。这包括：

* Genius Flight2000 F-23 摇杆
* Genius Flight2000 F-31 摇杆
* Genius G-09D 游戏手柄

其他 Genius 数字摇杆尚未得到支持，但添加支持相对容易。

InterAct 数字摇杆
--------------------------

InterAct 数字通信摇杆由 interact.c 模块支持。这包括：

* InterAct HammerHead/FX 游戏手柄
* InterAct ProPad8 游戏手柄

其他 InterAct 数字摇杆尚未得到支持，但添加支持相对容易。

PDPI Lightning 4 游戏卡
--------------------------

PDPI Lightning 4 游戏卡由 lightning.c 模块支持。
一旦加载了该模块，就可以使用 analog 驱动程序来处理摇杆。数字通信摇杆仅能在端口 0 上工作，而使用 Y 型电缆时，可以将最多 8 个模拟摇杆连接到一张 L4 卡上，如果系统中有两张卡，则可以连接 16 个模拟摇杆。
Trident 4DWave / Aureal Vortex
------------------------------

带有Trident 4DWave DX/NX或Aureal Vortex/Vortex2芯片组的声卡提供了一种“增强型游戏端口”模式，其中声卡负责轮询手柄。此模式由pcigame.c模块支持。加载后，模拟驱动程序可以使用这些游戏端口的增强功能。

Crystal SoundFusion
-------------------

带有Crystal SoundFusion芯片组的声卡也提供了一种“增强型游戏端口”，类似于上述的4DWave或Vortex。cs461x.c模块支持这种增强模式以及SoundFusion端口的普通模式。

SoundBlaster Live!
------------------

Live!具有一个特殊的PCI游戏端口，虽然它不提供像4DWave及其同类那样的“增强”功能，但比ISA接口的手柄快得多。它也需要特殊的支持，因此使用了emu10k1-gp.c模块而不是普通的ns558.c模块。

SoundBlaster 64和128 - ES1370和ES1371，ESS Solo1和S3 SonicVibes
------------------------------------------------------------------------

这些PCI声卡具有特定的游戏端口。它们由声卡驱动程序直接处理。确保在手柄菜单中选择游戏端口支持，并在声音菜单中为相应的声卡选择支持。

Amiga
-----

连接到Amiga上的Amiga手柄由amijoy.c驱动程序支持。由于它们无法自动检测，驱动程序有一个命令行参数：

	amijoy.map=<a>,<b>

a 和 b 定义了连接到Amiga的JOY0DAT和JOY1DAT端口的手柄。

====== ===========================
值       手柄类型
====== ===========================
 0      无
 1      单按钮数字手柄
====== ===========================

目前仅支持上述手柄类型，但如果我能接触到一台Amiga的话，未来可能会增加更多支持。

游戏机和8位手柄及手柄
-----------------------------------------

这些手柄和游戏机不是为PC和其他运行Linux的计算机设计的，通常需要一个特殊的连接器通过并行端口连接它们。
更多信息请参阅 :ref:`joystick-parport`

SpaceTec/LabTec设备
-----------------------

SpaceTec串行设备使用SpaceWare协议进行通信。这由spaceorb.c和spaceball.c驱动程序支持。目前由spaceorb.c支持的设备包括：

* SpaceTec SpaceBall Avenger
* SpaceTec SpaceOrb 360

目前由spaceball.c支持的设备包括：

* SpaceTec SpaceBall 4000 FLX

除了在内核中包含spaceorb/spaceball和serport模块外，还需要将一个串行端口连接到设备上。为此，请运行inputattach程序：

	inputattach --spaceorb /dev/tts/x &

或：

	inputattach --spaceball /dev/tts/x &

其中/dev/tts/x是设备连接的串行端口。这样做之后，设备会被报告并开始工作。

关于SpaceOrb有一个需要注意的地方：按钮#6（位于球体底部的按钮），尽管被报告为一个普通按钮，但实际上会引起SpaceOrb内部重新居中，将零点移动到按下按钮时球的位置。因此，在将其绑定到其他功能之前，请先考虑清楚。
SpaceTec SpaceBall 2003 FLX 和 3003 FLX 尚未得到支持  
Logitech SWIFT 设备  
----------------------  

SWIFT 串行协议由 warrior.c 模块支持。目前仅支持以下设备：  
* Logitech WingMan Warrior  

未来也可能支持 Logitech CyberMan（原版，而非 CM2）。要使用该模块，您需要在插入/编译模块到内核后运行 inputattach 命令：

```
inputattach --warrior /dev/tts/x &
```

`/dev/tts/x` 是您的 Warrior 设备所连接的串行端口  
Magellan / Space Mouse  
----------------------  

由 LogiCad3d（前身为 Space Systems）为其他许多公司（如 Logitech、HP 等）制造的 Magellan（或 Space Mouse）由 joy-magellan 模块支持。目前仅支持以下型号：  
* Magellan 3D  
* Space Mouse  

‘Plus’ 版本上的额外按钮尚未得到支持。要使用它，您需要使用以下命令将串行端口附加到驱动程序：

```
inputattach --magellan /dev/tts/x &
```

之后 Magellan 将被检测到并初始化，并会发出蜂鸣声，`/dev/input/jsX` 设备应该可以使用了  
I-Force 设备  
---------------  

所有 I-Force 设备都由 iforce 模块支持。这包括：  
* AVB Mag Turbo Force  
* AVB Top Shot Pegasus  
* AVB Top Shot Force Feedback Racing Wheel  
* Boeder Force Feedback Wheel  
* Logitech WingMan Force  
* Logitech WingMan Force Wheel  
* Guillemot Race Leader Force Feedback  
* Guillemot Force Feedback Racing Wheel  
* Thrustmaster Motor Sport GT  

要使用它，您需要使用以下命令将串行端口附加到驱动程序：

```
inputattach --iforce /dev/tts/x &
```

之后 I-Force 设备将被检测到，`/dev/input/jsX` 设备应该可以使用了。  
如果您是通过 USB 端口使用设备，则不需要 inputattach 命令。  
I-Force 驱动程序现在通过事件接口支持力反馈。请注意，Logitech WingMan 3D 设备不支持此模块，而是由 hid 支持。这些设备不支持力反馈。Logitech 游戏手柄也是 hid 设备。  
Gravis Stinger 游戏手柄  
----------------------  

专为笔记本电脑设计的 Gravis Stinger 串行端口游戏手柄由 stinger.c 模块支持。要使用它，请使用以下命令将串行端口附加到驱动程序：

```
inputattach --stinger /dev/tty/x &
```

其中 `x` 是串行端口的编号。
故障排除
===============

遇到一些问题的可能性相当高。为了测试驱动程序是否正常工作，如果有疑问，请使用 jstest 工具的一些模式。最有用的模式是“normal”（适用于 1.x 接口）和“old”（适用于 0.x 接口）。你可以通过以下命令来运行它：

```
jstest --normal /dev/input/js0
jstest --old    /dev/input/js0
```

此外，你还可以使用 evtest 工具进行测试：

```
evtest /dev/input/event0
```

哦，对了，记得阅读常见问题解答！ :)

常见问题解答
===

**问：运行 'jstest /dev/input/js0' 结果出现 "File not found" 错误。这是什么原因？**

**答：** 设备文件不存在。请创建它们（参见第 2.2 节）。

**问：是否可以将我的旧 Atari/Commodore/Amiga/游戏手柄（使用 9 针 D 型 Cannon 连接器）连接到我 PC 的串行端口？**

**答：** 是的，这是可能的，但这样做会烧毁你的串行端口或手柄。当然，这样是不会工作的。

**问：我的游戏杆在 Quake / Quake 2 中不起作用。这是什么原因？**

**答：** Quake / Quake 2 不支持游戏杆。你可以使用 joy2key 来模拟按键操作。
