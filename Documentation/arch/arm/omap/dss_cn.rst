OMAP2/3 显示子系统
=========================

这是对位于 `drivers/video/omap` 中的 OMAP 帧缓冲驱动程序（我们称之为 DSS1）的一次几乎完全重写。DSS1 和 DSS2 之间的主要区别在于 DSI、TV 输出以及多显示器支持，但还有许多小的改进。
DSS2 驱动程序（omapdss 模块）位于 `arch/arm/plat-omap/dss/` 中，而帧缓冲、面板和控制器驱动程序则位于 `drivers/video/omap2/` 中。目前 DSS1 和 DSS2 可以并存，您可以选择使用哪一个。
特性
--------

已经测试并通过的功能包括：

- MIPI DPI（并行）输出
- MIPI DSI 在命令模式下的输出
- MIPI DBI（RFBI）输出
- SDI 输出
- TV 输出
- 所有组件都可以编译为模块或内置于内核中
- 使用 DISPC 更新任何输出
- 使用 CPU 更新 RFBI 或 DSI 输出
- OMAP DISPC 平面
- RGB16、RGB24 包装、RGB24 未包装
- YUV2、UYVY
- 缩放
- 调整 DSS FCK 以找到合适的像素时钟
- 使用 DSI DPLL 创建 DSS FCK

已测试的板卡包括：
- OMAP3 SDP 板卡
- Beagle 板卡
- N810

omapdss 驱动程序
--------------

DSS 驱动程序本身没有像现有驱动程序那样支持 Linux 帧缓冲、V4L 等功能，但它提供了一个内核 API 供上层驱动程序使用。
DSS 驱动程序以灵活的方式建模 OMAP 的覆盖层、覆盖层管理器和显示设备，以实现非标准的多显示器配置。除了硬件覆盖层的建模之外，omapdss 还支持虚拟覆盖层和覆盖层管理器。当使用 CPU 或系统 DMA 更新显示设备时，可以使用这些虚拟覆盖层和覆盖层管理器。

omapdss 驱动程序对音频的支持
--------------------------------
存在多种显示技术和标准，它们也支持音频。因此，更新 DSS 设备驱动程序以提供一个音频接口是相关的，该接口可以被音频驱动程序或其他感兴趣的驱动程序使用。
`audio_enable` 函数旨在为播放准备相关 IP（例如启用音频 FIFO、复位某些 IP、启用伴音芯片等）。它打算在调用 `audio_start` 之前调用。`audio_disable` 函数执行相反的操作，并且应在 `audio_stop` 后调用。
虽然给定的 DSS 设备驱动程序可能支持音频，但在某些配置下可能不支持音频（例如使用 VESA 视频定时的 HDMI 显示器）。`audio_supported` 函数旨在查询当前显示配置是否支持音频。
`audio_config` 函数旨在配置显示的所有相关音频参数。为了使此函数独立于任何特定的 DSS 设备驱动程序，定义了一个 `struct omap_dss_audio` 结构体。其目的是包含所有用于音频配置所需的参数。目前，此类结构包含指向 IEC-60958 通道状态字和 CEA-861 音频信息帧结构的指针。这足以支持 HDMI 和 DisplayPort，因为两者都基于 CEA-861 和 IEC-60958。
`audio_enable`、`audio_disable`、`audio_config` 和 `audio_supported` 函数可以实现为可能睡眠的函数。因此，在持有自旋锁或读锁时不应调用它们。
`audio_start` 和 `audio_stop` 函数旨在在配置完成后实际开始/停止音频播放。这些函数设计用于原子上下文。因此，`audio_start` 应该快速返回，并且只应在为音频播放所需的所有资源（音频 FIFO、DMA 通道、伴音芯片等）启用以开始数据传输后调用。
`audio_stop`的设计仅用于停止音频传输。播放所使用的资源通过`audio_disable`释放。

枚举类型`omap_dss_audio_state`可用于帮助接口的实现跟踪音频状态。初始状态为 `_DISABLED`；随后，状态转变为`_CONFIGURED`，然后，在准备好播放音频时，变为`_ENABLED`。当正在渲染音频时使用`_PLAYING`状态。

面板和控制器驱动程序
----------------------

驱动程序实现了特定于面板或控制器的功能，并通常仅通过`omapfb`驱动程序对用户可见。它们向DSS驱动程序注册自己。

`omapfb`驱动程序
------------------

`omapfb`驱动程序实现了任意数量的标准Linux帧缓冲区。这些帧缓冲区可以灵活地路由到任何覆盖层，从而允许非常动态的显示架构。
该驱动程序导出了一些与旧驱动程序兼容的`omapfb`特有的ioctl调用。
其余的非标准特性则通过sysfs导出。最终实现是否使用sysfs还是ioctl仍然待定。

