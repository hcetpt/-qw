SPDX 许可证标识符: GPL-2.0

===========================
超调用操作码 (hcalls)
===========================

概述
=========

在 64 位 Power Book3S 平台上，虚拟化基于 PAPR 规范 [1]_，该规范描述了来宾操作系统运行时环境以及它如何与管理程序进行交互以执行特权操作。目前有两种符合 PAPR 规范的管理程序：

- **IBM PowerVM (PHYP)**：IBM 的专有管理程序支持 AIX、IBM-i 和 Linux 作为受支持的来宾（称为逻辑分区或 LPAR）。它支持完整的 PAPR 规范。
- **Qemu/KVM**：支持在 PPC64 Linux 主机上运行的 PPC64 Linux 来宾。尽管它仅实现了称为 LoPAPR [2]_ 的 PAPR 规范的一个子集。

在 PPC64 架构中，运行在 PAPR 管理程序之上的来宾内核被称为 *pSeries 来宾*。pseries 来宾在监管模式下运行（HV=0），并且当需要执行管理程序权限的操作 [3]_ 或其他由管理程序管理的服务时，必须向管理程序发出超调用。

因此，超调用（hcall）本质上是 pSeries 来宾请求管理程序代表来宾执行特权操作的一种方式。来宾会带着必要的输入操作数发起超调用。管理程序执行完特权操作后将返回一个状态码和输出操作数给来宾。

HCALL ABI
=========
pSeries 来宾与 PAPR 管理程序之间的 hcall 的 ABI 规范在参考文献 [2]_ 的第 14.5.3 节中有详细说明。切换到管理程序上下文是通过指令 **HVCS** 完成的，该指令期望将 hcall 的操作码设置在 *r3* 中，并且任何输入参数都提供在寄存器 *r4-r12* 中。如果值需要通过内存缓冲区传递，则该缓冲区中的数据应采用大端字节序。

一旦管理程序处理完 'HVCS' 指令并将控制权返回给来宾后，hcall 的返回值就会出现在 *r3* 中，而任何输出值则会返回在寄存器 *r4-r12* 中。同样地，对于输入参数，任何存储在内存缓冲区中的输出值也将采用大端字节序。

PowerPC 架构代码提供了方便的封装函数名为 **plpar_hcall_xxx**，定义在一个特定架构的头文件 [4]_ 中，用于从作为 pSeries 来宾运行的 Linux 内核中发出 hcalls。

寄存器约定
====================

任何 hcall 都应遵循 “64 位 ELF V2 ABI 规范: Power 架构”[5]_ 第 2.2.1.1 节中所描述的相同寄存器约定。下面的表格总结了这些约定：

+----------+----------+-------------------------------------------+
| 寄存器   | 可变性   | 目的                                      |
| 范围     | (Y/N)    |                                            |
+==========+==========+===========================================+
|   r0     |    Y     |  可选使用                                   |
+----------+----------+-------------------------------------------+
|   r1     |    N     |  栈指针                                    |
+----------+----------+-------------------------------------------+
|   r2     |    N     |  TOC                                       |
+----------+----------+-------------------------------------------+
|   r3     |    Y     |  hcall 操作码/返回值                       |
+----------+----------+-------------------------------------------+
|  r4-r10  |    Y     |  输入和输出值                              |
+----------+----------+-------------------------------------------+
|   r11    |    Y     |  可选使用/环境指针                         |
+----------+----------+-------------------------------------------+
|   r12    |    Y     |  可选使用/全局入口点处的函数入口地址       |
+----------+----------+-------------------------------------------+
|   r13    |    N     |  线程指针                                  |
+----------+----------+-------------------------------------------+
|  r14-r31 |    N     |  局部变量                                  |
+----------+----------+-------------------------------------------+
|    LR    |    Y     |  链接寄存器                                |
+----------+----------+-------------------------------------------+
|   CTR    |    Y     |  循环计数器                                |
+----------+----------+-------------------------------------------+
|   XER    |    Y     |  固定点异常寄存器.                          |
+----------+----------+-------------------------------------------+
|  CR0-1   |    Y     |  条件寄存器字段.                            |
+----------+----------+-------------------------------------------+
|  CR2-4   |    N     |  条件寄存器字段.                            |
+----------+----------+-------------------------------------------+
|  CR5-7   |    Y     |  条件寄存器字段.                            |
+----------+----------+-------------------------------------------+
|  其他    |    N     |                                            |
+----------+----------+-------------------------------------------+

