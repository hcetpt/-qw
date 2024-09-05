故障注入能力基础设施
===========================================

另见 drivers/md/md-faulty.c 和 scsi_debug 的 "every_nth" 模块选项
可用的故障注入能力
--------------------------------------

- failslab

  注入 slab 分配失败。 (kmalloc(), kmem_cache_alloc(), ...)

- fail_page_alloc

  注入页面分配失败。 (alloc_pages(), get_free_pages(), ...)

- fail_usercopy

  注入用户内存访问函数中的失败。 (copy_from_user(), get_user(), ...)

- fail_futex

  注入 futex 死锁和 uaddr 故障错误

- fail_sunrpc

  注入内核 RPC 客户端和服务器故障

- fail_make_request

  在允许的设备上注入磁盘 I/O 错误，通过设置 /sys/block/<device>/make-it-fail 或
  /sys/block/<device>/<partition>/make-it-fail。 (submit_bio_noacct())

- fail_mmc_request

  在允许的设备上注入 MMC 数据错误，通过设置 /sys/kernel/debug/mmc0/fail_mmc_request 中的调试文件系统条目

- fail_function

  在特定函数中注入错误返回值，这些函数由 ALLOW_ERROR_INJECTION() 宏标记，通过设置 /sys/kernel/debug/fail_function 中的调试文件系统条目。不支持引导选项

- NVMe 故障注入

  在允许的设备上注入 NVMe 状态码和重试标志，通过设置 /sys/kernel/debug/nvme*/fault_inject 中的调试文件系统条目。默认状态码是 NVME_SC_INVALID_OPCODE 并且不重试。状态码和重试标志可以通过调试文件系统设置

- Null 测试块驱动器故障注入

  通过设置 /sys/kernel/config/nullb/<disk>/timeout_inject 中的配置项来注入 I/O 超时，
  通过设置 /sys/kernel/config/nullb/<disk>/requeue_inject 中的配置项来注入重新排队请求，
  以及通过设置 /sys/kernel/config/nullb/<disk>/init_hctx_fault_inject 中的配置项来注入 init_hctx() 错误

配置故障注入能力的行为
-----------------------------------------------

调试文件系统条目
^^^^^^^^^^^^^^^

fault-inject-debugfs 内核模块提供了一些调试文件系统条目用于运行时配置故障注入能力
- /sys/kernel/debug/fail*/probability:

  故障注入的概率，以百分比表示
格式: <百分比>

  注意对于某些测试用例，每一百次有一失败是非常高的错误率。考虑将 probability 设置为 100，并为这些测试用例配置 /sys/kernel/debug/fail*/interval
- /sys/kernel/debug/fail*/interval:

  指定故障之间的间隔，对于通过 should_fail() 的所有其他测试调用
请注意，如果您通过设置 interval > 1 来启用此功能，您可能需要将 probability 设置为 100。

- `/sys/kernel/debug/fail*/times:`

  指定最多可以发生多少次故障。值为 -1 表示“无限制”。

- `/sys/kernel/debug/fail*/space:`

  指定初始资源“预算”，每次调用 `should_fail(,size)` 时会减去 “size”。直到 “space” 达到零之前，故障注入会被抑制。

- `/sys/kernel/debug/fail*/verbose`

  格式：{ 0 | 1 | 2 }

  指定注入故障时消息的详细程度。'0' 表示不打印任何消息；'1' 只打印每条故障的一行日志；'2' 还会打印调用堆栈跟踪——这对于调试由故障注入揭示的问题非常有用。

- `/sys/kernel/debug/fail*/task-filter:`

  格式：{ 'Y' | 'N' }

  值为 'N' 禁用按进程过滤（默认）。任何正数则限制故障仅发生在指定进程上，这些进程在 `/proc/<pid>/make-it-fail==1` 中定义。

- `/sys/kernel/debug/fail*/require-start`, `/sys/kernel/debug/fail*/require-end`, `/sys/kernel/debug/fail*/reject-start`, `/sys/kernel/debug/fail*/reject-end:`

  指定在堆栈跟踪遍历时测试的虚拟地址范围。只有当遍历的堆栈中有某个调用者位于要求的范围内，并且没有调用者位于拒绝的范围内时，才会注入故障。

  默认要求的范围是 [0, ULONG_MAX)（整个虚拟地址空间）。
  默认拒绝的范围是 [0, 0)。

- `/sys/kernel/debug/fail*/stacktrace-depth:`

  指定在搜索位于 `[require-start, require-end)` 或 `[reject-start, reject-end)` 范围内的调用者时的最大堆栈跟踪深度。
