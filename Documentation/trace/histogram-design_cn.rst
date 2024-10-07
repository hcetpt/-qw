SPDX 许可声明标识符: GPL-2.0

======================
直方图设计说明
======================

:作者: Tom Zanussi <zanussi@kernel.org>

本文档试图提供关于 ftrace 直方图如何工作以及各个组件如何映射到 trace_events_hist.c 和 tracing_map.c 中使用的数据结构的描述。
注意：所有 ftrace 直方图命令示例都假定工作目录是 ftrace 的 /tracing 目录。例如：

```
# cd /sys/kernel/tracing
```

此外，这些命令显示的直方图输出通常会被截断——仅显示足以说明问题的部分。

'hist_debug' 跟踪事件文件
==============================

如果内核编译时设置了 CONFIG_HIST_TRIGGERS_DEBUG，那么在每个事件的子目录中会出现一个名为 'hist_debug' 的事件文件。这个文件可以随时读取，并会显示本文档中描述的一些直方图触发器内部信息。具体的示例和输出将在下面的测试用例中详细描述。

基本直方图
================

首先，基本直方图。下面是使用直方图所能做的最简单的事情——为单个事件创建一个带有单个键的直方图并查看其输出：

```
# echo 'hist:keys=pid' >> events/sched/sched_waking/trigger

# cat events/sched/sched_waking/hist

{ pid:      18249 } hitcount:          1
{ pid:      13399 } hitcount:          1
{ pid:      17973 } hitcount:          1
{ pid:      12572 } hitcount:          1
...
{ pid:         10 } hitcount:        921
{ pid:      18255 } hitcount:       1444
{ pid:      25526 } hitcount:       2055
{ pid:       5257 } hitcount:       2055
{ pid:      27367 } hitcount:       2055
{ pid:       1728 } hitcount:       2161

总计：
命中次数：21305
条目数：183
丢弃次数：0
```

这会在 `sched_waking` 事件上创建一个以 `pid` 作为键的直方图，并带有一个值 `hitcount`，即使没有明确指定，该值对于每个直方图都是存在的。
`hitcount` 值是一个按桶计数的值，在每次命中给定键（在这种情况下是 `pid`）时自动递增。
因此，在此直方图中，每个 `pid` 都有一个单独的桶，每个桶包含一个该桶的值，统计了该 `pid` 下 `sched_waking` 被调用的次数。
每个直方图由一个 `hist_data` 结构体表示。
为了跟踪直方图中的每个键和值字段，`hist_data` 保持一个名为 `fields[]` 的数组。`fields[]` 数组包含每个直方图值和键的 `struct hist_field` 表示（变量也包括在此处，但稍后讨论）。所以对于上面的直方图，我们有一个键和一个值；在这种情况下，唯一的一个值是 `hitcount` 值，这是所有直方图都有的，无论是否定义该值，上述直方图没有定义它。
每个 `struct hist_field` 包含指向事件 `trace_event_file` 中的 `ftrace_event_field` 指针，以及与此相关的各种信息，如大小、偏移量、类型和 `hist_field_fn_t` 函数，用于从 ftrace 事件缓冲区获取字段的数据（在大多数情况下——一些 `hist_field` 如 `hitcount` 并不直接映射到跟踪缓冲区中的事件字段——在这种情况下，函数实现会从其他地方获取其值）。`flags` 字段指示其字段类型——键、值、变量、变量引用等，默认为值。
除了fields[]数组之外，另一个重要的hist_data数据结构是为直方图创建的tracing_map实例，它存储在.map成员中。tracing_map实现了无锁哈希表，用于实现直方图（有关实现tracing_map的低级数据结构的更多讨论，请参阅kernel/trace/tracing_map.h）。为了便于讨论，tracing_map包含多个桶，每个桶对应一个由特定直方图键散列的tracing_map_elt对象。

下面是描述上述直方图的hist_data及其关联的键和值字段的前半部分的图表。如您所见，fields数组中有两个字段，一个是表示hitcount的val字段，另一个是表示pid键的key字段。

下面是运行时快照中的tracing_map图表，试图展示几个假设的键和值与hist_data字段和tracing_map元素之间的关系：

