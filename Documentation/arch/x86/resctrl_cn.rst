### SPDX 许可证标识符：GPL-2.0
### 包含：<isonum.txt>

===========================================
资源控制功能的用户界面
===========================================

**版权所有**：© 2016 英特尔公司
**作者**：
- 余锋华 <fenghua.yu@intel.com>
- Tony Luck <tony.luck@intel.com>
- Vikas Shivappa <vikas.shivappa@intel.com>

英特尔将此功能称为英特尔资源导向技术（Intel® RDT）。
AMD 将此功能称为 AMD 平台服务质量（AMD QoS）。
此功能通过以下配置项和 x86 /proc/cpuinfo 标志位启用：

| RDT（资源导向技术）分配 | "rdt_a" |
|-------------------------|---------|
| CAT（缓存分配技术）     | "cat_l3", "cat_l2" |
| CDP（代码与数据优先级） | "cdp_l3", "cdp_l2" |
| CQM（缓存服务质量监控） | "cqm_llc", "cqm_occup_llc" |
| MBM（内存带宽监控）     | "cqm_mbm_total", "cqm_mbm_local" |
| MBA（内存带宽分配）     | "mba" |
| SMBA（慢速内存带宽分配） | "" |
| BMEC（带宽监控事件配置） | "" |

历史上，新特性默认在 /proc/cpuinfo 中可见。这导致了特性标志变得难以被人解析。如果用户空间可以从 resctrl 的信息目录中获取到关于特性的信息，则应避免向 /proc/cpuinfo 添加新的标志。
要使用此特性，请挂载文件系统：

```bash
# mount -t resctrl resctrl [-o cdp[,cdpl2][,mba_MBps][,debug]] /sys/fs/resctrl
```

挂载选项包括：

- "cdp"：
  启用 L3 缓存分配中的代码/数据优先级。
- "cdpl2"：
  启用 L2 缓存分配中的代码/数据优先级。
- "mba_MBps"：
  启用 MBA 软件控制器（mba_sc），以 MiBps 指定 MBA 带宽。
- "debug"：
  使调试文件可访问。可用的调试文件会标注为“仅在启用 debug 选项时可用”。

L2 和 L3 CDP 分别进行控制。
RDT 特性是相互独立的。特定系统可能仅支持监控、仅支持控制或同时支持监控和控制。缓存伪锁定是一种使用缓存控制来“固定”或“锁定”数据在缓存中的独特方式。详情请参阅“缓存伪锁定”部分。
如果存在分配或监控功能之一，则挂载成功，但仅创建系统支持的那些文件和目录。
有关接口在监控和分配期间行为的更多详细信息，请参阅“资源分配和监控组”部分。
信息目录
==============

“info”目录包含了已启用资源的相关信息。每个资源都有其自己的子目录，这些子目录的名称反映了资源的名称。
每个子目录包含了与分配相关的以下文件：

缓存资源（L3 / L2）子目录包含了以下与分配相关的文件：

"num_closids":
    对于此资源有效的CLOSID数量。内核使用所有启用资源中的最小CLOSID数量作为限制。
"cbm_mask":
    对于此资源有效的位掩码。此掩码相当于100%。
"min_cbm_bits":
    当写入掩码时必须设置的连续位数的最小值。
"shareable_bits":
    与其他执行实体（例如I/O）共享的资源的位掩码。用户在设置专属缓存分区时可以使用这个掩码。请注意，某些平台支持具有自己缓存使用设置的设备，这些设置可能会覆盖这些位。
"bit_usage":
    显示所有资源实例使用的注释容量位掩码。图例如下：

        "0":
            相应区域未被使用。当系统资源已经分配后，在“bit_usage”中发现“0”表示资源被浪费了。
        "H":
            相应区域仅由硬件使用但可供软件使用。如果资源在“shareable_bits”中有设置的位，但并非所有这些位出现在资源组的模式中，则“shareable_bits”中出现但没有出现在任何资源组中的位将被标记为"H"。
        "X":
            相应区域可用于共享，并且被硬件和软件使用。这些是在“shareable_bits”以及资源组分配中出现的位。
        "S":
            相应区域被软件使用并且可用于共享。
"E":
			      对应区域被一个资源组独占使用。不允许共享。
"P":
			      对应区域为伪锁定状态。不允许共享。
"sparse_masks":
		指示是否支持CBM中非连续的1值。
"0":
			      只支持CBM中连续的1值。
"1":
			      支持CBM中非连续的1值。
内存带宽(MB)子目录包含以下与分配相关的文件：

"min_bandwidth":
		用户可以请求的最小内存带宽百分比。
"bandwidth_gran":
		分配内存带宽百分比的粒度。分配的带宽百分比将四舍五入到硬件上可用的下一个控制步。可用的带宽控制步骤为：
		min_bandwidth + N * bandwidth_gran
"delay_linear":
		指示延迟尺度是线性的还是非线性的。此字段仅用于信息目的。
"thread_throttle_mode":
		在Intel系统中，当物理核心上的线程运行的任务请求不同的内存带宽百分比时，它们是如何受到节流的指示器：

		"max":
			应用所有线程中的最小百分比
		"per-thread":
			直接将带宽百分比应用于运行在核心上的线程

如果RDT监控可用，则会有一个"L3_MON"目录，其中包含以下文件：

"num_rmids":
		可用RMID的数量。这是创建"CTRL_MON" + "MON"组合的上限。
"mon_features":
		如果启用了监控，则列出监控事件。
### 翻译

#### 示例：

```
# cat /sys/fs/resctrl/info/L3_MON/mon_features
llc_occupancy
mbm_total_bytes
mbm_local_bytes
```

如果系统支持带宽监控事件配置（BMEC），则带宽事件将是可配置的。输出如下：

```
# cat /sys/fs/resctrl/info/L3_MON/mon_features
llc_occupancy
mbm_total_bytes
mbm_total_bytes_config
mbm_local_bytes
mbm_local_bytes_config
```

`mbm_total_bytes_config`, `mbm_local_bytes_config`:
当支持带宽监控事件配置（BMEC）功能时，这些是包含`mbm_total_bytes`和`mbm_local_bytes`事件配置的读写文件。
事件配置设置与域相关，并影响该域内的所有CPU。当任一事件配置发生变化时，该域内所有RMID的带宽计数器（包括`mbm_total_bytes`和`mbm_local_bytes`）将被清零。下一次读取每个RMID时会报告“不可用”，随后的读取将报告有效值。

以下为支持的事件类型：

| Bits | 描述 |
|------|-----------------|
| 6    | QoS域到所有类型内存的脏数据受害者 |
| 5    | 非本地NUMA域中慢速内存的读取 |
| 4    | 本地NUMA域中慢速内存的读取 |
| 3    | 非本地NUMA域中的非临时写入 |
| 2    | 本地NUMA域中的非临时写入 |
| 1    | 非本地NUMA域中的内存读取 |
| 0    | 本地NUMA域中的内存读取 |

