事件直方图
================

文档由 Tom Zanussi 编写

1. 引言
===============

  直方图触发器是一种特殊的事件触发器，可以将追踪事件数据汇总到直方图中。关于追踪事件和事件触发器的更多信息，请参阅 `Documentation/trace/events.rst`。

2. 直方图触发命令
============================

  直方图触发命令是一种事件触发命令，它将事件命中聚合到一个哈希表中，该哈希表以一个或多个追踪事件格式字段（或堆栈跟踪）为键，并根据一个或多个追踪事件格式字段和/或事件计数（命中计数）生成一组累计值。
直方图触发器的格式如下：

```
hist:keys=<field1[,field2,...]>[:values=<field1[,field2,...]>]
  [:sort=<field1[,field2,...]>][:size=#entries][:pause][:continue]
  [:clear][:name=histname1][:nohitcount][:<handler>.<action>] [if <filter>]
```

  当匹配的事件被命中时，使用指定的键和值在哈希表中添加一个条目。键和值对应于事件格式描述中的字段。值必须对应于数值字段 - 在事件命中时，值将被累加到该字段的总和中。特殊字符串 'hitcount' 可以代替显式的值字段 - 这只是事件命中的计数。如果未指定 'values'，则会自动创建隐式 'hitcount' 值并作为唯一的值使用。

键可以是任何字段，或者特殊的字符串 'common_stacktrace'，这将使用事件的内核堆栈跟踪作为键。关键词 'keys' 或 'key' 用于指定键，关键词 'values'、'vals' 或 'val' 用于指定值。复合键最多可以由三个字段组成，通过 'keys' 关键词指定。对复合键进行哈希处理会在表中为每个唯一组合的组件键生成一个独特的条目，这对于提供更细粒度的事件数据摘要很有用。

此外，可以通过 'sort' 关键词指定最多两个字段的排序键。如果指定了多个字段，则结果将是“排序中的排序”：第一个键被视为主要排序键，第二个键为次要键。如果使用 'name' 参数给直方图触发器命名，其直方图数据将与其他具有相同名称的触发器共享，触发器的命中将更新这些共同的数据。只有具有“兼容”字段的触发器才能以这种方式组合；触发器是“兼容”的，如果它们在触发器中命名的字段具有相同的数量和类型，并且这些字段也具有相同的名称。

请注意，任何两个事件始终共享兼容的 'hitcount' 和 'common_stacktrace' 字段，因此可以使用这些字段进行组合，尽管这样做可能毫无意义。

'hist' 触发器会为每个事件的子目录添加一个 'hist' 文件。读取事件的 'hist' 文件会将整个哈希表输出到标准输出。如果事件有多个直方图触发器，则输出中将包含每个触发器的一个表。对于具有相同名称的命名触发器，显示的表将与任何其他实例相同。每个打印的哈希表条目是一个简单的键和值列表；键首先打印，并用花括号分隔，然后是条目的值字段。默认情况下，数值字段以十进制整数形式显示。这可以通过在字段名称后附加以下任一修饰符来修改：

| 修饰符 | 描述 |
| --- | --- |
| .hex | 以十六进制值显示数字 |
| .sym | 以符号形式显示地址 |
| .sym-offset | 以符号和偏移量形式显示地址 |
| .syscall | 以系统调用名称显示系统调用ID |
| .execname | 以程序名称显示common_pid |
| .log2 | 显示对数2值而不是原始数字 |
| .buckets=size | 显示值的分组而不是原始数字 |
| .usecs | 以微秒形式显示common_timestamp |
| .percent | 以百分比形式显示数字 |
| .graph | 显示值的条形图 |
| .stacktrace | 以堆栈跟踪形式显示（必须是long[]类型） |

  请注意，一般而言，在应用修饰符时不会解释给定字段的语义，但在这方面有一些需要注意的限制：

