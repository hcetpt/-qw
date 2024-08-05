==================================================
Linux 中的 ARM TCM（紧密耦合内存）处理
==================================================

作者：Linus Walleij <linus.walleij@stericsson.com>

一些 ARM 系统芯片具有所谓的 TCM（紧密耦合内存）。
这通常只是位于 ARM 处理器内部的几 KB（4-64KB）的 RAM。
由于它嵌入在 CPU 内部，TCM 采用了哈佛架构，因此有 ITCM（指令 TCM）和 DTCM（数据 TCM）。DTCM 不能包含任何指令，但 ITCM 实际上可以包含数据。
DTCM 或 ITCM 的大小至少为 4KB，因此最典型的最小配置是 4KB 的 ITCM 和 4KB 的 DTCM。
ARM CPU 有专用寄存器来读取 TCM 内存的状态、物理位置和大小。`arch/arm/include/asm/cputype.h` 定义了一个可以从系统控制协处理器读取的 CPUID_TCM 寄存器。ARM 的文档可以在 http://infocenter.arm.com 找到，搜索“TCM 状态寄存器”以查看所有 CPU 的相关文档。通过读取此寄存器，您可以确定机器中是否存在 ITCM（位 1-0）和/或 DTCM（位 17-16）。
此外还有一个 TCM 区域寄存器（在 ARM 网站上搜索“TCM 区域寄存器”），它可以报告并在运行时修改 TCM 内存的位置和大小。这是用来读取和修改 TCM 位置和大小的。需要注意的是这不是一个 MMU 表：您实际上是在移动 TCM 的物理位置。在您放置它的位置，它会屏蔽掉 CPU 下方的任何底层 RAM，因此通常明智的做法是不要让 TCM 与任何物理 RAM 重叠。
然后可以使用 MMU 将 TCM 内存重新映射到另一个地址，但需要注意的是 TCM 经常被用于 MMU 关闭的情况。为了避免混淆，当前的 Linux 实现将从物理内存到虚拟内存按 1:1 映射 TCM 至内核指定的位置。目前 Linux 将 ITCM 映射到 0xfffe0000 及以后的地址，而 DTCM 映射到 0xfffe8000 及以后的地址，支持最大 32KB 的 ITCM 和 32KB 的 DTCM。
TCM 区域寄存器的新版本还支持将这些 TCM 分成两个独立的存储库，例如，8KB 的 ITCM 被分成两个 4KB 的存储库，每个存储库都有自己的控制寄存器。其目的是能够锁定并隐藏其中一个存储库供安全世界（如 TrustZone）使用。
TCM 用于以下几个方面：

- 需要确定性时序且不能等待缓存缺失的 FIQ 和其他中断处理程序
- 在所有外部 RAM 设置为自刷新保留模式的空闲循环中，只有片上 RAM 可由 CPU 访问，并且我们在 ITCM 中挂起等待中断
其他操作可能涉及关闭或重新配置外部RAM控制器。
在<asm/tcm.h>中有一个用于ARM架构上使用TCM（Tightly Coupled Memory）的接口。通过这个接口，可以实现：

- 定义ITCM和DTCM的物理地址及大小
- 标记需要编译到ITCM中的函数
- 标记需要分配到DTCM和ITCM的数据和常量
- 使用`gen_pool_create()`和`gen_pool_add()`将剩余的TCM RAM添加到一个特殊的分配池，并提供`tcm_alloc()`和`tcm_free()`来管理这部分内存。这样的堆非常适合用于保存在关闭设备电源域时的设备状态

拥有TCM内存的机器应当从arch/arm/Kconfig中选择HAVE_TCM。需要使用TCM的代码应当包含<asm/tcm.h>。

要放入ITCM中的函数可以这样标记：
```c
int __tcmfunc foo(int bar);
```

由于这些函数被标记为长调用(long_calls)，如果你希望在TCM内部进行局部调用而不浪费空间，还可以使用`__tcmlocalfunc`前缀使调用变为相对调用。

要放入DTCM中的变量可以这样标记：
```c
int __tcmdata foo;
```

常量可以这样标记：
```c
int __tcmconst foo;
```

要将汇编代码放入TCM中，只需使用：
```c
.section ".tcm.text" 或 .section ".tcm.data"
```

示例代码：
```c
#include <asm/tcm.h>

/* 未初始化的数据 */
static u32 __tcmdata tcmvar;
/* 已初始化的数据 */
static u32 __tcmdata tcmassigned = 0x2BADBABEU;
/* 常量 */
static const u32 __tcmconst tcmconst = 0xCAFEBABEU;

static void __tcmlocalfunc tcm_to_tcm(void)
{
    int i;
    for (i = 0; i < 100; i++)
        tcmvar ++;
}

static void __tcmfunc hello_tcm(void)
{
    /* 一些抽象代码，在ITCM中运行 */
    int i;
    for (i = 0; i < 100; i++) {
        tcmvar ++;
    }
    tcm_to_tcm();
}

static void __init test_tcm(void)
{
    u32 *tcmem;
    int i;

    hello_tcm();
    printk("Hello TCM executed from ITCM RAM\n");

    printk("TCM variable from testrun: %u @ %p\n", tcmvar, &tcmvar);
    tcmvar = 0xDEADBEEFU;
    printk("TCM variable: 0x%x @ %p\n", tcmvar, &tcmvar);

    printk("TCM assigned variable: 0x%x @ %p\n", tcmassigned, &tcmassigned);

    printk("TCM constant: 0x%x @ %p\n", tcmconst, &tcmconst);

    /* 从池中分配一些TCM内存 */
    tcmem = tcm_alloc(20);
    if (tcmem) {
        printk("TCM Allocated 20 bytes of TCM @ %p\n", tcmem);
        tcmem[0] = 0xDEADBEEFU;
        tcmem[1] = 0x2BADBABEU;
        tcmem[2] = 0xCAFEBABEU;
        tcmem[3] = 0xDEADBEEFU;
        tcmem[4] = 0x2BADBABEU;
        for (i = 0; i < 5; i++)
            printk("TCM tcmem[%d] = %08x\n", i, tcmem[i]);
        tcm_free(tcmem, 20);
    }
}
```