```
+------------------+
| hist_data        |
+------------------+     +----------------+
  | .fields[]      |---->| val = hitcount |----------------------------+
  +----------------+     +----------------+                            |
  | .map           |       | .size        |                            |
  +----------------+       +--------------+                            |
                            | .offset      |                            |
                            +--------------+                            |
                            | .fn()        |                            |
                            +--------------+                            |
                                  .                                     |
                                  .                                     |
                                  .                                     |
                          +----------------+ <--- n_vals                |
                          | key = pid      |----------------------------|--+
                          +----------------+                            |  |
                            | .size        |                            |  |
                            +--------------+                            |  |
                            | .offset      |                            |  |
                            +--------------+                            |  |
                            | .fn()        |                            |  |
                          +----------------+ <--- n_fields              |  |
                          | unused         |                            |  |
                          +----------------+                            |  |
                            |              |                            |  |
                            +--------------+                            |  |
                            |              |                            |  |
                            +--------------+                            |  |
                            |              |                            |  |
                            +--------------+                            |  |
                                            n_keys = n_fields - n_vals   |  |

hist_data中的n_vals和n_fields定义了fields[]数组的范围，并将键和值分开，以便后续代码使用。

下面是运行时表示的tracing_map部分图表，显示了fields[]数组的各个部分到tracing_map相应部分的指针。

tracing_map由一个tracing_map_entry数组和一组预分配的tracing_map_elts组成（以下简称为map_entry和map_elt）。hist_data.map数组中的map_entry总数 = map->max_elts（实际上是map->map_size，但仅使用max_elts）。这是map_insert()算法所需的一个属性。

如果map_entry未被使用，意味着尚未有键散列到该位置，则其.key值为0且.val指针为NULL。一旦map_entry被占用，.key值包含键的散列值，.val成员指向包含完整键和map_elt.fields[]数组中每个键或值条目的map_elt。map_elt.fields[]数组中的每一项对应直方图中的一个hist_field，这是持续聚合的总和所在的位置。

图表试图展示hist_data.fields[]和map_elt.fields[]之间的关系，通过图示中的链接表示：

```
+-----------+		                                                 |  |
| hist_data |		                                                 |  |
+-----------+		                                                 |  |
  | .fields |		                                                 |  |
  +---------+     +-----------+		                         |  |
  | .map    |---->| map_entry |		                         |  |
  +---------+     +-----------+		                         |  |
                | .key    |---> 0		                         |  |
                +---------+		                         |  |
                | .val    |---> NULL		                 |  |
              +-----------+                                        |  |
              | map_entry |                                        |  |
              +-----------+                                        |  |
                | .key    |---> pid = 999                          |  |
                +---------+    +-----------+                       |  |
                | .val    |--->| map_elt   |                       |  |
                +---------+    +-----------+                       |  |
                                 | .key    |---> full key *        |  |
                                 +---------+    +---------------+  |  |
				 | .fields |--->| .sum (val)    |<-+  |
                                 +---------+    | 2345          |  |  |
                                                  +---------------+  |  |
                                                  | .offset (key) |<----+
                                                  | 0             |  |  |
                                                  +---------------+  |  |
                                                  | .sum (val) or |  |  |
                                                  | .offset (key) |  |  |
                                                  +---------------+  |  |
                                                  | .sum (val) or |  |  |
                                                  | .offset (key) |  |  |
                                                  +---------------+  |  |
                                                           .          |  |
                                                           .          |  |
                                                  +---------------+  |  |
                                                  | .sum (val) or |  |  |
                                                  | .offset (key) |  |  |
                                                  +---------------+  |  |

```

每当发生新的事件并且该事件关联了一个直方图触发器时，会调用event_hist_trigger()。event_hist_trigger()首先处理键：对于键中的每个子键（在上面的例子中，只有一个子键对应pid），从hist_data.fields[]中获取表示该子键的hist_field，并使用该字段的hist_field_fn_t fn()以及字段的大小和偏移量来从当前跟踪记录中抓取该子键的数据。
一旦完整地获取到键，就用该键在tracing_map中查找。如果没有与该键关联的tracing_map_elt，则申请一个新的空tracing_map_elt并插入到map中以供新键使用。无论哪种情况，都会返回与该键关联的tracing_map_elt。
一旦有了可用的tracing_map_elt，就会调用hist_trigger_elt_update()。顾名思义，这会更新元素，基本上意味着更新元素的字段。直方图中的每个键和值都有一个关联的tracing_map_field，这些都对应于创建直方图时创建的键和值hist_fields。hist_trigger_elt_update()遍历每个值hist_field，并像处理键一样使用hist_field的fn()、大小和偏移量来从当前跟踪记录中抓取字段的值。一旦获取到该值，就会将该值加到该字段不断更新的tracing_map_field.sum成员上。有些hist_field的fn()，例如hitcount，并不实际从跟踪记录中抓取任何内容（hitcount的fn()只是将计数器sum递增1），但原理是一样的。
一旦所有值都被更新，hist_trigger_elt_update()完成并返回。请注意，键中的每个子键也有对应的tracing_map_fields，但hist_trigger_elt_update()不会查看它们或更新任何内容——这些字段仅用于排序，可以在稍后进行。
