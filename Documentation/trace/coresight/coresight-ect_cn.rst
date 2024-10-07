SPDX 许可声明标识符: GPL-2.0

=============================================
CoreSight 嵌入式交叉触发器 (CTI & CTM)
=============================================

    :作者:   Mike Leach <mike.leach@linaro.org>
    :日期:   2019年11月

硬件描述
--------------------

CoreSight 交叉触发接口 (CTI) 是一个硬件设备，它接收和发送称为触发器的单个输入和输出硬件信号，并通过交叉触发矩阵 (CTM) 将这些信号与其他设备相连，以便在设备之间传播事件。例如：

```
0000000  in_trigs  :::::::
0 C   0----------->:     :             +======>(其他 CTI 通道 I/O)
0  P  0<-----------:     :             v
0   U 0  out_trigs :     : Channels  *****      :::::::
0000000            : CTI :<=========>*CTM*<====>: CTI :---+
 #######  in_trigs  :     : (id 0-3)  *****      :::::::   v
 # ETM #----------->:     :                         ^   #######
 #     #<-----------:     :                         +---# ETR #
 ####### out_trigs  :::::::                             #######
```

CTI 驱动程序允许编程 CTI 以将触发器连接到通道。当输入触发器激活时，所连接的通道也会激活。任何与此通道相连的输出触发器也会被激活。激活的通道通过 CTM 传播到其他 CTI，从而激活连接的输出触发器（除非被 CTI 通道门控过滤）。也可以通过系统软件直接编程 CTI 寄存器来激活通道。

CTI 设备由系统注册并与 CPU 和/或其他跟踪数据路径上的 CoreSight 设备相关联。当这些设备启用时，连接的 CTI 也会被启用。默认情况下/上电时，CTI 没有编程的触发器/通道关联，因此直到明确编程前不会影响系统。

CTI 和设备之间的硬件触发器连接取决于具体实现，除非 CPU/ETM 组合是 v8 架构，在这种情况下，连接具有架构定义的标准布局。硬件触发信号还可以连接到非 CoreSight 设备（例如 UART），或者作为硬件 I/O 线路传播出芯片。

所有 CTI 设备都与一个 CTM 相关联。在许多系统中，会有一个有效的单一 CTM（一个 CTM 或多个相互连接的 CTM），但也有可能系统会有不通过 CTM 相互连接的 CTI+CTM 网络。在这种系统中，会声明一个 CTM 索引来关联通过特定 CTM 相互连接的 CTI 设备。

sysfs 文件和目录
--------------------------

CTI 设备出现在现有的 CoreSight 总线上，与其它 CoreSight 设备并列存在：

```
>$ ls /sys/bus/coresight/devices
cti_cpu0  cti_cpu2  cti_sys0  etm0  etm2  funnel0  replicator0  tmc_etr0
cti_cpu1  cti_cpu3  cti_sys1  etm1  etm3  funnel1  tmc_etf0     tpiu0
```

名为 `cti_cpu<N>` 的 CTI 与 CPU 及其使用的任何 ETM 相关联。`cti_sys<N>` CTI 是通用系统基础设施 CTI，可以与其它 CoreSight 设备或能够生成或使用触发信号的其它系统硬件相关联。

```
>$ ls /sys/bus/coresight/devices/etm0/cti_cpu0
channels  ctmid  enable  nr_trigger_cons mgmt  power powered  regs
connections subsystem triggers0 triggers1  uevent
```

*关键文件项包括：*
   * `enable`：启用/禁用 CTI。读取以确定当前状态。
如果显示为启用 (1)，但 `powered` 显示未供电 (0)，则启用表示在设备供电时请求启用。
* ``ctmid``：关联的CTM - 仅在系统具有多个未互连的CTI+CTM集群时相关
* ``nr_trigger_cons``：总连接数 - 触发器<triggers<N>>目录
* ``powered``：读取以确定CTI当前是否已上电
*子目录：-*
   * ``triggers<N>``：包含单个连接的触发器列表
* ``channels``：包含通道API - CTI的主要编程接口
* ``regs``：提供对原始可编程CTI寄存器的访问
* ``mgmt``：标准CoreSight管理寄存器
* ``connections``：链接到连接的*CoreSight*设备。链接的数量可以是0到``nr_trigger_cons``。实际数量由此目录中的``nr_links``给出

triggers<N> 目录
~~~~~~~~~~~~~~~~~~~~~~~

单个触发器连接信息。这描述了CoreSight和非CoreSight连接的触发信号
每个triggers目录都有一组参数，用于描述该连接的触发器
* ``name``：连接名称
* ``in_signals``：此连接中使用的输入触发信号索引
* ``in_types``：输入信号的功能类型
* ``out_signals``：此连接的输出触发信号
* ``out_types``：输出信号的功能类型

