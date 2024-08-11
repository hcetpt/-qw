使用 gcov 与 Linux 内核
=======================

gcov 覆盖率测试支持使得能够在 Linux 内核中使用 GCC 的覆盖率测试工具 gcov_。运行中的内核的覆盖率数据通过 "gcov" debugfs 目录以 gcov 兼容格式导出。为了获取特定文件的覆盖率数据，切换到内核构建目录，并使用带有 `-o` 选项的 gcov（需要 root 权限）如下所示： 

    # cd /tmp/linux-out
    # gcov -o /sys/kernel/debug/gcov/tmp/linux-out/kernel spinlock.c

这将在当前目录下创建带有执行次数注释的源代码文件。此外，可以使用图形化的 gcov 前端如 lcov_ 自动化收集整个内核的数据过程，并以 HTML 格式提供覆盖率概览。

可能的应用包括：

* 调试（该行是否被触发过？）
* 改进测试（我如何修改我的测试来覆盖这些行？）
* 减少内核配置（如果相关代码从未被执行，我是否需要这个选项？）

.. _gcov: https://gcc.gnu.org/onlinedocs/gcc/Gcov.html
.. _lcov: http://ltp.sourceforge.net/coverage/lcov.php

准备
----

配置内核时需要包含以下选项：

        CONFIG_DEBUG_FS=y
        CONFIG_GCOV_KERNEL=y

如果要为整个内核收集覆盖率数据，则还需包含：

        CONFIG_GCOV_PROFILE_ALL=y

注意，使用了性能分析标志编译的内核会显著变大并且运行速度会变慢。另外，CONFIG_GCOV_PROFILE_ALL 可能不是所有架构都支持的。
性能分析数据只有在挂载了 debugfs 后才可访问：

        mount -t debugfs none /sys/kernel/debug

定制
----

为了启用对特定文件或目录的性能分析，在相应的内核 Makefile 中添加如下类似的行：

- 对于单个文件（例如 main.o）：

	GCOV_PROFILE_main.o := y

- 对于一个目录中的所有文件：

	GCOV_PROFILE := y

如果即使指定了 CONFIG_GCOV_PROFILE_ALL 也不希望对某些文件进行性能分析，可以使用：

	GCOV_PROFILE_main.o := n

和

	GCOV_PROFILE := n

此机制只支持链接到主内核映像的文件或作为内核模块编译的文件。

文件
----

gcov 内核支持会在 debugfs 中创建以下文件：

``/sys/kernel/debug/gcov``
	所有与 gcov 相关文件的父目录。
``/sys/kernel/debug/gcov/reset``
	全局重置文件：写入时将所有覆盖率数据重置为零。
``/sys/kernel/debug/gcov/path/to/compile/dir/file.gcda``
	由 gcov 工具理解的实际 gcov 数据文件。写入时重置文件的覆盖率数据。
``/sys/kernel/debug/gcov/path/to/compile/dir/file.gcno``
	符号链接指向静态数据文件，这是 gcov 工具所必需的。当使用 `-ftest-coverage` 编译选项时由 gcc 生成。

模块
----

内核模块可能包含仅在模块卸载时运行的清理代码。gcov 机制通过保留已卸载模块相关数据的副本来收集此类代码的覆盖率数据。这些数据可通过 debugfs 访问。
一旦模块再次加载，其相关的覆盖率计数器将用之前实例的数据初始化。
这种行为可以通过指定 `gcov_persist` 内核参数来停用：

        gcov_persist=0

在运行时，用户也可以选择通过写入模块的数据文件或全局重置文件来丢弃已卸载模块的数据。

### 分离的构建和测试机器

gcov 内核性能分析基础设施设计为在构建内核和运行内核在同一台机器上的设置中开箱即用。当内核在单独的机器上运行时，需要根据 gcov 工具使用的地点进行特殊准备：

#### gcov 在 **测试** 机器上运行

测试机器上的 gcov 工具版本必须与用于构建内核的 gcc 版本兼容。此外，以下文件需要从构建机器复制到测试机器：

- 来自源代码树：
  - 所有 C 源文件 + 头文件
- 来自构建目录：
  - 所有 C 源文件 + 头文件
  - 所有 `.gcda` 和 `.gcno` 文件
  - 所有指向目录的链接

