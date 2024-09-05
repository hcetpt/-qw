===========================
帧缓冲设备 API
===========================

最后修订：2011年6月21日

0. 引言
---------------

本文档描述了应用程序与帧缓冲设备交互时使用的帧缓冲 API。内核中设备驱动程序和帧缓冲核心之间的 API 没有在此文档中描述。
由于原始帧缓冲 API 缺乏文档，驱动程序的行为在细微（或不那么细微）的地方有所不同。本文档描述了推荐的 API 实现，但应用程序应准备好处理不同的行为。

1. 功能
---------------

设备和驱动程序的功能通过固定屏幕信息中的功能字段报告：

```c
struct fb_fix_screeninfo {
	...
	__u16 capabilities;		/* 见 FB_CAP_* */
	...
};
```

应用程序应该使用这些功能来了解可以从设备和驱动程序期望哪些特性。

- `FB_CAP_FOURCC`

驱动程序支持基于四个字符代码（FOURCC）的格式设置 API。当被支持时，格式使用 FOURCC 进行配置，而不是手动指定颜色组件布局。

2. 类型和视觉
--------------------

像素以硬件依赖的格式存储在内存中。应用程序需要了解像素存储格式，以便将图像数据以硬件期望的格式写入帧缓冲内存。

格式由帧缓冲类型和视觉进行描述。某些视觉需要额外的信息，这些信息存储在可变屏幕信息的 bits_per_pixel、grayscale、red、green、blue 和 transp 字段中。

视觉描述了如何编码和组合颜色信息以创建宏像素。类型描述了宏像素如何存储在内存中。以下类型和视觉是受支持的：
- FB_TYPE_PACKED_PIXELS

宏像素连续存储在一个平面上。如果每个宏像素的位数不是8的倍数，那么宏像素是否填充到下一个8位的倍数或打包成字节取决于视觉格式。行末尾可能有填充，并通过固定屏幕信息中的 `line_length` 字段报告。

- FB_TYPE_PLANES

宏像素分布在多个平面上。平面的数量等于每个宏像素的位数，其中第 i 个平面存储所有宏像素的第 i 位。这些平面连续存储在内存中。

- FB_TYPE_INTERLEAVED_PLANES

宏像素分布在多个平面上。平面的数量等于每个宏像素的位数，其中第 i 个平面存储所有宏像素的第 i 位。这些平面交错存储在内存中。交错因子（定义为两个属于不同平面的连续交错块之间的字节距离）存储在固定屏幕信息的 `type_aux` 字段中。

- FB_TYPE_FOURCC

宏像素按照 `FOURCC` 格式标识符描述的方式存储在内存中，该标识符存储在可变屏幕信息的 `grayscale` 字段中。

- FB_VISUAL_MONO01

像素是黑色或白色，并且存储在由可变屏幕信息中的 `bpp` 字段指定的位数上（通常为1位）。黑色像素表示为所有位都为1，白色像素表示为所有位都为0。当每个像素的位数小于8时，几个像素会打包在一起成为一个字节。目前 `FB_VISUAL_MONO01` 只与 `FB_TYPE_PACKED_PIXELS` 一起使用。
- FB_VISUAL_MONO10

像素为黑色或白色，并以位的形式存储（通常为一位），具体由变量屏幕信息中的`bpp`字段指定。
黑色像素用所有位均为0表示，白色像素用所有位均为1表示。当每个像素的位数小于8时，多个像素会打包在一个字节中。
目前`FB_VISUAL_MONO01`仅与`FB_TYPE_PACKED_PIXELS`一起使用。

- FB_VISUAL_TRUECOLOR

像素被分解为红色、绿色和蓝色组件，每个组件通过只读查找表索引对应值。查找表依赖于设备，并提供线性或非线性的渐变。
每个组件根据变量屏幕信息中的`red`、`green`、`blue`和`transp`字段存储在宏像素中。

- FB_VISUAL_PSEUDOCOLOR 和 FB_VISUAL_STATIC_PSEUDOCOLOR

像素值作为索引编码到一个颜色映射中，该颜色映射存储红色、绿色和蓝色组件。对于`FB_VISUAL_STATIC_PSEUDOCOLOR`，颜色映射是只读的；而对于`FB_VISUAL_PSEUDOCOLOR`，则是可读写的。
每个像素值存储的位数由变量屏幕信息中的`bits_per_pixel`字段报告。

