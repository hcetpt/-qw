EP93xx LCD控制器驱动程序
================================

EP93xx LCD控制器可以驱动标准桌面显示器和嵌入式LCD显示屏。如果您使用的是标准桌面显示器，则可以使用标准Linux视频模式数据库。在您的板卡文件中，可以这样定义：

```c
static struct ep93xxfb_mach_info some_board_fb_info = {
	.num_modes	= EP93XXFB_USE_MODEDB,
	.bpp		= 16,
};
```

如果您使用的是嵌入式LCD显示屏，则需要为它定义一个视频模式如下：

```c
static struct fb_videomode some_board_video_modes[] = {
	{
		.name		= "some_lcd_name",
		/* 像素时钟、前/后沿等 */
	},
};
```

请注意，像素时钟的值是以皮秒为单位的。您可以使用KH2ZPICOS宏来转换像素时钟的值。大多数其他值都是以像素时钟为单位的。有关更多详细信息，请参阅Documentation/fb/framebuffer.rst。
对于您的板卡，ep93xxfb_mach_info结构应该如下所示：

```c
static struct ep93xxfb_mach_info some_board_fb_info = {
	.num_modes	= ARRAY_SIZE(some_board_video_modes),
	.modes		= some_board_video_modes,
	.default_mode	= &some_board_video_modes[0],
	.bpp		= 16,
};
```

可以通过在您的板卡初始化函数中添加以下内容来注册帧缓冲设备：

```c
ep93xx_register_fb(&some_board_fb_info);
```

视频属性标志
=====================

ep93xxfb_mach_info结构中有一个标志字段，可用于配置控制器。视频属性标志在EP93xx用户指南的第7节中有详细介绍。可用的标志如下：

| 标志 | 描述 |
| --- | --- |
| EP93XXFB_PCLK_FALLING | 在像素时钟的下降沿时钟数据。默认是在上升沿时钟数据 |
| EP93XXFB_SYNC_BLANK_HIGH | 空白信号为高电平有效。默认情况下空白信号为低电平有效 |
| EP93XXFB_SYNC_HORIZ_HIGH | 水平同步信号为高电平有效。默认情况下水平同步信号为低电平有效 |
| EP93XXFB_SYNC_VERT_HIGH | 垂直同步信号为高电平有效。默认情况下垂直同步信号为高电平有效 |

可以使用以下标志来控制帧缓冲区的物理地址：

| 标志 | 描述 |
| --- | --- |
| EP93XXFB_USE_SDCSN0 | 使用SDCSn[0]作为帧缓冲区。这是默认设置 |
| EP93XXFB_USE_SDCSN1 | 使用SDCSn[1]作为帧缓冲区 |
| EP93XXFB_USE_SDCSN2 | 使用SDCSn[2]作为帧缓冲区 |
| EP93XXFB_USE_SDCSN3 | 使用SDCSn[3]作为帧缓冲区 |

平台回调
==================

EP93xx帧缓冲驱动程序支持三个可选的平台回调：setup（设置）、teardown（拆除）和blank（黑屏）。当帧缓冲驱动程序安装和卸载时，将分别调用setup和teardown函数。每当显示被黑屏或取消黑屏时，将调用blank函数。
```plaintext
初始化和清理设备将平台设备结构（platform_device）作为参数传递。可以通过以下方式获取fb_info和ep93xxfb_mach_info结构体：

static int some_board_fb_setup(struct platform_device *pdev)
{
    struct ep93xxfb_mach_info *mach_info = pdev->dev.platform_data;
    struct fb_info *fb_info = platform_get_drvdata(pdev);

    /* 板载特定的帧缓冲区设置 */
}

======================
设置视频模式
======================

使用以下语法设置视频模式：

video=XRESxYRES[-BPP][@REFRESH]

如果EP93xx视频驱动程序是内置的，则在Linux内核命令行上设置视频模式，例如：

video=ep93xx-fb:800x600-16@60

如果EP93xx视频驱动程序是作为一个模块构建的，则在安装模块时设置视频模式：

modprobe ep93xx-fb video=320x240

==============
屏幕页错误
==============

至少在EP9315上存在一个硅片错误，导致VIDSCRNPAGE寄存器（帧缓冲区物理偏移）的第27位被固定为低电平。此错误有一个非官方的勘误表：

https://marc.info/?l=linux-arm-kernel&m=110061245502000&w=2

默认情况下，EP93xx帧缓冲区驱动程序会检查分配的物理地址是否设置了第27位。如果设置了，则释放该内存并返回错误。可以通过在加载驱动程序时添加以下选项来禁用此检查：

      ep93xx-fb.check_screenpage_bug=0

在某些情况下，可能可以通过重新配置SDRAM布局来避免此错误。详细信息请参见EP93xx用户指南的第13节。
```
