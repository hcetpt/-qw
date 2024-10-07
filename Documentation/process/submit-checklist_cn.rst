.. _submitchecklist:

=======================================
Linux 内核补丁提交检查清单
=======================================

以下是一些基本事项，如果开发者希望他们的内核补丁能够更快被接受，应该遵守这些事项。这些要求是在 :ref:`Documentation/process/submitting-patches.rst <submittingpatches>` 和其他地方提供的关于提交 Linux 内核补丁的文档之外的要求。

审查你的代码
================

1) 如果你使用了一个功能，则应 #include 定义/声明该功能的文件。不要依赖其他头文件来引入你使用的文件。
2) 根据 :ref:`Documentation/process/coding-style.rst <codingstyle>` 中详细描述的一般风格检查你的补丁。
3) 所有内存屏障（例如 ``barrier()``、``rmb()``、``wmb()``）都需要在源代码中添加注释，解释它们的作用逻辑和原因。

审查 Kconfig 变更
======================

1) 任何新的或修改的 ``CONFIG`` 选项不应干扰配置菜单，并且默认为关闭状态，除非它们符合 ``Documentation/kbuild/kconfig-language.rst`` 中记录的例外标准：菜单属性：默认值。
2) 所有新的 ``Kconfig`` 选项都应包含帮助文本。
3) 已经仔细审查了与相关 ``Kconfig`` 组合的关系。这在测试时非常难以做到——需要脑力付出。

提供文档
=====================

1) 包含 :ref:`kernel-doc <kernel_doc>` 以记录全局内核 API（静态函数不需要，但也可以这样做。）
2) 所有新的 ``/proc`` 条目应在 ``Documentation/`` 下进行记录。
3) 所有新的内核启动参数应在 ``Documentation/admin-guide/kernel-parameters.rst`` 中记录。
### 文档说明

4) 所有新的模块参数都使用 ``MODULE_PARM_DESC()`` 进行了文档说明。

5) 所有新的用户空间接口都在 ``Documentation/ABI/`` 中进行了文档说明。
更多详细信息请参见 ``Documentation/ABI/README``。
修改用户空间接口的补丁应抄送给 `linux-api@vger.kernel.org`。
6) 如果补丁添加了任何 ioctl，还应更新 ``Documentation/userspace-api/ioctl/ioctl-number.rst``。

### 使用工具检查代码

####

1) 提交前使用补丁风格检查器（``scripts/checkpatch.pl``）检查简单的违规项。
你应该能够为补丁中剩余的所有违规项提供合理的解释。
2) 使用 sparse 清晰地进行检查。
3) 使用 ``make checkstack`` 并修复它发现的问题。
注意：``checkstack`` 不会明确指出问题，但任何使用超过 512 字节栈空间的函数都是需要修改的对象。

### 编译代码

####

1) 清晰编译：

  a) 使用适用或修改后的 ``CONFIG`` 选项设置为 ``=y``、``=m`` 和 ``=n``。无 ``gcc`` 警告/错误，无链接器警告/错误。
b) 通过了 ``allnoconfig`` 和 ``allmodconfig`` 测试

c) 使用 ``O=builddir`` 时构建成功

d) 文档更改（如果有）在构建过程中没有新的警告或错误。使用 ``make htmldocs`` 或 ``make pdfdocs`` 进行检查并修复任何问题。

2) 在多种CPU架构上使用本地交叉编译工具或其他构建农场进行构建。注意，ppc64 是一个很好的交叉编译测试架构，因为它倾向于使用 ``unsigned long`` 来表示64位的数量。

3) 新增代码已使用 ``gcc -W`` 编译（使用 ``make KCFLAGS=-W``）。这会产生很多噪音，但有助于发现诸如“警告：有符号与无符号之间的比较”之类的错误。

4) 如果您的修改源码依赖于或使用了以下任何与内核API或功能相关的 ``Kconfig`` 符号，请测试这些相关符号禁用和/或设置为 ``=m``（如果该选项可用）的多种构建组合（不是同时禁用所有这些，而是各种随机组合）：

``CONFIG_SMP``、``CONFIG_SYSFS``、``CONFIG_PROC_FS``、``CONFIG_INPUT``、``CONFIG_PCI``、``CONFIG_BLOCK``、``CONFIG_PM``、``CONFIG_MAGIC_SYSRQ``、``CONFIG_NET``、``CONFIG_INET=n``（但后者应与 ``CONFIG_NET=y`` 一起使用）

测试代码
========

1) 已在同时启用 ``CONFIG_PREEMPT``、``CONFIG_DEBUG_PREEMPT``、``CONFIG_SLUB_DEBUG``、``CONFIG_DEBUG_PAGEALLOC``、``CONFIG_DEBUG_MUTEXES``、``CONFIG_DEBUG_SPINLOCK``、``CONFIG_DEBUG_ATOMIC_SLEEP``、``CONFIG_PROVE_RCU`` 和 ``CONFIG_DEBUG_OBJECTS_RCU_HEAD`` 的情况下进行了测试。

2) 已在启用和禁用 ``CONFIG_SMP`` 和 ``CONFIG_PREEMPT`` 的情况下进行了构建和运行测试。

3) 所有代码路径均在启用了所有锁依赖特性的情况下进行了测试。

4) 至少注入了slab和页面分配失败，并进行了检查。参见 ``Documentation/fault-injection/``。如果新代码量较大，则可能需要添加特定子系统的故障注入。

5) 使用最新的linux-next标签进行了测试，以确保其与其他排队补丁及VM、VFS和其他子系统中的各种更改兼容。
当然，请提供你需要翻译的文本。
