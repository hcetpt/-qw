SPDX 许可证标识符: GPL-2.0

=======
SCSI 错误处理 (EH)
=======

本文档描述了 SCSI 中间层的错误处理架构。关于 SCSI 中间层的更多信息，请参阅 `Documentation/scsi/scsi_mid_low_api.rst`。
.. 目录

   [1] SCSI 命令如何通过中间层并到达 EH
       [1-1] struct scsi_cmnd
       [1-2] scmd 如何完成？
       [1-2-1] 使用 scsi_done 完成 scmd
       [1-2-2] 使用超时完成 scmd
       [1-3] EH 如何接管
   [2] SCSI EH 的工作原理
       [2-1] 通过细粒度回调的 EH
       [2-1-1] 概述
       [2-1-2] scmd 通过 EH 的流程
       [2-1-3] 控制流
       [2-2] 通过 transport->eh_strategy_handler() 的 EH
       [2-2-1] 在调用 transport->eh_strategy_handler() 之前的 SCSI 中间层条件
       [2-2-2] 调用 transport->eh_strategy_handler() 之后的 SCSI 中间层条件
       [2-2-3] 需要考虑的问题

1. SCSI 命令如何通过中间层并到达 EH
==========================================================

1.1 struct scsi_cmnd
--------------------

每个 SCSI 命令都由 struct scsi_cmnd（简称 scmd）表示。一个 scmd 包含两个 `list_head`，用于将自身链接到列表中。这两个是 `scmd->list` 和 `scmd->eh_entry`。前者用于空闲列表或按设备分配的 scmd 列表，在此 EH 讨论中不太相关。后者用于完成和 EH 列表，除非另有说明，在此讨论中 scmd 总是使用 `scmd->eh_entry` 进行链接。

1.2 scmd 如何完成？
--------------------------------

一旦低级驱动程序 (LLDD) 获取了一个 scmd，LLDD 会通过调用从中间层传递的 `scsi_done` 回调函数来完成该命令，或者块层会将其超时。

1.2.1 使用 scsi_done 完成 scmd
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

对于所有非 EH 命令，`scsi_done()` 是完成回调。它只是调用 `blk_complete_request()` 来删除块层定时器并触发 SCSI_SOFTIRQ。

SCSI_SOFTIRQ 处理器 `scsi_softirq` 调用 `scsi_decide_disposition()` 来确定如何处理该命令。`scsi_decide_disposition()` 根据 `scmd->result` 值和感觉数据来确定如何处理该命令：
- 成功 (SUCCESS)

    调用 `scsi_finish_command()` 来处理该命令。该函数执行一些维护任务，然后调用 `scsi_io_completion()` 来完成 I/O。
    `scsi_io_completion()` 通过调用 `blk_end_request` 及其相关函数来通知块层已完成请求，或者在出现错误时确定如何处理剩余的数据。

- 需要重试 (NEEDS_RETRY)

    - 添加到 ML 队列 (ADD_TO_MLQUEUE)

        将 scmd 重新排队到块队列。
- 否则

    调用 `scsi_eh_scmd_add(scmd)` 来处理该命令。详见 [1-3] 了解该函数的详细信息。

1.2.2 使用超时完成 scmd
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

超时处理器为 `scsi_timeout()`。当发生超时时，此函数：

1. 调用可选的 `hostt->eh_timed_out()` 回调函数。返回值可以是：

    - SCSI_EH_RESET_TIMER

        表示需要更多时间来完成命令。定时器被重新启动
### SCSI_EH_NOT_HANDLED
`eh_timed_out()` 回调未处理该命令  
执行步骤 #2  

### SCSI_EH_DONE
`eh_timed_out()` 完成了该命令  

2. 调用 `scsi_abort_command()` 来安排一个异步中止，可能会重试 `scmd->allowed + 1` 次。对于设置了 `SCSI_EH_ABORT_SCHEDULED` 标志的命令（这表明命令已经被中止过一次，并且这是失败的重试），当超过重试次数或 EH 截止时间到期时，执行步骤 #3。

3. 对于该命令，调用 `scsi_eh_scmd_add(scmd, SCSI_EH_CANCEL_CMD)`。详见 [1-4]

#### 1.3 异步命令中止
-------------------

超时发生后，从 `scsi_abort_command()` 中安排命令中止。如果中止成功，命令将被重试（如果重试次数未耗尽）或以 `DID_TIME_OUT` 终止。否则，调用 `scsi_eh_scmd_add()` 处理该命令。详见 [1-4]

#### 1.4 EH 如何接管
---------------------

scmd 通过 `scsi_eh_scmd_add()` 进入 EH，具体如下：
1. 将 `scmd->eh_entry` 链接到 `shost->eh_cmd_q`
2. 设置 `shost->shost_state` 中的 `SHOST_RECOVERY` 位
3. 增加 `shost->host_failed`
4. 如果 `shost->host_busy == shost->host_failed`，唤醒 SCSI EH 线程

