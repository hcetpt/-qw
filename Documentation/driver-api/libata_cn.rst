========================
libATA 开发者指南
========================

:作者: Jeff Garzik

简介
============

libATA 是一个在 Linux 内核中使用的库，用于支持 ATA 主控制器和设备。libATA 提供了一个 ATA 驱动程序 API、适用于 ATA 和 ATAPI 设备的类传输，以及根据 T10 SAT 规范为 ATA 设备提供的 SCSI<->ATA 转换。
本指南记录了 libATA 驱动程序 API、库函数、库内部实现以及几个示例性的 ATA 低级驱动程序。

libata 驱动程序 API
==================

:c:type:`struct ata_port_operations <ata_port_operations>` 
为每个使用 libata 的低级硬件驱动程序定义，它控制低级驱动程序如何与 ATA 和 SCSI 层交互。
基于 FIS 的驱动程序将通过 `->qc_prep()` 和 `->qc_issue()` 高级挂钩接入系统。行为类似于 PCI IDE 硬件的设备可以利用一些通用的帮助程序，至少需要定义 ATA 阴影寄存器块的总线 I/O 地址。

:c:type:`struct ata_port_operations <ata_port_operations>`
--------------------------------------------------------------

标识后设备配置
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

```
void (*dev_config) (struct ata_port *, struct ata_device *);
```

在向每个找到的设备发出 IDENTIFY [PACKET] DEVICE 命令后调用。
通常用于在发出 SET FEATURES - XFER MODE 命令之前和操作之前应用特定于设备的修正。
此条目可以在 ata_port_operations 中指定为 NULL。

设置 PIO/DMA 模式
~~~~~~~~~~~~~~~~

```
void (*set_piomode) (struct ata_port *, struct ata_device *);
void (*set_dmamode) (struct ata_port *, struct ata_device *);
void (*post_set_mode) (struct ata_port *);
unsigned int (*mode_filter) (struct ata_port *, struct ata_device *, unsigned int);
```

在发出 SET FEATURES - XFER MODE 命令之前调用的挂钩。
可选的 `->mode_filter()` 挂钩会在 libata 构建可能模式掩码时被调用。这个掩码传递给 `->mode_filter()` 函数，该函数应该返回一个经过筛选的有效模式掩码，移除那些因硬件限制而不适合的模式。不可以通过此接口添加模式。

当 `->set_piomode()` 和 `->set_dmamode()` 被调用时，`dev->pio_mode` 和 `dev->dma_mode` 是有效的。此时，共享同一条电缆的任何其他驱动器的定时也会是有效的。也就是说，在尝试设置任何驱动器模式之前，库会记录通道上每个驱动器模式的决策。

`->post_set_mode()` 无条件调用，在 SET FEATURES - XFER MODE 命令成功完成之后。
``->set_piomode()`` 总是被调用（如果存在），但 ``->set_dma_mode()`` 仅在DMA可行时才被调用。

任务文件读写
~~~~~~~~~~~~~~

```
void (*sff_tf_load) (struct ata_port *ap, struct ata_taskfile *tf);
void (*sff_tf_read) (struct ata_port *ap, struct ata_taskfile *tf);
```

``->tf_load()`` 被用来将给定的任务文件加载到硬件寄存器/DMA缓冲区中。``->tf_read()`` 被用来读取硬件寄存器/DMA缓冲区，以获取当前的任务文件寄存器值集。大多数基于任务文件的硬件（PIO或MMIO）驱动程序使用函数 :c:func:`ata_sff_tf_load` 和 :c:func:`ata_sff_tf_read` 来实现这些钩子。

PIO数据读写
~~~~~~~~~~~~~~

```
void (*sff_data_xfer) (struct ata_device *, unsigned char *, unsigned int, int);
```

所有bmdma风格的驱动程序必须实现这个钩子。这是实际在PIO数据传输过程中复制数据字节的低级操作。通常驱动程序会选择 :c:func:`ata_sff_data_xfer` 或者 :c:func:`ata_sff_data_xfer32` 中的一个。

ATA命令执行
~~~~~~~~~~~~~~

```
void (*sff_exec_command)(struct ata_port *ap, struct ata_taskfile *tf);
```

使先前通过 ``->tf_load()`` 加载的ATA命令在硬件中开始执行。大多数基于任务文件的硬件驱动程序使用 :c:func:`ata_sff_exec_command` 来实现这个钩子。

每个命令的ATAPI DMA能力过滤器
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

```
int (*check_atapi_dma) (struct ata_queued_cmd *qc);
```

允许低级驱动程序过滤ATA包命令，并返回一个状态表示是否可以为提供的包命令使用DMA。
此钩子可以指定为NULL，在这种情况下，libata将假定支持atapi dma。

读取特定的ATA影子寄存器
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

