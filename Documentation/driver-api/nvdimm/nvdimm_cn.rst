===============================
LIBNVDIMM：非易失性设备
===============================

libnvdimm - 内核 / libndctl - 用户空间辅助库

nvdimm@lists.linux.dev

版本 13

.. 目录:

    词汇表
    概览
        支持文档
        Git 仓库
    LIBNVDIMM PMEM
        PMEM-区域、原子扇区与 DAX
    示例 NVDIMM 平台
    LIBNVDIMM 内核设备模型和 LIBNDCTL 用户空间 API
        LIBNDCTL: 上下文
            libndctl: 创建新的库上下文示例
        LIBNVDIMM/LIBNDCTL: 总线
            libnvdimm: /sys/class 中的控制类设备
            libnvdimm: 总线
            libndctl: 总线枚举示例
        LIBNVDIMM/LIBNDCTL: DIMM（NMEM）
            libnvdimm: DIMM（NMEM）
            libndctl: DIMM 枚举示例
        LIBNVDIMM/LIBNDCTL: 区域
            libnvdimm: 区域
            libndctl: 区域枚举示例
            为何不在区域名称中编码区域类型？
            如何确定区域的主要类型？
        LIBNVDIMM/LIBNDCTL: 命名空间
            libnvdimm: 命名空间
            libndctl: 命名空间枚举示例
            libndctl: 创建命名空间示例
            为何使用“命名空间”一词？
        LIBNVDIMM/LIBNDCTL: 块转换表 “btt”
            libnvdimm: btt 布局
            libndctl: 创建 btt 示例
    LIBNDCTL 概要图

词汇表
======

PMEM：
  系统物理地址范围，其中写入是持久性的。由 PMEM 组成的块设备能够支持 DAX。一个 PMEM 地址范围可能跨越多个 DIMM 的交错。
DPA：
  DIMM 物理地址，是相对于 DIMM 的偏移量。在一个系统中只有一个 DIMM 时，存在一对一的系统物理地址与 DPA 的关联。
一旦添加更多 DIMM，则必须解码内存控制器交错以确定与给定系统物理地址相关联的 DPA。
DAX：
  文件系统的扩展功能，用于绕过页缓存和块层，直接将持久性内存从 PMEM 块设备映射到进程地址空间。
DSM：
  设备特定方法：ACPI 方法来控制特定设备——在此情况下是固件。
DCR：
  NVDIMM 控制区域结构，定义于 ACPI 6 第 5.2.25.5 节。它定义了给定 DIMM 的供应商 ID、设备 ID 和接口格式。
BTT：
  块转换表：持久性内存是字节可寻址的。现有软件可能期望写入的电源故障原子性至少为一个扇区，即 512 字节。BTT 是一个具有原子更新语义的间接表，用于在 PMEM 块设备驱动程序前面呈现任意的原子扇区大小。
LABEL：
  存储在 DIMM 设备上的元数据，用于分区并标识（持久性命名）分配给不同 PMEM 命名空间的容量。它还表明是否对命名空间应用了如 BTT 这样的地址抽象。请注意，传统的分区表（如 GPT/MBR）位于 PMEM 命名空间之上，或如果存在则位于如 BTT 这样的地址抽象之上，但分区支持正逐步被废弃。
概述
========

LIBNVDIMM 子系统提供了由平台固件或设备驱动程序描述的持久内存(PMEM)支持。在基于ACPI的系统中，平台固件通过ACPI 6中的NFIT（非易失性内存固件接口表）传达持久内存资源。尽管LIBNVDIMM子系统的实现是通用的，并且支持前NFIT平台，但其设计主要遵循了支持ACPI 6定义下的NVDIMM资源所需的能力超集。最初的实现支持NFIT中描述的块窗口孔能力，但随后该支持被放弃，并且从未在产品中发布。

支持文档
--------------------

ACPI 6:
	https://www.uefi.org/sites/default/files/resources/ACPI_6.0.pdf
NVDIMM命名空间:
	https://pmem.io/documents/NVDIMM_Namespace_Spec.pdf
DSM接口示例:
	https://pmem.io/documents/NVDIMM_DSM_Interface_Example.pdf
驱动编写指南:
	https://pmem.io/documents/NVDIMM_Driver_Writers_Guide.pdf

Git仓库
---------

LIBNVDIMM:
	https://git.kernel.org/cgit/linux/kernel/git/nvdimm/nvdimm.git