如上所示，一旦任何 scmd 被添加到 `shost->eh_cmd_q`，`SHOST_RECOVERY` 位就会被设置。这会阻止任何新的 scmd 从块队列发送到主机；最终，所有主机上的 scmd 要么正常完成，要么失败并被添加到 `eh_cmd_q`，要么超时并被添加到 `shost->eh_cmd_q`。
如果所有 `scmd` 要么完成要么失败，那么在飞行中的 `scmd` 数量将等于失败的 `scmd` 数量，即 `shost->host_busy == shost->host_failed`。这会唤醒 SCSI EH 线程。因此，一旦被唤醒，SCSI EH 线程可以预期所有在飞行中的命令都已失败，并且这些命令已链接到 `shost->eh_cmd_q` 上。

需要注意的是，这并不意味着较低层已经处于静止状态。如果一个低层驱动（LLDD）以错误状态完成了某个 `scmd`，则假设该 `scmd` 已经被 LLDD 和较低层忘记。然而，如果某个 `scmd` 超时了，除非 `host->eh_timed_out()` 使较低层忘记了该 `scmd`（目前没有 LLDD 这样做），只要从较低层的角度来看，该命令仍然处于活动状态，并且随时可能完成。当然，由于定时器已经超时，所有这样的完成都将被忽略。

我们将在后面讨论 SCSI EH 如何采取行动来中止（让 LLDD 忘记）超时的 `scmd`。

2. SCSI EH 的工作原理
======================

LLDD 可以通过以下两种方式之一实现 SCSI EH 行动：

- 细粒度 EH 回调
  LLDD 可以实现细粒度 EH 回调，让 SCSI 中间层驱动错误处理并调用适当的回调。
  这将在 [2-1] 中进一步讨论。

- `eh_strategy_handler()` 回调
  这是一个大的回调函数，应该执行整个错误处理过程。因此，它应该完成 SCSI 中间层在恢复期间所做的所有任务。
  这将在 [2-2] 中讨论。

一旦恢复完成，SCSI EH 通过调用 `scsi_restart_operations()` 恢复正常操作，具体步骤如下：

1. 检查是否需要锁定门并锁定门。
2. 清除 `SHOST_RECOVERY` 标志位。
3. 唤醒 `shost->host_wait` 上的等待者。这发生在有人对该主机调用 `scsi_block_when_processing_errors()` 时。
   （*问题*：为什么需要这样做？所有操作在到达块队列后都会被阻止。）
4. 刷新主机上所有设备的队列。

2.1 通过细粒度回调实现 EH
-------------------------------

2.1.1 概览
^^^^^^^^^^^^^^

如果不存在 `eh_strategy_handler()`，SCSI 中间层将负责驱动错误处理。EH 的目标有两个：一是让 LLDD、主机和设备忘记超时的 `scmd`；二是让它们准备好接收新的命令。当一个 `scmd` 被较低层忘记，并且较低层准备好再次处理或失败该 `scmd` 时，该 `scmd` 就被认为已恢复。
为了实现这些目标，EH（错误处理）执行一系列逐步加重的恢复操作。一些操作通过发出SCSI命令来完成，而其他操作则通过调用以下细粒度的主机EH回调函数来完成。可以省略某些回调，并且省略的回调被认为总是失败：

    int (* eh_abort_handler)(struct scsi_cmnd *);
    int (* eh_device_reset_handler)(struct scsi_cmnd *);
    int (* eh_bus_reset_handler)(struct scsi_cmnd *);
    int (* eh_host_reset_handler)(struct scsi_cmnd *);

只有当较低严重级别的操作无法恢复某些失败的scmd时，才会采取较高严重级别的操作。请注意，最高严重级别操作的失败意味着EH失败，并会导致所有未恢复设备的离线。

在恢复过程中，遵循以下规则：

- 恢复操作会在待处理列表eh_work_q上的失败scmd上执行。如果某个scmd的恢复操作成功，则该scmd将从eh_work_q中移除。
- 单个scmd的恢复操作可能会恢复多个scmd。例如，重置一个设备会恢复该设备上的所有失败scmd。
- 只有在较低严重级别的操作完成后eh_work_q仍然不为空时，才会采取较高严重级别的操作。
- EH会重用失败的scmd来发出恢复命令。对于超时的scmd，SCSI EH确保LLDD在重新使用scmd之前忘记它。
- 当scmd恢复后，使用scsi_eh_finish_cmd()将其从eh_work_q移动到EH本地的eh_done_q。在所有scmd都恢复后（eh_work_q为空），调用scsi_eh_flush_done_q()来重试或结束恢复的scmd（通知上层失败）。
- scmd仅在以下情况下重试：其sdev仍在线（未离线），未设置REQ_FAILFAST，并且++scmd->retries小于scmd->allowed。