```
u8   (*sff_check_status)(struct ata_port *ap);
u8   (*sff_check_altstatus)(struct ata_port *ap);
```

从硬件读取Status/AltStatus ATA影子寄存器。在某些硬件上，读取Status寄存器会附带清除中断条件的效果。大多数基于任务文件的硬件驱动程序使用 :c:func:`ata_sff_check_status` 来实现这个钩子。

写入特定的ATA影子寄存器
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

```
void (*sff_set_devctl)(struct ata_port *ap, u8 ctl);
```

将设备控制ATA影子寄存器写入硬件。大多数驱动程序不需要定义这个功能。

选择ATA总线上的设备
~~~~~~~~~~~~~~~~~~~~~~~~

```
void (*sff_dev_select)(struct ata_port *ap, unsigned int device);
```

发出使得N个硬件设备中的一个被认为“已选中”（活跃且可用）于ATA总线上的低级硬件命令。这在基于FIS的设备上通常没有意义。大多数基于任务文件的硬件驱动程序使用 :c:func:`ata_sff_dev_select` 来实现这个钩子。
### 私有调谐方法

```c
void (*set_mode) (struct ata_port *ap);
```

默认情况下，libata 根据 ATA 时序规则执行驱动器和控制器的调谐，并应用黑名单和电缆限制。某些控制器需要特殊处理并具有自定义调谐规则，通常是那些使用 ATA 命令但实际上不进行驱动器时序调整的 RAID 控制器。
**警告**

    此钩子不应用于替换控制器在存在异常情况下的标准调谐逻辑。在这种情况下替换默认调谐逻辑会绕过对于数据可靠性可能很重要的驱动器和桥接器异常处理。如果控制器需要筛选模式选择，则应使用 `mode_filter` 钩子。

### 控制 PCI IDE BMDMA 引擎

```c
void (*bmdma_setup) (struct ata_queued_cmd *qc);
void (*bmdma_start) (struct ata_queued_cmd *qc);
void (*bmdma_stop) (struct ata_port *ap);
u8   (*bmdma_status) (struct ata_port *ap);
```

在设置 IDE BMDMA 交易时，这些钩子启动 (`->bmdma_setup`)、触发 (`->bmdma_start`) 和停止 (`->bmdma_stop`) 硬件的 DMA 引擎。`->bmdma_status` 用于读取标准 PCI IDE DMA 状态寄存器。
在基于 FIS 的驱动程序中，这些钩子通常要么是空操作（no-ops），要么根本未实现。
大多数遗留 IDE 驱动程序使用 `ata_bmdma_setup` 函数作为 `bmdma_setup` 钩子。`ata_bmdma_setup` 将将指向 PRD 表的指针写入到 IDE PRD 表地址寄存器，启用 DMA 指令寄存器中的 DMA，并调用 `exec_command` 开始传输。
大多数遗留 IDE 驱动程序使用 `ata_bmdma_start` 函数作为 `bmdma_start` 钩子。`ata_bmdma_start` 将 ATA_DMA_START 标志写入到 DMA 指令寄存器。
许多遗留 IDE 驱动程序使用 `ata_bmdma_stop` 函数作为 `bmdma_stop` 钩子。`ata_bmdma_stop` 清除 DMA 指令寄存器中的 ATA_DMA_START 标志。
许多遗留 IDE 驱动程序使用 `ata_bmdma_status` 函数作为 `bmdma_status` 钩子。

### 高级任务文件钩子

```c
enum ata_completion_errors (*qc_prep) (struct ata_queued_cmd *qc);
int (*qc_issue) (struct ata_queued_cmd *qc);
```

更高级别的钩子，这两个钩子有可能取代上述一些任务文件/DMA 引擎钩子。`->qc_prep` 在缓冲区被 DMA 映射后被调用，通常用于填充硬件的 DMA 分散/聚集表。一些驱动程序使用标准的 `ata_bmdma_qc_prep` 和 `ata_bmdma_dumb_qc_prep` 辅助函数，但更先进的驱动程序则自行实现其功能。
``->qc_issue`` 用于在硬件和 S/G 表准备就绪后激活命令。IDE BMDMA 驱动程序使用辅助函数 :c:func:`ata_sff_qc_issue` 来基于任务文件协议进行调度。更高级的驱动程序会实现它们自己的 ``->qc_issue`` 方法。:c:func:`ata_sff_qc_issue` 会根据需要调用 ``->sff_tf_load()``、``->bmdma_setup()`` 和 ``->bmdma_start()`` 来启动传输。

### 异常与探测处理（EH）

```c
void (*freeze) (struct ata_port *ap);
void (*thaw) (struct ata_port *ap);
```

