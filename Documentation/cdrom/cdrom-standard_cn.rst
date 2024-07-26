=======================
Linux CD-ROM 标准
=======================

:作者: David van Leeuwen <david@ElseWare.cistron.nl>
:日期: 1999年3月12日
:更新者: Erik Andersen (andersee@debian.org)
:更新者: Jens Axboe (axboe@image.dk)

简介
============

Linux 可能是支持最广泛硬件设备的类Unix操作系统。这背后的原因可能是：

- 对于 Linux 现在所支持的众多平台（如 i386-PC、Sparc Suns 等）上可用的大量硬件设备。
- 操作系统的开放设计，任何人都可以为 Linux 编写驱动程序。
- 大量可作为编写驱动程序示例的源代码存在。

Linux 的开放性以及各种各样的可用硬件使得 Linux 能够支持许多不同的硬件设备。不幸的是，正是这种开放性也让每个设备驱动程序的行为从一个设备到另一个设备大相径庭。这种行为差异对于 CD-ROM 设备尤其显著；特定驱动器对“标准” *ioctl()* 调用的响应方式在不同驱动程序之间有很大的差异。为了避免使他们的驱动程序完全不一致，Linux CD-ROM 驱动程序的编写者通常通过理解、复制然后修改现有的驱动程序来创建新的驱动程序。遗憾的是，这种做法并没有保持所有 Linux CD-ROM 驱动程序的一致性。

本文档描述了一项旨在为所有不同的 Linux CD-ROM 设备驱动程序建立统一行为的努力。本文档还定义了各种 *ioctl()* 调用以及低级 CD-ROM 设备驱动程序应该如何实现它们。目前（截至 Linux 2.1.\ *x* 开发内核），包括 IDE/ATAPI 和 SCSI 在内的多个低级 CD-ROM 设备驱动程序现在都使用这种统一接口。

当 CD-ROM 被开发时，CD-ROM 驱动器与计算机之间的接口并未在标准中规定。因此，开发出了许多不同的 CD-ROM 接口。其中一些有自己的专有设计（索尼、三美、松下、飞利浦），其他制造商采用了现有的电气接口并改变了功能（创新实验室/声霸卡、TEAC、Funai）或仅仅将他们的驱动器适配到一个或多个已有的电气接口（Aztech、三洋、Funai、Vertos、Longshine、Optics Storage 以及大多数的“无名”制造商）。在新驱动器真正带来了自己的接口或使用了自己的命令集和流控制方案的情况下，要么需要编写单独的驱动程序，要么需要增强现有的驱动程序。历史为我们提供了许多这些不同接口的 CD-ROM 支持。如今，几乎所有的新 CD-ROM 驱动器都是 IDE/ATAPI 或 SCSI，并且制造商创建新接口的可能性非常小。即使是为旧的专有接口找到驱动器也变得越来越困难。

