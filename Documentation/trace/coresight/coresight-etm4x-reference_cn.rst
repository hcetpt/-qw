===============================================
ETMv4 sysfs Linux驱动编程参考
===============================================

    :作者:   Mike Leach <mike.leach@linaro.org>
    :日期:     2019年10月11日

对现有ETMv4驱动文档的补充
sysfs文件和目录
---------------------------

根目录: ``/sys/bus/coresight/devices/etm<N>``

以下段落解释了sysfs文件与其影响的ETMv4寄存器之间的关联。注意，寄存器名称未包含‘TRC’前缀。
----

:文件:            ``mode`` (读写)
:跟踪寄存器: {CONFIGR + 其他}
:说明:
    位选择跟踪特性。参见下面的“mode”部分。这些位将导致等效地编程跟踪配置和其他寄存器以启用请求的功能
:语法与示例:
    ``echo 位字段 > mode``

    设置跟踪特性的位字段最多可达32位
:示例:
    ``$> echo 0x012 > mode``

----

:文件:            ``reset`` (写入)
:跟踪寄存器: 所有
:说明:
    将所有编程重置为不跟踪任何内容/无逻辑编程
:语法:
    ``echo 1 > reset``

----

:文件:            ``enable_source`` (写入)
:跟踪寄存器: PRGCTLR, 所有硬件寄存器
:说明:
    - > 0 : 使用当前在驱动程序中持有的值对硬件进行编程并启用跟踪
    - = 0 : 禁用跟踪硬件
:语法:
    ``echo 1 > enable_source``

----

:文件:            ``cpu`` (只读)
:跟踪寄存器: 无
注释：
    此ETM连接的CPU ID

示例：
    ``$> cat cpu``

    ``$> 0``

---

文件：          ``ts_source``（只读）
跟踪寄存器：无
注释：
    当实现FEAT_TRF时，用于跟踪会话的TRFCR_ELx.TS值。否则，-1表示未知的时间源。检查trcidr0.tssize以查看是否有全局时间戳可用。
示例：
    ``$> cat ts_source``

    ``$> 1``

---

文件：          ``addr_idx``（读写）
跟踪寄存器：无
注释：
    虚拟寄存器，用于索引地址比较器和范围特性。设置范围中一对中的第一个索引。
语法：
    ``echo idx > addr_idx``

    其中idx < nr_addr_cmp * 2

---

文件：          ``addr_range``（读写）
跟踪寄存器：ACVR[idx, idx+1], VIIECTLR
注释：
    由addr_idx选择的一对地址，用于定义一个范围。根据可选参数包括或排除，如果省略则使用当前‘mode’设置。在控制寄存器中选择比较器范围。如果索引是奇数值，则出错。
依赖项：``mode, addr_idx``
语法：
    ``echo addr1 addr2 [exclude] > addr_range``

    其中addr1和addr2定义了范围，并且addr1 < addr2
可选的排除值：

   - 0 表示包含
   - 1 表示排除
示例：
    ``$> echo 0x0000 0x2000 0 > addr_range``

---

文件：          ``addr_single``（读写）
跟踪寄存器：ACVR[idx]
注释：
    根据addr_idx设置单个地址比较器。如果地址比较器作为事件生成逻辑的一部分使用时会用到此功能。
依赖项：``addr_idx``
语法：
    ``echo addr1 > addr_single``

---

文件：         ``addr_start``（读写）
跟踪寄存器：ACVR[idx], VISSCTLR
注释：
    根据addr_idx设置跟踪启动地址比较器
选择控制寄存器中的比较器
:依赖: ``addr_idx``
:语法:
    ``echo addr1 > addr_start``

---

:文件:            ``addr_stop`` (可读写)
:追踪寄存器: ACVR[idx], VISSCTLR
:说明:
    根据 addr_idx 设置一个追踪停止地址比较器
选择控制寄存器中的比较器
:依赖: ``addr_idx``
:语法:
    ``echo addr1 > addr_stop``

---

:文件:            ``addr_context`` (可读写)
:追踪寄存器: ACATR[idx,{6:4}]
:说明:
    将上下文 ID 比较器链接到地址比较器 addr_idx

:依赖: ``addr_idx``
:语法:
    ``echo ctxt_idx > addr_context``

    其中 ctxt_idx 是链接的上下文 ID / VMID 比较器的索引
