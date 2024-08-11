### KCOV：用于模糊测试的代码覆盖率

KCOV收集并以适合指导性模糊测试的形式公开内核代码覆盖率信息。运行中的内核的覆盖率数据通过`kcov`调试文件系统（debugfs）导出。覆盖率收集基于任务进行，因此KCOV能够捕捉单一系统调用的确切覆盖率。需要注意的是，KCOV的目标并不是尽可能多地收集覆盖率，而是收集或多或少稳定的、与系统调用输入相关的覆盖率。为了实现这一目标，它不会在软中断/硬中断中收集覆盖率（除非启用了移除覆盖率收集功能，见下文），也不会从内核中一些本质上非确定性的部分（例如调度器、锁定机制等）收集覆盖率。

除了收集代码覆盖率之外，KCOV还可以收集比较操作数。有关详细信息，请参阅“比较操作数收集”部分。除了从系统调用处理程序中收集覆盖率数据外，KCOV还可以收集在后台内核任务或软中断中执行的已注释内核部分的覆盖率。详情请参阅“远程覆盖率收集”部分。

### 前提条件

KCOV依赖于编译器插桩，并且需要GCC 6.1.0或更高版本，或内核支持的任何Clang版本。
收集比较操作数支持GCC 8+或Clang。

要启用KCOV，请配置内核如下：

        CONFIG_KCOV=y

要启用比较操作数收集，请设置：

	CONFIG_KCOV_ENABLE_COMPARISONS=y

只有在挂载了debugfs之后，覆盖率数据才变得可访问：

        mount -t debugfs none /sys/kernel/debug

### 覆盖率收集

以下程序演示了如何在测试程序中使用KCOV为单一系统调用收集覆盖率：

```c
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <fcntl.h>
#include <linux/types.h>

#define KCOV_INIT_TRACE			_IOR('c', 1, unsigned long)
#define KCOV_ENABLE			_IO('c', 100)
#define KCOV_DISABLE			_IO('c', 101)
#define COVER_SIZE			(64<<10)

#define KCOV_TRACE_PC  0
#define KCOV_TRACE_CMP 1

int main(int argc, char **argv)
{
	int fd;
	unsigned long *cover, n, i;

	/* 单个文件描述符允许对单个线程进行覆盖率收集 */
	fd = open("/sys/kernel/debug/kcov", O_RDWR);
	if (fd == -1)
		perror("open"), exit(1);
	/* 设置跟踪模式和跟踪大小 */
	if (ioctl(fd, KCOV_INIT_TRACE, COVER_SIZE))
		perror("ioctl"), exit(1);
	/* 映射内核空间和用户空间共享的缓冲区 */
	cover = (unsigned long*)mmap(NULL, COVER_SIZE * sizeof(unsigned long),
				     PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if ((void*)cover == MAP_FAILED)
		perror("mmap"), exit(1);
	/* 启用当前线程的覆盖率收集 */
	if (ioctl(fd, KCOV_ENABLE, KCOV_TRACE_PC))
		perror("ioctl"), exit(1);
	/* 重置ioctl()调用尾部的覆盖率 */
	__atomic_store_n(&cover[0], 0, __ATOMIC_RELAXED);
	/* 调用目标系统调用 */
	read(-1, NULL, 0);
	/* 读取收集到的PC数量 */
	n = __atomic_load_n(&cover[0], __ATOMIC_RELAXED);
	for (i = 0; i < n; i++)
		printf("0x%lx\n", cover[i + 1]);
	/* 禁用当前线程的覆盖率收集。在此调用后，
	 * 可以为不同的线程启用覆盖率 */
```
请注意，上述示例代码未完整展示整个过程，仅作为示例说明如何使用KCOV。
下面是提供的C代码段及其注释的中文翻译：

如果`ioctl(fd, KCOV_DISABLE, 0)`失败，
则输出错误信息并退出程序。
/* 释放资源。 */
如果`munmap(cover, COVER_SIZE * sizeof(unsigned long))`失败，
则输出错误信息并退出程序。
如果`close(fd)`失败，
则输出错误信息并退出程序。
返回0。

通过`addr2line`工具处理程序输出后，其结果如下所示：

    SyS_read
    fs/read_write.c:562
    __fdget_pos
    fs/file.c:774
    __fget_light
    fs/file.c:746
    __fget_light
    fs/file.c:750
    __fget_light
    fs/file.c:760
    __fdget_pos
    fs/file.c:784
    SyS_read
    fs/read_write.c:562

如果一个程序需要从多个线程（独立地）收集覆盖率数据，
它需要在每个线程中单独打开`/sys/kernel/debug/kcov`文件。
该接口设计得足够精细以允许高效地fork测试进程。
也就是说，父进程打开`/sys/kernel/debug/kcov`文件，启用跟踪模式，
映射覆盖缓冲区，然后循环创建子进程。子进程只需要启用覆盖率收集
（当线程退出时会自动禁用）。

比较操作数收集
------------------

