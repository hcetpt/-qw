TCM 用户空间设计
====================

.. 目录:

   1) 设计
     a) 背景
     b) 好处
     c) 设计约束
     d) 实现概述
        i. 邮箱
        ii. 命令环
        iii. 数据区
     e) 设备发现
     f) 设备事件
     g) 其他应急措施
   2) 编写用户传递处理器
     a) 发现和配置 TCMU UIO 设备
     b) 等待设备上的事件
     c) 管理命令环
   3) 最后说明

设计
======

TCM 是 LIO 的另一个名称，LIO 是一个内核中的 iSCSI 目标（服务器）。现有的 TCM 目标在内核中运行。TCMU（TCM 在用户空间）允许编写用户空间程序作为 iSCSI 目标。本文档描述了该设计。现有内核提供了用于不同 SCSI 传输协议的模块。TCM 还模块化了数据存储。现有模块包括文件、块设备、RAM 或使用其他 SCSI 设备作为存储。这些被称为“后端存储”或“存储引擎”。这些内置模块完全由内核代码实现。

背景
----------

除了模块化用于承载 SCSI 命令的传输协议（“结构”），Linux 内核目标 LIO 还模块化了实际的数据存储。这些称为“后端存储”或“存储引擎”。目标自带了一些后端存储，可以使用文件、块设备、RAM 或其他 SCSI 设备作为导出 SCSI LUN 所需的本地存储。与 LIO 的其余部分一样，这些也是完全由内核代码实现的。

这些后端存储涵盖了最常见的用例，但并不是全部。一种新的用例是其他非内核目标解决方案（如 tgt）能够支持的，即使用 Gluster 的 GLFS 或 Ceph 的 RBD 作为后端存储。目标充当翻译器，允许启动器使用这些非传统的网络存储系统存储数据，同时仍然只使用标准协议。

如果目标是一个用户空间进程，支持这些后端存储就很容易。例如，tgt 只需要为每个后端存储添加一个小适配器模块，因为这些模块只需使用 RBD 和 GLFS 的可用用户空间库即可。

在 LIO 中添加对这些后端存储的支持要困难得多，因为 LIO 完全是内核代码。与其进行大量的工作将 GLFS 或 RBD 的 API 和协议移植到内核，另一种方法是为 LIO 创建一个用户空间传递后端存储，“TCMU”。

好处
--------

除了相对容易地支持 RBD 和 GLFS 外，TCMU 还将使新后端存储的开发变得更容易。TCMU 结合 LIO 的回环结构，类似于 FUSE（用户空间文件系统），但位于 SCSI 层而不是文件系统层。可以说是一个 SUSE 版本。

缺点是有更多独立的组件需要配置，并且可能会出现故障。这是不可避免的，但如果我们在尽量保持简单的情况下谨慎行事，希望这不会致命。
设计约束
------------------

- 良好的性能：高吞吐量、低延迟
- 如果用户空间出现以下情况，应妥善处理：

   1) 从未连接
   2) 挂起
   3) 死亡
   4) 行为不当

- 允许用户和内核实现未来的灵活性
- 合理地节省内存
- 简单配置与运行
- 容易编写用户空间后端

实现概述
-----------------------

TCMU接口的核心是一个共享的内存区域，该区域由内核和用户空间共享。在这个区域内包括：控制区（邮箱）；一个无锁的生产者/消费者环形缓冲区，用于传递命令并返回状态；以及输入/输出数据缓冲区。TCMU 使用现有的UIO子系统。UIO允许在用户空间中开发设备驱动程序，这在概念上与TCMU使用场景非常接近，只不过不是针对物理设备，而是TCMU实现了一个专为SCSI命令设计的内存映射布局。使用UIO还使TCMU受益于处理设备自检（例如，用户空间确定共享区域的大小的方法）和双向信号机制。
内存区域中没有嵌入指针。所有内容都表示为从区域起始地址的偏移量。这样即使用户进程死亡并以不同的虚拟地址重新映射该区域，环形缓冲区仍然可以正常工作。
请参见target_core_user.h中的结构定义。
邮箱
-----------

邮箱始终位于共享内存区域的开始处，并包含版本信息、关于命令环的起始偏移量和大小的详细信息，以及供内核和用户空间（分别）用于放置命令到环上并指示命令完成的头部和尾部指针。
版本 - 1（如果不同，则用户空间应终止）

标志：
    - TCMU_MAILBOX_FLAG_CAP_OOOC：
	表示支持乱序完成
详见“命令环”部分
cmdr_off
	命令环相对于内存区域开始位置的偏移量，以考虑邮箱的大小
cmdr_size
	命令环的大小。这不需要是2的幂
cmd_head
	由内核修改，以指示命令已放置到环上