LIBNDCTL:
	https://github.com/pmem/ndctl.git


LIBNVDIMM PMEM
==============

在NFIT出现之前，非易失性内存以各种特设的方式向系统描述。通常只提供最基本的描述，即一个系统物理地址范围，在系统断电后写入的内容保持不变。现在，NFIT规范不仅标准化了PMEM的描述，而且还规定了用于控制和配置PMEM的平台消息传递入口点。
PMEM（nd_pmem.ko）：驱动一个系统物理地址范围。这个范围在系统内存中是连续的，可能跨越多个DIMM进行交错（硬件内存控制器条带）。当交错时，平台可以选择性地提供参与交错的DIMM的详细信息。
值得注意的是，当检测到标记功能（找到EFI命名空间标签索引块）时，默认情况下不会创建块设备，因为用户空间至少需要对PMEM范围分配一次DPA。相比之下，一旦注册，ND_NAMESPACE_IO范围可以立即附加到nd_pmem。这种模式被称为无标签或“传统”模式。
PMEM-区域、原子扇区和DAX
-------------------------------------

对于需要原子扇区更新保证的应用程序或文件系统，可以在PMEM设备或分区上注册BTT。参见
LIBNVDIMM/NDCTL: 块转换表 “btt”

示例NVDIMM平台
=======================

在本文档的其余部分中，将参考以下图示来举例说明sysfs布局：

                               (a)               (b)           DIMM
            +-------------------+--------+--------+--------+
  +------+  |       pm0.0       |  free  | pm1.0  |  free  |    0
  | imc0 +--+- - - region0- - - +--------+        +--------+
  +--+---+  |       pm0.0       |  free  | pm1.0  |  free  |    1
     |      +-------------------+--------v        v--------+
  +--+---+                               |                 |
  | cpu0 |                                     region1
  +--+---+                               |                 |
     |      +----------------------------^        ^--------+
  +--+---+  |           free             | pm1.0  |  free  |    2
  | imc1 +--+----------------------------|        +--------+
  +------+  |           free             | pm1.0  |  free  |    3
            +----------------------------+--------+--------+

在这个平台上，我们有四个DIMM和两个位于一个插槽中的内存控制器。每个PMEM交错集由一个动态分配ID的区域设备标识。
1. DIMM0和DIMM1的第一部分交错为REGION0。在REGION0-SPA范围内创建了一个PMEM命名空间，跨越了DIMM0和DIMM1的大部分，并具有用户指定的名称“pm0.0”。该交错系统物理地址范围的一部分留空以便定义另一个PMEM命名空间。
2. 在DIMM0和DIMM1的最后一部分，我们有一个交错的系统物理地址范围，REGION1，它也跨越了DIMM2和DIMM3。REGION1的一部分被分配给了名为“pm1.0”的PMEM命名空间。
此总线由内核在加载了来自tools/testing/nvdimm的nfit_test.ko模块后，在设备/sys/devices/platform/nfit_test.0下提供。此模块是LIBNVDIMM和acpi_nfit.ko驱动程序的单元测试。
LIBNVDIMM内核设备模型和LIBNDCTL用户空间API
========================================================

以下是关于LIBNVDIMM sysfs布局及其通过LIBNDCTL API查看的对象层次结构图的描述。示例sysfs路径和图表与示例NVDIMM平台相关，该平台也是LIBNDCTL单元测试中使用的LIBNVDIMM总线。
LIBNDCTL: 上下文
-----------------

LIBNDCTL库中的每个API调用都需要一个上下文，其中包含日志记录参数和其他库实例状态。该库基于libabc模板：

	https://git.kernel.org/cgit/linux/kernel/git/kay/libabc.git

LIBNDCTL: 创建新的库上下文示例
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

	struct ndctl_ctx *ctx;

	if (ndctl_new(&ctx) == 0)
		return ctx;
	else
		return NULL;

LIBNVDIMM/LIBNDCTL: 总线
-----------------------

一个总线与一个NFIT之间存在一对一的关系。当前对于基于ACPI的系统，预期只有一个全局平台NFIT。
### 注释：可以非常容易地注册多个NFITs，规范本身并不禁止这样做。基础设施支持多个总线，并且我们利用这种能力在单元测试中测试多种NFIT配置。

### LIBNVDIMM: 控制类设备在 `/sys/class`
---------------------------------------------