DRC 和 DRC 索引
=================
::

     DR1                                  来宾
     +--+        +------------+         +---------+
     |  | <----> |            |         |  用户   |
     +--+  DRC1  |            |   DRC   |  空间   |
                 |    PAPR    |  索引  +---------+
     DR2         | 管理程序   |         |         |
     +--+        |            | <-----> |  内核   |
     |  | <----> |            |  hcall  |         |
     +--+  DRC2  +------------+         +---------+

PAPR 管理程序将共享硬件资源（如 PCI 设备、NVDIMMs 等）作为动态资源 (DR) 提供给 LPAR 使用。当 DR 分配给 LPAR 时，PHYP 创建了一个名为动态资源连接器 (DRC) 的数据结构来管理 LPAR 的访问。LPAR 通过一个不透明的 32 位数字（称为 DRC 索引）引用 DRC。DRC 索引值通过设备树提供给 LPAR，在那里它作为与 DR 关联的设备树节点中的属性存在。

HCALL 返回值
===================

在处理完 hcall 后，管理程序会在 *r3* 中设置返回值，指示 hcall 成功与否。在失败的情况下，错误码将指示出错原因。这些代码在特定架构的头文件 [4]_ 中定义并记录。
在某些情况下，一个hcall（hypervisor call）可能需要较长时间来完成，并且可能需要多次调用才能完全处理。这些hcall通常会在其参数列表中接受一个不透明的值 *continue-token*，而返回值为 *H_CONTINUE* 表示hypervisor尚未完成对该hcall的处理。
为了发起这样的hcall，客户机需要在初始调用时设置 *continue-token == 0*，并在后续每次hcall中使用hypervisor返回的 *continue-token* 值，直到hypervisor返回非 *H_CONTINUE* 的值为止。

### HCALL 操作码

以下是PHYP支持的部分HCALL操作码。对于相应操作码的值，请参阅特定架构的头文件[4]_：

**H_SCM_READ_METADATA**

- 输入: *drcIndex, offset, buffer-address, numBytesToRead*
- 输出: *numBytesRead*
- 返回值: *H_Success, H_Parameter, H_P2, H_P3, H_Hardware*

给定一个NVDIMM的DRC索引，从与之关联的元数据区域指定偏移处读取N字节，并将其复制到提供的缓冲区中。元数据区域存储诸如标签信息、坏块等配置信息。元数据区域位于NVDIMM存储区域之外，因此提供了单独的访问语义。

**H_SCM_WRITE_METADATA**

- 输入: *drcIndex, offset, data, numBytesToWrite*
- 输出: *None*
- 返回值: *H_Success, H_Parameter, H_P2, H_P4, H_Hardware*

给定一个NVDIMM的DRC索引，在指定偏移处向与其关联的元数据区域写入N字节，数据来自提供的缓冲区。

**H_SCM_BIND_MEM**

- 输入: *drcIndex, startingScmBlockIndex, numScmBlocksToBind, targetLogicalMemoryAddress, continue-token*
- 输出: *continue-token, targetLogicalMemoryAddress, numScmBlocksToBound*
- 返回值: *H_Success, H_Parameter, H_P2, H_P3, H_P4, H_Overlap, H_Too_Big, H_P5, H_Busy*

给定一个NVDIMM的DRC索引，将连续的SCM区块范围 *(startingScmBlockIndex, startingScmBlockIndex+numScmBlocksToBind)* 映射到客户机物理地址空间中的 *targetLogicalMemoryAddress*。如果 *targetLogicalMemoryAddress == 0xFFFFFFFF_FFFFFFFF*，则hypervisor会为客户机分配一个目标地址。如果客户机对正在绑定的SCM区块有一个有效的PTE条目，则此HCALL可能会失败。

**H_SCM_UNBIND_MEM**

- 输入: *drcIndex, startingScmLogicalMemoryAddress, numScmBlocksToUnbind*
- 输出: *numScmBlocksUnbound*
- 返回值: *H_Success, H_Parameter, H_P2, H_P3, H_In_Use, H_Overlap, H_Busy, H_LongBusyOrder1mSec, H_LongBusyOrder10mSec*

给定一个NVDIMM的DRC索引，从客户机物理地址空间中取消映射 *numScmBlocksToUnbind* 个SCM区块，这些区块从 *startingScmLogicalMemoryAddress* 开始。如果客户机对正在取消映射的SCM区块有一个有效的PTE条目，则此HCALL可能会失败。

**H_SCM_QUERY_BLOCK_MEM_BINDING**

- 输入: *drcIndex, scmBlockIndex*
- 输出: *Guest-Physical-Address*
- 返回值: *H_Success, H_Parameter, H_P2, H_NotFound*

给定一个DRC索引和一个SCM区块索引，返回该SCM区块映射到的客户机物理地址。

**H_SCM_QUERY_LOGICAL_MEM_BINDING**