- 只有 'hex' 修饰符可以用于值（因为值本质上是总和，而其他修饰符在这种上下文中没有意义）
- 'execname' 修饰符只能用于 'common_pid'。原因是 execname 仅是事件触发时为 'current' 进程保存的 'comm' 值，这与事件追踪代码保存的 common_pid 值相同。尝试将此 comm 值应用于其他 pid 值是不正确的，通常关心的事件会在事件本身中保存特定 pid 的 comm 字段

一个典型的使用场景如下所示，启用直方图触发器，读取其当前内容，然后关闭它：

```sh
# echo 'hist:keys=skbaddr.hex:vals=len' > \
  /sys/kernel/tracing/events/net/netif_rx/trigger

# cat /sys/kernel/tracing/events/net/netif_rx/hist

# echo '!hist:keys=skbaddr.hex:vals=len' > \
  /sys/kernel/tracing/events/net/netif_rx/trigger
```

触发器文件本身可以读取以显示当前附加的直方图触发器的详细信息。当读取 'hist' 文件时，这些信息也会显示在文件顶部。
默认情况下，哈希表的大小为2048个条目。可以通过'size'参数来指定更多或更少的条目数。单位是以哈希表条目计算的——如果运行过程中使用的条目数超过指定的数量，结果将显示被忽略的“丢弃”（drops）次数。大小应该是介于128和131072之间的2的幂（任何非2的幂的数值都会向上取整）。
  
'sort'参数可以用来指定排序的值字段。如果不指定，默认是按'hitcount'进行排序，并且默认的排序顺序是“升序”。若要按相反方向排序，则在排序键后添加'.descending'。

'pause'参数可以用来暂停现有的hist触发器，或者启动一个hist触发器但不记录事件，直到接收到指示为止。'continue'或'cont'可用于启动或重新启动已暂停的hist触发器。

'clear'参数会清除正在运行的hist触发器的内容，但保留其当前的暂停/活动状态。

注意，如果对现有的触发器应用'pause'、'cont'和'clear'参数时，应该使用'append'外壳运算符('>>')，而不是'>'运算符，后者会导致触发器通过截断而被移除。

'nohitcount'（或NOHC）参数将抑制直方图中原始hitcount的显示。此选项要求至少有一个不是'raw hitcount'的值字段。例如，'hist:...:vals=hitcount:nohitcount'会被拒绝，但'hist:...:vals=hitcount.percent:nohitcount'是可以接受的。

- enable_hist/disable_hist

  enable_hist和disable_hist触发器可用于有条件地启动和停止另一个事件已经附加的hist触发器。可以在给定事件上附加任意数量的enable_hist和disable_hist触发器，从而允许该事件启动并停止其他多个事件的聚合。

格式与enable/disable_event触发器非常相似：

      enable_hist:<system>:<event>[:count]
      disable_hist:<system>:<event>[:count]

  与enable/disable_event触发器启用或禁用目标事件进入跟踪缓冲区不同，enable/disable_hist触发器启用或禁用目标事件进入哈希表的聚合。

enable_hist/disable_hist触发器的一个典型使用场景是首先在一个事件上设置一个暂停的hist触发器，然后使用一对enable_hist/disable_hist触发器在特定条件满足时开启和关闭hist聚合：

   # echo 'hist:keys=skbaddr.hex:vals=len:pause' > \
      /sys/kernel/tracing/events/net/netif_receive_skb/trigger

    # echo 'enable_hist:net:netif_receive_skb if filename==/usr/bin/wget' > \
      /sys/kernel/tracing/events/sched/sched_process_exec/trigger

    # echo 'disable_hist:net:netif_receive_skb if comm==wget' > \
      /sys/kernel/tracing/events/sched/sched_process_exit/trigger

  上述配置设置了一个初始处于暂停状态的hist触发器，当执行某个程序时，该触发器解除暂停并开始聚合事件；当进程退出时，hist触发器再次暂停，停止聚合事件。

