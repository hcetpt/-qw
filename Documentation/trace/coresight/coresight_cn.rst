===============================
Coresight - 带硬件辅助追踪的ARM
===============================

   :作者:   Mathieu Poirier <mathieu.poirier@linaro.org>
   :日期:   2014年9月11日

介绍
------------

Coresight 是一组技术的总称，允许调试基于ARM的SoC。它包括JTAG和硬件辅助追踪的解决方案。本文档关注的是后者。
当处理具有多个SoC以及其他组件（如GPU和DMA引擎）的系统时，硬件辅助追踪变得越来越有用。ARM通过不同的组件开发了一种硬件辅助追踪解决方案，在设计阶段加入这些组件以满足特定的追踪需求。
这些组件通常分为源、链接和接收器，并且（通常）通过AMBA总线发现。
“源”根据用户配置的追踪场景生成压缩流，表示处理器指令路径。从那里，该流通过Coresight系统（通过ATB总线），使用连接源到接收器的链接。接收器作为Coresight实现的终点，要么将压缩流存储在内存缓冲区中，要么创建一个接口与外部世界通信，以便数据可以传输到主机而不必担心填满板载Coresight内存缓冲区。
典型的Coresight系统看起来像这样：

```
*****************************************************************
**************************** AMBA AXI  ****************************===||
*****************************************************************    ||
        ^                    ^                            |            ||
        |                    |                            *            **
     0000000    :::::     0000000    :::::    :::::    @@@@@@@    ||||||||||||
     0 CPU 0<-->: C :     0 CPU 0<-->: C :    : C :    @ STM @    || 系统 ||
  |->0000000    : T :  |->0000000    : T :    : T :<--->@@@@@     || 内存 ||
  |  #######<-->: I :  |  #######<-->: I :    : I :      @@@<-|   ||||||||||||
  |  # ETM #    :::::  |  # PTM #    :::::    :::::       @   |
  |   #####      ^ ^   |   #####      ^ !      ^ !        .   |   |||||||||
  | |->###       | !   | |->###       | !      | !        .   |   || DAP ||
  | |   #        | !   | |   #        | !      | !        .   |   |||||||||
  | |   .        | !   | |   .        | !      | !        .   |      |  |
  | |   .        | !   | |   .        | !      | !        .   |      |  *
  | |   .        | !   | |   .        | !      | !        .   |      | SWD/
  | |   .        | !   | |   .        | !      | !        .   |      | JTAG
*****************************************************************<-|
 *************************** AMBA Debug APB ************************
*****************************************************************
   |    .          !         .          !        !        .    |
   |    .          *         .          *        *        .    |
*****************************************************************
 ****************** Cross Trigger Matrix (CTM) *******************
*****************************************************************
   |    .     ^              .                            .    |
   |    *     !              *                            *    |
*****************************************************************
 ****************** AMBA Advanced Trace Bus (ATB) ******************
*****************************************************************
   |          !                        ===============         |
   |          *                         ===== F =====<---------|
   |   :::::::::                         ==== U ====
   |-->:: CTI ::<!!                       === N ===
   |   :::::::::  !                        == N ==
   |    ^         *                        == E ==
   |    !  &&&&&&&&&       IIIIIII         == L ==
   |------>&& ETB &&<......II     I        =======
   |    !  &&&&&&&&&       II     I
|    !                    I     I
|    !                    I REP I<.........
|    !                    I     I
   |    !!>&&&&&&&&&       II     I           * 来源：ARM有限公司
|------>& TPIU  &<......II    I            DAP = 调试访问端口
           &&&&&&&&&       IIIIIII            ETM = 嵌入式追踪宏单元
               ;                              PTM = 程序追踪宏单元
               ;                              CTI = 交叉触发接口
               *                              ETB = 嵌入式追踪缓冲区
          追踪端口                           TPIU= 追踪端口接口单元
                                              SWD = 串行线调试

虽然目标上的组件配置是通过APB总线完成的，但所有追踪数据都是通过ATB总线带外传输的。CTM提供了一种方法来聚合和分配Coresight组件之间的信号。
Coresight框架提供了一个中心点来表示、配置和管理平台上的Coresight设备。这一初步实现集中在基本的追踪功能上，启用了ETM/PTM、漏斗、复制器、TMC、TPIU和ETB等组件。未来的工作将启用更复杂的IP块，如STM和CTI。
缩写词和分类
---------------------------

缩写词：

PTM:
    程序跟踪宏单元
ETM:
    嵌入式跟踪宏单元
STM:
    系统跟踪宏单元
ETB:
    嵌入式跟踪缓冲区
ITM:
    仪器跟踪宏单元
TPIU:
     跟踪端口接口单元
TMC-ETR:
        配置为嵌入式跟踪路由器的跟踪内存控制器
TMC-ETF:
        配置为嵌入式跟踪FIFO的跟踪内存控制器
CTI:
    交叉触发接口

分类：

源设备：
   ETMv3.x ETMv4, PTMv1.0, PTMv1.1, STM, STM500, ITM
链路设备：
   漏斗，复制器（智能或非智能），TMC-ETR
接收设备：
   ETBv1.0, ETB1.1, TPIU, TMC-ETF
其他：
   CTI

设备树绑定
--------------------

详细信息请参见 `Documentation/devicetree/bindings/arm/arm,coresight-*.yaml`
截至本文档撰写时，ITM、STM 和 CTI 的驱动程序尚未提供，但随着解决方案的成熟，预计会添加。
框架与实现
----------------------------

Coresight框架提供了一个中心点来表示、配置和管理平台上的Coresight设备。任何符合Coresight规范的设备只要使用正确的API即可注册到该框架中：

.. c:function:: struct coresight_device *coresight_register(struct coresight_desc *desc);
.. c:function:: void coresight_unregister(struct coresight_device *csdev);

注册函数需要一个 `struct coresight_desc *desc` 参数，并将设备注册到核心框架中。注销函数则需要一个在注册时获得的 `struct coresight_device *csdev` 引用。

如果注册过程顺利进行，新设备将会出现在 `/sys/bus/coresight/devices` 目录下，如TC2平台所示：

```
root:~# ls /sys/bus/coresight/devices/
replicator  20030000.tpiu    2201c000.ptm  2203c000.etm  2203e000.etm
20010000.etb         20040000.funnel  2201d000.ptm  2203d000.etm
root:~#
```

这些函数需要一个 `struct coresight_device` 类型的参数，其结构如下：

```c
struct coresight_desc {
    enum coresight_dev_type type;
    struct coresight_dev_subtype subtype;
    const struct coresight_ops *ops;
    struct coresight_platform_data *pdata;
    struct device *dev;
    const struct attribute_group **groups;
};
```

`coresight_dev_type` 用于标识设备的类型，例如源设备、链路设备或接收设备；而 `coresight_dev_subtype` 进一步描述了该类型。`struct coresight_ops` 是必需的，它告诉框架如何执行与组件相关的基础操作。每个组件有一套不同的需求，因此提供了 `struct coresight_ops_sink`、`struct coresight_ops_link` 和 `struct coresight_ops_source`。

下一个字段 `struct coresight_platform_data *pdata` 可通过调用 `of_get_coresight_platform_data()` 在驱动程序的 `_probe` 函数中获取，而 `struct device *dev` 则从 `amba_device` 中获取设备引用：

```c
static int etm_probe(struct amba_device *adev, const struct amba_id *id)
{
    ...
    drvdata->dev = &adev->dev;
    ...
}
```

特定类型的设备（源设备、链路设备或接收设备）具有一组通用的操作（见 `struct coresight_ops`）。`**groups` 是一组与该组件相关的sysfs条目，这些条目用于控制特定于该组件的操作。“实现定义”的自定义可以通过这些条目访问和控制。

设备命名方案
--------------------

在 “coresight” 总线上出现的设备名称与其父设备相同，即在AMBA总线或平台总线上出现的真实设备。
因此，这些名称是基于Linux Open Firmware层命名约定的，该命名约定遵循设备的基本物理地址，后跟设备类型。例如：

    root:~# ls /sys/bus/coresight/devices/
     20010000.etf  20040000.funnel      20100000.stm     22040000.etm
     22140000.etm  230c0000.funnel      23240000.etm     20030000.tpiu
     20070000.etr  20120000.replicator  220c0000.funnel
     23040000.etm  23140000.etm         23340000.etm

然而，随着ACPI支持的引入，实际设备的名称变得有些晦涩难懂。因此，引入了一种新的命名方案，使用更通用的名字来表示设备类型。以下规则适用：

  1) 绑定到CPU的设备，其名称基于CPU的逻辑编号。
     例如，绑定到CPU0的ETM被命名为"etm0"。

  2) 其他所有设备遵循"<device_type_prefix>N"的模式，其中：
	<device_type_prefix> - 特定于设备类型的前缀
	N - 基于探测顺序分配的序号
例如，tmc_etf0, tmc_etr0, funnel0, funnel1

因此，在新方案下，设备可能显示为：

    root:~# ls /sys/bus/coresight/devices/
     etm0     etm1     etm2         etm3  etm4      etm5      funnel0
     funnel1  funnel2  replicator0  stm0  tmc_etf0  tmc_etr0  tpiu0

下面的一些示例可能会引用旧的命名方案，而一些则会引用新的方案，以确认你在系统上看到的情况并非意料之外。必须使用系统指定位置中出现的“名称”。

拓扑表示
-------------------

每个CoreSight组件都有一个`connections`目录，其中包含指向其他CoreSight组件的链接。这允许用户探索跟踪拓扑，并在较大的系统中确定给定源的最佳接收器。连接信息还可以用来确定哪些CTI设备与给定组件相连。此目录包含一个`nr_links`属性，详细说明了目录中的链接数量。
对于ETM源，在Juno平台上，例如`etm0`，典型布局如下：

  linaro-developer:~# ls -l /sys/bus/coresight/devices/etm0/connections
  <文件详情>  cti_cpu0 -> ../../../23020000.cti/cti_cpu0
  <文件详情>  nr_links
  <文件详情>  out:0 -> ../../../230c0000.funnel/funnel2

跟踪out端口到`funnel2`：

  linaro-developer:~# ls -l /sys/bus/coresight/devices/funnel2/connections
  <文件详情> in:0 -> ../../../23040000.etm/etm0
  <文件详情> in:1 -> ../../../23140000.etm/etm3
  <文件详情> in:2 -> ../../../23240000.etm/etm4
  <文件详情> in:3 -> ../../../23340000.etm/etm5
  <文件详情> nr_links
  <文件详情> out:0 -> ../../../20040000.funnel/funnel0

再次跟踪到`funnel0`：

  linaro-developer:~# ls -l /sys/bus/coresight/devices/funnel0/connections
  <文件详情> in:0 -> ../../../220c0000.funnel/funnel1
  <文件详情> in:1 -> ../../../230c0000.funnel/funnel2
  <文件详情> nr_links
  <文件详情> out:0 -> ../../../20010000.etf/tmc_etf0

找到第一个接收器`tmc_etf0`。它可以作为接收器收集数据，或作为链接进一步传播链路：

  linaro-developer:~# ls -l /sys/bus/coresight/devices/tmc_etf0/connections
  <文件详情> cti_sys0 -> ../../../20020000.cti/cti_sys0
  <文件详情> in:0 -> ../../../20040000.funnel/funnel0
  <文件详情> nr_links
  <文件详情> out:0 -> ../../../20150000.funnel/funnel4

通过`funnel4`：

  linaro-developer:~# ls -l /sys/bus/coresight/devices/funnel4/connections
  <文件详情> in:0 -> ../../../20010000.etf/tmc_etf0
  <文件详情> in:1 -> ../../../20140000.etf/tmc_etf1
  <文件详情> nr_links
  <文件详情> out:0 -> ../../../20120000.replicator/replicator0

再到一个`replicator0`：

  linaro-developer:~# ls -l /sys/bus/coresight/devices/replicator0/connections
  <文件详情> in:0 -> ../../../20150000.funnel/funnel4
  <文件详情> nr_links
  <文件详情> out:0 -> ../../../20030000.tpiu/tpiu0
  <文件详情> out:1 -> ../../../20070000.etr/tmc_etr0

到达链路中的最终接收器`tmc_etr0`：

  linaro-developer:~# ls -l /sys/bus/coresight/devices/tmc_etr0/connections
  <文件详情> cti_sys0 -> ../../../20020000.cti/cti_sys0
  <文件详情> in:0 -> ../../../20120000.replicator/replicator0
  <文件详情> nr_links

如下面所述，当使用sysfs时，启用一个接收器和一个源就足以成功进行跟踪。框架将正确启用所有必要的中间链接。
注意：`cti_sys0`出现在上面两个连接列表中。
CTI可以连接多个设备，并通过CTM形成星型拓扑。有关更多详细信息，请参阅(文档/trace/coresight/coresight-ect.rst)[#fourth]。
查看这个设备，我们看到有4个连接：

  linaro-developer:~# ls -l /sys/bus/coresight/devices/cti_sys0/connections
  <文件详情> nr_links
  <文件详情> stm0 -> ../../../20100000.stm/stm0
  <文件详情> tmc_etf0 -> ../../../20010000.etf/tmc_etf0
  <文件详情> tmc_etr0 -> ../../../20070000.etr/tmc_etr0
  <文件详情> tpiu0 -> ../../../20030000.tpiu/tpiu0

如何使用跟踪模块
-----------------------------

有两种方式使用Coresight框架：

1. 使用perf命令行工具
2. 直接通过sysFS接口与Coresight设备交互

首选前者，因为使用sysFS接口需要对Coresight硬件有深入的理解。以下各节提供了使用这两种方法的详细信息。
使用sysFS接口
~~~~~~~~~~~~~~~~~~~~~~~~~

在开始收集跟踪数据之前，需要识别一个coresight接收器。
没有任何限制规定在任何给定时刻可以启用多少个接收器（或源）。
作为通用操作，所有与接收器类相关的设备在sysfs中都有一个“active”条目：

    root:/sys/bus/coresight/devices# ls
    replicator  20030000.tpiu    2201c000.ptm  2203c000.etm  2203e000.etm
    20010000.etb         20040000.funnel  2201d000.ptm  2203d000.etm
    root:/sys/bus/coresight/devices# ls 20010000.etb
    enable_sink  status  trigger_cntr
    root:/sys/bus/coresight/devices# echo 1 > 20010000.etb/enable_sink
    root:/sys/bus/coresight/devices# cat 20010000.etb/enable_sink
    1
    root:/sys/bus/coresight/devices#

启动时，当前的etm3x驱动程序将使用"_stext"和"_etext"配置第一个地址比较器，基本上会跟踪落在该范围内的任何指令。因此，“启用”一个源将立即触发跟踪捕获：

    root:/sys/bus/coresight/devices# echo 1 > 2201c000.ptm/enable_source
    root:/sys/bus/coresight/devices# cat 2201c000.ptm/enable_source
    1
    root:/sys/bus/coresight/devices# cat 20010000.etb/status
    Depth:          0x2000
    Status:         0x1
    RAM read ptr:   0x0
    RAM wrt ptr:    0x19d3   <----- 写指针正在移动
    Trigger cnt:    0x0
    Control:        0x1
    Flush status:   0x0
    Flush ctrl:     0x2001
    root:/sys/bus/coresight/devices#

停止跟踪数据收集的方式相同：

    root:/sys/bus/coresight/devices# echo 0 > 2201c000.ptm/enable_source
    root:/sys/bus/coresight/devices#

可以从/dev直接获取ETB缓冲区的内容：

    root:/sys/bus/coresight/devices# dd if=/dev/20010000.etb \
    of=~/cstrace.bin
    64+0 records in
    64+0 records out
    32768 bytes (33 kB) copied, 0.00125258 s, 26.2 MB/s
    root:/sys/bus/coresight/devices#

文件cstrace.bin可以使用"ptm2human"、DS-5或Trace32进行解压。以下是一个实验性循环的DS-5输出示例，该循环将变量递增到某个值。这个例子虽然简单，但展示了coresight提供的丰富可能性：

    Info                                    Tracing enabled
    Instruction     106378866       0x8026B53C      E52DE004        false   PUSH     {lr}
    Instruction     0       0x8026B540      E24DD00C        false   SUB      sp,sp,#0xc
    Instruction     0       0x8026B544      E3A03000        false   MOV      r3,#0
    Instruction     0       0x8026B548      E58D3004        false   STR      r3,[sp,#4]
    Instruction     0       0x8026B54C      E59D3004        false   LDR      r3,[sp,#4]
    Instruction     0       0x8026B550      E3530004        false   CMP      r3,#4
    Instruction     0       0x8026B554      E2833001        false   ADD      r3,r3,#1
    Instruction     0       0x8026B558      E58D3004        false   STR      r3,[sp,#4]
    Instruction     0       0x8026B55C      DAFFFFFA        true    BLE      {pc}-0x10 ; 0x8026b54c
    Timestamp                                       Timestamp: 17106715833
    Instruction     319     0x8026B54C      E59D3004        false   LDR      r3,[sp,#4]
    Instruction     0       0x8026B550      E3530004        false   CMP      r3,#4
    Instruction     0       0x8026B554      E2833001        false   ADD      r3,r3,#1
    Instruction     0       0x8026B558      E58D3004        false   STR      r3,[sp,#4]
    Instruction     0       0x8026B55C      DAFFFFFA        true    BLE      {pc}-0x10 ; 0x8026b54c
    Instruction     9       0x8026B54C      E59D3004        false   LDR      r3,[sp,#4]
    Instruction     0       0x8026B550      E3530004        false   CMP      r3,#4
    Instruction     0       0x8026B554      E2833001        false   ADD      r3,r3,#1
    Instruction     0       0x8026B558      E58D3004        false   STR      r3,[sp,#4]
    Instruction     0       0x8026B55C      DAFFFFFA        true    BLE      {pc}-0x10 ; 0x8026b54c
    Instruction     7       0x8026B54C      E59D3004        false   LDR      r3,[sp,#4]
    Instruction     0       0x8026B550      E3530004        false   CMP      r3,#4
    Instruction     0       0x8026B554      E2833001        false   ADD      r3,r3,#1
    Instruction     0       0x8026B558      E58D3004        false   STR      r3,[sp,#4]
    Instruction     0       0x8026B55C      DAFFFFFA        true    BLE      {pc}-0x10 ; 0x8026b54c
    Instruction     7       0x8026B54C      E59D3004        false   LDR      r3,[sp,#4]
    Instruction     0       0x8026B550      E3530004        false   CMP      r3,#4
    Instruction     0       0x8026B554      E2833001        false   ADD      r3,r3,#1
    Instruction     0       0x8026B558      E58D3004        false   STR      r3,[sp,#4]
    Instruction     0       0x8026B55C      DAFFFFFA        true    BLE      {pc}-0x10 ; 0x8026b54c
    Instruction     10      0x8026B54C      E59D3004        false   LDR      r3,[sp,#4]
    Instruction     0       0x8026B550      E3530004        false   CMP      r3,#4
    Instruction     0       0x8026B554      E2833001        false   ADD      r3,r3,#1
    Instruction     0       0x8026B558      E58D3004        false   STR      r3,[sp,#4]
    Instruction     0       0x8026B55C      DAFFFFFA        true    BLE      {pc}-0x10 ; 0x8026b54c
    Instruction     6       0x8026B560      EE1D3F30        false   MRC      p15,#0x0,r3,c13,c0,#1
    Instruction     0       0x8026B564      E1A0100D        false   MOV      r1,sp
    Instruction     0       0x8026B568      E3C12D7F        false   BIC      r2,r1,#0x1fc0
    Instruction     0       0x8026B56C      E3C2203F        false   BIC      r2,r2,#0x3f
    Instruction     0       0x8026B570      E59D1004        false   LDR      r1,[sp,#4]
    Instruction     0       0x8026B574      E59F0010        false   LDR      r0,[pc,#16] ; [0x8026B58C] = 0x80550368
    Instruction     0       0x8026B578      E592200C        false   LDR      r2,[r2,#0xc]
    Instruction     0       0x8026B57C      E59221D0        false   LDR      r2,[r2,#0x1d0]
    Instruction     0       0x8026B580      EB07A4CF        true    BL       {pc}+0x1e9344 ; 0x804548c4
    Info                                    Tracing enabled
    Instruction     13570831        0x8026B584      E28DD00C        false   ADD      sp,sp,#0xc
    Instruction     0       0x8026B588      E8BD8000        true    LDM      sp!,{pc}
    Timestamp                                       Timestamp: 17107041535

使用perf框架
~~~~~~~~~~~~~~~~~~~~

Coresight跟踪器使用perf框架的性能监控单元（PMU）抽象表示。因此，perf框架负责根据进程的兴趣时间来控制何时启用跟踪。当系统中配置了Coresight PMU时，使用perf命令行工具查询时将会列出这些PMU：

	linaro@linaro-nano:~$ ./perf list pmu

		List of pre-defined events (to be used in -e):

		cs_etm//                                    [Kernel PMU event]

	linaro@linaro-nano:~$

无论系统中有多少个跟踪器（通常等于处理器核心的数量），"cs_etm" PMU只会被列出一次。
一个Coresight PMU与其他PMU一样工作，即PMU的名称会与斜线‘/’内的配置选项一起列出。由于一个Coresight系统通常会有多个接收器，因此需要指定要使用的接收器名称作为事件选项。
在较新的内核版本中，可用的接收器会在sysFS下（$SYSFS）/bus/event_source/devices/cs_etm/sinks/中列出：

	root@localhost:/sys/bus/event_source/devices/cs_etm/sinks# ls
	tmc_etf0  tmc_etr0  tpiu0

在较旧的内核版本中，这可能需要从coresight设备列表中找到，这些设备位于（$SYSFS）/bus/coresight/devices/下：

	root:~# ls /sys/bus/coresight/devices/
	 etm0     etm1     etm2         etm3  etm4      etm5      funnel0
	 funnel1  funnel2  replicator0  stm0  tmc_etf0  tmc_etr0  tpiu0
	root@linaro-nano:~# perf record -e cs_etm/@tmc_etr0/u --per-thread program

如上一节“设备命名方案”所述，设备名称可能与上述示例中的不同。必须使用sysFS下显示的设备名称。
斜线‘/’内的语法很重要。‘@’字符告诉解析器即将指定一个接收器，并且这是用于跟踪会话的接收器。
关于上述内容和其他如何使用perf工具与Coresight结合使用的示例，可以在openCSD gitHub仓库的"HOWTO.md"文件中找到。

高级perf框架用法
-----------------------------

使用perf工具进行AutoFDO分析
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

perf可用于记录和分析程序的跟踪数据。
可以使用'perf record'与cs_etm事件记录执行情况，并指定要记录到的接收器名称，例如：

    perf record -e cs_etm/@tmc_etr0/u --per-thread

可以使用'perf report'和'perf script'命令来分析执行情况，从指令跟踪合成指令和分支事件。
`perf inject` 可用于将跟踪数据替换为合成事件。
`--itrace` 选项控制合成事件的类型和频率（参见 `perf` 文档）。
请注意，目前仅支持 64 位程序；需要进一步的工作来支持 32 位 Arm 程序的指令解码。

跟踪 PID
~~~~~~~~~~~

内核可以构建为将 PID 值写入 PE ContextID 寄存器。对于在 EL1 运行的内核，PID 存储在 CONTEXTIDR_EL1 中。PE 可能实现了 Arm 虚拟化主机扩展（VHE），在这种情况下内核可以在 EL2 上作为虚拟化主机运行；此时，PID 值存储在 CONTEXTIDR_EL2 中。

`perf` 提供了 PMU 格式，这些格式配置 ETM 将这些值插入到跟踪数据中；PMU 格式定义如下：

  - `"contextid1"`：在 EL1 内核和 EL2 内核上都可用。当内核在 EL1 运行时，`"contextid1"` 启用 PID 跟踪；当内核在 EL2 运行时，这启用对来宾应用程序的 PID 跟踪。
  - `"contextid2"`：仅在内核在 EL2 运行时可用。选择后，启用 EL2 内核上的 PID 跟踪。
  - `"contextid"`：将是启用 PID 跟踪选项的别名。即，
    - 在 EL1 内核上，`contextid == contextid1`
    - 在 EL2 内核上，`contextid == contextid2`

`perf` 总是在相关 EL 上启用 PID 跟踪，这是通过自动启用 `"contextid"` 配置来实现的——但对于 EL2，可以使用 `"contextid1"` 和 `"contextid2"` 配置进行特定调整。例如，如果用户希望同时跟踪主机和来宾的 PID，则可以同时设置两个配置 `"contextid1"` 和 `"contextid2"`：

  ```sh
  perf record -e cs_etm/contextid1,contextid2/u -- vm
  ```

生成用于反馈导向优化（AutoFDO）的覆盖率文件：
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`perf inject` 接受 `--itrace` 选项，在这种情况下，跟踪数据被移除并替换为合成事件。例如：
```bash
perf inject --itrace --strip -i perf.data -o perf.data.new

