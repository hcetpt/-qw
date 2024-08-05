===============================================
AArch64 Linux 中的内存标记扩展 (MTE)
===============================================

作者：Vincenzo Frascino <vincenzo.frascino@arm.com>
         Catalin Marinas <catalin.marinas@arm.com>

日期：2020-02-25

本文档描述了在 AArch64 Linux 中提供的内存标记扩展 (MTE) 功能。
引言
============

基于 ARMv8.5 的处理器引入了内存标记扩展 (MTE) 特性。MTE 是基于 ARMv8.0 虚拟地址标记 TBI (Top Byte Ignore) 特性构建的，并允许软件访问物理地址空间中每个 16 字节粒度的 4 位分配标签。
这样的内存范围必须使用 Normal-Tagged 内存属性进行映射。从用于内存访问的虚拟地址的第 59 至 56 位可得出一个逻辑标签。如果启用了 MTE 的 CPU 在系统寄存器配置的条件下检测到逻辑标签与分配标签不匹配，则可能会引发异常。
用户空间支持
=================

当选择了 `CONFIG_ARM64_MTE` 并且硬件支持内存标记扩展时，内核会通过 `HWCAP2_MTE` 向用户空间通告此功能。
PROT_MTE
--------

为了访问分配标签，用户进程必须使用为 `mmap()` 和 `mprotect()` 新增的 `prot` 标志在地址范围内启用标记内存属性：

`PROT_MTE` - 页面允许访问 MTE 分配标签
此类页面首次在用户地址空间中映射时，其分配标签被设置为 0，并且在复制写入时得以保留。支持 `MAP_SHARED`，并且分配标签可以在不同进程中共享。

**注意**：`PROT_MTE` 仅支持 `MAP_ANONYMOUS` 和基于 RAM 的文件映射 (`tmpfs`, `memfd`)。将其传递给其他类型的映射将导致这些系统调用返回 `-EINVAL`。

**注意**：`mprotect()` 无法清除 `PROT_MTE` 标志（及其对应的内存类型）。

**注意**：使用 `MADV_DONTNEED` 和 `MADV_FREE` 的 `madvise()` 内存范围可能会在系统调用之后的任何时刻将分配标签清零（设置为 0）。
标记检查错误
--------------

当为地址范围启用了 `PROT_MTE` 并且访问时发生逻辑和分配标签之间的不匹配时，存在三种可配置的行为：

- *忽略* - 这是默认模式。CPU（和内核）忽略标记检查错误
- **同步模式** - 内核同步地引发一个 ``SIGSEGV`` 信号，其中 ``.si_code = SEGV_MTESERR`` 并且 ``.si_addr = <故障地址>``。不会执行内存访问操作。如果 ``SIGSEGV`` 被忽略或被违规线程阻塞，则包含该线程的进程将通过生成“核心转储”(``coredump``)的方式终止。
- **异步模式** - 内核在违规线程中异步地引发一个 ``SIGSEGV`` 信号，在一个或多个标签检查故障之后，其中 ``.si_code = SEGV_MTEAERR`` 并且 ``.si_addr = 0``（故障地址未知）。
- **非对称模式** - 读取操作按同步模式处理，而写入操作则按异步模式处理。

用户可以使用 ``prctl(PR_SET_TAGGED_ADDR_CTRL, flags, 0, 0, 0)`` 系统调用来为每个线程选择上述模式，其中 ``flags`` 包含以下值中的任意数量，这些值位于 ``PR_MTE_TCF_MASK`` 位字段中：

- ``PR_MTE_TCF_NONE``  - 忽略标签检查故障（与其他选项组合时被忽略）
- ``PR_MTE_TCF_SYNC``  - 同步模式下的标签检查故障
- ``PR_MTE_TCF_ASYNC`` - 异步模式下的标签检查故障