下面的例子提供了更具体的说明，展示了上述概念和典型使用模式。
特殊事件字段
------------------------

有一些“特殊事件字段”可以作为hist触发器中的键或值使用。这些字段看起来和行为都像是实际的事件字段，但实际上并不是事件字段定义或格式文件的一部分。然而，它们对于任何事件都是可用的，并且可以在需要实际事件字段的任何地方使用。

| 特殊事件字段 | 类型   | 描述 |
|--------------|--------|--------------------------------------------------|
| `common_timestamp` | `u64` | 与事件关联的时间戳（来自环形缓冲区），以纳秒为单位。可以通过`.usecs`修改为微秒。 |
| `common_cpu` | `int`  | 发生事件的CPU编号。 |

扩展错误信息
--------------------------

对于在调用hist触发器命令时遇到的一些错误条件，可以通过`tracing/error_log`文件获取扩展错误信息。详见《Documentation/trace/ftrace.rst》中的“错误条件”部分。

6.2 'hist' 触发器示例
---------------------------

下面的一组示例展示了如何使用`kmalloc`事件创建聚合。可以在`kmalloc`事件的格式文件中查看可用于hist触发器的字段：

```shell
# cat /sys/kernel/tracing/events/kmem/kmalloc/format
name: kmalloc
ID: 374
format:
field:unsigned short common_type; offset:0; size:2; signed:0;
field:unsigned char common_flags; offset:2; size:1; signed:0;
field:unsigned char common_preempt_count; offset:3; size:1; signed:0;
field:int common_pid; offset:4; size:4; signed:1;

field:unsigned long call_site; offset:8; size:8; signed:0;
field:const void * ptr; offset:16; size:8; signed:0;
field:size_t bytes_req; offset:24; size:8; signed:0;
field:size_t bytes_alloc; offset:32; size:8; signed:0;
field:gfp_t gfp_flags; offset:40; size:4; signed:0;
```

我们首先创建一个hist触发器，生成一个简单的表格，列出内核中每个调用`kmalloc`函数的功能请求的总字节数：

```shell
# echo 'hist:key=call_site:val=bytes_req.buckets=32' > \
        /sys/kernel/tracing/events/kmem/kmalloc/trigger
```

这告诉追踪系统使用`kmalloc`事件中的`call_site`字段作为表的键，即每个唯一的`call_site`地址将在表中创建一个条目。参数`val=bytes_req`表示对于表中的每个唯一条目（`call_site`），应该记录该`call_site`请求的字节数的累计值。
我们让它运行一段时间，然后输出`kmalloc`事件子目录中的`hist`文件的内容（为了便于阅读，省略了一些条目）：

```shell
# cat /sys/kernel/tracing/events/kmem/kmalloc/hist
# trigger info: hist:keys=call_site:vals=bytes_req:sort=hitcount:size=2048 [active]

{ call_site: 18446744072106379007 } hitcount:          1  bytes_req:        176
{ call_site: 18446744071579557049 } hitcount:          1  bytes_req:       1024
{ call_site: 18446744071580608289 } hitcount:          1  bytes_req:      16384
{ call_site: 18446744071581827654 } hitcount:          1  bytes_req:         24
{ call_site: 18446744071580700980 } hitcount:          1  bytes_req:          8
{ call_site: 18446744071579359876 } hitcount:          1  bytes_req:        152
{ call_site: 18446744071580795365 } hitcount:          3  bytes_req:        144
{ call_site: 18446744071581303129 } hitcount:          3  bytes_req:        144
{ call_site: 18446744071580713234 } hitcount:          4  bytes_req:       2560
{ call_site: 18446744071580933750 } hitcount:          4  bytes_req:        736

{ call_site: 18446744072106047046 } hitcount:         69  bytes_req:       5576
{ call_site: 18446744071582116407 } hitcount:         73  bytes_req:       2336
{ call_site: 18446744072106054684 } hitcount:        136  bytes_req:     140504
{ call_site: 18446744072106224230 } hitcount:        136  bytes_req:      19584
{ call_site: 18446744072106078074 } hitcount:        153  bytes_req:       2448
{ call_site: 18446744072106062406 } hitcount:        153  bytes_req:      36720
{ call_site: 18446744071582507929 } hitcount:        153  bytes_req:      37088
{ call_site: 18446744072102520590 } hitcount:        273  bytes_req:      10920
{ call_site: 18446744071582143559 } hitcount:        358  bytes_req:        716
{ call_site: 18446744072106465852 } hitcount:        417  bytes_req:      56712
{ call_site: 18446744072102523378 } hitcount:        485  bytes_req:      27160
{ call_site: 18446744072099568646 } hitcount:       1676  bytes_req:      33520

Totals:
    Hits: 4610
    Entries: 45
    Dropped: 0
```

