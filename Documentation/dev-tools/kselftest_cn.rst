======================
Linux 内核自测
======================

内核在 tools/testing/selftests/ 目录下包含了一系列的“自测试”。这些测试旨在针对内核中的各个独立代码路径进行验证。测试应在构建、安装并引导内核后运行。
来自主线版本的 Kselftest 可以在较旧的稳定内核上运行。运行来自主线版本的测试提供了最佳的覆盖范围。多个测试环路会在稳定发布版上运行主线 Kselftest 套件。原因在于，当添加新的测试来针对现有代码进行回归测试以修复一个错误时，我们应该能够在较旧的内核上运行该测试。因此，重要的是要保持可以测试较旧内核的代码，并确保在新版本中优雅地跳过测试。
您可以在 Kselftest 维基上找到有关 Kselftest 框架的更多信息，以及如何使用该框架编写新的测试：

https://kselftest.wiki.kernel.org/

在某些系统上，热插拔测试可能会永远挂起等待 CPU 和内存准备好被离线。为此创建了一个特殊的热插拔目标来运行完整的热插拔测试范围。默认情况下，热插拔测试以安全模式运行，范围有限。在有限模式下，CPU 热插拔测试仅在一个 CPU 上运行，而不是所有支持热插拔的 CPU；而内存热插拔测试则在 2% 的可热插拔内存上运行，而非 10%。
Kselftest 作为一个用户空间进程运行。可以在用户空间编写的/运行的测试可能希望使用 `测试框架`_。需要在内核空间运行的测试可能希望使用 `测试模块`_。
运行自测试（热插拔测试在有限模式下运行）
=============================================================

要构建测试，请执行以下命令：

  $ make headers
  $ make -C tools/testing/selftests

要运行测试，请执行以下命令：

  $ make -C tools/testing/selftests run_tests

要使用单个命令构建并运行测试，请执行以下命令：

  $ make kselftest

请注意，某些测试将需要 root 权限。
Kselftest 支持将输出文件保存在单独的目录中，然后运行测试。为此支持两种语法。在这两种情况下，工作目录必须是内核源码的根目录。这适用于下面的“运行子集的自测试”部分。
要构建并在单独的目录中保存输出文件，请使用 O= ：

  $ make O=/tmp/kselftest kselftest

要在单独的目录中保存输出文件，请使用 KBUILD_OUTPUT ：

  $ export KBUILD_OUTPUT=/tmp/kselftest; make kselftest

O= 赋值优先于 KBUILD_OUTPUT 环境变量。
上述命令默认会运行测试并打印完整的通过/失败报告。
Kselftest 支持“summary”选项，以便更容易理解测试结果。请在指定 summary 选项时，在 /tmp/testname 文件中查看每个测试的详细个体测试结果。这也适用于下面的“运行子集的自测试”部分。
要启用 summary 选项运行 kselftest，请执行以下命令：

  $ make summary=1 kselftest

运行自测试子集
=============================

您可以在 make 命令行上使用“TARGETS”变量来指定要运行的单一测试或测试列表。
为了仅运行针对单一子系统的测试：

  $ make -C tools/testing/selftests TARGETS=ptrace run_tests

您可以指定多个要构建和运行的测试：

  $ make TARGETS="size timers" kselftest

为了构建，并将输出文件保存在单独的目录中，请使用O=：

  $ make O=/tmp/kselftest TARGETS="size timers" kselftest

为了构建，并将输出文件保存在通过KBUILD_OUTPUT指定的单独目录中：

  $ export KBUILD_OUTPUT=/tmp/kselftest; make TARGETS="size timers" kselftest

此外，您可以在make命令行中使用“SKIP_TARGETS”变量来指定要从TARGETS列表中排除的一个或多个目标
为了运行除了单一子系统外的所有测试：

  $ make -C tools/testing/selftests SKIP_TARGETS=ptrace run_tests

您可以指定多个要跳过的测试：

  $ make SKIP_TARGETS="size timers" kselftest

您还可以指定一个要一起运行的限制性测试列表，同时指定一个专用的跳过列表：

  $ make TARGETS="breakpoints size timers" SKIP_TARGETS=size kselftest

请参阅顶层tools/testing/selftests/Makefile以获取所有可能的目标列表。
运行完整的热插拔自测
========================================

为了构建热插拔测试：

  $ make -C tools/testing/selftests hotplug

为了运行热插拔测试：

  $ make -C tools/testing/selftests run_hotplug

请注意，某些测试需要root权限。
安装自测
=================

您可以使用make的"install"目标（它调用`kselftest_install.sh`工具）将自测安装到默认位置（`tools/testing/selftests/kselftest_install`），或者通过`INSTALL_PATH` make变量安装到用户指定的位置。
为了将自测安装到默认位置：

   $ make -C tools/testing/selftests install

为了将自测安装到用户指定的位置：

   $ make -C tools/testing/selftests install INSTALL_PATH=/some/other/path