---

:文件:            ``addr_ctxtype`` (可读写)
:追踪寄存器: ACATR[idx,{3:2}]
:说明:
    输入值字符串。为链接的上下文 ID 比较器设置类型

:依赖: ``addr_idx``
:语法:
    ``echo type > addr_ctxtype``

    类型之一 {all, vmid, ctxid, none}
:示例:
    ``$> echo ctxid > addr_ctxtype``

---

:文件:            ``addr_exlevel_s_ns`` (可读写)
:追踪寄存器: ACATR[idx,{14:8}]
:说明:
    为选定的地址比较器设置异常级别安全和非安全匹配位

:依赖: ``addr_idx``
:语法:
    ``echo val > addr_exlevel_s_ns``

    val 是一个7位值，用于排除异常级别。输入值移位至寄存器中的正确位置
:示例:
    ``$> echo 0x4F > addr_exlevel_s_ns``

---

:文件:            ``addr_instdatatype`` (可读写)
:追踪寄存器: ACATR[idx,{1:0}]
:说明:
    设置匹配的比较器地址类型。驱动程序仅支持设置指令地址类型
:依赖: ``addr_idx``

---

:文件:            ``addr_cmp_view`` (只读)
:追踪寄存器: ACVR[idx, idx+1], ACATR[idx], VIIECTLR
:说明:
    读取当前选定的地址比较器。如果属于地址范围，则显示两个地址
:依赖: ``addr_idx``
:语法:
    ``cat addr_cmp_view``
:示例:
    ``$> cat addr_cmp_view``

   ``addr_cmp[0] range 0x0 0xffffffffffffffff include ctrl(0x4b00)``

---

:文件:            ``nr_addr_cmp`` (只读)
:追踪寄存器: 从 IDR4 获取
:说明:
    地址比较器对的数量

---

:文件:            ``sshot_idx`` (可读写)
:追踪寄存器: 无
:说明:
    选择单次触发寄存器集

---

:文件:            ``sshot_ctrl`` (可读写)
:追踪寄存器: SSCCR[idx]
:说明:
    访问单次触发比较器控制寄存器
:依赖: ``sshot_idx``
:语法:
    ``echo val > sshot_ctrl``

    将 val 写入选定的控制寄存器
---

:文件:            ``sshot_status`` (只读)
:跟踪寄存器:      SSCSR[idx]
:说明:
    读取单次比较器状态寄存器

:依赖项:          ``sshot_idx``
:语法:
    ``cat sshot_status``

    读取状态
:示例:
    ``$> cat sshot_status``

    ``0x1``

---

:文件:            ``sshot_pe_ctrl`` (读写)
:跟踪寄存器:      SSPCICR[idx]
:说明:
    访问单次PE比较器输入控制寄存器
:依赖项:          ``sshot_idx``
:语法:
    ``echo val > sshot_pe_ctrl``

    将val写入选定的控制寄存器
---

:文件:            ``ns_exlevel_vinst`` (读写)
:跟踪寄存器:      VICTLR{23:20}
:说明:
    编程非安全异常级别过滤器。设置/清除NS异常过滤位。设置‘1’表示排除该异常级别的跟踪
:语法:
    ``echo bitfield > ns_exlevel_vinst``

    其中bitfield包含从EL0到EL2要设置或清除的位
:示例:
    ``%> echo 0x4 > ns_exlevel_vinst``

    排除EL2非安全跟踪
---

:文件:            ``vinst_pe_cmp_start_stop`` (读写)
:跟踪寄存器:      VIPCSSCTLR
:说明:
    访问PE起始停止比较器输入控制寄存器

---

:文件:            ``bb_ctrl`` (读写)
:跟踪寄存器:      BBCTLR
:说明:
    定义Branch Broadcast将运行的地址范围
默认值（0x0）为所有地址
:依赖项:          Branch Broadcast启用
---

:文件:            ``cyc_threshold`` (读写)
:跟踪寄存器:      CCCTLR
:说明:
    设置周期计数发出的阈值
尝试设置低于IDR3定义的最小值时会出错，并且会被有效位宽度屏蔽
---
### 依赖：CC 启用

