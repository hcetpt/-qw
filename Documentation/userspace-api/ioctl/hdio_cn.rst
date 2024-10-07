==============================
`HDIO_` ioctl 调用概要
==============================

- Edward A. Falk <efalk@google.com>

2004年11月

本文档尝试描述由 HD/IDE 层支持的 ioctl(2) 调用。这些调用大部分在 Linux 5.11 版本中实现在 drivers/ata/libata-scsi.c 中。ioctl 值列在 <linux/hdreg.h> 中。截至本文档撰写时，它们如下：

    向用户空间传递指针参数的 ioctl 调用：

	=======================	=======================================
	HDIO_GETGEO		获取设备几何信息
	HDIO_GET_32BIT		获取当前 io_32bit 设置
	HDIO_GET_IDENTITY	获取 IDE 识别信息
	HDIO_DRIVE_TASKFILE	执行原始任务文件
	HDIO_DRIVE_TASK		执行任务和特殊驱动命令
	HDIO_DRIVE_CMD		执行特殊驱动命令
	=======================	=======================================

    传递非指针值的 ioctl 调用：

	=======================	=======================================
	HDIO_SET_32BIT		更改 io_32bit 标志
	=======================	=======================================

以下信息是从阅读内核源代码得出的。随着时间推移可能会进行一些修正。

------------------------------------------------------------------------------

通用说明：
	除非另有说明，所有 ioctl 调用成功返回 0，并在出错时将 errno 设置为适当的值并返回 -1。
除非另有说明，所有 ioctl 调用在尝试将数据复制到或从用户地址空间失败时返回 -1 并将 errno 设置为 EFAULT。
除非另有说明，所有数据结构和常量都定义在 <linux/hdreg.h> 中。

------------------------------------------------------------------------------

HDIO_GETGEO
	获取设备几何信息

使用方法::

	  struct hd_geometry geom;

	  ioctl(fd, HDIO_GETGEO, &geom);

输入：
	无

输出：
	hd_geometry 结构体包含：

	    =========	==================================
	    heads	number of heads
	    sectors	number of sectors/track
	    cylinders	number of cylinders, mod 65536
	    start	starting sector of this partition
=========	==================================

错误返回：
	  - EINVAL

			如果设备不是磁盘驱动器或软盘驱动器，或者用户传递了一个空指针

备注：
	对于现代磁盘驱动器来说，此 ioctl 不是很有用，因为现代驱动器的几何信息本身就是一个礼貌性的虚构。现代驱动器纯粹通过扇区编号进行寻址（LBA 寻址），而驱动器的几何信息实际上是可以变化的。目前（截至 2004 年 11 月），几何值是“BIOS”值——即驱动器在 Linux 首次启动时的值。
此外，hd_geometry 结构体中的 cylinders 字段是一个无符号短整型，这意味着在大多数架构上，此 ioctl 在具有超过 65535 磁道的驱动器上不会返回有意义的值。
start 字段是无符号长整型，这意味着对于大于 219 GB 的磁盘，它将不包含有意义的值。

HDIO_GET_IDENTITY
	获取 IDE 识别信息

使用方法::

	  unsigned char identity[512];

	  ioctl(fd, HDIO_GET_IDENTITY, identity);

输入：
	无

输出：
	ATA 驱动器身份信息。详细描述请参见 ATA 规范中的 IDENTIFY DEVICE 和 IDENTIFY PACKET DEVICE 命令。
错误返回：
	  - EINVAL	在分区而不是整个磁盘设备上调用
	  - ENOMSG	IDENTIFY DEVICE 信息不可用

备注：
	返回的信息是在驱动器探测时获得的。其中一些信息是可变的，此 ioctl 不会对驱动器重新进行探测以更新信息。
此信息也可从 `/proc/ide/hdX/identify` 获取。

### HDIO_GET_32BIT
获取当前的 io_32bit 设置。

**用法：**

```c
long val;

ioctl(fd, HDIO_GET_32BIT, &val);
```

**输入：**
无

**输出：**
当前 io_32bit 设置的值

**注意事项：**
0=16位，1=32位，2、3 = 32位+同步

### HDIO_DRIVE_TASKFILE
执行原始任务文件。

**注意：**
如果您没有 ANSI ATA 规范的副本，您应该忽略这个 ioctl。
直接通过写入驱动器的“任务文件”寄存器来执行 ATA 磁盘命令。需要 ADMIN 和 RAWIO 访问权限。

**用法：**

