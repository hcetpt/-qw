SPDX 许可证标识符: GPL-2.0

===============================================
ARM 虚拟中断转换服务 (ITS)
===============================================

支持的设备类型:
  KVM_DEV_TYPE_ARM_VGIC_ITS    ARM 中断转换服务控制器

ITS 允许将 MSI(-X) 中断注入到客户机中。此扩展是可选的。创建一个虚拟 ITS 控制器还需要主机上的 GICv3（参见 arm-vgic-v3.txt），但不依赖于是否具有物理 ITS 控制器。每个客户机可以有多个 ITS 控制器，每个控制器必须有一个独立且不重叠的 MMIO 区域。
组
======

KVM_DEV_ARM_VGIC_GRP_ADDR
-------------------------

  属性:
    KVM_VGIC_ITS_ADDR_TYPE (读写, 64位)
      GICv3 ITS 控制寄存器帧在客户机物理地址空间中的基地址
此地址需要对齐至 64KB，并且该区域覆盖 128KB。

错误：

    =======  =================================================
    -E2BIG   地址超出可寻址的 IPA 范围
    -EINVAL  地址未正确对齐
    -EEXIST  地址已配置
    -EFAULT  attr->addr 的用户指针无效
    -ENODEV  错误的属性或不支持 ITS
    =======  =================================================

KVM_DEV_ARM_VGIC_GRP_CTRL
-------------------------

  属性:
    KVM_DEV_ARM_VGIC_CTRL_INIT
      请求初始化 ITS，在 kvm_device_attr.addr 中没有附加参数
KVM_DEV_ARM_ITS_CTRL_RESET
      重置 ITS，在 kvm_device_attr.addr 中没有附加参数
参见“ITS 重置状态”部分
KVM_DEV_ARM_ITS_SAVE_TABLES
      将 ITS 表数据保存到客户机内存中，在相应寄存器/表项中由客户机提供的位置。如果用户空间需要一种脏页跟踪机制来识别哪些页面被保存过程修改，则应使用位图，即使使用其他机制来跟踪 vCPU 弄脏的内存。
客体内存中的表布局定义了一个ABI。这些条目按照上一段描述的小端格式排列。

`KVM_DEV_ARM_ITS_RESTORE_TABLES`
      从客体RAM恢复ITS表到ITS内部结构。
GICV3必须在恢复ITS之前恢复，并且所有ITS寄存器（除了GITS_CTLR）也必须在恢复ITS表之前恢复。
只读寄存器GITS_IIDR也必须在调用`KVM_DEV_ARM_ITS_RESTORE_TABLES`之前恢复，因为IIDR修订字段编码了ABI修订版本。
恢复GICv3/ITS时的预期顺序在“ITS Restore Sequence”部分中描述。

错误：

    =======  ==========================================================
     -ENXIO  在设置此属性前，ITS未按要求正确配置
    -ENOMEM  分配ITS内部数据时内存不足
    -EINVAL  恢复的数据不一致
    -EFAULT  客体RAM访问无效
    -EBUSY   一个或多个VCPUS正在运行
    -EACCES  虚拟ITS由物理GICv4 ITS支持，并且没有GICv4.1无法获取状态
    =======  ==========================================================

`KVM_DEV_ARM_VGIC_GRP_ITS_REGS`
-----------------------------

  属性：
      `kvm_device_attr` 的 `attr` 字段编码了相对于ITS控制帧基地址（ITS_base）的ITS寄存器偏移量
`kvm_device_attr.addr` 指向一个 `__u64` 值，无论所寻址寄存器的宽度（32/64位）。64位寄存器只能通过全长度访问。
对只读寄存器的写入操作会被内核忽略，除了以下情况：

      - GITS_CREADR。它必须恢复，否则队列中的命令将在恢复CWRITER后重新执行。GITS_CREADR必须在恢复GITS_CTLR之前恢复，因为GITS_CTLR可能会启用ITS。此外，在写入GITS_CBASER之后也必须恢复GITS_CREADR，因为写入GITS_CBASER会重置GITS_CREADR。
