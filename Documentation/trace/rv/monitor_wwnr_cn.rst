监视器 wwnr
============

- 名称：wwrn - 在未运行时唤醒
- 类型：每任务确定性自动机
- 作者：Daniel Bristot de Oliveira <bristot@kernel.org>

描述
------------

这是一个每任务的样本监视器，定义如下：

```
               |
               |
               v
    wakeup   +-------------+
  +--------- |             |
  |          | not_running |
  +--------> |             | <+
             +-------------+  |
               |              |
               | switch_in    | switch_out
               v              |
             +-------------+  |
             |   running   | -+
             +-------------+
```

这个模型是不正确的，原因是任务可以在处理器上运行而没有被设置为 RUNNABLE。考虑一个即将休眠的任务：

```c
  1:      set_current_state(TASK_UNINTERRUPTIBLE);
  2:      schedule();
```

然后想象在第1行和第2行之间发生了一个IRQ，唤醒了该任务。这时，任务在运行时发生了唤醒。

- 那么为什么我们需要这个模型呢？
- 为了测试反应器

规范
-------------
Graphviz Dot 文件位于 tools/verification/models/wwnr.dot 中
