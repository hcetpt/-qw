======  
Kbuild
======

输出文件
============

modules.order
-------------
此文件记录了模块在 Makefiles 中出现的顺序。这用于让 modprobe 确定性地解析匹配多个模块的别名。
modules.builtin
---------------
此文件列出了所有内置到内核中的模块。这用于让 modprobe 在尝试加载内置模块时不会失败。
modules.builtin.modinfo
-----------------------
此文件包含所有内置到内核中的模块的 modinfo 信息。
与单独模块的 modinfo 不同，所有字段都以模块名称为前缀。

环境变量
=====================

KCPPFLAGS
---------
预处理时传递的附加选项。这些预处理选项会在 kbuild 进行预处理的所有情况下使用，包括编译 C 文件和汇编文件。
KAFLAGS
-------
附加到汇编器的选项（适用于内置模块和独立模块）。
AFLAGS_MODULE
-------------
适用于模块的附加汇编选项。
AFLAGS_KERNEL
-------------
适用于内置模块的附加汇编选项。
KCFLAGS
-------
附加到 C 编译器的选项（适用于内置模块和独立模块）。
KRUSTFLAGS
----------
附加到 Rust 编译器的选项（适用于内置模块和独立模块）。
CFLAGS_KERNEL  
--------------
当使用$(CC)编译作为内置代码的内核代码时的附加选项

CFLAGS_MODULE  
--------------
编译模块时为$(CC)使用的附加模块特定选项

RUSTFLAGS_KERNEL  
----------------
当使用$(RUSTC)编译作为内置代码的内核代码时的附加选项

RUSTFLAGS_MODULE  
----------------
编译模块时为$(RUSTC)使用的附加模块特定选项

LDFLAGS_MODULE  
---------------
链接模块时为$(LD)使用的附加选项

HOSTCFLAGS  
----------
构建主机程序时传递给$(HOSTCC)的附加标志

HOSTCXXFLAGS  
------------
构建主机程序时传递给$(HOSTCXX)的附加标志

HOSTRUSTFLAGS  
-------------
构建主机程序时传递给$(HOSTRUSTC)的附加标志

HOSTLDFLAGS  
-----------
链接主机程序时传递的附加标志

HOSTLDLIBS  
----------
构建主机程序时链接的附加库
.. _userkbuildflags:

USERCFLAGS
----------
在编译用户程序时为 $(CC) 使用的附加选项。

USERLDFLAGS
-----------
在链接用户程序时为 $(LD) 使用的附加选项。用户程序使用 CC 进行链接，因此 $(USERLDFLAGS) 应包含 "-Wl," 前缀（如果适用）。

KBUILD_KCONFIG
--------------
将顶层 Kconfig 文件设置为此环境变量的值。默认名称是 "Kconfig"。

KBUILD_VERBOSE
--------------
设置 kbuild 的详细程度。可以赋值与 "V=..." 相同的值。
详见 `make help` 获取完整列表。
设置 "V=..." 优先于 KBUILD_VERBOSE。

KBUILD_EXTMOD
-------------
设置查找内核源代码的目录，用于构建外部模块。
设置 "M=..." 优先于 KBUILD_EXTMOD。

KBUILD_OUTPUT
-------------
指定编译内核时的输出目录。
输出目录也可以使用 "O=..." 来指定。
设置 "O=..." 优先于 KBUILD_OUTPUT

KBUILD_EXTRA_WARN
-----------------
指定额外的构建检查。相同的值可以通过从命令行传递 W=... 来设置。
参见 `make help` 获取支持的值列表。
设置 "W=..." 优先于 KBUILD_EXTRA_WARN

KBUILD_DEBARCH
--------------
对于 deb-pkg 目标，允许覆盖 deb-pkg 使用的正常启发式方法。通常情况下，deb-pkg 会尝试根据 UTS_MACHINE 变量来猜测正确的架构，在某些架构上还会参考内核配置。
KBUILD_DEBARCH 的值被假定（但未检查）为有效的 Debian 架构。

KDOCFLAGS
---------
在构建过程中指定用于 kernel-doc 检查的额外（警告/错误）标志，详见 scripts/kernel-doc 中支持的标志。注意，这目前不适用于文档构建。

ARCH
----
设置 ARCH 为要构建的架构。
在大多数情况下，架构名称与 arch/ 目录中的目录名称相同。
但是某些架构如 x86 和 sparc 有别名。
### x86:
- 对于32位：i386
- 对于64位：x86_64

### parisc:
- 对于64位：parisc64

### sparc:
- 对于32位：sparc32
- 对于64位：sparc64

### CROSS_COMPILE
-----------------
指定 binutils 文件名中的可选固定部分。
CROSS_COMPILE 可以是文件名的一部分或完整路径。
在某些配置中，CROSS_COMPILE 也用于 ccache。

