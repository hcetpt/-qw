SPDX 许可证标识符: GPL-2.0

=========
SAS 层
=========

SAS 层是一个管理基础设施，用于管理 SAS LLDD。它位于 SCSI 核心和 SAS LLDD 之间。其布局如下：SCSI 核心关注 SAM/SPC 问题，而 SAS LLDD+序列器关注 phy/OOB/link 管理；SAS 层则关注以下内容：

      * SAS Phy/Port/HA 事件管理（LLDD 生成，SAS 层处理），
      * SAS 端口管理（创建/销毁），
      * SAS 域发现与重新验证，
      * SAS 域设备管理，
      * SCSI 主机注册/注销，
      * 设备在 SCSI 核心（SAS）或 libata（SATA）中的注册，并且
      * 扩展器管理和将扩展器控制导出到用户空间。

一个 SAS LLDD 是一个 PCI 设备驱动程序。它关注 phy/OOB 管理以及厂商特定的任务，并向 SAS 层生成事件。
SAS 层执行大部分 SAS 任务，如 SAS 1.1 规范中所述。
`sas_ha_struct` 描述了 SAS LLDD 对 SAS 层的接口。其中大部分由 SAS 层使用，但有少数字段需要由 LLDD 初始化。
在初始化硬件后，从 `probe()` 函数调用 `sas_register_ha()`。这会将你的 LLDD 注册到 SCSI 子系统，创建一个 SCSI 主机，并将你的 SAS 驱动程序注册到它创建的 sysfs SAS 树中。
然后返回。之后，你可以启用物理层以实际开始 OOB 操作（此时你的驱动程序将开始调用 `notify_*` 事件回调函数）。

结构描述
======================

``struct sas_phy``
------------------

通常，此结构静态嵌入到你的驱动程序的 phy 结构中，如下所示：

    struct my_phy {
	    blah;
	    struct sas_phy sas_phy;
	    bleh;
    };

然后所有 phy 都是你的 HA 结构中的 `my_phy` 数组（如下所示）。
随着你初始化 phy，你也初始化 `sas_phy` 结构及其自身的 phy 结构。
一般来说，phy 由 LLDD 管理，端口由 SAS 层管理。因此，phy 由 LLDD 初始化和更新，端口由 SAS 层初始化和更新。
以下是一个方案，其中LLDD可以读写某些字段，而SAS层只能读取这些字段，反之亦然。这样做的目的是为了避免不必要的锁定。

- `enabled`：必须设置（0/1）。
- `id`：必须设置在[0, MAX_PHYS]范围内。
- `class`, `proto`, `type`, `role`, `oob_mode`, `linkrate`：必须设置。
- `oob_mode`：当OOB完成时设置，并通知SAS层。
- `sas_addr`：通常指向一个数组，该数组保存PHY的SAS地址，可能位于`my_phy`结构中的某个位置。
- `attached_sas_addr`：当你（LLDD）接收到IDENTIFY帧或FIS帧之前设置此字段，然后通知SAS层。有时候LLDD可能希望伪造或提供PHY/端口上的不同SAS地址，这允许它这样做。最好从IDENTIFY帧中复制SAS地址，或者为直接连接的SATA设备生成一个SAS地址。发现过程可能会稍后更改这个值。
- `frame_rcvd`：当你接收到IDENTIFY/FIS帧时，将帧复制到这里；锁定、复制、设置`frame_rcvd_size`并解锁，然后调用事件。由于无法确切知道硬件帧大小，因此你需在PHY结构中定义实际数组，并让此指针指向它。锁定状态下从DMA内存区域复制帧到该区域。
- `sas_prim`：接收原始命令时放在这里。参见`sas.h`。获取锁，设置原始命令，释放锁，通知。
- `port`：如果PHY属于某个端口，则指向`sas_port`——LLDD只读取此字段。它指向PHY所属的`sas_port`。由SAS层设置。
- `ha`：可设置；无论如何SAS层会设置它。
- `lldd_phy`：你应该将其设置为指向你的PHY，以便当SAS层调用你的回调函数并传递一个PHY给你时，你可以更快地找到路径。如果`sas_phy`是嵌入式的，也可以使用`container_of`——任选其一。
``struct sas_port``
-------------------

LLDD 不设置此结构体中的任何字段 —— 它只读取这些字段。这些字段应该不难理解。
`phy_mask` 是 32 位的，目前这应该是足够的，因为我还没有听说过有 HA 设备拥有超过 8 个物理端口。
`lldd_port`
    - 我还没有发现它的用途 —— 也许其他希望有自己的内部端口表示的 LLDD 可以利用这个字段。

``struct sas_ha_struct``
------------------------

它通常在你自己的 LLDD 结构体中静态声明，描述你的适配器，如下所示：