比较操作数收集与覆盖率收集类似：

```c
/* 同上包括和定义。 */

/* 每个记录中的64位字的数量。 */
#define KCOV_WORDS_PER_CMP 4

/*
 * 收集到的比较类型格式
 *
 * 第0位表示其中一个参数是否为编译时常量
 * 第1位和第2位包含参数大小的log2值，最大8字节
*/

#define KCOV_CMP_CONST          (1 << 0)
#define KCOV_CMP_SIZE(n)        ((n) << 1)
#define KCOV_CMP_MASK           KCOV_CMP_SIZE(3)

int main(int argc, char **argv)
{
    int fd;
    uint64_t *cover, type, arg1, arg2, is_const, size;
    unsigned long n, i;

    fd = open("/sys/kernel/debug/kcov", O_RDWR);
    如果 (fd == -1)
        输出错误信息("open")，退出程序；
    如果(`ioctl(fd, KCOV_INIT_TRACE, COVER_SIZE)`失败)
        输出错误信息("ioctl")，退出程序；
    /*
     * 注意缓冲区指针类型为uint64_t*，因为所有
     * 比较操作数都被提升为uint64_t
     */
    cover = (uint64_t *)映射内存(NULL, COVER_SIZE * sizeof(unsigned long),
                                     PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    如果((void*)cover == MAP_FAILED)
        输出错误信息("munmap")，退出程序；
    /* 注意KCOV_TRACE_CMP而不是KCOV_TRACE_PC。 */
    如果(`ioctl(fd, KCOV_ENABLE, KCOV_TRACE_CMP)`失败)
        输出错误信息("ioctl")，退出程序；
    __atomic_store_n(&cover[0], 0, __ATOMIC_RELAXED);
    read(-1, NULL, 0);
    /* 读取收集到的比较次数。 */
    n = __atomic_load_n(&cover[0], __ATOMIC_RELAXED);
    for (i = 0; i < n; i++) {
        uint64_t ip;

        type = cover[i * KCOV_WORDS_PER_CMP + 1];
        /* arg1 和 arg2 - 比较的操作数。 */
        arg1 = cover[i * KCOV_WORDS_PER_CMP + 2];
        arg2 = cover[i * KCOV_WORDS_PER_CMP + 3];
        /* ip - 调用者地址。 */
        ip = cover[i * KCOV_WORDS_PER_CMP + 4];
        /* 操作数的大小。 */
        size = 1 << ((type & KCOV_CMP_MASK) >> 1);
        /* is_const - 如果任一操作数是编译时常量，则为真。*/
        is_const = type & KCOV_CMP_CONST;
        printf("ip: 0x%lx 类型: 0x%lx, arg1: 0x%lx, arg2: 0x%lx, "
            "大小: %lu, %s\n",
            ip, type, arg1, arg2, size,
        is_const ? "常量" : "非常量");
    }
    如果(`ioctl(fd, KCOV_DISABLE, 0)`失败)
        输出错误信息("ioctl")，退出程序；
    /* 释放资源。 */
    如果(`munmap(cover, COVER_SIZE * sizeof(unsigned long))`失败)
        输出错误信息("munmap")，退出程序；
    如果(`close(fd)`失败)
        输出错误信息("close")，退出程序；
    返回0；
}

注意KCOV模式（收集代码覆盖率或比较操作数）是互斥的。

远程覆盖率收集
-------------------

除了可以收集来自用户空间进程发起的系统调用处理器的覆盖率数据外，
KCOV还可以收集内核在其他上下文中执行的部分的覆盖率——所谓的“远程”覆盖率。
使用KCOV来收集远程覆盖率需要：

1. 修改内核代码，在应该收集覆盖率的代码段前后加上`kcov_remote_start`和`kcov_remote_stop`。
使用 `KCOV_REMOTE_ENABLE` 而不是 `KCOV_ENABLE` 在收集覆盖率的用户空间进程中，
`kcov_remote_start` 和 `kcov_remote_stop` 注释以及 `KCOV_REMOTE_ENABLE` ioctl 均接受句柄，这些句柄标识特定的覆盖率收集部分。句柄的使用方式取决于匹配代码段执行的上下文。
KCOV 支持从以下上下文中收集远程覆盖率：

1. 全局内核后台任务。这些是在内核启动期间生成的有限数量的任务实例（例如，每个 USB HCD 将生成一个 USB `hub_event` 工作者）。
2. 本地内核后台任务。当用户空间进程与某些内核接口交互时会生成这些任务，并且通常在进程退出时被销毁（例如，vhost 工作者）。
3. 软中断

对于第 1 和第 3 类情况，必须选择一个唯一的全局句柄并传递给相应的 `kcov_remote_start` 调用。然后，用户空间进程必须将此句柄通过 `kcov_remote_arg` 结构中的 `handles` 数组字段传递给 `KCOV_REMOTE_ENABLE`。这将使所使用的 KCOV 设备与该句柄引用的代码段关联起来。可以一次性传递多个标识不同代码段的全局句柄。

对于第 2 类情况，用户空间进程必须通过 `kcov_remote_arg` 结构中的 `common_handle` 字段传递一个非零句柄。这个公共句柄会被保存到当前 `task_struct` 的 `kcov_handle` 字段中，并需要通过自定义内核代码修改传递给新生成的本地任务。这些任务应进一步在其 `kcov_remote_start` 和 `kcov_remote_stop` 注释中使用传递过来的句柄。

KCOV 对于全局和公共句柄都遵循预定义的格式。每个句柄是一个 `u64` 整数。目前只使用了最高位和最低的 4 个字节。第 4 到第 7 位是保留的，必须为零。
对于全局句柄，句柄的最高位表示该句柄所属子系统的 ID。例如，KCOV 使用 `1` 作为 USB 子系统的 ID。
全局句柄的最低 4 个字节表示该子系统内任务实例的 ID。例如，每个 `hub_event` 工作者使用 USB 总线编号作为任务实例的 ID。
对于通用句柄，预留值`0`被用作子系统ID，因为这类句柄不属于特定的子系统。通用句柄的较低4字节标识由传递了通用句柄给`KCOV_REMOTE_ENABLE`的用户空间进程所启动的所有本地任务的一个集合实例。实际上，如果仅从系统中的单一用户空间进程中收集覆盖数据，则可以为通用句柄实例ID使用任何值。但是，如果多个进程使用通用句柄，则必须为每个进程使用唯一的实例ID。一个选项是使用进程ID作为通用句柄的实例ID。
以下程序演示了如何使用KCOV来同时从进程启动的本地任务以及处理USB总线#1的全局任务收集覆盖数据：

```c
/* 与上述相同的包含文件和定义。 */