- `/sys/kernel/debug/fail_page_alloc/ignore-gfp-highmem:`

  格式：{ 'Y' | 'N' }

  默认值为 'Y'，将其设置为 'N' 将会在高内存/用户分配（__GFP_HIGHMEM 分配）中注入失败

- `/sys/kernel/debug/failslab/ignore-gfp-wait:`
- `/sys/kernel/debug/fail_page_alloc/ignore-gfp-wait:`

  格式：{ 'Y' | 'N' }

  默认值为 'Y'，将其设置为 'N' 将会在可以睡眠的分配（__GFP_DIRECT_RECLAIM 分配）中注入失败

- `/sys/kernel/debug/fail_page_alloc/min-order:`

  指定要注入失败的最小页面分配顺序

- `/sys/kernel/debug/fail_futex/ignore-private:`

  格式：{ 'Y' | 'N' }

  默认值为 'N'，将其设置为 'Y' 将在处理私有（地址空间）futex 时禁用失败注入

- `/sys/kernel/debug/fail_sunrpc/ignore-client-disconnect:`

  格式：{ 'Y' | 'N' }

  默认值为 'N'，将其设置为 'Y' 将在 RPC 客户端上禁用断开注入

- `/sys/kernel/debug/fail_sunrpc/ignore-server-disconnect:`

  格式：{ 'Y' | 'N' }

  默认值为 'N'，将其设置为 'Y' 将在 RPC 服务器上禁用断开注入

- `/sys/kernel/debug/fail_sunrpc/ignore-cache-wait:`

  格式：{ 'Y' | 'N' }

  默认值为 'N'，将其设置为 'Y' 将在 RPC 服务器上禁用缓存等待注入

- `/sys/kernel/debug/fail_function/inject:`

  格式：{ 'function-name' | '!function-name' | '' }

  按名称指定错误注入的目标函数。如果函数名称以 '!' 开头，则表示从注入列表中移除该函数；如果不指定任何内容（''），则清空注入列表

- `/sys/kernel/debug/fail_function/injectable:`

  （只读）显示可注入错误的函数及其可指定的错误类型。错误类型将如下所示：
  - NULL: 返回值必须为 0
ERRNO: `retval` 必须为 -1 到 -MAX_ERRNO（-4096）之间
- ERR_NULL: `retval` 必须为 0 或 -1 到 -MAX_ERRNO（-4096）之间
- `/sys/kernel/debug/fail_function/<function-name>/retval:`

  指定要注入给定函数的“错误”返回值
  当用户指定一个新的注入条目时，这个文件将会被创建。
  注意，此文件只接受无符号值。因此，如果你想使用负数的 errno，
  最好使用 `printf` 而不是 `echo`，例如：
  ```
  $ printf %#x -12 > retval
  ```

启动选项
^^^^^^^^^^^

为了在 debugfs 不可用的情况下（早期启动阶段）注入故障，请使用以下启动选项：

```
failslab=
fail_page_alloc=
fail_usercopy=
fail_make_request=
fail_futex=
mmc_core.fail_request=<interval>,<probability>,<space>,<times>
```

proc 条目
^^^^^^^^^^^^

- `/proc/<pid>/fail-nth`，`/proc/self/task/<tid>/fail-nth`：

  向此文件写入整数 N 会使任务中的第 N 次调用失败。
  从该文件读取会返回一个整数值。值 '0' 表示之前通过写入该文件设置的故障已注入。
  正整数 N 表示故障尚未注入。
  注意，此文件启用了所有类型的故障（slab、futex 等）。
  此设置优先于所有其他通用 debugfs 设置（如概率、间隔、次数等）。
  但是特定功能设置（如 fail_futex/ignore-private）优先于它。
  此功能旨在对单个系统调用进行系统的故障测试。请参见下面的例子。
错误注入函数
--------------------------

这一部分是为考虑向 `ALLOW_ERROR_INJECTION()` 宏添加函数的内核开发者准备的。
错误注入函数的要求
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

由于函数级别的错误注入会强制改变代码路径，并且即使输入和条件正确也会返回错误，因此如果你允许在非错误注入函数上进行错误注入，则可能会导致意外的内核崩溃。因此，你（以及审查者）必须确保：

- 函数失败时返回一个错误码，并且调用者必须正确检查它（需要从中恢复）
- 函数在第一次返回错误之前不执行任何可能改变状态的代码。状态包括全局或局部变量，或者输入变量。例如，清除输出地址存储（如 `*ret = NULL`），增加/减少计数器，设置标志，抢占/中断禁用或获取锁（如果这些操作在返回错误前被恢复，则是可以接受的）

第一个要求非常重要，这意味着释放（释放对象）函数通常比分配函数更难注入错误。如果此类释放函数的错误处理不当，很容易导致内存泄漏（调用者会混淆该对象是否已被释放或损坏）。

