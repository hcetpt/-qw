构建外部模块
=========================

本文档描述了如何构建树外内核模块。
.. 目录

	=== 1 引言
	=== 2 如何构建外部模块
	   --- 2.1 命令语法
	   --- 2.2 选项
	   --- 2.3 构建目标
	   --- 2.4 构建独立文件
	=== 3 为外部模块创建 Kbuild 文件
	   --- 3.1 共享的 Makefile
	   --- 3.2 单独的 Kbuild 文件和 Makefile
	   --- 3.3 二进制 Blob
	   --- 3.4 构建多个模块
	=== 4 包含文件
	   --- 4.1 内核包含文件
	   --- 4.2 单个子目录
	   --- 4.3 多个子目录
	=== 5 模块安装
	   --- 5.1 INSTALL_MOD_PATH
	   --- 5.2 INSTALL_MOD_DIR
	=== 6 模块版本控制
	   --- 6.1 来自内核的符号（vmlinux + 模块）
	   --- 6.2 符号和外部模块
	   --- 6.3 来自另一个外部模块的符号
	=== 7 小贴士与技巧
	   --- 7.1 测试 CONFIG_FOO_BAR 配置项

1. 引言
===============

"kbuild" 是 Linux 内核使用的构建系统。为了保持与构建基础设施的变化兼容并获取正确的 "gcc" 标志，模块必须使用 kbuild。提供了构建树内和树外模块的功能。无论是构建树内还是树外模块，方法都是相似的，并且所有模块最初都是在树外开发和构建的。

本文档中的信息旨在帮助有兴趣构建树外（或“外部”）模块的开发者。外部模块的作者应提供一个 Makefile 来隐藏大部分复杂性，因此只需键入 "make" 即可构建模块。这很容易实现，并将在第 3 节中给出一个完整的示例。

2. 如何构建外部模块
================================

要构建外部模块，您需要有一个预先构建好的内核，该内核包含用于构建的配置文件和头文件。此外，内核必须是启用模块支持的情况下构建的。如果您使用的是发行版内核，则您的发行版会提供一个用于运行内核的包。

另一种选择是使用 "make" 目标 "modules_prepare"。这将确保内核包含所需的信息。该目标仅作为准备内核源代码树以构建外部模块的一种简单方式而存在。

注意：即使设置了 CONFIG_MODVERSIONS，"modules_prepare" 也不会构建 Module.symvers；因此，需要执行完整的内核构建以使模块版本控制生效。

2.1 命令语法
==================

构建外部模块的命令如下：

	$ make -C <path_to_kernel_src> M=$PWD

kbuild 系统通过命令中的 "M=<dir>" 选项知道正在构建外部模块。

针对当前运行的内核构建时，可以使用以下命令：

	$ make -C /lib/modules/`uname -r`/build M=$PWD

然后要安装刚刚构建的模块，可以在命令中添加目标 "modules_install"：

	$ make -C /lib/modules/`uname -r`/build M=$PWD modules_install

2.2 选项
===========

（$KDIR 指内核源代码目录的路径）

make -C $KDIR M=$PWD

	-C $KDIR
		内核源代码所在的目录。"make" 在执行时会切换到指定目录，并在完成后返回。
M=$PWD  
通知 kbuild 正在构建一个外部模块  
给 "M" 的值是外部模块（kbuild 文件）所在的目录的绝对路径  

2.3 目标  
----------------  
当构建一个外部模块时，只有部分 "make" 目标可用  
make -C $KDIR M=$PWD [target]  

默认情况下，会构建当前目录中的模块，因此不需要指定目标。所有输出文件也将生成在此目录中。不会尝试更新内核源代码，并且前提是已经成功执行了内核的 "make" 命令  

modules  
外部模块的默认目标。它与未指定目标时的功能相同。参见上面的描述  

modules_install  
安装外部模块。默认位置是 /lib/modules/<kernel_release>/updates/，但可以使用 INSTALL_MOD_PATH 添加前缀（在第 5 节讨论）  

clean  
仅移除模块目录中的所有生成文件  

help  
列出外部模块的可用目标  

2.4 单独构建文件  
----------------------------  