默认情况下，`mbm_total_bytes`配置设置为0x7f以统计所有事件类型，而`mbm_local_bytes`配置设置为0x15以统计所有本地内存事件。

#### 示例：

* 查看当前配置：
  ```
  # cat /sys/fs/resctrl/info/L3_MON/mbm_total_bytes_config
  0=0x7f;1=0x7f;2=0x7f;3=0x7f

  # cat /sys/fs/resctrl/info/L3_MON/mbm_local_bytes_config
  0=0x15;1=0x15;3=0x15;4=0x15
  ```

* 将`mbm_total_bytes`设置为仅统计域0上的读取操作，需要设置位0、1、4和5，即二进制下的110011（十六进制下为0x33）：
  ```
  # echo "0=0x33" > /sys/fs/resctrl/info/L3_MON/mbm_total_bytes_config

  # cat /sys/fs/resctrl/info/L3_MON/mbm_total_bytes_config
  0=0x33;1=0x7f;2=0x7f;3=0x7f
  ```

* 将`mbm_local_bytes`设置为统计域0和1上所有慢速内存读取操作，需要设置位4和5，即二进制下的110000（十六进制下为0x30）：
  ```
  # echo "0=0x30;1=0x30" > /sys/fs/resctrl/info/L3_MON/mbm_local_bytes_config

  # cat /sys/fs/resctrl/info/L3_MON/mbm_local_bytes_config
  0=0x30;1=0x30;3=0x15;4=0x15
  ```

`max_threshold_occupancy`:
提供一个最大值（以字节为单位），先前使用的LLC_occupancy计数器在达到这个值时可以考虑重用。

最后，在"info"目录的顶层有一个名为"last_cmd_status"的文件。此文件会随着每次通过文件系统发出的命令（创建新目录或写入任何控制文件）而重置。如果命令成功，它将显示为"ok"；如果命令失败，则会提供更多错误信息，这些信息无法通过文件操作的错误返回来传达。例如：

```
# echo L3:0=f7 > schemata
bash: echo: write error: Invalid argument
# cat info/last_cmd_status
mask f7 has non-consecutive 1-bits
```

### 资源分配和监控组

资源组在resctrl文件系统中表示为目录。默认组是根目录，安装后立即拥有系统中的所有任务和CPU，并能充分利用所有资源。
在具有RDT控制功能的系统上，可以在根目录中创建额外的目录，以指定每种资源的不同数量（参见下面的"schemata"）。根目录及其顶级子目录称为“CTRL_MON”组。
在具有RDT监控功能的系统上，根目录和其他顶级目录包含一个名为"mon_groups"的目录，其中可以创建额外的目录来监控其祖先CTRL_MON组中的任务子集。本文档其余部分将这些称为“MON”组。
删除一个目录会将其代表的组所拥有的所有任务和CPU移动到父级目录。删除一个创建的CTRL_MON组会自动移除其下的所有MON组。
将MON组目录移动到新的父级CTRL_MON组是被支持的，目的是为了改变MON组的资源分配，同时不影响其监控数据或已分配的任务。此操作不适用于监控CPU的MON组。除了简单重命名CTRL_MON或MON组之外，目前不允许进行其他任何移动操作。
所有组都包含以下文件：

"tasks"：
	读取此文件可显示属于该组的所有任务列表。向该文件写入任务ID会将任务添加到组中。可以通过逗号分隔多个任务ID来添加多个任务。任务将按顺序分配。不支持处理多个失败情况。在尝试分配任务时遇到单一失败会导致操作中断，并且失败前已经添加的任务仍将保留在组内。
失败信息将记录在/sys/fs/resctrl/info/last_cmd_status中。
如果该组是CTRL_MON组，则任务将从先前拥有该任务的任何CTRL_MON组中移除，并从拥有该任务的任何MON组中移除。如果该组是MON组，则任务必须已经属于该组的CTRL_MON父级。任务将从任何先前的MON组中移除。
"cpus"：
	读取此文件可显示表示该组所拥有的逻辑CPU的位掩码。向此文件写入掩码会向/从该组添加/移除CPU。与"tasks"文件一样，维持了一个层次结构，其中MON组只能包括其父级CTRL_MON组拥有的CPU。
当资源组处于伪锁定模式时，此文件仅可读取，反映了与伪锁定区域关联的CPU。
"cpus_list"：
	与"cpus"相同，只是使用CPU范围而非位掩码。
当启用控制功能时，所有CTRL_MON组还将包含：

"schemata"：
	列出可供该组使用的所有资源。
每个资源都有其自己的行和格式，请参见下面的详细信息。
"size"：
	镜像显示"schemata"文件的内容，以字节形式展示每项分配的大小，而不是表示分配的位数。
"模式":
资源组的“模式”决定了其分配的共享方式。一个“可共享”的资源组允许其分配被共享，而一个“独占”的资源组不允许这样做。通过首先将“pseudo-locksetup”写入“模式”文件，然后将缓存伪锁定区域的模式写入资源组的“模式”文件来创建缓存伪锁定区域。在成功创建伪锁定区域后，模式会自动变为“pseudo-locked”。

"ctrl_hw_id":
仅在启用调试选项时可用。硬件用于控制组的标识符。在x86系统中，这是CLOSID。
当启用监控功能时，所有MON组还将包含：

"mon_data":
这包含一组按L3域和RDT事件组织的文件。例如，在具有两个L3域的系统上，会有名为"mon_L3_00"和"mon_L3_01"的子目录。这些目录中的每一个都有针对每个事件的一个文件（例如"llc_occupancy"、"mbm_total_bytes"和"mbm_local_bytes"）。在MON组中，这些文件提供了该组内所有任务当前事件值的读出。在CTRL_MON组中，这些文件提供了CTRL_MON组内所有任务以及MON组内所有任务的总和。请参阅示例部分以了解更详细的使用信息。
在启用了子NUMA集群（SNC）的系统上，每个节点有额外的目录（位于其所占用的L3缓存的"mon_L3_XX"目录内）。这些目录名为"mon_sub_L3_YY"，其中"YY"是节点编号。

"mon_hw_id":
仅在启用调试选项时可用。硬件用于监控组的标识符。在x86系统中，这是RMID。

资源分配规则
-------------------------
当任务运行时，以下规则定义了可供其使用的资源：

1) 如果任务属于非默认组，则使用该组的模式。
2) 否则如果任务属于默认组，但正在运行于分配给某个特定组的CPU上，则使用该CPU所属组的模式。
3) 否则，使用默认组的模式。