以下是使用ARM ETM进行autoFDO的一个示例。它需要autofdo（https://github.com/google/autofdo）和GCC版本5。冒泡排序的示例来自AutoFDO教程（https://gcc.gnu.org/wiki/AutoFDO/Tutorial）：

	$ gcc-5 -O3 sort.c -o sort
	$ taskset -c 2 ./sort
	冒泡排序包含30000个元素的数组
	5910 ms

	$ perf record -e cs_etm/@tmc_etr0/u --per-thread taskset -c 2 ./sort
	冒泡排序包含30000个元素的数组
	12543 ms
	[ perf record: 被唤醒了35次以写入数据 ]
	[ perf record: 捕获并写入了69.640 MB 的perf.data ]

	$ perf inject -i perf.data -o inj.data --itrace=il64 --strip
	$ create_gcov --binary=./sort --profile=inj.data --gcov=sort.gcov -gcov_version=1
	$ gcc-5 -O3 -fauto-profile=sort.gcov sort.c -o sort_autofdo
	$ taskset -c 2 ./sort_autofdo
	冒泡排序包含30000个元素的数组
	5806 ms

配置选项格式
~~~~~~~~~~~~

以下字符串可以在perf命令行中的//之间提供以启用各种选项。
它们也列在/sys/bus/event_source/devices/cs_etm/format/文件夹中。

