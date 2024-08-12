SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

============================================================
Linux化的 ACPICA - ACPICA 发布自动化的介绍
============================================================

:版权所有: |copy| 2013-2016, Intel Corporation

:作者: Lv Zheng <lv.zheng@intel.com>


摘要
========
本文档描述了 ACPICA 项目以及 ACPICA 和 Linux 之间的关系。还描述了如何将 drivers/acpi/acpica、include/acpi 和 tools/power/acpi 中的 ACPICA 代码自动更新以跟踪上游
ACPICA 项目
==============

ACPI 组件架构 (ACPICA) 项目提供了一个高级配置和电源接口规范 (ACPI) 的操作系统 (OS) 独立的参考实现。它已被各种主机操作系统采纳。通过直接集成 ACPICA，Linux 也可以从其他主机操作系统中 ACPICA 的应用经验中受益。
ACPICA 项目的主页是：www.acpica.org，由 Intel Corporation 维护和支持。
下图描绘了包含 ACPICA 适应性的 Linux ACPI 子系统：

```
      +---------------------------------------------------------+
      |                                                         |
      |   +---------------------------------------------------+ |
      |   | +------------------+                              | |
      |   | | 表管理          |                              | |
      |   | +------------------+                              | |
      |   | +----------------------+                          | |
      |   | | 命名空间管理      |                          | |
      |   | +----------------------+                          | |
      |   | +------------------+       ACPICA 组件           | |
      |   | | 事件管理          |                              | |
      |   | +------------------+                              | |
      |   | +---------------------+                           | |
      |   | | 资源管理           |                           | |
      |   | +---------------------+                           | |
      |   | +---------------------+                           | |
      |   | | 硬件管理           |                           | |
      |   | +---------------------+                           | |
      | +---------------------------------------------------+ | |
      | | |                            +------------------+ | | |
      | | |                            | 操作系统服务层 | | | |
      | | |                            +------------------+ | | |
      | | +-------------------------------------------------|-+ |
      | |   +--------------------+                          |   |
      | |   | 设备枚举           |                          |   |
      | |   +--------------------+                          |   |
      | |   +------------------+                            |   |
      | |   | 电源管理           |                            |   |
      | |   +------------------+     Linux/ACPI 组件         |   |
      | |   +--------------------+                          |   |
      | |   | 热管理             |                          |   |
      | |   +--------------------+                          |   |
      | |   +--------------------------+                    |   |
      | |   | ACPI 设备的驱动程序     |                    |   |
      | |   +--------------------------+                    |   |
      | |   +--------+                                      |   |
      | |   | ...... |                                      |   |
      | |   +--------+                                      |   |
      | +---------------------------------------------------+   |
      |                                                         |
      +---------------------------------------------------------+
```

                 图 1. Linux ACPI 软件组件

.. note::
    A. 操作系统服务层 - 由 Linux 提供，以提供预定义的 ACPICA 接口（acpi_os_*）的 OS 依赖实现：
```
         include/acpi/acpiosxf.h
         drivers/acpi/osl.c
         include/acpi/platform
         include/asm/acenv.h
```
B. ACPICA 功能性 - 从 ACPICA 代码库发布，以提供 ACPICA 接口（acpi_*）的 OS 独立实现：
```
         drivers/acpi/acpica
         include/acpi/ac*.h
         tools/power/acpi
```
C. Linux/ACPI 功能性 - 向其他 Linux 内核子系统和用户空间程序提供 Linux 特定的 ACPI 功能：
```
         drivers/acpi
         include/linux/acpi.h
         include/linux/acpi*.h
         include/acpi
         tools/power/acpi
```
D. 架构特定的 ACPICA/ACPI 功能 - 由 ACPI 子系统提供，以提供 ACPI 接口的架构特定实现。它们是 Linux 特定组件，并且不在本文档的范围之内：
```
         include/asm/acpi.h
         include/asm/acpi*.h
         arch/*/acpi
```

ACPICA 发布
==============

ACPICA 项目在其代码库位于以下仓库 URL：https://github.com/acpica/acpica.git。按照惯例，每个月都会发布一次。
由于 ACPICA 项目采用的编码风格不符合 Linux 的要求，因此有一个发布过程用于将 ACPICA 的 Git 提交转换为 Linux 的补丁。此过程生成的补丁被称为“Linux化的 ACPICA 补丁”。此过程在 ACPICA Git 仓库的本地副本上执行。每月发布的每个提交都被转换为一个 Linux化的 ACPICA 补丁。它们共同构成了 Linux ACPI 社区的每月 ACPICA 发布补丁集。此过程如下图所示：

```
    +-----------------------------+
    | acpica / master (-) 提交    |
    +-----------------------------+
       /|\         |
        |         \|/
        |  /---------------------\    +----------------------+
        | < Linuxize 仓库实用工具 >-->| 旧版 Linux化的 acpica |--+
        |  \---------------------/    +----------------------+  |
        |                                                       |
     /---------\                                                |
    < git reset >                                                \
     \---------/                                                  \
       /|\                                                        /+-+
        |                                                        /   |
    +-----------------------------+                             |    |
    | acpica / master (+) 提交    |                             |    |
    +-----------------------------+                             |    |
                   |                                            |    |
                  \|/                                           |    |
         /-----------------------\    +----------------------+  |    |
        < Linuxize 仓库实用工具 >-->| 新版 Linux化的 acpica |--+    |
         \-----------------------/    +----------------------+       |
                                                                    \|/
    +--------------------------+                  /----------------------\
    | Linux化的 ACPICA 补丁 |<----------------< Linuxize 补丁实用工具 >
    +--------------------------+                  \----------------------/
                   |
                  \|/
     /---------------------------\
    < Linux ACPI 社区审查 >
     \---------------------------/
                   |
                  \|/
    +-----------------------+    /------------------\    +----------------+
    | linux-pm / linux-next |-->< Linux 合并窗口 >-->| linux / master |
    +-----------------------+    \------------------/    +----------------+
```

                图 2. ACPICA -> Linux 上游流程