:c:func:`ata_port_freeze` 在HSM违规或其他条件破坏端口正常运行时被调用。一个冻结的端口不允许执行任何操作，直到端口解冻，这通常跟随一次成功的重置。

可选的 ``->freeze()`` 回调可以用于从硬件上冻结端口（例如，屏蔽中断并停止DMA引擎）。如果端口无法从硬件上冻结，则中断处理程序必须无条件地确认和清除中断，当端口处于冻结状态时。

可选的 ``->thaw()`` 回调用于执行与 ``->freeze()`` 相反的操作：重新准备端口以恢复正常的运行。解除中断屏蔽，启动DMA引擎等。

```c
void (*error_handler) (struct ata_port *ap);
```

``->error_handler()`` 是驱动程序对探测、热插拔、恢复和其他异常条件的挂钩。实现的主要责任是调用 :c:func:`ata_do_eh` 或 :c:func:`ata_bmdma_drive_eh`，并将一组EH钩子作为参数：

- 'prereset' 钩子（可以为NULL）在EH重置期间被调用，在采取任何其他动作之前。
- 'postreset' 钩子（可以为NULL）在执行EH重置之后被调用。根据现有条件、问题的严重性以及硬件能力，

- 要么 'softreset'（可以为NULL），要么 'hardreset'（可以为NULL）将被调用来执行低级别的EH重置。

```c
void (*post_internal_cmd) (struct ata_queued_cmd *qc);
```

在通过 :c:func:`ata_exec_internal` 执行探测时间或EH时间命令后，执行任何必要的硬件特定操作来完成处理。

### 硬件中断处理

```c
irqreturn_t (*irq_handler)(int, void *, struct pt_regs *);
void (*irq_clear) (struct ata_port *);
```

``->irq_handler`` 是由libata注册到系统中的中断处理例程。``->irq_clear`` 在探测期间、在中断处理程序注册之前被调用，以确保硬件处于静默状态。

第二个参数 `dev_instance` 应该被转换为指向 :c:type:`struct ata_host_set <ata_host_set>` 的指针。
大多数传统的IDE驱动程序使用:c:func:`ata_sff_interrupt`作为中断处理程序的钩子，该函数会扫描主机集中的所有端口，确定哪些挂起的命令处于活动状态（如果有的话），并调用 ata_sff_host_intr(ap,qc)。

大多数传统的IDE驱动程序使用:c:func:`ata_sff_irq_clear`作为:c:func:`irq_clear`的钩子，其仅仅清除DMA状态寄存器中的中断和错误标志。

### SATA PHY 读写

```
int (*scr_read) (struct ata_port *ap, unsigned int sc_reg,
             u32 *val);
int (*scr_write) (struct ata_port *ap, unsigned int sc_reg,
                       u32 val);
```

这些函数用于读取和写入标准的SATA PHY寄存器。`sc_reg`可以是SCR_STATUS、SCR_CONTROL、SCR_ERROR或SCR_ACTIVE之一。

### 初始化与关闭

```
int (*port_start) (struct ata_port *ap);
void (*port_stop) (struct ata_port *ap);
void (*host_stop) (struct ata_host_set *host_set);
```

`->port_start()`在每个端口的数据结构初始化后立即被调用。通常用于分配每个端口的DMA缓冲区/表/环，启用DMA引擎等类似任务。一些驱动程序还利用这个入口点来为`ap->private_data`分配私有内存。

许多驱动程序将:c:func:`ata_port_start`作为此钩子，或者从它们自己的:c:func:`port_start`钩子中调用它。:c:func:`ata_port_start`分配一个传统IDE PRD表的空间并返回。

`->port_stop()`在`->host_stop()`之后被调用。其唯一功能是释放不再使用的DMA/内存资源。许多驱动程序也在此时从端口释放私有数据。

`->host_stop()`在所有的`->port_stop()`调用完成后被调用。该钩子必须完成硬件关闭，释放DMA和其他资源等。此钩子可以指定为NULL，在这种情况下，它不会被调用。

### 错误处理

本章描述了libata下的错误处理方式。建议读者先阅读SCSI EH (Documentation/scsi/scsi_eh.rst) 和 ATA异常文档。
命令的起源
-------------------

在 libata 中，一个命令通过 `struct ata_queued_cmd <ata_queued_cmd>`（或简称 qc）来表示。
qc 在端口初始化时预先分配，并且重复用于命令执行。目前每个端口仅分配一个 qc，但尚未合并的 NCQ 分支为每个标签分配一个 qc，并将每个 qc 映射到 NCQ 标签实现一对一映射。
libata 的命令可以来源于两个地方 —— libata 本身和 SCSI 中间层。libata 内部命令用于初始化和错误处理。所有正常的块请求和用于 SCSI 模拟的命令都作为 SCSI 命令通过 SCSI 主机模板的 queuecommand 回调传递。