例如：

    >$ ls ./cti_cpu0/triggers0/
    in_signals  in_types  name  out_signals  out_types
    >$ cat ./cti_cpu0/triggers0/name
    cpu0
    >$ cat ./cti_cpu0/triggers0/out_signals
    0-2
    >$ cat ./cti_cpu0/triggers0/out_types
    pe_edbgreq pe_dbgrestart pe_ctiirq
    >$ cat ./cti_cpu0/triggers0/in_signals
    0-1
    >$ cat ./cti_cpu0/triggers0/in_types
    pe_dbgtrigger pe_pmuirq

如果一个连接在输入（'in'）或输出（'out'）触发信号中没有信号，则这些参数将被省略。

通道 API 目录
~~~~~~~~~~~~~~

这提供了一种简单的方法来将触发器附加到通道，而无需直接操作 `regs` 子目录元素所需的多个寄存器操作。
一些文件提供了这种 API：

   >$ ls ./cti_sys0/channels/
   chan_clear         chan_inuse      chan_xtrigs_out     trigin_attach
   chan_free          chan_pulse      chan_xtrigs_reset   trigin_detach
   chan_gate_disable  chan_set        chan_xtrigs_sel     trigout_attach
   chan_gate_enable   chan_xtrigs_in  trig_filter_enable  trigout_detach
   trigout_filtered

对这些元素的大多数访问形式如下：

  echo <chan> [<trigger>] > /<device_path>/<operation>

其中可选的 <trigger> 只在进行 trigXX_attach | detach 操作时需要。

例如：

   >$ echo 0 1 > ./cti_sys0/channels/trigout_attach
   >$ echo 0 > ./cti_sys0/channels/chan_set

将 trigout(1) 附加到 channel(0)，然后激活 channel(0)，从而在 cti_sys0.trigout(1) 上生成一个设置状态。

*API 操作*

   * ``trigin_attach, trigout_attach``：将一个通道附加到触发信号
* ``trigin_detach, trigout_detach``：将一个通道从触发信号上分离
* ``chan_set``：设置通道 - 设置状态将在 CTM 中传播到其他连接的设备
* ``chan_clear``: 清除通道
* ``chan_pulse``: 为单个 CoreSight 时钟周期设置通道
* ``chan_gate_enable``: 写入操作将 CTI 门控设置为传播（启用）到其他设备的通道。此操作需要一个通道编号。CTI 门控在上电时默认对所有通道启用。读取以列出当前门控上已启用的通道
* ``chan_gate_disable``: 写入通道编号以禁用该通道的门控
* ``chan_inuse``: 显示当前连接到任何信号的通道
* ``chan_free``: 显示没有连接信号的通道
* ``chan_xtrigs_sel``: 写入一个通道编号以选择要查看的通道，读取以显示所选的通道编号
* ``chan_xtrigs_in``: 读取以显示连接到所选查看通道的输入触发器
* ``chan_xtrigs_out``: 读取以显示连接到所选查看通道的输出触发器
* ``trig_filter_enable``: 默认启用，禁用以允许设置潜在危险的输出信号
* ``trigout_filtered``: 如果启用了过滤功能 ``trig_filter_enable``，则阻止设置的触发输出信号。其中一个用途是防止意外的 ``EDBGREQ`` 信号停止核心运行
* ``chan_xtrigs_reset``：写入1以清除所有通道/触发器编程
将设备硬件重置为默认状态
下面的示例将输入触发器索引1连接到通道2，并将输出触发器索引6连接到同一通道。然后使用相应的sysfs属性检查通道/触发器连接的状态。
这些设置意味着如果输入触发器1或通道2中的任何一个变为激活状态，则触发器输出6也会变为激活状态。接下来我们启用CTI，并使用软件通道控制来激活通道2。我们可以在``choutstatus``寄存器中看到激活的通道，在``trigoutstatus``寄存器中看到激活的信号。最后，清除通道会移除这种关联。
例如：

   .../cti_sys0/channels# echo 2 1 > trigin_attach
   .../cti_sys0/channels# echo 2 6 > trigout_attach
   .../cti_sys0/channels# cat chan_free
   0-1,3
   .../cti_sys0/channels# cat chan_inuse
   2
   .../cti_sys0/channels# echo 2 > chan_xtrigs_sel
   .../cti_sys0/channels# cat chan_xtrigs_trigin
   1
   .../cti_sys0/channels# cat chan_xtrigs_trigout
   6
   .../cti_sys0/# echo 1 > enable
   .../cti_sys0/channels# echo 2 > chan_set
   .../cti_sys0/channels# cat ../regs/choutstatus
   0x4
   .../cti_sys0/channels# cat ../regs/trigoutstatus
   0x40
   .../cti_sys0/channels# echo 2 > chan_clear
   .../cti_sys0/channels# cat ../regs/trigoutstatus
   0x0
   .../cti_sys0/channels# cat ../regs/choutstatus
   0x0