```c
struct {
    ide_task_request_t req_task;
    u8 outbuf[OUTPUT_SIZE];
    u8 inbuf[INPUT_SIZE];
} task;
memset(&task.req_task, 0, sizeof(task.req_task));
task.req_task.out_size = sizeof(task.outbuf);
task.req_task.in_size = sizeof(task.inbuf);
..
ioctl(fd, HDIO_DRIVE_TASKFILE, &task);
..
```

**输入：**

（有关传递给 ioctl 的内存区域的详细信息，请参见下面。）

| 字段            | 描述                                                         |
|-----------------|--------------------------------------------------------------|
| io_ports[8]     | 要写入任务文件寄存器的值                                     |
| hob_ports[8]    | 扩展命令的高字节                                             |
| out_flags       | 表示哪些寄存器有效的标志                                     |
| in_flags        | 表示应返回哪些寄存器的标志                                   |
| data_phase      | 请参见下面说明                                               |
| req_cmd         | 要执行的命令类型                                             |
| out_size        | 输出缓冲区的大小                                             |
| outbuf          | 要传输到磁盘的数据缓冲区                                     |
| inbuf           | 要从磁盘接收的数据缓冲区（参见注释 [1]）                     |

**输出：**

| 字段            | 描述                                                         |
|-----------------|--------------------------------------------------------------|
| io_ports[]      | 返回的任务文件寄存器值                                        |
| hob_ports[]     | 扩展命令的高字节                                              |
| out_flags       | 表示哪些寄存器有效的标志（参见注释 [2]）                     |
| in_flags        | 表示应返回哪些寄存器的标志                                   |
| outbuf          | 要传输到磁盘的数据缓冲区（参见注释 [1]）                     |
| inbuf           | 从磁盘接收到的数据缓冲区                                      |

**错误返回：**
- `EACCES`   没有设置 CAP_SYS_ADMIN 或 CAP_SYS_RAWIO 特权
- `ENOMSG`   设备不是磁盘驱动器
- `ENOMEM`   无法为任务分配内存
- `EFAULT`   req_cmd == TASKFILE_IN_OUT（在 2.6.8 及以前版本未实现）
- `EPERM`    
  
        req_cmd == TASKFILE_MULTI_OUT 且驱动器多计数尚未设置
- `EIO`      驱动器未能执行命令
注释：

  [1] 请*仔细*阅读以下注意事项。此ioctl充满了陷阱。使用时应极其小心，因为任何错误都可能导致数据损坏或系统挂起。
  
  [2] 输入和输出缓冲区都会从用户复制并写回到用户，即使它们未被使用也是如此。

  [3] 如果out_flags中有任何一个位被设置而in_flags为零，则在完成时使用以下值作为in_flags.all，并将其写回in_flags：
  * 如果启用了驱动器的LBA48寻址：IDE_TASKFILE_STD_IN_FLAGS | (IDE_HOB_STD_IN_FLAGS << 8)
  * 如果是CHS/LBA28寻址：IDE_TASKFILE_STD_IN_FLAGS

  in_flags.all与每个使能位字段之间的关联取决于字节序；幸运的是，TASKFILE仅使用inflags.b.data位，并忽略所有其他位。最终结果是，在任何字节序的机器上，除了修改完成后的in_flags外，它没有其他效果。

  [4] SELECT的默认值是(0xa0|DEV_bit|LBA_bit)，除非是每端口四个驱动器的芯片组。对于每端口四个驱动器的芯片组，第一个对是(0xa0|DEV_bit|LBA_bit)，第二个对是(0x80|DEV_bit|LBA_bit)。

  [5] ioctl的参数是指向包含一个ide_task_request_t结构的内存区域的指针，后面跟着一个可选的数据缓冲区（用于传输到驱动器），再后面跟着一个可选的缓冲区（用于接收来自驱动器的数据）。

  命令通过ide_task_request_t结构传递给磁盘驱动器，该结构包含以下字段：

    ============	===============================================
    io_ports[8]		任务寄存器的值
    hob_ports[8]	高字节部分，用于扩展命令
    out_flags		指示io_ports[]和hob_ports[]数组中哪些项包含有效值的标志。类型为ide_reg_valid_t
    in_flags		指示io_ports[]和hob_ports[]数组中哪些项预期在返回时包含有效值的标志
    data_phase		见下文
    req_cmd		命令类型，见下文
    out_size		输出（用户->驱动器）缓冲区大小，字节
    in_size		输入（驱动器->用户）缓冲区大小，字节
    ============	===============================================

  当out_flags为零时，将加载以下寄存器。
