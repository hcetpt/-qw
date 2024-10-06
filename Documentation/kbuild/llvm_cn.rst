.. _kbuild_llvm:

==============================
使用 Clang/LLVM 构建 Linux
==============================

本文档介绍了如何使用 Clang 和 LLVM 工具构建 Linux 内核。
关于
-----

Linux 内核传统上一直使用 GNU 工具链（如 GCC 和 binutils）进行编译。正在进行的工作使得可以将 `Clang <https://clang.llvm.org/>`_ 和 `LLVM <https://llvm.org/>`_ 工具作为可行的替代品。诸如 `Android <https://www.android.com/>`_、`ChromeOS <https://www.chromium.org/chromium-os>`_、`OpenMandriva <https://www.openmandriva.org/>`_ 和 `Chimera Linux <https://chimera-linux.org/>`_ 等发行版都使用了由 Clang 构建的内核。Google 和 Meta 的数据中心也运行着用 Clang 构建的内核。

`LLVM 是一组使用 C++ 对象实现的工具链组件 <https://www.aosabook.org/en/llvm.html>`_。Clang 是 LLVM 的前端，支持内核所需的 C 语言和 GNU C 扩展，并且发音为“klang”，而不是“see-lang”。

使用 LLVM 构建
------------------

通过以下命令调用 ``make`` 来编译主机目标：

::
   
   make LLVM=1

对于交叉编译：

::
   
   make LLVM=1 ARCH=arm64

``LLVM=`` 参数
------------------

LLVM 提供了 GNU binutils 工具的替代品。这些工具可以单独启用。支持的所有 make 变量如下：

::
   
   make CC=clang LD=ld.lld AR=llvm-ar NM=llvm-nm STRIP=llvm-strip \
     OBJCOPY=llvm-objcopy OBJDUMP=llvm-objdump READELF=llvm-readelf \
     HOSTCC=clang HOSTCXX=clang++ HOSTAR=llvm-ar HOSTLD=ld.lld

``LLVM=1`` 展开后即为上述内容。

如果您的 LLVM 工具不在您的 PATH 中，可以使用带有尾斜杠的 LLVM 变量指定其位置：

::
   
   make LLVM=/path/to/llvm/

这会使用 `/path/to/llvm/clang`、`/path/to/llvm/ld.lld` 等工具。您也可以使用以下命令：

::
   
   PATH=/path/to/llvm:$PATH make LLVM=1

如果您希望测试特定版本的 LLVM 工具而不是默认的工具，可以使用带有版本后缀的 LLVM 变量：

::
   
   make LLVM=-14

这会使用 `clang-14`、`ld.lld-14` 等工具。

为了支持路径与版本后缀组合的情况，建议使用以下命令：

::
   
   PATH=/path/to/llvm/:$PATH make LLVM=-14

``LLVM=0`` 不同于完全省略 LLVM，它会像 ``LLVM=1`` 一样工作。如果您只想使用某些 LLVM 工具，请使用相应的 make 变量。

在配置和构建过程中，每次调用 ``make`` 都应使用相同的 ``LLVM=`` 值。当运行最终会调用 ``make`` 的脚本时，应将 ``LLVM=`` 设置为环境变量。

交叉编译
--------------

通常，单个 Clang 编译器二进制文件（及其对应的 LLVM 工具）会包含所有支持的后端，这有助于简化交叉编译，尤其是在使用 ``LLVM=1`` 时。如果您仅使用 LLVM 工具，则无需使用 `CROSS_COMPILE` 或目标三元组前缀。示例：

::
   
   make LLVM=1 ARCH=arm64

作为一个混合使用 LLVM 和 GNU 工具的例子，对于尚未支持 `ld.lld` 或 `llvm-objcopy` 的目标（如 `ARCH=s390`），您可以使用以下命令：

::
   
   make LLVM=1 ARCH=s390 LD=s390x-linux-gnu-ld.bfd \
     OBJCOPY=s390x-linux-gnu-objcopy

此示例会调用 `s390x-linux-gnu-ld.bfd` 作为链接器以及 `s390x-linux-gnu-objcopy`，因此请确保它们在您的 `$PATH` 中。