这个字符设备接受DSM消息并将其传递给通过其NFIT句柄标识的DIMM：

```
/sys/class/nd/ndctl0
|-- dev
|-- device -> ../../../ndbus0
|-- subsystem -> ../../../../../../../class/nd
```

### LIBNVDIMM: 总线
--------------

```
struct nvdimm_bus *nvdimm_bus_register(struct device *parent,
       struct nvdimm_bus_descriptor *nfit_desc);

/sys/devices/platform/nfit_test.0/ndbus0
|-- commands
|-- nd
|-- nfit
|-- nmem0
|-- nmem1
|-- nmem2
|-- nmem3
|-- power
|-- provider
|-- region0
|-- region1
|-- region2
|-- region3
|-- region4
|-- region5
|-- uevent
`-- wait_probe
```

### LIBNDCTL: 总线枚举示例
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

找到描述示例NVDIMM平台中的总线的总线句柄：

```c
static struct ndctl_bus *get_bus_by_provider(struct ndctl_ctx *ctx,
			const char *provider)
{
    struct ndctl_bus *bus;

    ndctl_bus_foreach(ctx, bus)
        if (strcmp(provider, ndctl_bus_get_provider(bus)) == 0)
            return bus;

    return NULL;
}

bus = get_bus_by_provider(ctx, "nfit_test.0");
```

### LIBNVDIMM/LIBNDCTL: DIMM (NMEM)
-------------------------------

DIMM设备提供了一个用于向硬件发送命令的字符设备，并且它是一个LABEL容器。如果DIMM由NFIT定义，则可选的'nfit'属性子目录可用于添加NFIT特定信息。
请注意，内核设备名称为“DIMMs”的是“nmemX”。NFIT通过“内存设备到系统物理地址范围映射结构”来描述这些设备，并没有要求它们实际上是物理DIMMs，因此我们使用一个更通用的名字。

### LIBNVDIMM: DIMM (NMEM)
^^^^^^^^^^^^^^^^^^^^^^

```
struct nvdimm *nvdimm_create(struct nvdimm_bus *nvdimm_bus, void *provider_data,
        const struct attribute_group **groups, unsigned long flags,
        unsigned long *dsm_mask);

/sys/devices/platform/nfit_test.0/ndbus0
|-- nmem0
|   |-- available_slots
|   |-- commands
|   |-- dev
|   |-- devtype
|   |-- driver -> ../../../../../bus/nd/drivers/nvdimm
|   |-- modalias
|   |-- nfit
|       |-- device
|       |-- format
|       |-- handle
|       |-- phys_id
|       |-- rev_id
|       |-- serial
|       `-- vendor
|   |-- state
|   |-- subsystem -> ../../../../../bus/nd
|   `-- uevent
|-- nmem1
[..]
```

### LIBNDCTL: DIMM枚举示例
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

注意，在这个例子中，我们假设由NFIT定义的DIMMs，它们通过“nfit_handle”来识别，这是一个32位值，其中：

- 位3:0 DIMM在内存通道内的编号
- 位7:4 内存通道编号
- 位11:8 内存控制器ID
- 位15:12 插槽ID（如果存在节点控制器，则在节点控制器范围内）
- 位27:16 节点控制器ID
- 位31:28 预留

```c
static struct ndctl_dimm *get_dimm_by_handle(struct ndctl_bus *bus,
       unsigned int handle)
{
    struct ndctl_dimm *dimm;

    ndctl_dimm_foreach(bus, dimm)
        if (ndctl_dimm_get_handle(dimm) == handle)
            return dimm;

    return NULL;
}

#define DIMM_HANDLE(n, s, i, c, d) \
    (((n & 0xfff) << 16) | ((s & 0xf) << 12) | ((i & 0xf) << 8) \
     | ((c & 0xf) << 4) | (d & 0xf))

dimm = get_dimm_by_handle(bus, DIMM_HANDLE(0, 0, 0, 0, 0));
```

### LIBNVDIMM/LIBNDCTL: 区域
--------------------------

为每个PMEM交错集/范围注册一个通用的REGION设备。根据示例，“nfit_test.0”总线上有2个PMEM区域。区域的主要作用是作为“映射”的容器。映射是一个<DIMM, DPA起始偏移, 长度>元组。
LIBNVDIMM为REGION设备提供了内置驱动程序。此驱动程序负责解析所有LABEL（如果存在），然后为nd_pmem驱动程序生成NAMESPACE设备。

除了“映射”的通用属性、“交错方式”和“大小”之外，REGION设备还导出一些便利属性。“nstype”表示此区域生成的命名空间设备的整型类型，“devtype”复制udev在‘add’事件时存储的DEVTYPE变量，“modalias”复制udev在‘add’事件时存储的MODALIAS变量，最后，可选的“spa_index”在区域由SPA定义的情况下提供。

### LIBNVDIMM: 区域
```
struct nd_region *nvdimm_pmem_region_create(struct nvdimm_bus *nvdimm_bus,
        struct nd_region_desc *ndr_desc);