资源监控规则
-------------------------
1) 如果任务属于MON组或非默认CTRL_MON组，则该任务的RDT事件将在该组中报告。
2) 如果任务属于默认CTRL_MON组，但正在运行于分配给某个特定组的CPU上，则该任务的RDT事件将在该组中报告。
3) 否则，该任务的 RDT 事件将在根级别的 "mon_data" 组中报告。

关于缓存占用监控与控制的说明
===============================================

当你将一个任务从一个组移动到另一个组时，请记住这仅会影响该任务的*新*缓存分配。例如，你可能有一个在监控组中的任务，显示了3 MB 的缓存占用。如果你将其移动到一个新的组，并立即检查旧组和新组的占用情况，很可能会发现旧组仍然显示3 MB，而新组为零。当任务访问之前移动前所驻留在缓存中的位置时，硬件不会更新任何计数器。在一个繁忙的系统上，你可能会看到随着缓存行被逐出并重新使用，旧组的占用量逐渐下降；而新组的占用量随着任务访问内存以及基于新组成员资格对加载到缓存进行计数而逐渐上升。

对于缓存分配控制来说也是同样的道理。将一个任务移动到具有较小缓存分区的组并不会逐出任何缓存行。该进程可能还会继续使用来自旧分区的缓存行。

硬件使用 CLOSid（服务等级 ID）和 RMID（资源监控 ID）来标识控制组和监控组。每个资源组根据其类型映射到这些 ID 上。CLOSid 和 RMID 的数量由硬件限制，因此如果 CLOSID 或 RMID 用尽，则创建 "CTRL_MON" 目录可能会失败；如果 RMID 用尽，则创建 "MON" 组可能会失败。

最大阈值占用 - 通用概念
------------------------------------------

请注意，一旦 RMID 被释放，它可能不会立即可用，因为 RMID 仍然与前一个用户的缓存行相关联。
因此，这样的 RMID 将被放置在等待列表上，并检查其缓存占用是否已降低。如果系统中有大量处于等待状态但尚未准备好使用的 RMID，用户在执行 `mkdir` 操作时可能会遇到 -EBUSY 错误。

`max_threshold_occupancy` 是一个可由用户配置的值，用于确定何时可以释放 RMID 的占用量。

`mon_llc_occupancy_limbo` 追踪点给出了一个子集的 RMID 的精确占用量（以字节为单位），这些 RMID 不是立即可用于分配的。这个追踪点不能保证每秒都会产生输出，可能需要尝试创建一个空的监控组以强制更新。只有当创建控制或监控组失败时，才可能产生输出。

模式文件 - 通用概念
---------------------------------
文件中的每一行描述了一个资源。该行以资源名称开始，随后是应用于系统中该资源各个实例的具体值。
### 缓存ID

在当前一代的系统中，每个插座有一个L3缓存，并且L2缓存通常只是由核心上的超线程共享，但这并不是架构上的必要条件。我们可能会在一个插座上有多个独立的L3缓存，或者多个核心共享一个L2缓存。因此，我们不使用“插座”或“核心”来定义共享资源的一组逻辑CPU，而是使用“缓存ID”。在一个特定的缓存级别上，这将是一个在整个系统中唯一的数字（但并不保证是一个连续的序列，可能存在空缺）。要查找每个逻辑CPU的ID，请查看`/sys/devices/system/cpu/cpu*/cache/index*/id`。

### 缓存位掩码 (CBM)

对于缓存资源，我们使用位掩码来描述可用于分配的缓存部分。掩码的最大值由每个CPU模型定义（并且可能对不同的缓存级别有所不同）。它可以通过CPUID找到，但也提供在resctrl文件系统的“info”目录中的`info/{resource}/cbm_mask`。一些Intel硬件要求这些掩码的所有'1'位必须位于一个连续的块中。因此，0x3、0x6和0xC是合法的4位掩码（其中有两位设置为1），但0x5、0x9和0xA不是。如果支持非连续1值，请检查`/sys/fs/resctrl/info/{resource}/sparse_masks`。在一个具有20位掩码的系统中，每位代表缓存容量的5%。你可以使用掩码：0x1f、0x3e0、0x7c00、0xf8000将缓存划分为四个相等的部分。

### 关于子NUMA集群模式的说明

当启用SNC模式时，Linux可能会更容易地在子NUMA节点之间进行任务负载平衡，而不是在常规NUMA节点之间，因为子NUMA节点上的CPU共享相同的L3缓存，并且系统可能报告子NUMA节点之间的NUMA距离比常规NUMA节点更低的值。
每个“mon_L3_XX”目录中的顶层监控文件提供了所有共享L3缓存实例的SNC节点的数据总和。
绑定到特定子NUMA节点CPU的任务用户可以读取“mon_sub_L3_YY”目录中的“llc_occupancy”、“mbm_total_bytes”和“mbm_local_bytes”，以获取节点本地数据。
内存带宽分配仍然在L3缓存级别执行。也就是说，节流控制适用于所有SNC节点。
L3缓存分配位图也适用于所有SNC节点。但是请注意，每个位所代表的L3缓存量除以每个L3缓存的SNC节点数量。例如，在具有100MB缓存的系统上，如果分配掩码为10位，则每位通常代表10MB。启用SNC模式后，如果每个L3缓存有两个SNC节点，那么每位只代表5MB。

### 内存带宽分配与监控

对于内存带宽资源，默认情况下用户通过指示总内存带宽的百分比来控制资源。
每个CPU模型的最小带宽百分比值预先定义，并可以在`info/MB/min_bandwidth`中查找。所分配的带宽粒度也取决于CPU模型，并可以在`info/MB/bandwidth_gran`中查找。可用的带宽控制步骤为：min_bw + N * bw_gran。中间值会四舍五入到硬件上可用的下一个控制步骤。
在某些Intel SKU上，带宽节流是一种针对核心的具体机制。在共享一个核心的两个线程上使用高带宽和低带宽设置可能导致两个线程都被节流到使用低带宽（参见“thread_throttle_mode”）。
由于内存带宽分配(MBA)可能是一种针对核心的具体机制，而内存带宽监控(MBM)是在包级别完成的，这可能会导致用户试图通过MBA应用控制然后监控带宽以查看控制是否有效时产生混淆。以下是一些此类情况：

1. 当增加百分比值时，用户可能**不会**看到实际带宽的增加：

这种情况发生在聚合L2外部带宽大于L3外部带宽时。考虑一个带有24个核心的SKL SKU，在一个包上，其中L2外部带宽为10GBps（因此聚合L2外部带宽为240GBps），L3外部带宽为100GBps。现在一个工作负载有20个线程，每个线程使用50%的带宽，每个线程消耗5GBps，尽管指定的百分比值仅为50% << 100%，但仍消耗了最大L3带宽100GBps。因此增加带宽百分比不会带来更多的带宽。这是因为虽然L2外部带宽仍有容量，但L3外部带宽已完全使用。还请注意，这将取决于基准测试运行的核心数。
2. 相同的带宽百分比在不同线程数量下可能意味着不同的实际带宽：