V4L2驱动程序
--------------

V4L2正在TI中实施。
从omapdss的角度来看，V4L2驱动程序应类似于帧缓冲区驱动程序。

架构
--------------------

下面是对不同组件功能的一些澄清：

- 帧缓冲区是OMAP的SRAM/SDRAM内部的一个内存区域，其中包含图像的像素数据。帧缓冲区具有宽度、高度和颜色深度。
- Overlay 定义了从哪里读取像素以及这些像素在屏幕上的显示位置。Overlay 可能比帧缓冲区小，因此只显示帧缓冲区的一部分。如果Overlay小于显示区域，其位置可以改变。
- Overlay 管理器将多个Overlay合并为一个图像，并将其输出到显示设备。
- 显示是指实际的物理显示设备。
一个帧缓冲区可以连接到多个Overlay，以便在所有这些Overlay上显示相同的像素数据。需要注意的是，在这种情况下，输入到各个Overlay的尺寸必须相同，但对于视频Overlay，输出尺寸可以不同。任何帧缓冲区都可以连接到任意Overlay。
一个Overlay只能连接到一个Overlay管理器。此外，DISPC Overlay只能连接到DISPC Overlay管理器，而虚拟Overlay只能连接到虚拟Overlay管理器。
一个Overlay管理器只能连接到一个显示设备。对于Overlay管理器能够连接的显示类型存在一定的限制：

    - DISPC 电视Overlay管理器只能连接到电视显示设备。
- 虚拟Overlay管理器只能连接到DBI或DSI显示设备。
- DISPC LCD Overlay管理器可以连接到除电视显示设备之外的所有显示设备。

### Sysfs
---
Sysfs接口主要用于测试目的。我认为在最终版本中，Sysfs接口可能不是最佳选择，但我不确定什么样的接口最适合这些功能。
Sysfs接口分为两个部分：DSS 和 FB。
以下是给定内容的中文翻译：

/sys/class/graphics/fb? 目录：
mirror		0=关闭，1=开启
rotate		旋转 0-3 分别代表 0、90、180、270 度
rotate_type	0 = DMA 旋转，1 = VRFB 旋转
overlays	帧缓冲像素所对应的覆盖层编号列表
phys_addr	帧缓冲的物理地址
virt_addr	帧缓冲的虚拟地址
size		帧缓冲的大小

/sys/devices/platform/omapdss/overlay? 目录：
enabled		0=关闭，1=开启
input_size	宽度,高度（即帧缓冲的大小）
manager		目标覆盖层管理器名称
name
output_size	宽度,高度
position	x,y
screen_width	宽度
global_alpha	全局透明度 0-255 0=透明 255=不透明

/sys/devices/platform/omapdss/manager? 目录：
display				目标显示设备
name
alpha_blending_enabled		0=关闭，1=开启
trans_key_enabled		0=关闭，1=开启
trans_key_type			gfx-destination, video-source
trans_key_value			透明色键（RGB24）
default_color			默认背景颜色（RGB24）

/sys/devices/platform/omapdss/display? 目录：

=============== =============================================================
ctrl_name	控制器名称
mirror		0=关闭，1=开启
update_mode	0=关闭，1=自动，2=手动
enabled		0=关闭，1=开启
name
rotate		旋转 0-3 分别代表 0、90、180、270 度
timings		显示定时（像素时钟,水平分辨率/水平前/水平后/水平同步,垂直分辨率/垂直前/垂直后/垂直同步）
		当写入时，对于电视输出接受两种特殊定时：“pal”和“ntsc”
panel_name
tear_elim	消除撕裂 0=关闭，1=开启
output_type	输出类型（仅视频编码器）：“composite”或“svideo”
=============== =============================================================

还有一些调试文件位于 <debugfs>/omapdss/，这些文件展示了关于时钟和寄存器的信息。
示例
--------

下面为示例定义了一些变量：

	ovl0=/sys/devices/platform/omapdss/overlay0
	ovl1=/sys/devices/platform/omapdss/overlay1
	ovl2=/sys/devices/platform/omapdss/overlay2

	mgr0=/sys/devices/platform/omapdss/manager0
	mgr1=/sys/devices/platform/omapdss/manager1

	lcd=/sys/devices/platform/omapdss/display0
	dvi=/sys/devices/platform/omapdss/display1
	tv=/sys/devices/platform/omapdss/display2

	fb0=/sys/class/graphics/fb0
	fb1=/sys/class/graphics/fb1
	fb2=/sys/class/graphics/fb2

OMAP3 SDP 的默认设置
--------------------------