#### 文件：`syncfreq`（读写）
**跟踪寄存器：** SYNCPR  
**说明：**
设置跟踪同步周期。2 的幂值，0（关闭）或 8-20。驱动程序默认为 12（每 4096 字节）

#### 文件：`cntr_idx`（读写）
**跟踪寄存器：** 无  
**说明：**
选择要访问的计数器  
**语法：**
```sh
echo idx > cntr_idx
```
其中 idx < nr_cntr

#### 文件：`cntr_ctrl`（读写）
**跟踪寄存器：** CNTCTLR[idx]  
**说明：**
设置计数器控制值  
**依赖：** `cntr_idx`  
**语法：**
```sh
echo val > cntr_ctrl
```
其中 val 符合 ETMv4 规范

#### 文件：`cntrldvr`（读写）
**跟踪寄存器：** CNTRLDVR[idx]  
**说明：**
设置计数器重载值  
**依赖：** `cntr_idx`  
**语法：**
```sh
echo val > cntrldvr
```
其中 val 符合 ETMv4 规范

#### 文件：`nr_cntr`（只读）
**跟踪寄存器：** 来自 IDR5  
**说明：**
实现的计数器数量

#### 文件：`ctxid_idx`（读写）
**跟踪寄存器：** 无  
**说明：**
选择要访问的上下文 ID 比较器  
**语法：**
```sh
echo idx > ctxid_idx
```
其中 idx < numcidc

#### 文件：`ctxid_pid`（读写）
**跟踪寄存器：** CIDCVR[idx]  
**说明：**
设置上下文 ID 比较器值  
**依赖：** `ctxid_idx`

#### 文件：`ctxid_masks`（读写）
**跟踪寄存器：** CIDCCTLR0, CIDCCTLR1, CIDCVR<0-7>  
**说明：**
用于设置 1-8 个上下文 ID 比较器的字节掩码的一对值。自动清除 CID 值寄存器中的掩码字节为 0  
**语法：**
```sh
echo m3m2m1m0 [m7m6m5m4] > ctxid_masks
```
由掩码字节组成的 32 位值，其中 mN 表示上下文 ID 比较器 N 的字节掩码值  
在具有少于 4 个上下文 ID 比较器的系统上不需要第二个值

#### 文件：`numcidc`（只读）
**跟踪寄存器：** 来自 IDR4  
**说明：**
上下文 ID 比较器的数量

#### 文件：`vmid_idx`（读写）
**跟踪寄存器：** 无  
**说明：**
选择要访问的 VM ID 比较器
### 语法：
```
echo idx > vmid_idx
```

其中 `idx < numvmidc`

---

**文件**: `vmid_val`（读写）
**跟踪寄存器**: VMIDCVR[idx]
**备注**: 
设置 VM ID 比较器值

**依赖**: `vmid_idx`

---

**文件**: `vmid_masks`（读写）
**跟踪寄存器**: VMIDCCTLR0, VMIDCCTLR1, VMIDCVR<0-7>
**备注**: 
设置 1-8 个 VM ID 比较器的字节掩码值
自动将掩码字节清零到 VMID 值寄存器中
**语法**: 
```
echo m3m2m1m0 [m7m6m5m4] > vmid_masks
```

其中 `mN` 表示 VMID 比较器 N 的字节掩码值
在具有少于 4 个 VMID 比较器的系统上不需要第二个值

---

**文件**: `numvmidc`（只读）
**跟踪寄存器**: 来自 IDR4
**备注**: 
VMID 比较器的数量

---

**文件**: `res_idx`（读写）
**跟踪寄存器**: 无
**备注**: 
选择要访问的资源选择控制。必须大于或等于 2，因为选择器 0 和 1 是硬连线的
**语法**: 
```
echo idx > res_idx
```

其中 `2 <= idx < nr_resource x 2`

---

**文件**: `res_ctrl`（读写）
**跟踪寄存器**: RSCTLR[idx]
**备注**: 
设置资源选择控制值。值根据 ETMv4 规范
**依赖**: `res_idx`
**语法**: 
```
echo val > res_ctrl
```

其中 `val` 根据 ETMv4 规范

---

**文件**: `nr_resource`（只读）
**跟踪寄存器**: 来自 IDR4
**备注**: 
资源选择器对的数量