命令如何发出
-----------------------

内部命令
    分配好的 qc 的任务文件（taskfile）被初始化以执行特定的命令。qc 目前有两种机制来通知完成状态：一种是通过 `qc->complete_fn()` 回调函数，另一种是完成标志 `qc->waiting`。`qc->complete_fn()` 回调函数是常规 SCSI 转换命令使用的异步路径，而 `qc->waiting` 是内部命令使用的同步路径（发起者在进程上下文中睡眠）。
一旦初始化完成，就获取 host_set 锁并发出 qc。

SCSI 命令
    所有的 libata 驱动程序都使用 `ata_scsi_queuecmd` 作为 `hostt->queuecommand` 的回调函数。scmd 可以模拟也可以转换。处理模拟的 scmd 时不需要涉及 qc。结果会立即计算出来，然后完成 scmd。
`qc->complete_fn()` 回调函数用于完成通知。ATA 命令使用 `ata_scsi_qc_complete` 函数，而 ATAPI 命令使用 `atapi_qc_complete` 函数。这两个函数最终都会调用 `qc->scsidone` 来在 qc 完成时通知上层。转换完成后，使用 `ata_qc_issue` 函数发出 qc。
需要注意的是，SCSI 中间层在持有 host_set 锁的情况下调用 hostt->queuecommand，因此上述所有操作都在持有 host_set 锁的情况下进行。

命令如何处理
--------------------------

根据所使用的协议和控制器的不同，命令的处理方式也不同。为了讨论的目的，假设使用了任务文件接口和所有标准回调的控制器。
目前有六种 ATA 命令协议被使用。它们可以根据处理方式归类为以下四类：
### ATA 无数据或DMA
`ATA_PROT_NODATA` 和 `ATA_PROT_DMA` 属于此类。这些类型的命令一旦发出后不需要任何软件干预。设备会在完成时触发中断。

### ATA 程序输入输出（PIO）
`ATA_PROT_PIO` 属于此类别。目前libata通过轮询实现PIO。设置`ATA_NIEN`位以关闭中断，`pio_task`在`ata_wq`上执行轮询和I/O操作。

### ATAPI 无数据或DMA
`ATA_PROT_ATAPI_NODATA` 和 `ATA_PROT_ATAPI_DMA` 属于此类别。发出PACKET命令后使用`packet_task`来轮询BSY位。一旦设备关闭BSY，`packet_task`将CDB传输并交由中断处理程序继续处理。

### ATAPI PIO
`ATA_PROT_ATAPI` 属于此类别。设置`ATA_NIEN`位，并且像ATAPI 无数据或DMA一样，`packet_task`提交cdb。但是，在提交cdb之后，进一步的数据传输处理则交给`pio_task`。