============	===============================================
	    HOB_FEATURE		如果驱动器支持 LBA48
	    HOB_NSECTOR		如果驱动器支持 LBA48
	    HOB_SECTOR		如果驱动器支持 LBA48
	    HOB_LCYL		如果驱动器支持 LBA48
	    HOB_HCYL		如果驱动器支持 LBA48
	    FEATURE
	    NSECTOR
	    SECTOR
	    LCYL
	    HCYL
	    SELECT		首先，如果支持 LBA48，则与 0xE0 进行按位与操作；否则与 0xEF 进行按位与操作；然后，与 SELECT 的默认值进行或操作
============	===============================================

	  如果 out_flags 中的任何一位被设置，则加载以下寄存器
============	===============================================
	    HOB_DATA		如果 out_flags.b.data 被设置。在小端字节序机器上，HOB_DATA 将通过 DD8-DD15 传输；在大端字节序机器上，将通过 DD0-DD7 传输
DATA		如果 out_flags.b.data 被设置。在小端字节序机器上，DATA 将通过 DD0-DD7 传输；在大端字节序机器上，将通过 DD8-DD15 传输
HOB_NSECTOR		如果 out_flags.b.nsector_hob 被设置
	    HOB_SECTOR		如果 out_flags.b.sector_hob 被设置
	    HOB_LCYL		如果 out_flags.b.lcyl_hob 被设置
	    HOB_HCYL		如果 out_flags.b.hcyl_hob 被设置
	    FEATURE		如果 out_flags.b.feature 被设置
	    NSECTOR		如果 out_flags.b.nsector 被设置
	    SECTOR		如果 out_flags.b.sector 被设置
	    LCYL		如果 out_flags.b.lcyl 被设置
	    HCYL		如果 out_flags.b.hcyl 被设置
	    SELECT		与 SELECT 的默认值进行或操作，并且无论 out_flags.b.select 是否被设置都会加载
============	===============================================

	  在命令完成后，如果满足以下任一条件，则从驱动器读回任务文件寄存器到 {io|hob}_ports[]；否则，原始值将保持不变
1. 驱动器命令失败（EIO）
2. out_flags 中的一位或多于一位被设置
3. 请求的数据阶段为 TASKFILE_NO_DATA
============	===============================================
	    HOB_DATA		如果 in_flags.b.data 被设置。它将包含小端字节序机器上的 DD8-DD15 或大端字节序机器上的 DD0-DD7
### 数据
如果 `in_flags.b.data` 被设置，它将包含：
- 小端字节序机器上的 `DD0-DD7`
- 大端字节序机器上的 `DD8-DD15`

### HOB 特性
如果驱动器支持 LBA48，则包含以下字段：
- `HOB_FEATURE`
- `HOB_NSECTOR`
- `HOB_SECTOR`
- `HOB_LCYL`
- `HOB_HCYL`

### 字段
```
NSECTOR
SECTOR
LCYL
HCYL
```

### 数据阶段字段描述
数据阶段字段描述了要执行的数据传输。值可以是以下之一：
```
====================        ========================================
TASKFILE_IN
TASKFILE_MULTI_IN
TASKFILE_OUT
TASKFILE_MULTI_OUT
TASKFILE_IN_OUT
TASKFILE_IN_DMA
TASKFILE_IN_DMAQ		== IN_DMA (不支持队列)
TASKFILE_OUT_DMA
TASKFILE_OUT_DMAQ		== OUT_DMA (不支持队列)
TASKFILE_P_IN		未实现
TASKFILE_P_IN_DMA		未实现
TASKFILE_P_IN_DMAQ		未实现
TASKFILE_P_OUT		未实现
TASKFILE_P_OUT_DMA		未实现
TASKFILE_P_OUT_DMAQ		未实现
====================        ========================================
```

### 请求命令字段分类
请求命令字段分类了命令类型。可能是以下之一：
```
=======================    =======================================
IDE_DRIVE_TASK_NO_DATA
IDE_DRIVE_TASK_SET_XFER	未实现
IDE_DRIVE_TASK_IN
IDE_DRIVE_TASK_OUT		未实现
IDE_DRIVE_TASK_RAW_WRITE
=======================    =======================================
```

### 注意事项
[6] 不要访问 `{in|out}_flags->all` 除非重置所有位。始终访问单个位字段。`->all` 的值会根据字节序翻转。出于同样的原因，请不要使用在 `hdreg.h` 中定义的 `IDE_{TASKFILE|HOB}_STD_{OUT|IN}_FLAGS` 常量。

