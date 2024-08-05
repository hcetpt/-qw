SPDX 许可证标识符: GPL-2.0

=========================================
MTRR（内存类型范围寄存器）控制
=========================================

:作者: - Richard Gooch <rgooch@atnf.csiro.au> - 1999年6月3日
          - Luis R. Rodriguez <mcgrof@do-not-panic.com> - 2015年4月9日


逐步淘汰 MTRR 的使用
====================

在现代的 x86 硬件上，MTRR 的使用已经被 PAT 替代。Linux 上的驱动程序直接使用 MTRR 已经完全被淘汰，设备驱动程序应使用 arch_phys_wc_add() 结合 ioremap_wc() 来使非 PAT 系统上的 MTRR 生效，同时在启用了 PAT 的系统上这是一个无操作但同样有效的方案。
即使 Linux 不直接使用 MTRR，某些 x86 平台固件可能仍然会在启动操作系统之前早期设置 MTRR。它们这样做是因为一些平台固件可能仍然实现了对 MTRR 的访问，这将由平台固件直接控制和处理。一个平台使用 MTRR 的例子是通过 SMI 处理器，一种情况可能是风扇控制，平台代码需要对其部分风扇控制寄存器进行非缓存访问。这种平台访问不需要任何操作系统 MTRR 代码，除了 mtrr_type_lookup() 以确保任何特定于操作系统的映射请求与平台 MTRR 设置一致。如果 MTRR 只是由平台固件代码设置，并且操作系统没有提出任何具体的 MTRR 映射请求，mtrr_type_lookup() 应该始终返回 MTRR_TYPE_INVALID。
详情请参阅 Documentation/arch/x86/pat.rst
.. 提示::
  在 Intel P6 家族处理器（Pentium Pro、Pentium II 及以后版本）中，
  内存类型范围寄存器（MTRRs）可用于控制处理器对内存范围的访问。这对于您拥有一张 PCI 或 AGP 总线上的视频（VGA）卡时最有用。启用写合并允许总线写入传输组合成更大的传输，在通过 PCI/AGP 总线爆发之前。这可以提高图像写入操作性能 2.5 倍或更多。
Cyrix 6x86、6x86MX 和 M II 处理器具有地址范围寄存器（ARRs），这些寄存器提供与 MTRRs 类似的功能。对于这些处理器，ARRs 用于模拟 MTRRs。
AMD K6-2（第 8 步骤及以上）和 K6-3 处理器有两个 MTRR。这些得到了支持。AMD Athlon 家族提供了 8 个 Intel 风格的 MTRRs。
Centaur C6（WinChip）有 8 个 MCR，允许写合并。这些得到了支持。
VIA Cyrix III 和 VIA C3 CPU 提供了 8 个 Intel 风格的 MTRRs。
CONFIG_MTRR 选项创建了一个 /proc/mtrr 文件，可以用来操纵您的 MTRRs。通常，X 服务器应该使用这个文件。这个接口应该是相当通用的，以便其他处理器上的类似控制寄存器可以轻松得到支持。
/proc/mtrr 有两种接口：一种是 ASCII 接口，允许读写；另一种是一个 ioctl() 接口。ASCII 接口适用于管理。ioctl() 接口适用于 C 程序（例如 X 服务器）。下面描述了这些接口及其示例命令和 C 代码。
从Shell读取MTRRs
============================

::
  
  % cat /proc/mtrr
  reg00: 基址=0x00000000 (   0MB), 大小= 128MB: 写回, 计数=1
  reg01: 基址=0x08000000 ( 128MB), 大小=  64MB: 写回, 计数=1

从C-shell创建MTRRs::

  # echo "基址=0xf8000000 大小=0x400000 类型=写合并" >! /proc/mtrr

或者如果你使用bash::

  # echo "基址=0xf8000000 大小=0x400000 类型=写合并" >| /proc/mtrr

其结果为::

  % cat /proc/mtrr
  reg00: 基址=0x00000000 (   0MB), 大小= 128MB: 写回, 计数=1
  reg01: 基址=0x08000000 ( 128MB), 大小=  64MB: 写回, 计数=1
  reg02: 基址=0xf8000000 (3968MB), 大小=   4MB: 写合并, 计数=1

