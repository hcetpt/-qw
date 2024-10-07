确定性自动机的仪器化
======================================

由dot2k生成的RV监视器文件，命名为"$MODEL_NAME.c"，包含一个专门用于仪器化的部分。在[1]中创建的wip.dot监视器的例子中，这部分看起来像这样：

  ```
  /*
   * 这是监视器的仪器化部分
   *
   * 这一节需要手动完成工作。在这里，内核事件被转换为模型的事件。
   */
  static void handle_preempt_disable(void *data, /* XXX: 填充头部 */)
  {
    da_handle_event_wip(preempt_disable_wip);
  }

  static void handle_preempt_enable(void *data, /* XXX: 填充头部 */)
  {
    da_handle_event_wip(preempt_enable_wip);
  }

  static void handle_sched_waking(void *data, /* XXX: 填充头部 */)
  {
    da_handle_event_wip(sched_waking_wip);
  }

  static int enable_wip(void)
  {
    int retval;

    retval = da_monitor_init_wip();
    if (retval)
      return retval;

    rv_attach_trace_probe("wip", /* XXX: tracepoint */, handle_preempt_disable);
    rv_attach_trace_probe("wip", /* XXX: tracepoint */, handle_preempt_enable);
    rv_attach_trace_probe("wip", /* XXX: tracepoint */, handle_sched_waking);

    return 0;
  }
  ```

这一部分顶部的注释解释了其基本思想：仪器化部分将*内核事件*转换为*模型的事件*。

追踪回调函数
--------------------------

前三个函数是wip模型中的三个事件对应的回调*处理函数*的起点。开发者不一定需要使用它们：它们只是起点。以以下示例为例：

  ```c
  void handle_preempt_disable(void *data, /* XXX: 填充头部 */)
  {
    da_handle_event_wip(preempt_disable_wip);
  }
  ```

模型中的`preempt_disable`事件直接连接到`preemptirq:preempt_disable`。`preemptirq:preempt_disable`事件的签名如下，来自`include/trace/events/preemptirq.h`：

  ```c
  TP_PROTO(unsigned long ip, unsigned long parent_ip)
  ```

因此，`handle_preempt_disable()`函数看起来像这样：

  ```c
  void handle_preempt_disable(void *data, unsigned long ip, unsigned long parent_ip)
  ```

在这种情况下，内核事件与自动机事件是一对一的映射，实际上，这个函数不需要其他更改。下一个处理函数`handle_preempt_enable()`具有与`handle_preempt_disable()`相同的参数列表。不同之处在于，`preempt_enable`事件将用于同步系统和模型。最初，模型处于初始状态，但系统可能或不处于初始状态。监视器无法开始处理事件，直到它知道系统已经到达初始状态；否则，监视器和系统可能会不同步。

查看自动机定义，可以看到在`preempt_enable`执行后，系统和模型预计会返回到初始状态。因此，可以利用`preempt_enable`事件在监视部分初始化时同步系统和模型。
启动是通过一个特殊的句柄函数来通知的，即“da_handle_start_event_$(MONITOR_NAME)(event)”：

```c
da_handle_start_event_wip(preempt_enable_wip);
```

因此，回调函数将如下所示：

```c
void handle_preempt_enable(void *data, unsigned long ip, unsigned long parent_ip)
{
    da_handle_start_event_wip(preempt_enable_wip);
}
```

最后，“handle_sched_waking()”将如下所示：

```c
void handle_sched_waking(void *data, struct task_struct *task)
{
    da_handle_event_wip(sched_waking_wip);
}
```

关于这些函数的解释留给读者作为练习。

### 启用和禁用函数

dot2k 自动创建两个特殊函数：

```c
enable_$(MONITOR_NAME)();
disable_$(MONITOR_NAME)();
```

这些函数分别在监视器启用和禁用时被调用。它们应该用于将监控工具*附加*到正在运行的系统中。开发人员必须在相应的函数中添加所有需要将监视器*附加*或*分离*到系统的代码。对于 wip 情况，这些函数被命名为：

```c
enable_wip();
disable_wip();
```

但由于默认情况下，这些函数已经能够*附加*和*分离* tracepoints_to_attach，这已经足够了。

### 监控工具助手

为了完成监控工具，需要在监控启用阶段将*处理函数*与内核事件关联起来。RV 接口也简化了这一步骤。例如，宏 “rv_attach_trace_probe()” 用于将 wip 模型事件连接到相关的内核事件。dot2k 在启用阶段自动为每个模型事件添加 “rv_attach_trace_probe()” 函数调用，作为建议。

例如，从 wip 示例模型：

```c
static int enable_wip(void)
{
    int retval;

    retval = da_monitor_init_wip();
    if (retval)
        return retval;

    rv_attach_trace_probe("wip", /* XXX: tracepoint */, handle_preempt_enable);
    rv_attach_trace_probe("wip", /* XXX: tracepoint */, handle_sched_waking);
    rv_attach_trace_probe("wip", /* XXX: tracepoint */, handle_preempt_disable);

    return 0;
}
```

然后需要在禁用阶段将探针分离。

[1] wip 模型在以下文档中介绍：

```
Documentation/trace/rv/deterministic_automata.rst
```

wip 监视器在以下文档中介绍：

```
Documentation/trace/rv/da_monitor_synthesis.rst
```
