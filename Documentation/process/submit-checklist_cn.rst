下面是开发者在希望他们的内核补丁能够被更快接受时应做的一些基本事项。这些要求超出了在 :ref:`Documentation/process/submitting-patches.rst <submittingpatches>` 和其他地方关于提交 Linux 内核补丁的文档。

审查您的代码
=============

1) 如果您使用了某个功能，则应该 #include 定义或声明该功能的文件。不要依赖于其他头文件引入您使用的文件。
2) 根据 :ref:`Documentation/process/coding-style.rst <codingstyle>` 中的细节检查您的补丁的一般风格。
3) 所有的内存屏障（例如，`barrier()`、`rmb()`、`wmb()`）都需要在源代码中添加注释来解释它们的作用逻辑和原因。

审查 Kconfig 变更
==================

1) 任何新的或修改过的 `CONFIG` 选项不应破坏配置菜单，并且默认情况下应为关闭状态，除非它们满足 `Documentation/kbuild/kconfig-language.rst` 中所记录的例外标准。Menu 属性：默认值。
2) 所有新的 `Kconfig` 选项都有帮助文本。
3) 已经仔细审查与相关的 `Kconfig` 组合。这很难通过测试来验证——需要大量的脑力工作。

提供文档
============

1) 包含 :ref:`kernel-doc <kernel_doc>` 来记录全局内核 API（对于静态函数不是必需的，但也可以这样做。）
2) 所有新的 `/proc` 入口都在 `Documentation/` 下进行文档说明。
3) 所有新的内核启动参数都记录在 `Documentation/admin-guide/kernel-parameters.rst` 中。
### 使用 `MODULE_PARM_DESC()` 文档化所有新的模块参数

### 在 `Documentation/ABI/` 中文档化所有新的用户空间接口
更多详情请参阅 `Documentation/ABI/README`。
更改用户空间接口的补丁应抄送给 `linux-api@vger.kernel.org`。

### 如果补丁添加了任何 ioctl，则还需更新
`Documentation/userspace-api/ioctl/ioctl-number.rst`

### 使用工具检查你的代码

#### 1) 提交前使用补丁样式检查器检查简单的违规 (`scripts/checkpatch.pl`)
你应该能够为你的补丁中剩余的所有违规提供合理的解释。

#### 2) 使用 sparse 清晰地检查。
#### 3) 使用 `make checkstack` 并修复它发现的任何问题
请注意，`checkstack` 不会明确指出问题，
但是任何一个在栈上使用超过 512 字节的函数都是需要修改的对象。

### 构建你的代码

#### 1) 清晰构建：

  - a) 使用适用或修改后的 `CONFIG` 选项 `=y`、`=m` 和 `=n`。无 `gcc` 警告/错误，无链接器警告/错误。
b) 通过了 ``allnoconfig`` 和 ``allmodconfig`` 测试。

c) 使用 ``O=builddir`` 时能成功构建。

d) 所有文档更改都能成功构建，且没有新的警告或错误。使用 ``make htmldocs`` 或 ``make pdfdocs`` 来检查构建并修复任何问题。

2) 能在多种CPU架构上构建，通过使用本地交叉编译工具或其他构建农场。注意ppc64是一个很好的用于交叉编译检查的架构，因为它倾向于将 ``unsigned long`` 用于64位的数量。

3) 新添加的代码已使用 ``gcc -W`` 进行编译（使用 ``make KCFLAGS=-W``）。这会产生很多信息输出，但有助于发现如“警告：带符号和无符号之间的比较”之类的bug。

4) 如果您的修改后的源代码依赖于或使用了与以下 ``Kconfig`` 符号相关的内核API或特性，则应在禁用相关 ``Kconfig`` 符号或将其设置为 ``=m``（如果该选项可用）的情况下测试多次构建[不是同时禁用所有这些符号，而是测试各种随机组合]：

``CONFIG_SMP``、``CONFIG_SYSFS``、``CONFIG_PROC_FS``、``CONFIG_INPUT``、``CONFIG_PCI``、``CONFIG_BLOCK``、``CONFIG_PM``、``CONFIG_MAGIC_SYSRQ``、``CONFIG_NET``、``CONFIG_INET=n``（但后者应与 ``CONFIG_NET=y`` 结合使用）。

测试您的代码
=============

1) 已在同时启用 ``CONFIG_PREEMPT``、``CONFIG_DEBUG_PREEMPT``、``CONFIG_SLUB_DEBUG``、``CONFIG_DEBUG_PAGEALLOC``、``CONFIG_DEBUG_MUTEXES``、``CONFIG_DEBUG_SPINLOCK``、``CONFIG_DEBUG_ATOMIC_SLEEP``、``CONFIG_PROVE_RCU`` 和 ``CONFIG_DEBUG_OBJECTS_RCU_HEAD`` 的情况下进行了测试。

2) 在启用和禁用 ``CONFIG_SMP`` 和 ``CONFIG_PREEMPT`` 的情况下进行了构建和运行测试。

3) 在启用了所有锁依赖特性的情况下，所有代码路径都得到了验证。

4) 已检查至少注入了slab和页分配失败的情况。参见 ``Documentation/fault-injection/``。
如果新增代码量较大，增加特定子系统的故障注入可能是合适的。

5) 使用最新的linux-next标签进行了测试，以确保其与其他排队的补丁以及虚拟内存管理器（VM）、虚拟文件系统（VFS）和其他子系统中的各种变更兼容。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
