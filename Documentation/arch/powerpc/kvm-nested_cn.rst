### SPDX 许可标识符: GPL-2.0

====================================
POWER 架构上的嵌套 KVM
====================================

简介
============

本文档解释了如何通过使用超调用（如果虚拟化器已实现这些超调用）使来宾操作系统充当虚拟化器并运行嵌套的来宾。术语 L0、L1 和 L2 用于指代不同的软件实体。L0 是通常被称为“主机”或“虚拟化器”的虚拟化模式实体。L1 是直接在 L0 下运行的来宾虚拟机，由 L0 启动和控制。L2 是由充当虚拟化器的 L1 启动和控制的来宾虚拟机。

现有 API
============

自 2018 年起，Linux/KVM 已支持作为 L0 或 L1 的嵌套功能。

L0 代码添加如下：

   提交 8e3f5fc1045dc49fd175b978c5457f5f51e7a2ce
   作者: Paul Mackerras <paulus@ozlabs.org>
   日期: 2018 年 10 月 8 日 周一 16:31:03 +1100
   KVM: PPC: Book3S HV: 为嵌套虚拟化提供框架和超调用存根

L1 代码添加如下：

   提交 360cae313702cdd0b90f82c261a8302fecef030a
   作者: Paul Mackerras <paulus@ozlabs.org>
   日期: 2018 年 10 月 8 日 周一 16:31:04 +1100
   KVM: PPC: Book3S HV: 通过超调用进入嵌套来宾

此 API 主要通过单一的超调用 `h_enter_nested()` 运作。此调用由 L1 发起，告知 L0 使用给定状态启动一个 L2 vCPU。然后 L0 启动此 L2 并一直运行直到达到 L2 退出条件。一旦 L2 退出，L2 的状态由 L0 返回给 L1。当运行 L2 时，完整的 L2 vCPU 状态始终从 L1 转移到 L1。L0 不保存 L2 vCPU 的任何状态（除了在 L1 到 L2 入口和 L2 到 L1 出口时的短暂序列）。L0 保存的唯一状态是分区表。L1 使用 `h_set_partition_table()` 超调用来注册其分区表。L0 关于 L2 的所有其他状态都是缓存的状态（例如影子页表）。
L1 可以在不事先通知 L0 的情况下运行任何 L2 或 vCPU。它只需使用 `h_enter_nested()` 开始 vCPU。L2 和 vCPU 的创建是在每次调用 `h_enter_nested()` 时隐式完成的。
在此文档中，我们称此现有的 API 为 v1 API。

新 PAPR API
===============

新的 PAPR API 对 v1 API 进行了更改，使得创建 L2 和关联的 vCPUs 成为显式操作。在此文档中，我们将此称为 v2 API。
`h_enter_nested()` 被替换为 `H_GUEST_VCPU_RUN()`。在此之前，L1 必须明确地使用 `h_guest_create()` 创建 L2，并使用 `h_guest_create_vCPU()` 创建关联的 vCPUs。获取和设置 vCPU 状态也可以使用 `h_guest_{g|s}et` 超调用来完成。
L1 创建、运行和删除 L2 的基本执行流程如下：

- L1 和 L0 通过 `H_GUEST_{G,S}ET_CAPABILITIES()` 协商能力（通常在 L1 引导时）
- L1 请求 L0 创建一个 L2，使用 `H_GUEST_CREATE()` 并接收一个令牌

- L1 请求 L0 创建一个 L2 vCPU，使用 `H_GUEST_CREATE_VCPU()`

- L1 和 L0 使用 `H_GUEST_{G,S}ET()` 超调用来交换 vCPU 状态

- L1 请求 L0 运行 vCPU，使用 `H_GUEST_VCPU_RUN()` 超调用

- L1 删除 L2，使用 `H_GUEST_DELETE()`

以下更详细地介绍了各个超调用：

HCALL 细节
=============

本文档旨在提供对 API 的整体理解。它并不旨在提供实施 L1 或 L0 所需的所有细节。可以参考最新版本的 PAPR 获取更多详情。
所有这些 HCALL 都是由 L1 发送到 L0 的。
### H_GUEST_GET_CAPABILITIES()
--------------------------

此函数用于获取L0嵌套虚拟机监视器的能力。这包括诸如支持的CPU版本（例如POWER9、POWER10）等能力：

```plaintext
H_GUEST_GET_CAPABILITIES(uint64 flags)

参数：
  输入：
    flags：保留
  输出：
    R3：返回码
    R4：虚拟机支持的能力位图 1
```

### H_GUEST_SET_CAPABILITIES()
--------------------------

