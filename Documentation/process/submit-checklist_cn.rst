下面是开发者在希望自己的内核补丁能够被更快接受时应做的一些基本事项。这些要求超出了在 :ref:`Documentation/process/submitting-patches.rst <submittingpatches>` 和其他地方关于提交 Linux 内核补丁的文档。

审查您的代码
=============

1) 如果您使用了某个功能，则应在代码中 #include 定义或声明该功能的文件。不要依赖于其他头文件引入您所使用的文件。
2) 检查您的补丁是否符合 :ref:`Documentation/process/coding-style.rst <codingstyle>` 中详述的一般编码风格。
3) 所有的内存屏障（例如 `barrier()`, `rmb()`, `wmb()`）都需要在源代码中添加注释来解释它们的作用逻辑和原因。

审查 Kconfig 变更
==================

1) 新增或修改的 `CONFIG` 选项不应使配置菜单变得混乱，并且默认情况下应关闭，除非它们满足 `Documentation/kbuild/kconfig-language.rst` 中记录的例外标准。Menu 属性：默认值
2) 所有新的 `Kconfig` 选项都应包含帮助文本。
3) 已经仔细审查了与相关 `Kconfig` 组合的关系。这很难通过测试得到正确的结果——在这里需要脑力劳动。

提供文档
==========

1) 包含 :ref:`kernel-doc <kernel_doc>` 来记录全局内核 API（对于静态函数不是必需的，但在那里也可以这样做。）

2) 所有新的 `/proc` 项都应在 `Documentation/` 目录下进行记录。

3) 所有新的内核启动参数都应在 `Documentation/admin-guide/kernel-parameters.rst` 中记录。
翻译如下：

4) 所有新的模块参数都应使用 ``MODULE_PARM_DESC()`` 进行文档说明。

5) 所有新的用户空间接口都应在 ``Documentation/ABI/`` 中进行文档记录。更多信息请参阅 ``Documentation/ABI/README``。
修改用户空间接口的补丁应该抄送给
   linux-api@vger.kernel.org
6) 如果补丁添加了任何 ioctl，那么也应该更新
   ``Documentation/userspace-api/ioctl/ioctl-number.rst``
使用工具检查你的代码
==========================

1) 在提交前使用补丁样式检查器检查是否存在明显的违规行为（``scripts/checkpatch.pl``）
你应该能够为你的补丁中保留的所有违规行为提供合理解释
2) 使用 sparse 清晰地检查
3) 使用 ``make checkstack`` 并修复它发现的任何问题
请注意，``checkstack`` 不会明确指出问题，
   但是任何一个在栈上使用超过 512 字节的函数都是需要更改的候选者
构建你的代码
===============

1) 清晰构建：

  a) 使用适用或修改后的 ``CONFIG`` 选项 ``=y``、``=m`` 和
     ``=n`` 进行构建。没有 ``gcc`` 的警告/错误，没有链接器的警告/错误
b) 通过 "allnoconfig", "allmodconfig" 配置测试。

c) 使用 "O=builddir" 时，构建成功。

d) 所有文档更改在无新警告或错误的情况下构建成功。使用 "make htmldocs" 或 "make pdfdocs" 检查构建并修复任何问题。

2) 利用本地交叉编译工具或其它构建农场，在多种CPU架构上构建。注意，ppc64 是一个很好的用于交叉编译检查的架构，因为它倾向于使用 "unsigned long" 来处理64位量。

3) 新添加的代码已使用 "gcc -W" 编译（使用 "make KCFLAGS=-W"）。这将产生大量信息，但对找出如 "警告：有符号和无符号之间的比较" 这类的bug很有帮助。

4) 如果你修改的源代码依赖于或使用了与以下 "Kconfig" 符号相关的内核API或特性，那么应该在禁用相关 "Kconfig" 符号和/或设置为 "=m"（如果该选项可用）的情况下测试多次构建[不是同时禁用所有这些，而是以各种/随机组合的方式]：

   "CONFIG_SMP", "CONFIG_SYSFS", "CONFIG_PROC_FS", "CONFIG_INPUT",
   "CONFIG_PCI", "CONFIG_BLOCK", "CONFIG_PM", "CONFIG_MAGIC_SYSRQ",
   "CONFIG_NET", "CONFIG_INET=n" （但后者需与 "CONFIG_NET=y" 结合使用）

测试你的代码
==============

1) 已在同时启用 "CONFIG_PREEMPT", "CONFIG_DEBUG_PREEMPT",
   "CONFIG_SLUB_DEBUG", "CONFIG_DEBUG_PAGEALLOC", "CONFIG_DEBUG_MUTEXES",
   "CONFIG_DEBUG_SPINLOCK", "CONFIG_DEBUG_ATOMIC_SLEEP",
   "CONFIG_PROVE_RCU" 和 "CONFIG_DEBUG_OBJECTS_RCU_HEAD" 的情况下进行测试。

2) 在启用和禁用 "CONFIG_SMP" 及 "CONFIG_PREEMPT" 的情况下进行了构建和运行时测试。

3) 所有代码路径都在启用了所有锁依赖功能的情况下进行了测试。

4) 已经检查了至少注入slab和页面分配失败的情况。参见 "Documentation/fault-injection/"

如果新代码量大，可能需要增加特定子系统的故障注入。

5) 使用最新标签的linux-next进行测试，确保它仍然能在所有排队的补丁以及虚拟内存、虚拟文件系统和其他子系统中的各种变化下正常工作。
你没有给出需要翻译的文本，所以我无法完成翻译。请提供需要翻译成中文的英文文本。例如：

Translate to Chinese: "Hello, how are you?"

你好，你怎么样？