### 命令如何完成
一旦发出，所有的队列元素(qc)要么通过函数`:c:func:`ata_qc_complete`完成，要么超时。对于由中断处理的命令，`:c:func:`ata_host_intr`调用`:c:func:`ata_qc_complete`；对于PIO任务，`pio_task`调用`:c:func:`ata_qc_complete`。在错误情况下，`packet_task`也可能完成命令。
函数`:c:func:`ata_qc_complete`执行以下操作：
1. 解映射DMA内存。
2. 清除`qc->flags`中的`ATA_QCFLAG_ACTIVE`标志。
3. 调用`qc->complete_fn`回调函数。如果该回调函数的返回值不为零，则跳过后续步骤，`:c:func:`ata_qc_complete`直接返回。
4. 调用`:c:func:`__ata_qc_complete`，它会：

   1. 将`qc->flags`清零。
2. `ap->active_tag` 和 `qc->tag` 被标记为无效
3. `qc->waiting` 被清除并完成（按此顺序）
4. 通过清除 `ap->qactive` 中的适当位来释放 qc
因此，这基本上通知了上层并释放了 qc。一个例外是第3点中的快捷路径，该路径被 :c:func:`atapi_qc_complete` 使用
对于所有非 ATAPI 命令，无论它们是否失败，几乎都采用相同的代码路径，并且很少进行错误处理。如果 qc 成功，则以成功状态完成；否则，则以失败状态完成。
然而，失败的 ATAPI 命令需要更多的处理，因为需要 REQUEST SENSE 来获取感应数据。如果一个 ATAPI 命令失败，
:c:func:`ata_qc_complete` 将被调用并带有错误状态，进而通过 `qc->complete_fn()` 回调调用 :c:func:`atapi_qc_complete`
这使得 :c:func:`atapi_qc_complete` 将 `scmd->result` 设置为 SAM_STAT_CHECK_CONDITION，完成 scmd 并返回 1。由于感应数据为空但 `scmd->result` 是 CHECK CONDITION，SCSI 中间层将为 scmd 调用 EH（错误处理），而返回 1 会使 :c:func:`ata_qc_complete` 在不释放 qc 的情况下返回。这导致我们进入部分完成的 qc 的 :c:func:`ata_scsi_error`
:c:func:`ata_scsi_error`
------------------------
:c:func:`ata_scsi_error` 是 libata 当前的 `transportt->eh_strategy_handler()`。如上所述，这将在两种情况下进入 - 超时和 ATAPI 错误完成。此函数将检查 qc 是否处于活动状态且尚未失败。这样的 qc 将被标记为 AC_ERR_TIMEOUT，以便 EH 稍后处理它。然后，它调用低级 libata 驱动程序的 :c:func:`error_handler` 回调
当 :c:func:`error_handler` 回调被调用时，它会停止 BMDMA 并完成 qc。请注意，由于我们现在处于 EH 中，我们不能调用 scsi_done。如 SCSI EH 文档中所述，已恢复的 scmd 应使用 :c:func:`scsi_queue_insert` 重试或使用 :c:func:`scsi_finish_command` 完成。在这里，我们将 `qc->scsidone` 替换为 :c:func:`scsi_finish_command` 并调用 :c:func:`ata_qc_complete`
如果因失败的 ATAPI qc 导致 EH 被调用，这里的 qc 已经完成但未被释放。这种半完成的目的在于利用 qc 作为占位符，使 EH 代码能够到达这里。这种方法有点取巧，但它有效。
一旦控制到达这里，通过显式调用 `__ata_qc_complete` 来释放 qc。然后，为 REQUEST SENSE 发出内部的 qc。一旦获取到感应数据，就直接通过在 scmd 上调用 `scsi_finish_command` 来完成 scmd。需要注意的是，因为我们已经完成了与 scmd 关联的 qc 的处理并将其释放了，所以我们不需要/不能再次调用 `ata_qc_complete`。

当前 EH 存在的问题
------------------

-  错误表示过于粗糙。目前所有错误状况都使用 ATA 状态和错误寄存器来表示。那些不是 ATA 设备错误的情况也被当作 ATA 设备错误来处理，即通过设置 ATA_ERR 位。需要一个更好的错误描述符来正确表示 ATA 和其他类型的错误/异常。
-  在处理超时问题时，没有采取任何措施使设备忘记已超时的命令，并准备好接收新的命令。
-  通过 `ata_scsi_error` 函数进行的 EH 处理没有得到适当的保护以避免常规命令处理的影响。在进入 EH 时，设备并非处于静止状态。超时命令可能随时成功或失败；pio_task 和 atapi_task 可能仍在运行。
-  错误恢复能力太弱。经常导致 HSM 不匹配错误和其他错误的设备/控制器通常需要重置才能回到已知状态。此外，为了支持如 NCQ 和热插拔等功能，需要更高级的错误处理。
-  ATA 错误直接在中断处理程序中处理，而 PIO 错误则在 pio_task 中处理。这对于高级错误处理来说存在问题：
首先，高级错误处理往往需要上下文信息以及内部 qc 的执行。
其次，即使是一个简单的故障（比如 CRC 错误）也需要收集信息，并可能触发复杂的错误处理流程（例如，重置和重新配置）。有多条代码路径用于收集信息、进入 EH 并触发操作，这会带来很大的复杂度。
第三，分散的错误处理（EH）代码使得实现低级驱动程序变得困难。低级驱动程序会覆盖libata的回调函数。如果错误处理分散在多个地方，则每个受影响的回调函数都应该执行其部分的错误处理工作。这可能会导致错误频发并且实施起来十分痛苦。

libata 库
==========

.. kernel-doc:: drivers/ata/libata-core.c
   :export:

libata 核心内部结构
====================

.. kernel-doc:: drivers/ata/libata-core.c
   :internal:

.. kernel-doc:: drivers/ata/libata-eh.c

libata SCSI 转换/仿真
======================

.. kernel-doc:: drivers/ata/libata-scsi.c
   :export:

.. kernel-doc:: drivers/ata/libata-scsi.c
   :internal:

ATA 错误与异常
===============

本章试图识别对于ATA/ATAPI设备存在的错误/异常情况，并以一种与实现无关的方式描述如何处理这些情况。
术语“错误”用来描述设备报告了明确的错误条件或命令超时的情况。
术语“异常”通常用来描述非错误的特殊状况（例如，电源或热插拔事件），或者同时描述错误和非错误的特殊状况。当需要明确区分错误和异常时，使用术语“非错误异常”。

异常类别
----------

异常主要根据传统的任务文件+总线主IDE接口进行描述。如果控制器提供了更好的错误报告机制，将其映射到下面描述的类别中应该不会太难。
在接下来的部分中，提到了两种恢复操作：重置和重新配置传输方式。这些将在 `EH恢复操作 <#exrec>`__ 中进一步说明。