对于第1点中相同的SKU，'单线程，10%带宽' 和 '4线程，10%带宽' 虽然带宽百分比相同为10%，但实际消耗的带宽可以分别达到最高10GB/s和40GB/s。这是因为当线程开始使用rdtgroup中的更多核心时，即使用户指定的带宽百分比相同，实际带宽也可能增加或变化。
为了缓解这种情况并使接口更加用户友好，resctrl增加了以MiB/s来指定带宽的支持。内核底层会使用一种软件反馈机制或“软件控制器（mba_sc）”，该机制通过MBM计数器读取实际带宽，并调整内存带宽百分比以确保：

    “实际带宽 < 用户指定的带宽”

默认情况下，策略会采用带宽百分比值，而用户可以通过挂载选项'mba_MBps'切换到“MBA软件控制器”模式。策略格式在下面的章节中有详细说明。

L3 策略文件详情（禁用代码和数据优先级）
---------------------------------------------------
当禁用CDP时，L3策略格式如下：

    L3:<cache_id0>=<cbm>;<cache_id1>=<cbm>;..

L3 策略文件详情（通过挂载选项启用CDP）
---------------------------------------------------
当启用CDP时，L3控制被分为两个独立的资源，因此您可以为代码和数据指定独立的掩码，如下所示：

    L3DATA:<cache_id0>=<cbm>;<cache_id1>=<cbm>;..
    L3CODE:<cache_id0>=<cbm>;<cache_id1>=<cbm>;..

L2 策略文件详情
-----------------------
CDP支持通过使用'cdpl2'挂载选项在L2上实现。策略格式如下：

    L2:<cache_id0>=<cbm>;<cache_id1>=<cbm>;..
或者

    L2DATA:<cache_id0>=<cbm>;<cache_id1>=<cbm>;..
    L2CODE:<cache_id0>=<cbm>;<cache_id1>=<cbm>;..

内存带宽分配（默认模式）
------------------------------------------
内存带宽域是L3缓存
内存带宽分配，单位为 MiBps
-------------------------------

内存带宽域是 L3 缓存
::

    MB:<cache_id0>=bw_MiBps0;<cache_id1>=bw_MiBps1;..

慢速内存带宽分配 (SMBA)
-------------------------------
AMD 硬件支持慢速内存带宽分配 (SMBA)
CXL.memory 是唯一支持的“慢速”内存设备。通过 SMBA 的支持，硬件能够在慢速内存设备上实现带宽分配。如果系统中有多个此类设备，则节流逻辑会将所有慢速源组合在一起，并整体应用限制。
SMBA（与 CXL.memory 一起）的存在独立于慢速内存设备的存在。如果系统上没有此类设备，则配置 SMBA 将不会影响系统的性能。
慢速内存的带宽域是 L3 缓存。其模式文件格式如下：
::

    SMBA:<cache_id0>=bandwidth0;<cache_id1>=bandwidth1;..

读取/写入模式文件
----------------------
读取模式文件会显示所有域上所有资源的状态。在写入时，只需指定您希望更改的值。例如：
::

  # cat schemata
  L3DATA:0=fffff;1=fffff;2=fffff;3=fffff
  L3CODE:0=fffff;1=fffff;2=fffff;3=fffff
  # echo "L3DATA:2=3c0;" > schemata
  # cat schemata
  L3DATA:0=fffff;1=fffff;2=3c0;3=fffff
  L3CODE:0=fffff;1=fffff;2=fffff;3=fffff

在 AMD 系统上读取/写入模式文件
------------------------------------
读取模式文件会显示所有域上的当前带宽限制。分配的资源以每八分之一 GB/s 为单位。
在写入文件时，需要指定希望配置带宽限制的缓存 ID。
例如，要在第一个缓存ID上分配2GB/s的限制：

::

  # cat schemata
    MB:0=2048;1=2048;2=2048;3=2048
    L3:0=ffff;1=ffff;2=ffff;3=ffff

  # echo "MB:1=16" > schemata
  # cat schemata
    MB:0=2048;1=  16;2=2048;3=2048
    L3:0=ffff;1=ffff;2=ffff;3=ffff

使用SMBA特性在AMD系统上读写schemata文件
--------------------------------------------------------------------
读写schemata文件的方式与不使用SMBA时相同。
例如，要在第一个缓存ID上分配8GB/s的限制：

::

  # cat schemata
    SMBA:0=2048;1=2048;2=2048;3=2048
      MB:0=2048;1=2048;2=2048;3=2048
      L3:0=ffff;1=ffff;2=ffff;3=ffff

  # echo "SMBA:1=64" > schemata
  # cat schemata
    SMBA:0=2048;1=  64;2=2048;3=2048
      MB:0=2048;1=2048;2=2048;3=2048
      L3:0=ffff;1=ffff;2=ffff;3=ffff

缓存伪锁定
====================
CAT允许用户指定应用程序可以填充的缓存空间量。缓存伪锁定基于这样一个事实：CPU仍然可以在缓存命中时读取和写入预先分配在其当前分配区域之外的数据。通过缓存伪锁定，数据可以预加载到一个任何应用程序都无法填充的保留缓存部分中，从那以后只会处理缓存命中。伪锁定的缓存内存被暴露给用户空间，在那里应用程序可以将其映射到其虚拟地址空间中，从而具有较低平均读取延迟的内存区域。创建缓存伪锁定区域是由用户的请求触发的，并且伴随着要伪锁定的区域的schemata。创建缓存伪锁定区域的过程如下：

- 使用与用户指定的缓存区域schemata匹配的CBM创建一个新的CAT分配CLOS（CLOSNEW）。这个区域不能与系统上的任何当前CAT分配/CLOS重叠，并且只要伪锁定区域存在就不能与该缓存区域发生未来的重叠。
- 创建与缓存区域大小相同的连续内存区域。
- 清除缓存、禁用硬件预取器、禁用抢占。
- 将CLOSNEW设置为活动CLOS，并触碰分配的内存以将其加载到缓存中。
- 设置之前的CLOS为活动状态。
- 此时可以释放closid CLOSNEW —— 只要其CBM不出现在任何CAT分配中，缓存伪锁定区域就会受到保护。即使从这一点开始，伪锁定缓存区域不会出现在任何CLOS的任何CBM中，运行任何CLOS的应用程序仍能访问伪锁定区域中的内存，因为该区域将继续提供缓存命中服务。
- 加载到缓存中的连续内存区域作为字符设备暴露给用户空间。
缓存伪锁定通过仔细配置CAT特性和控制应用程序行为来提高数据保留在缓存中的概率。无法保证数据会被放置在缓存中。诸如INVD、WBINVD、CLFLUSH等指令仍然可以从缓存中驱逐“锁定”的数据。电源管理C状态可能会缩小或关闭缓存。在创建伪锁定区域时，更深的C状态将自动受到限制。
要求使用伪锁定区域的应用程序与该伪锁定区域所在的缓存关联的核心（或核心子集）具有亲和性。代码中的合理性检查不允许应用程序映射伪锁定内存，除非它与该伪锁定区域所在缓存关联的核心具有亲和性。合理性检查仅在初始`mmap()`处理期间进行，之后没有强制执行，并且应用程序自身需要确保它保持与正确的核心的亲和性。伪锁定分为两个阶段完成：

