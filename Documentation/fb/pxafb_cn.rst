PX25x LCD控制器驱动程序
================================

该驱动支持以下选项，无论是通过模块化时的options=<OPTIONS>还是内置时的video=pxafb:<OPTIONS>
例如::

    modprobe pxafb options=vmem:2M,mode:640x480-8,passive

或者在内核命令行中::

    video=pxafb:vmem:2M,mode:640x480-8,passive

vmem: VIDEO_MEM_SIZE

    要分配的视频内存数量（可以以K或M为单位表示千字节或兆字节）

mode:XRESxYRES[-BPP]

    XRES == LCCR1_PPL + 1

    YRES == LLCR2_LPP + 1

        显示屏的分辨率（像素）

    BPP == 位深度。有效值为1、2、4、8和16
pixclock: PIXCLOCK

    像素时钟（皮秒）

left: LEFT == LCCR1_BLW + 1

right: RIGHT == LCCR1_ELW + 1

hsynclen: HSYNC == LCCR1_HSW + 1

upper: UPPER == LCCR2_BFW

lower: LOWER == LCCR2_EFR

vsynclen: VSYNC == LCCR2_VSW + 1

    显示边距和同步时间

color | mono => LCCR0_CMS

    umm..

active | passive => LCCR0_PAS

    活动（TFT）或被动（STN）显示屏

single | dual => LCCR0_SDS

    单面板或双面板被动显示屏

4pix | 8pix => LCCR0_DPD

    4像素或8像素单色单面板数据

hsync: HSYNC, vsync: VSYNC

    水平和垂直同步。0 => 低电平有效，1 => 高电平有效
dpc: DPC

    双像素时钟。1 => 真实，0 => 虚假

outputen: POLARITY

    输出使能极性。0 => 低电平有效，1 => 高电平有效

pixclockpol: POLARITY

    像素时钟极性
    0 => 下降沿，1 => 上升沿

PX27x及后续LCD控制器的覆盖层支持
====================================================

  PX27x及后续处理器支持覆盖层overlay1和overlay2位于基础帧缓冲区之上（尽管也有可能位于其下）。它们支持调色板和无调色板RGB格式以及YUV格式（仅在overlay2上可用）。这些覆盖层具有专用的DMA通道，并且行为类似于帧缓冲区。
然而，这些覆盖层帧缓冲区与普通帧缓冲区之间存在一些差异，如下所示：

  1. 覆盖层可以在基础帧缓冲区内的32位字对齐位置开始，这意味着它们有一个起始点(x, y)。此信息被编码到var->nonstd（注意：var->xoffset和var->yoffset不用于此目的）
2. 覆盖层帧缓冲区根据指定的'struct fb_var_screeninfo'动态分配，其大小由以下决定::

    var->xres_virtual * var->yres_virtual * bpp

    bpp = 16 -- 对于RGB565或RGBT555

    bpp = 24 -- 对于YUV444打包

    bpp = 24 -- 对于YUV444平面

    bpp = 16 -- 对于YUV422平面（1像素 = 1 Y + 1/2 Cb + 1/2 Cr）

    bpp = 12 -- 对于YUV420平面（1像素 = 1 Y + 1/4 Cb + 1/4 Cr）

    注意：

    a. 覆盖层不支持x方向的平移，因此var->xres_virtual将始终等于var->xres

    b. 覆盖层的行长度必须是32位字的倍数；对于YUV平面模式，这是指具有最少每像素位数的组件的要求，例如对于YUV420，一个像素的Cr组件实际上是2位，这意味着行长度应该是16像素的倍数

    c. 开始水平位置（XPOS）应该在32位字边界开始，否则fb_check_var()会失败

    d. 覆盖层的矩形应在基础平面内，否则会失败

    应用程序应按照以下顺序操作覆盖层帧缓冲区：

    a. 打开("/dev/fb[1-2]", ...)
    b. ioctl(fd, FBIOGET_VSCREENINFO, ...)
    c. 修改带有期望参数的'var'：

        1) var->xres 和 var->yres
        2) 如果需要更多内存，则增加var->yres_virtual，通常用于双缓冲
        3) var->nonstd 用于设置(x, y)起点和颜色格式
        4) 如果使用RGB模式，则修改var->{red, green, blue, transp}

    d. ioctl(fd, FBIOPUT_VSCREENINFO, ...)
    e. ioctl(fd, FBIOGET_FSCREENINFO, ...)
    f. mmap
    g. ...

3. 对于YUV平面格式，实际上并不受帧缓冲框架支持，应用程序需要处理帧缓冲区内部每个组件的偏移量和长度
4. var->nonstd 用于传递起始(x, y)位置和颜色格式，详细位字段如下所示::

    31                23  20         10          0
     +-----------------+---+----------+----------+
     |  ... 未使用 ... |FOR|   XPOS   |   YPOS   |
     +-----------------+---+----------+----------+

    FOR  - 颜色格式，由pxafb.h中的OVERLAY_FORMAT_*定义

         - 0 - RGB
         - 1 - YUV444 PACKED
         - 2 - YUV444 PLANAR
         - 3 - YUV422 PLANAR
         - 4 - YUV420 PLANAR

    XPOS - 起始水平位置

    YPOS - 起始垂直位置