/sys/devices/platform/nfit_test.0/ndbus0
|-- region0
|   |-- available_size
|   |-- btt0
|   |-- btt_seed
|   |-- devtype
|   |-- driver -> ../../../../../bus/nd/drivers/nd_region
|   |-- init_namespaces
|   |-- mapping0
|   |-- mapping1
|   |-- mappings
|   |-- modalias
|   |-- namespace0.0
|   |-- namespace_seed
|   |-- numa_node
|   |-- nfit
|       `-- spa_index
|   |-- nstype
|   |-- set_cookie
|   |-- size
|   |-- subsystem -> ../../../../../bus/nd
|   `-- uevent
|-- region1
[..]
```

### LIBNDCTL: 区域枚举示例
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

基于NFIT唯一数据（如“spa_index”，即交错集ID）的区域检索例程：

```c
static struct ndctl_region *get_pmem_region_by_spa_index(struct ndctl_bus *bus,
       unsigned int spa_index)
{
    struct ndctl_region *region;

    ndctl_region_foreach(bus, region) {
        if (ndctl_region_get_type(region) != ND_DEVICE_REGION_PMEM)
            continue;
        if (ndctl_region_get_spa_index(region) == spa_index)
            return region;
    }
    return NULL;
}
```

### LIBNVDIMM/LIBNDCTL: 命名空间
-----------------------------

一个REGION，在解决了DPA别名和LABEL指定边界后，会呈现一个或多个“命名空间”设备。当前，“命名空间”设备的到来会触发nd_pmem驱动程序加载和注册磁盘/块设备。

### LIBNVDIMM: 命名空间
^^^^^^^^^^^^^^^^^^^^

以下是两种主要类型的NAMESPACE的样本布局，其中namespace0.0代表DIMM信息支持的PMMEM（注意它有一个'uuid'属性），而namespace1.0代表匿名PMMEM命名空间（注意由于不支持LABEL所以没有'uuid'属性）：

```
/sys/devices/platform/nfit_test.0/ndbus0/region0/namespace0.0
|-- alt_name
|-- devtype
|-- dpa_extents
|-- force_raw
|-- modalias
|-- numa_node
|-- resource
|-- size
|-- subsystem -> ../../../../../../bus/nd
|-- type
|-- uevent
`-- uuid
/sys/devices/platform/nfit_test.1/ndbus1/region1/namespace1.0
|-- block
|   `-- pmem0
|-- devtype
|-- driver -> ../../../../../../bus/nd/drivers/pmem
|-- force_raw
|-- modalias
|-- numa_node
|-- resource
|-- size
|-- subsystem -> ../../../../../../bus/nd
|-- type
`-- uevent
```

### LIBNDCTL: 命名空间枚举示例
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
命名空间相对于其父区域进行索引，例如下面的示例。
这些索引大多从启动到启动都是静态的，但子系统在这方面不做任何保证。对于静态命名空间标识符，请使用其“uuid”属性。

```c
static struct ndctl_namespace
*get_namespace_by_id(struct ndctl_region *region, unsigned int id)
{
    struct ndctl_namespace *ndns;

    ndctl_namespace_foreach(region, ndns)
            if (ndctl_namespace_get_id(ndns) == id)
                    return ndns;

    return NULL;
}
```

**LIBNDCTL：创建命名空间示例**

如果给定区域有足够的可用容量来创建一个新的命名空间，则空闲命名空间会由内核自动创建。命名空间实例化涉及找到一个空闲的命名空间并对其进行配置。大多数情况下，设置命名空间属性可以以任意顺序进行，唯一约束是“uuid”必须在“size”之前设置。这使得内核能够使用静态标识符内部跟踪DPA分配。