1) 在第一阶段，系统管理员分配一部分缓存，这部分缓存将专门用于伪锁定。此时，分配等量的内存，加载到已分配的缓存部分中，并以字符设备的形式暴露出来。
2) 在第二阶段，用户空间应用程序将伪锁定内存映射 (`mmap()`) 到其地址空间中。
缓存伪锁定接口
----------------
通过以下步骤使用`resctrl`接口创建伪锁定区域：

1) 在`/sys/fs/resctrl`下创建一个新的资源组目录。
2) 将新资源组的模式更改为“pseudo-locksetup”，方法是向“mode”文件写入“pseudo-locksetup”。
3) 将伪锁定区域的模式写入“schemata”文件。根据“bit_usage”文件，模式中的所有位都应该是“未使用”的。
成功创建伪锁定区域后，“mode”文件将包含“pseudo-locked”，并且会在`/dev/pseudo_lock`下存在一个与资源组同名的新字符设备。用户空间可以通过`mmap()`这个字符设备来访问伪锁定内存区域。
下面可以找到缓存伪锁定区域创建和使用的示例。
缓存伪锁定调试接口
----------------------
默认情况下启用伪锁定调试接口（如果启用了`CONFIG_DEBUG_FS`），可以在`/sys/kernel/debug/resctrl`中找到它。
内核没有明确的方式来测试给定内存位置是否存在于缓存中。伪锁定调试接口利用跟踪基础架构提供了两种测量伪锁定区域缓存驻留的方法：

1) 使用`pseudo_lock_mem_latency`跟踪点测量内存访问延迟。这些测量数据最好使用hist触发器可视化（见下面的示例）。在这个测试中，以32字节的步长遍历伪锁定区域，同时禁用硬件预取器和抢占。这也提供了一种替代性的缓存命中和未命中的可视化方式。
### 使用模型特定精度计数器进行缓存命中和未命中测量（如果可用）。根据系统上的缓存层级，提供`pseudo_lock_l2` 和 `pseudo_lock_l3` 的追踪点。
当创建一个伪锁定区域时，会在 debugfs 中为它创建一个新的目录作为 `/sys/kernel/debug/resctrl/<newdir>`。此目录中存在一个只写文件 `pseudo_lock_measure`。对伪锁定区域的测量取决于写入此 debugfs 文件的数值：

1:
     写入“1”到 `pseudo_lock_measure` 文件将触发在 `pseudo_lock_mem_latency` 追踪点捕获的延迟测量。参见下面的例子。
2:
     写入“2”到 `pseudo_lock_measure` 文件将触发在 `pseudo_lock_l2` 追踪点捕获的 L2 缓存驻留（命中与未命中）测量。参见下面的例子。
3:
     写入“3”到 `pseudo_lock_measure` 文件将触发在 `pseudo_lock_l3` 追踪点捕获的 L3 缓存驻留（命中与未命中）测量。
所有测量均使用追踪基础设施记录。这需要在触发测量前启用相关的追踪点。

### 延迟调试接口示例
在这个例子中，创建了一个名为 “newlock” 的伪锁定区域。以下是测量从该区域读取的周期性延迟，并通过直方图可视化这些数据的方法（如果设置了 `CONFIG_HIST_TRIGGERS` 可用）：
```
# :> /sys/kernel/tracing/trace
# echo 'hist:keys=latency' > /sys/kernel/tracing/events/resctrl/pseudo_lock_mem_latency/trigger
# echo 1 > /sys/kernel/tracing/events/resctrl/pseudo_lock_mem_latency/enable
# echo 1 > /sys/kernel/debug/resctrl/newlock/pseudo_lock_measure
# echo 0 > /sys/kernel/tracing/events/resctrl/pseudo_lock_mem_latency/enable
# cat /sys/kernel/tracing/events/resctrl/pseudo_lock_mem_latency/hist

# 事件直方图
#
# 触发信息：hist:keys=latency:vals=hitcount:sort=hitcount:size=2048 [活动]

{ latency:        456 } hitcount:          1
{ latency:         50 } hitcount:         83
{ latency:         36 } hitcount:         96
{ latency:         44 } hitcount:        174
{ latency:         48 } hitcount:        195
{ latency:         46 } hitcount:        262
{ latency:         42 } hitcount:        693
{ latency:         40 } hitcount:       3204
{ latency:         38 } hitcount:       3484

总计:
    命中: 8192
    条目: 9
    丢失: 0
```

### 缓存命中/未命中调试示例
在这个例子中，在平台的 L2 缓存上创建了一个名为 “newlock” 的伪锁定区域。以下是如何利用平台的精度计数器来获取缓存命中的详细信息和未命中的情况：
```
# :> /sys/kernel/tracing/trace
# echo 1 > /sys/kernel/tracing/events/resctrl/pseudo_lock_l2/enable
# echo 2 > /sys/kernel/debug/resctrl/newlock/pseudo_lock_measure
# echo 0 > /sys/kernel/tracing/events/resctrl/pseudo_lock_l2/enable
# cat /sys/kernel/tracing/trace

# 追踪器: nop
#
#                              _-----=> irqs-off
#                             / _----=> need-resched
#                            | / _---=> hardirq/softirq
#                            || / _--=> preempt-depth
#                            ||| /     delay
#           TASK-PID   CPU#  ||||    TIMESTAMP  FUNCTION
#              | |       |   ||||       |         |
pseudo_lock_mea-1672  [002] ....  3132.860500: pseudo_lock_l2: hits=4097 miss=0
```

### RDT 分配使用的示例

#### 示例 1

在一个双插槽机器上（每个插槽有一个 L3 缓存），对于缓存位掩码只有四个比特位，最小带宽为 10%，内存带宽粒度为 10%：
```
# mount -t resctrl resctrl /sys/fs/resctrl
# cd /sys/fs/resctrl
# mkdir p0 p1
# echo "L3:0=3;1=c\nMB:0=50;1=50" > /sys/fs/resctrl/p0/schemata
# echo "L3:0=3;1=3\nMB:0=50;1=50" > /sys/fs/resctrl/p1/schemata
```