- FB_VISUAL_DIRECTCOLOR

像素被分解为红色、绿色和蓝色组件，每个组件通过可编程查找表索引对应值。
每个组件根据变量屏幕信息中的`red`、`green`、`blue`和`transp`字段存储在宏像素中。

- FB_VISUAL_FOURCC

像素按照存储在变量屏幕信息的`grayscale`字段中的FOURCC格式标识符描述的方式进行编码和解释。
### 3. 屏幕信息
---------------------

屏幕信息通过使用 `FBIOGET_FSCREENINFO` 和 `FBIOGET_VSCREENINFO` 的 ioctl 调用由应用程序查询。这些 ioctl 调用分别需要一个指向 `fb_fix_screeninfo` 和 `fb_var_screeninfo` 结构的指针。

`struct fb_fix_screeninfo` 存储了关于帧缓冲设备及其当前格式的设备无关且不可更改的信息。这些信息不能直接被应用程序修改，但在应用程序修改格式时，驱动程序可以更改它们：

```c
struct fb_fix_screeninfo {
    char id[16];                /* 标识字符串，例如 "TT Builtin" */
    unsigned long smem_start;   /* 帧缓冲内存的起始地址（物理地址） */
    __u32 smem_len;             /* 帧缓冲内存长度 */
    __u32 type;                 /* 参见 FB_TYPE_* */
    __u32 type_aux;             /* 对于交错平面的交错 */
    __u32 visual;               /* 参见 FB_VISUAL_* */
    __u16 xpanstep;             /* 如果没有硬件平移，则为零 */
    __u16 ypanstep;             /* 如果没有硬件平移，则为零 */
    __u16 ywrapstep;            /* 如果没有硬件 Y 裁剪，则为零 */
    __u32 line_length;          /* 每行的字节数 */
    unsigned long mmio_start;   /* 内存映射 I/O 的起始地址（物理地址） */
    __u32 mmio_len;             /* 内存映射 I/O 长度 */
    __u32 accel;                /* 向驱动程序指示特定的芯片/卡 */
    __u16 capabilities;         /* 参见 FB_CAP_* */
    __u16 reserved[2];          /* 保留以供将来兼容性使用 */
};
```

`struct fb_var_screeninfo` 存储了关于帧缓冲设备及其当前格式和视频模式以及其他杂项参数的设备无关且可更改的信息：

```c
struct fb_var_screeninfo {
    __u32 xres;                 /* 可见分辨率 */
    __u32 yres;
    __u32 xres_virtual;         /* 虚拟分辨率 */
    __u32 yres_virtual;
    __u32 xoffset;              /* 从虚拟到可见的偏移量 */
    __u32 yoffset;              /* 分辨率偏移量 */

    __u32 bits_per_pixel;       /* 猜猜是什么 */
    __u32 grayscale;            /* 0 = 彩色，1 = 灰度，>1 = FOURCC */
    struct fb_bitfield red;     /* 如果是真彩色，则是帧缓冲内存中的位字段，否则只有长度有意义 */
    struct fb_bitfield green;
    struct fb_bitfield blue;
    struct fb_bitfield transp;  /* 透明度 */

    __u32 nonstd;               /* 不等于 0 表示非标准像素格式 */

    __u32 activate;             /* 参见 FB_ACTIVATE_* */

    __u32 height;               /* 图片高度（毫米） */
    __u32 width;                /* 图片宽度（毫米） */

    __u32 accel_flags;          /* （已废弃）参见 fb_info.flags */

    /* 定时：除 pixclock 外所有值都以 pixclock 为单位 */
    __u32 pixclock;             /* 像素时钟（皮秒） */
    __u32 left_margin;          /* 从同步到图片的时间 */
    __u32 right_margin;         /* 从图片到同步的时间 */
    __u32 upper_margin;         /* 从同步到图片的时间 */
    __u32 lower_margin;
    __u32 hsync_len;            /* 水平同步长度 */
    __u32 vsync_len;            /* 垂直同步长度 */
    __u32 sync;                 /* 参见 FB_SYNC_* */
    __u32 vmode;                /* 参见 FB_VMODE_* */
    __u32 rotate;               /* 逆时针旋转的角度 */
    __u32 colorspace;           /* 对于基于 FOURCC 的模式的颜色空间 */
    __u32 reserved[4];          /* 保留以供将来兼容性使用 */
};
```