---

**文件**: `event`（读写）
**跟踪寄存器**: EVENTCTRL0R
**备注**: 
设置最多 4 个实现的事件字段
**语法**: 
```
echo ev3ev2ev1ev0 > event
```

其中 `evN` 是一个 8 位的事件字段。最多 4 个事件字段组成 32 位输入值。有效字段的数量取决于具体实现，在 IDR0 中定义
:文件: ``event_instren`` (读写）
:跟踪寄存器: EVENTCTRL1R
:说明:
    选择将事件数据包插入跟踪流的事件
:依赖: EVENTCTRL0R
:语法:
    ``echo bitfield > event_instren``

    其中 bitfield 是根据事件字段数量最多为 4 位的位字段

---

:文件:            ``event_ts`` (读写）
:跟踪寄存器: TSCTLR
:说明:
    设置将生成时间戳请求的事件
:依赖: ``时间戳已激活``
:语法:
    ``echo evfield > event_ts``

    其中 evfield 是一个 8 位的事件选择器

---

:文件:            ``seq_idx`` (读写）
:跟踪寄存器: 无
:说明:
    序列器事件寄存器选择 - 0 到 2

---

:文件:            ``seq_state`` (读写）
:跟踪寄存器: SEQSTR
:说明:
    序列器当前状态 - 0 到 3

---

:文件:            ``seq_event`` (读写）
:跟踪寄存器: SEQEVR[idx]
:说明:
    状态转换事件寄存器

:依赖: ``seq_idx``
:语法:
    ``echo evBevF > seq_event``

    其中 evBevF 是由两个事件选择器组成的 16 位值，

    - evB : 后向
    - evF : 前向

---

:文件:            ``seq_reset_event`` (读写）
:跟踪寄存器: SEQRSTEVR
:说明:
    序列器重置事件

:语法:
    ``echo evfield > seq_reset_event``

    其中 evfield 是一个 8 位的事件选择器

---

:文件:            ``nrseqstate`` (只读）
:跟踪寄存器: 来自 IDR5
:说明:
    序列器状态数量（0 或 4）

---

:文件:            ``nr_pe_cmp`` (只读）
:跟踪寄存器: 来自 IDR4
:说明:
    PE 比较器输入数量

---

:文件:            ``nr_ext_inp`` (只读）
:跟踪寄存器: 来自 IDR5
:说明:
    外部输入数量

---

:文件:            ``nr_ss_cmp`` (只读）
:跟踪寄存器: 来自 IDR4
:说明:
    单次控制寄存器数量

---

*注释:* 当编程任何地址比较器时，驱动程序会为比较器打上一个类型标签——即 RANGE、SINGLE、START、STOP。一旦设置此标签，则只能使用相同的 sysfs 文件/类型来更改其值。
因此：

  % echo 0 > addr_idx		; 选择地址比较器 0
  % echo 0x1000 0x5000 0 > addr_range ; 在比较器 0 和 1 上设置地址范围
% echo 0x2000 > addr_start    ; 错误，因为比较器 0 是一个范围比较器
  % echo 2 > addr_idx		; 选择地址比较器 2
  % echo 0x2000 > addr_start	; 这是正确的，因为比较器 2 尚未使用
```shell
% echo 0x3000 > addr_stop	; 将比较器2设置为起始地址时出现错误
% echo 2 > addr_idx		; 选择地址比较器3
% echo 0x3000 > addr_stop	; 这是正确的
```

要移除所有比较器（和其他硬件）上的编程，可以使用 `reset` 参数：

```shell
% echo 1 > reset
```

### ‘mode’ sysfs参数

这是一个位字段选择参数，用于设置ETM的整体跟踪模式。下表描述了各个位的定义及其代表的功能。许多功能是可选的，因此取决于硬件实现。

---

**位 (0):**
    `ETM_MODE_EXCLUDE`

**描述:**
    这是在设置地址范围时的默认包含/排除功能值。设置为1表示排除范围。当设置模式参数时，此值将应用于当前索引的地址范围。

--- 

**位 (4):**
    `ETM_MODE_BB`

**描述:**
    如果硬件支持（[IDR0]），设置以启用分支广播。此功能的主要用途是在运行时动态修补代码时，无法仅通过条件分支重建完整的程序流。目前Perf不支持向解码器提供修改后的二进制文件，因此此功能仅用于调试目的或第三方工具。
    选择此选项会导致生成大量跟踪数据 - 可能会出现溢出风险，或者覆盖的指令较少。注意，此选项还会覆盖任何设置的 :ref:`ETM_MODE_RETURNSTACK <coresight-return-stack>`，因此当分支广播范围与返回栈范围重叠时，该范围内的返回栈将不可用。

---

**位 (5):**
    `ETMv4_MODE_CYCACC`

**描述:**
    如果硬件支持（[IDR0]），设置以启用周期准确跟踪。

---

**位 (6):**
    `ETMv4_MODE_CTXID`

**描述:**
    如果硬件支持（[IDR2]），设置以启用上下文ID跟踪。

---

**位 (7):**
    `ETM_MODE_VMID`

**描述:**
    如果硬件支持（[IDR2]），设置以启用虚拟机ID跟踪。
```
.. _coresight-timestamp:

**位 (11):**
    ETMv4_MODE_TIMESTAMP

**描述:**
    如果支持，则设置以启用时间戳生成 [IDR0]

.. _coresight-return-stack:

**位 (12):**
    ETM_MODE_RETURNSTACK
**描述:**
    如果支持，则设置以启用跟踪返回堆栈使用 [IDR0]

**位 (13-14):**
    ETM_MODE_QELEM(val)

**描述:**
    ‘val’ 确定启用的 Q 元素支持级别（如果由 ETM 实现）[IDR0]

**位 (19):**
    ETM_MODE_ATB_TRIGGER

**描述:**
    如果支持，则设置以启用事件控制寄存器中的 ATBTRIGGER 位 [EVENTCTLR1] [IDR5]

**位 (20):**
    ETM_MODE_LPOVERRIDE

**描述:**
    如果支持，则设置以启用事件控制寄存器中的 LPOVERRIDE 位 [EVENTCTLR1] [IDR5]

**位 (21):**
    ETM_MODE_ISTALL_EN

**描述:**
    设置以启用停顿控制寄存器中的 ISTALL 位 [STALLCTLR]

**位 (23):**
    ETM_MODE_INSTPRIO

**描述:**
    如果支持，则设置以启用停顿控制寄存器中的 INSTPRIORITY 位 [STALLCTLR] [IDR0]

**位 (24):**
    ETM_MODE_NOOVERFLOW

**描述:**
    如果支持，则设置以启用停顿控制寄存器中的 NOOVERFLOW 位 [STALLCTLR] [IDR3]

**位 (25):**
    ETM_MODE_TRACE_RESET

**描述:**
    如果支持，则设置以启用视图指令控制寄存器中的 TRCRESET 位 [VICTLR] [IDR3]

**位 (26):**
    ETM_MODE_TRACE_ERR

**描述:**
    设置以启用视图指令控制寄存器中的 TRCCTRL 位 [VICTLR]

**位 (27):**
    ETM_MODE_VIEWINST_STARTSTOP

**描述:**
    设置视图指令控制寄存器中视图指令开始/停止逻辑的初始状态值 [VICTLR]

**位 (30):**
    ETM_MODE_EXCL_KERN

**描述:**
    设置默认跟踪配置以排除内核模式跟踪（参见注释 a）

**位 (31):**
    ETM_MODE_EXCL_USER

**描述:**
    设置默认跟踪配置以排除用户空间跟踪（参见注释 a）

---

*注释 a)* 在启动时，ETM 被编程为使用地址范围比较器 0 来跟踪整个地址空间。‘mode’ 位 30/31 修改此设置，以设置地址范围比较器中的 EL 排除位，用于用户空间（EL0）或内核空间（EL1）的非安全状态（默认设置排除所有安全 EL 和非安全 EL2）

一旦使用了复位参数和/或实现了自定义编程，使用这些位将导致地址比较器 0 的 EL 位以相同的方式设置
*注释 b)* 位 2-3、8-10、15-16、18、22 控制仅与数据跟踪相关的功能。由于 ETMv4 架构上禁止 A-profile 数据跟踪，这里省略了这些位。可能的应用场景包括内核支持对异构系统中 R 或 M profile 基础设施的控制。
位17、28-29未使用