当我（在 1.3.70 年代）查看现有软件接口时——这个接口通过 `cdrom.h` 表达——它看起来是一组相当杂乱的命令和数据格式[#f1]_。似乎软件接口中的许多特性是为了适应特定驱动器的能力而以一种即兴的方式添加的。更重要的是，大多数不同驱动程序中的“标准”命令的行为似乎都不同：例如，有些驱动程序会在 *open()* 调用发生时托盘打开的情况下关闭托盘，而有些则不会。一些驱动程序在打开设备时锁定门，以防止文件系统不一致，但另一些则不这样做，以便允许软件弹出。毫无疑问，不同驱动器的能力各不相同，但是即使两个驱动器具有相同的能力，它们的驱动程序行为通常也是不同的。

.. [#f1]
   我记不清当时查看的是哪个内核版本，大概是在 1.2.13 和 1.3.34 ——这是我间接参与的最新内核版本。

我决定开始讨论如何让所有 Linux CD-ROM 驱动程序的行为更加统一。我首先联系了许多在 Linux 内核中发现的 CD-ROM 驱动程序的开发者。他们的反馈鼓励我编写了一个统一的 CD-ROM 驱动程序，本文档旨在对此进行描述。统一 CD-ROM 驱动程序的实现位于文件 `cdrom.c` 中。该驱动程序旨在作为一个额外的软件层，位于每个 CD-ROM 驱动器的低级设备驱动程序之上。
通过添加这一额外层，可以使得所有不同的CD-ROM设备的行为**完全**相同（在底层硬件允许的范围内）。
统一CD-ROM驱动程序的目标**不是**要疏远那些尚未采取措施支持这项工作的驱动开发者。统一CD-ROM驱动程序的目标仅仅是为那些为CD-ROM驱动编写应用程序的人提供**一个**具有统一行为的Linux CD-ROM接口，适用于所有的CD-ROM设备。此外，这也为低级别的设备驱动代码与Linux内核之间提供了统一的接口。确保与`cdrom.h`中定义的数据结构和编程接口100%兼容。本指南编写的目的就是为了帮助CD-ROM驱动开发者适应使用`cdrom.c`中定义的统一CD-ROM驱动代码。
就我个人而言，我认为最重要的硬件接口是IDE/ATAPI驱动器和当然的SCSI驱动器，但随着硬件价格的持续下降，人们可能拥有多个CD-ROM驱动器，可能是不同类型混合的。重要的是这些驱动器的行为方式需要一致。1994年12月，最便宜的CD-ROM驱动器之一是Philips cm206，这是一个专有的双速驱动器。在我忙着为其编写Linux驱动程序的那几个月里，专有驱动器变得过时，而IDE/ATAPI驱动器成为了标准。在本文档最后一次更新的时候（1997年11月），甚至很难找到低于16倍速的CD-ROM驱动器，而24倍速的驱动器已经很常见了。

### 通过另一软件层进行标准化

当本文档构思时，所有驱动程序都直接通过它们自己的例程实现了CD-ROM的*ioctl()*调用。这导致了不同驱动程序可能会忘记做一些重要的事情，比如检查用户是否给驱动程序提供了有效数据的风险。更重要的是，这导致了行为的分歧，这一点已经在前面讨论过。
为此，创建了统一CD-ROM驱动程序来强制执行一致的CD-ROM驱动行为，并为各种低级别的CD-ROM设备驱动程序提供一组共同的服务。统一CD-ROM驱动程序现在提供了一个额外的软件层，将*ioctl()*和*open()*的实现与实际的硬件实现分离。需要注意的是，这项努力所做的更改很少会影响到用户的应用程序。最大的改变是将各种低级别CD-ROM驱动程序头文件的内容移到内核的cdrom目录下。这样做的目的是为了确保用户仅看到一个CDROM接口，即`cdrom.h`中定义的接口。
CD-ROM驱动器足够特殊（即，与其他块设备如软盘或硬盘驱动器不同），可以定义一套**通用的CD-ROM设备操作**，*<cdrom-device>_dops*。
这些操作不同于经典的块设备文件操作，*<block-device>_fops*。
统一CD-ROM驱动程序接口层的例程实现在文件`cdrom.c`中。在这个文件中，统一CD-ROM驱动程序作为块设备与内核交互，通过注册以下一般的*struct file_operations*：

```c
struct file_operations cdrom_fops = {
    NULL,                      /* lseek */
    block_read,                /* read--general block-dev read */
    block_write,               /* write--general block-dev write */
    NULL,                      /* readdir */
    NULL,                      /* select */
    cdrom_ioctl,               /* ioctl */
    NULL,                      /* mmap */
    cdrom_open,                /* open */
    cdrom_release,             /* release */
    NULL,                      /* fsync */
    NULL,                      /* fasync */
    NULL                       /* revalidate */
};
```

每个活动的CD-ROM设备都共享这个*struct*。上述声明的例程都在`cdrom.c`中实现，因为这个文件是定义和标准化所有CD-ROM设备行为的地方。对各种类型的CD-ROM硬件的实际接口仍然由各种低级别的CD-ROM设备驱动程序完成。这些例程仅仅实现了一些**功能**，这些功能对于所有CD-ROM（实际上，对于所有可移动媒体设备）都是通用的。
低级别的CD-ROM设备驱动程序的注册现在是通过`cdrom.c`中的通用例程完成的，而不是再通过虚拟文件系统（VFS）。在`cdrom.c`中实现的接口是通过两个通用结构完成的，这些结构包含有关驱动程序的功能信息以及该驱动程序所操作的具体驱动器的信息。这些结构是：

- cdrom_device_ops
  这个结构包含有关CD-ROM设备的低级驱动程序的信息。此结构概念上与设备的主要编号相关联（尽管某些驱动程序可能有不同的主要编号，例如IDE驱动程序就是这种情况）。
- cdrom_device_info
  此结构包含有关特定CD-ROM驱动器的信息，例如其设备名称、速度等。此结构概念上与设备的次要编号相关联。
通过调用以下函数来使用统一CD-ROM驱动程序注册特定的CD-ROM驱动器：

```c
register_cdrom(struct cdrom_device_info * <device>_info)
```

设备信息结构`*<device>_info`包含了内核与低级CD-ROM设备驱动程序交互所需的所有信息。在这个结构中最重要的条目之一是指向低级驱动程序的`cdrom_device_ops`结构的指针。

`cdrom_device_ops`结构包含了一系列指向在低级设备驱动程序中实现的功能的指针。当`cdrom.c`访问CD-ROM设备时，它是通过这个结构中的功能来进行的。由于无法预知未来CD-ROM驱动器的所有能力，因此预计随着新技术的发展，这个列表可能需要不时扩展。例如，CD-R和CD-R/W驱动器开始变得流行，并且很快将需要为它们添加支持。目前，当前的`struct`定义如下：

```c
struct cdrom_device_ops {
    int (*open)(struct cdrom_device_info *, int)
    void (*release)(struct cdrom_device_info *);
    int (*drive_status)(struct cdrom_device_info *, int);
    unsigned int (*check_events)(struct cdrom_device_info *,
                                 unsigned int, int);
    int (*media_changed)(struct cdrom_device_info *, int);
    int (*tray_move)(struct cdrom_device_info *, int);
    int (*lock_door)(struct cdrom_device_info *, int);
    int (*select_speed)(struct cdrom_device_info *, unsigned long);
    int (*get_last_session)(struct cdrom_device_info *,
                            struct cdrom_multisession *);
    int (*get_mcn)(struct cdrom_device_info *, struct cdrom_mcn *);
    int (*reset)(struct cdrom_device_info *);
    int (*audio_ioctl)(struct cdrom_device_info *,
                       unsigned int, void *);
    const int capability;           /* capability flags */
    int (*generic_packet)(struct cdrom_device_info *,
                          struct packet_command *);
};
```

当低级设备驱动程序实现了这些功能之一时，应该在这个`struct`中添加一个函数指针。如果某个特定的功能没有实现，则该`struct`应该包含一个NULL值。`capability`标志指定了在注册CD-ROM驱动器到统一CD-ROM驱动程序时CD-ROM硬件和/或低级CD-ROM驱动程序的能力。

请注意，大多数函数比它们的`blkdev_fops`对应函数具有更少的参数。这是因为结构`inode`和`file`中的大部分信息很少被使用。对于大多数驱动程序来说，主要参数是`struct cdrom_device_info`，从中可以提取主次号。（大多数低级CD-ROM驱动程序甚至不会查看主次号，因为它们中的许多只支持一个设备。）这将通过`cdrom_device_info`中的`dev`字段获得。

与`cdrom.c`注册的驱动器特有的、类似次设备的信息当前包含以下字段：

```c
struct cdrom_device_info {
    const struct cdrom_device_ops * ops;   /* 本主设备的操作 */
    struct list_head list;                 /* 所有设备_info的链表 */
    struct gendisk * disk;                 /* 匹配块层磁盘 */
    void *  handle;                        /* 驱动程序相关的数据 */

    int mask;                              /* 能力掩码：禁用它们 */
    int speed;                             /* 读取数据的最大速度 */
    int capacity;                          /* 自动换片机中的光盘数量 */

    unsigned int options:30;               /* 选项标志 */
    unsigned mc_flags:2;                   /* 媒体更改缓冲标志 */
    unsigned int vfs_events;               /* 用于vfs路径的缓存事件 */
    unsigned int ioctl_events;             /* 用于ioctl路径的缓存事件 */
    int use_count;                         /* 设备打开次数 */
    char name[20];                         /* 设备类型名称 */

    __u8 sanyo_slot : 2;                   /* Sanyo 3-CD换片器支持 */
    __u8 keeplocked : 1;                   /* CDROM_LOCKDOOR状态 */
    __u8 reserved : 5;                     /* 尚未使用 */
    int cdda_method;                       /* 参见CDDA_*标志 */
    __u8 last_sense;                       /* 保存上次感觉键 */
    __u8 media_written;                    /* 脏标记，DVD+RW账本维护 */
    unsigned short mmc3_profile;           /* 当前MMC3配置文件 */
    int for_data;                          /* 未知：待定 */
    int (*exit)(struct cdrom_device_info *); /* 未知：待定 */
    int mrw_mode_page;                     /* 使用的MRW模式页 */
};
```

使用这个`struct`，构建了一个已注册次设备的链表，使用`list`字段。设备号、设备操作结构以及驱动器特性的说明存储在这个结构中。

`mask`标志可用于屏蔽`ops->capability`中列出的一些能力，如果特定驱动器不支持驱动程序的一个特性。`speed`值指定了驱动器的最大头速，以正常音频速度（176kB/秒原始数据或150kB/秒文件系统数据）为单位进行测量。参数被声明为`const`，因为它们描述了驱动器的属性，在注册后不会改变。

一些寄存器包含CD-ROM驱动器本地的变量。`options`标志用于指定通用CD-ROM例程应如何行为。这些各种标志寄存器应该提供足够的灵活性来适应不同用户的需求（而不是像旧方案那样，按照低级设备驱动程序作者的“任意”愿望）。`mc_flags`寄存器用于将`media_changed()`的信息缓冲到两个独立队列中。可以通过`handle`访问特定于次设备的数据，它可以指向特定于低级驱动程序的数据结构。

`use_count`、`next`、`options`和`mc_flags`字段无需初始化。

`cdrom.c`形成的中间软件层将执行一些额外的簿记工作。设备的使用计数（打开设备的进程数量）记录在`use_count`中。`cdrom_ioctl()`函数将验证适当的用户内存区域用于读写，并且如果传输CD上的位置，它将以标准化格式请求低级驱动程序，并在用户软件和低级驱动程序之间转换所有格式。这减轻了许多驱动程序的内存检查和格式检查及转换负担。此外，必要的结构将在程序堆栈上声明。

函数的实现应按照以下各节中定义的方式。必须实现两个函数，即`open()`和`release()`。其他函数可以省略，其相应的功能标志将在注册时清除。

通常，函数成功时返回零，错误时返回负值。函数调用应在命令完成后返回，但等待设备时不应占用处理器时间。
```c
int open(struct cdrom_device_info *cdi, int purpose)
/*
* 函数 *open()* 应尝试根据特定的 *purpose* 打开设备，该 *purpose* 可以是：
*
* - 为读取数据打开，如 `mount()`（2）命令或用户命令 `dd` 或 `cat` 所做。
* - 为 *ioctl* 命令打开，如音频 CD 播放程序所做。
*
* 注意任何策略性的代码（例如在 *open()* 时关闭托盘等）都由 `cdrom.c` 中的调用例程处理，
* 因此低级例程只应关注适当的初始化工作，如启动光盘等。
*/

void release(struct cdrom_device_info *cdi)
/*
* 应采取针对设备的具体动作，如降低设备转速。
* 然而，如弹出托盘或解锁门等策略性动作应留给通用例程 *cdrom_release()* 来处理。
* 这是唯一返回类型为 *void* 的函数。
* .. _cdrom_drive_status:
*/

int drive_status(struct cdrom_device_info *cdi, int slot_nr)
/*
* 如果实现了 *drive_status* 函数，则应提供关于驱动器状态的信息（不是光盘的状态，光盘可能在驱动器中也可能不在）。
* 如果驱动器不是一个更换器，则应忽略 *slot_nr*。在 `cdrom.h` 中列出了可能性：
*
* CDS_NO_INFO         /* 无可用信息 */
* CDS_NO_DISC         /* 未插入光盘，托盘已关闭 */
* CDS_TRAY_OPEN       /* 托盘打开 */
* CDS_DRIVE_NOT_READY /* 出现问题，托盘正在移动？ */
* CDS_DISC_OK         /* 光盘已装入且一切正常 */
*/

int tray_move(struct cdrom_device_info *cdi, int position)
/*
* 如果实现了这个函数，则应控制托盘的移动。（没有其他函数应控制这一点。）
* 参数 *position* 控制所需的移动方向：
*
* - 0 关闭托盘
* - 1 打开托盘
*
* 成功时返回 0，错误时返回非零值。请注意，如果托盘已经处于所需位置，则无需采取任何操作，
* 返回值应为 0。
*/

int lock_door(struct cdrom_device_info *cdi, int lock)
/*
* 此函数（而非其他代码）控制门锁，如果驱动器支持这项功能的话。
* *lock* 的值控制所需的锁定状态：
*
* - 0 解锁门，允许手动打开
* - 1 锁定门，无法手动弹出托盘
*
* 成功时返回 0，错误时返回非零值。请注意，如果门已经处于请求的状态，则无需采取任何操作，
* 返回值应为 0。
*/

int select_speed(struct cdrom_device_info *cdi, unsigned long speed)
/*
* 一些 CD-ROM 驱动器能够改变它们的头速。有几种原因需要改变 CD-ROM 驱动器的速度。
* 制造不良的 CD-ROM 可能会从低于最大头速中获益。现代 CD-ROM 驱动器可以获得非常高的头速（高达 *24x* 是常见的）。
* 已经有报告称这些驱动器在高速下可能会出现读取错误，降低速度可以防止在这种情况下丢失数据。
* 最后，这些驱动器中的一些会产生令人讨厌的噪音，较低的速度可能会减轻这种情况。
*
* 此函数指定了读取数据或播放音频的速度。*speed* 的值指定驱动器的头速，以标准 CD-ROM 速度单位（176kB/秒原始数据或 150kB/秒文件系统数据）进行测量。
* 因此，要请求 CD-ROM 驱动器以 300kB/秒运行，您将使用 CDROM_SELECT_SPEED *ioctl* 调用 *speed=2*。
* 特殊值 `0` 表示 `自动选择`，即最大数据率或实时音频速率。如果驱动器不具备这种 `自动选择` 功能，
* 则应根据当前加载的光盘作出决定，并且返回值应为正数。负返回值表示错误。
*/
```
以下是提供的英文代码注释和描述的中文翻译：

```plaintext
int get_last_session(struct cdrom_device_info *cdi,
                     struct cdrom_multisession *ms_info)

此函数应该实现旧版本对应的 *ioctl()*. 对于设备 *cdi->dev*，当前光盘最后一会话的开始位置应通过指针参数 *ms_info* 返回。需要注意的是，在 `cdrom.c` 中的例程已经对这个参数进行了规范化：请求的格式将**始终**为 *CDROM_LBA*（线性块寻址模式），无论调用软件请求的是什么格式。但是规范化处理更为深入：低级实现如果希望可以以 *CDROM_MSF* 格式返回请求的信息（当然要适当地设置 *ms_info->addr_format* 字段），在 `cdrom.c` 中的例程会在必要时进行转换。成功时返回值为 0。

int get_mcn(struct cdrom_device_info *cdi,
            struct cdrom_mcn *mcn)

某些光盘携带有“媒体目录号”（MCN），也称为“通用产品代码”（UPC）。该号码应该反映产品条形码上通常能找到的编号。不幸的是，少数携带此类号码的光盘甚至不使用相同的格式。此函数的返回参数是一个预先声明的类型为 *struct cdrom_mcn* 的内存区域的指针。MCN 应该是一个由空字符终止的 13 个字符的字符串。

int reset(struct cdrom_device_info *cdi)

此调用应该对驱动器执行硬复位（尽管在需要硬复位的情况下，驱动器可能不再响应命令）。最好是在驱动器完成复位后才将控制权返回给调用者。如果驱动器不再响应，则底层低级 CD-ROM 驱动程序可能会超时。

int audio_ioctl(struct cdrom_device_info *cdi,
                unsigned int cmd, void *arg)

`cdrom.h` 中定义的一些 CD-ROM-\ *ioctl()* 可以通过上述例程来实现，因此 *cdrom_ioctl* 函数会使用这些例程。然而，大多数 *ioctl()* 涉及音频控制。我们决定通过一个单独的函数来处理这些调用，重复 *cmd* 和 *arg* 参数。需要注意的是后者是 *void* 类型而不是 *unsigned long int* 类型。
*cdrom_ioctl()* 函数确实做了一些有用的事情，它将地址格式类型规范化为 *CDROM_MSF*（分钟、秒、帧）用于所有音频调用。它还会验证 *arg* 的内存位置，并为参数保留栈内存。这使得 *audio_ioctl()* 的实现比旧驱动程序方案简单得多。例如，您可以在 `cm206.c` 中查找应该根据此文档更新的 *cm206_audio_ioctl()* 函数。
未实现的 ioctl 应返回 *-ENOSYS*，但无害的请求（例如，*CDROMSTART*）可以通过返回 0（成功）来忽略。其他错误应遵循标准，无论它们是什么。当底层驱动程序返回错误时，统一 CD-ROM 驱动程序会尽可能地将错误代码返回给调用程序（我们可能会决定在 *cdrom_ioctl()* 中规范化返回值，以便为音频播放软件提供统一的接口）。

int dev_ioctl(struct cdrom_device_info *cdi,
              unsigned int cmd, unsigned long arg)

一些 *ioctl()* 似乎特定于某些 CD-ROM 驱动器。也就是说，它们被引入以服务于某些驱动器的某些功能。实际上，有 6 种不同的 *ioctl()* 用于以某种特定格式或音频数据读取数据。我认为支持将音频轨作为数据读取的驱动器并不多，这可能是出于保护艺术家版权的原因。此外，如果支持音频轨，我认为应该通过 VFS 而不是通过 *ioctl()* 来实现。这里的一个问题可能是音频帧长度为 2352 字节，因此要么音频文件系统一次性请求 75264 字节（512 和 2352 的最小公倍数），要么驱动程序需要处理这种不一致性（对此我持反对意见）。此外，硬件很难找到精确的帧边界，因为音频帧中没有同步头。一旦这些问题得到解决，此代码应在 `cdrom.c` 中标准化。
由于有许多 *ioctl()* 似乎是为了满足某些驱动程序而引入的，任何非标准的 *ioctl()* 都通过 *dev_ioctl()* 调用来处理。原则上，“私有”的 *ioctl()* 应该编号为设备的主要编号之后，而不是一般的 CD-ROM *ioctl* 编号 `0x53`。目前不受支持的 *ioctl()* 包括：

CDROMREADMODE1, CDROMREADMODE2, CDROMREADAUDIO, CDROMREADRAW,
CDROMREADCOOKED, CDROMSEEK, CDROMPLAY-BLK 和 CDROM-READALL

.. [#f2]

   是否有实际使用的这些功能的软件？我很感兴趣！

.. _cdrom_capabilities:

CD-ROM 功能
-----------

除了仅仅实现某些 *ioctl* 调用之外，`cdrom.c` 中的接口提供了指示 CD-ROM 驱动器**功能**的可能性。这可以通过在注册阶段对 `cdrom.h` 中定义的功能常量进行 OR 操作来完成。目前，功能包括：

CDC_CLOSE_TRAY		/* 可以通过软件控制关闭托盘 */
CDC_OPEN_TRAY		/* 可以打开托盘 */
CDC_LOCK		/* 可以锁定和解锁门 */
CDC_SELECT_SPEED	/* 可以选择速度，单位为 * sim*150 kB/s */
CDC_SELECT_DISC		/* 驱动器是点唱机 */
CDC_MULTI_SESSION	/* 可以读取会话 *> rm1* */
CDC_MCN			/* 可以读取媒体目录号 */
CDC_MEDIA_CHANGED	/* 可以报告光盘是否已更改 */
CDC_PLAY_AUDIO		/* 可以执行音频功能（播放、暂停等） */
CDC_RESET		/* 硬件重置设备 */
CDC_IOCTLS		/* 驱动程序具有非标准 ioctl */
CDC_DRIVE_STATUS	/* 驱动程序实现了驱动状态 */

功能标志被声明为 *const*，以防止驱动程序意外篡改其内容。功能标志实际上告知 `cdrom.c` 驱动程序能够做什么。如果驱动程序发现的驱动器不具备该功能，则可以通过 *cdrom_device_info* 变量 *mask* 掩码掉。例如，SCSI CD-ROM 驱动程序已经实现了加载和弹出 CD-ROM 的代码，因此其对应的 *capability* 标志会被设置。但是 SCSI CD-ROM 驱动器可能是盒装系统，不能装载托盘，因此对于此类驱动器，*cdrom_device_info* 结构体将 *CDC_CLOSE_TRAY* 位设置在 *mask* 中。
在 `cdrom.c` 文件中，你会遇到许多这样的构造：

if (cdo->capability & ~cdi->mask & CDC_<capability>) ..
没有 *ioctl* 来设置掩码... 原因是我认为控制**行为**比控制**功能**更好。
```

请注意，文本中的某些部分（如注释和脚注）被直接翻译并保留了原文的格式。
最终标志寄存器控制CD-ROM驱动器的行为，以满足不同用户的需求，希望这能独立于为Linux社区提供驱动支持的作者的想法。当前的行为选项包括：

- `CDO_AUTO_CLOSE` /* 在设备打开时尝试关闭托盘 */
- `CDO_AUTO_EJECT` /* 在设备最后关闭时尝试打开托盘 */
- `CDO_USE_FFLAGS` /* 使用 file_pointer->f_flags 来指示打开的目的 */
- `CDO_LOCK` /* 如果设备被打开，则尝试锁定门 */
- `CDO_CHECK_TYPE` /* 如果为数据打开则确保光盘类型为数据 */

该寄存器的初始值为 `CDO_AUTO_CLOSE | CDO_USE_FFLAGS | CDO_LOCK`，这反映了我个人对用户界面和软件标准的看法。在你提出异议之前，有两个新的 *ioctl()* 已在 `cdrom.c` 中实现，允许您通过软件控制行为。这些是：

- `CDROM_SET_OPTIONS` /* 设置由 (int)arg 指定的选项 */
- `CDROM_CLEAR_OPTIONS` /* 清除由 (int)arg 指定的选项 */

有一个选项需要更多的解释：`CDO_USE_FFLAGS`。在接下来的部分中，我们将解释为什么需要这个选项。一个名为 `setcd` 的软件包，可从Debian发行版和 `sunsite.unc.edu` 获得，允许用户级别控制这些标志。

了解打开CD-ROM设备目的的必要性
=================================

传统上，Unix设备可以以两种不同的“模式”使用，一种是通过读写设备文件，另一种是通过设备的 *ioctl()* 调用来发出控制命令。CD-ROM驱动器的问题在于它们可以用于两个完全不同的目的。一个是挂载可移动文件系统（CD-ROM），另一个是播放音频CD。音频命令完全是通过 *ioctl()* 实现的，这可能是由于最初的实现（如SUN？）就是这样。原则上，这样做并没有什么不对，但良好的CD播放控制要求无论驱动器处于何种状态，设备始终能够被打开以便发出 *ioctl* 命令。另一方面，当用作可移动介质磁盘驱动器（这是CD-ROM最初的目的）时，我们希望确保在打开设备时磁盘驱动器已准备好运行。在旧方案下，一些CD-ROM驱动程序不做任何完整性检查，导致在空驱动器上尝试挂载CD-ROM时，VFS向内核报告大量的I/O错误。这不是一种特别优雅的方式来发现没有插入CD-ROM；它更像是老式的IBM-PC尝试读取空软盘驱动器几秒钟后，然后系统抱怨无法从中读取数据。现在我们可以**感知**驱动器中的可移动介质是否存在，并且我们认为应该利用这一事实。在打开设备时进行完整性检查，验证CD-ROM的存在及其正确的类型（数据），将是理想的。

这两种使用CD-ROM驱动器的方式——主要用于数据传输，其次用于播放音频CD——对 *open()* 调用的行为有不同的需求。音频使用只是想打开设备以获取用于发出 *ioctl* 命令所需的文件句柄，而数据使用则希望打开以进行正确可靠的传输。用户程序唯一可以表明其打开设备**目的**的方式是通过 *flags* 参数（参见 `open(2)`）。对于CD-ROM设备而言，这些标志并未得到实现（某些驱动程序实现了对与写入相关的标志的检查，但这并不是严格必要的，如果设备文件具有正确的权限标志）。大多数选项标志对CD-ROM来说没有任何意义：*O_CREAT*、*O_NOCTTY*、*O_TRUNC*、*O_APPEND* 和 *O_SYNC* 对CD-ROM来说毫无意义。

因此，我们建议使用标志 *O_NONBLOCK* 来表明设备仅用于发出 *ioctl* 命令。严格地说， *O_NONBLOCK* 的含义是打开和随后对设备的调用不会使调用进程等待。我们可以将其解释为不要等待直到有人插入有效的数据CD-ROM。因此，我们对CD-ROM *open()* 调用的实现建议如下：

- 如果除了 *O_RDONLY* 之外没有设置其他标志，则设备将为数据传输而打开，并且只有在成功初始化传输的情况下返回值才会为0。该调用甚至可能引起CD-ROM的一些动作，例如关闭托盘。
- 如果设置了选项标志 *O_NONBLOCK*，则打开总是成功的，除非整个设备不存在。驱动程序将不采取任何动作。

那么标准如何？
-----------------

你可能会犹豫接受这个提议，因为它来自Linux社区，而不是某个标准化机构。Sun、SGI、HP和其他所有Unix和硬件供应商呢？嗯，这些公司处于幸运的位置，通常他们对其支持的产品的硬件和软件都有控制权，并且足够大到可以设定自己的标准。他们不必处理十几个或更多不同的竞争硬件配置。
顺便说一句，我认为Sun对安装CD-ROM的方法本质上非常好：在Solaris下，一个卷守护程序会自动将新插入的CD-ROM挂载在 `/cdrom/*<volume-name>*` 下。
在我看来，他们本应进一步推动这种方法，让**每个**局域网上的CD-ROM都挂载在相似的位置，也就是说，无论你在哪台特定机器上插入CD-ROM，它总会在目录树的相同位置出现，在每台系统上都是如此。当我想要为Linux实现这样的用户程序时，我遇到了各种驱动程序行为的差异，以及对一个通知媒体变化的 *ioctl* 的需求。
我们相信，在 Linux 社区中引入使用 *O_NONBLOCK* 来指示设备仅用于 *ioctl* 命令的做法是很容易实现的。所有的 CD 播放器程序作者都需要得到通知，我们甚至可以向这些程序提交我们自己的补丁。使用 *O_NONBLOCK* 在其他操作系统上很可能对 CD 播放器的行为没有影响。最后，用户可以通过调用 *ioctl(file_descriptor, CDROM_CLEAR_OPTIONS, CDO_USE_FFLAGS)* 回归到旧的行为。
*open()* 的首选策略
------------------------

`cdrom.c` 中的例程设计得如此之好，以至于可以在运行时配置任何类型的 CD-ROM 设备的行为，通过 *CDROM_SET/CLEAR_OPTIONS* *ioctls* 实现。因此，可以设置各种操作模式：

`CDO_AUTO_CLOSE | CDO_USE_FFLAGS | CDO_LOCK`
   这是默认设置。（未来加上 *CDO_CHECK_TYPE* 会更好。）如果设备尚未被任何其他进程打开，并且如果设备被打开以用于数据（未设置 *O_NONBLOCK*），并且发现托盘是打开的，则尝试关闭托盘。然后验证驱动器中是否有一张光盘，并且如果设置了 *CDO_CHECK_TYPE*，则验证它是否包含类型为“数据模式 1”的音轨。只有在所有测试都通过的情况下，返回值才为零。锁定门以防止文件系统损坏。如果驱动器被打开用于音频（设置 *O_NONBLOCK*），则不采取任何行动，并将返回值设为 0。
`CDO_AUTO_CLOSE | CDO_AUTO_EJECT | CDO_LOCK`
   这模仿了当前 sbpcd 驱动程序的行为。忽略选项标志，在首次打开时必要时关闭托盘。同样，在最后一次释放时打开托盘，也就是说，如果卸载了 CD-ROM，它会被自动弹出，以便用户可以更换它。

我们希望这些选项能够说服所有人（包括驱动程序维护者和用户程序开发者）采用新的 CD-ROM 驱动程序方案和选项标志解释。
`cdrom.c` 中例程的描述
======================

`cdrom.c` 中只有少数例程被导出给驱动程序。在这个新章节中，我们将讨论这些例程以及那些接管 CD-ROM 内核接口的功能。与 `cdrom.c` 相关的头文件称为 `cdrom.h`。以前，该文件的部分内容放在 `ucdrom.h` 文件中，但现在已合并回 `cdrom.h`。
```
struct file_operations cdrom_fops
```

这个结构体的内容已在 cdrom_api_ 中描述。指向此结构体的指针被分配给 *gendisk* 结构中的 *fops* 字段。
```
int register_cdrom(struct cdrom_device_info *cdi)
```

此函数的使用方式类似于将 *cdrom_fops* 注册给内核的方式：设备操作和信息结构应按照 cdrom_api_ 中所述注册给统一 CD-ROM 驱动程序：
```
register_cdrom(&<device>_info);
```

此函数成功时返回零，失败时返回非零。结构体 *<device>_info* 应有一个指向驱动程序的 *<device>_dops* 的指针，如下所示：
```
struct cdrom_device_info <device>_info = {
    <device>_dops;
    ..
}
```

请注意，驱动程序必须有一个静态结构 *<device>_dops*，而它可以有任意数量的 *<device>_info* 结构体，这取决于有多少个次设备处于活动状态。*register_cdrom()* 从这些结构体构建一个链表。
```
void unregister_cdrom(struct cdrom_device_info *cdi)
```

取消注册具有次号 *MINOR(cdi->dev)* 的设备 *cdi* 会从列表中移除次设备。如果它是低级驱动程序注册的最后一个次设备，这将断开已注册的设备操作例程与 CD-ROM 接口之间的连接。此函数成功时返回零，失败时返回非零。
``` 
int cdrom_open(struct inode *ip, struct file *fp)
```

此函数并非由低级驱动程序直接调用，而是列在标准的 *cdrom_fops* 中。如果虚拟文件系统（VFS）打开一个文件，则此函数将被激活。在此例程中实现了一种策略，处理 *cdrom_device_ops* 中与设备关联的所有能力和选项。然后，程序流程转移至设备相关的 *open()* 调用：

```
void cdrom_release(struct inode *ip, struct file *fp)
```

此函数实现了 *cdrom_open()* 的逆向逻辑，并随后调用设备相关的 *release()* 常规。当使用计数达到 0 时，通过调用 *sync_dev(dev)* 和 *invalidate_buffers(dev)* 来刷新分配的缓冲区。
.. _cdrom_ioctl:

```
int cdrom_ioctl(struct inode *ip, struct file *fp, unsigned int cmd, unsigned long arg)
```

此函数以统一的方式处理所有针对 CD-ROM 设备的标准 *ioctl* 请求。不同的调用可以分为三类：可以通过设备操作直接实现的 *ioctl()*，通过 *audio_ioctl()* 调用路由的，以及剩下的可能依赖于设备的。通常，负返回值表示错误。

### 直接实现的 *ioctl()* 

以下“旧”CD-ROM *ioctl()* 是通过直接调用 *cdrom_device_ops* 中的设备操作来实现的（如果已经实现并且没有被屏蔽）：

- `CDROMMULTISESSION`
    - 请求 CD-ROM 上的最后一会话
- `CDROMEJECT`
    - 打开托盘
- `CDROMCLOSETRAY`
    - 关闭托盘
- `CDROMEJECT_SW`
    - 如果 *arg ≠ 0*，设置行为为自动关闭（首次打开时关闭托盘）和自动弹出（最后一次释放时弹出），否则设置行为为在 *open()* 和 *release()* 调用时不移动托盘
- `CDROM_GET_MCN`
    - 从 CD 获取媒体目录编号

### 通过 *audio_ioctl()* 路由的 *ioctl()* 

以下一组 *ioctl()* 是通过调用 *cdrom_fops* 函数 *audio_ioctl()* 实现的。内存检查和分配在 *cdrom_ioctl()* 中执行，同时对地址格式（*CDROM_LBA*/*CDROM_MSF*）进行清理。

- `CDROMSUBCHNL`
    - 在类型为 `struct cdrom_subchnl *` 的参数 *arg* 中获取子通道数据
```
`CDROMREADTOCHDR`
读取目录表头，在*arg*中，类型为
`struct cdrom_tochdr *`

`CDROMREADTOCENTRY`
读取目录表中的一个条目，在*arg*中指定，类型为
`struct cdrom_tocentry *`

`CDROMPLAYMSF`
以分钟、秒、帧格式播放音频片段，由*arg*界定，类型为
`struct cdrom_msf *`

`CDROMPLAYTRKIND`
以曲目-索引格式播放音频片段，由*arg*界定，类型为
`struct cdrom_ti *`

`CDROMVOLCTRL`
设置音量，由*arg*指定，类型为
`struct cdrom_volctrl *`

`CDROMVOLREAD`
读取音量到*arg*，类型为
`struct cdrom_volctrl *`

`CDROMSTART`
启动光盘

`CDROMSTOP`
停止播放音频片段

`CDROMPAUSE`
暂停播放音频片段

`CDROMRESUME`
恢复播放
### `cdrom.c` 中新增的 *ioctl()* 函数

以下 *ioctl()* 函数已被引入，以允许用户程序控制各个 CD-ROM 设备的行为。新 *ioctl* 命令可以通过其名称中的下划线来识别：

- `CDROM_SET_OPTIONS`
    - 设置由 *arg* 指定的选项。返回修改后的选项标志寄存器。使用 *arg = 0* 来读取当前标志。
- `CDROM_CLEAR_OPTIONS`
    - 清除由 *arg* 指定的选项。返回修改后的选项标志寄存器。
- `CDROM_SELECT_SPEED`
    - 根据 *arg* 选择光盘的倍速，单位为标准 CD-ROM 倍速（176 kB/s 的原始数据或 150 kB/s 的文件系统数据）。值 0 表示“自动选择”，即音频光盘以实时速度播放，数据光盘以最高速度播放。
    - *arg* 的值会与在 *cdrom_dops* 中找到的驱动器的最大倍速进行比较。
- `CDROM_SELECT_DISC`
    - 从自动换盘机中选择编号为 *arg* 的光盘。第一张光盘编号为 0。*arg* 的值会与在 *cdrom_dops* 中找到的自动换盘机的最大光盘数量进行比较。
- `CDROM_MEDIA_CHANGED`
    - 如果自上次调用以来光盘已被更换，则返回 1。
    - 对于自动换盘机，额外的参数 *arg* 指定了要提供信息的插槽。特殊值 *CDSL_CURRENT* 请求返回有关当前选定插槽的信息。
- `CDROM_TIMED_MEDIA_CHANGE`
    - 检查自用户提供的某个时间点以来光盘是否已更换，并返回最后一次更换光盘的时间。
*arg* 是指向 *cdrom_timed_media_change_info* 结构体的指针。
*arg->last_media_change* 可能会被调用代码设置，以指示最后一次已知媒体更换的时间戳（由调用者提供）。
在成功返回后，此 ioctl 调用将 *arg->last_media_change* 设置为内核/驱动程序所知的最新媒体更换时间戳（以毫秒为单位），如果该时间戳比调用者设置的时间戳更新，则将 *arg->has_changed* 设置为 1。
`CDROM_DRIVE_STATUS`
通过调用 *drive_status()* 返回驱动器的状态。返回值定义在 cdrom_drive_status_ 中。
请注意，此调用不会返回有关驱动器当前播放活动的信息；可以通过向 *CDROMSUBCHNL* 发出 *ioctl* 调用来查询这些信息。对于自动换盘机，额外参数 *arg* 指定了提供（可能有限的）信息的插槽。特殊值 *CDSL_CURRENT* 表示请求返回关于当前选定插槽的信息。
`CDROM_DISC_STATUS`
返回当前在驱动器中的光盘类型。
应将其视为 *CDROM_DRIVE_STATUS* 的补充。
此 *ioctl* 可以提供一些关于当前插入驱动器的光盘的信息。此功能以前实现在低级驱动程序中，但现在完全在统一 CD-ROM 驱动程序中实现。
CD 作为各种数字信息载体的历史发展导致了许多不同类型的光盘。
此 *ioctl* 仅在 CD 上 \emph{只有一种} 类型的数据时有用。虽然这通常是这种情况，但也非常常见的是，CD 上有一些数据轨道和一些音频轨道。由于这是一个现有接口，而不是通过更改其创建时所做的假设来修复这个接口（这样会破坏所有使用此功能的用户应用程序），统一 CD-ROM 驱动程序按照以下方式实现此 *ioctl*：如果在考虑的 CD 上有音频轨道，并且绝对没有 CD-I、XA 或数据轨道，则报告为 *CDS_AUDIO*。如果有音频和数据轨道，则返回 *CDS_MIXED*。如果没有音频轨道，并且在考虑的 CD 上有任何 CD-I 轨道，则报告为 *CDS_XA_2_2*。如果不符合上述情况，但 CD 上有任何 XA 轨道，则报告为 *CDS_XA_2_1*。
最后，如果所讨论的 CD 上有任何数据轨，
它将被报告为数据 CD（*CDS_DATA_1*）
此 *ioctl* 可以返回：

		CDS_NO_INFO	/* 没有可用的信息 */
		CDS_NO_DISC	/* 没有插入光盘，或托盘打开 */
		CDS_AUDIO	/* 音频光盘 (每帧 2352 字节音频数据) */
		CDS_DATA_1	/* 数据光盘，模式 1 (每帧 2048 用户字节) */
		CDS_XA_2_1	/* 混合数据 (XA)，模式 2，形式 1 (2048 用户字节) */
		CDS_XA_2_2	/* 混合数据 (XA)，模式 2，形式 2 (2324 用户字节) */
		CDS_MIXED	/* 音频/数据混合光盘 */

关于各种光盘类型帧布局的一些信息，请参阅最近版本的 `cdrom.h`
`CDROM_CHANGER_NSLOTS`
	返回自动换碟机中的插槽数量
`CDROMRESET`
	重置驱动器
`CDROM_GET_CAPABILITY`
	返回驱动器的能力标志。有关这些标志的更多信息，请参阅
	`cdrom_capabilities_` 部分
`CDROM_LOCKDOOR`
	锁定驱动器门。`arg == 0` 解锁门，
	其他任何值则将其锁定
`CDROM_DEBUG`
	开启调试信息。只有 root 用户允许这样做
与 `CDROM_LOCKDOOR` 相同的语义
设备相关的 *ioctl()* 函数
---------------------------

最后，所有其他 *ioctl()* 调用若已实现，则传递给 *dev_ioctl()* 函数。
不会执行内存分配或验证
如何更新你的驱动程序
======================

- 备份当前的驱动程序
- 获取文件 `cdrom.c` 和 `cdrom.h`，它们应该位于随此文档一同提供的目录树中。
- 确保你包含了 `cdrom.h`。
- 将 *register_blkdev* 函数的第三个参数从 `&<your-drive>_fops` 更改为 `&cdrom_fops`。
- 在该行之后，添加以下内容以与统一CD-ROM驱动程序注册：

  ```
  register_cdrom(&<your-drive>_info);
  ```

- 同样地，在适当的位置添加对 *unregister_cdrom()* 的调用。
- 复制一个设备操作 *struct* 的示例到你的源代码中，例如，从 `cm206.c` 中的 *cm206_dops*，并将所有条目更改为对应于你的驱动程序的名字，或者你喜欢的名字。如果你的驱动程序不支持某个功能，则将该条目的值设置为 *NULL*。在 *capability* 条目中，你应该列出你的驱动程序当前支持的所有功能。如果你的驱动程序具有未列出的功能，请给我发送一条消息。
- 从同一个示例驱动程序复制 *cdrom_device_info* 声明，并根据需要修改各条目。如果你的驱动程序动态确定硬件的功能，则此结构也应该动态声明。
- 根据 `cdrom.h` 中列出的原型和 cdrom_api_ 中给出的规范实现你在 `<device>_dops` 结构中的所有函数。很可能你已经实现了大部分代码，你几乎肯定需要调整函数原型和返回值。
- 将你的 `<device>_ioctl()` 函数重命名为 *audio_ioctl* 并稍作修改其原型。删除 cdrom_ioctl_ 第一部分中列出的条目，如果你的代码是正确的，这些只是调用你前一步中修改过的例程。
- 你可以移除 *audio_ioctl()* 函数中处理音频命令的所有剩余内存检查代码（这些在 cdrom_ioctl_ 的第二部分列出）。不需要进行内存分配，因此 *switch* 语句中的大多数 *case* 应看起来类似如下：

  ```
  case CDROMREADTOCENTRY:
      get_toc_entry((struct cdrom_tocentry *) arg);
  ```

- 所有剩余的 *ioctl* 情况必须移到单独的函数 *<device>_ioctl* 中，即设备相关的 *ioctl()*。请注意，内存检查和分配必须保留在这个代码中！
- 修改 *<device>_open()* 和 *<device>_release()* 的原型，并移除任何策略性代码（例如，托盘移动、门锁等）。
- 尝试重新编译驱动程序。我们建议使用模块化方式，既适用于 `cdrom.o` 也适用于你的驱动程序，因为这样调试更容易。
感谢所有参与的人。首先，感谢埃里克·安德森（Erik Andersen），他接手了维护`cdrom.c`的工作，并在2.1内核中整合了大量的CD-ROM相关代码。感谢斯科特·斯奈德（Scott Snyder）和格哈德·克诺尔（Gerd Knorr），他们是第一批为SCSI和IDE-CD驱动程序实现此接口的人，并为相对于2.0内核的数据结构扩展提出了许多想法。此外，还要感谢海科·艾斯费尔特（Heiko Eißfeldt）、托马斯·奎诺（Thomas Quinot）、乔恩·汤姆斯（Jon Tombs）、肯·皮齐尼（Ken Pizzini）、埃伯哈德·莫恩克贝格（Eberhard Mönkeberg）和安德鲁·克罗尔（Andrew Kroll），这些Linux CD-ROM设备驱动程序的开发者们，在撰写过程中慷慨地提供了建议和批评。最后，当然要感谢林纳斯·托瓦兹（Linus Torvalds），因为他使这一切成为可能。
