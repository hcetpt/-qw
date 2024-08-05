### SPDX 许可证标识符: GPL-2.0

==================================
特定于 x86 的 ELF 辅助向量
==================================

本文档描述了 x86 辅助向量的语义。

#### 引言

ELF 辅助向量使内核能够高效地向用户空间提供配置特定参数。在下面的例子中，一个程序根据内核提供的大小分配了一个备用栈：

```c
#include <sys/auxv.h>
#include <elf.h>
#include <signal.h>
#include <stdlib.h>
#include <assert.h>
#include <err.h>

#ifndef AT_MINSIGSTKSZ
#define AT_MINSIGSTKSZ 51
#endif

...

stack_t ss;

ss.ss_sp = malloc(ss.ss_size);
assert(ss.ss_sp != NULL);

ss.ss_size = getauxval(AT_MINSIGSTKSZ) + SIGSTKSZ;
ss.ss_flags = 0;

if (sigaltstack(&ss, NULL)) {
    err(1, "sigaltstack");
}
```

#### 暴露的辅助向量

- `AT_SYSINFO` 用于定位 vsyscall 的入口点。在 64 位模式下不导出。
- `AT_SYSINFO_EHDR` 是包含 vDSO 的页面的起始地址。
- `AT_MINSIGSTKSZ` 表示内核为了向用户空间发送信号所需的最小栈大小。`AT_MINSIGSTKSZ` 考虑了内核为适应当前硬件配置下的用户上下文所占用的空间。它不包括后续用户空间栈的消耗，这部分需要用户自行添加。（例如，在上面的代码中，用户空间会在 `AT_MINSIGSTKSZ` 上加上 `SIGSTKSZ`。）