- GITS_IIDR。修订字段编码了表布局的ABI修订版本。
将来我们可能会实现虚拟LPI的直接注入。
这将需要升级表布局并进化ABI。在调用 `KVM_DEV_ARM_ITS_RESTORE_TABLES` 之前必须恢复 `GITS_IIDR`。
对于其他寄存器，获取或设置寄存器的效果与在真实硬件上读写寄存器相同。

错误：

    =======  ====================================================
    -ENXIO   偏移量不对应任何支持的寄存器
    -EFAULT  attr->addr 的用户指针无效
    -EINVAL  偏移量未对齐到64位
    -EBUSY   一个或多个VCPUS正在运行
    =======  ====================================================

ITS 恢复顺序：
---------------------

在恢复 GIC 和 ITS 时必须遵循以下顺序：

a) 恢复所有客户内存并创建 VCPUs
b) 恢复所有重分发器
c) 提供 ITS 基地址 (KVM_DEV_ARM_VGIC_GRP_ADDR)
d) 按以下顺序恢复 ITS：

     1. 恢复 GITS_CBASER
     2. 恢复所有其他 `GITS_` 寄存器（除了 GITS_CTLR！）
     3. 加载 ITS 表数据 (KVM_DEV_ARM_ITS_RESTORE_TABLES)
     4. 恢复 GITS_CTLR

然后可以启动 VCPUs

ITS 表 ABI REV0：
-------------------

ABI 修订版 0 仅支持虚拟 GICv3 的功能，并不支持带有直接注入虚拟中断功能的虚拟 GICv4 以支持嵌套的虚拟机管理程序。
设备表和 ITT 分别由 DeviceID 和 EventID 索引。集合表不按 CollectionID 索引，且集合中的条目无特定顺序列出。
所有条目均为 8 字节。

设备表条目 (DTE) ::

   bits:     | 63| 62 ... 49 | 48 ... 5 | 4 ... 0 |
   values:   | V |   next    | ITT_addr |  Size   |

 其中：

 - V 表示该条目是否有效。如果无效，则其他字段没有意义
 - next: 如果这是最后一个条目，则等于 0；否则对应下一个 DTE 的 DeviceID 偏移量，上限为 2^14 -1
 - ITT_addr 匹配 ITT 地址的 [51:8] 位（256 字节对齐）
 - Size 指定 EventID 支持的位数减一

集合表条目 (CTE) ::

   bits:     | 63| 62 ..  52  | 51 ... 16 | 15  ...   0 |
   values:   | V |    RES0    |  RDBase   |    ICID     |

 其中：

 - V 表示该条目是否有效。如果无效，则其他字段没有意义
RES0：保留字段，应为零或保持不变的行为
- RDBase 是 PE 编号（具有 GICR_TYPER.Processor_Number 的语义）
- ICID 是集合 ID

中断转换条目 (ITE)：

   位:     | 63 ... 48 | 47 ... 16 | 15 ... 0 |
   值:     |    next   |   pINTID  |  ICID    |

 其中：

- next：如果这是最后一个条目，则等于 0；否则它对应于下一个 ITE 的 EventID 偏移量，上限为 2^16 - 1
- pINTID 是物理 LPI ID；如果为零，则表示该条目无效，其他字段也无意义
- ICID 是集合 ID

ITS 重置状态：
---------------

重置命令将 ITS 恢复到其最初创建和初始化时的状态。当重置命令返回时，以下事项得到保证：

- ITS 未启用且处于静止状态
  GITS_CTLR.Enabled = 0, Quiescent = 1
- 内部没有缓存的状态
- 未使用任何集合或设备表
  GITS_BASER<n>.Valid = 0
- GITS_CBASER = 0, GITS_CREADR = 0, GITS_CWRITER = 0
- ABI 版本保持不变，仍为 ITS 设备首次创建时设置的版本