- 输入: *Guest-Physical-Address*
- 输出: *drcIndex, scmBlockIndex*
- 返回值: *H_Success, H_Parameter, H_P2, H_NotFound*

给定一个客户机物理地址，返回映射到该地址的DRC索引和SCM区块。

**H_SCM_UNBIND_ALL**

- 输入: *scmTargetScope, drcIndex*
- 输出: *None*
- 返回值: *H_Success, H_Parameter, H_P2, H_P3, H_In_Use, H_Busy, H_LongBusyOrder1mSec, H_LongBusyOrder10mSec*

根据目标范围，从LPAR内存中取消映射所有NVDIMM的所有SCM区块，或者取消映射单个由其drcIndex标识的NVDIMM的所有SCM区块。
**H_SCM_HEALTH**

| 输入: drcIndex |
| 输出: *health-bitmap (r4), health-bit-valid-bitmap (r5)* |
| 返回值: *H_Success, H_Parameter, H_Hardware* |

根据给定的DRC索引返回PMEM设备的预测性故障和整体健康状况信息。在`health-bitmap`中被设置的位表示一个或多个PMEM设备状态（如下表所示），而`health-bit-valid-bitmap`则指示`health-bitmap`中的哪些位是有效的。位报告采用逆序方式，例如，值`0xC400000000000000`表示位0、1和5有效。
健康位图标志：

+------+-----------------------------------------------------------------------+
|  位  |               定义                                                  |
+======+=======================================================================+
|  00  | PMEM设备无法持久化内存内容。                                         |
|      | 如果系统断电，则不会保存任何数据。                                    |
+------+-----------------------------------------------------------------------+
|  01  | PMEM设备未能持久化内存内容。要么是在断电时未能成功保存内容，        |
|      | 要么是在启动时未能正确恢复内容。                                     |
+------+-----------------------------------------------------------------------+
|  02  | PMEM设备的内容从上次启动时持久化。上一次启动的数据已成功恢复。     |
+------+-----------------------------------------------------------------------+
|  03  | PMEM设备的内容未从上次启动时持久化。没有来自上一次启动的数据可恢复。|
+------+-----------------------------------------------------------------------+
|  04  | PMEM设备剩余内存寿命极低。                                           |
+------+-----------------------------------------------------------------------+
|  05  | 因故障PMEM设备将在下次启动时被隔离。                                |
+------+-----------------------------------------------------------------------+
|  06  | 由于当前平台健康状况，PMEM设备无法持久化内容。                       |
|      | 硬件故障可能阻止数据的保存或恢复。                                   |
+------+-----------------------------------------------------------------------+
|  07  | 在某些条件下PMEM设备无法持久化内存内容。                             |
+------+-----------------------------------------------------------------------+
|  08  | PMEM设备已加密。                                                     |
+------+-----------------------------------------------------------------------+
|  09  | PMEM设备已成功完成请求的擦除或安全擦除过程。                         |
+------+-----------------------------------------------------------------------+
| 10:63 | 预留 / 未使用                                                        |
+------+-----------------------------------------------------------------------+


**H_SCM_PERFORMANCE_STATS**

| 输入: drcIndex, resultBuffer 地址 |
| 输出: 无 |
| 返回值: *H_Success, H_Parameter, H_Unsupported, H_Hardware, H_Authority, H_Privilege* |

根据给定的DRC索引收集NVDIMM的性能统计信息，并将其复制到`resultBuffer`中。

**H_SCM_FLUSH**

| 输入: *drcIndex, 继续令牌* |
| 输出: *继续令牌* |
| 返回值: *H_SUCCESS, H_Parameter, H_P2, H_BUSY* |

根据给定的DRC索引将数据刷新到后端NVDIMM设备。当刷新耗时较长时，此hcall会返回`H_BUSY`，此时需要多次调用该hcall才能完全处理完毕。应将输出中的`继续令牌`传递给后续对hypervisor的调用，直到该hcall完全处理完毕，此时hypervisor会返回`H_SUCCESS`或其他错误码。

参考文献
========
.. [1] "Power Architecture 平台参考"
       https://en.wikipedia.org/wiki/Power_Architecture_Platform_Reference
.. [2] "Power Architecture上的Linux平台参考"
       https://members.openpowerfoundation.org/document/dl/469
.. [3] "定义与符号" 书III-第14.5.3节
       https://openpowerfoundation.org/?resource_lib=power-isa-version-3-0
.. [4] arch/powerpc/include/asm/hvcall.h
.. [5] "64位ELF V2 ABI规范：Power Architecture"
       https://openpowerfoundation.org/?resource_lib=64-bit-elf-v2-abi-specification-power-architecture