可以单独构建模块的一部分文件  
这对于内核、模块甚至外部模块同样适用。
示例（模块foo.ko由bar.o和baz.o组成）：

		make -C $KDIR M=$PWD bar.lst
		make -C $KDIR M=$PWD baz.o
		make -C $KDIR M=$PWD foo.ko
		make -C $KDIR M=$PWD ./

3. 创建外部模块的Kbuild文件
================================

在上一节中，我们看到了用于构建当前内核模块的命令。然而，该模块实际上并未被构建，因为需要一个构建文件。该文件将包含正在构建的模块名称以及必需的源文件列表。该文件可以简单到只有一行：

	obj-m := <module_name>.o

kbuild系统将从<module_name>.c构建<module_name>.o，并在链接后生成内核模块<module_name>.ko。上述行可以放在“Kbuild”文件或“Makefile”中。当模块由多个源文件构建时，需要额外的一行列出这些文件：

	<module_name>-y := <src1>.o <src2>.o ...

注意：关于kbuild使用的语法的进一步文档位于Documentation/kbuild/makefiles.rst。

下面的示例演示了如何为模块8123.ko创建构建文件，该模块由以下文件构建：

	8123_if.c
	8123_if.h
	8123_pci.c
	8123_bin.o_shipped	<= 二进制块

3.1 共享Makefile
-------------------

	外部模块始终包括一个包装的Makefile，支持使用“make”无参数构建模块。
此目标不是由kbuild使用的；它仅为了方便。
可以包含其他功能，例如测试目标，但应从kbuild中过滤掉，以避免可能的命名冲突。
示例1：

		--> 文件名: Makefile
		ifneq ($(KERNELRELEASE),)
		# Makefile中的kbuild部分
		obj-m  := 8123.o
		8123-y := 8123_if.o 8123_pci.o 8123_bin.o

		else
		# 正常的Makefile
		KDIR ?= /lib/modules/`uname -r`/build

		default:
			$(MAKE) -C $(KDIR) M=$$PWD

		# 模块特定的目标
		genbin:
			echo "X" > 8123_bin.o_shipped

		endif

	KERNELRELEASE的检查用于分离Makefile的两个部分。在示例中，kbuild只能看到两个赋值语句，而“make”可以看到除了这两个赋值语句之外的所有内容。这是由于对文件进行了两次处理：第一次是由命令行运行的“make”实例进行的；第二次是由默认目标中的参数化“make”启动的kbuild系统。

3.2 单独的Kbuild文件和Makefile
-------------------------------------

	在较新版本的内核中，kbuild首先查找名为“Kbuild”的文件，如果找不到，则查找Makefile。使用“Kbuild”文件允许我们将示例1中的Makefile拆分为两个文件：

	示例2：

		--> 文件名: Kbuild
		obj-m  := 8123.o
		8123-y := 8123_if.o 8123_pci.o 8123_bin.o

		--> 文件名: Makefile
		KDIR ?= /lib/modules/`uname -r`/build

		default:
			$(MAKE) -C $(KDIR) M=$$PWD

		# 模块特定的目标
		genbin:
			echo "X" > 8123_bin.o_shipped

	示例2中的拆分由于每个文件的简单性而值得商榷；然而，一些外部模块使用包含几百行的Makefile，在这种情况下，将kbuild部分与其他部分分开确实很有帮助。
下一个示例展示了向后兼容的版本。
示例3：

		--> 文件名: Kbuild
		obj-m  := 8123.o
		8123-y := 8123_if.o 8123_pci.o 8123_bin.o

		--> 文件名: Makefile
		ifneq ($(KERNELRELEASE),)
		# Makefile中的kbuild部分
		include Kbuild

		else
		# 正常的Makefile
		KDIR ?= /lib/modules/`uname -r`/build

		default:
			$(MAKE) -C $(KDIR) M=$$PWD

		# 模块特定的目标
		genbin:
			echo "X" > 8123_bin.o_shipped

		endif

	在这里，“Kbuild”文件是从Makefile中包含的。这允许使用旧版本的kbuild（只知道Makefile），当“make”和kbuild部分拆分为单独文件时。
3.3 二进制 Blob 文件
--------------------

一些外部模块需要包含一个作为 Blob 的对象文件，kbuild 支持这一点，但要求 Blob 文件命名为 `<filename>_shipped`。当 kbuild 规则生效时，会创建一个 `<filename>_shipped` 的副本，并去掉 `_shipped` 后缀，这样就得到了 `<filename>`。这个缩短后的文件名可以在模块的赋值中使用。

