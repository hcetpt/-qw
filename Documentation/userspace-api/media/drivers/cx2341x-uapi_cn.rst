SPDX 许可证标识符: GPL-2.0

cx2341x 驱动程序
===============

非压缩文件格式
----------------

cx23416 可以生成（而 cx23415 也可以读取）原始 YUV 输出。YUV 帧的格式是 16x16 线性平铺的 NV12（V4L2_PIX_FMT_NV12_16L16）。这种格式为 YUV 4:2:0，每像素使用 1 个 Y 字节和每四个像素使用 1 个 U 和 V 字节。

数据被编码为两个宏块平面，第一个包含 Y 值，第二个包含 UV 宏块。

Y 平面被划分为从左到右、从上到下的 16x16 像素块。每个块依次逐行传输。因此，前 16 个字节是左上角块的第一行，接下来的 16 个字节是左上角块的第二行，以此类推。在传输完这个块后，传输右侧块的第一行，依此类推。

UV 平面被划分为从左到右、从上到下的 16x8 UV 值块。每个块依次逐行传输。因此，前 16 个字节是左上角块的第一行，并包含 8 对 UV 值（总共 16 个字节）。接下来的 16 个字节是左上角块的第二行中的 8 对 UV 值，依此类推。在传输完这个块后，传输右侧块的第一行，依此类推。

下面的代码作为一个示例，展示了如何将 V4L2_PIX_FMT_NV12_16L16 转换为单独的 Y、U 和 V 平面。此代码假设帧大小为 720x576（PAL）像素。

帧的宽度始终为 720 像素，无论实际指定的宽度是多少。

如果高度不是 32 行的倍数，则捕获的视频在末尾缺少宏块，无法使用。因此，高度必须是 32 的倍数。
原始格式 C 语言示例
~~~~~~~~~~~~~~~~~~~~

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned char frame[576*720*3/2];
static unsigned char framey[576*720];
static unsigned char frameu[576*720 / 4];
static unsigned char framev[576*720 / 4];

static void de_macro_y(unsigned char* dst, unsigned char *src, int dstride, int w, int h)
{
    unsigned int y, x, i;

    // 解码 Y 平面
    // dstride = 720 = w
    // Y 平面被分成 16x16 像素的块
    // 每个块逐行传输
    for (y = 0; y < h; y += 16) {
        for (x = 0; x < w; x += 16) {
            for (i = 0; i < 16; i++) {
                memcpy(dst + x + (y + i) * dstride, src, 16);
                src += 16;
            }
        }
    }
}

static void de_macro_uv(unsigned char *dstu, unsigned char *dstv, unsigned char *src, int dstride, int w, int h)
{
    unsigned int y, x, i;

    // 解码 U/V 平面
    // dstride = 720 / 2 = w
    // U/V 值交错（UVUV...）
    // U/V 平面同样被分成 16x16 的 UV 值块
    // 每个块逐行传输
    for (y = 0; y < h; y += 16) {
        for (x = 0; x < w; x += 8) {
            for (i = 0; i < 16; i++) {
                int idx = x + (y + i) * dstride;

                dstu[idx+0] = src[0];  dstv[idx+0] = src[1];
                dstu[idx+1] = src[2];  dstv[idx+1] = src[3];
                dstu[idx+2] = src[4];  dstv[idx+2] = src[5];
                dstu[idx+3] = src[6];  dstv[idx+3] = src[7];
                dstu[idx+4] = src[8];  dstv[idx+4] = src[9];
                dstu[idx+5] = src[10]; dstv[idx+5] = src[11];
                dstu[idx+6] = src[12]; dstv[idx+6] = src[13];
                dstu[idx+7] = src[14]; dstv[idx+7] = src[15];
                src += 16;
            }
        }
    }
}

int main(int argc, char **argv)
{
    FILE *fin;
    int i;

    if (argc == 1) fin = stdin;
    else fin = fopen(argv[1], "r");

    if (fin == NULL) {
        fprintf(stderr, "无法打开输入文件\n");
        exit(-1);
    }
    while (fread(frame, sizeof(frame), 1, fin) == 1) {
        de_macro_y(framey, frame, 720, 720, 576);
        de_macro_uv(frameu, framev, frame + 720 * 576, 720 / 2, 720 / 2, 576 / 2);
        fwrite(framey, sizeof(framey), 1, stdout);
        fwrite(framev, sizeof(framev), 1, stdout);
        fwrite(frameu, sizeof(frameu), 1, stdout);
    }
    fclose(fin);
    return 0;
}
```

嵌入式 V4L2_MPEG_STREAM_VBI_FMT_IVTV VBI 数据格式
---------------------------------------------------------

作者：Hans Verkuil <hverkuil@xs4all.nl>

本节描述了嵌入在 MPEG-2 节目流中的 V4L2_MPEG_STREAM_VBI_FMT_IVTV 格式的 VBI 数据。该格式部分由 ivtv 驱动（用于 Conexant cx23415/6 芯片）的一些硬件限制所决定，特别是 VBI 数据的最大大小。任何超出此限制的数据将在通过 cx23415 播放时被截断。这种格式的优点是非常紧凑，并且所有 VBI 数据都能在最大允许的大小内存储。VBI 数据的流 ID 是 0xBD。嵌入数据的最大大小是 4 + 43 * 36 字节，即 4 字节的头部和 2 * 18 行 VBI 数据，每行包含一个 1 字节的头部和 42 字节的有效载荷。任何超出此限制的数据将被 cx23415/6 固件截断。除了 VBI 行的数据外，我们还需要 36 位用于位掩码来确定哪些行被捕获，以及 4 字节的魔法值，表示这个数据包包含 V4L2_MPEG_STREAM_VBI_FMT_IVTV VBI 数据。

如果使用所有行，则不再有空间用于位掩码。为了解决这个问题，引入了两个不同的魔法值：

- `'itv0'`：在这个魔法值之后跟着两个无符号长整数。第一个无符号长整数的第 0 到第 17 位表示第一场捕获的行。第一个无符号长整数的第 18 到第 31 位和第二个无符号长整数的第 0 到第 3 位用于第二场。
- `'ITV0'`：这个魔法值假设所有 VBI 行都被捕获，即隐含地意味着位掩码为 0xffffffff 和 0xf。

在这些魔法值之后（对于 `'itv0'` 魔法值还包括 8 字节的位掩码），开始捕获的 VBI 行：

对于每一行，第一个字节的最低 4 位包含数据类型。
可能的值如下面的表格所示。负载在接下来的42个字节中。
以下是可能的数据类型列表：

.. code-block:: c

	#define IVTV_SLICED_TYPE_TELETEXT       0x1     // 电视图文 (使用PAL制式的6-22行)
	#define IVTV_SLICED_TYPE_CC             0x4     // 闭合字幕 (NTSC制式第21行)
	#define IVTV_SLICED_TYPE_WSS            0x5     // 宽屏幕信号 (PAL制式第23行)
	#define IVTV_SLICED_TYPE_VPS            0x7     // 视频节目系统 (PAL制式第16行)