struct kcov_remote_arg {
	__u32		trace_mode;
	__u32		area_size;
	__u32		num_handles;
	__aligned_u64	common_handle;
	__aligned_u64	handles[0];
};

#define KCOV_INIT_TRACE			_IOR('c', 1, unsigned long)
#define KCOV_DISABLE			_IO('c', 101)
#define KCOV_REMOTE_ENABLE		_IOW('c', 102, struct kcov_remote_arg)

#define COVER_SIZE	(64 << 10)

#define KCOV_TRACE_PC	0

#define KCOV_SUBSYSTEM_COMMON	(0x00ull << 56)
#define KCOV_SUBSYSTEM_USB	(0x01ull << 56)

#define KCOV_SUBSYSTEM_MASK	(0xffull << 56)
#define KCOV_INSTANCE_MASK	(0xffffffffull)

static inline __u64 kcov_remote_handle(__u64 subsys, __u64 inst)
{
	if (subsys & ~KCOV_SUBSYSTEM_MASK || inst & ~KCOV_INSTANCE_MASK)
		return 0;
	return subsys | inst;
}

#define KCOV_COMMON_ID	0x42
#define KCOV_USB_BUS_NUM	1

int main(int argc, char **argv)
{
	int fd;
	unsigned long *cover, n, i;
	struct kcov_remote_arg *arg;

	fd = open("/sys/kernel/debug/kcov", O_RDWR);
	if (fd == -1)
		perror("open"), exit(1);
	if (ioctl(fd, KCOV_INIT_TRACE, COVER_SIZE))
		perror("ioctl"), exit(1);
	cover = (unsigned long*)mmap(NULL, COVER_SIZE * sizeof(unsigned long),
				     PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if ((void*)cover == MAP_FAILED)
		perror("mmap"), exit(1);

	/* 通过通用句柄及USB总线#1启用覆盖数据收集。 */
	arg = calloc(1, sizeof(*arg) + sizeof(uint64_t));
	if (!arg)
		perror("calloc"), exit(1);
	arg->trace_mode = KCOV_TRACE_PC;
	arg->area_size = COVER_SIZE;
	arg->num_handles = 1;
	arg->common_handle = kcov_remote_handle(KCOV_SUBSYSTEM_COMMON,
							KCOV_COMMON_ID);
	arg->handles[0] = kcov_remote_handle(KCOV_SUBSYSTEM_USB,
						KCOV_USB_BUS_NUM);
	if (ioctl(fd, KCOV_REMOTE_ENABLE, arg))
		perror("ioctl"), free(arg), exit(1);
	free(arg);

	/*
	 * 在这里，用户需要触发执行带有通用句柄注解的内核代码段，
	 * 或者触发USB总线#1上的一些活动。
	 */
	sleep(2);

	n = __atomic_load_n(&cover[0], __ATOMIC_RELAXED);
	for (i = 0; i < n; i++)
		printf("0x%lx\n", cover[i + 1]);
	if (ioctl(fd, KCOV_DISABLE, 0))
		perror("ioctl"), exit(1);
	if (munmap(cover, COVER_SIZE * sizeof(unsigned long)))
		perror("munmap"), exit(1);
	if (close(fd))
		perror("close"), exit(1);
	return 0;
}
```
```