默认资源组未被修改，因此我们有权访问所有缓存的所有部分（其 schemata 文件读取为 “L3:0=f;1=f”）。
受 “p0” 组控制的任务只能从缓存 ID 0 的 “较低” 50% 和缓存 ID 1 的 “较高” 50% 进行分配。
“p1” 组中的任务使用两个插槽缓存的 “较低” 50%。
同样地，由“p0”组控制的任务可以在socket0上使用最高50%的内存带宽，在socket1上也可以使用50%。而“p1”组中的任务在两个socket上也都可以使用50%的内存带宽。
需要注意的是，与缓存掩码不同，内存带宽无法指定这些分配是否可以重叠。分配指定了组可能使用的最大带宽，并且系统管理员可以根据此配置带宽。
如果resctrl使用的是软件控制器（mba_sc），那么用户可以输入以MB为单位的最大带宽，而不是百分比值。

```
# echo "L3:0=3;1=c\nMB:0=1024;1=500" > /sys/fs/resctrl/p0/schemata
# echo "L3:0=3;1=3\nMB:0=1024;1=500" > /sys/fs/resctrl/p1/schemata
```

在上面的例子中，“p1”和“p0”组中的任务在socket0上的最大带宽为1024MB，而在socket1上则为500MB。
2) 示例2

同样是两个socket，但这次采用更为实际的20位掩码。
有两个实时任务：pid=1234运行在处理器0上，pid=5678运行在处理器1上，均位于socket0，在一个双socket、双核机器上。为了避免干扰，每个实时任务独占socket0上L3缓存的四分之一。

```
# mount -t resctrl resctrl /sys/fs/resctrl
# cd /sys/fs/resctrl
```

首先我们为默认组重置策略，这样普通任务将不能使用socket0上L3缓存的“上层”50%以及50%的内存带宽：

```
# echo "L3:0=3ff;1=fffff\nMB:0=50;1=100" > schemata
```

接下来，我们为第一个实时任务创建资源组，并给予它访问socket0上缓存“顶层”25%的权限：

```
# mkdir p0
# echo "L3:0=f8000;1=fffff" > p0/schemata
```

最后，我们将第一个实时任务移入这个资源组。同时，我们使用taskset(1)确保该任务始终在一个专用CPU上运行于socket0。大多数资源组的使用都会限制任务运行在哪些处理器上：

```
# echo 1234 > p0/tasks
# taskset -cp 1 1234
```

对于第二个实时任务（使用剩余的25%缓存）也同样操作：

```
# mkdir p1
# echo "L3:0=7c00;1=fffff" > p1/schemata
# echo 5678 > p1/tasks
# taskset -cp 2 5678
```

对于同一个双socket系统，带有内存带宽资源和CAT L3的情况，策略会如下所示（假设最小带宽为10，带宽粒度为10）：

对于我们的第一个实时任务来说，这将请求socket0上20%的内存带宽。
### 示例 2

对于我们的第二个实时任务，这将请求在插槽 0 上额外的 20% 内存带宽：

```
# echo -e "L3:0=f8000;1=fffff\nMB:0=20;1=100" > p0/schemata
```

这是一个实时任务需要额外 20% 的内存带宽在插槽 0 上的例子。

### 示例 3

一个单插槽系统，在核心 4-7 上运行实时任务，并将非实时工作负载分配给核心 0-3。实时任务共享文本和数据，因此不需要每个任务的关联性，并且由于与内核的交互，希望这些核心上的内核能与任务共享 L3 缓存：

```
# mount -t resctrl resctrl /sys/fs/resctrl
# cd /sys/fs/resctrl
```

首先我们重置默认组的 schemata，使得插槽 0 的 L3 缓存的“上部”50%，以及插槽 0 的 50% 内存带宽不能被普通任务使用：

```
# echo "L3:0=3ff\nMB:0=50" > schemata
```

接下来，我们为我们的实时核心创建一个资源组，并给予它访问插槽 0 的缓存“顶部”50% 和 50% 内存带宽的权利：

```
# mkdir p0
# echo "L3:0=ffc00\nMB:0=50" > p0/schemata
```

最后，我们将核心 4-7 移动到新的组，并确保内核和在那里运行的任务得到 50% 的缓存。假设核心 4-7 是 SMT 兄弟，并且只有实时线程被调度到核心 4-7 上，它们也应该获得 50% 的内存带宽：

```
# echo F0 > p0/cpus
```

### 示例 4

前面的例子中的资源组都处于默认的“可共享”模式，允许它们的缓存分配被共享。如果一个资源组配置了一个缓存分配，则没有阻止另一个资源组与该分配重叠的规定。
在这个例子中，我们将在具有两个可以使用 8 位容量掩码进行配置的 L2 缓存实例的 L2 CAT 系统上创建一个新的独占资源组。新的独占资源组将被配置为使用每个缓存实例的 25%：

```
# mount -t resctrl resctrl /sys/fs/resctrl/
# cd /sys/fs/resctrl
```

首先，我们观察到默认组被配置为分配所有 L2 缓存：

```
# cat schemata
L2:0=ff;1=ff
```

我们可以尝试在此时创建新的资源组，但会因为与默认组的 schemata 重叠而失败：

```
# mkdir p0
# echo 'L2:0=0x3;1=0x3' > p0/schemata
# cat p0/mode
shareable
# echo exclusive > p0/mode
-sh: echo: write error: Invalid argument
# cat info/last_cmd_status
schemata overlaps
```

为了确保不与其他资源组重叠，必须更改默认资源组的 schemata，从而让新的资源组能够成为独占的：

```
# echo 'L2:0=0xfc;1=0xfc' > schemata
# echo exclusive > p0/mode
# grep . p0/*
p0/cpus:0
p0/mode:exclusive
p0/schemata:L2:0=03;1=03
p0/size:L2:0=262144;1=262144
```

新创建的资源组不会与独占资源组重叠：

```
# mkdir p1
# grep . p1/*
p1/cpus:0
p1/mode:shareable
p1/schemata:L2:0=fc;1=fc
p1/size:L2:0=786432;1=786432
```

bit_usage 将反映缓存的使用情况：

```
# cat info/L2/bit_usage
0=SSSSSSEE;1=SSSSSSEE
```

资源组不能被强制与独占资源组重叠：

```
# echo 'L2:0=0x1;1=0x1' > p1/schemata
-sh: echo: write error: Invalid argument
# cat info/last_cmd_status
overlaps with exclusive group
```