.. list-table::
   :header-rows: 1

   * - 选项
     - 描述
   * - branch_broadcast
     - 会话本地版本的系统范围设置：
       :ref:`ETM_MODE_BB <coresight-branch-broadcast>`
   * - contextid
     - 参见 `Tracing PID`_
   * - contextid1
     - 参见 `Tracing PID`_
   * - contextid2
     - 参见 `Tracing PID`_
   * - configid
     - 自定义配置的选择。这是实现细节，不会直接使用，请参阅：:ref:`trace/coresight/coresight-config:Using Configurations in perf`
   * - preset
     - 自定义配置中的参数覆盖，请参阅：:ref:`trace/coresight/coresight-config:Using Configurations in perf`
   * - sinkid
     - 字符串的哈希版本以选择一个sink，在使用@符号时自动设置
这是内部实现细节，不会直接使用，请参阅 `Using perf framework`_
   * - cycacc
     - 会话本地版本的系统范围设置：:ref:`ETMv4_MODE_CYCACC <coresight-cycle-accurate>`
   * - retstack
     - 会话本地版本的系统范围设置：:ref:`ETM_MODE_RETURNSTACK <coresight-return-stack>`
   * - timestamp
     - 会话本地版本的系统范围设置：:ref:`ETMv4_MODE_TIMESTAMP <coresight-timestamp>`
   * - cc_threshold
     - 周期计数阈值值。如果没有在此处提供或提供的值为0，则将使用默认值即0x100。如果提供的值小于通过TRCIDR3.CCITMIN指示的最小周期阈值，则将使用最小值

