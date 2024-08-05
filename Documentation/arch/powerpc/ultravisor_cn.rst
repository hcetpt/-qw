### SPDX 许可证标识符: GPL-2.0
### _ultravisor_

============================
受保护执行设施
============================

.. contents::
    :depth: 3

#### 引言
受保护执行设施（PEF）是为POWER 9架构进行的一项改进，它支持安全虚拟机（SVM）。DD2.3芯片（PVR=0x004e1203）及更高版本将具备PEF能力。新的指令集发布将包括PEF RFC02487的变更。
启用后，PEF为POWER架构添加了一个新的更高级别的特权模式，称为超监视器（Ultravisor）模式。与新模式一起，还有一个新的固件被称为受保护执行超监视器（或简称超监视器）。超监视器模式是POWER架构中权限最高的模式。

+------------------+
	| 特权状态 |
	+==================+
	|  问题状态        |
	+------------------+
	|  监视器状态      |
	+------------------+
	|  虚拟监视器状态  |
	+------------------+
	|  超监视器状态    |
	+------------------+

PEF保护SVM不受虚拟监视器、特权用户和其他系统中的虚拟机的影响。在静止状态下，SVM受到保护，并且只能由授权的机器执行。所有虚拟机都利用虚拟监视器服务。超监视器过滤SVM与虚拟监视器之间的调用，以确保信息不会意外泄露。除了H_RANDOM之外的所有超调用都会被转发到虚拟监视器。
H_RANDOM不被转发，以防止虚拟监视器影响SVM中的随机值。
为了支持这一点，对CPU中资源的所有权进行了重构。一些原本属于虚拟监视器特权的资源现在变成了超监视器特权。

### 硬件

硬件变更包括以下内容：

- 在MSR中有一个新位来确定当前进程是否处于安全模式，MSR(S)位41。MSR(S)=1，进程处于安全模式；MSR(S)=0，进程处于普通模式。
- MSR(S)位只能由超监视器设置。
- 不能使用HRFID来设置MSR(S)位。如果虚拟监视器需要返回到一个SVM，必须使用超调用。它可以判断所返回的虚拟机是否是安全的。
- 新增了一个超监视器特权寄存器SMFCTRL，其中包含一个使能/禁用位SMFCTRL(E)。
- 进程的特权现在由三个MSR位决定：MSR(S, HV, PR)。在下面的每个表中，模式从最低特权到最高特权列出。更高特权的模式可以访问较低特权模式的所有资源。
**安全模式MSR设置**

+---+---+---+---------------+
| S | HV| PR| 特权          |
+===+===+===+===============+
| 1 | 0 | 1 | 错误           |
+---+---+---+---------------+
| 1 | 0 | 0 | 特权(操作系统) |
+---+---+---+---------------+
| 1 | 1 | 0 | 超级监视器     |
+---+---+---+---------------+
| 1 | 1 | 1 | 保留           |
+---+---+---+---------------+

**普通模式MSR设置**

+---+---+---+---------------+
| S | HV| PR| 特权          |
+===+===+===+===============+
| 0 | 0 | 1 | 错误           |
+---+---+---+---------------+
| 0 | 0 | 0 | 特权(操作系统) |
+---+---+---+---------------+
| 0 | 1 | 0 | 监视器         |
+---+---+---+---------------+
| 0 | 1 | 1 | 错误(宿主机)    |
+---+---+---+---------------+

* 内存被划分为安全内存和普通内存。只有运行在安全模式下的进程才能访问安全内存。
* 硬件不允许任何非安全运行的实体访问安全内存。这意味着，监视器无法直接访问SVM（安全虚拟机）的内存，除非通过超调用（向超级监视器请求）。超级监视器只会允许监视器看到加密后的SVM内存。
* 输入/输出系统不允许直接寻址安全内存。这将SVM限制为只能使用虚拟I/O。
* 架构允许SVM与监视器共享未加密保护的内存页面。但是，这种共享必须由SVM发起。
* 当一个进程运行在安全模式下时，所有超调用（系统调用级别=1）都会转到超级监视器。
* 当一个进程处于安全模式时，所有中断都会转到超级监视器。
* 以下资源已成为超级监视器特有，并需要通过超级监视器接口进行操作：

  * 处理器配置寄存器（SCOMs）