### 缓存伪锁定示例
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
使用 CBM 0x3 从缓存 ID 1 锁定 L2 缓存的一部分。伪锁定区域暴露在 `/dev/pseudo_lock/newlock`，可以提供给应用程序作为 `mmap()` 的参数：

```
# mount -t resctrl resctrl /sys/fs/resctrl/
# cd /sys/fs/resctrl
```

确保有可用的位可以被伪锁定，因为只有未使用的位才能被伪锁定，所以要从默认资源组的 schemata 中移除要伪锁定的位：

```
# cat info/L2/bit_usage
0=SSSSSSSS;1=SSSSSSSS
# echo 'L2:1=0xfc' > schemata
# cat info/L2/bit_usage
0=SSSSSSSS;1=SSSSSS00
```

创建一个新的资源组，该资源组将与伪锁定区域相关联，指示它将用于伪锁定区域，并配置请求的伪锁定区域容量掩码：

```
# mkdir newlock
# echo pseudo-locksetup > newlock/mode
# echo 'L2:1=0x3' > newlock/schemata
```

成功后，资源组的模式将更改为伪锁定，bit_usage 将反映伪锁定区域，暴露伪锁定区域的字符设备也将存在：

```
# cat newlock/mode
pseudo-locked
# cat info/L2/bit_usage
0=SSSSSSSS;1=SSSSSSPP
# ls -l /dev/pseudo_lock/newlock
crw------- 1 root root 243, 0 Apr  3 05:01 /dev/pseudo_lock/newlock
```

```
/*
* 从用户空间访问伪锁定缓存区域的一页的示例代码
*/
#define _GNU_SOURCE
#include <fcntl.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>

/*
* 要求应用程序仅在与伪锁定区域相关的内核上运行。这里为了方便起见，CPU 硬编码
*/ 
```
```c
static int cpuid = 2;

int main(int argc, char *argv[]) {
    cpu_set_t cpuset;
    long page_size;
    void *mapping;
    int dev_fd;
    int ret;

    page_size = sysconf(_SC_PAGESIZE);

    CPU_ZERO(&cpuset);
    CPU_SET(cpuid, &cpuset);
    ret = sched_setaffinity(0, sizeof(cpuset), &cpuset);
    if (ret < 0) {
      perror("sched_setaffinity");
      exit(EXIT_FAILURE);
    }

    dev_fd = open("/dev/pseudo_lock/newlock", O_RDWR);
    if (dev_fd < 0) {
      perror("open");
      exit(EXIT_FAILURE);
    }

    mapping = mmap(0, page_size, PROT_READ | PROT_WRITE, MAP_SHARED, dev_fd, 0);
    if (mapping == MAP_FAILED) {
      perror("mmap");
      close(dev_fd);
      exit(EXIT_FAILURE);
    }

    /* 应用程序与伪锁定内存 @mapping 进行交互 */

    ret = munmap(mapping, page_size);
    if (ret < 0) {
      perror("munmap");
      close(dev_fd);
      exit(EXIT_FAILURE);
    }

    close(dev_fd);
    exit(EXIT_SUCCESS);
}
```

应用程序间的锁定
-----------------

对 resctrl 文件系统进行的某些操作，包括读写多个文件的操作，必须是原子性的。
例如，为 L3 缓存分配独占预留涉及以下步骤：

1. 从每个目录或每个资源的 "bit_usage" 中读取 cbmmasks。
2. 在全局 CBM 位掩码中找到一组连续的未使用的位。
3. 创建一个新的目录。
4. 将第 2 步找到的位设置到新目录的 "schemata" 文件中。

如果两个应用程序试图同时分配空间，则它们可能会分配相同的位，这样预留就不是独占的而是共享的。
为了协调 resctrlfs 上的原子操作并避免上述问题，建议采用以下锁定过程：

锁定基于 `flock`，它在 libc 中可用，也可以作为 shell 脚本命令使用。

写锁：
A) 对 `/sys/fs/resctrl` 使用 `flock(LOCK_EX)`
B) 读写目录结构
C) 解锁

读锁：
A) 对 `/sys/fs/resctrl` 使用 `flock(LOCK_SH)`
B) 如果成功则读取目录结构
C) 解锁

使用 bash 的示例：
```bash
# 原子性地读取目录结构
$ flock -s /sys/fs/resctrl/ find /sys/fs/resctrl

# 读取目录内容并创建新的子目录

$ cat create-dir.sh
find /sys/fs/resctrl/ > output.txt
mask = function-of(output.txt)
mkdir /sys/fs/resctrl/newres/
echo mask > /sys/fs/resctrl/newres/schemata

$ flock /sys/fs/resctrl/ ./create-dir.sh
```

使用 C 的示例：
```c
/*
 * 示例代码用于在访问 resctrl 文件系统之前获取咨询锁
 */
#include <sys/file.h>
#include <stdlib.h>

void resctrl_take_shared_lock(int fd) {
    int ret;

    /* 在 resctrl 文件系统上获取共享锁 */
    ret = flock(fd, LOCK_SH);
    if (ret) {
        perror("flock");
        exit(-1);
    }
}

void resctrl_take_exclusive_lock(int fd) {
    int ret;

    /* 在 resctrl 文件系统上获取独占锁 */
    ret = flock(fd, LOCK_EX);
    if (ret) {
        perror("flock");
        exit(-1);
    }
}

void resctrl_release_lock(int fd) {
    int ret;

    /* 释放 resctrl 文件系统的锁 */
    ret = flock(fd, LOCK_UN);
    if (ret) {
        perror("flock");
        exit(-1);
    }
}

int main() {
    int fd, ret;

    fd = open("/sys/fs/resctrl", O_DIRECTORY);
    if (fd == -1) {
        perror("open");
        exit(-1);
    }
    resctrl_take_shared_lock(fd);
    /* 读取目录内容的代码 */
    resctrl_release_lock(fd);

    resctrl_take_exclusive_lock(fd);
    /* 读取和写入目录内容的代码 */
    resctrl_release_lock(fd);
}
```

RDT 监控以及分配使用的示例
================================

读取监控数据
----------------------
读取事件文件（例如：mon_data/mon_L3_00/llc_occupancy）会显示相应 MON 组或 CTRL_MON 组的 LLC 占用率的当前快照。
示例 1（监控 CTRL_MON 组及其子任务集）
------------------------------------------------------------------------
在一个双插槽机器（每个插槽一个 L3 缓存）上，假设只有四个位用于缓存位掩码：

```bash
# mount -t resctrl resctrl /sys/fs/resctrl
# cd /sys/fs/resctrl
# mkdir p0 p1
# echo "L3:0=3;1=c" > /sys/fs/resctrl/p0/schemata
# echo "L3:0=3;1=3" > /sys/fs/resctrl/p1/schemata
# echo 5678 > p1/tasks
# echo 5679 > p1/tasks
```

