### Ptrace

GDB打算支持BookE处理器的以下硬件调试特性：

- 4个硬件断点（IAC）
- 2个硬件监视点（读、写和读写）（DAC）
- 2个硬件监视点的值条件（DVC）

为了实现这一点，我们需要扩展`ptrace`功能，以便GDB能够查询和设置这些资源。既然我们正在做扩展，我们尝试创建一个可扩展的接口，并且该接口同时覆盖BookE和服务器处理器，这样GDB就不需要为每种处理器特别处理。我们新增了以下三个`ptrace`请求：
1. PPC_PTRACE_GETHWDBGINFO
============================

供GDB查询以发现硬件调试特性。这里主要返回的信息是硬件监视点的最小对齐要求。BookE处理器在这方面没有限制，但服务器处理器对于硬件监视点有一个8字节的对齐限制。我们希望避免根据在AUXV中看到的内容向GDB添加特殊处理。
由于我们正在进行这项工作，我们还增加了其他有用的信息，内核可以返回给GDB：此查询将返回硬件断点的数量、硬件监视点的数量以及是否支持地址范围和条件。查询将填充请求进程提供的以下结构体：

```c
struct ppc_debug_info {
    uint32_t version;
    uint32_t num_instruction_bps;
    uint32_t num_data_bps;
    uint32_t num_condition_regs;
    uint32_t data_bp_alignment;
    uint32_t sizeof_condition; /* DVC寄存器的大小 */
    uint64_t features; /* 特性位掩码 */
};
```

`features`字段将包含以下特性的位标志：

```c
#define PPC_DEBUG_FEATURE_INSN_BP_RANGE     0x1
#define PPC_DEBUG_FEATURE_INSN_BP_MASK      0x2
#define PPC_DEBUG_FEATURE_DATA_BP_RANGE     0x4
#define PPC_DEBUG_FEATURE_DATA_BP_MASK      0x8
#define PPC_DEBUG_FEATURE_DATA_BP_DAWR      0x10
#define PPC_DEBUG_FEATURE_DATA_BP_ARCH_31   0x20
```

2. PPC_PTRACE_SETHWDEBUG

根据提供的结构设置硬件断点或监视点：

```c
struct ppc_hw_breakpoint {
    uint32_t version;
    /* 触发类型定义 */
    uint32_t trigger_type;
    /* 地址匹配模式定义 */
    uint32_t addr_mode;
    /* 条件模式定义 */
    uint32_t condition_mode;
    uint64_t addr;
    uint64_t addr2;
    uint64_t condition_value;
};
```

一个请求指定一个事件，而不仅仅是一个要设置的寄存器。
例如，如果请求的是带有条件的监视点，则在同一请求中将同时设置DAC和DVC寄存器。
通过这种方式，GDB可以请求所有BookE支持的硬件断点和监视点。服务器处理器中可用的COME FROM断点不在本工作的范围内。
`ptrace`将返回一个整数（句柄），唯一标识所创建的断点或监视点。这个整数将在PPC_PTRACE_DELHWDEBUG请求中用于请求删除它。如果请求的断点无法在寄存器上分配，则返回-ENOSPC。
一些使用结构的例子：

- 在第一个断点寄存器中设置断点：

```c
p.version         = PPC_DEBUG_CURRENT_VERSION;
p.trigger_type    = PPC_BREAKPOINT_TRIGGER_EXECUTE;
p.addr_mode       = PPC_BREAKPOINT_MODE_EXACT;
p.condition_mode  = PPC_BREAKPOINT_CONDITION_NONE;
p.addr            = (uint64_t) address;
p.addr2           = 0;
p.condition_value = 0;
```

- 在第二个监视点寄存器中设置触发于读操作的监视点：

```c
p.version         = PPC_DEBUG_CURRENT_VERSION;
p.trigger_type    = PPC_BREAKPOINT_TRIGGER_READ;
p.addr_mode       = PPC_BREAKPOINT_MODE_EXACT;
p.condition_mode  = PPC_BREAKPOINT_CONDITION_NONE;
p.addr            = (uint64_t) address;
p.addr2           = 0;
p.condition_value = 0;
```

- 设置仅在特定值时触发的监视点：

```c
p.version         = PPC_DEBUG_CURRENT_VERSION;
p.trigger_type    = PPC_BREAKPOINT_TRIGGER_READ;
p.addr_mode       = PPC_BREAKPOINT_MODE_EXACT;
p.condition_mode  = PPC_BREAKPOINT_CONDITION_AND | PPC_BREAKPOINT_CONDITION_BE_ALL;
p.addr            = (uint64_t) address;
p.addr2           = 0;
p.condition_value = (uint64_t) condition;
```

- 设置范围型硬件断点：

```c
p.version         = PPC_DEBUG_CURRENT_VERSION;
p.trigger_type    = PPC_BREAKPOINT_TRIGGER_EXECUTE;
p.addr_mode       = PPC_BREAKPOINT_MODE_RANGE_INCLUSIVE;
p.condition_mode  = PPC_BREAKPOINT_CONDITION_NONE;
p.addr            = (uint64_t) begin_range;
p.addr2           = (uint64_t) end_range;
p.condition_value = 0;
```

- 在服务器处理器（BookS）中设置监视点：

```c
p.version         = 1;
p.trigger_type    = PPC_BREAKPOINT_TRIGGER_RW;
p.addr_mode       = PPC_BREAKPOINT_MODE_RANGE_INCLUSIVE;
// 或
p.addr_mode       = PPC_BREAKPOINT_MODE_EXACT;
p.condition_mode  = PPC_BREAKPOINT_CONDITION_NONE;
p.addr            = (uint64_t) begin_range;
/* 对于PPC_BREAKPOINT_MODE_RANGE_INCLUSIVE，addr2需要被指定，其中
 * addr2 - addr <= 8 字节
*/
p.addr2           = (uint64_t) end_range;
p.condition_value = 0;
```

3. PPC_PTRACE_DELHWDEBUG

接收一个标识现有断点或监视点的整数（即，从`PTRACE_SETHWDEBUG`返回的值），并删除对应的断点或监视点。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