HSM 违规
~~~~~~~~

当在发送或执行任何ATA/ATAPI命令期间，状态值不符合HSM的要求时，会出现此错误。
-  在尝试发送命令时，ATA_STATUS不包含!BSY && DRDY && !DRQ
-  在PIO数据传输过程中，出现!BSY && !DRQ
-  在命令完成时出现DRQ
在CDB传输开始但还未传输完CDB的最后一个字节时出现 !BSY && ERR。ATA/ATAPI标准在PACKET命令的错误输出描述中指出，“在命令包的最后一个字节被写入之前，设备不应以错误终止PACKET命令”，并且状态图中并未包括这样的转换。
在这种情况下，HSM（主机状态机）被违反，并且从STATUS或ERROR寄存器中无法获取关于错误的更多信息。换句话说，这种错误可能是驱动程序错误、设备故障、控制器和/或电缆问题等。由于HSM被违反，需要进行重置来恢复已知的状态。另外，为传输配置较低的速度也可能有所帮助，因为有时传输错误会导致这类错误。
ATA/ATAPI设备错误（非NCQ / 非CHECK CONDITION）
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

这些是由ATA/ATAPI设备检测并报告的错误，表明存在设备问题。对于这类错误，STATUS和ERROR寄存器的值是有效的，并描述了错误情况。需要注意的是，某些ATA总线错误也会由ATA/ATAPI设备检测到，并使用与设备错误相同的机制进行报告。这部分情况将在本节稍后部分详细描述。
对于ATA命令，这类错误在命令执行期间及完成时通过!BSY && ERR指示。
对于ATAPI命令，

-  如果在发出PACKET后立即出现 !BSY && ERR && ABRT，则表示设备不支持PACKET命令，属于此类错误；
-  如果在传输完CDB的最后一个字节之后出现 !BSY && ERR(==CHK) && !ABRT，则表示CHECK CONDITION，不属于此类错误；
-  如果在传输完CDB的最后一个字节之后出现 !BSY && ERR(==CHK) && ABRT，则*可能*表示CHECK CONDITION，不属于此类错误。
对于上述检测到的错误，以下情况并非ATA/ATAPI设备错误，而是ATA总线错误，应根据`ATA总线错误 <#excatATAbusErr>`__进行处理。
数据传输期间出现CRC错误  
    这通过ERROR寄存器中的ICRC位表示，意味着在数据传输过程中发生了损坏。直到ATA/ATAPI-7标准，规定该位仅适用于UDMA传输，但ATA/ATAPI-8草案修订版1f指出该位也可能适用于多字DMA和PIO传输。
数据传输期间或完成后出现ABRT错误  
    直到ATA/ATAPI-7，标准规定ABRT可能在ICRC错误或设备无法完成命令的情况下被设置。结合MWDMA和PIO传输错误不允许使用ICRC位的规定（直到ATA/ATAPI-7），这似乎意味着单独的ABRT位可以指示传输错误。
然而，ATA/ATAPI-8草案修订版1f删除了ICRC错误可以触发ABRT的部分。因此，这是一个模糊地带。这里需要一些启发式方法。
ATA/ATAPI设备错误可以进一步分类如下：
介质错误  
    这通过ERROR寄存器中的UNC位表示。ATA设备只有在多次重试仍无法恢复数据后才会报告UNC错误，因此除了通知上层外没有其他可做的。
读取和写入命令会报告首次失败扇区的CHS或LBA，但ATA/ATAPI标准规定，在完成错误时已传输的数据量是不确定的，所以我们不能假设失败扇区之前的扇区已被传输，因此不能像SCSI那样成功完成这些扇区。
介质更换/请求介质更换错误  
    <<待办事项：此处填写>>
地址错误  
    这通过ERROR寄存器中的IDNF位表示。上报给上层。
其他错误  
    这可能是由ABRT ERROR位指示的无效命令或参数或其他某种错误条件。需要注意的是，ABRT位可以指示很多种情况，包括ICRC和地址错误。需要启发式方法。
根据不同的命令，并非所有的STATUS/ERROR位都适用。这些不适用的位在输出描述中标记为“na”，但直到ATA/ATAPI-7并没有定义“na”的含义。然而，ATA/ATAPI-8草案修订版1f对“N/A”做了如下描述：
3.2.3.3a N/A  
        一个关键词，表明在此标准中字段没有定义值，主机或设备不应检查。N/A字段应清除为零。