为了修改可变信息，应用程序调用 `FBIOPUT_VSCREENINFO` ioctl，并传递一个指向 `fb_var_screeninfo` 结构的指针。如果调用成功，驱动程序将相应地更新固定屏幕信息。而不是手动填写完整的 `fb_var_screeninfo` 结构，应用程序应调用 `FBIOGET_VSCREENINFO` ioctl 并仅修改关心的字段。

### 4. 格式配置
-----------------------

帧缓冲设备提供了两种配置帧缓冲格式的方法：传统 API 和基于 FOURCC 的 API。
传统 API 在很长一段时间内是唯一的帧缓冲格式配置 API，因此被广泛应用于应用程序中。当使用 RGB 和灰度格式以及传统的非标准格式时，这是推荐的 API。

为了选择一个格式，应用程序设置 `fb_var_screeninfo` 的 `bits_per_pixel` 字段为其所需的帧缓冲深度。通常，最多 8 的值会映射到单色、灰度或伪彩色视觉，但这不是必须的：
- 对于灰度格式，应用程序将 `grayscale` 字段设置为 1。红、蓝、绿和 `transp` 字段必须由应用程序设置为 0，并且由驱动程序忽略。驱动程序必须将红、蓝和绿的偏移量填充为 0，长度设置为 `bits_per_pixel` 的值。
- 对于伪彩色格式，应用程序将 `grayscale` 字段设置为 0。红、蓝、绿和 `transp` 字段必须由应用程序设置为 0，并且由驱动程序忽略。驱动程序必须将红、蓝和绿的偏移量填充为 0，长度设置为 `bits_per_pixel` 的值。
- 对于真彩色和直接色彩格式，应用程序将 `grayscale` 字段设置为 0，并将红、蓝、绿和 `transp` 字段设置为描述内存中颜色分量的布局：

```c
struct fb_bitfield {
    __u32 offset;              /* 位字段的起始位置 */
    __u32 length;              /* 位字段的长度 */
    __u32 msb_right;           /* != 0：最高有效位在右边 */
};
```

像素值的宽度为 `bits_per_pixel`，并分为不重叠的红、绿、蓝和 alpha（透明度）组件。每个组件在像素值中的位置和大小由 `fb_bitfield` 的 `offset` 和 `length` 字段描述。偏移量是从右侧计算的。
像素始终存储在一个整数数量的字节中。如果每像素的位数不是 8 的倍数，像素值将填充到下一个 8 的倍数。
在成功配置格式后，驱动程序会根据所选格式更新 `fb_fix_screeninfo` 的 `type`、`visual` 和 `line_length` 字段。
基于 FOURCC 的 API 使用四个字符代码（FOURCC）替换格式描述。FOURCC 是抽象标识符，能够唯一定义一种格式而无需显式描述它。这是唯一支持 YUV 格式的 API。同时，鼓励驱动程序为 RGB 和灰度格式也实现基于 FOURCC 的 API。
支持基于 FOURCC 的 API 的驱动程序通过设置 `fb_fix_screeninfo` 能力字段中的 `FB_CAP_FOURCC` 位来报告此能力。
FOURCC 定义位于 `linux/videodev2.h` 头文件中。然而，尽管以 `V4L2_PIX_FMT_` 前缀开始，它们并不局限于 V4L2，也不需要使用 V4L2 子系统。FOURCC 文档可以在 `Documentation/userspace-api/media/v4l/pixfmt.rst` 中找到。
为了选择一个格式，应用程序将 `grayscale` 字段设置为所需的 FOURCC。对于 YUV 格式，还应通过将 `colorspace` 字段设置为 `linux/videodev2.h` 中列出并记录在 `Documentation/userspace-api/media/v4l/colorspaces.rst` 中的颜色空间之一来选择适当的颜色空间。
`red`、`green`、`blue` 和 `transp` 字段在基于 FOURCC 的 API 中不使用。出于向前兼容的原因，应用程序必须将这些字段设置为零，而驱动程序必须忽略它们。非零值在未来扩展中可能会赋予特定意义。
在成功配置格式后，驱动程序会根据所选格式更新 `fb_fix_screeninfo` 的 `type`、`visual` 和 `line_length` 字段。`type` 和 `visual` 字段分别被设置为 `FB_TYPE_FOURCC` 和 `FB_VISUAL_FOURCC`。