### CF
----
为 sparse 添加额外选项。
CF 经常像下面这样在命令行中使用：

```sh
make CF=-Wbitwise C=2
```

### INSTALL_PATH
-----------------
指定放置更新后的内核和系统映射图像的位置。默认值是 `/boot`，但可以设置为其他值。

### INSTALLKERNEL
-----------------
使用 `make install` 时调用的安装脚本。
默认名称是 `installkernel`。
该脚本将使用以下参数被调用：

- `$1` - 内核版本
- `$2` - 内核映像文件
- `$3` - 内核映射文件
- `$4` - 默认安装路径（如果为空则使用根目录）

`make install` 的实现是架构特定的，并且可能与上述不同。
提供 INSTALLKERNEL 是为了在交叉编译内核时能够指定自定义安装程序。

### MODLIB
------
指定模块的安装位置。
默认值为：

     $(INSTALL_MOD_PATH)/lib/modules/$(KERNELRELEASE)

此值可以在需要时覆盖，此时将忽略默认值。
INSTALL_MOD_PATH
----------------
INSTALL_MOD_PATH 指定了一个前缀给 MODLIB，用于构建根目录所需的模块目录重定位。此变量在 Makefile 中未定义，但如果需要，可以将其作为参数传递给 make 命令。
INSTALL_MOD_STRIP
-----------------
如果定义了 INSTALL_MOD_STRIP，则会在安装模块后进行精简（strip）。如果 INSTALL_MOD_STRIP 的值为 '1'，则使用默认选项 --strip-debug。否则，将使用 INSTALL_MOD_STRIP 的值作为 strip 命令的选项。
INSTALL_HDR_PATH
----------------
执行 "make headers_*" 时，INSTALL_HDR_PATH 指定了安装用户空间头文件的位置。
默认值为：

    $(objtree)/usr

$(objtree) 是保存输出文件的目录。输出目录通常通过命令行中的 "O=..." 设置。
此值可以在需要时覆盖，此时将忽略默认值。
INSTALL_DTBS_PATH
-----------------
INSTALL_DTBS_PATH 指定了设备树 blob 文件的安装位置，以满足构建根目录所需的重定位。此变量在 Makefile 中未定义，但如果需要，可以将其作为参数传递给 make 命令。
KBUILD_ABS_SRCTREE
--------------------------------------------------
Kbuild 尽可能使用相对路径指向源代码树。例如，在源代码树中构建时，源代码树路径为 '.'。

设置此标志请求 Kbuild 使用到源代码树的绝对路径。在某些情况下这样做是有用的，比如在生成包含绝对路径条目的标签文件时。
### KBUILD_SIGN_PIN
-----------------
此变量允许在签名内核模块时，将口令或PIN码传递给sign-file工具，如果私钥需要的话。

### KBUILD_MODPOST_WARN
---------------------
可以设置`KBUILD_MODPOST_WARN`以避免在最终模块链接阶段因未定义符号而产生的错误。它会将这些错误转换为警告。

### KBUILD_MODPOST_NOFINAL
-----------------------
可以设置`KBUILD_MODPOST_NOFINAL`以跳过模块的最终链接。这仅用于加快测试编译的速度。

### KBUILD_EXTRA_SYMBOLS
--------------------
对于使用其他模块中的符号的模块，请参阅更多详细信息见`modules.rst`文件。

### ALLSOURCE_ARCHS
---------------
对于`tags/TAGS/cscope`目标，您可以指定多个架构包含在数据库中，用空格分隔。例如：
```
$ make ALLSOURCE_ARCHS="x86 mips arm" tags
```

您也可以指定`all`来获取所有可用的架构。例如：
```
$ make ALLSOURCE_ARCHS=all tags
```

### IGNORE_DIRS
-------------
对于`tags/TAGS/cscope`目标，您可以选择哪些目录不包含在数据库中，用空格分隔。例如：
```
$ make IGNORE_DIRS="drivers/gpu/drm/radeon tools" cscope
```

### KBUILD_BUILD_TIMESTAMP
----------------------
将此变量设置为日期字符串可以覆盖在`UTS_VERSION`定义中使用的时间戳（运行内核中的`uname -v`）。该值必须是可以传递给`date -d`的字符串。默认值是构建过程中某时刻`date`命令的输出。

### KBUILD_BUILD_USER, KBUILD_BUILD_HOST
------------------------------------
这两个变量允许覆盖启动时和`/proc/version`中显示的用户@主机字符串。默认值分别是`whoami`和`hostname`命令的输出。

### LLVM
----
如果将此变量设置为1，Kbuild将使用Clang和LLVM工具代替GCC和GNU binutils来编译内核。