这是针对基址为0xf8000000且大小为4兆字节的视频RAM。要找出你的基址，你需要查看X服务器的输出信息，它会告诉你线性帧缓冲区地址的位置。你可能会得到的一条典型信息是::

  (--) S3: PCI: 968 rev 0, 线性FB @ 0xf8000000

请注意，你应该只使用来自X服务器的值，因为它可能会移动帧缓冲区的基址，所以唯一可以信任的值就是X服务器报告的那个值。
要找出你的帧缓冲区的大小（你不知道这个吗？），以下这行信息会告诉你::

  (--) S3: 视频内存:  4096k

这是4兆字节，也就是0x400000字节（以十六进制表示）
正在为XFree86编写一个补丁，使这一过程自动化：换句话说，X服务器将使用ioctl()接口来操作/proc/mtrr，因此用户无需做任何事情。如果你使用商业X服务器，请向供应商游说添加对MTRRs的支持。
创建重叠的MTRRs
==========================

::
  
  %echo "基址=0xfb000000 大小=0x1000000 类型=写合并" >/proc/mtrr
  %echo "基址=0xfb000000 大小=0x1000 类型=不可缓存" >/proc/mtrr

其结果为::

  % cat /proc/mtrr
  reg00: 基址=0x00000000 (   0MB), 大小=  64MB: 写回, 计数=1
  reg01: 基址=0xfb000000 (4016MB), 大小=  16MB: 写合并, 计数=1
  reg02: 基址=0xfb000000 (4016MB), 大小=   4kB: 不可缓存, 计数=1

某些显卡（尤其是Voodoo Graphics板卡）需要从区域开始排除这4 kB的区域，因为这部分用于寄存器。
注意：你只能创建类型为不可缓存的区域，前提是第一个创建的区域必须是类型为写合并的。
从C-shell移除MTRRs
==============================

::
  
  % echo "禁用=2" >! /proc/mtrr

或者使用bash::

  % echo "禁用=2" >| /proc/mtrr

从C程序使用ioctl()读取MTRRs
==============================================

::
  
  /*  mtrr-show.c
  
      mtrr-show的源文件（示例程序，使用ioctl()显示MTRRs）
      
      版权(C) 1997-1998  Richard Gooch
      
      本程序是自由软件；你可以按照自由软件基金会发布的GNU通用公共许可证的规定重新分发或修改它；要么是许可证的第2版，要么(由你选择)是任何后续版本。
此程序以期望它能有用的方式发布，
      但是没有任何保证；甚至没有隐含的适销性或适用于特定目的的保证。详情请参见GNU通用公共许可证。
你应该已经收到了一份GNU通用公共许可证的副本；
      如果没有，请写信给自由软件基金会, Inc., 675 Mass Ave, Cambridge, MA 02139, USA
可以通过电子邮件rgooch@atnf.csiro.au联系Richard Gooch
      邮政地址是：
        Richard Gooch, c/o ATNF, P. O. Box 76, Epping, N.S.W., 2121, Australia
*/

  /*
      本程序将使用/proc/mtrr上的ioctl()来显示当前MTRR设置。这是替代直接读取/proc/mtrr的方法。
下面是提供的C程序代码及其注释的中文翻译：

编写者：Richard Gooch   1997年12月17日

最后更新者：Richard Gooch   1998年5月2日

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <errno.h>
#include <asm/mtrr.h>

#define TRUE 1
#define FALSE 0
#define ERRSTRING strerror (errno)

static char *mtrr_strings[MTRR_NUM_TYPES] = {
    "不可缓存",               /* 0 */
    "写合并",                 /* 1 */
    "?",                      /* 2 */
    "?",                      /* 3 */
    "写穿透",                 /* 4 */
    "写保护",                 /* 5 */
    "写回",                   /* 6 */
};

