======================
Linux 内核 Makefile
======================

本文档描述了 Linux 内核的 Makefile。
概述
========

Makefile 有五个部分::

   Makefile                    根 Makefile
   .config                     内核配置文件
   arch/$(SRCARCH)/Makefile    架构 Makefile
   scripts/Makefile.*          所有 kbuild Makefile 的通用规则等
   kbuild Makefile             存在于每个子目录中

根 Makefile 读取来自内核配置过程的 .config 文件。
根 Makefile 负责构建两个主要产品：vmlinux（驻留内核映像）和模块（任何模块文件）。
它通过递归进入内核源树的子目录来构建这些目标。
访问的子目录列表取决于内核配置。根 Makefile 文本包含一个名为 arch/$(SRCARCH)/Makefile 的架构 Makefile。架构 Makefile 向根 Makefile 提供架构特定的信息。
每个子目录都有一个 kbuild Makefile，执行从上面传递下来的命令。kbuild Makefile 使用 .config 文件中的信息来构造用于构建任何内置或模块化目标的文件列表。
### scripts/Makefile.* 包含所有用于基于 kbuild Makefiles 构建内核的定义、规则等。

### 各自的角色
####

人们对内核 Makefiles 有四种不同的关系：

- **用户** 是构建内核的人。这些人会输入如 `make menuconfig` 或 `make` 这样的命令。他们通常不会阅读或编辑任何内核 Makefiles（或其他源文件）。
- **普通开发者** 是从事设备驱动程序、文件系统和网络协议等特性开发的人。这些人需要维护他们所工作的子系统的 kbuild Makefiles。为了有效地做到这一点，他们需要对内核 Makefiles 有一些总体了解，并且需要详细了解 kbuild 的公共接口。
- **架构开发者** 是从事整个架构（如sparc或x86）开发的人。架构开发者需要了解架构相关的 Makefile 以及 kbuild Makefiles。
- **kbuild 开发者** 是从事内核构建系统本身开发的人。这些人需要了解内核 Makefiles 的各个方面。

本文档主要面向普通开发者和架构开发者。

### kbuild 文件
####

内核中的大多数 Makefiles 都是使用 kbuild 基础设施的 kbuild Makefiles。本章介绍了 kbuild Makefiles 中使用的语法。

对于 kbuild 文件，首选名称是 `Makefile`，但也可以使用 `Kbuild`。如果同时存在 `Makefile` 和 `Kbuild` 文件，则会使用 `Kbuild` 文件。
### 目标定义

目标定义是 kbuild Makefile 的主要部分（核心）。这些行定义了要构建的文件、任何特殊的编译选项以及需要递归进入的子目录。
最简单的 kbuild Makefile 包含一行：

示例：

```makefile
obj-y += foo.o
```

这告诉 kbuild 在该目录中有一个名为 `foo.o` 的对象文件。`foo.o` 将从 `foo.c` 或 `foo.S` 构建。
如果 `foo.o` 需要作为模块构建，则使用变量 `obj-m`。
因此，以下模式经常被使用：

示例：

```makefile
obj-$(CONFIG_FOO) += foo.o
```

`$(CONFIG_FOO)` 可以评估为 `y`（内置）或 `m`（模块）。
如果 `CONFIG_FOO` 既不是 `y` 也不是 `m`，则该文件将不会被编译也不会被链接。

### 内置对象目标 - `obj-y`

kbuild Makefile 在 `$(obj-y)` 列表中指定了用于 vmlinux 的对象文件。这些列表依赖于内核配置。
kbuild 编译所有 `$(obj-y)` 文件。然后调用 `$(AR) rcSTP` 将这些文件合并到一个 `built-in.a` 文件中。
这是一个没有符号表的薄档案。它将在稍后由 `scripts/link-vmlinux.sh` 脚本链接到 `vmlinux` 中。

`$(obj-y)` 列表中的文件顺序很重要。允许列表中有重复项：第一个实例将被链接到 `built-in.a` 中，后续的实例将被忽略。
链接顺序非常重要，因为某些函数（如 `module_init()` / `__initcall`）会在启动过程中按照它们出现的顺序被调用。因此，请记住，更改链接顺序可能会改变SCSI控制器的检测顺序，从而导致磁盘重新编号。例如：

```plaintext
# drivers/isdn/i4l/Makefile
# 内核ISDN子系统和设备驱动程序的Makefile
# 每个配置选项会启用一个文件列表
obj-$(CONFIG_ISDN_I4L) += isdn.o
obj-$(CONFIG_ISDN_PPP_BSDCOMP) += isdn_bsdcomp.o
```

可加载模块目标 - obj-m
------------------------

`$(obj-m)` 指定作为可加载内核模块构建的目标对象文件。
一个模块可以从一个源文件或多个源文件构建。在只有一个源文件的情况下，kbuild Makefile 简单地将该文件添加到 `$(obj-m)` 中。

例如：
```plaintext
# drivers/isdn/i4l/Makefile
obj-$(CONFIG_ISDN_PPP_BSDCOMP) += isdn_bsdcomp.o
```

注意：在这个例子中，`$(CONFIG_ISDN_PPP_BSDCOMP)` 的值为 "m"。

如果一个内核模块是从多个源文件构建的，你需要像上面那样指定要构建一个模块；但是，kbuild 需要知道你希望从哪些对象文件来构建你的模块，所以你需要通过设置 `$(<module_name>-y)` 变量来告诉它。

例如：
```plaintext
# drivers/isdn/i4l/Makefile
obj-$(CONFIG_ISDN_I4L) += isdn.o
isdn-y := isdn_net_lib.o isdn_v110.o isdn_common.o
```

在这个例子中，模块名称将是 `isdn.o`。kbuild 将编译 `$(isdn-y)` 列表中的对象文件，并运行 `$(LD) -r` 来生成 `isdn.o`。

由于 kbuild 能够识别 `$(<module_name>-y)` 用于复合对象，你可以使用 `CONFIG_` 符号的值来有条件地包含一个对象文件作为复合对象的一部分。

例如：
```plaintext
# fs/ext2/Makefile
obj-$(CONFIG_EXT2_FS) += ext2.o
ext2-y := balloc.o dir.o file.o ialloc.o inode.o ioctl.o \
  namei.o super.o symlink.o
ext2-$(CONFIG_EXT2_FS_XATTR) += xattr.o xattr_user.o \
  xattr_trusted.o
```

在这个例子中，只有当 `$(CONFIG_EXT2_FS_XATTR)` 的值为 "y" 时，`xattr.o`、`xattr_user.o` 和 `xattr_trusted.o` 才会成为复合对象 `ext2.o` 的一部分。

注意：当然，在将对象编入内核时，上述语法同样适用。因此，如果你有 `CONFIG_EXT2_FS=y`，kbuild 会为你从各个部分构建一个 `ext2.o` 文件，然后将其链接到 `built-in.a` 中，正如你所期望的那样。
库文件目标 - lib-y
--------------------------