此函数用于告知L0关于L1虚拟机监视器的能力。传递的标志集与`H_GUEST_GET_CAPABILITIES()`相同。

通常，首先会调用GET，然后使用GET返回的一部分标志调用SET。这个过程允许L0和L1协商一组一致的能力：

```plaintext
H_GUEST_SET_CAPABILITIES(uint64 flags,
                         uint64 capabilitiesBitmap1)
参数：
  输入：
    flags：保留
    capabilitiesBitmap1：仅通过H_GUEST_GET_CAPABILITIES广告的能力
  输出：
    R3：返回码
    R4：如果R3 = H_P2：无效位图的数量
    R5：如果R3 = H_P2：第一个无效位图的索引
```

### H_GUEST_CREATE()
----------------

此函数用于创建一个L2。将返回一个唯一的L2标识符（类似于LPID），后续的HCALL可以使用它来识别L2：

```plaintext
H_GUEST_CREATE(uint64 flags,
               uint64 continueToken);
参数：
  输入：
    flags：保留
    continueToken：初始调用设为-1。在返回了H_Busy或H_LongBusyOrder之后的后续调用中，使用之前返回的R4中的值
输出：
  R3：返回码。值得注意的是：
    H_Not_Enough_Resources：由于虚拟机内存不足无法创建访客VCPU。参见H_GUEST_CREATE_GET_STATE(flags = takeOwnershipOfVcpuState)
  R4：如果R3 = H_Busy 或 H_LongBusyOrder -> continueToken
```

### H_GUEST_CREATE_VCPU()
---------------------

此函数用于创建与L2关联的vCPU。应传递L2 ID（从`H_GUEST_CREATE()`返回）。还应传递一个对于此L2来说唯一的vCPU ID。此vCPU ID由L1分配：

```plaintext
H_GUEST_CREATE_VCPU(uint64 flags,
                    uint64 guestId,
                    uint64 vcpuId);
参数：
  输入：
    flags：保留
    guestId：从H_GUEST_CREATE获得的ID
    vcpuId：要创建的vCPU的ID。此值必须在0到2047的范围内
  输出：
    R3：返回码。值得注意的是：
    H_Not_Enough_Resources：由于虚拟机内存不足无法创建访客VCPU。参见H_GUEST_CREATE_GET_STATE(flags = takeOwnershipOfVcpuState)
```

### H_GUEST_GET_STATE()
-------------------

此函数用于获取与L2（访客范围或vCPU特定）相关的状态。这些信息通过访客状态缓冲区（GSB）传递，这是一种标准格式，如本文档稍后所述，以下是必要的细节：

这可以获取L2范围或vCPU特定的信息。L2范围的例子是时间基准偏移或进程范围的页表信息。vCPU特定的例子是GPR或VSR。标志参数中的一个位指定此调用是L2范围还是vCPU特定的，并且GSB中的ID必须与此匹配。
L1提供一个指向GSB的指针作为此调用的参数。还提供了与要设置的状态相关的L2和vCPU ID。
L1只在GSB中写入ID和大小。L0则写入GSB中每个ID的相关值：

```plaintext
H_GUEST_GET_STATE(uint64 flags,
                  uint64 guestId,
                  uint64 vcpuId,
                  uint64 dataBuffer,
                  uint64 dataBufferSizeInBytes);
参数：
  输入：
    flags：
       第0位：getGuestWideState：请求访客的状态而不是单个VCPU的状态
       第1位：takeOwnershipOfVcpuState 表示L1正在接管VCPU状态的所有权，并且L0可以释放存储状态的存储空间。在为该VCPU调用H_GUEST_RUN_VCPU之前，需要通过H_GUEST_SET_STATE将VCPU状态返回给虚拟机。dataBuffer中的数据以虚拟机内部格式返回
       第2至63位：保留
    guestId：从H_GUEST_CREATE获得的ID
    vcpuId：通过H_GUEST_CREATE_VCPU传递给的vCPU ID
    dataBuffer：GSB的L1实际地址
       如果takeOwnershipOfVcpuState，则大小必须至少为ID=0x0001返回的大小
    dataBufferSizeInBytes：dataBuffer的大小（字节）
  输出：
    R3：返回码
    R4：如果R3 = H_Invalid_Element_Id：错误元素ID的数组索引
        如果R3 = H_Invalid_Element_Size：错误元素大小的数组索引
        如果R3 = H_Invalid_Element_Value：错误元素值的数组索引
```
### H_GUEST_SET_STATE()

此函数用于设置 L2 范围或特定 vCPU 的 L2 状态。相关信息通过“访客状态缓冲区”（GSB）传递，具体细节如下：