运行已安装的自测
===========================

在安装目录中，以及在Kselftest压缩包中，有一个名为`run_kselftest.sh`的脚本来运行测试。
您可以简单地按照以下步骤来运行已安装的Kselftests。请注意，某些测试需要root权限：

   $ cd kselftest_install
   $ ./run_kselftest.sh

要查看可用测试的列表，可以使用`-l`选项：

   $ ./run_kselftest.sh -l

`-c`选项可用于运行来自测试集合的所有测试，或者`-t`选项用于特定的单个测试。这两种选项都可以多次使用：

   $ ./run_kselftest.sh -c size -c seccomp -t timers:posix_timers -t timer:nanosleep

对于其他功能，请参阅使用`-h`选项获得的脚本使用说明。
自测的超时设置
=====================

自测设计为快速运行，因此每个测试都使用默认的45秒超时。测试可以通过在其目录中添加设置文件并在此处设置超时变量来覆盖默认超时，从而为测试配置所需的最长超时时间。只有少数测试会将超时设置为超过45秒的值，自测的目标是保持这种状态。在自测中，超时并不被视为致命错误，因为测试运行的系统可能会发生变化，这也会影响预期的测试运行时间。如果您能够控制将运行测试的系统，您可以在命令行上使用`-o`或`--override-timeout`参数配置测试运行器以使用更长或更短的超时时间。例如，要使用165秒，您可以这样做：

   $ ./run_kselftest.sh --override-timeout 165

您可以查看TAP输出以查看是否遇到了超时。如果知道某个测试必须在特定时间内运行，则测试运行器可以选择将这些超时视为致命错误。
打包自测
===================

在某些情况下，可能需要打包自测，例如当测试需要在不同的系统上运行时。为了打包自测，请运行：

   $ make -C tools/testing/selftests gen_tar

这会在`INSTALL_PATH/kselftest-packages`目录中生成一个压缩包。默认情况下，使用`.gz`格式。可以通过指定`FORMAT` make变量来覆盖tar压缩格式。任何被`tar的auto-compress`_选项支持的值都是可以接受的，例如：

    $ make -C tools/testing/selftests gen_tar FORMAT=.xz

`make gen_tar`会调用`make install`，因此您可以使用在“运行自测子集”_部分中指定的变量来打包测试子集：

    $ make -C tools/testing/selftests gen_tar TARGETS="size" FORMAT=.xz

.. _tar's auto-compress: https://www.gnu.org/software/tar/manual/html_node/gzip.html#auto_002dcompress

贡献新测试
======================

一般来说，自测的规则如下：

 * 尽可能多地在非root环境下完成；

 * 不要花费太多时间；

 * 不要在任何架构上破坏构建，并且

 * 如果您的特性未配置，则不要导致顶级"make run_tests"失败
* 测试输出必须符合TAP标准以确保高质量的测试并捕获带有具体细节的失败/错误
kselftest.h 和 kselftest_harness.h 头文件提供了用于输出测试结果的包装函数。这些包装函数应被用于通过、失败、退出和跳过的消息。CI系统可以轻松解析TAP输出消息以检测测试结果。
贡献新的测试（详情）
==================

 * 在你的 `Makefile` 中，通过包含 `lib.mk` 来使用其中提供的功能，而不是重新造轮子。在包含 `lib.mk` 之前根据需要指定标志和二进制文件生成标志。例如：

    ```
    CFLAGS = $(KHDR_INCLUDES)
    TEST_GEN_PROGS := close_range_test
    include ../lib.mk
    ```

 * 如果编译过程中会生成此类二进制文件或文件，请使用 `TEST_GEN_XXX`。
   - `TEST_PROGS` 和 `TEST_GEN_PROGS` 表示这些是默认要测试的可执行程序。
   - 如果测试需要构建模块，则应使用 `TEST_GEN_MODS_DIR`。该变量将包含包含这些模块的目录名称。
   - 如果测试需要自定义构建规则，并且希望避免使用通用构建规则，则应使用 `TEST_CUSTOM_PROGS`。
   - `TEST_PROGS` 适用于测试脚本。请确保脚本设置了可执行位，否则 `lib.mk` 中的 `run_tests` 将生成警告。
   - `TEST_CUSTOM_PROGS` 和 `TEST_PROGS` 都会被 `run_tests` 命令运行。
   - `TEST_PROGS_EXTENDED` 和 `TEST_GEN_PROGS_EXTENDED` 表示这些不是默认测试的可执行程序。
   - `TEST_FILES` 和 `TEST_GEN_FILES` 表示这些是被测试使用的文件。
   - `TEST_INCLUDES` 类似于 `TEST_FILES`，它列出了导出或安装测试时应包含的文件，不同之处在于：
     - 其他目录中的文件符号链接会被保留。
     - 当复制文件到输出目录时，会保留路径中 `tools/testing/selftests/` 以下的部分。
   - `TEST_INCLUDES` 主要用于列出自测体系结构中其他目录下的依赖项。

 * 首先使用内核源码或 Git 仓库内的头文件，然后才是系统头文件。相对于由发行版安装在系统上的头文件，内核版本的头文件应该是主要关注点，以便能够发现回归问题。在 `Makefile` 中使用 `KHDR_INCLUDES` 来包含来自内核源码的头文件。
