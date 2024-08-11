### 组装器注释
=====================

版权所有 © 2017-2019 Jiri Slaby

本文档描述了用于在汇编代码中注释数据和代码的新宏。特别是，它包含了关于 `SYM_FUNC_START`、`SYM_FUNC_END`、`SYM_CODE_START` 及类似宏的信息。

#### 理由
有些代码如入口点、跳板或启动代码需要以汇编语言编写。与 C 语言一样，这样的代码被分组为函数并伴随有数据。标准的汇编器并不强制用户精确地标记这些部分为代码、数据或指定其长度。然而，汇编器为开发者提供了这样的注释来帮助调试程序贯穿整个汇编过程。此外，开发者还希望标记一些函数为“全局”以便它们在其翻译单元之外可见。

随着时间的推移，Linux 内核从各种项目（如 `binutils`）采纳了一些宏来促进这类注释。因此，出于历史原因，开发者已经在汇编中使用了 `ENTRY`、`END`、`ENDPROC` 和其他注释。由于缺乏文档，这些宏在某些地方被错误地使用。显然，`ENTRY` 是用来表示全局符号（无论是数据还是代码）的开始，而 `END` 用来标记数据的结束或具有非标准调用约定的特殊函数的结束。相比之下，`ENDPROC` 应该只用来注释标准函数的结束。

当这些宏被正确使用时，它们可以帮助汇编器生成一个良好的对象，其中大小和类型都被正确设置。例如，`arch/x86/lib/putuser.S` 的结果如下：

```
Num:    Value          Size Type    Bind   Vis      Ndx Name
25: 0000000000000000    33 FUNC    GLOBAL DEFAULT    1 __put_user_1
29: 0000000000000030    37 FUNC    GLOBAL DEFAULT    1 __put_user_2
32: 0000000000000060    36 FUNC    GLOBAL DEFAULT    1 __put_user_4
35: 0000000000000090    37 FUNC    GLOBAL DEFAULT    1 __put_user_8
```

这不仅对于调试目的很重要。当有像这样适当注释的对象时，可以在它们之上运行工具来生成更有用的信息。特别是，在适当注释的对象上，可以运行 `objtool` 来检查并必要时修复对象。目前，`objtool` 可以报告函数中缺少帧指针的设置/销毁。它还可以自动生成针对 ORC 解绕器（[Documentation/arch/x86/orc-unwinder.rst](Documentation/arch/x86/orc-unwinder.rst)）的注释，适用于大多数代码。这两点对于支持可靠的堆栈跟踪尤其重要，而可靠的堆栈跟踪对于内核实时打补丁又是必要的（[Documentation/livepatch/livepatch.rst](Documentation/livepatch/livepatch.rst)）。

#### 注意和讨论
人们可能已经意识到，以前只有三个宏。这确实不足以覆盖所有的情况组合：

* 标准/非标准函数
* 代码/数据
* 全局/局部符号

有一个讨论_，并且决定不扩展当前的 `ENTRY/END*` 宏，而是引入全新的宏。

```
所以为什么不使用真正显示目的的宏名，而不是导入所有这些糟糕的历史上随机选择的调试符号宏名，这些宏名来自 `binutils` 和更老的内核？

.. _discussion: https://lore.kernel.org/r/20170217104757.28588-1-jslaby@suse.cz
```

#### 宏的描述
新宏以 `SYM_` 前缀开头，并且可以分为三大类：

1. `SYM_FUNC_*` —— 用来注释类似于 C 的函数。这意味着遵循标准 C 调用约定的函数。例如，在 x86 上，这意味着栈在一个预定义的位置包含返回地址，并且可以从函数中以标准方式返回。当启用帧指针时，应当在函数开始和结束时分别保存/恢复帧指针。
检查工具如 `objtool` 应确保这些标记的函数符合这些规则。工具也可以轻松地自动为这些函数添加调试信息（如 *ORC 数据*）。
2. `SYM_CODE_*` —— 特殊函数，使用特殊的栈调用。可能是具有特殊栈内容的中断处理程序、跳板或启动函数。
检查工具主要忽略对这些函数的检查。但仍然可以自动生成一些调试信息。为了正确的调试数据，这段代码需要开发者提供的提示，如 `UNWIND_HINT_REGS`。
3. ``SYM_DATA*`` —— 显然属于 ``.data`` 部分的数据，而不是 ``.text``。数据不包含指令，因此工具必须特殊处理：它们不应该将字节视为指令，也不应该给它们分配任何调试信息。
   
   指令宏
   ~~~~~~~~~~
   
   本节涵盖了上述的 ``SYM_FUNC_*`` 和 ``SYM_CODE_*`` 枚举。“objtool”要求所有代码都必须包含在一个 ELF 符号中。带有 ``.L`` 前缀的符号名称不会生成符号表条目。带有 ``.L`` 前缀的符号可以在代码区域内使用，但应避免用于通过 ``SYM_*_START/END`` 注释来表示代码范围。
   
   * ``SYM_FUNC_START`` 和 ``SYM_FUNC_START_LOCAL`` 应该是 **最常用的标记**。它们用于具有标准调用约定的函数——全局和局部。就像在 C 语言中一样，它们都将函数对齐到特定于架构的 ``__ALIGN`` 字节。对于开发者不希望这种隐式对齐的特殊情况，还提供了 ``_NOALIGN`` 变体。
   
     ``SYM_FUNC_START_WEAK`` 和 ``SYM_FUNC_START_WEAK_NOALIGN`` 标记也作为 C 语言中已知的 *弱* 属性的汇编器对应项提供。
   
   这些标记 **应当** 与 ``SYM_FUNC_END`` 结合使用。首先，它将指令序列标记为一个函数，并计算其大小并将其添加到生成的对象文件中。其次，这也简化了此类对象文件的检查和处理，因为工具可以轻松地找到确切的函数边界。
   
   因此，在大多数情况下，开发者应该像下面的例子那样编写代码，当然，宏之间会有一些汇编指令：