此函数可以设置 L2 范围或特定于 vCPU 的信息。L2 范围的例子包括时间基准偏移或进程范围的页表信息。特定于 vCPU 的例子包括通用寄存器（GPRs）或矢量寄存器（VSRs）。参数 `flags` 中的一个位指定此调用是 L2 范围还是特定于 vCPU，并且 GSB 中的 ID 必须与之匹配。
L1 在此调用中提供指向 GSB 的指针作为参数。同时提供的还有与要设置的状态关联的 L2 和 vCPU ID。
L1 写入 GSB 中的所有值，而 L0 只读取 GSB 以响应此调用：

```c
H_GUEST_SET_STATE(uint64_t flags,
                  uint64_t guestId,
                  uint64_t vcpuId,
                  uint64_t dataBuffer,
                  uint64_t dataBufferSizeInBytes);
```

**参数：**
- **输入：**
  - `flags`: 
     - 位 0: getGuestWideState: 请求整个访客的状态而不是单个 VCPU 的状态。
     - 位 1: returnOwnershipOfVcpuState 返回访客 VCPU 状态。参见 `GET_STATE` 的 `takeOwnershipOfVcpuState`。
     - 位 2-63: 保留。
  - `guestId`: 从 `H_GUEST_CREATE` 获取的 ID。
  - `vcpuId`: 传递给 `H_GUEST_CREATE_VCPU` 的 vCPU ID。
  - `dataBuffer`: GSB 的 L1 实际地址。
    如果 `takeOwnershipOfVcpuState` 为真，则大小必须至少等于 ID 为 0x0001 返回的大小。
  - `dataBufferSizeInBytes`: `dataBuffer` 的大小。
- **输出：**
  - `R3`: 返回码。
  - `R4`: 如果 `R3 = H_Invalid_Element_Id`: 错误元素 ID 的数组索引。
    如果 `R3 = H_Invalid_Element_Size`: 错误元素大小的数组索引。
    如果 `R3 = H_Invalid_Element_Value`: 错误元素值的数组索引。

### H_GUEST_RUN_VCPU()

此函数用于运行一个 L2 vCPU。L2 和 vCPU ID 作为参数传递。vCPU 使用之前通过 `H_GUEST_SET_STATE()` 设置的状态运行。当 L2 退出时，L1 将从此 hcall 继续执行。

此 hcall 还有关联的输入和输出 GSB。与 `H_GUEST_{S,G}ET_STATE()` 不同，这些 GSB 指针不是作为 hcall 的参数传递（这是出于性能考虑）。这些 GSB 的位置必须预先使用带有 ID 0x0c00 和 0x0c01 的 `H_GUEST_SET_STATE()` 函数进行注册（见下表）。

输入 GSB 可能只包含要设置的特定于 vCPU 的元素。如果不需要设置任何内容，此 GSB 也可以不包含任何元素（即 GSB 的前 4 个字节为 0）。
从hcall返回时，输出缓冲区被L0确定的元素填充。退出的原因包含在GPR4中（即NIP被放入GPR4）。返回的元素取决于退出类型。例如，如果退出原因是L2执行了hcall（GPR4 = 0xc00），则GPR3至GPR12作为输出GSB提供，因为这些状态很可能需要来服务该hcall。如果还需要额外的状态，L1可以调用H_GUEST_GET_STATE()。为了在L2中合成中断，在调用H_GUEST_RUN_VCPU()时，L1可以通过设置一个标志（作为hcall参数）来让L0在L2中合成该中断。或者，L1也可以使用H_GUEST_SET_STATE()或H_GUEST_RUN_VCPU()的输入GSB自行合成中断，以适当设置状态：

  H_GUEST_RUN_VCPU(uint64 flags,
                   uint64 guestId,
                   uint64 vcpuId,
                   uint64 dataBuffer,
                   uint64 dataBufferSizeInBytes);
参数：
  输入：
    flags:
      位0: generateExternalInterrupt: 生成外部中断
      位1: generatePrivilegedDoorbell: 生成特权门铃
      位2: sendToSystemReset: 生成系统重置中断
      位3-63: 预留
    guestId: 从H_GUEST_CREATE获得的ID
    vcpuId: 传递给H_GUEST_CREATE_VCPU的vCPU ID
  输出：
    R3: 返回码
    R4: 如果R3 = H_Success: L1 VCPU退出的原因（例如NIA）
        0x000: VCPU因未指定原因停止运行。例如，虚拟机监视器因主机分区有未决中断而停止VCPU运行。
        0x980: HDEC
        0xC00: HCALL
        0xE00: HDSI
        0xE20: HISI
        0xE40: HEA
        0xF80: HV Fac Unavail
    如果R3 = H_Invalid_Element_Id, H_Invalid_Element_Size, 或 H_Invalid_Element_Value: R4是输入缓冲区中无效元素的偏移量