如果测试需要特定的内核配置选项被启用，可以在测试目录中添加一个配置文件来启用它们。
例如：`tools/testing/selftests/android/config`

* 在测试目录内创建一个`.gitignore`文件，并在其中添加所有生成的对象。

* 在`selftests/Makefile`中的`TARGETS`变量添加新的测试名称：
```makefile
TARGETS += android
```

* 所有的更改都应该通过以下命令的测试：
```sh
kselftest-{all,install,clean,gen_tar}
kselftest-{all,install,clean,gen_tar} O=abo_path
kselftest-{all,install,clean,gen_tar} O=rel_path
make -C tools/testing/selftests {all,install,clean,gen_tar}
make -C tools/testing/selftests {all,install,clean,gen_tar} O=abs_path
make -C tools/testing/selftests {all,install,clean,gen_tar} O=rel_path
```

测试模块
========

Kselftest从用户空间测试内核。有时，需要在内核内部进行测试，一种方法是创建一个测试模块。我们可以通过使用shell脚本测试运行器将模块与kselftest框架绑定起来。`kselftest/module.sh`旨在为此过程提供便利。还提供了一个头文件以帮助编写用于kselftest的内核模块：

- `tools/testing/selftests/kselftest_module.h`
- `tools/testing/selftests/kselftest/module.sh`

请注意，测试模块应该通过TAINT_TEST标记内核。这将自动为位于`tools/testing/`目录内的模块或使用上述`kselftest_module.h`头文件的模块发生。否则，您需要在模块源代码中添加`MODULE_INFO(test, "Y")`。通常不加载模块的自测不应该标记内核，但在非测试模块被加载的情况下，可以通过写入`/proc/sys/kernel/tainted`从用户空间应用TEST_TAINT。

如何使用
--------

这里展示了创建测试模块并将其与kselftest绑定的一般步骤。我们以`lib/`目录下的kselftests为例：
1. 创建测试模块。

2. 创建将运行（加载/卸载）模块的测试脚本。
   例如：`tools/testing/selftests/lib/printf.sh`

3. 在配置文件中添加一行。
   例如：`tools/testing/selftests/lib/config`

4. 将测试脚本添加到Makefile中。
   例如：`tools/testing/selftests/lib/Makefile`

5. 验证它是否工作：
```sh
# 假设您已使用此内核树的新构建启动
cd /path/to/linux/tree
make kselftest-merge
make modules
sudo make modules_install
make TARGETS=lib kselftest
```

示例模块
--------

一个基本的测试模块可能看起来像这样：

```c
// SPDX-License-Identifier: GPL-2.0+

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include "../tools/testing/selftests/kselftest_module.h"

KSTM_MODULE_GLOBALS();

/*
 * 用于测试foobinator的内核模块
 */

static int __init test_function()
{
        ..
}

static void __init selftest(void)
{
        KSTM_CHECK_ZERO(do_test_case("", 0));
}

KSTM_MODULE_LOADERS(test_foo);
MODULE_AUTHOR("John Developer <jd@fooman.org>");
MODULE_LICENSE("GPL");
MODULE_INFO(test, "Y");
```

示例测试脚本
------------

```sh
#!/bin/bash
# SPDX-License-Identifier: GPL-2.0+
$(dirname $0)/../kselftest/module.sh "foo" test_foo
```

测试框架
========

`kselftest_harness.h` 文件包含用于构建测试的有用辅助函数。测试框架用于用户空间测试，对于内核空间测试，请参见上面的“测试模块”部分。
`tools/testing/selftests/seccomp/seccomp_bpf.c` 中的测试可以用作示例。

示例
----

```c
// 示例代码片段
```

辅助函数
--------

```c
TH_LOG TEST TEST_SIGNAL FIXTURE FIXTURE_DATA FIXTURE_SETUP FIXTURE_TEARDOWN TEST_F TEST_HARNESS_MAIN FIXTURE_VARIANT FIXTURE_VARIANT_ADD
```

运算符
-------

```c
ASSERT_EQ ASSERT_NE ASSERT_LT ASSERT_LE ASSERT_GT ASSERT_GE ASSERT_NULL ASSERT_TRUE ASSERT_FALSE ASSERT_STREQ ASSERT_STRNE EXPECT_EQ EXPECT_NE EXPECT_LT EXPECT_LE EXPECT_GT EXPECT_GE EXPECT_NULL EXPECT_TRUE EXPECT_FALSE EXPECT_STREQ EXPECT_STRNE
```