```assembly
    SYM_FUNC_START(memset)
        ... asm insns ..
    SYM_FUNC_END(memset)
```

   实际上，这种注释方式对应于现已弃用的 ``ENTRY`` 和 ``ENDPROC`` 宏。
   
   * ``SYM_FUNC_ALIAS``, ``SYM_FUNC_ALIAS_LOCAL``, 和 ``SYM_FUNC_ALIAS_WEAK`` 可以用来为一个函数定义多个名称。典型用途如下：

```assembly
    SYM_FUNC_START(__memset)
        ... asm insns ..
    SYM_FUNC_END(__memset)
    SYM_FUNC_ALIAS(memset, __memset)
```

   在这个例子中，可以调用 ``__memset`` 或者 ``memset``，结果相同，除了指令的调试信息只针对非-``ALIAS`` 的情况生成一次——即只为 ``__memset`` 生成到对象文件中。
* ``SYM_CODE_START`` 和 ``SYM_CODE_START_LOCAL`` 应仅在特殊情况下使用——如果你知道自己在做什么。这专门用于中断处理程序和类似场合，其中调用约定不是C语言的。也存在 ``_NOALIGN`` 变体。其使用方式与上面的 ``FUNC`` 类别相同：

    ```plaintext
    SYM_CODE_START_LOCAL(bad_put_user)
        ... asm 指令 ..
    SYM_CODE_END(bad_put_user)
    ```

  再次强调，每一个 ``SYM_CODE_START*`` **必须** 配对使用 ``SYM_CODE_END``。在某种程度上，此类别对应于已废弃的 ``ENTRY`` 和 ``END``。只是 ``END`` 还有其他多种含义。
* ``SYM_INNER_LABEL*`` 用于标记位于某个 ``SYM_{CODE,FUNC}_START`` 和 ``SYM_{CODE,FUNC}_END`` 之间的标签。它们非常类似于C中的标签，但可以被声明为全局可见。一个使用示例：

    ```plaintext
    SYM_CODE_START(ftrace_caller)
        /* save_mcount_regs 填充前两个参数 */
        ..
    SYM_INNER_LABEL(ftrace_caller_op_ptr, SYM_L_GLOBAL)
        /* 将ftrace_ops加载到第三个参数中 */
        ..
    SYM_INNER_LABEL(ftrace_call, SYM_L_GLOBAL)
        call ftrace_stub
        ..
    retq
    SYM_CODE_END(ftrace_caller)
    ```

### 数据宏

如同指令一样，有一些宏用于描述汇编代码中的数据：
* ``SYM_DATA_START`` 和 ``SYM_DATA_START_LOCAL`` 标记数据的开始，并应与 ``SYM_DATA_END`` 或 ``SYM_DATA_END_LABEL`` 结合使用。后者还会添加一个结束标签，以便人们可以在下面的例子中使用 ``lstack`` 和（局部） ``lstack_end``：

    ```plaintext
    SYM_DATA_START_LOCAL(lstack)
        .skip 4096
    SYM_DATA_END_LABEL(lstack, SYM_L_LOCAL, lstack_end)
    ```

* ``SYM_DATA`` 和 ``SYM_DATA_LOCAL`` 是用于简单、大多单行数据的变体：

    ```plaintext
    SYM_DATA(HEAP,     .long rm_heap)
    SYM_DATA(heap_end, .long rm_stack)
    ```

  最终，它们会扩展为内部使用的 ``SYM_DATA_START`` 和 ``SYM_DATA_END``。

### 支持宏

所有上述宏最终都会归结为某种形式的 ``SYM_START``、``SYM_END`` 或 ``SYM_ENTRY`` 的调用。通常，开发者应当避免直接使用这些宏。
此外，在上述示例中可以看到 ``SYM_L_LOCAL``。还有 ``SYM_L_GLOBAL`` 和 ``SYM_L_WEAK``。所有这些都旨在表示由它们标记的符号的链接属性。它们要么在先前宏的 ``_LABEL`` 变体中使用，要么在 ``SYM_START`` 中使用。
覆盖宏
~~~~~~~~~~~~
架构也可以在它们自己的 `asm/linkage.h` 中覆盖任何宏，包括指定符号类型 (`SYM_T_FUNC`、`SYM_T_OBJECT` 和 `SYM_T_NONE`) 的宏。由于此文件中描述的每个宏都被 `#ifdef` + `#endif` 包围，因此只需在上述架构相关的头文件中以不同的方式定义这些宏就足够了。