H_GUEST_DELETE()
----------------

此函数用于删除一个L2。所有关联的vCPUs也会被删除。没有提供特定的vCPU删除调用
可以提供一个标志来删除所有guest。这在kdump/kexec情况下用于重置L0：

  H_GUEST_DELETE(uint64 flags,
                 uint64 guestId)
参数：
  输入：
    flags:
      位0: deleteAllGuests: 删除所有guest
      位1-63: 预留
    guestId: 从H_GUEST_CREATE获得的ID
  输出：
    R3: 返回码

Guest State Buffer
==================

Guest State Buffer (GSB)是L1和L0之间通过H_GUEST_{G,S}ET()和H_GUEST_VCPU_RUN()调用通信关于L2状态的主要方法。
状态可能与整个L2相关（如时间基准偏移），也可能与特定的L2 vCPU相关（如GPR状态）。只有L2 VCPU状态可通过H_GUEST_VCPU_RUN()设置。
GSB中的所有数据都是大端字节序（PAPR标准）

Guest状态缓冲区有一个头部，给出元素的数量，随后是GSB元素本身。
GSB头部结构如下：

+----------+----------+-------------------------------------------+
|  Offset  |  Size    |  Purpose                                  |
|  Bytes   |  Bytes   |                                           |
+==========+==========+===========================================+
|    0     |    4     | 元素数量                                  |
+----------+----------+-------------------------------------------+
|    4     |          | Guest状态缓冲区元素                       |
+----------+----------+-------------------------------------------+

GSB元素结构如下：

+----------+----------+-------------------------------------------+
|  Offset  |  Size    |  Purpose                                  |
|  Bytes   |  Bytes   |                                           |
+==========+==========+===========================================+
|    0     |    2     | ID                                        |
+----------+----------+-------------------------------------------+
|    2     |    2     | 值的大小                                  |
+----------+----------+-------------------------------------------+
|    4     | 如上所示 | 值                                        |
+----------+----------+-------------------------------------------+

GSB元素中的ID指定了要设置的内容。这包括架构定义的状态，如GPR、VSR、SPR，以及一些关于分区的元数据，如时间基准偏移和分区范围页表信息。

以下表格详细列出了GSB中的各个元素及其含义：

[此处省略了大部分表格内容，以节省篇幅]

其他信息
==================

不在ptregs/hvregs中的状态
--------------------------

在v1 API中，某些状态不在ptregs/hvstate中，包括向量寄存器和部分SPR。为了使L1为L2设置这种状态，L1在h_enter_nested()调用前加载这些硬件寄存器，并且L0确保它们最终成为L2的状态（即不改变它们）。
v2 API去除了这种方式，并通过GSB显式地设置了这种状态。
L1 实现细节：缓存状态
----------------------------------------

在 v1 API 中，所有状态都会在每次调用 `h_enter_nested()` hcall 时从 L1 发送到 L0 反之亦然。如果 L0 当前没有运行任何 L2，那么 L0 就没有关于这些 L2 的状态信息。唯一的例外是分区表的位置，它是通过 `h_set_partition_table()` 注册的。
v2 API 改变了这一点，使得即使 L2 的 vCPU 不再运行时，L0 也会保留 L2 的状态。这意味着 L1 只需要在需要修改 L2 状态或其值过时时与 L0 通信关于 L2 状态的信息。这为性能优化提供了机会。
当一个 vCPU 从 `H_GUEST_RUN_VCPU()` 调用中退出时，L1 内部将所有 L2 状态标记为无效。这意味着如果 L1 想要知道 L2 状态（例如，通过 `kvm_get_one_reg()` 调用），它需要调用 `H_GUEST_GET_STATE()` 来获取该状态。一旦读取，该状态在 L1 中被标记为有效，直到再次运行 L2。
此外，当 L1 修改 L2 vCPU 状态时，它不需要立即写入 L0，而是等到该 L2 vCPU 再次运行。因此，当 L1 更新状态（例如，通过 `kvm_set_one_reg()` 调用）时，它会写入 L1 内部的一个副本，并且只在 L2 再次通过 `H_GUEST_VCPU_RUN()` 输入缓冲区运行时刷新这个副本到 L0。
L1 这种懒惰更新状态的方式避免了不必要的 `H_GUEST_{G|S}ET_STATE()` 调用。