* 停止状态信息
* 当SMFCTRL(D)设置时，CIABR、DAWR和DAWRX调试寄存器
如果不设置SMFCTRL(D)，它们在安全模式下无法工作。当设置后，读取或写入需要通过超级监视器调用，否则会导致监视器仿真辅助中断。
* PTCR 和分区表条目（分区表位于安全内存中）。尝试写入 PTCR 将导致出现 Hypervisor 模拟辅助中断。
* LDBAR（加载基址寄存器）和 IMC（内存内收集）非体系结构寄存器。尝试写入这些寄存器将导致出现 Hypervisor 模拟辅助中断。
* SVM 的分页，以及与 Hypervisor 共享内存用于 SVM（包括虚拟处理器区域[VPA]和虚拟 I/O）

软件/微码
=========

软件更改包括：

* 使用 IBM 提供的（开源）工具从普通 VM 创建 SVM。
* 所有的 SVM 都以普通 VM 的形式启动，并利用一个超调用 UV_ESM（进入安全模式）进行转换。
* 当执行 UV_ESM 超调用时，Ultravisor 将 VM 复制到安全内存中，解密验证信息，并检查 SVM 的完整性。如果完整性检查通过，则 Ultravisor 以安全模式传递控制权。
* 验证信息包括与 SVM 关联的加密磁盘的密码短语。当 SVM 请求时，会提供这个密码短语。
* Ultravisor 不参与在静态状态下保护 SVM 的加密磁盘。
* 对于外部中断，Ultravisor 保存 SVM 的状态，并将中断反映给 Hypervisor 进行处理。
对于超调用（hypercalls），Ultravisor会在所有与超调用无关的寄存器中插入中立状态，然后将调用反射到虚拟机监控程序（hypervisor）以进行处理。H_RANDOM超调用是由Ultravisor执行的，并不会被反射。

要使虚拟I/O工作，必须进行缓冲区跳转（bounce buffering）。

Ultravisor使用AES（IAPM模式）来保护SVM内存。IAPM是一种AES模式，可以同时提供完整性和保密性。

数据在普通页面和安全页面之间的移动是通过虚拟机监控程序中的一个新HMM插件与Ultravisor协调完成的。

Ultravisor为虚拟机监控程序和SVM提供了新的服务。这些服务可以通过超调用（ultracalls）访问。

术语
=====

- **超调用（Hypercalls）**：用于请求来自虚拟机监控程序的服务的特殊系统调用。
- **普通内存**：可被虚拟机监控程序访问的内存。
- **普通页面**：由普通内存支持且可供虚拟机监控程序访问的页面。
- **共享页面**：由普通内存支持且可供虚拟机监控程序/QEMU和SVM访问的页面（即页面在SVM和虚拟机监控程序/QEMU中都有映射）。
- **安全内存**：仅对Ultravisor和SVM可访问的内存。
* 安全页面：由安全内存支持的页面，仅对Ultravisor和SVM可用。
* SVM: 安全虚拟机
* Ultracalls: 特殊的系统调用，用于请求Ultravisor提供的服务
Ultravisor 调用 API
#########################

    本节描述了支持安全虚拟机（SVM）和准虚拟化KVM所需的Ultravisor调用（ultracalls）。这些ultracalls允许SVM和Hypervisor从Ultravisor请求服务，例如访问只能在Ultravisor特权模式下访问的寄存器或内存区域。

所需的具体服务通过寄存器R3（ultracall的第一个参数）指定。如果有其他ultracall参数，则指定在寄存器R4至R12中。
所有ultracalls的返回值都在寄存器R3中。如果有其他输出值，则返回在寄存器R4至R12中。
唯一例外是下面描述的``UV_RETURN`` ultracall对于寄存器使用的情况。
每个ultracall都会返回特定的错误代码，适用于该ultracall的上下文中。但是，类似于PowerPC架构平台参考（PAPR），如果某个特定情况没有定义具体的错误代码，则ultracall将回退到基于错误参数位置的代码，即U_PARAMETER, U_P2, U_P3等，取决于可能引起错误的ultracall参数。
一些ultracalls涉及在Ultravisor和Hypervisor之间传输一页数据。从安全内存传输到普通内存的安全页面可能使用动态生成的密钥进行加密。
当安全页面传回安全内存时，可以使用相同的动态生成的密钥进行解密。这些密钥的生成和管理将在单独的文档中覆盖。
目前这仅涵盖了已被Hypervisor和SVMs使用且已实现的ultracalls，但当有必要时可以在此添加其他ultracalls。
所有hypercalls/ultracalls的完整规范最终将在PAPR规范的公共/OpenPower版本中提供。
.. 注意::

        如果PEF未启用，则ultracalls将被重定向到Hypervisor，Hypervisor必须处理或使这些调用失败。