```c
static int configure_namespace(struct ndctl_region *region,
               struct ndctl_namespace *ndns,
               struct namespace_parameters *parameters)
{
    char devname[50];

    snprintf(devname, sizeof(devname), "namespace%d.%d",
                     ndctl_region_get_id(region), parameters->id);

    ndctl_namespace_set_alt_name(ndns, devname);
    /* 'uuid' 必须在设置大小前设置！*/
    ndctl_namespace_set_uuid(ndns, parameters->uuid);
    ndctl_namespace_set_size(ndns, parameters->size);
    /* 与 pmem 命名空间不同，blk 命名空间具有扇区大小 */
    if (parameters->lbasize)
            ndctl_namespace_set_sector_size(ndns, parameters->lbasize);
    ndctl_namespace_enable(ndns);
}
```

**为何采用术语 “命名空间”？**

1. 为什么不使用“卷”？“卷”可能会使ND（libnvdimm子系统）与像device-mapper这样的卷管理器混淆。
2. 该术语最初用于描述可以在NVMe控制器中创建的子设备（参见NVMe规范：https://www.nvmexpress.org/specifications/），而NFIT命名空间旨在与NVMe命名空间的功能和可配置性相匹配。

**LIBNVDIMM/LIBNDCTL：块转换表 “btt”**

BTT（设计文档：https://pmem.io/2014/09/23/btt.html）是面向整个命名空间的一种“地址抽象”的命名空间特性驱动程序。

**LIBNVDIMM：btt布局**

每个区域都会至少有一个BTT设备作为种子设备。要激活它，需要设置“namespace”，“uuid”，和“sector_size”属性，并根据区域类型将设备绑定到nd_pmem或nd_blk驱动程序：

```bash
/sys/devices/platform/nfit_test.1/ndbus0/region0/btt0/
|-- namespace
|-- delete
|-- devtype
|-- modalias
|-- numa_node
|-- sector_size
|-- subsystem -> ../../../../../bus/nd
|-- uevent
`-- uuid
```

**LIBNDCTL：创建btt示例**

类似于命名空间，每个区域都会自动创建一个空闲的BTT设备。每次这个“种子”btt设备被配置并启用时，就会创建一个新的种子。创建BTT配置涉及两个步骤：找到空闲的BTT并将其分配给消费一个命名空间。

```c
static struct ndctl_btt *get_idle_btt(struct ndctl_region *region)
{
    struct ndctl_btt *btt;

    ndctl_btt_foreach(region, btt)
            if (!ndctl_btt_is_enabled(btt)
                    && !ndctl_btt_is_configured(btt))
                return btt;

    return NULL;
}

static int configure_btt(struct ndctl_region *region,
             struct btt_parameters *parameters)
{
    btt = get_idle_btt(region);

    ndctl_btt_set_uuid(btt, parameters->uuid);
    ndctl_btt_set_sector_size(btt, parameters->sector_size);
    ndctl_btt_set_namespace(btt, parameters->ndns);
    /* 关闭原始模式设备 */
    ndctl_namespace_disable(parameters->ndns);
    /* 启用btt访问 */
    ndctl_btt_enable(btt);
}
```

一旦实例化后，一个新的非活动btt种子设备将会出现在该区域内。一旦从BTT移除“命名空间”，该实例的BTT设备将会被删除或重置为默认值。这种删除仅在设备模型层面。为了销毁一个BTT，“信息块”需要被销毁。注意，要销毁一个BTT，需要以原始模式写入介质。默认情况下，内核会自动检测BTT的存在并禁用原始模式。可以通过启用命名空间的原始模式来抑制此自动检测行为，即通过API `ndctl_namespace_set_raw_mode()`。

**LIBNDCTL总结图**

对于上述示例，以下是通过LIBNDCTL API所看到的对象视图：

```
              +---+
              |CTX|
              +-+-+
                |
  +-------+     |
  | DIMM0 <-+   |      +---------+   +--------------+  +---------------+
  +-------+ |   |    +-> REGION0 +---> NAMESPACE0.0 +--> PMEM8 "pm0.0" |
  | DIMM1 <-+ +-v--+ | +---------+   +--------------+  +---------------+
  +-------+ +-+BUS0+-| +---------+   +--------------+  +----------------------+
  | DIMM2 <-+ +----+ +-> REGION1 +---> NAMESPACE1.0 +--> PMEM6 "pm1.0" | BTT1 |
  +-------+ |        | +---------+   +--------------+  +---------------+------+
  | DIMM3 <-+
  +-------+
```