如何使用STM模块
------------------

使用System Trace Macrocell模块与使用跟踪器相同——唯一的区别是客户端正在驱动跟踪捕获，而不是通过代码流来驱动程序。
与其他CoreSight组件一样，有关STM跟踪器的具体信息可以在sysfs中找到，每个条目的更多详细信息请参见[#first]_：

	root@genericarmv8:~# ls /sys/bus/coresight/devices/stm0
	enable_source   hwevent_select  port_enable     subsystem       uevent
	hwevent_enable  mgmt            port_select     traceid
	root@genericarmv8:~#

像任何其他源一样，需要识别一个sink，并在使用之前启用STM：

	root@genericarmv8:~# echo 1 > /sys/bus/coresight/devices/tmc_etf0/enable_sink
	root@genericarmv8:~# echo 1 > /sys/bus/coresight/devices/stm0/enable_source

从那里，用户空间应用程序可以请求并使用由通用STM API为此提供的devfs接口所提供的通道：

	root@genericarmv8:~# ls -l /dev/stm0
	crw-------    1 root     root       10,  61 Jan  3 18:11 /dev/stm0
	root@genericarmv8:~#

关于如何使用通用STM API的详细信息可以在这里找到：
- 文档/trace/stm.rst [#second]_

CTI & CTM模块
-----------------

CTI（交叉触发接口）为各个CTI和组件之间提供了一组触发信号，并可以通过CTM（交叉触发矩阵）上的通道将这些信号传播到所有CTI。
提供了单独的文档文件来解释这些设备的使用方法（文档/trace/coresight/coresight-ect.rst） [#fourth]_
```
CoreSight 系统配置
------------------------------

CoreSight 组件可能是具有许多编程选项的复杂设备。此外，这些组件可以被编程以在整个系统中相互交互。提供了一个 CoreSight 系统配置管理器，以便能够轻松地从 perf 和 sysfs 中选择和使用这些复杂的编程配置。更多信息请参阅单独的文档（Documentation/trace/coresight/coresight-config.rst）。

.. [#first] Documentation/ABI/testing/sysfs-bus-coresight-devices-stm

.. [#second] Documentation/trace/stm.rst

.. [#third] https://github.com/Linaro/perf-opencsd

.. [#fourth] Documentation/trace/coresight/coresight-ect.rst

.. [#fifth] Documentation/trace/coresight/coresight-config.rst