因此，可以合理地假设“na”位被设备清零，因此不需要明确的屏蔽。
ATAPI 设备 CHECK CONDITION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ATAPI 设备 CHECK CONDITION 错误通过在 PACKET 命令最后一个 CDB 字节传输后 STATUS 寄存器中设置的 CHK 位（ERR 位）来指示。对于这类错误，应获取感知数据以收集有关错误的信息。应当使用 REQUEST SENSE 命令包来获取感知数据。
一旦获取了感知数据，这种类型的错误就可以像处理其他 SCSI 错误一样处理。需要注意的是，感知数据可能会指示 ATA 总线错误（例如：Sense Key 04h 硬件错误 && ASC/ASCQ 47h/00h SCSI 奇偶校验错误）。在这种情况下，应将此错误视为 ATA 总线错误，并根据 `ATA 总线错误 <#excatATAbusErr>`__ 进行处理。
ATA 设备错误 (NCQ)
~~~~~~~~~~~~~~~~~~~~~~

NCQ 命令错误在 NCQ 命令阶段通过清除 BSY 和设置 ERR 位来指示（有一个或多个 NCQ 命令未完成）。尽管 STATUS 和 ERROR 寄存器将包含描述错误的有效值，但需要使用 READ LOG EXT 来清除错误状态、确定哪个命令失败并获取更多信息。
READ LOG EXT 的日志页 10h 报告了哪个标签失败以及描述错误的任务文件寄存器值。有了这些信息，可以像处理 `ATA/ATAPI 设备错误 (非-NCQ / 非-CHECK CONDITION) <#excatDevErr>`__ 中那样处理失败的命令，并且所有其他正在执行中的命令都必须重试。需要注意的是，这种重试不应该计入——很可能这些重试的命令如果没有遇到失败的命令本来会正常完成。
需要注意的是，ATA 总线错误可能报告为 ATA 设备 NCQ 错误。这种情况应按照 `ATA 总线错误 <#excatATAbusErr>`__ 描述的方式进行处理。
如果 READ LOG EXT 日志页 10h 失败或报告 NQ，则情况十分严重。这种情况应该根据 `HSM 违规 <#excatHSMviolation>`__ 进行处理。
ATA 总线错误
~~~~~~~~~~~~~

ATA 总线错误意味着在通过 ATA 总线（SATA 或 PATA）传输期间发生了数据损坏。此类错误可以通过以下方式指示：

-  ICRC 或 ABRT 错误，如 `ATA/ATAPI 设备错误 (非-NCQ / 非-CHECK CONDITION) <#excatDevErr>`__ 所述；
-  控制器特定的错误完成，并带有指示传输错误的错误信息；
-  在某些控制器上，命令超时。在这种情况下，可能存在一种机制来确定超时是由传输错误引起的。
未知/随机错误、超时及各种异常情况

如上所述，传输错误可能导致一系列症状，从设备ICRC错误到随机设备锁定，在许多情况下，无法判断错误状况是否由传输错误引起；因此，在处理错误和超时时采用某种启发式方法是必要的。例如，对于已知支持的命令反复出现ABRT错误很可能表明存在ATA总线错误。
一旦确定可能发生了ATA总线错误，降低ATA总线传输速度是可能缓解问题的一种措施。更多信息请参阅《重新配置传输 <#exrecReconf>`__》。

PCI总线错误
~~~~~~~~~~~~~

在通过PCI（或其他系统总线）进行传输时发生的数据损坏或其他故障。对于标准BMDMA，这通过BMDMA状态寄存器中的错误位来指示。这种类型的错误必须被记录下来，因为它表明系统出现了严重的问题。建议重置主机控制器。

延迟完成
~~~~~~~~~~~~~~~

当发生超时且超时处理器发现超时的命令已经成功完成或带有错误完成时就会发生这种情况。这通常是由于丢失中断引起的。这种类型的错误必须被记录下来。建议重置主机控制器。

未知错误（超时）
~~~~~~~~~~~~~~~~~~~~~~~

这是指当超时发生而命令仍在处理中或主机与设备处于未知状态的情况。在这种情况下，HSM可能处于任何有效或无效的状态。为了将设备恢复到已知状态并使其忘记超时的命令，有必要进行重置。可以尝试重新执行超时的命令。
超时也可能由传输错误引起。更多详细信息请参阅《ATA总线错误 <#excatATAbusErr>`__》。

热插拔和电源管理异常
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
<<待办事项：此处填写>>

EH恢复行动
---------------

本节讨论了几种重要的恢复行动。
清除错误条件
~~~~~~~~~~~~~~~~~~~~~~~~

许多控制器需要其错误寄存器由错误处理器清除。不同的控制器可能有不同的要求。
对于SATA，强烈建议在错误处理期间至少清除SError寄存器。

重置
~~~~~

在错误处理（EH）期间，以下情况下需要进行重置：
- HSM处于未知或无效状态
- HBA处于未知或无效状态
- EH需要让HBA/设备忘记正在执行中的命令
- HBA/设备行为异常