```c
struct my_sas_ha {
    blah;
    struct sas_ha_struct sas_ha;
    struct my_phy phys[MAX_PHYS];
    struct sas_port sas_ports[MAX_PHYS]; /* (1) */
    bleh;
};

(1) 如果你的 LLDD 没有自己的端口表示方式
需要初始化的内容（下面提供了一个示例函数）
pcidev
^^^^^^

sas_addr
       - 由于 SAS 层不想处理内存分配等事务，因此它指向某处静态分配的数组（例如在你的主机适配器结构中），并保存由你或制造商提供的主机适配器的 SAS 地址
sas_port
^^^^^^^^

sas_phy
      - 指针数组。 （参见上面关于 sas_addr 的说明）
这些必须被设置。 请参阅下方更多注释
num_phys
       - sas_phy 数组中存在的物理端口数量，以及 sas_port 数组中存在的端口数量。 最多可以有 num_phys 个端口（每个端口一个），所以我们去掉 num_ports，仅使用 num_phys

事件接口：
```
/* LLDD 调用这些函数来通知类事件。 */
void sas_notify_port_event(struct sas_phy *, enum port_event, gfp_t);
void sas_notify_phy_event(struct sas_phy *, enum phy_event, gfp_t);
```

端口通知：
```
/* 类调用这些函数来通知 LLDD 事件。 */
void (*lldd_port_formed)(struct sas_phy *);
void (*lldd_port_deformed)(struct sas_phy *);
```

如果 LLDD 希望在端口形成或解除时得到通知，则将其设置为满足该类型的函数。
SAS 低级设备驱动（LLDD）还应实现SAM中描述的至少一个任务管理功能（TMFs）：

```c
/* 任务管理功能。必须从进程上下文调用。 */
int (*lldd_abort_task)(struct sas_task *);
int (*lldd_abort_task_set)(struct domain_device *, u8 *lun);
int (*lldd_clear_task_set)(struct domain_device *, u8 *lun);
int (*lldd_I_T_nexus_reset)(struct domain_device *);
int (*lldd_lu_reset)(struct domain_device *, u8 *lun);
int (*lldd_query_task)(struct sas_task *);

/* 请阅读T10.org上的SAM以获取更多信息。 */

/* 端口和适配器管理 */
int (*lldd_clear_nexus_port)(struct sas_port *);
int (*lldd_clear_nexus_ha)(struct sas_ha_struct *);

/* SAS LLDD应实现以下至少一个功能。 */

/* 物理层管理 */
int (*lldd_control_phy)(struct sas_phy *, enum phy_func);

/* 设置该指针指向您的HA结构。您也可以使用container_of，如上面所示。 */
lldd_ha
    - 设置此指针指向您的HA结构。如果已嵌入，请使用container_of。

一个初始化和注册函数示例可以如下所示（在probe()最后调用，但在使物理层进行带外操作之前）：
```
static int register_sas_ha(struct my_sas_ha *my_ha)
{
    int i;
    static struct sas_phy   *sas_phys[MAX_PHYS];
    static struct sas_port  *sas_ports[MAX_PHYS];

    my_ha->sas_ha.sas_addr = &my_ha->sas_addr[0];

    for (i = 0; i < MAX_PHYS; i++) {
        sas_phys[i] = &my_ha->phys[i].sas_phy;
        sas_ports[i] = &my_ha->sas_ports[i];
    }

    my_ha->sas_ha.sas_phy  = sas_phys;
    my_ha->sas_ha.sas_port = sas_ports;
    my_ha->sas_ha.num_phys = MAX_PHYS;

    my_ha->sas_ha.lldd_port_formed = my_port_formed;

    my_ha->sas_ha.lldd_dev_found = my_dev_found;
    my_ha->sas_ha.lldd_dev_gone = my_dev_gone;

    my_ha->sas_ha.lldd_execute_task = my_execute_task;

    my_ha->sas_ha.lldd_abort_task     = my_abort_task;
    my_ha->sas_ha.lldd_abort_task_set = my_abort_task_set;
    my_ha->sas_ha.lldd_clear_task_set = my_clear_task_set;
    my_ha->sas_ha.lldd_I_T_nexus_reset = NULL; // SAS 1.1未定义I_T Nexus Reset TMF
    my_ha->sas_ha.lldd_lu_reset       = my_lu_reset;
    my_ha->sas_ha.lldd_query_task     = my_query_task;

    my_ha->sas_ha.lldd_clear_nexus_port = my_clear_nexus_port;
    my_ha->sas_ha.lldd_clear_nexus_ha = my_clear_nexus_ha;

    my_ha->sas_ha.lldd_control_phy = my_control_phy;

    return sas_register_ha(&my_ha->sas_ha);
}
```

事件
====
事件是SAS LLDD通知SAS层的唯一方式。没有其他方法可以让LLDD告诉SAS层任何内部或SAS域中的事件。
物理事件：
```
PHYE_LOSS_OF_SIGNAL,    // 可选(C)
PHYE_OOB_DONE,
PHYE_OOB_ERROR,         // 可选(C)
PHYE_SPINUP_HOLD
```