Hypervisor使用的ultracalls
=============================

    本节描述了Hypervisor用于管理SVMs的虚拟内存管理ultracalls。

UV_PAGE_OUT
-----------

    加密并将页面内容从安全内存移动到普通内存。
语法
~~~~~~

.. code-block:: c

	uint64_t ultracall(const uint64_t UV_PAGE_OUT,
		uint16_t lpid,		/* LPAR ID */
		uint64_t dest_ra,	/* 目标页的真实地址 */
		uint64_t src_gpa,	/* 源guest-物理地址 */
		uint8_t  flags,		/* 标志 */
		uint64_t order)		/* 页面大小顺序 */

返回值
~~~~~~~~~~~~~

    下列之一：

	* U_SUCCESS	成功时
* U_PARAMETER	如果`lpid`无效
* U_P2		如果`dest_ra`无效
* U_P3		如果`src_gpa`地址无效
* U_P4		如果`flags`中的任何位不被识别
	* U_P5		如果`order`参数不受支持
* U_FUNCTION	如果功能不受支持
* U_BUSY	如果当前页面无法被换出
描述
~~~~~~~~~~~

    加密安全页面的内容，并将其提供给虚拟机监视器（Hypervisor）在一个常规页面中。
默认情况下，源页面将从SVM的分区特定页表中解除映射。但是，虚拟机监视器可以向超监视器（Ultravisor）提供一个提示以保留该页面映射，通过在`flags`参数中设置`UV_SNAPSHOT`标志。
如果源页面已经是一个共享页面，则调用返回`U_SUCCESS`，而不执行任何操作。
使用场景
~~~~~~~~~

    1. QEMU尝试访问属于SVM的一个地址，但该地址对应的页框没有映射到QEMU的地址空间中。在这种情况下，虚拟机监视器会分配一个页框，将其映射到QEMU的地址空间，并发出`UV_PAGE_OUT`调用来检索该页面的加密内容。
2. 当超监视器的可用安全内存不足且需要将最近最少使用的（LRU）页面换出时。在这种情况下，超监视器会向虚拟机监视器发出`H_SVM_PAGE_OUT`超调用。然后，虚拟机监视器会分配一个常规页面并发出`UV_PAGE_OUT`超调用，超监视器将加密并将安全页面的内容移动到常规页面中。
3. 当虚拟机监视器访问SVM数据时，虚拟机监视器请求超监视器将相应的页面转移到一个非安全页面中，以便虚拟机监视器可以访问。常规页面中的数据将是加密过的。
UV_PAGE_IN
----------

    将页面的内容从常规内存移动到安全内存中。
语法
~~~~~~

.. code-block:: c

    uint64_t ultracall(const uint64_t UV_PAGE_IN,
        uint16_t lpid,      /* LPAR ID */
        uint64_t src_ra,    /* 页面的源实际地址 */
        uint64_t dest_gpa,  /* 目的地客户物理地址 */
        uint64_t flags,     /* 标志 */
        uint64_t order)     /* 页大小顺序 */

返回值
~~~~~~~~~~~~~

    下列之一：

    * U_SUCCESS	成功时
* U_BUSY	如果当前无法将页面换入
* U_FUNCTION	如果不支持该功能
* U_PARAMETER	如果`lpid`无效
* U_P2	如果`src_ra`无效
* U_P3	如果`dest_gpa`地址无效
* U_P4	如果`flags`中的任何位不认识
* U_P5	如果`order`参数不受支持
描述
~~~~~~~~~~~

    将由`src_ra`标识的页面内容从常规内存移动到安全内存，并将其映射到访客物理地址`dest_gpa`
