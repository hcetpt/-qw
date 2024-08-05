==========================
AArch64 标记地址 ABI
==========================

作者: Vincenzo Frascino <vincenzo.frascino@arm.com>
         Catalin Marinas <catalin.marinas@arm.com>

日期: 2019年8月21日

本文档描述了在AArch64 Linux上标记地址ABI的使用和语义。
1. 引言
---------------

在AArch64架构中，默认设置`TCR_EL1.TBI0`位，允许用户空间（EL0）通过非零高位字节的64位指针进行内存访问。本文档描述了对系统调用ABI的放宽，这使得用户空间能够将某些带有标记的指针传递给内核系统调用。
2. AArch64 标记地址 ABI
-----------------------------

从内核系统调用接口的角度来看，并且就本文档的目的而言，“有效的标记指针”是指一个可能具有非零高位字节的指针，它引用的是用户进程地址空间中的地址，该地址可以通过以下方式之一获得：

- `mmap()`系统调用，其中：
  
  - 标志设置了`MAP_ANONYMOUS`位或
  - 文件描述符指向常规文件（包括由`memfd_create()`返回的那些文件或`/dev/zero`）

- `brk()`系统调用（即，在进程创建时程序断点的初始位置与当前位置之间的堆区）
- 任何在进程创建期间由内核映射到进程地址空间的内存，其限制与上面的`mmap()`相同（例如：数据段、bss段、栈段）
AArch64 标记地址 ABI根据内核如何使用用户地址分为两个阶段的放宽：

1. 内核不直接访问的用户地址，但用于地址空间管理（例如`mprotect()`、`madvise()`）。在这种情况下使用有效标记指针是允许的，除了以下情况：

   - `brk()`、`mmap()`以及`mremap()`的`new_address`参数，因为这些有可能与现有的用户地址产生别名
注意: 这种行为在v5.6版本有所改变，因此一些早期的内核可能会错误地接受`brk()`、`mmap()`和`mremap()`系统调用的有效标记指针。
- 使用从`userfaultfd()`获取的文件描述符进行的`UFFDIO_*` `ioctl()`调用的`range.start`、`start`和`dst`参数，因为随后通过读取该文件描述符获得的故障地址将是未标记的，这可能会使不了解标记的程序混淆。
注意: 这种行为在v5.14版本有所改变，因此一些早期的内核可能会错误地接受此系统调用的有效标记指针。
2. 被内核访问的用户地址（例如`write()`）。这种ABI放宽默认是禁用的，应用程序线程需要通过`prctl()`显式启用它如下：

   - `PR_SET_TAGGED_ADDR_CTRL`：为调用线程启用或禁用AArch64 标记地址 ABI
`(unsigned int) arg2`参数是一个位掩码，描述所使用的控制模式：

     - `PR_TAGGED_ADDR_ENABLE`：启用AArch64 标记地址 ABI
默认状态是禁用的。
参数 `arg3`、`arg4` 和 `arg5` 必须为 0。
- `PR_GET_TAGGED_ADDR_CTRL`：获取调用线程的 AArch64 标记地址 ABI 状态
参数 `arg2`、`arg3`、`arg4` 和 `arg5` 必须为 0。
上述 ABI 属性是针对每个线程的，会在 `clone()` 和 `fork()` 时继承，并在 `exec()` 时清除。
调用 `prctl(PR_SET_TAGGED_ADDR_CTRL, PR_TAGGED_ADDR_ENABLE, 0, 0, 0)` 如果全局禁用了AArch64 标记地址 ABI（即通过 `sysctl abi.tagged_addr_disabled=1` 设置），将返回 `-EINVAL`。默认的 `sysctl abi.tagged_addr_disabled` 配置值为 0。
当为一个线程启用了 AArch64 标记地址 ABI 时，以下行为得到保证：

- 除了第 3 节中提到的情况外，所有系统调用都可以接受任何有效的标记指针。
- 对于无效的标记指针，系统调用的行为是未定义的：可能会返回错误代码，引发（致命的）信号或其他形式的失败。
- 对于有效标记指针的系统调用行为与相应的未标记指针相同。
关于 AArch64 上标记指针的定义可以在 `Documentation/arch/arm64/tagged-pointers.rst` 中找到。
3. AArch64 标记地址 ABI 异常
-----------------------------------------

无论 ABI 放宽与否，以下系统调用参数必须去除标记：

- `prctl()`：除了直接或间接作为参数传递给内核访问的用户数据指针外
- `ioctl()`：除了直接或间接作为参数传递给内核访问的用户数据指针外
- `shmat()` 和 `shmdt()`
- `brk()`（自内核版本 5.6 起）
- `mmap()`（自内核版本 5.6 起）
- `mremap()`，`new_address` 参数（自内核版本 5.6 起）

任何尝试使用非零标记指针的行为都可能导致返回错误码、引发致命信号或其他形式的失败。
4. 正确使用的示例
---------------------------

```c
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/prctl.h>

#define PR_SET_TAGGED_ADDR_CTRL   55
#define PR_TAGGED_ADDR_ENABLE     (1UL << 0)

#define TAG_SHIFT          56

int main(void)
{
    int tbi_enabled = 0;
    unsigned long tag = 0;
    char *ptr;

    /* 检查并启用标记地址 ABI */
    if (!prctl(PR_SET_TAGGED_ADDR_CTRL, PR_TAGGED_ADDR_ENABLE, 0, 0, 0))
        tbi_enabled = 1;

    /* 内存分配 */
    ptr = mmap(NULL, sysconf(_SC_PAGE_SIZE), PROT_READ | PROT_WRITE,
               MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (ptr == MAP_FAILED)
        return 1;

    /* 如果 ABI 可用，则设置非零标记 */
    if (tbi_enabled)
        tag = rand() & 0xff;
    ptr = (char *)((unsigned long)ptr | (tag << TAG_SHIFT));

    /* 对标记地址进行内存访问 */
    strcpy(ptr, "tagged pointer\n");

    /* 带有标记指针的系统调用 */
    write(1, ptr, strlen(ptr));

    return 0;
}
```