这是 OMAP3 SDP 板的默认设置。所有平面都指向 LCD，DVI 和电视输出未使用。从左到右的列分别是：帧缓冲、覆盖层、覆盖层管理器、显示设备。帧缓冲由 omapfb 处理，其余部分由 DSS 处理：

	FB0 --- GFX  -\            DVI
	FB1 --- VID1 --+- LCD ---- LCD
	FB2 --- VID2 -/   TV ----- TV

示例：从 LCD 切换到 DVI
-------------------------------

::

	w=`cat $dvi/timings | cut -d "," -f 2 | cut -d "/" -f 1`
	h=`cat $dvi/timings | cut -d "," -f 3 | cut -d "/" -f 1`

	echo "0" > $lcd/enabled
	echo "" > $mgr0/display
	fbset -fb /dev/fb0 -xres $w -yres $h -vxres $w -vyres $h
	# 这时您需要切换 omap 板上的 dvi/lcd 拨动开关
	echo "dvi" > $mgr0/display
	echo "1" > $dvi/enabled

在此之后配置如下所示：

	FB0 --- GFX  -\         -- DVI
	FB1 --- VID1 --+- LCD -/   LCD
	FB2 --- VID2 -/   TV ----- TV

示例：将 GFX 覆盖层克隆到 LCD 和电视
----------------------------------------

::

	w=`cat $tv/timings | cut -d "," -f 2 | cut -d "/" -f 1`
	h=`cat $tv/timings | cut -d "," -f 3 | cut -d "/" -f 1`

	echo "0" > $ovl0/enabled
	echo "0" > $ovl1/enabled

	echo "" > $fb1/overlays
	echo "0,1" > $fb0/overlays

	echo "$w,$h" > $ovl1/output_size
	echo "tv" > $ovl1/manager

	echo "1" > $ovl0/enabled
	echo "1" > $ovl1/enabled

	echo "1" > $tv/enabled

在此之后配置如下所示（仅显示相关部分）：

	FB0 +-- GFX  ---- LCD ---- LCD
	\- VID1 ---- TV  ---- TV

杂项说明
----------

OMAP FB 使用标准 DMA 分配器分配帧缓冲内存。您可以启用连续内存分配器 (CONFIG_CMA) 来改进 DMA 分配器，并且如果启用了 CMA，则可以使用 "cma=" 内核参数来增加全局 CMA 内存区域。
使用 DSI DPLL 生成像素时钟，可以产生最大可能的 86.5MHz 像素时钟，并且通过这种方式可以从 DVI 输出 1280x1024@57。
当前旋转和镜像仅支持 RGB565 和 RGB8888 模式。VRFB 不支持镜像。
VRFB 旋转需要比非旋转帧缓冲更多的内存，因此在使用 VRFB 旋转之前，您可能需要增加您的 vram 设置。此外，许多应用程序如果不注意所有帧缓冲参数则可能无法与 VRFB 兼容。

内核引导参数
---------------------

omapfb.mode=<display>:<mode>[,...]
	- 指定显示设备的默认视频模式。例如，“dvi:800x400MR-24@60”。参见 drivers/video/modedb.c
还有两个特殊模式：“pal”和“ntsc”，可用于电视输出
omapfb.vram=<fbnum>:<size>[@<physaddr>][,...]
	- 为帧缓冲分配的 VRAM。通常 omapfb 根据显示尺寸分配 vram。使用此选项可以手动分配更多或定义每个帧缓冲的物理地址。例如，“1:4M”为 fb1 分配 4M
omapfb.debug=<y|n>
	- 启用调试打印。您必须在内核配置中启用 OMAPFB 调试支持
omapfb.test=<y|n>
	- 每当帧缓冲设置改变时，在帧缓冲上绘制测试图案
你需要在内核配置中启用 OMAPFB 调试支持。
omapfb.vrfb=<y|n>
	- 对所有帧缓冲区使用 VRFB 旋转
omapfb.rotate=<角度>
	- 应用于所有帧缓冲区的默认旋转
0 - 0 度旋转
	  1 - 90 度旋转
	  2 - 180 度旋转
	  3 - 270 度旋转

omapfb.mirror=<y|n>
	- 所有帧缓冲区的默认镜像。仅与 DMA 旋转一起工作
omapdss.def_disp=<显示设备>
	- 默认显示设备的名称，所有覆盖层都将连接到该显示设备
常见的示例是 "lcd" 或 "tv"
omapdss.debug=<y|n>
	- 启用调试打印。你必须在内核配置中启用了 DSS 调试支持
待办事项
----

DSS 锁定

错误检查

- 缺少许多检查或仅实现了 BUG()

系统 DMA 更新以支持 DSI

- 可用于 RGB16 和 RGB24P 模式。可能不适用于 RGB24U（如何跳过空字节？）

OMAP1 支持

- 不确定是否需要