### 2.1.2 SCMD通过EH的流程
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. 错误完成/超时

    :ACTION: 调用scsi_eh_scmd_add()处理scmd
    
        - 将scmd添加到shost->eh_cmd_q
        - 设置SHOST_RECOVERY
        - shost->host_failed++
    
    :LOCKING: shost->host_lock

2. EH启动

    :ACTION: 将所有scmd移到EH的本地eh_work_q。清空shost->eh_cmd_q
    
    :LOCKING: shost->host_lock（并非严格必要，只是为了保持一致性）

3. scmd恢复

    :ACTION: 调用scsi_eh_finish_cmd()完成scmd
    
        - 调用scsi_setup_cmd_retry()
        - 从本地eh_work_q移到本地eh_done_q
    
    :LOCKING: 无
    
    :CONCURRENCY: 每个独立的eh_work_q最多有一个线程以保持队列操作无锁

4. EH完成

    :ACTION: 调用scsi_eh_flush_done_q()重试scmd或通知上层失败。可能并发调用，但每个独立的eh_work_q最多有一个线程以保持队列操作无锁
    
        - scmd从eh_done_q移除并清除scmd->eh_entry
        - 如果需要重试，使用scsi_queue_insert()重新排队
        - 否则，调用scsi_finish_command()处理scmd
        - 清零shost->host_failed
    
    :LOCKING: 队列或完成函数执行适当的锁定

### 2.1.3 控制流
^^^^^^^^^^^^^^^^^^^^^^

细粒度的EH回调从scsi_unjam_host()开始。
``scsi_unjam_host``

1. 锁定 `shost->host_lock`，将 `shost->eh_cmd_q` 初始化并链接到本地 `eh_work_q`，然后解锁 `host_lock`。注意，此操作会清空 `shost->eh_cmd_q`。
2. 调用 `scsi_eh_get_sense`

`scsi_eh_get_sense`

对于每个没有有效状态数据的错误完成命令（!SCSI_EH_CANCEL_CMD），执行此操作。大多数 SCSI 传输层/LLDD 在命令失败时自动获取状态数据（自动获取状态）。出于性能原因以及为了避免在发生 CHECK CONDITION 和此操作之间状态信息不同步，推荐使用自动获取状态。
注意，如果未支持自动获取状态，在错误完成 `scmd` 时，`scmd->sense_buffer` 中包含无效的状态数据。在这种情况下，`scsi_decide_disposition()` 总是返回 FAILED，从而调用 SCSI EH。当 `scmd` 到达这里时，获取状态数据，并再次调用 `scsi_decide_disposition()`。
1. 调用 `scsi_request_sense()` 发送 REQUEST_SENSE 命令。如果失败，则不采取任何操作。注意，不采取任何操作会导致对 `scmd` 进行更严重的恢复。
2. 对 `scmd` 调用 `scsi_decide_disposition()`

   - SUCCESS
     将 `scmd->retries` 设置为 `scmd->allowed`，防止 `scsi_eh_flush_done_q()` 重试 `scmd`，并调用 `scsi_eh_finish_cmd()`
   - NEEDS_RETRY
     调用 `scsi_eh_finish_cmd()`
   - 否则
     不采取任何操作
3. 如果 `!list_empty(&eh_work_q)`，调用 `scsi_eh_abort_cmds`

`scsi_eh_abort_cmds`

当主机模板中启用了 no_async_abort 时，对于每个超时命令执行此操作。
对于每个 `scmd` 调用 `hostt->eh_abort_handler()`。如果成功使 LLDD 及所有相关硬件忘记 `scmd`，则该处理程序返回 SUCCESS。
如果超时的scmd成功中止，并且sdev处于离线或就绪状态，则会调用`scsi_eh_finish_cmd()`来处理该scmd。否则，scmd将保留在eh_work_q中以进行更高级别的处理。

请注意，无论是离线还是就绪状态都意味着sdev已经准备好处理新的scmd，其中处理也包括立即失败；因此，如果sdev处于这两种状态之一，则无需进一步的恢复操作。

设备的就绪状态通过`scsi_eh_tur()`进行测试，该函数会发出TEST_UNIT_READY命令。请注意，在重用scmd进行TEST_UNIT_READY之前，必须先成功中止scmd。

4. 如果`!list_empty(&eh_work_q)`，则调用`scsi_eh_ready_devs()`。

    `scsi_eh_ready_devs`

    此函数采取四种越来越严重的措施使故障的sdev准备好接收新命令。
    