第二个要求是为了满足期望函数始终执行某些操作的调用者。因此，如果函数错误注入跳过了整个函数，就会违背这种期望并导致意外错误。
错误注入函数的类型
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

每个错误注入函数将通过 `ALLOW_ERROR_INJECTION()` 宏指定错误类型。如果你添加新的错误注入函数，必须谨慎选择。如果选择了错误的错误类型，内核可能会崩溃，因为它可能无法处理该错误。
在 `include/asm-generic/error-injection.h` 中定义了 4 种错误类型：

EI_ETYPE_NULL
  如果此函数失败，则返回 `NULL`。例如，返回已分配的对象地址
EI_ETYPE_ERRNO
  如果此函数失败，则返回 `-errno` 错误码。例如，如果输入错误则返回 `-EINVAL`。这包括使用 `ERR_PTR()` 宏编码 `-errno` 的函数
EI_ETYPE_ERRNO_NULL
  如果此函数失败，则返回 `-errno` 或 `NULL`。如果调用者使用 `IS_ERR_OR_NULL()` 宏检查返回值，则此类型是适当的
EI_ETYPE_TRUE
  如果此函数失败，则返回 `true`（非零正数）

如果你指定了错误的类型，例如对于返回已分配对象的函数使用 EI_ETYPE_ERRNO，则可能会出现问题，因为返回的值不是对象地址，调用者无法访问该地址。
如何添加新的故障注入能力
-----------------------------------------

- `#include <linux/fault-inject.h>`

- 定义故障属性

  `DECLARE_FAULT_ATTR(name);`

  请参阅 `fault-inject.h` 中 `struct fault_attr` 的定义以了解详细信息
- 提供配置故障属性的方法

- 引导选项

  如果需要从启动时启用故障注入功能，您可以提供引导选项来配置它。有一个辅助函数用于此目的：

  ```c
  setup_fault_attr(attr, str);
  ```

- `debugfs` 条目

  `failslab`、`fail_page_alloc`、`fail_usercopy` 和 `fail_make_request` 使用这种方法。辅助函数如下：

  ```c
  fault_create_debugfs_attr(name, parent, attr);
  ```

- 模块参数

  如果故障注入功能的作用范围仅限于单个内核模块，最好提供模块参数来配置故障属性。

- 添加一个插入故障的钩子

  当 `should_fail()` 返回 `true` 时，客户端代码应注入一个故障：

  ```c
  should_fail(attr, size);
  ```

应用示例
--------

- 向模块初始化/退出代码中注入 slab 分配失败：

  ```bash
  #!/bin/bash

  FAILTYPE=failslab
  echo Y > /sys/kernel/debug/$FAILTYPE/task-filter
  echo 10 > /sys/kernel/debug/$FAILTYPE/probability
  echo 100 > /sys/kernel/debug/$FAILTYPE/interval
  echo -1 > /sys/kernel/debug/$FAILTYPE/times
  echo 0 > /sys/kernel/debug/$FAILTYPE/space
  echo 2 > /sys/kernel/debug/$FAILTYPE/verbose
  echo Y > /sys/kernel/debug/$FAILTYPE/ignore-gfp-wait

  faulty_system() {
      bash -c "echo 1 > /proc/self/make-it-fail && exec $*"
  }

  if [ $# -eq 0 ]; then
      echo "Usage: $0 modulename [ modulename ... ]"
      exit 1
  fi

  for m in $*; do
      echo inserting $m..
      faulty_system modprobe $m

      echo removing $m..
      faulty_system modprobe -r $m
  done
  ```

---

- 仅针对特定模块注入页面分配失败：

  ```bash
  #!/bin/bash

  FAILTYPE=fail_page_alloc
  module=$1

  if [ -z "$module" ]; then
      echo "Usage: $0 <modulename>"
      exit 1
  fi

  modprobe $module

  if [ ! -d "/sys/module/$module/sections" ]; then
      echo "Module $module is not loaded"
      exit 1
  fi

  cat /sys/module/$module/sections/.text > /sys/kernel/debug/$FAILTYPE/require-start
  cat /sys/module/$module/sections/.data > /sys/kernel/debug/$FAILTYPE/require-end

  echo N > /sys/kernel/debug/$FAILTYPE/task-filter
  echo 10 > /sys/kernel/debug/$FAILTYPE/probability
  echo 100 > /sys/kernel/debug/$FAILTYPE/interval
  echo -1 > /sys/kernel/debug/$FAILTYPE/times
  echo 0 > /sys/kernel/debug/$FAILTYPE/space
  echo 2 > /sys/kernel/debug/$FAILTYPE/verbose
  echo Y > /sys/kernel/debug/$FAILTYPE/ignore-gfp-wait
  echo Y > /sys/kernel/debug/$FAILTYPE/ignore-gfp-highmem
  echo 10 > /sys/kernel/debug/$FAILTYPE/stacktrace-depth

  trap "echo 0 > /sys/kernel/debug/$FAILTYPE/probability" SIGINT SIGTERM EXIT

  echo "Injecting errors into the module $module... (interrupt to stop)"
  sleep 1000000
  ```