无论错误条件如何，在EH期间进行重置可能都是个好主意，以提高EH的稳健性。是否重置HBA和/或设备取决于具体情况，但推荐采用以下方案：
- 当已知HBA处于就绪状态而ATA/ATAPI设备处于未知状态时，仅重置设备
- 如果HBA处于未知状态，则同时重置HBA和设备
HBA的重置是特定于实现的。对于符合任务文件/BMDMA PCI IDE标准的控制器而言，如果BMDMA状态是唯一的HBA上下文，则停止活动的DMA事务可能是足够的。但是，即使是大部分符合任务文件/BMDMA PCI IDE标准的控制器也可能有特定于实现的要求和机制来重置自己。这必须由特定驱动程序解决。
另一方面，ATA/ATAPI标准详细描述了重置ATA/ATAPI设备的方法。
PATA硬件重置
    这是由硬件发起的设备重置，通过激活PATA的RESET-信号来指示。虽然没有标准方法从软件启动硬件重置，但某些硬件提供了允许驱动程序直接调整RESET-信号的寄存器。
软件重置
    这是通过将CONTROL SRST位设置为至少5微秒的时间来实现的。
PATA和SATA都支持它，但在SATA的情况下，这可能需要特定于控制器的支持，因为在BSY位仍然设置的情况下，应该发送第二个注册FIS来清除SRST。请注意，在PATA上，这会重置通道上的主设备和从设备。
执行设备诊断命令
尽管ATA/ATAPI标准没有明确描述，但EDD（设备诊断命令）隐含了一定程度的重置操作，可能与软件重置的级别类似。
主机端的EDD协议可以通过常规命令处理来实现，大多数SATA控制器应该能够像处理其他命令一样处理EDD。
如同软件重置一样，EDD会影响PATA总线上的两个设备。
虽然EDD确实会对设备进行重置，但这并不适合用于错误处理，因为当BSY标志位被设置时无法发出EDD命令，并且当设备处于未知或异常状态时其行为也不明确。
ATAPI设备重置命令
这与软件重置非常相似，只是重置可以仅限于选定的设备而不影响共享同一电缆的其他设备。
SATA物理重置
这是重置SATA设备的首选方式。实际上，它与PATA硬件重置相同。值得注意的是，这可以通过标准的SCR控制寄存器来完成。因此，通常比软件重置更容易实现。
在重置设备时需要考虑的一点是，重置会清除某些配置参数，这些参数需要在重置后恢复为之前的或新调整的值。
受影响的参数包括：
- 通过INITIALIZE DEVICE PARAMETERS（很少使用）设置的CHS
- 通过SET FEATURES（包括传输模式设置）设置的参数
- 通过SET MULTIPLE MODE设置的块计数
- 其他参数（SET MAX, MEDIA LOCK...）

ATA/ATAPI标准规定了在硬件或软件重置期间某些参数必须保持不变，但并没有严格指定所有参数。为了确保系统的稳定性，在重置后重新配置所需的参数是必要的。需要注意的是，这也适用于从深度睡眠（关机）状态恢复的情况。
此外，ATA/ATAPI标准要求在更新任何配置参数或进行硬件重置之后发出IDENTIFY DEVICE / IDENTIFY PACKET DEVICE命令，并利用其结果进行后续操作。操作系统驱动程序需要实现重新验证机制以支持这一点。
重新配置传输
对于PATA和SATA而言，为了降低成本，很多连接器、电缆或控制器都做了大量的简化处理，因此出现高传输错误率的情况很常见。这可以通过降低传输速度来缓解。
以下是Jeff Garzik提出的一个可能方案：
如果在15分钟内发生超过N次（可能是3次？）的传输错误，

    - 如果是SATA，则降低SATA PHY的速度。如果速度已无法降低，

    - 则降低UDMA传输速度。如果已经在UDMA0模式，切换到PIO4模式，

    - 降低PIO传输速度。如果已经是PIO3模式，发出警告但继续运行

ATA_PIIX 内部结构
==================

.. kernel-doc:: drivers/ata/ata_piix.c
   :internal:

SATA_SIL 内部结构
==================

.. kernel-doc:: drivers/ata/sata_sil.c
   :internal:

致谢
======

大量的ATA知识得益于与Andre Hedrick（www.linux-ide.org）长时间的交流讨论，以及对ATA和SCSI规范长时间的研究。
感谢Alan Cox指出了SATA与SCSI之间的相似之处，并且总体上激发了我对libata进行改进的动力。
libata中的设备检测方法（ata_pio_devchk）及早期的探测过程都是基于对Hale Landis在其ATADRVR驱动程序（www.ata-atapi.com）中的探测/重置代码进行了深入研究的基础上实现的。
