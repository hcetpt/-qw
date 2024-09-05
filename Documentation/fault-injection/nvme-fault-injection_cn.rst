### NVMe 故障注入

Linux 的故障注入框架提供了一种系统化的方式来支持通过 `/sys/kernel/debug` 目录下的 debugfs 进行错误注入。当启用时，默认的 `NVME_SC_INVALID_OPCODE`（无效的操作码）且不重试将被注入到 `nvme_try_complete_req` 中。用户可以通过 debugfs 更改默认的状态码和不重试标志。通用命令状态列表可以在 `include/linux/nvme.h` 中找到。

以下示例展示了如何向 NVMe 注入错误：

首先，启用 `CONFIG_FAULT_INJECTION_DEBUG_FS` 内核配置，并重新编译内核。启动内核后，执行以下操作。

#### 示例 1：注入默认状态码且不重试

```
mount /dev/nvme0n1 /mnt
echo 1 > /sys/kernel/debug/nvme0n1/fault_inject/times
echo 100 > /sys/kernel/debug/nvme0n1/fault_inject/probability
cp a.file /mnt
```

**预期结果：**
```
cp: cannot stat ‘/mnt/a.file’: Input/output error
```

**来自 `dmesg` 的消息：**
```
FAULT_INJECTION: forcing a failure
name fault_inject, interval 1, probability 100, space 0, times 1
CPU: 0 PID: 0 Comm: swapper/0 Not tainted 4.15.0-rc8+ #2
Hardware name: innotek GmbH VirtualBox/VirtualBox, BIOS VirtualBox 12/01/2006
Call Trace:
  <IRQ>
  dump_stack+0x5c/0x7d
  should_fail+0x148/0x170
  nvme_should_fail+0x2f/0x50 [nvme_core]
  nvme_process_cq+0xe7/0x1d0 [nvme]
  nvme_irq+0x1e/0x40 [nvme]
  __handle_irq_event_percpu+0x3a/0x190
  handle_irq_event_percpu+0x30/0x70
  handle_irq_event+0x36/0x60
  handle_fasteoi_irq+0x78/0x120
  handle_irq+0xa7/0x130
  ? tick_irq_enter+0xa8/0xc0
  do_IRQ+0x43/0xc0
  common_interrupt+0xa2/0xa2
</IRQ>
RIP: 0010:native_safe_halt+0x2/0x10
RSP: 0018:ffffffff82003e90 EFLAGS: 00000246 ORIG_RAX: ffffffffffffffdd
RAX: ffffffff817a10c0 RBX: ffffffff82012480 RCX: 0000000000000000
RDX: 0000000000000000 RSI: 0000000000000000 RDI: 0000000000000000
RBP: 0000000000000000 R08: 000000008e38ce64 R09: 0000000000000000
R10: 0000000000000000 R11: 0000000000000000 R12: ffffffff82012480
R13: ffffffff82012480 R14: 0000000000000000 R15: 0000000000000000
? __sched_text_end+0x4/0x4
default_idle+0x18/0xf0
do_idle+0x150/0x1d0
cpu_startup_entry+0x6f/0x80
start_kernel+0x4c4/0x4e4
? set_init_arg+0x55/0x55
secondary_startup_64+0xa5/0xb0
print_req_error: I/O error, dev nvme0n1, sector 9240
EXT4-fs error (device nvme0n1): ext4_find_entry:1436:
inode #2: comm cp: reading directory lblock 0
```

#### 示例 2：注入默认状态码但允许重试

```
mount /dev/nvme0n1 /mnt
echo 1 > /sys/kernel/debug/nvme0n1/fault_inject/times
echo 100 > /sys/kernel/debug/nvme0n1/fault_inject/probability
echo 1 > /sys/kernel/debug/nvme0n1/fault_inject/status
echo 0 > /sys/kernel/debug/nvme0n1/fault_inject/dont_retry
cp a.file /mnt
```

**预期结果：**
```
command success without error
```