输出显示每条记录的一行，从触发器中指定的键开始，后跟触发器中指定的值。输出的开头有一行显示触发器信息，也可以通过读取`trigger`文件来显示：

```shell
# cat /sys/kernel/tracing/events/kmem/kmalloc/trigger
hist:keys=call_site:vals=bytes_req:sort=hitcount:size=2048 [active]
```

输出的末尾有几行显示了整个运行的总计数。“Hits”字段显示触发器被触发的总次数，“Entries”字段显示哈希表中使用的总条目数，“Dropped”字段显示由于运行期间使用的条目数超过表允许的最大条目数而被丢弃的次数（通常为0，如果不是，则提示你可能需要增加表的大小，使用`size`参数）。

请注意，在上面的输出中有一个额外的字段`hitcount`，这个字段并没有在触发器中指定。同时注意，在触发器信息输出中有一个参数`sort=hitcount`，也没有在触发器中指定。原因是每个触发器都会隐式地记录每个条目的命中次数，称为`hitcount`。这个`hitcount`信息会在输出中显式显示，并且如果没有用户指定排序参数，则将其作为默认排序字段。
值 'hitcount' 可以在 'values' 参数中代替显式的值，如果你不需要特定字段的总和，并且主要关心命中频率。

要关闭 hist 触发器，只需在命令历史中调用触发器并重新执行它，在前面加上一个 '!'：

```
# echo '!hist:key=call_site:val=bytes_req' > \
       /sys/kernel/tracing/events/kmem/kmalloc/trigger
```

最后，请注意上面输出中的 call_site 并不是非常有用。它是一个地址，但通常地址是以十六进制显示的。要将数字字段作为十六进制值显示，只需在触发器中的字段名后加上 '.hex' ：