.. note::
    A. Linuxize 实用工具 - 由 ACPICA 仓库提供，包括位于 source/tools/acpisrc 文件夹中的一个工具和位于 generate/linux 文件夹中的多个脚本
B. acpica / master - git 仓库中“master”分支位于 <https://github.com/acpica/acpica.git>
C. linux-pm / linux-next - “linux-next”分支位于 Git 仓库 <https://git.kernel.org/pub/scm/linux/kernel/git/rafael/linux-pm.git>
D. linux / master - “master”分支位于 Git 仓库 <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git>

在将 Linux 化的 ACPICA 补丁发送给 Linux ACPI 社区进行审查之前，有一个质量保证构建测试流程来减少移植问题。目前这个构建流程只处理以下内核配置选项：
   CONFIG_ACPI/CONFIG_ACPI_DEBUG/CONFIG_ACPI_DEBUGGER

ACPICA 分歧
=============

理想情况下，所有的 ACPICA 提交都应该被自动转换为 Linux 补丁，无需人工修改，“linux / master”树应该包含与“新的 Linux 化 ACPICA”树中所含的 ACPICA 代码完全对应的 ACPICA 代码，并且应该能够全自动地运行发布流程。
然而实际上，在 Linux 中的 ACPICA 代码和上游 ACPICA 代码之间存在源代码差异，这些被称为“ACPICA 分歧”。
ACPICA 分歧的各种来源包括：
   1. 遗留分歧 - 在当前的 ACPICA 发布流程建立之前，Linux 和 ACPICA 之间就已经存在分歧。在过去几年中，这些分歧已经大大减少，但仍有一些分歧需要时间来找出它们存在的根本原因。
2. 手动修改 - 对 Linux 源码进行的任何手动修改（例如编码风格修复）显然会损害 ACPICA 发布自动化。因此建议在上游 ACPICA 源码中修复此类问题，并使用 ACPICA 发布工具生成 Linux 化的修复（请参阅下面第 4 节的详细信息）。
3. Linux 特有功能 - 有时无法使用现有的 ACPICA API 来实现 Linux 内核所需的功能，因此 Linux 开发者偶尔需要直接更改 ACPICA 代码。
这些更改可能不被上游 ACPICA 接受，在这种情况下，除非 ACPICA 方面能够实现新的机制作为替代，否则它们将作为已提交的 ACPICA 分歧保留下来。
4. ACPICA 发布修复 - ACPICA 仅使用一组用户空间模拟工具来测试提交，因此 Linux 化的 ACPICA 补丁可能会破坏 Linux 内核，导致构建/启动失败。为了避免破坏 Linux 的二分查找，会在发布过程中直接对 Linux 化的 ACPICA 补丁应用修复。当这些发布修复回传到上游 ACPICA 源码时，它们必须遵循上游 ACPICA 的规则，因此可能会出现进一步的修改。
这可能导致新分歧的出现。
### ACPICA 提交的快速跟踪 —— 一些 ACPICA 的提交是针对回归修复或稳定候选的内容，因此它们会提前于 ACPICA 发布流程被应用。如果这些提交在 ACPICA 方面被撤销或基于更好的解决方案进行重基，则会产生新的 ACPICA 分歧。

#### ACPICA 开发

本段落指导 Linux 开发者如何使用 ACPICA 上游发布的工具，在这些提交正式通过 ACPICA 发布流程之前获取与之对应的 Linux 补丁。

1. **选择性提取（Cherry-Pick）一个 ACPICA 提交**

   首先需要使用 `git clone` 命令克隆 ACPICA 仓库，并且你想要选择性提取的 ACPICA 变更必须已经被提交到本地仓库中。
   然后可以使用 `gen-patch.sh` 命令帮助选择性提取 ACPICA 提交内容：
   
   ```
   $ git clone https://github.com/acpica/acpica
   $ cd acpica
   $ generate/linux/gen-patch.sh -u [commit ID]
   ```

   这里的 `commit ID` 是你想选择性提取的 ACPICA 本地仓库中的提交 ID。如果提交是“HEAD”，则可以省略 `commit ID`。
   
2. **选择性提取最近的 ACPICA 提交**

   有时你需要将你的代码基于最新但尚未应用于 Linux 的 ACPICA 变更进行重基。
   你可以自行生成 ACPICA 发布系列，并基于生成的 ACPICA 发布补丁对你的代码进行重基：

   ```
   $ git clone https://github.com/acpica/acpica
   $ cd acpica
   $ generate/linux/make-patches.sh -u [commit ID]
   ```

   `commit ID` 应该是最后一个被 Linux 接受的 ACPICA 提交。通常情况下，这是修改了 `ACPI_CA_VERSION` 的提交。你可以通过执行 `git blame source/include/acpixf.h` 并参考包含 `ACPI_CA_VERSION` 的行来找到这个提交。

3. **检查当前分歧的状态**

   如果你同时拥有 Linux 和上游 ACPICA 的本地副本，你可以生成一个 diff 文件来指示当前分歧的状态：

   ```
   # git clone https://github.com/acpica/acpica
   # git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
   # cd acpica
   # generate/linux/divergence.sh -s ../linux
   ```
