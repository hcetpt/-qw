=======================================================
VIA集成图形芯片控制台帧缓冲驱动
=======================================================

平台
--------
    该控制台帧缓冲驱动适用于VIA UniChrome系列图形芯片
    （CLE266, PM800 / CN400 / CN300,
    P4M800CE / P4M800Pro / CN700 / VN800,
    CX700 / VX700, K8M890, P4M890,
    CN896 / P4M900, VX800, VX855）

驱动特性
---------------
    设备：CRT、LCD、DVI

    支持的viafb_mode：

    CRT：
        640x480（60、75、85、100、120 Hz），720x480（60 Hz），
        720x576（60 Hz），800x600（60、75、85、100、120 Hz），
        848x480（60 Hz），856x480（60 Hz），1024x512（60 Hz），
        1024x768（60、75、85、100 Hz），1152x864（75 Hz），
        1280x768（60 Hz），1280x960（60 Hz），1280x1024（60、75、85 Hz），
        1440x1050（60 Hz），1600x1200（60、75 Hz），1280x720（60 Hz），
        1920x1080（60 Hz），1400x1050（60 Hz），800x480（60 Hz）

    色彩深度：8 bpp，16 bpp，32 bpp支持
    支持2D硬件加速器
使用viafb模块
----------------------
    使用默认设置启动viafb：

    #modprobe viafb

    使用用户选项启动viafb：

    #modprobe viafb viafb_mode=800x600 viafb_bpp=16 viafb_refresh=60
    viafb_active_dev=CRT+DVI viafb_dvi_port=DVP1
    viafb_mode1=1024x768 viafb_bpp1=16 viafb_refresh1=60
    viafb_SAMM_ON=1

    viafb_mode：
        - 640x480（默认）
        - 720x480
        - 800x600
        - 1024x768

    viafb_bpp：
        - 8, 16, 32（默认：32）

    viafb_refresh：
        - 60, 75, 85, 100, 120（默认：60）

    viafb_lcd_dsp_method：
        - 0 ：扩展（默认）
        - 1 ：居中

    viafb_lcd_mode：
        0 ：带有LSB数据格式输入的LCD面板（默认）
        1 ：带有MSB数据格式输入的LCD面板

    viafb_lcd_panel_id：
        - 0 ：分辨率：640x480，通道：单，抖动：启用
        - 1 ：分辨率：800x600，通道：单，抖动：启用
        - 2 ：分辨率：1024x768，通道：单，抖动：启用（默认）
        - 3 ：分辨率：1280x768，通道：单，抖动：启用
        - 4 ：分辨率：1280x1024，通道：双，抖动：启用
        - 5 ：分辨率：1400x1050，通道：双，抖动：启用
        - 6 ：分辨率：1600x1200，通道：双，抖动：启用

        - 8 ：分辨率：800x480，通道：单，抖动：启用
        - 9 ：分辨率：1024x768，通道：双，抖动：启用
        - 10：分辨率：1024x768，通道：单，抖动：禁用
        - 11：分辨率：1024x768，通道：双，抖动：禁用
        - 12：分辨率：1280x768，通道：单，抖动：禁用
        - 13：分辨率：1280x1024，通道：双，抖动：禁用
        - 14：分辨率：1400x1050，通道：双，抖动：禁用
        - 15：分辨率：1600x1200，通道：双，抖动：禁用
        - 16：分辨率：1366x768，通道：单，抖动：禁用
        - 17：分辨率：1024x600，通道：单，抖动：启用
        - 18：分辨率：1280x768，通道：双，抖动：启用
        - 19：分辨率：1280x800，通道：单，抖动：启用

    viafb_accel：
        - 0 ：无2D硬件加速
        - 1 ：2D硬件加速（默认）

    viafb_SAMM_ON：
        - 0 ：禁用viafb_SAMM_ON（默认）
        - 1 ：启用viafb_SAMM_ON

    viafb_mode1：（次级显示设备）
        - 640x480（默认）
        - 720x480
        - 800x600
        - 1024x768

    viafb_bpp1：（次级显示设备）
        - 8, 16, 32（默认：32）

    viafb_refresh1：（次级显示设备）
        - 60, 75, 85, 100, 120（默认：60）

    viafb_active_dev：
        此选项用于指定活动设备。（CRT、DVI、CRT+LCD...）
        DVI代表DVI或HDMI。例如，如果要启用HDMI，请设置viafb_active_dev=DVI。
        在SAMM情况下，viafb_active_dev之前的设备是主设备，之后的是次级设备。
        示例：

        要启用一个设备，如仅DVI，我们可以使用：

            modprobe viafb viafb_active_dev=DVI

        要启用两个设备，如CRT+DVI：

            modprobe viafb viafb_active_dev=CRT+DVI;

        对于DuoView情况，我们可以使用：

            modprobe viafb viafb_active_dev=CRT+DVI

        或者：

            modprobe viafb viafb_active_dev=DVI+CRT