如果没有指定任何模式，则忽略标签检查故障。如果指定了单一模式，程序将以该模式运行。如果指定了多个模式，则按照下面“每CPU首选的标签检查模式”部分所述进行选择。
当前的标签检查故障配置可以通过 ``prctl(PR_GET_TAGGED_ADDR_CTRL, 0, 0, 0, 0)`` 系统调用来读取。如果请求了多个模式，则所有模式都将被报告。
用户线程也可以通过设置 ``PSTATE.TCO`` 位来禁用标签检查，例如通过 ``MSR TCO, #1``。
**注意**：无论中断上下文如何，信号处理器总是被调用时 ``PSTATE.TCO = 0``。在 ``sigreturn()`` 时恢复 ``PSTATE.TCO`` 的值。
**注意**：对于用户应用程序，没有可用的“匹配所有”的逻辑标签。
**注意**：如果用户线程的标签检查模式是 ``PR_MTE_TCF_NONE`` 或 ``PR_MTE_TCF_ASYNC``，内核访问用户地址空间（如通过 ``read()`` 系统调用）将不会被检查。如果标签检查模式是 ``PR_MTE_TCF_SYNC``，内核会尽力检查其对用户地址空间的访问，但不能总是保证做到。无论用户配置如何，内核对用户地址的访问始终以有效的 ``PSTATE.TCO`` 值为零进行。

**排除``IRG``、``ADDG`` 和 ``SUBG`` 指令中的标签**

体系结构允许通过 ``GCR_EL1.Exclude`` 寄存器位字段排除某些标签的随机生成。默认情况下，Linux 排除了除 0 以外的所有标签。用户线程可以使用 ``prctl(PR_SET_TAGGED_ADDR_CTRL, flags, 0, 0, 0)`` 系统调用来启用随机生成集中的特定标签，其中 ``flags`` 包含 ``PR_MTE_TAG_MASK`` 位字段中的标签位图。
**注释**：硬件使用排除掩码，但`prctl()`接口提供的是包含掩码。一个包含掩码为`0`（排除掩码为`0xffff`）的结果是CPU始终生成标签`0`。

### 每CPU首选标签检查模式

在某些CPU上，更严格的标签检查模式的性能与较宽松的标签检查模式相似。这意味着，在请求了较宽松的检查模式时，为了获得更严格检查带来的错误检测益处而没有性能上的不利影响，启用更严格的检查是有意义的。为此类场景提供支持，特权用户可以配置更严格的标签检查模式作为CPU的首选标签检查模式。每个CPU的首选标签检查模式由`/sys/devices/system/cpu/cpu<N>/mte_tcf_preferred`控制，特权用户可以向其中写入值`async`、`sync`或`asymm`。每个CPU的默认首选模式是`async`。

为了让程序可能以CPU的首选标签检查模式运行，用户程序可以在`prctl(PR_SET_TAGGED_ADDR_CTRL, flags, 0, 0, 0)`系统调用的`flags`参数中设置多个标签检查故障模式位。如果同时请求同步和异步模式，则内核还可以选择非对称模式。如果CPU的首选标签检查模式在任务提供的标签检查模式集中，将选择该模式。否则，内核将从任务的模式集中按照以下优先顺序选择模式：

1. 异步
2. 非对称
3. 同步

请注意，用户空间无法同时请求多个模式并禁用非对称模式。

### 进程初始状态

在`execve()`时，新进程具有以下配置：

- `PR_TAGGED_ADDR_ENABLE` 设置为 0（禁用）
- 没有选择任何标签检查模式（忽略标签检查故障）
- `PR_MTE_TAG_MASK` 设置为 0（排除所有标签）
- `PSTATE.TCO` 设置为 0
- 初始内存映射上未设置 `PROT_MTE`

在`fork()`时，新进程继承父进程的配置和内存映射属性，除了带有`MADV_WIPEONFORK`的`madvise()`范围，这些范围的数据和标签将被清除（设置为 0）。