---

- 在挂载 Btrfs 文件系统时注入 `open_ctree` 错误：

  ```bash
  #!/bin/bash

  rm -f testfile.img
  dd if=/dev/zero of=testfile.img bs=1M seek=1000 count=1
  DEVICE=$(losetup --show -f testfile.img)
  mkfs.btrfs -f $DEVICE
  mkdir -p tmpmnt

  FAILTYPE=fail_function
  FAILFUNC=open_ctree
  echo $FAILFUNC > /sys/kernel/debug/$FAILTYPE/inject
  printf %#x -12 > /sys/kernel/debug/$FAILTYPE/$FAILFUNC/retval
  echo N > /sys/kernel/debug/$FAILTYPE/task-filter
  echo 100 > /sys/kernel/debug/$FAILTYPE/probability
  echo 0 > /sys/kernel/debug/$FAILTYPE/interval
  echo -1 > /sys/kernel/debug/$FAILTYPE/times
  echo 0 > /sys/kernel/debug/$FAILTYPE/space
  echo 1 > /sys/kernel/debug/$FAILTYPE/verbose

  mount -t btrfs $DEVICE tmpmnt
  if [ $? -ne 0 ]; then
      echo "SUCCESS!"
  else
      echo "FAILED!"
      umount tmpmnt
  fi

  echo > /sys/kernel/debug/$FAILTYPE/inject

  rmdir tmpmnt
  losetup -d $DEVICE
  rm testfile.img
  ```

用于运行带有 `failslab` 或 `fail_page_alloc` 的命令的工具
----------------------------------------------------

为了更方便地完成上述任务，我们可以使用 `tools/testing/fault-injection/failcmd.sh`。请运行命令 `./tools/testing/fault-injection/failcmd.sh --help` 获取更多信息，并参见以下示例：

示例：

使用 slab 分配失败注入运行命令 `make -C tools/testing/selftests/ run_tests`：

  ```bash
  # ./tools/testing/fault-injection/failcmd.sh \
      -- make -C tools/testing/selftests/ run_tests
  ```

与上一个示例相同，但指定最多注入 100 次失败（默认为最多一次）：

  ```bash
  # ./tools/testing/fault-injection/failcmd.sh --times=100 \
      -- make -C tools/testing/selftests/ run_tests
  ```

与上一个示例相同，但注入页面分配失败而不是 slab 分配失败：

  ```bash
  # env FAILCMD_TYPE=fail_page_alloc \
      ./tools/testing/fault-injection/failcmd.sh --times=100 \
      -- make -C tools/testing/selftests/ run_tests
  ```

使用 `fail-nth` 进行系统性故障注入
--------------------------------------

以下代码在 `socketpair()` 系统调用中系统性地注入第 0 个、第 1 个、第 2 个等故障：

```c
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>

int main() {
    int i, err, res, fail_nth, fds[2];
    char buf[128];

    system("echo N > /sys/kernel/debug/failslab/ignore-gfp-wait");
    sprintf(buf, "/proc/self/task/%ld/fail-nth", syscall(SYS_gettid));
    fail_nth = open(buf, O_RDWR);
    for (i = 1;; i++) {
        sprintf(buf, "%d", i);
        write(fail_nth, buf, strlen(buf));
        res = socketpair(AF_LOCAL, SOCK_STREAM, 0, fds);
        err = errno;
        pread(fail_nth, buf, sizeof(buf), 0);
        if (res == 0) {
            close(fds[0]);
            close(fds[1]);
        }
        printf("%d-th fault %c: res=%d/%d\n", i, atoi(buf) ? 'N' : 'Y', res, err);
        if (atoi(buf))
            break;
    }
    return 0;
}
```

示例输出：

```
1-th fault Y: res=-1/23
2-th fault Y: res=-1/23
3-th fault Y: res=-1/12
4-th fault Y: res=-1/12
5-th fault Y: res=-1/23
6-th fault Y: res=-1/23
7-th fault Y: res=-1/23
8-th fault Y: res=-1/12
9-th fault Y: res=-1/12
10-th fault Y: res=-1/12
11-th fault Y: res=-1/12
12-th fault Y: res=-1/12
13-th fault Y: res=-1/12
14-th fault Y: res=-1/12
15-th fault Y: res=-1/12
16-th fault N: res=0/12
```