命令环 (Command Ring)
------------------

命令通过内核增加 `mailbox.cmd_head` 的值（增加的值为命令的大小，模 `cmdr_size`），然后通过 `uio_event_notify()` 通知用户空间。当命令处理完成后，用户空间以相同的方式更新 `mailbox.cmd_tail` 并通过一个 4 字节的写操作 (`write()`) 通知内核。当 `cmd_head` 等于 `cmd_tail` 时，命令环为空 —— 没有命令正在等待用户空间处理。

TCMU 命令是 8 字节对齐的。它们以一个公共头开始，该头包含一个 32 位值 "len_op"，存储长度以及在最低未使用位中的操作码。它还包含由内核设置的 `cmd_id` 和标志字段 (`kflags`) 以及用户空间设置的标志字段 (`uflags`)。

目前仅定义了两个操作码：`TCMU_OP_CMD` 和 `TCMU_OP_PAD`。

当操作码为 `CMD` 时，命令环中的条目是一个 `tcmu_cmd_entry` 结构体。用户空间通过 `tcmu_cmd_entry.req.cdb_off` 找到 SCSI CDB（命令数据块）。这是一个从整个共享内存区域起始位置的偏移量，而不是从条目开始的偏移量。输入/输出缓冲区可通过 `req.iov[]` 数组访问。`iov_cnt` 包含描述输入或输出缓冲区所需的 `iov[]` 入口数。对于双向命令，`iov_cnt` 指定多少个 `iovec` 条目覆盖输出区域，而 `iov_bidi_cnt` 指定紧随其后的 `iov[]` 中有多少 `iovec` 条目覆盖输入区域。和其它字段一样，`iov.iov_base` 是从区域起始位置的偏移量。

完成一个命令时，用户空间设置 `rsp.scsi_status`，必要时设置 `rsp.sense_buffer`。用户空间然后将 `mailbox.cmd_tail` 增加 `entry.hdr.length` （模 `cmdr_size`）并通过 UIO 方法（即向文件描述符写入 4 字节）通知内核。

如果设置了 `mailbox->flags` 的 `TCMU_MAILBOX_FLAG_CAP_OOOC` 标志，则内核能够处理乱序完成。在这种情况下，用户空间可以以不同于原始顺序的方式处理命令。由于内核仍然会按命令环中出现的顺序处理命令，因此用户空间需要在完成命令时更新 `cmd->id`（即“窃取”原始命令的条目）。

当操作码为 `PAD` 时，用户空间只需像上面那样更新 `cmd_tail` 即可——这是一个空操作。（内核插入 `PAD` 条目以确保每个 `CMD` 条目在命令环中是连续的。）

未来可能会添加更多操作码。如果用户空间遇到无法处理的操作码，必须在 `hdr.uflags` 中设置未知操作码标志（第 0 位），更新 `cmd_tail` 并继续处理其他命令（如果有）。

数据区域
-------------

这是命令环之后的共享内存空间。该区域的组织方式并未在 TCMU 接口中定义，用户空间应只访问由待处理的 `iovs` 引用的部分。

设备发现
-----------------

除 TCMU 外，其他设备也可能使用 UIO。无关的用户进程可能也在处理不同的 TCMU 设备集。TCMU 用户空间进程必须通过扫描 `sysfs` 的 `class/uio/uio*/name` 来查找其设备。对于 TCMU 设备，这些名称将采用以下格式：

```
tcm-user/<hba_num>/<device_name>/<subtype>/<path>
```

其中，“tcm-user” 对所有 TCMU 支持的 UIO 设备都是通用的。`<hba_num>` 和 `<device_name>` 允许用户空间在内核目标的 `configfs` 树中找到设备路径。假设通常的挂载点，该位置位于：

```
/sys/kernel/config/target/core/user_<hba_num>/<device_name>
```

该位置包含用户空间需要了解的属性，例如 “hw_block_size”，以便正确运行。
<subtype> 将是一个用户空间进程唯一的字符串，用于标识 TCMU 设备并期望由某个特定的处理器支持，而 <path> 是一个附加的处理器特定字符串，供用户进程配置设备时使用（如果需要）。由于 LIO 的限制，名称中不能包含 ':'。

对于所有发现的设备，用户处理器会打开 `/dev/uioX` 并调用 `mmap()`：

```c
mmap(NULL, size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0)
```

其中 `size` 必须等于从 `/sys/class/uio/uioX/maps/map0/size` 读取的值。
### 设备事件

如果添加或移除了一个新设备，则会通过 netlink 广播通知，使用通用 netlink 家族名称 "TCM-USER" 和名为 "config" 的多播组。这将包括前面章节描述的 UIO 名称以及 UIO 次设备号。这应该允许用户空间识别 UIO 设备和 LIO 设备，以便在确定设备受支持（基于子类型）后采取适当的行动。
### 其他情况