默认资源组保持不变，因此我们能够访问所有缓存的所有部分（其 schemata 文件读取 "L3:0=f;1=f"）。
受组 "p0" 控制的任务仅能从缓存 ID 0 的“较低”50% 和缓存 ID 1 的“较高”50% 分配空间。
组 "p1" 中的任务使用两个插槽上的缓存的“较低”50%。
创建监控组并将任务集的子集分配给每个监控组：

```bash
# cd /sys/fs/resctrl/p1/mon_groups
# mkdir m11 m12
# echo 5678 > m11/tasks
# echo 5679 > m12/tasks
```

获取数据（以字节形式显示的数据）：

```bash
# cat m11/mon_data/mon_L3_00/llc_occupancy
16234000
# cat m11/mon_data/mon_L3_01/llc_occupancy
14789000
# cat m12/mon_data/mon_L3_00/llc_occupancy
16789000
```

父级 ctrl_mon 组显示聚合数据。
```
### 示例 2（从任务创建开始监控）
--------------------------------------------
在双插槽机器上（每个插槽一个 L3 缓存）：

```bash
# mount -t resctrl resctrl /sys/fs/resctrl
# cd /sys/fs/resctrl
# mkdir p0 p1

# 将 RMID 分配给一旦创建的组，因此下面的 <cmd> 从创建时起被监控
# echo $$ > /sys/fs/resctrl/p1/tasks
# <cmd>

# 获取数据
# cat /sys/fs/resctrl/p1/mon_data/mon_l3_00/llc_occupancy
31789000
```

### 示例 3（在没有 CAT 支持或在创建 CAT 组之前进行监控）
---------------------------------------------------------------------
假设像 HSW 这样的系统只有 CQM 而没有 CAT 支持。在这种情况下，`resctrl` 仍然可以挂载，但不能创建 `CTRL_MON` 目录。但是用户可以在根组内创建不同的 MON 组，从而能够监控所有任务，包括内核线程。
这也可以用来在能够将任务分配到不同的分配组之前，对作业的缓存大小占用进行性能分析。

```bash
# mount -t resctrl resctrl /sys/fs/resctrl
# cd /sys/fs/resctrl
# mkdir mon_groups/m01
# mkdir mon_groups/m02

# echo 3478 > /sys/fs/resctrl/mon_groups/m01/tasks
# echo 2467 > /sys/fs/resctrl/mon_groups/m02/tasks

# 单独监控这些组，并获取每个域的数据。从下面可以看出，任务主要在域(插槽) 0 上运行
# cat /sys/fs/resctrl/mon_groups/m01/mon_L3_00/llc_occupancy
31234000
# cat /sys/fs/resctrl/mon_groups/m01/mon_L3_01/llc_occupancy
34555
# cat /sys/fs/resctrl/mon_groups/m02/mon_L3_00/llc_occupancy
31234000
# cat /sys/fs/resctrl/mon_groups/m02/mon_L3_01/llc_occupancy
32789
```

### 示例 4（监控实时任务）
-----------------------------------

单插槽系统中，有实时任务运行在 4-7 号核心，而非实时任务则运行在其他 CPU 上。我们希望监控这些核心上的实时线程的缓存占用情况。

```bash
# mount -t resctrl resctrl /sys/fs/resctrl
# cd /sys/fs/resctrl
# mkdir p1

# 将 CPU 4-7 移动到 p1
# echo f0 > p1/cpus

# 查看 LLC 占用情况快照
# cat /sys/fs/resctrl/p1/mon_data/mon_L3_00/llc_occupancy
11234000
```

### 英特尔 RDT 错误
=================

### 英特尔内存带宽监控器可能会错误报告系统内存带宽
-----------------------------------------------------------------

针对 Skylake 服务器的错误 SKX99 和针对 Broadwell 服务器的 BDF102
问题：英特尔内存带宽监控（MBM）计数器根据为该逻辑核心指定的资源监控 ID（RMID）跟踪指标。IA32_QM_CTR 寄存器（MSR 0xC8E），用于报告这些指标，对于某些 RMID 值可能会报告不正确的系统带宽。
影响：由于此错误，系统内存带宽可能与报告的值不符。
解决方法：MBM 总计和本地读数根据以下修正因子表进行修正：

| 核心数量 | RMID 数量 | RMID 阈值 | 修正因子 |
| -------- | --------- | --------- | -------- |
| 1        | 8         | 0         | 1.000000 |
| 2        | 16        | 0         | 1.000000 |
| 3        | 24        | 15        | 0.969650 |
| 4        | 32        | 0         | 1.000000 |
| 6        | 48        | 31        | 0.969650 |
| 7        | 56        | 47        | 1.142857 |
| 8        | 64        | 0         | 1.000000 |
| 9        | 72        | 63        | 1.185115 |
| 10       | 80        | 63        | 1.066553 |
| 11       | 88        | 79        | 1.454545 |
| 12       | 96        | 0         | 1.000000 |
| 13       | 104       | 95        | 1.230769 |
| 14       | 112       | 95        | 1.142857 |
| 15       | 120       | 95        | 1.066667 |
| 16       | 128       | 0         | 1.000000 |
| 17       | 136       | 127       | 1.254863 |
| 18       | 144       | 127       | 1.185255 |
| 19       | 152       | 0         | 1.000000 |
| 20       | 160       | 127       | 1.066667 |
| 21       | 168       | 0         | 1.000000 |
| 22       | 176       | 159       | 1.454334 |
| 23       | 184       | 0         | 1.000000 |
| 24       | 192       | 127       | 0.969744 |
| 25       | 200       | 191       | 1.280246 |
| 26       | 208       | 191       | 1.230921 |
| 27       | 216       | 0         | 1.000000 |
| 28       | 224       | 191       | 1.143118 |

如果 RMID 大于 RMID 阈值，则应将 MBM 总计和本地值乘以修正因子。
请参阅以下链接以获取更多信息：

1. Intel Xeon 可扩展处理器系列规范更新中的 SKX99 错误：
   http://web.archive.org/web/20200716124958/https://www.intel.com/content/www/us/en/processors/xeon/scalable/xeon-scalable-spec-update.html

2. Intel Xeon E5-2600 v4 处理器系列规范更新中的 BDF102 错误：
   http://web.archive.org/web/20191125200531/https://www.intel.com/content/dam/www/public/us/en/documents/specification-updates/xeon-e5-v4-spec-update.pdf

3. 第二代 Intel Xeon 可扩展处理器上的 Intel 资源导向技术（Intel RDT）参考手册中的错误：
   https://software.intel.com/content/www/us/en/develop/articles/intel-resource-director-technology-rdt-reference-manual.html