重要的是要注意这些文件需要放置在测试机器上的与构建机器完全相同的文件系统位置。如果路径中的任何组件是符号链接，则需要使用实际目录（因为 make 的 CURDIR 处理方式）。

#### gcov 在 **构建** 机器上运行

每个测试案例之后，需要将以下文件从测试机器复制到构建机器：

- 来自 sysfs 中的 gcov 目录：
  - 所有 `.gcda` 文件
  - 所有指向 `.gcno` 文件的链接

这些文件可以复制到构建机器上的任意位置。然后需要使用 `-o` 选项调用 gcov，该选项指向该目录。
构建机器上的示例目录结构如下：

      /tmp/linux:    内核源代码树
      /tmp/out:      由 make O= 指定的内核构建目录
      /tmp/coverage: 从测试机器复制文件的位置

      [user@build] cd /tmp/out
      [user@build] gcov -o /tmp/coverage/tmp/out/init main.c

### 关于编译器的说明

GCC 和 LLVM 的 gcov 工具不一定兼容。使用 gcov_ 来处理 GCC 生成的 `.gcno` 和 `.gcda` 文件，并使用 llvm-cov_ 来处理 Clang。
.. _gcov: https://gcc.gnu.org/onlinedocs/gcc/Gcov.html
.. _llvm-cov: https://llvm.org/docs/CommandGuide/llvm-cov.html

GCC 和 Clang gcov 之间的构建差异由 Kconfig 处理。它会自动根据检测到的工具链选择适当的 gcov 格式。

### 故障排除

#### 问题
编译在链接步骤中断
#### 原因
为未链接到主内核或通过自定义链接程序链接的源文件指定了性能分析标志
#### 解决方案
通过在相应的 Makefile 中指定 `GCOV_PROFILE := n` 或 `GCOV_PROFILE_basename.o := n` 来排除受影响的源文件

#### 问题
从 sysfs 复制的文件为空或不完整
#### 原因
由于 seq_file 的工作方式，一些工具如 cp 或 tar 可能无法正确地从 sysfs 复制文件
### 解决方案
使用 `cat` 来读取 `.gcda` 文件，并使用 `cp -d` 来复制链接。
或者使用附录 B 中所示的机制。

### 附录 A: gather_on_build.sh

用于在构建机器上收集覆盖率元文件的示例脚本
（参见：[分开的构建和测试机器 a.](#gcov-test)）：

```sh
#!/bin/bash

KSRC=$1
KOBJ=$2
DEST=$3

if [ -z "$KSRC" ] || [ -z "$KOBJ" ] || [ -z "$DEST" ]; then
  echo "用法: $0 <ksrc 目录> <kobj 目录> <output.tar.gz>" >&2
  exit 1
fi

KSRC=$(cd $KSRC; printf "all:\n\t@echo \${CURDIR}\n" | make -f -)
KOBJ=$(cd $KOBJ; printf "all:\n\t@echo \${CURDIR}\n" | make -f -)

find $KSRC $KOBJ \( -name '*.gcno' -o -name '*.[ch]' -o -type l \) -a \
                     -perm /u+r,g+r | tar cfz $DEST -P -T -

if [ $? -eq 0 ] ; then
  echo "$DEST 成功创建，将其复制到测试系统并使用以下命令解压:"
  echo "  tar xfz $DEST -P"
else
  echo "无法创建文件 $DEST"
fi
```

### 附录 B: gather_on_test.sh

用于在测试机器上收集覆盖率数据文件的示例脚本
（参见：[分开的构建和测试机器 b.](#gcov-build)）：

```sh
#!/bin/bash -e

DEST=$1
GCDA=/sys/kernel/debug/gcov

if [ -z "$DEST" ] ; then
  echo "用法: $0 <output.tar.gz>" >&2
  exit 1
fi

TEMPDIR=$(mktemp -d)
echo 收集数据。
find $GCDA -type d -exec mkdir -p $TEMPDIR/\{\} \;
find $GCDA -name '*.gcda' -exec sh -c 'cat < $0 > '$TEMPDIR'/$0' {} \;
find $GCDA -name '*.gcno' -exec sh -c 'cp -d $0 '$TEMPDIR'/$0' {} \;
tar czf $DEST -C $TEMPDIR sys
rm -rf $TEMPDIR

echo "$DEST 成功创建，将其复制到构建系统并使用以下命令解压:"
echo "  tar xfz $DEST"
```