```
# echo 'hist:key=call_site.hex:val=bytes_req' > \
       /sys/kernel/tracing/events/kmem/kmalloc/trigger

# cat /sys/kernel/tracing/events/kmem/kmalloc/hist
# 触发器信息: hist:keys=call_site.hex:vals=bytes_req:sort=hitcount:size=2048 [active]

{ call_site: ffffffffa026b291 } hitcount:          1  bytes_req:        433
{ call_site: ffffffffa07186ff } hitcount:          1  bytes_req:        176
{ call_site: ffffffff811ae721 } hitcount:          1  bytes_req:      16384
{ call_site: ffffffff811c5134 } hitcount:          1  bytes_req:          8
{ call_site: ffffffffa04a9ebb } hitcount:          1  bytes_req:        511
{ call_site: ffffffff8122e0a6 } hitcount:          1  bytes_req:         12
{ call_site: ffffffff8107da84 } hitcount:          1  bytes_req:        152
{ call_site: ffffffff812d8246 } hitcount:          1  bytes_req:         24
{ call_site: ffffffff811dc1e5 } hitcount:          3  bytes_req:        144
{ call_site: ffffffffa02515e8 } hitcount:          3  bytes_req:        648
{ call_site: ffffffff81258159 } hitcount:          3  bytes_req:        144
{ call_site: ffffffff811c80f4 } hitcount:          4  bytes_req:        544

{ call_site: ffffffffa06c7646 } hitcount:        106  bytes_req:       8024
{ call_site: ffffffffa06cb246 } hitcount:        132  bytes_req:      31680
{ call_site: ffffffffa06cef7a } hitcount:        132  bytes_req:       2112
{ call_site: ffffffff8137e399 } hitcount:        132  bytes_req:      23232
{ call_site: ffffffffa06c941c } hitcount:        185  bytes_req:     171360
{ call_site: ffffffffa06f2a66 } hitcount:        185  bytes_req:      26640
{ call_site: ffffffffa036a70e } hitcount:        265  bytes_req:      10600
{ call_site: ffffffff81325447 } hitcount:        292  bytes_req:        584
{ call_site: ffffffffa072da3c } hitcount:        446  bytes_req:      60656
{ call_site: ffffffffa036b1f2 } hitcount:        526  bytes_req:      29456
{ call_site: ffffffffa0099c06 } hitcount:       1780  bytes_req:      35600

总计：
    命中数：4775
    条目数：46
    被丢弃：0

即使这样也只是稍微更有用一些——虽然十六进制值看起来更像地址，但在查看文本地址时用户通常更感兴趣的是相应的符号。要将地址作为符号值显示，只需在触发器中的字段名后加上 '.sym' 或 '.sym-offset' ：

```
# echo 'hist:key=call_site.sym:val=bytes_req' > \
       /sys/kernel/tracing/events/kmem/kmalloc/trigger

# cat /sys/kernel/tracing/events/kmem/kmalloc/hist
# 触发器信息: hist:keys=call_site.sym:vals=bytes_req:sort=hitcount:size=2048 [active]

{ call_site: [ffffffff810adcb9] syslog_print_all                              } hitcount:          1  bytes_req:       1024
{ call_site: [ffffffff8154bc62] usb_control_msg                               } hitcount:          1  bytes_req:          8
{ call_site: [ffffffffa00bf6fe] hidraw_send_report [hid]                      } hitcount:          1  bytes_req:          7
{ call_site: [ffffffff8154acbe] usb_alloc_urb                                 } hitcount:          1  bytes_req:        192
{ call_site: [ffffffffa00bf1ca] hidraw_report_event [hid]                     } hitcount:          1  bytes_req:          7
{ call_site: [ffffffff811e3a25] __seq_open_private                            } hitcount:          1  bytes_req:         40
{ call_site: [ffffffff8109524a] alloc_fair_sched_group                        } hitcount:          2  bytes_req:        128
{ call_site: [ffffffff811febd5] fsnotify_alloc_group                          } hitcount:          2  bytes_req:        528
{ call_site: [ffffffff81440f58] __tty_buffer_request_room                     } hitcount:          2  bytes_req:       2624
{ call_site: [ffffffff81200ba6] inotify_new_group                             } hitcount:          2  bytes_req:         96
{ call_site: [ffffffffa05e19af] ieee80211_start_tx_ba_session [mac80211]      } hitcount:          2  bytes_req:        464
{ call_site: [ffffffff81672406] tcp_get_metrics                               } hitcount:          2  bytes_req:        304
{ call_site: [ffffffff81097ec2] alloc_rt_sched_group                          } hitcount:          2  bytes_req:        128
{ call_site: [ffffffff81089b05] sched_create_group                            } hitcount:          2  bytes_req:       1424

