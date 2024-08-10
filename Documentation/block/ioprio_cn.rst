===================
区块 I/O 优先级
===================

简介
-----

I/O 优先级功能使用户能够为进程或进程组设置 I/O 优先级，类似于长期以来在 CPU 调度中可以做到的方式。I/O 优先级的支持依赖于 I/O 调度程序，并且目前由 BFQ 和 mq-deadline 支持。

调度类别
------------------

为 I/O 优先级实现了三种通用的调度类别，这些类别决定了进程如何获取 I/O 服务：

IOPRIO_CLASS_RT：这是实时 I/O 类别。此调度类别比系统中的任何其他类别具有更高的优先级，来自此类别的进程总是最先获得磁盘访问权。因此，使用时需要谨慎，一个实时 I/O 进程可能会导致整个系统饥饿。在实时类别内部，有 8 个级别来确定每次服务时该进程需要占用磁盘多长时间。未来可能会改变这种方式，通过指定所需的数据速率来更直接地映射到性能。
IOPRIO_CLASS_BE：这是尽力而为的调度类别，默认情况下，任何未设置特定 I/O 优先级的进程都属于此类别。类数据确定了进程将获得多少 I/O 带宽，它与 CPU 的优先级等级直接相关，但实现得更粗糙一些。0 是最高的 BE 优先级级别，7 是最低的。CPU 优先级和 I/O 优先级之间的映射关系为：io_nice = (cpu_nice + 20) / 5。
IOPRIO_CLASS_IDLE：这是空闲调度类别，在这个级别的进程只有当其他进程都不需要磁盘时才能获得 I/O 时间。空闲类别没有类数据，因为它在这里并不适用。

工具
-----

下面是一个示例的 ionice 工具。用法如下：

```
# ionice -c<class> -n<level> -p<pid>
```

如果不指定 pid，则默认为当前进程。I/O 优先级设置在 fork 时会被继承，所以您可以使用 ionice 在给定的级别启动进程：

```
# ionice -c2 -n0 /bin/ls
```

这将以最高的优先级运行 ls 命令，在尽力而为的调度类别中。
对于正在运行的进程，您可以指定 pid：

```
# ionice -c1 -n2 -p100
```

这会将 pid 100 更改为以实时调度类别运行，优先级为 2。
ionice.c 工具代码：

```c
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <getopt.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include <asm/unistd.h>

extern int sys_ioprio_set(int, int, int);
extern int sys_ioprio_get(int, int);

#if defined(__i386__)
#define __NR_ioprio_set         289
#define __NR_ioprio_get         290
#elif defined(__ppc__)
#define __NR_ioprio_set         273
#define __NR_ioprio_get         274
#elif defined(__x86_64__)
#define __NR_ioprio_set         251
#define __NR_ioprio_get         252
#else
#error "Unsupported architecture"
#endif

static inline int ioprio_set(int which, int who, int ioprio)
{
    return syscall(__NR_ioprio_set, which, who, ioprio);
}

static inline int ioprio_get(int which, int who)
{
    return syscall(__NR_ioprio_get, which, who);
}

enum {
    IOPRIO_CLASS_NONE,
    IOPRIO_CLASS_RT,
    IOPRIO_CLASS_BE,
    IOPRIO_CLASS_IDLE,
};

enum {
    IOPRIO_WHO_PROCESS = 1,
    IOPRIO_WHO_PGRP,
    IOPRIO_WHO_USER,
};

#define IOPRIO_CLASS_SHIFT 13

const char *to_prio[] = { "none", "realtime", "best-effort", "idle", };

int main(int argc, char *argv[])
{
    int ioprio = 4, set = 0, ioprio_class = IOPRIO_CLASS_BE;
    int c, pid = 0;

    while ((c = getopt(argc, argv, "+n:c:p:")) != EOF) {
        switch (c) {
        case 'n':
            ioprio = strtol(optarg, NULL, 10);
            set = 1;
            break;
        case 'c':
            ioprio_class = strtol(optarg, NULL, 10);
            set = 1;
            break;
        case 'p':
            pid = strtol(optarg, NULL, 10);
            break;
        }
    }

    switch (ioprio_class) {
    case IOPRIO_CLASS_NONE:
        ioprio_class = IOPRIO_CLASS_BE;
        break;
    case IOPRIO_CLASS_RT:
    case IOPRIO_CLASS_BE:
        break;
    case IOPRIO_CLASS_IDLE:
        ioprio = 7;
        break;
    default:
        printf("bad prio class %d\n", ioprio_class);
        return 1;
    }

    if (!set) {
        if (!pid && argv[optind])
            pid = strtol(argv[optind], NULL, 10);

        ioprio = ioprio_get(IOPRIO_WHO_PROCESS, pid);

        printf("pid=%d, %d\n", pid, ioprio);

        if (ioprio == -1)
            perror("ioprio_get");
        else {
            ioprio_class = ioprio >> IOPRIO_CLASS_SHIFT;
            ioprio = ioprio & 0xff;
            printf("%s: prio %d\n", to_prio[ioprio_class], ioprio);
        }
    } else {
        if (ioprio_set(IOPRIO_WHO_PROCESS, pid, ioprio | ioprio_class << IOPRIO_CLASS_SHIFT) == -1) {
            perror("ioprio_set");
            return 1;
        }

        if (argv[optind])
            execvp(argv[optind], &argv[optind]);
    }

    return 0;
}
```

2005年3月11日，Jens Axboe <jens.axboe@oracle.com>