如果`dest_gpa`指的是共享地址，则将该页面映射到SVM的分区范围页表中。如果`dest_gpa`不是共享地址，则将页面的内容复制到相应的安全页面。
根据上下文，在复制前对页面进行解密（如果需要）。
调用者通过`flags`参数提供页面属性。`flags`的有效值包括：

    * CACHE_INHIBITED
    * CACHE_ENABLED
    * WRITE_PROTECTION

    虚拟机监控器在发出`UV_PAGE_IN`超调用之前必须将页面固定在内存中。
使用场景
~~~~~~~~~

    1. 当普通虚拟机切换到安全模式时，它位于常规内存中的所有页面都会被移动到安全内存中。
当一个SVM请求与Hypervisor共享一个页面时，Hypervisor分配一个页面并通知Ultravisor。

当一个SVM访问一个已经被换出的保护页面时，Ultravisor调用Hypervisor来定位该页面。定位到页面后，Hypervisor使用UV_PAGE_IN使页面对Ultravisor可用。

UV_PAGE_INVAL
-------------

    使Ultravisor映射的一个页面失效
语法
~~~~~~

.. code-block:: c

    uint64_t ultracall(const uint64_t UV_PAGE_INVAL,
        uint16_t lpid,      /* 逻辑分区ID */
        uint64_t guest_pa,  /* 目标客户物理地址 */
        uint64_t order)     /* 页面大小顺序 */

返回值
~~~~~~~~~~~~~

以下某个值：

    * U_SUCCESS   成功时
    * U_PARAMETER 若`lpid`无效
    * U_P2        若`guest_pa`无效（或对应于一个保护页面映射）
    * U_P3        若`order`无效
    * U_FUNCTION  若不支持该功能
    * U_BUSY      若当前无法使页面失效

描述
~~~~~~~~~~~

    此超调用告知Ultravisor，对应给定客户物理地址的Hypervisor中的页面映射已失效，并且Ultravisor不应访问该页面。如果指定的`guest_pa`对应一个保护页面，Ultravisor将忽略尝试使页面失效的操作并返回U_P2。
用例
~~~~~~~~~

1. 当一个共享页面从QEMU的页表中解除映射时，可能是因为它被交换到磁盘，Ultravisor需要知道该页面也不应从其这边访问。

UV_WRITE_PATE
--------------

验证并为给定分区写入分区表项（PATE）。
语法
~~~~~~

.. code-block:: c

    uint64_t ultracall(const uint64_t UV_WRITE_PATE,
        uint32_t lpid,         /* 逻辑分区ID */
        uint64_t dw0,          /* 要写入的第一个双字 */
        uint64_t dw1);         /* 要写入的第二个双字 */

返回值
~~~~~~~~~~~~~

以下值之一：

- `U_SUCCESS`：成功时
- `U_BUSY`：如果当前无法写入PATE
- `U_FUNCTION`：如果不支持此功能
- `U_PARAMETER`：如果`lpid`无效
- `U_P2`：如果`dw0`无效
- `U_P3`：如果`dw1`地址无效
- `U_PERMISSION`：如果Hypervisor试图更改安全虚拟机的PATE，或者从非Hypervisor上下文中调用

描述
~~~~~~~~~~~

验证并为给定LPID写入其逻辑分区ID及其分区表项。如果LPID已经分配并初始化，则此调用会导致更改分区表项。
用例
~~~~~~~~~

    #. 分区表驻留在安全内存中，其条目（称为PATE，即分区表条目）指向为管理程序及其每个虚拟机（包括安全和普通虚拟机）分配的分区范围页表。管理程序在分区0中运行，其分区范围页表位于常规内存中。
    #. 此超调用允许管理程序向超管理程序注册管理程序和其他分区（虚拟机）的分区范围及进程范围页表条目。
    #. 如果现有分区（虚拟机）的PATE值发生变化，则该分区的TLB缓存将被刷新。
    #. 管理程序负责分配LPID。LPID与其PATE条目一起注册。管理程序管理普通虚拟机的PATE条目，并且可以随时更改PATE条目。超管理程序管理SVM的PATE条目，不允许管理程序修改它们。

UV_RETURN
---------

    在处理完一个超调用或转发（即*反射*）给管理程序的中断后，将控制权从管理程序返回到超管理程序。
语法
~~~~~~

.. code-block:: c

    uint64_t ultracall(const uint64_t UV_RETURN);