端口事件，通过_phy_传递：
```
PORTE_BYTES_DMAED,      // 必须(M)
PORTE_BROADCAST_RCVD,   // 扩展器(E)
PORTE_LINK_RESET_ERR,   // 可选(C)
PORTE_TIMER_EVENT,      // 可选(C)
PORTE_HARD_RESET
```

主机适配器事件：
```
HAE_RESET
```

SAS LLDD应能够生成：
- 至少一个来自组C（可选）的事件，
- 标记为M（必须）的事件是必须的（仅一个），
- 如果希望SAS层处理域重新验证，则标记为E（扩展器）的事件（仅一个此类）
- 未标记的事件是可选的。

含义：
```
HAE_RESET
    - 当您的HA发生内部错误并被重置时
```
### 翻译成中文：

#### 常量定义：
- `PORTE_BYTES_DMAED`
    - 在接收到 IDENTIFY/FIS 帧时

- `PORTE_BROADCAST_RCVD`
    - 在接收到一个原始数据包时

- `PORTE_LINK_RESET_ERR`
    - 定时器超时，信号丢失，DWS 丢失等 [1]_

- `PORTE_TIMER_EVENT`
    - DWS 重置定时器超时 [1]_

- `PORTE_HARD_RESET`
    - 收到硬重置原始数据包

- `PHYE_LOSS_OF_SIGNAL`
    - 设备已消失 [1]_

- `PHYE_OOB_DONE`
    - OOB 操作正常完成且 oob_mode 有效

- `PHYE_OOB_ERROR`
    - 执行 OOB 操作时出现错误，设备可能已断开连接 [1]_

- `PHYE_SPINUP_HOLD`
    - SATA 存在，但未发送 COMWAKE
    .. [1] 应该设置/清除 phy 中相应的字段，
           或者可以调用内联的 sas_phy_disconnected() 函数（只是一个辅助函数），从它们的任务中调用

#### 执行命令 SCSI 远程过程调用 (RPC)：

```c
int (*lldd_execute_task)(struct sas_task *, gfp_t gfp_flags);
```

用于将任务排队到 SAS LLDD。`@task` 是要执行的任务，`@gfp_mask` 定义了调用者的上下文。

此函数应实现执行命令 SCSI RPC，

也就是说，当调用 `lldd_execute_task()` 时，命令应立即通过传输层发出。在 SAS LLDD 中没有任何级别的排队。

返回值：
- `-SAS_QUEUE_FULL`，`-ENOMEM`，没有任务被排队；
- `0`，任务已被排队；

```c
struct sas_task {
	dev -- 此任务的目标设备
	task_proto -- 枚举 `sas_proto` 中的一个
	scatter -- 分散/聚集列表数组指针
	num_scatter -- 分散列表中的元素数量
	total_xfer_len -- 预期传输的总字节数
	data_dir -- PCI_DMA_...
	task_done -- 任务执行完成后回调
};
```

#### 发现
##### sysfs 树的目的：
1. 显示当前时间 SAS 域的物理布局，即当前域在物理世界中的样子。
2. 显示一些设备参数，在发现时的状态。
这是一个链接到 tree(1) 程序，对于查看 SAS 域非常有用：
ftp://mama.indstate.edu/linux/tree/

我期望用户空间应用程序能够创建这个图形界面。
也就是说，sysfs 域树不会显示或保留状态（例如，如果你更改了 READY LED MEANING 设置），但它会显示域设备当前的连接状态。
保持内部设备状态变化的责任在于上层（命令集驱动程序）和用户空间。
当一个或多个设备从域中拔出时，这会立即反映在 sysfs 树中，并且这些设备会被从系统中移除。
结构 `domain_device` 描述了 SAS 域中的任何设备。它完全由 SAS 层管理。一个任务指向一个域设备，这样 SAS LLDD 就知道将任务发送到哪里。SAS LLDD 只读取 `domain_device` 结构的内容，但从不创建或销毁它。

用户空间中的扩展器管理
========================

在 sysfs 中每个扩展器目录中，有一个名为 "smp_portal" 的文件。这是一个二进制 sysfs 属性文件，实现了 SMP portal（注意：这不是一个 SMP 端口），用户空间应用程序可以向其发送 SMP 请求并接收 SMP 响应。
功能看似简单：

1. 构建你想要发送的 SMP 帧。格式和布局在 SAS 规范中有描述。将 CRC 字段设为 0。
   ```c
   open(2)
   ```

2. 以读写模式打开扩展器的 SMP portal sysfs 文件。
   ```c
   write(2)
   ```

3. 写入你在步骤 1 中构建的帧。
   ```c
   read(2)
   ```

4. 读取你预期接收的数据量。
如果你收到的数据量与预期的不同，那么就发生了某种错误。
close(2)

所有这个过程在函数 do_smp_func() 及其调用者中详细展示，位于文件 "expander_conf.c" 中。
内核功能实现在文件 "sas_expander.c" 中。
程序 "expander_conf.c" 实现了这一点。它接受一个参数，即到扩展器的SMP端口的sysfs文件名，并提供扩展器信息，包括路由表。
SMP端口让你完全控制扩展器，所以请务必小心。
