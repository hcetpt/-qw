符号命名空间
=================

以下文档描述了如何使用符号命名空间来结构化通过EXPORT_SYMBOL()宏家族导出的内核符号的导出表面。
.. 目录表

	=== 1 引言
	=== 2 如何定义符号命名空间
	   --- 2.1 使用EXPORT_SYMBOL宏
	   --- 2.2 使用DEFAULT_SYMBOL_NAMESPACE定义
	=== 3 如何使用在命名空间中导出的符号
	=== 4 加载使用命名空间符号的模块
	=== 5 自动创建MODULE_IMPORT_NS语句

1. 引言
===============

引入符号命名空间作为一种手段，用于结构化内核API的导出表面。它允许子系统维护者将其导出的符号划分到独立的命名空间中。这对于文档目的（例如，考虑SUBSYSTEM_DEBUG命名空间）以及限制一组符号在内核其他部分中的可用性都是有用的。目前，使用被导出到命名空间中的符号的模块需要导入该命名空间。否则，根据内核配置的不同，内核将拒绝加载该模块或警告缺少导入。
2. 如何定义符号命名空间
==================================

可以通过不同方法将符号导出到命名空间。所有这些方法都改变了EXPORT_SYMBOL及其相关宏的工作方式，以创建ksymtab条目。
2.1 使用EXPORT_SYMBOL宏
==================================

除了EXPORT_SYMBOL()和EXPORT_SYMBOL_GPL()宏之外，还可以使用它们导出内核符号到内核符号表，还提供了这些宏的变体以将符号导出到特定的命名空间：EXPORT_SYMBOL_NS()和EXPORT_SYMBOL_NS_GPL()。它们接受一个额外的参数：命名空间。

请注意，由于宏展开，该参数需要是一个预处理符号。例如，要将符号`usb_stor_suspend`导出到命名空间`USB_STORAGE`中，请使用：

	EXPORT_SYMBOL_NS(usb_stor_suspend, USB_STORAGE);

相应的ksymtab条目结构`kernel_symbol`的成员`namespace`将相应设置。没有命名空间导出的符号将引用`NULL`。如果没有定义，默认情况下没有默认命名空间。`modpost`和内核/module/main.c在构建时或加载模块时利用此命名空间。
2.2 使用DEFAULT_SYMBOL_NAMESPACE定义
=============================================

为子系统的所有符号定义命名空间可能非常冗长，并且可能难以维护。因此，提供了一个默认定义（DEFAULT_SYMBOL_NAMESPACE），如果设置了该定义，则将成为所有未指定命名空间的EXPORT_SYMBOL()和EXPORT_SYMBOL_GPL()宏扩展的默认值。

有多种方式可以指定此定义，具体取决于子系统和维护者的偏好。第一个选项是在子系统的`Makefile`中定义默认命名空间。例如，为了将usb-common中定义的所有符号导出到USB_COMMON命名空间中，请在drivers/usb/common/Makefile中添加如下行：

	ccflags-y += -DDEFAULT_SYMBOL_NAMESPACE=USB_COMMON

这将影响所有EXPORT_SYMBOL()和EXPORT_SYMBOL_GPL()声明。当存在此定义时，使用EXPORT_SYMBOL_NS()导出的符号仍将被导出到作为命名空间参数传递的命名空间中，因为该参数优先于默认符号命名空间。

在编译单元中直接作为预处理器语句定义默认命名空间是第二个选项。上述示例将在对应的编译单元中变为：

	#undef  DEFAULT_SYMBOL_NAMESPACE
	#define DEFAULT_SYMBOL_NAMESPACE USB_COMMON

在使用任何EXPORT_SYMBOL宏之前。
3. 如何使用在命名空间中导出的符号
============================================

为了使用导出到命名空间中的符号，内核模块需要明确导入这些命名空间。否则，内核可能会拒绝加载该模块。模块代码需要使用MODULE_IMPORT_NS宏来导入其使用的符号所在的命名空间。例如，使用上面的usb_stor_suspend符号的模块需要使用如下语句导入USB_STORAGE命名空间：

	MODULE_IMPORT_NS(USB_STORAGE);

这将在模块中为每个导入的命名空间创建一个“modinfo”标签。

这样做的副作用是，可以通过modinfo检查模块导入的命名空间：

	$ modinfo drivers/usb/storage/ums-karma.ko
	[...]
	import_ns:      USB_STORAGE
	[...]

建议将MODULE_IMPORT_NS()语句与其它模块元数据定义（如MODULE_AUTHOR()或MODULE_LICENSE()）放在附近。请参阅第5节了解自动创建缺失导入语句的方法。
4. 加载使用了命名空间符号的模块
==============================================

在模块加载时（例如通过 `insmod`），内核会检查模块引用的所有符号是否可用，以及这些符号可能导出到的命名空间是否已被该模块导入。内核默认的行为是拒绝加载没有指定足够导入信息的模块。这种情况下，将会记录一个错误并以EINVAL失败。为了允许加载不满足这个前提条件的模块，可以设置一个配置选项：将 `MODULE_ALLOW_MISSING_NAMESPACE_IMPORTS=y` 设置为开启状态即可允许加载，但会发出警告。

5. 自动创建 `MODULE_IMPORT_NS` 语句
=====================================================

未导入的命名空间可以在构建时很容易地被检测出来。实际上，`modpost` 如果发现模块使用了一个未导入的命名空间中的符号，将会发出警告。
`MODULE_IMPORT_NS()` 语句通常会被添加到一个固定的位置（与其它模块元数据一起）。为了让模块作者和子系统维护者的工作更加轻松，提供了一个脚本和 make 目标来修复缺失的导入。修复缺失的导入可以通过以下命令完成：

	$ make nsdeps

对于模块作者来说，一个典型的场景如下：

	- 编写依赖于未导入命名空间中符号的代码
	- 运行 `make`
	- 注意 `modpost` 发出的关于缺失导入的警告
	- 运行 `make nsdeps` 将导入添加到正确的代码位置

对于引入新命名空间的子系统维护者而言，步骤非常相似。再次强调，`make nsdeps` 最终会为内核树内的模块添加缺失的命名空间导入：

	- 将符号移动或添加到命名空间（例如通过 `EXPORT_SYMBOL_NS()`）
	- 运行 `make`（最好使用 allmodconfig 来覆盖所有的内核模块）
	- 注意 `modpost` 发出的关于缺失导入的警告
	- 运行 `make nsdeps` 将导入添加到正确的代码位置

你也可以为外部模块构建运行 `nsdeps`。一个典型的用法如下：

	$ make -C <kernel_source_path> M=$PWD nsdeps