返回值
~~~~~~~~~~~~~

    成功时此调用不会返回到管理程序。如果超调用不是从管理程序上下文中发出的，则返回U_INVALID。
描述
~~~~~~~~~~~

    当SVM发起一个超调用或其他异常时，超管理程序通常会将这些异常转发（即*反射*）给管理程序。在处理完异常后，管理程序使用`UV_RETURN`超调用来将控制权返回给SVM。

对于此超调用，期望的寄存器状态如下：

    * 非易失性寄存器恢复为其原始值。
    * 如果是从超调用返回，寄存器R0包含返回值（**与其他超调用不同**），而寄存器R4至R12包含超调用的任何输出值。
    * 寄存器R3包含超调用编号，即UV_RETURN。
如果通过合成中断返回，R2寄存器中将包含合成的中断编号。

使用场景
~~~~~~~~~

    1. Ultravisor依赖于Hypervisor为SVM提供多项服务，例如处理超调用和其他异常。在处理完异常后，Hypervisor使用UV_RETURN将控制权返回给Ultravisor。
    2. Hypervisor必须使用此超调用来将控制权返回给SVM。

UV_REGISTER_MEM_SLOT
--------------------

    向指定属性的SVM地址范围内注册信息
语法
~~~~~~

.. code-block:: c

	uint64_t ultracall(const uint64_t UV_REGISTER_MEM_SLOT,
		uint64_t lpid,		/* SVM 的逻辑分区ID */
		uint64_t start_gpa,	/* 客户端物理地址起始位置 */
		uint64_t size,		/* 地址范围大小（字节） */
		uint64_t flags,		/* 预留以供未来扩展 */
		uint16_t slotid)	/* 插槽标识符 */

返回值
~~~~~~~~~~~~~

    可能返回以下值之一：

    * U_SUCCESS	操作成功时
    * U_PARAMETER	若 `lpid` 无效
    * U_P2		若 `start_gpa` 无效
    * U_P3		若 `size` 无效
    * U_P4		若 `flags` 中有任何位无法识别
    * U_P5		若 `slotid` 参数不受支持
* U_PERMISSION	如果调用的上下文不是来自虚拟机监视器（Hypervisor）
* U_FUNCTION	如果不支持该功能
描述
~~~~~~~~~~~
注册一个SVM（Secure Virtual Machine，安全虚拟机）的内存区间。内存区间的起始位置为来宾物理地址`start_gpa`，长度为`size`字节。
使用场景
~~~~~~~~~

1. 当虚拟机进入安全模式时，所有由虚拟机监视器管理的内存槽将移至安全内存中。虚拟机监视器会遍历每一个内存槽，并将其与UltraVisor进行注册。虚拟机监视器可能会忽略一些内存槽，例如用于固件（如SLOF）的内存槽。
2. 当新的内存被热插拔时，一个新的内存槽会被注册。

UV_UNREGISTER_MEM_SLOT
----------------------
取消注册之前通过UV_REGISTER_MEM_SLOT注册的一个SVM地址区间。
语法
~~~~~~

.. code-block:: c

   uint64_t ultracall(const uint64_t UV_UNREGISTER_MEM_SLOT,
        uint64_t lpid,      /* SVM的LPAR ID */
        uint64_t slotid)    /* 预留的槽ID */

返回值
~~~~~~~~~~~~~

以下值之一：

- U_SUCCESS	成功时返回
- U_FUNCTION	如果不支持该功能
- U_PARAMETER	如果`lpid`无效
- U_P2		如果`slotid`无效
* U_PERMISSION	若从非虚拟机监控程序(Hypervisor)上下文中调用
描述
~~~~~~~~~~~

    释放由 `slotid` 标识的内存槽，并释放为此预留分配的所有资源。
用途
~~~~~~~~~~~

    #. 内存热插拔移除
UV_SVM_TERMINATE
----------------

    终止一个SVM并释放其所有资源
语法
~~~~~~

