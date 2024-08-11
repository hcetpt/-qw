KUnit 架构
==================

KUnit 架构分为两个部分：

- `内核测试框架`_
- `kunit_tool（命令行测试驱动程序）`_

内核测试框架
===========================

内核测试库支持使用 KUnit 编写的 C 语言 KUnit 测试。这些 KUnit 测试是内核代码的一部分。KUnit 执行以下任务：

- 组织测试
- 报告测试结果
- 提供测试工具

测试用例
----------

测试用例是 KUnit 中的基本单元。KUnit 的测试用例被组织到套件中。一个 KUnit 测试用例是一个类型为 ``void (*)(struct kunit *test)`` 的函数。这些测试用例函数被封装在一个名为 `struct kunit_case` 的结构体中。
.. note::
   对于非参数化测试，“generate_params” 是可选的
每个 KUnit 测试用例都会接收一个 ``struct kunit`` 上下文对象，用于跟踪正在运行的测试。KUnit 断言宏和其他 KUnit 工具会使用这个 ``struct kunit`` 上下文对象。例外的是有两个字段：

- ``->priv``：设置函数可以使用它来存储任意测试用户数据
- ``->param_value``：它包含了可以在参数化测试中获取的参数值
测试套件
-----------

一个 KUnit 套件包括一系列测试用例。KUnit 套件由 `struct kunit_suite` 表示。例如：

.. code-block:: c

    static struct kunit_case example_test_cases[] = {
        KUNIT_CASE(example_test_foo),
        KUNIT_CASE(example_test_bar),
        KUNIT_CASE(example_test_baz),
        {}
    };

    static struct kunit_suite example_test_suite = {
        .name = "example",
        .init = example_test_init,
        .exit = example_test_exit,
        .test_cases = example_test_cases,
    };
    kunit_test_suite(example_test_suite);

在上面的例子中，测试套件 ``example_test_suite`` 运行测试用例 ``example_test_foo``、``example_test_bar`` 和 ``example_test_baz``。在运行测试之前调用 ``example_test_init`` 并且在运行测试之后调用 ``example_test_exit``。``kunit_test_suite(example_test_suite)`` 将测试套件注册到 KUnit 测试框架。
执行器
--------

KUnit 执行器可以在启动时列出并运行内置的 KUnit 测试
测试套件被存储在名为 ``.kunit_test_suites`` 的链接器段中。有关代码，请参阅 `include/asm-generic/vmlinux.lds.h <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/include/asm-generic/vmlinux.lds.h?h=v6.0#n950>`_ 中的 ``KUNIT_TABLE()`` 宏定义
链接器段由指向 `struct kunit_suite` 的指针数组组成，并通过 ``kunit_test_suites()`` 宏填充。KUnit 执行器遍历该链接器段数组以运行所有编译到内核中的测试
.. kernel-figure:: kunit_suitememorydiagram.svg
	:alt: KUnit 套件内存

	KUnit 套件内存图

在内核启动时，KUnit 执行器使用该段的开始和结束地址来遍历并运行所有测试。有关执行器的实现，请参阅 `lib/kunit/executor.c <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/lib/kunit/executor.c>`_
当作为模块构建时，`kunit_test_suites()` 宏定义了一个 `module_init()` 函数，该函数运行编译单元中的所有测试，而不是使用执行器。

在 KUnit 测试中，某些错误类别不会影响其他测试或内核的其他部分；每个 KUnit 用例都在单独的线程上下文中执行。请参阅 `lib/kunit/try-catch.c <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/lib/kunit/try-catch.c?h=v5.15#n58>`_ 中的 `kunit_try_catch_run()` 函数。

### 断言宏

KUnit 测试通过期望值/断言来验证状态。
所有期望值/断言都格式化为：`KUNIT_{EXPECT|ASSERT}_<op>[_MSG](kunit, 属性[, 消息])`

- `{EXPECT|ASSERT}` 确定检查是断言还是期望。
在失败的情况下，测试流程有所不同：

- 对于期望值，测试被标记为失败并且记录了失败。
- 而失败的断言则导致测试用例立即终止。
- 断言调用函数：
    `void __noreturn __kunit_abort(struct kunit *)`
- `__kunit_abort` 调用函数：
    `void __noreturn kunit_try_catch_throw(struct kunit_try_catch *try_catch)`
- `kunit_try_catch_throw` 调用函数：
    `void kthread_complete_and_exit(struct completion *, long) __noreturn;`
并终止特殊线程上下文。
- `<op>` 表示带有选项的检查：`TRUE`（提供的属性具有布尔值 "true"）、`EQ`（两个提供的属性相等）、`NOT_ERR_OR_NULL`（提供的指针不为空且不包含 "err" 值）。
```[_MSG]```在失败时打印自定义消息。

测试结果报告
---------------------
KUnit 以 KTAP 格式打印测试结果。KTAP 基于 TAP14，详情请参阅
`Documentation/dev-tools/ktap.rst`
KTAP 与 KUnit 和 Kselftest 兼容。KUnit 执行器将 KTAP 结果打印到
dmesg 中，以及 debugfs（如果已配置）。

参数化测试
-------------------

每个 KUnit 参数化测试都与一组参数相关联。该测试会被多次调用，每次使用一个不同的参数值，并且该参数被存储在 `param_value` 字段中。
测试案例包括一个 `KUNIT_CASE_PARAM()` 宏，接受一个生成器函数。生成器函数接收前一个参数并返回下一个参数。它还包括一个用于生成基于数组的常见情况生成器的宏。

kunit_tool（命令行测试框架）
======================================

`kunit_tool` 是一个 Python 脚本，位于 `tools/testing/kunit/kunit.py`。它用于配置、构建、执行、解析测试结果以及按正确顺序运行所有上述命令（即配置、构建、执行和解析）。
您可以选择两种方式来运行 KUnit 测试：一种是启用 KUnit 构建内核并手动解析结果（详情请参阅
`Documentation/dev-tools/kunit/run_manual.rst`），另一种是使用 `kunit_tool`（详情请参阅
`Documentation/dev-tools/kunit/run_wrapper.rst`）。

- `configure` 命令从 `.kunitconfig` 文件（及任何架构特定选项）生成内核的 `.config` 文件
位于 `qemu_configs` 文件夹中的 Python 脚本
  （例如，`tools/testing/kunit/qemu_configs/powerpc.py`）包含针对特定架构的附加配置选项
它会解析现有的 `.config` 文件和 `.kunitconfig` 文件
  以确保 `.config` 文件是 `.kunitconfig` 文件的超集。```
如果不适用，则会将两者合并并运行 `make olddefconfig` 来重新生成 `.config` 文件。然后检查 `.config` 是否已成为一个超集。
这验证了所有的 Kconfig 依赖项是否在文件 `.kunitconfig` 中正确指定。`kunit_config.py` 脚本包含了解析 Kconfigs 的代码。运行 `make olddefconfig` 的代码是 `kunit_kernel.py` 脚本的一部分。你可以通过以下命令调用它：`./tools/testing/kunit/kunit.py config`，并生成一个 `.config` 文件。
- `build` 命令使用所需选项（取决于架构和某些选项，例如：build_dir）对内核树运行 `make` 并报告任何错误
要从当前的 `.config` 构建一个 KUnit 内核，可以使用 `build` 参数：`./tools/testing/kunit/kunit.py build`
- `exec` 命令直接执行内核结果（使用用户模式 Linux 配置），或通过模拟器如 QEMU 执行。它从日志中读取结果，并通过标准输出（stdout）传递给 `parse` 进行解析
如果你已经构建了一个包含内置 KUnit 测试的内核，可以运行内核并显示测试结果，使用 `exec` 参数：`./tools/testing/kunit/kunit.py exec`
- `parse` 从内核日志中提取 KTAP 输出，解析测试结果，并打印摘要。对于失败的测试，将包括任何诊断输出
