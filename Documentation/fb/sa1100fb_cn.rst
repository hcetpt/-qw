=================
什么是 sa1100fb？
=================

.. [此文件是从 VesaFB/matroxfb 克隆而来]

这是一个用于 SA-1100 LCD 控制器的图形帧缓冲驱动程序。

配置
==============

对于大多数常见的被动显示器，只需在内核命令行中给出以下选项即可配置控制器：

```
video=sa1100fb:bpp:<value>,lccr0:<value>,lccr1:<value>,lccr2:<value>,lccr3:<value>
```

每像素位数（bpp）值应为 4、8、12 或 16。LCCR 值是特定于显示器的，并应在 SA-1100 开发者手册第 11.7 节中按文档说明计算。双面板显示器只要在 LCCR0 中设置了 SDS 位就可以支持；GPIO<9:2> 用于下部面板。

对于主动显示器或需要额外配置的显示器（如控制背光、开启 LCD 等），仅命令行选项可能不足以配置显示器。可能需要在 `sa1100fb_init_fbinfo()`、`sa1100fb_activate_var()`、`sa1100fb_disable_lcd_controller()` 和 `sa1100fb_enable_lcd_controller()` 函数中添加部分代码。

接受的选项如下：

```
bpp:<value>		配置为 <value> 每像素位数
lccr0:<value>		配置 LCD 控制寄存器 0（11.7.3）
lccr1:<value>		配置 LCD 控制寄存器 1（11.7.4）
lccr2:<value>		配置 LCD 控制寄存器 2（11.7.5）
lccr3:<value>		配置 LCD 控制寄存器 3（11.7.6）
```

黄铭（Mark Huang）<mhuang@livetoy.com>