1. 调用`scsi_eh_stu()`
    
    `scsi_eh_stu`
    
        对于每个有失败scmd（具有有效sense数据）且scsi_check_sense()判定为FAILED的sdev，发出START_STOP_UNIT命令，start=1。请注意，由于我们明确选择了已完成错误的scmd，已知较低层已忘记该scmd，因此可以重用它来进行STU。
        
        如果STU成功并且sdev处于离线或就绪状态，则使用`scsi_eh_finish_cmd()`完成sdev上的所有失败scmd。
        
        *注意* 如果hostt->eh_abort_handler()未实现或失败，此时我们可能仍然有超时的scmd，并且STU不会让较低层忘记这些scmd。然而，此函数在STU成功后会完成sdev上的所有scmd，导致较低层处于不一致状态。看来只有当sdev没有超时scmd时才应采取STU操作。
        
2. 如果`!list_empty(&eh_work_q)`，则调用`scsi_eh_bus_device_reset()`
    
    `scsi_eh_bus_device_reset`
    
        此操作与`scsi_eh_stu()`非常相似，不同之处在于不是发出STU，而是使用hostt->eh_device_reset_handler()。此外，由于我们没有发出SCSI命令，并且重置会清除sdev上的所有scmd，因此无需选择已完成错误的scmd。
        
3. 如果`!list_empty(&eh_work_q)`，则调用`scsi_eh_bus_reset()`
    
    `scsi_eh_bus_reset`
    
        对于每个存在失败scmd的通道，调用hostt->eh_bus_reset_handler()。如果总线重置成功，则完成通道上所有就绪或离线sdev上的失败scmd。
4. 如果 `!list_empty(&eh_work_q)`，调用 `scsi_eh_host_reset()`

    ``scsi_eh_host_reset``
    
        这是最后的手段。调用 `host->eh_host_reset_handler()`。如果主机重置成功，则在该主机上所有已准备好或离线的 `sdev` 上的所有失败的 `scmd` 都会被 EH 完成。

5. 如果 `!list_empty(&eh_work_q)`，调用 `scsi_eh_offline_sdevs()`

    ``scsi_eh_offline_sdevs``
    
        将所有仍有未恢复 `scmd` 的 `sdev` 设置为离线状态，并将这些 `scmd` EH 完成。
    
5. 调用 `scsi_eh_flush_done_q()`
    
    ``scsi_eh_flush_done_q``
    
        此时所有 `scmd` 已经被恢复（或放弃）并由 `scsi_eh_finish_cmd()` 放到 `eh_done_q` 中。此函数通过重试或通知上层来清除 `eh_done_q` 中的 `scmd` 失败情况。

2.2 通过 `transport->eh_strategy_handler()` 进行 EH 处理
-------------------------------------------------------------

在 `scsi_unjam_host()` 的位置调用 `transport->eh_strategy_handler()`，它负责整个恢复过程。处理完成后，处理器应使下层忘记所有失败的 `scmd` 并准备好接收新命令或设置为离线状态。同时，它还应执行 SCSI EH 维护任务以保持 SCSI 中间层的完整性。换句话说，在 [2-1-2] 中描述的步骤中，除了第 1 步之外，其余步骤都应由 `eh_strategy_handler()` 实现。

2.2.1 在调用 `transport->eh_strategy_handler()` 前的 SCSI 中间层条件
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

进入处理器时，以下条件为真：
- 每个失败的 `scmd` 的 `eh_flags` 字段已适当设置。
- 每个失败的 `scmd` 通过 `scmd->eh_entry` 链接到 `scmd->eh_cmd_q`。
- `SHOST_RECOVERY` 标志已设置。
### 翻译结果

#### 2.2.2 `post transport->eh_strategy_handler()` SCSI 中间层条件
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在处理程序退出时，必须满足以下条件：
- `shost->host_failed` 为零
- 每个 `scmd` 处于这样的状态：对 `scmd` 调用 `scsi_setup_cmd_retry()` 不会产生任何影响
- `shost->eh_cmd_q` 已被清除
- 每个 `scmd->eh_entry` 已被清除
- 对每个 `scmd` 调用了 `scsi_queue_insert()` 或 `scsi_finish_command()`。注意，处理程序可以自由使用 `scmd->retries` 来限制重试次数

#### 2.2.3 需要考虑的事项
^^^^^^^^^^^^^^^^^^^^^^^^

- 注意超时的 `scmd` 在较低层仍然处于活动状态。在对这些 `scmd` 进行其他操作之前，让较低层忘记它们
- 为了保持一致性，在访问或修改 `shost` 数据结构时，获取 `shost->host_lock`
- 在完成时，每个失败的 `sdev` 必须已经忘记了所有活跃的 `scmd`
- 在完成时，每个失败的 `sdev` 必须准备好接受新的命令或下线
Tejun Heo
htejun@gmail.com

2005年9月11日
