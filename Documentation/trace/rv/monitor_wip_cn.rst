监控器 wip
==========

- 名称：wip - 在抢占模式下唤醒
- 类型：每核确定性自动机
- 作者：Daniel Bristot de Oliveira <bristot@kernel.org>

描述
----

在抢占模式下唤醒（wip）监控器是一个样本的每核监控器，用于验证唤醒事件是否总是在抢占禁用的情况下发生：

```
                     |
                     |
                     v
                   #==================#
                   H    preemptive    H <+
                   #==================#  |
                     |                   |
                     | preempt_disable   | preempt_enable
                     v                   |
    sched_waking   +------------------+  |
  +--------------- |                  |  |
  |                |  non_preemptive  |  |
  +--------------> |                  | -+
                   +------------------+
```

由于调度器同步机制，唤醒事件总是发生在抢占禁用的情况下。然而，由于 `preempt_count` 及其跟踪事件与中断不是原子操作的，可能会出现一些不一致的情况。例如：

```
preempt_disable() {
  __preempt_count_add(1)
  -------> smp_apic_timer_interrupt() {
            preempt_disable()
             不跟踪 (preempt count >= 1)

            唤醒一个线程

            preempt_enable()
             不跟踪 (preempt count >= 1)
          }
  <------
  trace_preempt_disable();
}
```

这个问题已在以下链接中报告和讨论：
https://lore.kernel.org/r/cover.1559051152.git.bristot@redhat.com/

规范
----
Graphviz Dot 文件位于 tools/verification/models/wip.dot 中。
