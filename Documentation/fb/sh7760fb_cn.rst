================================================
SH7760/SH7763 集成 LCDC 帧缓冲驱动
================================================

0. 概览
-----------
SH7760/SH7763 集成了一个 LCD 显示控制器（LCDC），理论上支持从 1x1 到 1024x1024 的分辨率，颜色深度范围从 1 到 16 位，在 STN、DSTN 和 TFT 面板上均可使用。
注意事项：

* 帧缓冲内存必须是位于 Area3 最顶部的大块内存（硬件要求）。由于这个要求，你不应该将驱动程序做成模块，因为运行时可能无法获得足够大的连续内存块。
* 驱动程序不支持在加载过程中更改分辨率（显示器不可热插拔）。

* 可能会观察到严重的闪烁现象：
  a) 如果你使用的是 15/16 位颜色模式，并且分辨率 ≥ 640x480 像素，
  b) 在 PCMCIA（或其他任何慢速总线）活动期间
* 旋转仅支持顺时针旋转 90 度，并且仅当水平分辨率 ≤ 320 像素时有效。

文件：
- drivers/video/sh7760fb.c
- include/asm-sh/sh7760fb.h
- Documentation/fb/sh7760fb.rst

1. 平台设置
-----------------
SH7760：
 视频数据通过 DMABRG DMA 引擎获取，因此你需要配置 SH DMAC 为 DMABRG 模式（在启动时某处向 DMARSRA 寄存器写入 0x94808080）
PFC 寄存器 PCCR 和 PCDR 必须设置为外设模式（两者都写零）
驱动程序不会为你执行上述操作，因为平台设置是平台设置代码的工作。

2. 面板定义
--------------------
LCDC 必须明确告知所连接的 LCD 面板类型。数据必须包装在一个 "struct sh7760fb_platdata" 中，并作为 platform_data 传递给驱动程序。
建议仔细查看 SH7760 手册第 30 节。
以下代码说明了如何使640x480 TFT的帧缓冲区工作：

```c
#include <linux/fb.h>
#include <asm/sh7760fb.h>

/*
 * NEC NL6440bc26-01 640x480 TFT
 * 点时钟 25175 kHz
 * X分辨率 640     Y分辨率 480
 * 水平总和 800     垂直总和 525
 * 水平同步开始 656     垂直同步开始 490
 * 水平同步长度 30     垂直同步长度 2
 *
 * Linux帧缓冲层不使用syncstart/synclen值，而是使用右/左/上/下边距值。对于x边距的注释解释了如何从给定的面板同步时间计算这些值。
*/

static struct fb_videomode nl6448bc26 = {
         .name           = "NL6448BC26",
         .refresh        = 60,
         .xres           = 640,
         .yres           = 480,
         .pixclock       = 39683,        /* 以皮秒为单位！ */
         .hsync_len      = 30,
         .vsync_len      = 2,
         .left_margin    = 114,  /* HTOT - (HSYNSLEN + HSYNSTART) */
         .right_margin   = 16,   /* HSYNSTART - XRES */
         .upper_margin   = 33,   /* VTOT - (VSYNLEN + VSYNSTART) */
         .lower_margin   = 10,   /* VSYNSTART - YRES */
         .sync           = FB_SYNC_HOR_HIGH_ACT | FB_SYNC_VERT_HIGH_ACT,
         .vmode          = FB_VMODE_NONINTERLACED,
         .flag           = 0,
};

static struct sh7760fb_platdata sh7760fb_nl6448 = {
         .def_mode       = &nl6448bc26,
         .ldmtr          = LDMTR_TFT_COLOR_16,   /* 16位TFT面板 */
         .lddfr          = LDDFR_8BPP,           /* 我们希望输出8位 */
         .ldpmmr         = 0x0070,
         .ldpspr         = 0x0500,
         .ldaclnr        = 0,
         .ldickr         = LDICKR_CLKSRC(LCDC_CLKSRC_EXTERNAL) |
                           LDICKR_CLKDIV(1),
         .rotate         = 0,
         .novsync        = 1,
         .blank          = NULL,
};

/* SH7760:
 * 0xFE300800：256 * 4字节xRGB调色板RAM
 * 0xFE300C00：42字节控制寄存器
 */
static struct resource sh7760_lcdc_res[] = {
         [0] = {
	       .start  = 0xFE300800,
	       .end    = 0xFE300CFF,
	       .flags  = IORESOURCE_MEM,
         },
         [1] = {
	       .start  = 65,
	       .end    = 65,
	       .flags  = IORESOURCE_IRQ,
         },
};

static struct platform_device sh7760_lcdc_dev = {
         .dev    = {
	       .platform_data = &sh7760fb_nl6448,
         },
         .name           = "sh7760-lcdc",
         .id             = -1,
         .resource       = sh7760_lcdc_res,
         .num_resources  = ARRAY_SIZE(sh7760_lcdc_res),
};
```