### `ptrace()`接口

`PTRACE_PEEKMTETAGS` 和 `PTRACE_POKEMTETAGS` 允许追踪者从被追踪者的地址空间读取标签或将标签设置到被追踪者的地址空间。通过`ptrace()`系统调用来调用，形式为`ptrace(request, pid, addr, data)`，其中：

- `request` - 可以是`PTRACE_PEEKMTETAGS`或`PTRACE_POKEMTETAGS`
- `pid` - 被追踪者的PID
- `addr` - 被追踪者地址空间中的地址
- `data` - 指向一个`struct iovec`的指针，其中`iov_base`指向追踪者地址空间中长度为`iov_len`的缓冲区

追踪者地址空间中的`iov_base`缓冲区中的标签表示为每字节一个4位标签，并对应于被追踪者地址空间中的一个16字节MTE标签粒度。
**注释**：如果 `addr` 没有对齐到 16 字节的粒度，内核将使用相应的已对齐地址。
`ptrace()` 的返回值：

- 0 - 标签已被复制，跟踪器的 `iov_len` 已更新为传输的标签数量。如果在被跟踪进程或跟踪器的空间中请求的地址范围无法访问或没有有效的标签，则这个数量可能小于请求的 `iov_len`。
- `-EPERM` - 指定的进程无法被跟踪。
- `-EIO` - 被跟踪进程的地址范围无法访问（例如，无效地址），且没有复制任何标签。`iov_len` 不会被更新。
- `-EFAULT` - 访问跟踪器的内存时出错（`struct iovec` 或 `iov_base` 缓冲区），且没有复制任何标签。`iov_len` 不会被更新。
- `-EOPNOTSUPP` - 被跟踪进程的地址没有有效的标签（从未使用 `PROT_MTE` 标志映射）。`iov_len` 不会被更新。

**注释**：对于上述请求不存在瞬态错误，因此用户程序不应该在系统调用返回非零值时重试。
`PTRACE_GETREGSET` 和 `PTRACE_SETREGSET` 与 `addr == NT_ARM_TAGGED_ADDR_CTRL` 结合使用允许 `ptrace()` 访问进程的标记地址 ABI 控制和 MTE 配置，正如 `prctl()` 选项中所描述的那样，具体说明在 `Documentation/arch/arm64/tagged-address-abi.rst` 及上文所述。对应的 `regset` 是一个 8 字节（`sizeof(long)`）的元素。

### 核转储支持

使用 `PROT_MTE` 映射的用户内存的分配标签会作为额外的 `PT_AARCH64_MEMTAG_MTE` 段落存储在核心文件中。此类段落的程序头定义如下：

- `p_type`: `PT_AARCH64_MEMTAG_MTE`
- `p_flags`: 0
- `p_offset`: 段落文件偏移量
- `p_vaddr`: 段落虚拟地址，与对应的 `PT_LOAD` 段落相同
- `p_paddr`: 0
- `p_filesz`: 文件中的段落大小，计算方式为 `p_mem_sz / 32` （两个 4 位标签覆盖 32 字节的内存）
- `p_memsz`: 内存中的段落大小，与对应的 `PT_LOAD` 段落相同
- `p_align`: 0

标签以每字节两个 4 位标签的形式存储在核心文件中的 `p_offset` 处。由于标签粒度为 16 字节，一个 4K 页需要 128 字节的核心文件空间。

### 正确使用的示例

#### MTE 示例代码