int main () {
    int fd;
    struct mtrr_gentry gentry;

    if ((fd = open ("/proc/mtrr", O_RDONLY, 0)) == -1) {
        if (errno == ENOENT) {
            fputs ("/proc/mtrr 未找到: 不支持或您没有PPro?\n", stderr);
            exit (1);
        }
        fprintf (stderr, "打开 /proc/mtrr 出错\t%s\n", ERRSTRING);
        exit (2);
    }
    for (gentry.regnum = 0; ioctl (fd, MTRRIOC_GET_ENTRY, &gentry) == 0; ++gentry.regnum) {
        if (gentry.size < 1) {
            fprintf (stderr, "寄存器: %u 禁用\n", gentry.regnum);
            continue;
        }
        fprintf (stderr, "寄存器: %u 基址: 0x%lx 大小: 0x%lx 类型: %s\n",
            gentry.regnum, gentry.base, gentry.size, mtrr_strings[gentry.type]);
    }
    if (errno == EINVAL) exit (0);
    fprintf (stderr, "在 /dev/mtrr 上执行 ioctl(2) 出错\t%s\n", ERRSTRING);
    exit (3);
}   /*  主函数结束  */
```

使用ioctl()从C程序创建MTRRs
==================================

:: 

```c
/*  mtrr-add.c

    mtrr-add 源文件（示例程序，用于使用ioctl()添加MTRR）

    版权所有 © 1997-1998 Richard Gooch

    本程序是自由软件；您可以根据由自由软件基金会发布的GNU通用公共许可证的条款重新分发它和/或修改它；版本2或许可证的任何后续版本。

    本程序分发的目的是希望它能有所帮助，
    但是没有任何形式的保证；甚至不隐含保证适销性或适合于某一特定目的。详情请参阅GNU通用公共许可证。

    您应该随同本程序一起收到了一份GNU通用公共许可证的副本；如果没有，请写信给自由软件基金会，地址是Inc., 675 Mass Ave, Cambridge, MA 02139, USA

    可以通过电子邮件联系Richard Gooch：rgooch@atnf.csiro.au
    邮寄地址为：
        Richard Gooch, c/o ATNF, P. O. Box 76, Epping, N.S.W., 2121, 澳大利亚
*/

/*
    本程序将使用对 /proc/mtrr 的ioctl()来添加一个条目。使用第一个可用的MTRR。这是替代直接写入 /proc/mtrr 的方法。
编写者：Richard Gooch   1997年12月17日

    最后更新者：Richard Gooch   1998年5月2日
*/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <errno.h>
#include <asm/mtrr.h>

#define TRUE 1
#define FALSE 0
#define ERRSTRING strerror (errno)

static char *mtrr_strings[MTRR_NUM_TYPES] = {
    "不可缓存",               /* 0 */
    "写合并",                 /* 1 */
    "?",                      /* 2 */
    "?",                      /* 3 */
    "写穿透",                 /* 4 */
    "写保护",                 /* 5 */
    "写回",                   /* 6 */
};

int main (int argc, char **argv) {
    int fd;
    struct mtrr_sentry sentry;

    if (argc != 4) {
        fprintf (stderr, "用法:\tmtrr-add 基址 大小 类型\n");
        exit (1);
    }
    sentry.base = strtoul (argv[1], NULL, 0);
    sentry.size = strtoul (argv[2], NULL, 0);
    for (sentry.type = 0; sentry.type < MTRR_NUM_TYPES; ++sentry.type) {
        if (strcmp (argv[3], mtrr_strings[sentry.type]) == 0) break;
    }
    if (sentry.type >= MTRR_NUM_TYPES) {
        fprintf (stderr, "非法类型: \"%s\"\n", argv[3]);
        exit (2);
    }
    if ((fd = open ("/proc/mtrr", O_WRONLY, 0)) == -1) {
        if (errno == ENOENT) {
            fputs ("/proc/mtrr 未找到: 不支持或您没有PPro?\n", stderr);
            exit (3);
        }
        fprintf (stderr, "打开 /proc/mtrr 出错\t%s\n", ERRSTRING);
        exit (4);
    }
    if (ioctl (fd, MTRRIOC_ADD_ENTRY, &sentry) == -1) {
        fprintf (stderr, "在 /dev/mtrr 上执行 ioctl(2) 出错\t%s\n", ERRSTRING);
        exit (5);
    }
    fprintf (stderr, "暂停5秒以便您可以看到新的条目\n");
    sleep (5);
    close (fd);
    fputs ("我刚刚关闭了 /proc/mtrr 所以现在新的条目应该消失了\n", stderr);
}   /*  主函数结束  */
```