在本节中，8123_bin.o_shipped 被用于构建内核模块 8123.ko；它被包含为 8123_bin.o：

```
8123-y := 8123_if.o 8123_pci.o 8123_bin.o
```

尽管普通源文件和二进制文件之间没有区别，但在创建模块的对象文件时，kbuild 会应用不同的规则。

3.4 构建多个模块
==================

kbuild 支持在一个构建文件中构建多个模块。例如，如果你想构建两个模块 foo.ko 和 bar.ko，kbuild 行如下所示：

```
obj-m := foo.o bar.o
foo-y := <foo_srcs>
bar-y := <bar_srcs>
```

就是这么简单！

4. 包含文件
==============

在内核中，头文件根据以下规则保存在标准位置：

- 如果头文件仅描述了模块的内部接口，则该文件放置在源文件所在的目录中。
- 如果头文件描述了一个由位于不同目录中的其他内核部分使用的接口，则该文件放置在 `include/linux/` 目录下。

注意：
- 有两个值得注意的例外：较大的子系统有自己的 `include/` 目录下的子目录，例如 `include/scsi`；特定架构的头文件位于 `arch/$(SRCARCH)/include/` 下。

4.1 内核包含
-------------------

要包含位于 `include/linux/` 下的头文件，只需使用：

```c
#include <linux/module.h>
```

kbuild 会向 `gcc` 添加选项，以便搜索相关的目录。

4.2 单个子目录
----------------------

外部模块倾向于在其源代码所在位置放置一个单独的 `include/` 目录中的头文件，尽管这不是通常的内核风格。为了告知 kbuild 这个目录，可以使用 `ccflags-y` 或 `CFLAGS_<filename>.o`。

以第 3 节中的示例为例，如果我们把 8123_if.h 移到名为 `include` 的子目录中，生成的 kbuild 文件将如下所示：

```
--> 文件名: Kbuild
obj-m := 8123.o

ccflags-y := -Iinclude
8123-y := 8123_if.o 8123_pci.o 8123_bin.o
```

请注意，在 `-I` 和路径之间没有空格。这是 kbuild 的限制：不能有空格存在。

4.3 多个子目录
------------------------

kbuild 可以处理分布在多个目录中的文件。
考虑以下示例：
```
|__ src
    |   |__ complex_main.c
    |   |__ hal
    |   |__ hardwareif.c
    |   |__ include
    |   |__ hardwareif.h
|__ include
|__ complex.h
```

为了构建模块 `complex.ko`，我们需要以下的 kbuild 文件：
```
--> 文件名: Kbuild
obj-m := complex.o
complex-y := src/complex_main.o
complex-y += src/hal/hardwareif.o

ccflags-y := -I$(src)/include
ccflags-y += -I$(src)/src/hal/include
```

如你所见，kbuild 知道如何处理位于其他目录中的目标文件。关键在于指定相对于 kbuild 文件位置的目录。但需要注意的是，这种做法并不推荐。

对于头文件，必须明确告诉 kbuild 去哪里查找。当 kbuild 执行时，当前目录始终是内核树的根目录（即 `-C` 参数所指向的位置），因此需要绝对路径。`$(src)` 提供了绝对路径，它指向当前执行的 kbuild 文件所在的目录。

5. 模块安装
===========

包含在内核中的模块将被安装到目录：

```
/lib/modules/$(KERNELRELEASE)/kernel/
```

而外部模块则被安装到：

```
/lib/modules/$(KERNELRELEASE)/updates/
```

5.1 INSTALL_MOD_PATH
--------------------

上述目录是默认安装路径，但可以进行一定程度的自定义。可以通过变量 `INSTALL_MOD_PATH` 添加一个前缀：

```
$ make INSTALL_MOD_PATH=/frodo modules_install
=> 安装目录: /frodo/lib/modules/$(KERNELRELEASE)/kernel/
```

`INSTALL_MOD_PATH` 可以作为普通 shell 变量设置，或者像上面所示，在调用 `make` 时在命令行中指定。这在安装树内和树外模块时都有效。

5.2 INSTALL_MOD_DIR
-------------------