### HDIO_DRIVE_CMD
执行一个特殊的驱动器命令

注意：如果你没有 ANSI ATA 规范的副本，你可能应该忽略这个 ioctl。
用法示例：
```c
u8 args[4 + XFER_SIZE];

...
ioctl(fd, HDIO_DRIVE_CMD, args);
```

### 输入
对于除 WIN_SMART 之外的命令：
```
=======     =======
args[0]	COMMAND
args[1]	NSECTOR
args[2]	FEATURE
args[3]	NSECTOR
=======     =======
```

对于 WIN_SMART：
```
=======     =======
args[0]	COMMAND
args[1]	SECTOR
args[2]	FEATURE
args[3]	NSECTOR
=======     =======
```

### 输出
`args[]` 缓冲区被填充值，随后是磁盘返回的任何数据。
```
========	====================================================
args[0]	status
args[1]	error
args[2]	NSECTOR
args[3]	undefined
args[4+]	NSECTOR * 512 字节的数据由命令返回
========	====================================================
```

### 错误返回
- `EACCES` 访问被拒绝：需要 `CAP_SYS_RAWIO` 权限
- `ENOMEM` 无法分配任务内存
- `EIO` 驱动器报告错误

### 注意事项
[1] 对于除 WIN_SMART 之外的命令，`args[1]` 应等于 `args[3]`。`SECTOR`、`LCYL` 和 `HCYL` 是未定义的。对于 WIN_SMART，分别将 `0x4f` 和 `0xc2` 加载到 `LCYL` 和 `HCYL` 中。在这两种情况下，`SELECT` 将包含驱动器的默认值。请参考 `HDIO_DRIVE_TASKFILE` 注释以获取 `SELECT` 的默认值。

[2] 如果 `NSECTOR` 的值大于零，并且驱动器在中断命令时设置了 `DRQ`，则 `NSECTOR * 512` 字节的数据从设备读入 `NSECTOR` 后面的区域。例如，在上面的例子中，该区域将是 `args[4..4+XFER_SIZE]`。无论 `HDIO_SET_32BIT` 设置如何，都使用 16 位 PIO。

[3] 如果 `COMMAND == WIN_SETFEATURES && FEATURE == SETFEATURES_XFER && NSECTOR >= XFER_SW_DMA_0` 并且驱动器支持任何 DMA 模式，IDE 驱动程序将尝试相应地调整驱动器的传输模式。
### HDIO_DRIVE_TASK
执行任务和特殊驱动器命令。

**注意：**
如果你没有 ANSI ATA 规格的手册，你可能应该忽略这个 ioctl。

**用法：**

```c
u8 args[7];

// ...

ioctl(fd, HDIO_DRIVE_TASK, args);
```

**输入：**
- 任务文件寄存器值：
  
  | 寄存器 | 对应值   |
  |--------|----------|
  | args[0]| COMMAND  |
  | args[1]| FEATURE  |
  | args[2]| NSECTOR  |
  | args[3]| SECTOR   |
  | args[4]| LCYL     |
  | args[5]| HCYL     |
  | args[6]| SELECT   |

**输出：**
- 任务文件寄存器值：

  | 寄存器 | 对应值   |
  |--------|----------|
  | args[0]| status   |
  | args[1]| error    |
  | args[2]| NSECTOR  |
  | args[3]| SECTOR   |
  | args[4]| LCYL     |
  | args[5]| HCYL     |
  | args[6]| SELECT   |

**错误返回：**
- EACCES：访问被拒绝（需要 CAP_SYS_RAWIO 权限）
- ENOMEM：无法分配内存用于任务
- ENOMSG：设备不是磁盘驱动器
- EIO：驱动器未能完成命令

**注释：**
1. SELECT 寄存器的 DEV 位（0x10）被忽略，并使用适用于该驱动器的值。所有其他位保持不变。

### HDIO_SET_32BIT
更改 io_32bit 标志。

**用法：**

```c
int val;

ioctl(fd, HDIO_SET_32BIT, val);
```

**输入：**
- 新的 io_32bit 标志值

**输出：**
- 无

**错误返回：**
- EINVAL：在分区上而不是整个磁盘设备上调用
- EACCES：访问被拒绝（需要 CAP_SYS_ADMIN 权限）
- EINVAL：值超出范围 [0, 3]
- EBUSY：控制器忙
