==================
控制组统计信息 (Control Group Stats)
==================

控制组统计信息 (Control Groupstats) 是受到以下讨论的启发：
https://lore.kernel.org/r/461CF883.2030308@sw.ru，并实现了 Andrew Morton 在
https://lore.kernel.org/r/20070411114927.1277d7c9.akpm@linux-foundation.org 中建议的每个控制组的统计信息。
每个控制组的统计信息基础设施重用了来自任务统计接口 (taskstats) 的代码。为控制组注册了一套新的操作，包括特定于控制组的命令和属性。通过向 cgroupstats 结构添加成员来扩展每个控制组的统计信息应该非常容易。
当前的 cgroupstats 模型是拉取模式，推送模型（用于在有趣事件发生时发布统计信息）也应该很容易添加。目前用户空间通过传递控制组路径请求统计信息。
返回给用户空间的是关于控制组中所有任务状态的统计信息。
**注意**：我们目前依赖延迟会计 (delay accounting) 来提取被 I/O 阻塞的任务的信息。如果禁用了 CONFIG_TASK_DELAY_ACCT 配置项，则此信息将不可用。
为了提取控制组的统计信息，已经开发了一个类似于 getdelays.c 的工具，该工具的示例输出如下所示：

```
~/balbir/cgroupstats # ./getdelays  -C "/sys/fs/cgroup/a"
sleeping 1, blocked 0, running 1, stopped 0, uninterruptible 0
~/balbir/cgroupstats # ./getdelays  -C "/sys/fs/cgroup"
sleeping 155, blocked 0, running 1, stopped 0, uninterruptible 2
```