当交叉编译并使用 ``LLVM_IAS=0`` 时，需要设置 `CROSS_COMPILE` 以便为编译器设置 `--prefix=`，从而找到相应的非集成汇编器（通常，您不希望在针对其他架构时使用系统汇编器）。示例：

::
   
   make LLVM=1 ARCH=arm LLVM_IAS=0 CROSS_COMPILE=arm-linux-gnueabi-

LLVM_IAS= 参数
----------------------

Clang 可以汇编汇编代码。您可以传递 ``LLVM_IAS=0`` 来禁用这种行为，并让 Clang 调用相应的非集成汇编器。示例：

::
   
   make LLVM=1 LLVM_IAS=0

ccache
------

可以使用 ``ccache`` 与 ``clang`` 结合来提高后续构建的速度（不过，为了防止缓存命中率为 100%，应在构建之间设置 KBUILD_BUILD_TIMESTAMP_ 为确定性值，详情参见 Reproducible_builds_）：

::
   
   KBUILD_BUILD_TIMESTAMP='' make LLVM=1 CC="ccache clang"

.. _KBUILD_BUILD_TIMESTAMP: kbuild.html#kbuild-build-timestamp
.. _Reproducible_builds: reproducible-builds.html#timestamps

支持的架构
-----------------------

LLVM 并不支持所有 Linux 支持的架构，并且即使某个目标在 LLVM 中受到支持，也不能保证内核能无问题地构建或工作。以下是目前支持的架构概览。支持级别对应于 MAINTAINERS 文件中的 "S" 值。如果某个架构没有列出，要么是因为 LLVM 不支持该架构，要么是因为已知存在问题。使用最新稳定版本的 LLVM 或者开发树通常会得到最好的结果。

一个架构的 `defconfig` 通常期望能很好地工作，某些配置可能存在尚未发现的问题。欢迎在下面的问题跟踪器中报告 bug！

.. list-table::
   :widths: 10 10 10
   :header-rows: 1

   * - 架构
     - 支持级别
     - make 命令
   * - arm
     - 支持
     - ``LLVM=1``
   * - arm64
     - 支持
     - ``LLVM=1``
   * - hexagon
     - 维护中
     - ``LLVM=1``
   * - loongarch
     - 维护中
     - ``LLVM=1``
   * - mips
     - 维护中
     - ``LLVM=1``
   * - powerpc
     - 维护中
     - ``LLVM=1``
   * - riscv
     - 支持
     - ``LLVM=1``
   * - s390
     - 维护中
     - ``LLVM=1`` (LLVM >= 18.1.0)，``CC=clang`` (LLVM < 18.1.0)
   * - um (用户模式)
     - 维护中
     - ``LLVM=1``
   * - x86
     - 支持
     - ``LLVM=1``

获取帮助
------------

- `网站 <https://clangbuiltlinux.github.io/>`_
- `邮件列表 <https://lore.kernel.org/llvm/>`_： <llvm@lists.linux.dev>
- `旧邮件列表归档 <https://groups.google.com/g/clang-built-linux>`_
- `问题跟踪器 <https://github.com/ClangBuiltLinux/linux/issues>`_
- IRC：#clangbuiltlinux 在 irc.libera.chat 上
- `Telegram <https://t.me/ClangBuiltLinux>`_：@ClangBuiltLinux
- `维基 <https://github.com/ClangBuiltLinux/linux/wiki>`_
- `适合新手的问题 <https://github.com/ClangBuiltLinux/linux/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22>`_

.. _getting_llvm:

获取 LLVM
------------

我们在 `kernel.org <https://kernel.org/pub/tools/llvm/>`_ 提供了预构建的稳定版本的 LLVM。这些版本已经使用了构建 Linux 内核的性能数据进行了优化，相比其他 LLVM 发行版应该能缩短内核构建时间。
以下是可能对从源代码构建 LLVM 或通过发行版的包管理器获取 LLVM 有用的链接：
- https://releases.llvm.org/download.html
- https://github.com/llvm/llvm-project
- https://llvm.org/docs/GettingStarted.html
- https://llvm.org/docs/CMake.html
- https://apt.llvm.org/
- https://www.archlinux.org/packages/extra/x86_64/llvm/
- https://github.com/ClangBuiltLinux/tc-build
- https://github.com/ClangBuiltLinux/linux/wiki/Building-Clang-from-source
- https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/
