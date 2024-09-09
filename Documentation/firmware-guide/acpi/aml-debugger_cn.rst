.. SPDX-License-Identifier: GPL-2.0
.. include:: <isonum.txt>

================
AML 调试器
================

:版权: |copy| 2016，Intel 公司
:作者: Lv Zheng <lv.zheng@intel.com>

本文档描述了嵌入到 Linux 内核中的 AML 调试器的使用方法。

1. 构建调试器
=====================

要从 Linux 内核启用 AML 调试器接口，需要以下内核配置项：

```
CONFIG_ACPI_DEBUGGER=y
CONFIG_ACPI_DEBUGGER_USER=m
```

可以通过以下命令从内核源代码树构建用户空间工具：

```
$ cd tools
$ make acpi
```

生成的用户空间工具二进制文件位于：

```
tools/power/acpi/acpidbg
```

通过运行 "make install"（作为具有足够权限的用户）可以将其安装到系统目录中。

2. 启动用户空间调试器接口
=========================================

在使用内置调试器引导内核后，可以通过以下命令启动调试器：

```
# mount -t debugfs none /sys/kernel/debug
# modprobe acpi_dbg
# tools/power/acpi/acpidbg
```

这将启动一个交互式的 AML 调试器环境，在这里你可以执行调试器命令。这些命令在可以从以下网址下载的《ACPICA 概览与程序员参考》中有详细说明：

https://acpica.org/documentation

详细的调试器命令参考位于第 12 章“ACPICA 调试器参考”。可以使用 "help" 命令快速查看。

3. 停止用户空间调试器接口
========================================

可以通过按 Ctrl+C 或使用 "quit" 或 "exit" 命令关闭交互式调试器接口。完成后，卸载模块：

```
# rmmod acpi_dbg
```

如果有一个正在运行的 acpidbg 实例，则模块卸载可能会失败。

4. 在脚本中运行调试器
===============================

在测试脚本中运行 AML 调试器可能很有用。“acpidbg”支持一种特殊的“批处理”模式。例如，以下命令输出整个 ACPI 名称空间：

```
# acpidbg -b "namespace"
```