.. code-block:: c

	uint64_t ultracall(const uint64_t UV_SVM_TERMINATE,
		uint64_t lpid,		/* SVM 的 LPAR ID */

返回值
~~~~~~~~~~~~~

    以下值之一：

	* U_SUCCESS	成功时
* U_FUNCTION	如果不支持此功能
* U_PARAMETER	如果 `lpid` 无效
* U_INVALID	如果虚拟机不是安全的
* U_PERMISSION	如果不是从虚拟机监控程序上下文中调用
描述
~~~~~~~~~~~

    终止一个SVM并释放其所有资源
使用案例
~~~~~~~~~

    #. 当终止一个SVM时由Hypervisor调用
超调用（Ultracalls）在SVM中的使用
======================

UV_SHARE_PAGE
-------------

    与Hypervisor共享一组来宾物理页面
语法
~~~~~~

.. code-block:: c

    uint64_t ultracall(const uint64_t UV_SHARE_PAGE,
        uint64_t gfn,     /* 来宾页框号 */
        uint64_t num)     /* 页面数量，大小为PAGE_SIZE */

返回值
~~~~~~~~~~~~~

    下列值之一：

	* U_SUCCESS	成功时
* U_FUNCTION	如果不支持该功能
* U_INVALID	如果虚拟机不是安全的
* U_PARAMETER	如果`gfn`无效
* U_P2		如果`num`无效
描述
~~~~~~~~~~~

    与Hypervisor共享从来宾物理页框号`gfn`开始的`num`个页面。假设页面大小为PAGE_SIZE字节。在返回前将页面清零。
如果地址已经由安全页面支持，则解除映射该页面，并借助Hypervisor的支持将其替换为非安全页面。如果它尚未被任何页面支持，则标记PTE为非安全，并在其被访问时使用非安全页面支持它。如果它已经被非安全页面支持，则清零页面并返回。
使用案例
~~~~~~~~~

    #. 由于SVM的页面是由安全页面支持的，因此Hypervisor无法访问这些页面。因此，SVM必须明确请求Ultravisor提供可以与Hypervisor共享的页面。
#. 共享页面对于支持SVM中的virtio和虚拟处理器区域(VPA)是必需的。
   
   UV_UNSHARE_PAGE
   ---------------

   **恢复共享的SVM页面到其初始状态**

   **语法**
   ~~~~~~~

   .. code-block:: c

      uint64_t ultracall(const uint64_t UV_UNSHARE_PAGE,
           uint64_t gfn,     /* 客户机页框编号 */
           uint73 num)      /* 页的数量，大小为PAGE_SIZE */

   **返回值**
   ~~~~~~~~~~

   下列之一：

   * U_SUCCESS  成功时
   * U_FUNCTION 如果不支持该功能
   * U_INVALID  如果虚拟机不是安全的
   * U_PARAMETER 如果 `gfn` 无效
   * U_P2       如果 `num` 无效

   **描述**
   ~~~~~~~~~

   停止从 `gfn` 开始的 `num` 个页面与Hypervisor之间的共享。假设页面大小为PAGE_SIZE，在返回之前清零这些页面。

   如果地址已经被一个非安全页面支持，则取消映射该页面，并用一个安全页面来支持它。通知Hypervisor释放对其共享页面的引用。如果地址尚未被任何页面支持，则将PTE标记为安全，并在访问该地址时用一个安全页面支持它。如果已经由一个安全页面支持，则清零该页面并返回。
### 使用案例

#### SVM 可能决定从 Hypervisor 中取消共享页面
##### UV_UNSHARE_ALL_PAGES
**取消共享 SVM 与 Hypervisor 共享的所有页面**

**语法**
```c
uint64_t ultracall(const uint64_t UV_UNSHARE_ALL_PAGES);
```

**返回值**
- `U_SUCCESS`：成功时返回
- `U_FUNCTION`：如果功能不支持时返回
- `U_INVAL`：如果虚拟机不是安全的时返回

**描述**
取消共享所有从 Hypervisor 中共享的页面。返回时，所有取消共享的页面都会被清零。只有 SVM 明确与 Hypervisor 共享的页面（使用 UV_SHARE_PAGE ultracall）才会被取消共享。Ultravisor 内部可能会在没有 SVM 明确请求的情况下与 Hypervisor 共享一些页面，这些页面不会通过此 ultracall 被取消共享。

**使用案例**
1. 当使用 `kexec` 来启动不同的内核时需要这个调用。在 SVM 重置时也可能需要它。

#### UV_ESM
**使虚拟机进入安全模式**

**语法**
```c
uint64_t ultracall(const uint64_t UV_ESM,
		uint64_t esm_blob_addr, /* 安全模式 blob 的位置 */
		uint64_t fdt); /* 展平设备树 */
```

**返回值**
- `U_SUCCESS`：成功时返回（包括虚拟机已经是安全状态的情况）
- `U_FUNCTION`：如果功能不支持时返回
* U_INVALID	如果虚拟机不是安全的
* U_PARAMETER	如果 ``esm_blob_addr`` 无效
* U_P2 		如果 ``fdt`` 无效
* U_PERMISSION	如果有任何完整性检查失败
* U_RETRY	创建SVM时内存不足
* U_NO_KEY	对称密钥不可用
描述
~~~~

    保护虚拟机。在成功完成操作后，返回对虚拟机的控制到ESM blob中指定的地址。
使用案例
~~~~~~

    1. 一个普通的虚拟机可以选择切换到安全模式
虚拟机管理程序调用API
######################

    本文档描述了支持Ultravisor所需的虚拟机管理程序调用（超调用）。超调用是由虚拟机管理程序提供给虚拟机和Ultravisor的服务。
对于这些超调用的寄存器使用与Power Architecture Platform Reference (PAPR)文档中定义的其他超调用相同。也就是说，在输入时，寄存器R3标识所请求的具体服务，而寄存器R4至R11包含超调用的附加参数（如果有的话）。在输出时，寄存器R3包含返回值，寄存器R4至R9包含来自超调用的其他输出值。
本文档仅涵盖了当前已实现/计划用于Ultravisor使用的超调用，但当有必要时可以添加其他超调用。
所有超调用/特超调用的完整规范最终将在PAPR规范的公共/OpenPower版本中公开。

支持Ultravisor的虚拟机监视器调用
==================================

以下是一系列需要支持Ultravisor的超调用：

H_SVM_INIT_START
----------------

开始将一个普通虚拟机转换为SVM的过程。
语法
~~~~~~

.. code-block:: c

   uint64_t hypercall(const uint64_t H_SVM_INIT_START);

返回值
~~~~~~~~~~~~~

下列之一：

-  H_SUCCESS       成功时
-  H_STATE         如果虚拟机不处于可以切换到安全模式的位置

描述
~~~~~~~~~~~

启动将虚拟机安全化的过程。这涉及与Ultravisor协作，使用特超调用来在Ultravisor中为新的SVM分配资源，将虚拟机的页面从普通内存转移到安全内存等。当这一过程完成时，Ultravisor会发出H_SVM_INIT_DONE超调用。
使用场景
~~~~~~~~~

1. Ultravisor使用此超调用来通知虚拟机监视器一个虚拟机已经开始切换到安全模式的过程。

H_SVM_INIT_DONE
---------------

完成将SVM安全化的过程。
语法
~~~~~~

.. code-block:: c

   uint64_t hypercall(const uint64_t H_SVM_INIT_DONE);

返回值
~~~~~~~~~~~~~

下列之一：

-  H_SUCCESS       成功时
* H_UNSUPPORTED	如果从错误的上下文中调用（例如
从一个SVM或在H_SVM_INIT_START
超调用之前）
* H_STATE	如果无法成功
将虚拟机转换为安全SVM
描述
~~~~~~~~~~~

    完成对虚拟机进行安全化的流程。此调用必须
在先前调用了`H_SVM_INIT_START`超调用之后发出。
使用场景
~~~~~~~~~

    在成功地对虚拟机进行了安全化后，Ultravisor会通知
Hypervisor。Hypervisor可以利用此调用来完成为此虚拟机设置
其内部状态。
H_SVM_INIT_ABORT
----------------

    中断对SVM的安全化流程
语法
~~~~~~

.. code-block:: c

    uint64_t hypercall(const uint64_t H_SVM_INIT_ABORT);

返回值
~~~~~~~~~~~~~

    以下值之一：

	* H_PARAMETER	在成功清理状态后，
Hypervisor将返回此值给
**客户机**，以表明底层UV_ESM超调用失败
* H_STATE	如果在虚拟机已经变为安全状态后被调用（即
H_SVM_INIT_DONE超调用成功）
* H_UNSUPPORTED	如果从错误的上下文中调用（例如
从普通虚拟机中调用）
描述
~~~~~~~~~~~

    中断对虚拟机进行安全化的流程。此调用必须
在先前调用了`H_SVM_INIT_START`超调用之后和
`H_SVM_INIT_DONE`调用之前发出。
进入此超调用时，期望非易失性通用寄存器 (GPR) 和浮点寄存器 (FPR) 包含虚拟机 (VM) 发出 `UV_ESM` 超调用时的值。此外，期望 `SRR0` 包含 `UV_ESM` 超调用后指令的地址，而 `SRR1` 包含返回到 VM 的机器状态寄存器 (MSR) 值。

此超调用将清理自上次 `H_SVM_INIT_START` 超调用以来为 VM 建立的任何部分状态，包括将之前分页到安全内存的页面分页出去，并发出 `UV_SVM_TERMINATE` 超调用来终止 VM。
在清理完部分状态之后，控制权返回到 VM（**不是 Ultravisor**），在 `SRR0` 指定的地址处，MSR 值设置为 `SRR1` 中的值。

### 使用场景

如果在成功调用 `H_SVM_INIT_START` 之后，Ultravisor 在保护虚拟机过程中遇到错误，无论是由于资源不足还是因为无法验证 VM 的安全性信息，Ultravisor 将此情况通知给 Hypervisor。
Hypervisor 应使用此调用来清理与此虚拟机相关的任何内部状态，并返回到 VM。

### H_SVM_PAGE_IN

将一页内容从常规内存移动到安全内存。

#### 语法

```c
uint64_t hypercall(const uint64_t H_SVM_PAGE_IN,
		uint64_t guest_pa,	/* 客户机物理地址 */
		uint64_t flags,		/* 标志 */
		uint64_t order)		/* 页面大小顺序 */
```

#### 返回值

可能返回以下值之一：

- `H_SUCCESS`：成功时返回
- `H_PARAMETER`：如果 `guest_pa` 无效
- `H_P2`：如果 `flags` 无效
- `H_P3`：如果页面的 `order` 无效
描述
~~~~~~~~~~~

    从指定的客户机物理地址处获取属于虚拟机（VM）页面的内容。
`flags` 中的有效值为：

        * H_PAGE_IN_SHARED，表示该页面将与 Ultravisor 共享
* H_PAGE_IN_NONSHARED，表示 Ultravisor 对此页面不再感兴趣。仅当页面为共享页面时适用
`order` 参数必须对应于已配置的页面大小
使用场景
~~~~~~~~~

    1. 当普通虚拟机变为安全虚拟机（通过使用 UV_ESM 超调用），Ultravisor 使用此超调用来将虚拟机每一页的内容从常规内存移动到安全内存
2. Ultravisor 使用此超调用来请求 Hypervisor 提供一个可以被 SVM 和 Hypervisor 共享的常规内存中的页面
3. Ultravisor 使用此超调用来将换出的页面换入。这可能发生在 SVM 访问了一个已换出的页面时
4. 如果 SVM 希望禁用与 Hypervisor 的页面共享，它可以通知 Ultravisor 进行操作。Ultravisor 将使用此超调用来告知 Hypervisor 它已经释放了对常规页面的访问权限
H_SVM_PAGE_OUT
---------------

    将页面内容移动到常规内存
语法
~~~~~~

.. code-block:: c

    uint64_t hypercall(const uint64_t H_SVM_PAGE_OUT,
		uint64_t guest_pa,	/* 客户机物理地址 */
		uint64_t flags,		/* 标志（目前没有） */
		uint64_t order)		/* 页面大小顺序 */

返回值
~~~~~~~~~~~~~

    以下值之一：

	* H_SUCCESS	在成功时
* H_PARAMETER 如果 `guest_pa` 无效
* H_P2 如果 `flags` 无效
* H_P3 如果 `order` 无效

描述
~~~~

    将由 `guest_pa` 标识的页面内容移动到常规内存中。
    当前 `flags` 未被使用，必须设置为 0。`order` 参数必须与配置的页面大小相对应。

用例
~~~~

    1. 如果 Ultravisor 的安全页面不足，它可以使用此超调用来将一些安全页面的内容移动到常规页面中。这些内容将会被加密。

参考
####

- 《在 IBM Power Architecture 上支持受保护计算》 `<https://developer.ibm.com/articles/l-support-protected-computing/>`_