外部模块默认安装在 `/lib/modules/$(KERNELRELEASE)/updates/` 目录下，但如果你想为特定功能的模块指定一个单独的目录，可以使用 `INSTALL_MOD_DIR` 来指定替代的目录名：

```
$ make INSTALL_MOD_DIR=gandalf -C $KDIR \
       M=$PWD modules_install
=> 安装目录: /lib/modules/$(KERNELRELEASE)/gandalf/
```

6. 模块版本控制
===============

模块版本控制由 `CONFIG_MODVERSIONS` 标签启用，并用于简单的 ABI 一致性检查。对每个导出符号的完整原型生成一个 CRC 值。当加载或使用模块时，内核中的 CRC 值会与模块中的类似值进行比较；如果它们不相等，则内核拒绝加载该模块。

`Module.symvers` 包含了内核构建过程中所有导出符号的列表。

6.1 内核中的符号（vmlinux + 模块）
-----------------------------------

在内核构建期间，将生成一个名为 `Module.symvers` 的文件。`Module.symvers` 包含了内核及其编译模块中所有的导出符号。对于每个符号，相应的 CRC 值也会被存储。

`Module.symvers` 文件的语法如下：

```
<CRC>       <Symbol>         <Module>                         <Export Type>     <Namespace>
0xe1cc2a05  usb_stor_suspend drivers/usb/storage/usb-storage  EXPORT_SYMBOL_GPL USB_STORAGE
```

字段之间由制表符分隔，值可能为空（例如，如果导出符号没有命名空间）。

对于未启用 `CONFIG_MODVERSIONS` 的内核构建，CRC 值将读作 `0x00000000`。
Module.symvers 有两个用途：

1) 列出 vmlinux 和所有模块中导出的所有符号。
2) 如果启用了 CONFIG_MODVERSIONS，列出符号的 CRC。

6.2 符号和外部模块
-------------------

在构建外部模块时，构建系统需要访问内核中的符号以检查所有外部符号是否已定义。这是在 MODPOST 步骤中完成的。modpost 通过读取内核源树中的 Module.symvers 文件来获取这些符号。在 MODPOST 步骤期间，将写入一个新的 Module.symvers 文件，其中包含该外部模块中导出的所有符号。

6.3 另一个外部模块中的符号
----------------------------

有时，一个外部模块会使用另一个外部模块中导出的符号。kbuild 需要了解所有符号以避免发出关于未定义符号的警告。在这种情况下有两种解决方案：
注意：推荐使用顶层 kbuild 文件的方法，但在某些情况下可能不实用。

使用顶层 kbuild 文件
如果有两个模块 foo.ko 和 bar.ko，其中 foo.ko 需要来自 bar.ko 的符号，可以使用一个共同的顶层 kbuild 文件以便两个模块在同一个构建过程中编译。考虑以下目录结构：

```
./foo/ <= 包含 foo.ko
./bar/ <= 包含 bar.ko
```

顶层 kbuild 文件如下所示：

```
#./Kbuild（或 ./Makefile）:
obj-m := foo/ bar/
```

执行以下命令：

```
$ make -C $KDIR M=$PWD
```

将按预期编译这两个模块，并完全了解每个模块中的符号。

使用 "make" 变量 KBUILD_EXTRA_SYMBOLS
如果添加顶层 kbuild 文件不切实际，可以在构建文件中为 KBUILD_EXTRA_SYMBOLS 分配一个空格分隔的文件列表。

这些文件将在 modpost 初始化其符号表时加载。

7. 小贴士与技巧
================

7.1 测试 CONFIG_FOO_BAR
------------------------

模块通常需要检查某些 `CONFIG_` 选项以决定是否包含特定功能。在 kbuild 中，这是通过直接引用 `CONFIG_` 变量来实现的：

```
#fs/ext2/Makefile
obj-$(CONFIG_EXT2_FS) += ext2.o

ext2-y := balloc.o bitmap.o dir.o
ext2-$(CONFIG_EXT2_FS_XATTR) += xattr.o
```

外部模块传统上使用 "grep" 直接在 .config 中检查具体的 `CONFIG_` 设置。这种用法是错误的。如前所述，外部模块应使用 kbuild 进行构建，并且在测试 `CONFIG_` 定义时可以使用与树内模块相同的方法。