使用 obj-* 列出的对象用于模块，或者在特定目录下的 built-in.a 中组合。
还有可能列出将包含在库 lib.a 中的对象。
所有用 lib-y 列出的对象都会在一个单一的库中为该目录组合。
如果某个对象同时列在 obj-y 和 lib-y 中，则不会将其包含在库中，因为这些对象无论如何都是可访问的。
为了保持一致性，列出在 lib-m 中的对象将会被包含在 lib.a 中。
需要注意的是，同一个 kbuild Makefile 可能会列出需要构建为内建模块和库的一部分的文件。因此，同一个目录可以包含一个 built-in.a 文件和一个 lib.a 文件。
示例：

  # arch/x86/lib/Makefile
  lib-y    := delay.o

这将基于 delay.o 创建一个库 lib.a。为了让 kbuild 识别正在构建 lib.a，该目录应当被列入 libs-y 中。
参见 `递归时要访问的目录列表`_。
lib-y 的使用通常限制在 ``lib/`` 和 ``arch/*/lib`` 目录中。
递归进入子目录
------------------------------

一个 Makefile 只负责构建其所在目录中的对象。子目录中的文件应该由这些子目录中的 Makefile 来处理。构建系统会自动递归地在子目录中调用 make，前提是你让它知道这些子目录的存在。
为此，使用 `obj-y` 和 `obj-m`。
`ext2` 位于一个单独的目录中，`fs/` 目录中的 `Makefile` 通过以下赋值告诉 Kbuild 进入该目录。
示例：

  # fs/Makefile
  obj-$(CONFIG_EXT2_FS) += ext2/

如果 `CONFIG_EXT2_FS` 被设置为 "y"（内置）或 "m"（模块化），相应的 `obj-` 变量将被设置，并且 Kbuild 将进入 `ext2` 目录。
Kbuild 不仅使用这些信息来决定是否需要访问该目录，还决定是否将该目录中的对象链接到 `vmlinux` 中。
当 Kbuild 以 "y" 方式进入目录时，该目录中的所有内置对象将被合并到 `built-in.a` 文件中，最终链接到 `vmlinux`。
而当 Kbuild 以 "m" 方式进入目录时，该目录中的任何内容都不会被链接到 `vmlinux`。如果该目录中的 `Makefile` 指定了 `obj-y`，那些对象将被遗弃。
这很可能是 `Makefile` 或 `Kconfig` 中依赖项的一个错误。
Kbuild 还支持专用语法 `subdir-y` 和 `subdir-m` 来进入子目录。当你知道这些子目录根本不包含内核空间的对象时，这种做法非常合适。典型的用法是让 Kbuild 进入子目录来构建工具。
示例：

  # scripts/Makefile
  subdir-$(CONFIG_GCC_PLUGINS) += gcc-plugins
  subdir-$(CONFIG_MODVERSIONS) += genksyms
  subdir-$(CONFIG_SECURITY_SELINUX) += selinux

与 `obj-y/m` 不同，`subdir-y/m` 不需要尾随的斜杠，因为这种语法总是用于目录。
在分配目录名时使用 `CONFIG_` 变量是一个好习惯。这样，如果对应的 `CONFIG_` 选项既不是 "y" 也不是 "m"，Kbuild 可以完全跳过该目录。
非内置的 vmlinux 目标 - extra-y
-------------------------------------

`extra-y` 指定的是构建 `vmlinux` 所需的目标，但这些目标不会被合并到 `built-in.a` 中。
示例包括：

1) `vmlinux` 的链接脚本

`vmlinux` 的链接脚本位于 `arch/$(SRCARCH)/kernel/vmlinux.lds`

示例::

  # arch/x86/kernel/Makefile
  extra-y += vmlinux.lds

`$(extra-y)` 应该只包含 `vmlinux` 所需的目标。当显然 `vmlinux` 不是最终目标时（例如 `make modules` 或构建外部模块），Kbuild 会跳过 `extra-y`。

如果你希望无条件地构建某些目标，请使用 `always-y`（在下一节中解释）作为正确的语法。

始终构建的目标 - always-y
-----------------------------

`always-y` 指定的目标是在 Kbuild 访问 Makefile 时始终会被构建的。
示例::

  # ./Kbuild
  offsets-file := include/generated/asm-offsets.h
  always-y += $(offsets-file)

编译标志
-----------------

`ccflags-y`, `asflags-y` 和 `ldflags-y`
  这三个标志仅适用于它们被分配的 Kbuild Makefile。它们用于递归构建过程中所有正常的 cc、as 和 ld 调用。
注意：以前具有相同行为的标志名为：
  `EXTRA_CFLAGS`, `EXTRA_AFLAGS` 和 `EXTRA_LDFLAGS`
它们仍然受支持，但其使用已被弃用。
`ccflags-y` 指定了使用 $(CC) 编译时的选项。
示例::

    # drivers/acpi/acpica/Makefile
    ccflags-y := -Os -D_LINUX -DBUILDING_ACPICA
    ccflags-$(CONFIG_ACPI_DEBUG) += -DACPI_DEBUG_OUTPUT

此变量是必要的，因为顶层 Makefile 拥有变量 $(KBUILD_CFLAGS)，并将其用于整个树的编译标志。
`asflags-y` 指定汇编器选项。
例如：

    # arch/sparc/kernel/Makefile
    asflags-y := -ansi

`ldflags-y` 指定与 $(LD) 链接时的选项。
例如：

    # arch/cris/boot/compressed/Makefile
    ldflags-y += -T $(src)/decompress_$(arch-y).lds

`subdir-ccflags-y`, `subdir-asflags-y`
  上述两个标志类似于 `ccflags-y` 和 `asflags-y`。
不同之处在于，带有 `subdir-` 前缀的标志对其所在 KBuild 文件及其所有子目录有效。
使用 `subdir-*` 指定的选项会在使用非 `subdir` 变体指定的选项之前添加到命令行中。
例如：

    subdir-ccflags-y := -Werror

`ccflags-remove-y`, `asflags-remove-y`
  这些标志用于移除特定的编译器和汇编器调用中的标志。
例如：

    ccflags-remove-$(CONFIG_MCOUNT) += -pg

`CFLAGS_$@`, `AFLAGS_$@`
  `CFLAGS_$@` 和 `AFLAGS_$@` 仅适用于当前 KBuild Makefile 中的命令。
`$(CFLAGS_$@)` 为 $(CC) 指定每个文件的选项。$@ 部分具有一个字面值，该值指定了它所对应的文件。
`CFLAGS_$@` 的优先级高于 `ccflags-remove-y`；`CFLAGS_$@` 可以重新添加由 `ccflags-remove-y` 移除的编译器标志。
例如：

    # drivers/scsi/Makefile
    CFLAGS_aha152x.o = -DAHA152X_STAT -DAUTOCONF

  这一行指定了 aha152x.o 的编译标志。
$(AFLAGS_$@) 是针对汇编语言源文件的类似特性  
`AFLAGS_$@` 的优先级高于 `asflags-remove-y`；`AFLAGS_$@` 可以重新添加被 `asflags-remove-y` 移除的汇编器标志  
示例：

    # arch/arm/kernel/Makefile
    AFLAGS_head.o        := -DTEXT_OFFSET=$(TEXT_OFFSET)
    AFLAGS_crunch-bits.o := -Wa,-mcpu=ep9312
    AFLAGS_iwmmxt.o      := -Wa,-mcpu=iwmmxt

依赖跟踪
--------

Kbuild 跟踪以下依赖项：

1) 所有前置文件（包括 ``*.c`` 和 ``*.h``）
2) 在所有前置文件中使用的 ``CONFIG_`` 选项
3) 用于编译目标的命令行

因此，如果你修改了 $(CC) 的某个选项，所有受影响的文件都将被重新编译

自定义规则
------------

当 Kbuild 架构不提供所需支持时，可以使用自定义规则。一个典型的例子是在构建过程中生成的头文件  
另一个例子是需要自定义规则来准备引导映像等架构特定的 Makefile  
自定义规则以常规 Make 规则的形式编写  
Kbuild 不在 Makefile 所在目录执行，所以所有的自定义规则都应使用相对于前置文件和目标文件的路径  
定义自定义规则时会用到两个变量：

$(src)
  $(src) 是 Makefile 所在的目录。引用源树中的文件时始终使用 $(src)
$(obj)
  $(obj) 是保存目标文件的目录。引用生成文件时始终使用 $(obj)。对于需要同时适用于生成文件和实际源文件的模式规则，也应使用 $(obj)（VPATH 将帮助查找不仅在对象树中还在源树中的前置文件）
示例：

    #drivers/scsi/Makefile
    $(obj)/53c8xx_d.h: $(src)/53c7,8xx.scr $(src)/script_asm.pl
    $(CPP) -DCHIP=810 - < $< | ... $(src)/script_asm.pl

  这是一个遵循 make 所需标准语法的自定义规则
目标文件依赖于两个先决条件文件。对目标文件的引用以 `$(obj)` 开头，对先决条件文件的引用使用 `$(src)`（因为它们不是生成文件）。

$(kecho)
在规则中向用户显示信息通常是一个好习惯，但在执行 `make -s` 时，不希望看到任何输出，除非是警告或错误。
为了支持这一点，kbuild 定义了 $(kecho)，它会将紧跟在 $(kecho) 后面的文本输出到标准输出，除非使用了 `make -s`。

示例：

```makefile
# arch/arm/Makefile
$(BOOT_TARGETS): vmlinux
        $(Q)$(MAKE) $(build)=$(boot) MACHINE=$(MACHINE) $(boot)/$@
        @$(kecho) '  Kernel: $(boot)/$@ is ready'
```

当 kbuild 在未设置 KBUILD_VERBOSE 的情况下执行时，默认只显示命令的简写形式。
为了使自定义命令启用这种行为，kbuild 要求设置两个变量：

- `quiet_cmd_<command>` - 需要显示的内容
- `cmd_<command>` - 要执行的命令

示例：

```makefile
# lib/Makefile
quiet_cmd_crc32 = GEN     $@
cmd_crc32 = $< > $@

$(obj)/crc32table.h: $(obj)/gen_crc32table
        $(call cmd,crc32)
```

在更新 $(obj)/crc32table.h 目标时，会显示以下行：

```shell
GEN     lib/crc32table.h
```

通过执行 `make KBUILD_VERBOSE=` 可以看到这条信息。

命令变更检测
------------------------

在评估规则时，会比较目标文件和其先决条件文件的时间戳。GNU Make 当任何先决条件比目标文件更新时更新目标文件。
当命令行自上次调用以来发生变化时，也应重建目标文件。这本身不受 Make 支持，因此 kbuild 通过一种元编程方式实现了这一点。
用于此目的的宏是 `if_changed`，其形式如下：

```makefile
quiet_cmd_<command> = ..
cmd_<command> = ..
<target>: <source(s)> FORCE
        $(call if_changed,<command>)
```

任何使用 `if_changed` 的目标都必须列在 $(targets) 中，否则命令行检查会失败，并且目标文件将始终被构建。
如果目标已经在识别的语法中列出，如 obj-y/m、lib-y/m、extra-y/m、always-y/m、hostprogs、userprogs 或 Kbuild，Kbuild 会自动将其添加到 $(targets)。否则，必须显式地将目标添加到 $(targets)。

对 $(targets) 的赋值不包含 $(obj)/ 前缀。可以结合使用 `if_changed` 和自定义规则，具体定义见“自定义规则”部分。

注意：常见的错误是忘记添加 FORCE 先决条件。

另一个常见的陷阱是有时空格很重要；例如，下面的代码会失败（请注意逗号后面的多余空格）：

```plaintext
target: source(s) FORCE

**WRONG!**	$(call if_changed, objcopy)
```

注意：
  每个目标不应使用多于一次的 `if_changed`。
  它将执行的命令存储在对应的 .cmd 文件中，多次调用会导致覆盖，并且当目标是最新的但只有更改的命令触发命令执行时，可能会导致意外的结果。

$(CC) 支持函数
-----------------------

内核可以使用多个不同版本的 $(CC) 编译，每个版本支持一组独特的特性和选项。
Kbuild 提供了基本的支持来检查 $(CC) 的有效选项。
$(CC) 通常是 gcc 编译器，但也支持其他替代方案。

as-option
  `as-option` 用于检查 $(CC) 在编译汇编文件（``*.S``）时是否支持给定的选项。如果第一个选项不被支持，可以指定一个可选的第二个选项。
示例：

```plaintext
# arch/sh/Makefile
cflags-y += $(call as-option,-Wa$(comma)-isa=$(isa-y),)
```

在上面的例子中，如果 $(CC) 支持该选项，则 cflags-y 将被赋值为 `-Wa$(comma)-isa=$(isa-y)`。
第二个参数是可选的，如果提供，则在第一个参数不被支持时使用。

`as-instr`
`as-instr` 检查汇编器是否报告了特定指令，并根据结果输出 `option1` 或 `option2`。
测试指令支持 C 转义字符。
注意：`as-instr-option` 使用 `KBUILD_AFLAGS` 来设置汇编器选项。

`cc-option`
`cc-option` 用于检查编译器 `$(CC)` 是否支持给定的选项，如果不支持，则使用可选的第二个选项。
示例：

```makefile
# arch/x86/Makefile
cflags-y += $(call cc-option, -march=pentium-mmx, -march=i586)
```

在上述示例中，如果 `$(CC)` 支持 `-march=pentium-mmx` 选项，那么 `cflags-y` 将被赋值为 `-march=pentium-mmx`；否则赋值为 `-march=i586`。
`cc-option` 的第二个参数是可选的，如果没有提供，则当第一个选项不被支持时，`cflags-y` 将被赋值为空。
注意：`cc-option` 使用 `KBUILD_CFLAGS` 来设置 `$(CC)` 的选项。

`cc-option-yn`
`cc-option-yn` 用于检查 `gcc` 是否支持给定的选项，并在支持时返回 "y"，否则返回 "n"。
示例：

```makefile
# arch/ppc/Makefile
biarch := $(call cc-option-yn, -m32)
aflags-$(biarch) += -a32
cflags-$(biarch) += -m32
```

在上述示例中，如果 `$(CC)` 支持 `-m32` 选项，则 `$(biarch)` 被设为 "y"。当 `$(biarch)` 等于 "y" 时，扩展变量 `$(aflags-y)` 和 `$(cflags-y)` 分别被赋值为 `-a32` 和 `-m32`。
注意：`cc-option-yn` 使用 `KBUILD_CFLAGS` 来设置 `$(CC)` 的选项。

`cc-disable-warning`
`cc-disable-warning` 检查 `gcc` 是否支持给定的警告，并返回禁用该警告的命令行开关。这个特殊函数是必需的，因为从 `gcc 4.4` 及更高版本开始，任何未知的 `-Wno-*` 选项都会被接受，只有当源文件中有其他警告时才会发出警告。
示例：

```makefile
KBUILD_CFLAGS += $(call cc-disable-warning, unused-but-set-variable)
```

在上述示例中，如果 `gcc` 真正支持 `-Wno-unused-but-set-variable`，则将其添加到 `KBUILD_CFLAGS` 中。

`gcc-min-version`
`gcc-min-version` 检查 `$(CONFIG_GCC_VERSION)` 的值是否大于或等于提供的值，并在满足条件时返回 "y"。
示例：

```makefile
cflags-$(call gcc-min-version, 70100) := -foo
```

在上述示例中，如果 `$(CC)` 是 `gcc` 并且 `$(CONFIG_GCC_VERSION)` 大于或等于 `7.1`，那么 `cflags-y` 将被赋值为 `-foo`。
### clang-min-version
`clang-min-version` 用于检查 `$(CONFIG_CLANG_VERSION)` 的值是否大于或等于提供的值。如果满足条件，则结果为 `y`。

**示例：**

```makefile
cflags-$(call clang-min-version, 110000) := -foo
```

在这个示例中，如果 `$(CC)` 是 `clang` 并且 `$(CONFIG_CLANG_VERSION)` 大于或等于 11.0.0，则 `cflags-y` 将被赋值 `-foo`。

### cc-cross-prefix
`cc-cross-prefix` 用于检查路径中是否存在带有指定前缀的 `$(CC)`。如果有多个前缀，将返回第一个存在 `prefix$(CC)` 的前缀；如果没有找到任何 `prefix$(CC)`，则不返回任何内容。

额外的前缀在调用 `cc-cross-prefix` 时通过单个空格分隔。

此功能对于尝试设置 `CROSS_COMPILE` 的架构 Makefile 非常有用，因为它们可能有多个值可供选择。

建议仅在交叉编译（主机架构与目标架构不同）时尝试设置 `CROSS_COMPILE`。如果 `CROSS_COMPILE` 已经设置，则保留其旧值。

**示例：**

```makefile
# arch/m68k/Makefile
ifneq ($(SUBARCH),$(ARCH))
        ifeq ($(CROSS_COMPILE),)
                CROSS_COMPILE := $(call cc-cross-prefix, m68k-linux-gnu-)
        endif
endif
```

### $(LD) 支持函数
#### ld-option
`ld-option` 用于检查 `$(LD)` 是否支持提供的选项。它接受两个参数作为输入，第二个参数是可选的，当第一个选项不受支持时可以使用。

**示例：**

```makefile
# Makefile
LDFLAGS_vmlinux += $(call ld-option, -X)
```

### 脚本调用
Make 规则可以调用脚本来构建内核。规则应当始终提供适当的解释器来执行脚本，不应依赖于脚本的执行权限，并且不应直接调用脚本。

为了方便手动调用脚本（如调用 `./scripts/checkpatch.pl`），建议仍然设置脚本的执行权限。
Kbuild 提供了变量 $(CONFIG_SHELL)，$(AWK)，$(PERL)，和 $(PYTHON3)，用于引用各自脚本的解释器。
示例：

  # Makefile
  cmd_depmod = $(CONFIG_SHELL) $(srctree)/scripts/depmod.sh $(DEPMOD) \
          $(KERNELRELEASE)

主机程序支持
=============

Kbuild 支持在编译阶段构建主机上的可执行文件以供使用。
为了使用主机可执行文件，需要两个步骤：
第一步是告诉 Kbuild 存在一个主机程序。这通过使用变量 `hostprogs` 来完成。
第二步是为该可执行文件添加一个显式依赖项。
这可以通过两种方式实现：在规则中添加依赖项，或者使用变量 `always-y`。
以下将分别介绍这两种可能性。

简单的主机程序
-------------------

在某些情况下，需要在构建运行的计算机上编译并运行一个程序。
以下行告诉 Kbuild 程序 bin2hex 应当在构建主机上进行构建。
示例：

  hostprogs := bin2hex

在上述示例中，Kbuild 假定 bin2hex 是由位于与 Makefile 相同目录下的名为 bin2hex.c 的单个 C 源文件构成的。
复合主机程序
-----------------------

主机程序可以基于复合对象构建。
用于定义主机程序复合对象的语法与内核对象的语法类似。
`$(<executable>-objs)` 列出了用于链接最终可执行文件的所有对象。
示例：

  ```
  # scripts/lxdialog/Makefile
  hostprogs     := lxdialog
  lxdialog-objs := checklist.o lxdialog.o
  ```

带有 `.o` 扩展名的对象是从相应的 `.c` 文件编译而来的。在上述示例中，`checklist.c` 被编译为 `checklist.o`，`lxdialog.c` 被编译为 `lxdialog.o`。
最后，这两个 `.o` 文件被链接到可执行文件 `lxdialog`。
注意：对于主机程序，不允许使用 `<executable>-y` 的语法。

使用 C++ 编写主机程序
---------------------------

Kbuild 支持用 C++ 编写的主机程序。这最初是为了支持 kconfig 而引入的，并不推荐在一般情况下使用。
示例：

  ```
  # scripts/kconfig/Makefile
  hostprogs     := qconf
  qconf-cxxobjs := qconf.o
  ```

在上面的示例中，可执行文件由 C++ 文件 `qconf.cc` 组成 —— 这是由 `$(qconf-cxxobjs)` 标识的。
如果 `qconf` 包含了 `.c` 和 `.cc` 文件的混合体，则可以使用额外的一行来标识这一点。
示例：

  ```
  # scripts/kconfig/Makefile
  hostprogs     := qconf
  qconf-cxxobjs := qconf.o
  qconf-objs    := check.o
  ```

使用 Rust 编写主机程序
----------------------------

Kbuild 支持用 Rust 编写的主机程序。然而，由于 Rust 工具链不是内核编译的必需项，因此只能在需要 Rust 可用的情况下使用（例如当启用 `CONFIG_RUST` 时）。
示例：

``` 
hostprogs     := target
target-rust   := y
```

Kbuild 将使用位于与 `Makefile` 相同目录下的 `target.rs` 作为 crate 根来编译 `target`。该 crate 可以包含多个源文件（参见 `samples/rust/hostprogs`）。

控制主机程序的编译选项
------------------------------

在编译主机程序时，可以设置特定的标志。这些程序将始终使用 $(HOSTCC) 编译，并传递在 $(KBUILD_HOSTCFLAGS) 中指定的选项。
为了设置对在该 `Makefile` 中创建的所有主机程序生效的标志，可以使用变量 `HOST_EXTRACFLAGS`。
示例：

``` 
# scripts/lxdialog/Makefile
HOST_EXTRACFLAGS += -I/usr/include/ncurses
```

为了为单个文件设置特定的标志，可以使用以下结构：

示例：

``` 
# arch/ppc64/boot/Makefile
HOSTCFLAGS_piggyback.o := -DKERNELBASE=$(KERNELBASE)
```

还可以为链接器指定额外的选项：

示例：

``` 
# scripts/kconfig/Makefile
HOSTLDLIBS_qconf := -L$(QTDIR)/lib
```

在链接 `qconf` 时，将传递额外的选项 `-L$(QTDIR)/lib`。

当实际构建主机程序时
-----------------------------------

Kbuild 仅在主机程序被引用为先决条件时才会构建它们。
这可以通过两种方式实现：

(1) 在自定义规则中显式列出先决条件
示例：

``` 
# drivers/pci/Makefile
hostprogs := gen-devlist
$(obj)/devlist.h: $(src)/pci.ids $(obj)/gen-devlist
(cd $(obj); ./gen-devlist) < $<
```

目标 $(obj)/devlist.h 在 $(obj)/gen-devlist 被更新之前不会被构建。请注意，在自定义规则中引用主机程序时必须加上 $(obj) 前缀。

(2) 使用 always-y

如果没有合适的自定义规则，并且希望在进入 `Makefile` 时构建主机程序，则应使用 `always-y` 变量。
用户空间程序支持
==================

就像宿主程序一样，Kbuild 也支持为目标架构构建用户空间可执行文件（即与构建内核相同的架构）。
语法非常相似。不同之处在于使用 `userprogs` 而不是 `hostprogs`。

简单用户空间程序
------------------

以下行告诉 Kbuild 程序 `bpf-direct` 应当为目标架构构建。
示例::

  userprogs := bpf-direct

在上述示例中，Kbuild 假定 `bpf-direct` 是由位于与 Makefile 相同目录下的名为 `bpf-direct.c` 的单个 C 源文件构成的。

复合用户空间程序
-------------------

用户空间程序可以基于复合对象构建。
定义用户空间程序的复合对象的语法类似于用于内核对象的语法。
`$(<executable>-objs)` 列出了用于链接最终可执行文件的所有对象。
示例::

  #samples/seccomp/Makefile
  userprogs := bpf-fancy
  bpf-fancy-objs := bpf-fancy.o bpf-helper.o

扩展名为 `.o` 的对象是从相应的 `.c` 文件编译而来的。在上述示例中，`bpf-fancy.c` 被编译为 `bpf-fancy.o`，`bpf-helper.c` 被编译为 `bpf-helper.o`。
最后，这两个 `.o` 文件被链接到可执行文件 `bpf-fancy`。
注释：语法 `<executable>-y` 不允许用于用户空间程序
控制用户空间程序的编译选项
---------------------------------------------------

在编译用户空间程序时，可以设置特定的标志。
这些程序将始终使用传递给 $(CC) 的 $(KBUILD_USERCFLAGS) 中指定的选项进行编译。
为了设置对在该 Makefile 中创建的所有用户空间程序生效的标志，请使用变量 `userccflags`。
示例::

  # samples/seccomp/Makefile
  userccflags += -I usr/include

为了为单个文件设置特定的标志，可以使用以下结构：

示例::

  bpf-helper-userccflags += -I user/include

还可以为链接器指定附加选项。

示例::

  # net/bpfilter/Makefile
  bpfilter_umh-userldflags += -static

为了指定与用户空间程序链接的库，可以使用 ``<executable>-userldlibs``。`userldlibs` 语法指定了与当前 Makefile 中创建的所有用户空间程序链接的库。
当链接 bpfilter_umh 时，会传递额外的选项 `-static`。
从命令行，也会使用 :ref:`USERCFLAGS 和 USERLDFLAGS <userkbuildflags>`。
实际构建用户空间程序时
------------------------------------------

Kbuild 只有在被明确告知时才会构建用户空间程序。
有两种方法可以做到这一点。
(1) 将其作为另一个文件的先决条件

    示例::

      #net/bpfilter/Makefile
      userprogs := bpfilter_umh
      $(obj)/bpfilter_umh_blob.o: $(obj)/bpfilter_umh

    在构建 $(obj)/bpfilter_umh_blob.o 之前，需要先构建 $(obj)/bpfilter_umh。

(2) 使用 always-y

    示例::

      userprogs := binderfs_example
      always-y := $(userprogs)

    Kbuild 提供了以下简写形式::

      userprogs-always-y := binderfs_example

    这会告诉 Kbuild 在处理此 Makefile 时构建 binderfs_example。

Kbuild 清理基础设施
===========================

``make clean`` 会删除编译内核时 obj 树中的大多数生成文件。这包括主机程序等生成文件。Kbuild 知道在 $(hostprogs)、$(always-y)、$(always-m)、$(always-)、$(extra-y)、$(extra-) 和 $(targets) 中列出的目标。它们都会在执行 ``make clean`` 时被删除。当执行 ``make clean`` 时，整个内核源代码树中匹配模式 ``*.[oas]``、``*.ko`` 的文件以及一些由 kbuild 生成的其他文件也会被删除。

可以通过使用 $(clean-files) 在 Kbuild 的 Makefile 中指定要删除的额外文件或目录。
示例::

  #lib/Makefile
  clean-files := crc32table.h

  当执行 ``make clean`` 时，文件 ``crc32table.h`` 会被删除。

Kbuild 假定文件位于与 Makefile 相同的相对目录中。
为了将某些文件或目录排除在 ``make clean`` 外，可以使用 $(no-clean-files) 变量。
通常情况下，kbuild 会通过 ``obj-* := dir/`` 递归进入子目录，但在架构 Makefile 中，如果 kbuild 架构不够充分，有时需要显式指定。
示例::

  #arch/x86/boot/Makefile
  subdir- := compressed

  上述赋值指示 kbuild 在执行 ``make clean`` 时进入 compressed/ 目录。

注意：arch/$(SRCARCH)/Makefile 不能使用 ``subdir-``，因为该文件是在顶层 Makefile 中包含的。相反，arch/$(SRCARCH)/Kbuild 可以使用 ``subdir-``。
注释2：在执行 `make clean` 时，会访问 core-y、libs-y、drivers-y 和 net-y 中列出的所有目录。

架构 Makefile
=============

顶层 Makefile 设置环境并进行准备，然后开始递归进入各个子目录。顶层 Makefile 包含通用部分，而 arch/$(SRCARCH)/Makefile 包含设置 kbuild 所需的部分。

为了做到这一点，arch/$(SRCARCH)/Makefile 设置了若干变量并定义了一些目标。当 kbuild 执行时，大致遵循以下步骤：

1) 配置内核 => 生成 .config 文件

2) 将内核版本存储在 include/linux/version.h 中

3) 更新目标 prepare 的所有其他先决条件：
   - 额外的先决条件在 arch/$(SRCARCH)/Makefile 中指定

4) 递归进入 init-*、core-*、drivers-*、net-* 和 libs-* 列出的所有目录，并构建所有目标
   - 上述变量的值在 arch/$(SRCARCH)/Makefile 中扩展

5) 然后链接所有对象文件，并将结果文件 vmlinux 放在 obj 树的根目录下
   - 最初链接的对象列表在 scripts/head-object-list.txt 中给出

6) 最后，架构特定的部分执行任何所需的后处理，并构建最终的启动映像
   - 这包括构建引导记录
   - 准备 initrd 映像等

设置变量以根据架构调整构建
-------------------------------

KBUILD_LDFLAGS
  通用 $(LD) 选项

  用于所有链接器调用的标志
通常指定仿真就足够了。
示例：

    #arch/s390/Makefile
    KBUILD_LDFLAGS         := -m elf_s390

  注意：可以使用ldflags-y进一步定制所使用的标志。详见`非内置vmlinux目标 - extra-y`_

LDFLAGS_vmlinux
  链接vmlinux时传递给$(LD)的选项

  LDFLAGS_vmlinux用于指定链接最终vmlinux镜像时传递给链接器的附加标志
LDFLAGS_vmlinux使用LDFLAGS_$@支持
示例：

    #arch/x86/Makefile
    LDFLAGS_vmlinux := -e stext

OBJCOPYFLAGS
  objcopy标志

  当使用$(call if_changed,objcopy)转换.o文件时，将使用OBJCOPYFLAGS中指定的标志
$(call if_changed,objcopy)常用于生成vmlinux的原始二进制文件
示例：

    #arch/s390/Makefile
    OBJCOPYFLAGS := -O binary

    #arch/s390/boot/Makefile
    $(obj)/image: vmlinux FORCE
            $(call if_changed,objcopy)

  在这个示例中，二进制文件$(obj)/image是vmlinux的二进制版本。$(call if_changed,xxx)的用法将在后面介绍

KBUILD_AFLAGS
  汇编器标志

  默认值 - 参见顶层Makefile
根据需要追加或修改
示例：

    #arch/sparc64/Makefile
    KBUILD_AFLAGS += -m64 -mcpu=ultrasparc

KBUILD_CFLAGS
  $(CC) 编译器标志

  默认值 - 参见顶层Makefile
根据架构需求追加或修改
通常，KBUILD_CFLAGS 变量依赖于配置
示例：

    # arch/x86/boot/compressed/Makefile
    cflags-$(CONFIG_X86_32) := -march=i386
    cflags-$(CONFIG_X86_64) := -mcmodel=small
    KBUILD_CFLAGS += $(cflags-y)

许多架构的 Makefile 动态运行目标 C 编译器来探测支持的选项：

    # arch/x86/Makefile

    ..
    cflags-$(CONFIG_MPENTIUMII)     += $(call cc-option, \-march=pentium2,-march=i686)
    ..
    # 禁用单元一次模式 ..
    KBUILD_CFLAGS += $(call cc-option,-fno-unit-at-a-time)
    ..

第一个示例利用了配置选项在被选中时展开为 "y" 的技巧
KBUILD_RUSTFLAGS
  $(RUSTC) 编译器标志

  默认值 - 请参见顶层 Makefile
根据架构需求追加或修改
通常，KBUILD_RUSTFLAGS 变量依赖于配置
请注意，目标规范文件生成（用于 `--target`）在 `scripts/generate_rust_target.rs` 中处理。

KBUILD_AFLAGS_KERNEL  
内置内核的汇编器选项

$(KBUILD_AFLAGS_KERNEL) 包含用于编译常驻内核代码的额外 C 编译器标志。

KBUILD_AFLAGS_MODULE  
模块专用的汇编器选项

$(KBUILD_AFLAGS_MODULE) 用于添加架构特定的选项，这些选项用于汇编器。从命令行应当使用 AFLAGS_MODULE（参见 kbuild.rst）。

KBUILD_CFLAGS_KERNEL  
内置内核的 $(CC) 选项

$(KBUILD_CFLAGS_KERNEL) 包含用于编译常驻内核代码的额外 C 编译器标志。

KBUILD_CFLAGS_MODULE  
构建模块时 $(CC) 的选项

$(KBUILD_CFLAGS_MODULE) 用于添加架构特定的选项，这些选项用于 $(CC)。从命令行应当使用 CFLAGS_MODULE（参见 kbuild.rst）。

KBUILD_RUSTFLAGS_KERNEL  
内置内核的 $(RUSTC) 选项

$(KBUILD_RUSTFLAGS_KERNEL) 包含用于编译常驻内核代码的额外 Rust 编译器标志。

KBUILD_RUSTFLAGS_MODULE  
构建模块时 $(RUSTC) 的选项

$(KBUILD_RUSTFLAGS_MODULE) 用于添加架构特定的选项，这些选项用于 $(RUSTC)。从命令行应当使用 RUSTFLAGS_MODULE（参见 kbuild.rst）。
KBUILD_LDFLAGS_MODULE  
链接模块时 $(LD) 的选项

$(KBUILD_LDFLAGS_MODULE) 用于在链接模块时添加架构特定的选项。这通常是链接器脚本。
从命令行传递的 LDFLAGS_MODULE 应该被使用（参见 kbuild.rst）

KBUILD_LDS  
包含完整路径的链接器脚本。由顶层 Makefile 分配。

KBUILD_VMLINUX_OBJS  
所有 vmlinux 的目标文件。它们按照 KBUILD_VMLINUX_OBJS 中列出的顺序链接到 vmlinux。
scripts/head-object-list.txt 中列出的目标文件是例外；它们会被放置在其他对象之前。

KBUILD_VMLINUX_LIBS  
所有用于 vmlinux 的 `.a` 库文件。KBUILD_VMLINUX_OBJS 和 KBUILD_VMLINUX_LIBS 一起指定了用于链接 vmlinux 的所有目标文件。

向 archheaders 添加先决条件
-------------------------------

archheaders: 规则用于生成可能通过 `make header_install` 安装到用户空间的头文件。
当在架构本身上运行 `make archprepare` 之前会运行此规则。

向 archprepare 添加先决条件
-------------------------------

archprepare: 规则用于列出需要在开始进入子目录之前构建的先决条件。
这通常用于包含汇编程序常量的头文件。
示例：

  #arch/arm/Makefile
  archprepare: maketools

在这个例子中，文件目标 `maketools` 将在进入子目录之前被处理。
参见章节 XXX-TODO，该章节描述了 kbuild 如何支持生成偏移头文件。

列出访问时的目录顺序
-------------------------------

一个架构 Makefile 与顶层 Makefile 配合定义变量，以指定如何构建 vmlinux 文件。注意，没有针对模块的特定架构部分；模块构建机制都是与架构无关的。
core-y, libs-y, drivers-y
  $(libs-y) 列出了可以定位 lib.a 归档文件的目录。
其他列出的则是可以定位内置 .a 对象文件的目录。
然后按以下顺序继续：

    $(core-y), $(libs-y), $(drivers-y)

顶层 Makefile 定义了所有通用目录的值，而 arch/$(SRCARCH)/Makefile 只添加特定于架构的目录。
示例：

    # arch/sparc/Makefile
    core-y                 += arch/sparc/

    libs-y                 += arch/sparc/prom/
    libs-y                 += arch/sparc/lib/

    drivers-$(CONFIG_PM) += arch/sparc/power/

特定于架构的引导映像
------------------------------

一个架构 Makefile 指定了将 vmlinux 文件压缩、用引导代码包裹并将其复制到某处的目标。这包括各种类型的安装命令。
实际的目标在不同架构之间并不标准化。
通常会在 arch/$(SRCARCH)/ 下的 boot/ 目录中进行任何附加处理。
kbuild 并不提供任何智能方式来支持构建 boot/ 中指定的目标。因此，arch/$(SRCARCH)/Makefile 应当手动调用 make 来构建 boot/ 中的目标。
推荐的方法是在 `arch/$(SRCARCH)/Makefile` 中包含快捷方式，并在调用 `arch/$(SRCARCH)/boot/Makefile` 时使用完整路径。
示例：

```makefile
# arch/x86/Makefile
boot := arch/x86/boot
bzImage: vmlinux
        $(Q)$(MAKE) $(build)=$(boot) $(boot)/$@
```

`$(Q)$(MAKE) $(build)=<dir>` 是推荐的在子目录中调用 make 的方法。

没有关于命名架构特定目标的规则，但执行 `make help` 将列出所有相关的目标。为了支持这一点，必须定义 `$(archhelp)`。
示例：

```makefile
# arch/x86/Makefile
define archhelp
    echo  '* bzImage      - 压缩内核镜像 (arch/x86/boot/bzImage)'
endef
```

当没有参数执行 make 时，将构建遇到的第一个目标。在顶层 Makefile 中，存在的第一个目标是 `all`：
一个架构应当始终默认构建一个可引导的镜像。
在 `make help` 中，默认目标会用 `*` 高亮显示。
向 `all` 添加一个新的先决条件以选择一个不同于 `vmlinux` 的默认目标。
示例：

```makefile
# arch/x86/Makefile
all: bzImage
```

当执行 `make` 且没有参数时，将构建 `bzImage`。

构建引导镜像时有用的命令
------------------------------

Kbuild 提供了一些宏，在构建引导镜像时非常有用。
### 链接目标
通常，`LDFLAGS_$@` 用于为 `ld` 设置特定的选项。

**示例：**

```makefile
# arch/x86/boot/Makefile
LDFLAGS_bootsect := -Ttext 0x0 -s --oformat binary
LDFLAGS_setup    := -Ttext 0x0 -s --oformat binary -e begtext

targets += setup setup.o bootsect bootsect.o
$(obj)/setup $(obj)/bootsect: %: %.o FORCE
        $(call if_changed,ld)
```

在这个示例中，有两个可能的目标，需要不同的链接器选项。链接器选项使用 `LDFLAGS_$@` 语法指定——每个潜在目标一个。

`$(targets)` 被分配了所有潜在的目标，这样 KBuild 就知道这些目标，并会：

1. 检查命令行的变化。
2. 在执行 `make clean` 时删除目标文件。

**注意：**
常见的错误是忘记 `targets :=` 的赋值，导致目标文件在没有任何明显原因的情况下被重新编译。

### objcopy
复制二进制文件。通常在 `arch/$(SRCARCH)/Makefile` 中指定 `OBJCOPYFLAGS`。

可以使用 `OBJCOPYFLAGS_$@` 来设置额外的选项。

### gzip
压缩目标。使用最大压缩级别来压缩目标文件。

**示例：**

```makefile
# arch/x86/boot/compressed/Makefile
$(obj)/vmlinux.bin.gz: $(vmlinux.bin.all-y) FORCE
        $(call if_changed,gzip)
```

### dtc
创建适合链接到 vmlinux 的扁平设备树 blob 对象。链接到 vmlinux 的设备树 blob 放置在图像中的 init 区段。平台代码 **必须** 在调用 `unflatten_device_tree()` 之前将 blob 复制到非 init 内存中。

要使用此命令，只需将 `*.dtb` 添加到 `obj-y` 或 `targets` 中，或者让其他目标依赖于 `%.dtb`。

存在一个中心规则，用于从 `$(src)/%.dts` 创建 `$(obj)/%.dtb`；架构 Makefile 不需要显式写出该规则。

**示例：**

```makefile
targets += $(dtb-y)
DTC_FLAGS ?= -p 1024
```

### 预处理链接脚本

当构建 vmlinux 映像时，会使用链接脚本 `arch/$(SRCARCH)/kernel/vmlinux.lds`。
该脚本是位于同一目录下的文件 vmlinux.lds.S 的预处理变体。
Kbuild 了解 .lds 文件，并包含一个规则 ``*lds.S`` -> ``*lds``。例如：

  # arch/x86/kernel/Makefile
  extra-y := vmlinux.lds

对 extra-y 的赋值用于告诉 Kbuild 构建目标 vmlinux.lds。
对 $(CPPFLAGS_vmlinux.lds) 的赋值告诉 Kbuild 在构建目标 vmlinux.lds 时使用指定的选项。
在构建 ``*.lds`` 目标时，Kbuild 使用以下变量：

  KBUILD_CPPFLAGS      : 在顶层 Makefile 中设置
  cppflags-y           : 可能在 Kbuild Makefile 中设置
  CPPFLAGS_$(@F)       : 目标特定的标志

请注意，在此赋值中使用了完整的文件名。
``*lds`` 文件的 Kbuild 基础结构在多个架构特定文件中被使用。
通用头文件
--------------

目录 include/asm-generic 包含可能在各个架构之间共享的头文件。
推荐使用通用头文件的方法是在 Kbuild 文件中列出该文件。
有关语法等更多信息，请参见 `generic-y`_。
### 链接后传递

如果文件 `arch/xxx/Makefile.postlink` 存在，此 Makefile 将被调用以处理架构的链接后对象（如 `vmlinux` 和 `modules.ko`）。还必须处理 `clean` 目标。此传递在生成 `kallsyms` 后运行。如果架构需要修改符号位置，而不是操作 `kallsyms`，可以为 `.tmp_vmlinux?` 目标添加另一个 `postlink` 目标，并在 `link-vmlinux.sh` 中调用它。

例如，`powerpc` 使用此方法检查已链接的 `vmlinux` 文件的重定位正确性。

### Kbuild 语法导出头文件

内核包含一组导出到用户空间的头文件。许多头文件可以直接导出，但其他头文件在准备好供用户空间使用之前需要进行最小的预处理。

预处理包括：

- 删除内核特定的注释
- 删除对 `compiler.h` 的包含
- 删除所有内核内部的部分（由 `ifdef __KERNEL__` 保护）

所有位于 `include/uapi/`, `include/generated/uapi/`, `arch/<arch>/include/uapi/` 和 `arch/<arch>/include/generated/uapi/` 下的头文件都会被导出。

可以在 `arch/<arch>/include/uapi/asm/` 和 `arch/<arch>/include/asm/` 下定义一个 Kbuild 文件来列出来自 `asm-generic` 的汇编文件。请参阅后续章节了解 Kbuild 文件的语法。

### no-export-headers

`no-export-headers` 主要用于 `include/uapi/linux/Kbuild` 来避免在不支持某些头文件（如 `kvm.h`）的架构上导出它们。应尽可能避免使用它。

### generic-y

如果架构使用了 `include/asm-generic` 中头文件的完全复制版本，则应在文件 `arch/$(SRCARCH)/include/asm/Kbuild` 中列出如下：

示例：

```plaintext
# arch/x86/include/asm/Kbuild
generic-y += termios.h
generic-y += rtc.h
```

在构建的准备阶段，将在目录中生成一个包装的包含文件：

```plaintext
arch/$(SRCARCH)/include/generated/asm
```

当导出一个使用通用头文件的头文件时，类似的包装文件将作为导出头文件集的一部分在目录中生成：

```plaintext
usr/include/asm
```

生成的包装文件在这两种情况下看起来如下：

示例：`termios.h`：

```plaintext
#include <asm-generic/termios.h>
```

### generated-y

如果架构除了生成 `generic-y` 包装文件之外还生成其他头文件，则 `generated-y` 会指定这些头文件。
这可以防止它们被视为过时的 asm-generic 包装层并被移除。
例如：

  #arch/x86/include/asm/Kbuild
  generated-y += syscalls_32.h

mandatory-y
-----------

mandatory-y 主要由 include/(uapi/)asm-generic/Kbuild 使用，以定义所有架构必须具有的最小 ASM 头文件集。
这类似于可选的 generic-y。如果在 arch/$(SRCARCH)/include/(uapi/)/asm 中缺少某个必需的头文件，Kbuild 将自动生成一个 asm-generic 的包装层。

Kbuild 变量
===========

顶层 Makefile 导出了以下变量：

VERSION, PATCHLEVEL, SUBLEVEL, EXTRAVERSION
  这些变量定义了当前内核版本。一些架构 Makefile 实际上直接使用这些值；但应使用 $(KERNELRELEASE)
$(VERSION)，$(PATCHLEVEL) 和 $(SUBLEVEL) 定义基本的三部分版本号，如 "2"、"4" 和 "0"。这三个值总是数字。
$(EXTRAVERSION) 定义了一个更小的子版本，用于预发布补丁或额外补丁。它通常是一个非数字字符串，如 "-pre4"，并且经常为空。
KERNELRELEASE
  $(KERNELRELEASE) 是一个单一的字符串，如 "2.4.0-pre4"，适合用于构建安装目录名或显示在版本字符串中。一些架构 Makefile 为此目的使用它。
ARCH
  此变量定义目标架构，如 "i386"、"arm" 或 "sparc"。一些 kbuild Makefile 通过测试 $(ARCH) 来确定编译哪些文件。
默认情况下，顶层 Makefile 将 $(ARCH) 设置为主机系统的架构。对于交叉编译，用户可以在命令行上覆盖 $(ARCH) 的值：

    make ARCH=m68k ..

SRCARCH
  此变量指定 arch/ 目录下的构建目录。
ARCH 和 SRCARCH 不一定匹配。一些架构目录是双架构的，也就是说，一个 `arch/*/` 目录同时支持 32 位和 64 位。

例如，您可以传递 ARCH=i386、ARCH=x86_64 或 ARCH=x86。对于所有这些情况，SRCARCH=x86，因为 arch/x86/ 同时支持 i386 和 x86_64。

INSTALL_PATH
  此变量定义了一个位置，用于安装架构相关的内核镜像和 System.map 文件。
使用此变量为特定架构的安装目标。

INSTALL_MOD_PATH, MODLIB
  $(INSTALL_MOD_PATH) 指定了模块安装时 $(MODLIB) 的前缀。此变量在 Makefile 中未定义，但用户可以根据需要传入。
  $(MODLIB) 指定了模块安装的目录。顶层 Makefile 将 $(MODLIB) 定义为 $(INSTALL_MOD_PATH)/lib/modules/$(KERNELRELEASE)。用户可以在命令行中覆盖此值，如果需要的话。

INSTALL_MOD_STRIP
  如果指定了此变量，则会在安装模块后对模块进行剥离。如果 INSTALL_MOD_STRIP 是 "1"，则会使用默认选项 --strip-debug。否则，INSTALL_MOD_STRIP 的值将作为 strip 命令的选项（s）使用。

INSTALL_DTBS_PATH
  此变量指定了构建根目录所需的重定位前缀。它定义了设备树 blob 的安装位置。与 INSTALL_MOD_PATH 类似，此变量在 Makefile 中未定义，但用户可以根据需要传入。否则，默认为内核安装路径。
Makefile 语言
=============

内核的 Makefile 被设计为与 GNU Make 一起使用。这些 Makefile 只使用 GNU Make 的已记录功能，但确实使用了许多 GNU 扩展。
GNU Make 支持基本的列表处理函数。内核的 Makefile 使用了一种新颖的列表构建和操作方式，并且很少使用 `if` 语句。
GNU Make 提供了两种赋值运算符：`:=` 和 `=`。`:=` 立即计算右侧表达式并将其实际字符串存储到左侧变量中。`=` 类似于公式定义；它以未计算的形式存储右侧表达式，并在每次使用左侧变量时评估该形式。
在某些情况下，`=` 是合适的。通常来说，`:=` 是更好的选择。

鸣谢
======

- 原版由 Michael Elizabeth Chastain 制作，<mailto:mec@shout.net>
- 更新由 Kai Germaschewski 完成，<kai@tp1.ruhr-uni-bochum.de>
- 更新由 Sam Ravnborg 完成，<sam@ravnborg.org>
- 语言质量保证由 Jan Engelhardt 完成，<jengelh@gmx.de>

待办事项
========

- 描述 kbuild 如何支持带有 _shipped 后缀的文件
- 生成偏移头文件
- 在第 7 或 9 章添加更多变量？