```c
/*
 * 使用 -march=armv8.5-a+memtag 编译
 */
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/auxv.h>
#include <sys/mman.h>
#include <sys/prctl.h>

/*
 * 从 arch/arm64/include/uapi/asm/hwcap.h 引入
 */
#define HWCAP2_MTE              (1 << 18)

/*
 * 从 arch/arm64/include/uapi/asm/mman.h 引入
 */
#define PROT_MTE                 0x20

/*
 * 从 include/uapi/linux/prctl.h 引入
 */
#define PR_SET_TAGGED_ADDR_CTRL 55
#define PR_GET_TAGGED_ADDR_CTRL 56
#define PR_TAGGED_ADDR_ENABLE  (1UL << 0)
#define PR_MTE_TCF_SHIFT       1
#define PR_MTE_TCF_NONE        (0UL << PR_MTE_TCF_SHIFT)
#define PR_MTE_TCF_SYNC        (1UL << PR_MTE_TCF_SHIFT)
#define PR_MTE_TCF_ASYNC       (2UL << PR_MTE_TCF_SHIFT)
#define PR_MTE_TCF_MASK        (3UL << PR_MTE_TCF_SHIFT)
#define PR_MTE_TAG_SHIFT       3
#define PR_MTE_TAG_MASK        (0xffffUL << PR_MTE_TAG_SHIFT)

/*
 * 在给定指针中插入一个随机逻辑标签
 */ 
```
下面是给定的 C 代码段翻译成中文的注释和说明：

```c
// 定义一个宏，用于在指针上插入随机标签
#define insert_random_tag(ptr) ({                       \
            uint64_t __val;                                 \
            asm("irg %0, %1" : "=r" (__val) : "r" (ptr));   \
            __val;                                          \
    })

/*
 * 在目标地址设置标签
*/
#define set_tag(tagged_addr) do {                                      \
            asm volatile("stg %0, [%0]" : : "r" (tagged_addr) : "memory"); \
    } while (0)

int main()
{
        unsigned char *a;
        unsigned long page_sz = sysconf(_SC_PAGESIZE); // 获取页面大小
        unsigned long hwcap2 = getauxval(AT_HWCAP2); // 获取硬件功能

        /* 检查是否支持 MTE */
        if (!(hwcap2 & HWCAP2_MTE))
                return EXIT_FAILURE;

        /*
         * 启用带有标签的地址 ABI，启用同步或异步 MTE 标签检查错误（基于每个 CPU 的偏好）
         * 并允许在随机生成的集合中使用所有非零标签
         */
        if (prctl(PR_SET_TAGGED_ADDR_CTRL,
                  PR_TAGGED_ADDR_ENABLE | PR_MTE_TCF_SYNC | PR_MTE_TCF_ASYNC |
                  (0xfffe << PR_MTE_TAG_SHIFT),
                  0, 0, 0)) {
                perror("prctl() failed");
                return EXIT_FAILURE;
        }

        a = mmap(0, page_sz, PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0); // 匿名映射内存
        if (a == MAP_FAILED) {
                perror("mmap() failed");
                return EXIT_FAILURE;
        }

        /*
         * 在上述匿名 mmap 上启用 MTE。该标志可以直接传递给 mmap() 并跳过此步骤
         */
        if (mprotect(a, page_sz, PROT_READ | PROT_WRITE | PROT_MTE)) {
                perror("mprotect() failed");
                return EXIT_FAILURE;
        }

        /* 使用默认标签 (0) 访问 */
        a[0] = 1;
        a[1] = 2;

        printf("a[0] = %hhu a[1] = %hhu\n", a[0], a[1]);

        /* 设置逻辑和分配标签 */
        a = (unsigned char *)insert_random_tag(a);
        set_tag(a);

        printf("%p\n", a);

        /* 非零标签访问 */
        a[0] = 3;
        printf("a[0] = %hhu a[1] = %hhu\n", a[0], a[1]);

        /*
         * 如果 MTE 正确启用，则下一条指令将触发异常
         */
        printf("Expecting SIGSEGV...\n");
        a[16] = 0xdd;

        /* 在 PR_MTE_TCF_SYNC 模式下，这行不应该被打印 */
        printf("...haven't got one\n");

        return EXIT_FAILURE;
}
```

以上是将原始英文注释和代码描述翻译为中文的过程。