{ call_site: [ffffffffa04a580c] intel_crtc_page_flip [i915]                   } hitcount:       1185  bytes_req:     123240
{ call_site: [ffffffffa0287592] drm_mode_page_flip_ioctl [drm]                } hitcount:       1185  bytes_req:     104280
{ call_site: [ffffffffa04c4a3c] intel_plane_duplicate_state [i915]            } hitcount:       1402  bytes_req:     190672
{ call_site: [ffffffff812891ca] ext4_find_extent                              } hitcount:       1518  bytes_req:     146208
{ call_site: [ffffffffa029070e] drm_vma_node_allow [drm]                      } hitcount:       1746  bytes_req:      69840
{ call_site: [ffffffffa045e7c4] i915_gem_do_execbuffer.isra.23 [i915]         } hitcount:       2021  bytes_req:     792312
{ call_site: [ffffffffa02911f2] drm_modeset_lock_crtc [drm]                   } hitcount:       2592  bytes_req:     145152
{ call_site: [ffffffffa0489a66] intel_ring_begin [i915]                       } hitcount:       2629  bytes_req:     378576
{ call_site: [ffffffffa046041c] i915_gem_execbuffer2 [i915]                   } hitcount:       2629  bytes_req:    3783248
{ call_site: [ffffffff81325607] apparmor_file_alloc_security                  } hitcount:       5192  bytes_req:      10384
{ call_site: [ffffffffa00b7c06] hid_report_raw_event [hid]                    } hitcount:       5529  bytes_req:     110584
{ call_site: [ffffffff8131ebf7] aa_alloc_task_context                         } hitcount:      21943  bytes_req:     702176
{ call_site: [ffffffff8125847d] ext4_htree_store_dirent                       } hitcount:      55759  bytes_req:    5074265

总计：
    命中数：109928
    条目数：71
    被丢弃：0

由于默认排序键是 'hitcount'，上述输出按递增的 hitcount 显示 call_site 列表，因此在底部我们可以看到运行期间调用次数最多的函数。如果我们想根据请求的字节数而不是调用次数查看顶级 kmalloc 调用者，并且希望顶级调用者出现在顶部，我们可以使用 'sort' 参数以及 'descending' 修饰符：

```
# echo 'hist:key=call_site.sym:val=bytes_req:sort=bytes_req.descending' > \
       /sys/kernel/tracing/events/kmem/kmalloc/trigger

# cat /sys/kernel/tracing/events/kmem/kmalloc/hist
# 触发器信息: hist:keys=call_site.sym:vals=bytes_req:sort=bytes_req.descending:size=2048 [active]

{ call_site: [ffffffffa046041c] i915_gem_execbuffer2 [i915]                   } hitcount:       2186  bytes_req:    3397464
{ call_site: [ffffffffa045e7c4] i915_gem_do_execbuffer.isra.23 [i915]         } hitcount:       1790  bytes_req:     712176
{ call_site: [ffffffff8125847d] ext4_htree_store_dirent                       } hitcount:       8132  bytes_req:     513135
{ call_site: [ffffffff811e2a1b] seq_buf_alloc                                 } hitcount:        106  bytes_req:     440128
{ call_site: [ffffffffa0489a66] intel_ring_begin [i915]                       } hitcount:       2186  bytes_req:     314784
{ call_site: [ffffffff812891ca] ext4_find_extent                              } hitcount:       2174  bytes_req:     208992
{ call_site: [ffffffff811ae8e1] __kmalloc                                     } hitcount:          8  bytes_req:     131072
{ call_site: [ffffffffa04c4a3c] intel_plane_duplicate_state [i915]            } hitcount:        859  bytes_req:     116824
{ call_site: [ffffffffa02911f2] drm_modeset_lock_crtc [drm]                   } hitcount:       1834  bytes_req:     102704
{ call_site: [ffffffffa04a580c] intel_crtc_page_flip [i915]                   } hitcount:        972  bytes_req:     101088
{ call_site: [ffffffffa0287592] drm_mode_page_flip_ioctl [drm]                } hitcount:        972  bytes_req:      85536
{ call_site: [ffffffffa00b7c06] hid_report_raw_event [hid]                    } hitcount:       3333  bytes_req:      66664
{ call_site: [ffffffff8137e559] sg_kmalloc                                    } hitcount:        209  bytes_req:      61632
```