对于SAMM情况：

    如果CRT为主设备且DVI为次级设备，我们应该使用：

        modprobe viafb viafb_active_dev=CRT+DVI viafb_SAMM_ON=1

    如果DVI为主设备且CRT为次级设备，我们应该使用：

        modprobe viafb viafb_active_dev=DVI+CRT viafb_SAMM_ON=1

viafb_display_hardware_layout：
    此选项用于指定CX700芯片的显示硬件布局
    - 1 ：仅LCD
    - 2 ：仅DVI
    - 3 ：LCD+DVI（默认）
    - 4 ：LCD1+LCD2（内部+内部）
    - 16：LCD1+外部LCD2（内部+外部）

    viafb_second_size：
    此选项用于在SAMM情况下设置次级设备的内存大小（MB）
    最小大小为16

    viafb_platform_epia_dvi：
    此选项用于在EPIA - M上启用DVI
    - 0 ：不在EPIA - M上启用DVI（默认）
    - 1 ：在EPIA - M上启用DVI

    viafb_bus_width：
    当使用24位总线宽度数字接口时，应设置此选项
### viafb_device_lcd_dualedge：
- 当使用双边缘面板时，应设置此选项
  - 0：无双边缘面板（默认）
  - 1：双边缘面板

### viafb_lcd_port：
此选项用于指定LCD输出端口，可用值为 "DVP0" "DVP1" "DFP_HIGHLOW" "DFP_HIGH" "DFP_LOW"。
对于外部LCD + 外部DVI在CX700上（外部LCD位于DVP0），应使用：

    modprobe viafb viafb_lcd_port=DVP0..

### 注意事项：
1. 在“640x480”PAL模式下，如果启用了DVI过扫描功能，CRT显示器可能无法正常显示。
2. SAMM表示单适配器多显示器。它不同于多头显示，因为SAMM在驱动程序层支持多显示器，因此fbcon层甚至不知道它的存在；SAMM的第二个屏幕没有设备节点文件，因此用户模式应用程序无法直接访问它。当启用SAMM时，viafb_mode和viafb_mode1、viafb_bpp和viafb_bpp1、viafb_refresh和viafb_refresh1可以不同。
3. 当控制台依赖于viafbinfo1时，动态更改分辨率和bpp需要调用VIAFB指定的ioctl接口VIAFB_SET_DEVICE，而不是调用通用ioctl函数FBIOPUT_VSCREENINFO，因为viafb不支持多头显示，否则会导致屏幕崩溃。

### 使用"fbset"工具配置viafb
"fbset"是Linux的一个内置实用工具。

1. 查询当前的viafb信息，执行：

       # fbset -i

2. 设置各种分辨率和刷新率：

       # fbset <resolution-vertical_sync>

   示例：

       # fbset "1024x768-75"

   或者：

       # fbset -g 1024 768 1024 768 32

   查看文件"/etc/fb.modes"以查找可用的显示模式。

3. 设置颜色深度：

       # fbset -depth <value>

   示例：

       # fbset -depth 16

### 通过/proc配置viafb
以下文件存在于/proc/viafb中：

### supported_output_devices
此只读文件包含一个逗号分隔的列表，列出了平台上所有可能可用的输出设备。虽然这些设备可能并非全部连接到您的硬件上，但它应该能提供一个很好的起点来确定哪些名称对应实际的连接器。
示例：

		# cat /proc/viafb/supported_output_devices

    iga1/output_devices, iga2/output_devices
	这两个文件可读可写。iga1 和 iga2 是生成屏幕图像的两个独立单元。这些图像可以转发到一个或多个输出设备。读取这些文件是一种查询某个 iga 当前使用哪些输出设备的方法。

示例：

		# cat /proc/viafb/iga1/output_devices

	如果没有打印输出设备，则此 iga 的输出将丢失。
这可能会发生在仅使用另一个（而不是当前这个）iga 的情况下。
写入这些文件允许在运行时调整输出设备。可以添加新设备、移除现有设备或在 igas 之间切换。基本上，你可以写一个以逗号分隔的设备名称列表（或单个名称），格式与这些文件的输出相同。可以在前面加上 '+' 或 '-' 来方便地添加和移除设备。因此，加上 '+' 前缀会将你的列表中的设备添加到已有的设备中，'-' 会从现有的设备中移除列出的设备，如果不给定前缀则用列出的设备替换所有现有的设备。如果你移除设备，它们会被关闭。如果你添加的设备已经是另一个 iga 的一部分，则它们会从那里移除并添加到新的 iga 中。

示例：

将 CRT 添加为 iga1 的输出设备：

		# echo +CRT > /proc/viafb/iga1/output_devices

移除（关闭）作为 iga2 输出设备的 DVP1 和 LVDS1：

		# echo -DVP1,LVDS1 > /proc/viafb/iga2/output_devices

将 iga1 的所有输出设备替换为 CRT：

		# echo CRT > /proc/viafb/iga1/output_devices

使用 viafb 启动
-----------------

在你的 grub.conf 文件中添加以下行：

    append = "video=viafb:viafb_mode=1024x768,viafb_bpp=32,viafb_refresh=85"

VIA 帧缓冲模式
==================

.. include:: viafb.modes
   :literal:
