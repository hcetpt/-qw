SPDX 许可证标识符: GPL-2.0

============================
运行 KUnit 测试的小贴士
============================

使用 `kunit.py run` ("kunit 工具")
=====================================

从任何目录运行
--------------------------

创建一个 bash 函数可能会很方便，例如：

.. 代码块:: bash

    function run_kunit() {
      ( cd "$(git rev-parse --show-toplevel)" && ./tools/testing/kunit/kunit.py run "$@" )
    }

.. 注意::
    早期版本的 `kunit.py`（5.6 之前）除非从内核根目录运行否则不起作用，因此使用子 shell 和 `cd`
仅运行一部分测试
-------------------------

`kunit.py run` 接受一个可选的 glob 参数来过滤测试。格式为 `"<suite_glob>[.test_glob]"`。
假设我们想要运行 sysctl 测试，我们可以这样做：

.. 代码块:: bash

    $ echo -e 'CONFIG_KUNIT=y\nCONFIG_KUNIT_ALL_TESTS=y' > .kunit/.kunitconfig
    $ ./tools/testing/kunit/kunit.py run 'sysctl*'

我们可以通过以下方式进一步过滤到仅 "write" 测试：

.. 代码块:: bash

    $ echo -e 'CONFIG_KUNIT=y\nCONFIG_KUNIT_ALL_TESTS=y' > .kunit/.kunitconfig
    $ ./tools/testing/kunit/kunit.py run 'sysctl*.*write*'

这样我们付出了构建多余测试的成本，但这比摆弄 `.kunitconfig` 文件或注释掉 `kunit_suite` 更容易。
然而，如果我们想以一种更非临时的方式定义一组测试，下一个提示会很有用。
定义一组测试
-------------------------

`kunit.py run`（以及 `build` 和 `config`）支持 `--kunitconfig` 标志。所以如果你有一组你想定期运行的测试（特别是如果它们有其他依赖项），你可以为它们创建一个特定的 `.kunitconfig`。

例如，KUnit 有一个用于其测试的配置文件：

.. 代码块:: bash

    $ ./tools/testing/kunit/kunit.py run --kunitconfig=lib/kunit/.kunitconfig

或者，如果你遵循将文件命名为 `.kunitconfig` 的约定，则只需传递目录名即可，例如：

.. 代码块:: bash

    $ ./tools/testing/kunit/kunit.py run --kunitconfig=lib/kunit

.. 注意::
    这是一个相对较新的功能（5.12+），所以我们还没有关于哪些文件应该被提交，哪些只保留在本地的约定。由你和你的维护者决定某个配置是否有用到足以提交（并因此必须维护）。
.. 注意::
    在父目录和子目录中都有 `.kunitconfig` 片段是不确定的。有关于在这些文件中添加 "import" 语句的讨论，以便可以有一个顶层配置来运行所有子目录中的测试。但这意味着 `.kunitconfig` 文件不再仅仅是简单的 `.config` 片段。
    一个替代方案是让 kunit 工具自动递归地组合配置，但理论上测试可能依赖于不兼容的选项，因此处理这种情况会很棘手。
设置内核命令行参数
-------------------------------------

你可以使用 `--kernel_args` 来传递任意内核参数，例如：
使用以下命令运行 KUnit 测试，并设置内核参数 `param=42` 和 `param2=false`：

```bash
$ ./tools/testing/kunit/kunit.py run --kernel_args=param=42 --kernel_args=param2=false
```

在 UML 下生成代码覆盖率报告
------------------------------------------

.. note::
   TODO(brendanhiggins@google.com): UML 和 GCC 7 及以上版本存在一些问题。您可能会遇到缺少 `.gcda` 文件或编译错误的情况。
这与在 `Documentation/dev-tools/gcov.rst` 中记录的获取覆盖率信息的“正常”方式不同。
而不是启用 `CONFIG_GCOV_KERNEL=y`，我们可以设置如下选项：

```none
CONFIG_DEBUG_KERNEL=y
CONFIG_DEBUG_INFO=y
CONFIG_DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT=y
CONFIG_GCOV=y
```

将这些组合成一个可复制粘贴的命令序列：

```bash
# 向当前配置追加覆盖率选项
$ ./tools/testing/kunit/kunit.py run --kunitconfig=.kunit/ --kunitconfig=tools/testing/kunit/configs/coverage_uml.config
# 从构建目录 (.kunit/) 提取覆盖率信息
$ lcov -t "my_kunit_tests" -o coverage.info -c -d .kunit/

# 从这里开始，过程与 `CONFIG_GCOV_KERNEL=y` 相同
# 例如，可以这样在临时目录中生成 HTML 报告：
$ genhtml -o /tmp/coverage_html coverage.info
```

如果已安装的 GCC 版本不起作用，您可以调整步骤：

```bash
$ ./tools/testing/kunit/kunit.py run --make_options=CC=/usr/bin/gcc-6
$ lcov -t "my_kunit_tests" -o coverage.info -c -d .kunit/ --gcov-tool=/usr/bin/gcov-6
```

或者，也可以使用基于 LLVM 的工具链：

```bash
# 使用 LLVM 构建并追加覆盖率选项到当前配置
$ ./tools/testing/kunit/kunit.py run --make_options LLVM=1 --kunitconfig=.kunit/ --kunitconfig=tools/testing/kunit/configs/coverage_uml.config
$ llvm-profdata merge -sparse default.profraw -o default.profdata
$ llvm-cov export --format=lcov .kunit/vmlinux -instr-profile default.profdata > coverage.info
# `coverage.info` 文件是 lcov 兼容格式，可用于生成 HTML 报告等
$ genhtml -o /tmp/coverage_html coverage.info
```

手动运行测试
=============

不使用 `kunit.py run` 运行测试也是一个重要的使用案例。
目前，如果您想要在非 UML 架构上进行测试，这是您唯一的选择。
由于在 UML 下运行测试相对直接（配置和编译内核，运行 `./linux` 二进制文件），本节将专注于非 UML 架构上的测试。

运行内置测试
--------------

当将测试设置为 `=y` 时，这些测试将在启动过程中运行并将结果以 TAP 格式打印到 dmesg 中。因此，您只需将您的测试添加到 `.config` 文件中，像平常一样构建并启动内核即可。
例如，如果我们用以下选项编译内核：

```none
CONFIG_KUNIT=y
CONFIG_KUNIT_EXAMPLE_TEST=y
```

那么我们会在 dmesg 中看到类似这样的输出，表明测试已经运行并通过：

```none
TAP version 14
1..1
    # Subtest: example
    1..1
    # example_simple_test: initializing
    ok 1 - example_simple_test
ok 1 - example
```

作为模块运行测试
------------------------

根据测试的不同，您可以将它们构建为可加载的模块。
例如，我们将之前的配置选项更改为：

```none
CONFIG_KUNIT=y
CONFIG_KUNIT_EXAMPLE_TEST=m
```

然后，在引导进入内核后，我们可以通过以下命令运行测试：

```none
$ modprobe kunit-example-test
```

这将导致它向标准输出打印 TAP 输出。
.. note::
   `modprobe` 命令即使有测试失败也不会返回非零退出码（截至 5.13）。但 `kunit.py parse` 会这样做，请参见下文。
.. note::
   您还可以设置 `CONFIG_KUNIT=m`，但是，某些功能将无法工作，因此某些测试可能会失败。理想情况下，测试应该在其 `Kconfig` 文件中指定依赖于 `KUNIT=y`，但这是一种大多数测试作者可能不会考虑的边缘情况。
截至 5.13，唯一的区别是 ``current->kunit_test`` 将不存在。

美化输出结果
--------------

你可以使用 `kunit.py parse` 来解析 dmesg 中的测试输出，并以与 `kunit.py run` 相同的熟悉格式打印出结果。
```bash
$ ./tools/testing/kunit/kunit.py parse /var/log/dmesg
```

获取每个测试套件的结果
------------------------

无论你如何运行你的测试，都可以启用 `CONFIG_KUNIT_DEBUGFS` 来暴露每个套件的 TAP 格式的结果：

```plaintext
CONFIG_KUNIT=y
CONFIG_KUNIT_EXAMPLE_TEST=m
CONFIG_KUNIT_DEBUGFS=y
```

每个套件的结果将被暴露在 `/sys/kernel/debug/kunit/<suite>/results` 下。因此，使用我们的示例配置：

```bash
$ modprobe kunit-example-test > /dev/null
$ cat /sys/kernel/debug/kunit/example/results
... <TAP 输出> ...
# 移除模块后，对应的文件也会消失
$ modprobe -r kunit-example-test
$ cat /sys/kernel/debug/kunit/example/results
/sys/kernel/debug/kunit/example/results: 没有该文件或目录
```

生成代码覆盖率报告
----------------------

有关如何操作的详细信息，请参阅 `Documentation/dev-tools/gcov.rst`。这里唯一与 KUnit 相关的建议是，你可能想要将你的测试作为模块来构建。这样可以将测试的覆盖率与其他在启动期间执行的代码隔离开来，例如：
```bash
# 在运行测试前重置覆盖率计数器
$ echo 0 > /sys/kernel/debug/gcov/reset
$ modprobe kunit-example-test
```

测试属性和过滤
==================

测试套件和案例可以用测试属性标记，如测试的速度。这些属性将在测试输出中打印出来，并可用于过滤测试执行。

标记测试属性
-------------------

通过在测试定义中包含一个 `kunit_attributes` 对象来标记测试属性。使用 `KUNIT_CASE_ATTR(test_name, attributes)` 宏代替 `KUNIT_CASE(test_name)` 来定义带有属性的测试案例。
### 代码块示例

```c
// 定义一个非常慢的测试属性
static const struct kunit_attributes example_attr = {
	.speed = KUNIT_VERY_SLOW,
};

// 使用上面定义的属性设置测试用例
static struct kunit_case example_test_cases[] = {
	KUNIT_CASE_ATTR(example_test, example_attr),
};
```

### 注释
为了标记测试用例为慢速，你也可以使用 `KUNIT_CASE_SLOW(test_name)`。这是一个很有用的宏，因为慢速属性是最常用的。测试套件可以通过在套件定义中设置 "attr" 字段来标记属性。

```c
// 定义一个非常慢的测试属性
static const struct kunit_attributes example_attr = {
	.speed = KUNIT_VERY_SLOW,
};

// 使用上面定义的属性设置测试套件
static struct kunit_suite example_test_suite = {
	...,
	.attr = example_attr,
};
```

### 注释
并非所有属性都需要在一个 `kunit_attributes` 对象中设置。未设置的属性将保持未初始化状态，并且会像属性被设置为 0 或 NULL 一样行为。因此，如果一个属性被设置为 0，则被视为未设置。这些未设置的属性不会被报告，并可能作为过滤目的的默认值。

### 属性报告

当用户运行测试时，属性将在原始内核输出（KTAP 格式）中呈现。请注意，默认情况下，在 kunit.py 输出中，对于所有通过的测试，属性会被隐藏，但可以通过 `--raw_output` 标志访问原始内核输出。以下是测试用例的测试属性如何在内核输出中格式化的示例：

```none
# example_test.speed: slow
ok 1 example_test
```

以下是测试套件的测试属性如何在内核输出中格式化的示例：

```none
  KTAP version 2
  # Subtest: example_suite
  # module: kunit_example_test
  1..3
  ..
ok 1 example_suite
```

此外，用户可以使用命令行标志 `--list_tests_attr` 输出带有其属性的完整测试报告：

```bash
kunit.py run "example" --list_tests_attr
```

### 注释
此报告可以在手动运行 KUnit 时通过传递模块参数 `kunit.action=list_attr` 访问。

### 过滤

用户可以在运行测试时使用命令行标志 `--filter` 来过滤测试。例如：

```bash
kunit.py run --filter speed=slow
```

你还可以对过滤器使用以下操作符："<", ">", "<=", ">=", "!=" 和 "="。示例：

```bash
kunit.py run --filter "speed>slow"
```

此示例将运行所有比“慢”更快的测试。注意，字符 `<` 和 `>` 经常会被 shell 解释，所以可能需要进行引号包围或转义，如上所示。
此外，你可以同时使用多个过滤器。只需用逗号分隔过滤器即可。示例：

```bash
kunit.py run --filter "speed>slow, module=kunit_example_test"
```

### 注释
你可以在手动运行 KUnit 时通过传递过滤器作为模块参数来使用此过滤功能：`kunit.filter="speed>slow, speed<=normal"`。

过滤的测试将不会运行或出现在测试输出中。你可以使用 `--filter_action=skip` 标志来跳过过滤的测试。这些测试会在测试输出中显示，但不会运行。要在手动运行 KUnit 时使用此功能，请使用模块参数 `kunit.filter_action=skip`。
过滤程序的规则
----------------------------

由于测试套件和测试用例都可以具有属性，所以在过滤过程中可能会出现属性冲突。过滤过程遵循以下规则：

- 过滤始终在每个测试的基础上进行。
- 如果一个测试具有设置好的属性，则对该测试的值进行过滤。
- 否则，其值回退到测试套件的值。
- 如果两者都没有设置，则该属性有一个全局的“默认”值，将使用此值。

当前属性列表
--------------------------

`speed`

此属性指示测试执行的速度（测试运行的快慢）。
此属性以枚举形式保存，分为以下几类：“normal”、“slow”或“very_slow”。测试的默认速度假设为“normal”，这表示无论在哪台机器上运行，测试所需的时间相对较少（小于1秒）。比这更慢的任何测试可以标记为“slow”或“very_slow”。
可以通过宏`KUNIT_CASE_SLOW(test_name)`轻松地将测试用例的速度设置为“slow”。

`module`

此属性指示与测试相关的模块名称。
此属性自动以字符串形式保存，并为每个测试套件打印出来。
也可以使用此属性对测试进行过滤。
``is_init``

该属性表示测试是否使用初始化数据或函数。
此属性会自动保存为布尔值，并且也可以使用此属性对测试进行过滤。