**来自 `dmesg` 的消息：**
```
FAULT_INJECTION: forcing a failure
name fault_inject, interval 1, probability 100, space 0, times 1
CPU: 1 PID: 0 Comm: swapper/1 Not tainted 4.15.0-rc8+ #4
Hardware name: innotek GmbH VirtualBox/VirtualBox, BIOS VirtualBox 12/01/2006
Call Trace:
  <IRQ>
  dump_stack+0x5c/0x7d
  should_fail+0x148/0x170
  nvme_should_fail+0x30/0x60 [nvme_core]
  nvme_loop_queue_response+0x84/0x110 [nvme_loop]
  nvmet_req_complete+0x11/0x40 [nvmet]
  nvmet_bio_done+0x28/0x40 [nvmet]
  blk_update_request+0xb0/0x310
  blk_mq_end_request+0x18/0x60
  flush_smp_call_function_queue+0x3d/0xf0
  smp_call_function_single_interrupt+0x2c/0xc0
  call_function_single_interrupt+0xa2/0xb0
</IRQ>
RIP: 0010:native_safe_halt+0x2/0x10
RSP: 0018:ffffc9000068bec0 EFLAGS: 00000246 ORIG_RAX: ffffffffffffff04
RAX: ffffffff817a10c0 RBX: ffff88011a3c9680 RCX: 0000000000000000
RDX: 0000000000000000 RSI: 0000000000000000 RDI: 0000000000000000
RBP: 0000000000000001 R08: 000000008e38c131 R09: 0000000000000000
R10: 0000000000000000 R11: 0000000000000000 R12: ffff88011a3c9680
R13: ffff88011a3c9680 R14: 0000000000000000 R15: 0000000000000000
? __sched_text_end+0x4/0x4
default_idle+0x18/0xf0
do_idle+0x150/0x1d0
cpu_startup_entry+0x6f/0x80
start_secondary+0x187/0x1e0
secondary_startup_64+0xa5/0xb0
```

#### 示例 3：注入第 10 个管理命令中的错误

```
echo 100 > /sys/kernel/debug/nvme0/fault_inject/probability
echo 10 > /sys/kernel/debug/nvme0/fault_inject/space
echo 1 > /sys/kernel/debug/nvme0/fault_inject/times
nvme reset /dev/nvme0
```

**预期结果：**
```
在 NVMe 控制器重置后，重新初始化可能成功也可能失败，这取决于实际被强制失败的是哪个管理命令。
```

**来自 `dmesg` 的消息：**
```
nvme nvme0: resetting controller
FAULT_INJECTION: forcing a failure
name fault_inject, interval 1, probability 100, space 1, times 1
CPU: 0 PID: 0 Comm: swapper/0 Not tainted 5.2.0-rc2+ #2
Hardware name: MSI MS-7A45/B150M MORTAR ARCTIC (MS-7A45), BIOS 1.50 04/25/2017
Call Trace:
  <IRQ>
  dump_stack+0x63/0x85
  should_fail+0x14a/0x170
  nvme_should_fail+0x38/0x80 [nvme_core]
  nvme_irq+0x129/0x280 [nvme]
  ? blk_mq_end_request+0xb3/0x120
  __handle_irq_event_percpu+0x84/0x1a0
  handle_irq_event_percpu+0x32/0x80
  handle_irq_event+0x3b/0x60
  handle_edge_irq+0x7f/0x1a0
  handle_irq+0x20/0x30
  do_IRQ+0x4e/0xe0
  common_interrupt+0xf/0xf
</IRQ>
RIP: 0010:cpuidle_enter_state+0xc5/0x460
Code: ff e8 8f 5f 86 ff 80 7d c7 00 74 17 9c 58 0f 1f 44 00 00 f6 c4 02 0f 85 69 03 00 00 31 ff e8 62 aa 8c ff fb 66 0f 1f 44 00 00 <45> 85 ed 0f 88 37 03 00 00 4c 8b 45 d0 4c 2b 45 b8 48 ba cf f7 53
RSP: 0018:ffffffff88c03dd0 EFLAGS: 00000246 ORIG_RAX: ffffffffffffffdc
RAX: ffff9dac25a2ac80 RBX: ffffffff88d53760 RCX: 000000000000001f
RDX: 0000000000000000 RSI: 000000002d958403 RDI: 0000000000000000
RBP: ffffffff88c03e18 R08: fffffff75e35ffb7 R09: 00000a49a56c0b48
R10: ffffffff88c03da0 R11: 0000000000001b0c R12: ffff9dac25a34d00
R13: 0000000000000006 R14: 0000000000000006 R15: ffffffff88d53760
cpuidle_enter+0x2e/0x40
call_cpuidle+0x23/0x40
do_idle+0x201/0x280
cpu_startup_entry+0x1d/0x20
rest_init+0xaa/0xb0
arch_call_rest_init+0xe/0x1b
start_kernel+0x51c/0x53b
x86_64_start_reservations+0x24/0x26
x86_64_start_kernel+0x74/0x77
secondary_startup_64+0xa4/0xb0
nvme nvme0: Could not set queue count (16385)
nvme nvme0: IO queues not created
```