- 用户空间处理器从未连接：
  - TCMU 将发布命令，并在超时后（30 秒）终止这些命令。
- 用户空间处理器被杀死：
  - 仍然可以重新启动并重新连接到 TCMU 设备。命令环保持不变。然而，在超时后，内核会终止待处理的任务。
- 用户空间处理器挂起：
  - 内核将在超时后终止待处理的任务。
- 用户空间处理器恶意行为：
  - 该进程可以轻易破坏其控制的设备处理，但不应能够访问共享内存区域之外的内核内存。
### 编写用户直通处理器（附示例代码）

处理 TCMU 设备的用户进程必须支持以下功能：

a) 发现和配置 TCMU uio 设备  
b) 等待设备上的事件  
c) 管理命令环：解析操作和命令，执行所需的工作，设置响应字段（如 scsi_status 和可能的 sense_buffer），更新 cmd_tail，并通知内核工作已完成

首先，考虑编写一个 tcmu-runner 插件。tcmu-runner 实现了所有这些功能，并为插件作者提供了一个更高级的 API。
TCMU 设计使得多个不相关的进程可以独立管理 TCMU 设备。所有处理器应确保仅打开其已知子类型的设备。
a) 发现和配置 TCMU UIO 设备：

```c
/* 为简洁起见省略错误检查 */

int fd, dev_fd;
char buf[256];
unsigned long long map_len;
void *map;

fd = open("/sys/class/uio/uio0/name", O_RDONLY);
ret = read(fd, buf, sizeof(buf));
close(fd);
buf[ret-1] = '\0'; /* 空字符终止并去掉 \n */

/* 我们只想要名字符合预期格式的 uio 设备 */
if (strncmp(buf, "tcm-user", 8))
    exit(-1);

/* 这里还需要进一步检查子类型 */

fd = open("/sys/class/uio/%s/maps/map0/size", O_RDONLY);
ret = read(fd, buf, sizeof(buf));
close(fd);
str_buf[ret-1] = '\0'; /* 空字符终止并去掉 \n */

map_len = strtoull(buf, NULL, 0);

dev_fd = open("/dev/uio0", O_RDWR);
map = mmap(NULL, map_len, PROT_READ|PROT_WRITE, MAP_SHARED, dev_fd, 0);

b) 等待设备上的事件

```c
while (1) {
    char buf[4];

    int ret = read(dev_fd, buf, 4); /* 将阻塞 */

    handle_device_events(dev_fd, map);
}
```

c) 管理命令环：

```c
#include <linux/target_core_user.h>

int handle_device_events(int fd, void *map)
{
    struct tcmu_mailbox *mb = map;
    struct tcmu_cmd_entry *ent = (void *) mb + mb->cmdr_off + mb->cmd_tail;
    int did_some_work = 0;

    /* 处理来自命令环的事件直到我们赶上 cmd_head */
    while (ent != (void *)mb + mb->cmdr_off + mb->cmd_head) {

        if (tcmu_hdr_get_op(ent->hdr.len_op) == TCMU_OP_CMD) {
            uint8_t *cdb = (void *)mb + ent->req.cdb_off;
            bool success = true;

            /* 处理命令 */
            printf("SCSI opcode: 0x%x\n", cdb[0]);

            /* 设置响应字段 */
            if (success)
                ent->rsp.scsi_status = SCSI_NO_SENSE;
            else {
                /* 也在此填充 rsp->sense_buffer */
                ent->rsp.scsi_status = SCSI_CHECK_CONDITION;
            }
        }
        else if (tcmu_hdr_get_op(ent->hdr.len_op) != TCMU_OP_PAD) {
            /* 告诉内核我们没有处理未知的操作码 */
            ent->hdr.uflags |= TCMU_UFLAG_UNKNOWN_OP;
        }
        else {
            /* 对于 PAD 条目除了更新 cmd_tail 以外什么都不做 */
        }

        /* 更新 cmd_tail */
        mb->cmd_tail = (mb->cmd_tail + tcmu_hdr_get_len(&ent->hdr)) % mb->cmdr_size;
        ent = (void *) mb + mb->cmdr_off + mb->cmd_tail;
        did_some_work = 1;
    }

    /* 通知内核工作已完成 */
    if (did_some_work) {
        uint32_t buf = 0;

        write(fd, &buf, 4);
    }

    return 0;
}
```

### 最后一点说明

请小心返回由 SCSI 规范定义的状态码。这些与 scsi/scsi.h 中定义的一些值不同。例如，CHECK CONDITION 的状态码是 2 而不是 1。
