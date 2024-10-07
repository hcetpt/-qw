SPDX 许可证标识符：GPL-2.0

测试
====

本文档包含有关如何测试内核中 Rust 代码的有用信息。
有三种类型的测试：

- KUnit 测试
- ``#[test]`` 测试
- Kselftests

KUnit 测试
----------

这些测试来自 Rust 文档中的示例。它们会被转换为 KUnit 测试。

用法
*****

这些测试可以通过 KUnit 运行。例如，通过命令行使用 ``kunit_tool``（即 ``kunit.py``）来运行测试：

	./tools/testing/kunit/kunit.py run --make_options LLVM=1 --arch x86_64 --kconfig_add CONFIG_RUST=y

或者，KUnit 可以在启动时将它们作为内建模块运行。关于通用的 KUnit 文档，请参阅 `Documentation/dev-tools/kunit/index.rst`；关于内建模块与命令行测试的详细信息，请参阅 `Documentation/dev-tools/kunit/architecture.rst`。

要使用这些 KUnit 文档测试，必须启用以下配置项：

- `CONFIG_KUNIT`
  内核黑客 -> 内核测试和覆盖率 -> KUnit - 启用单元测试支持
- `CONFIG_RUST_KERNEL_DOCTESTS`
  内核黑客 -> Rust 黑客 -> `kernel` 包的文档测试

在内核配置系统中。

KUnit 测试是文档测试
***************************

这些文档测试通常是任何项目（例如函数、结构体、模块等）使用的示例。
它们非常方便，因为它们就写在文档旁边。例如：

.. code-block:: rust

	/// 求两个数之和
```rust
/// ```
/// assert_eq!(mymod::f(10, 20), 30);
/// ```
pub fn f(a: i32, b: i32) -> i32 {
    a + b
}

// 在用户空间中，测试通过 `rustdoc` 收集和运行。使用该工具已经很有用，因为它允许验证示例是否能够编译（从而确保它们与所记录的代码保持同步），并运行那些不依赖内核API的示例。
// 然而，对于内核来说，这些测试会被转换为 KUnit 测试套件。这意味着文档测试会被编译为 Rust 内核对象，允许它们针对已构建的内核运行。
// KUnit 集成的一个好处是，Rust 文档测试可以复用现有的测试设施。例如，内核日志看起来像这样：

KTAP version 1
1..1
    KTAP version 1
    # 子测试：rust_doctests_kernel
    1..59
    # rust_doctest_kernel_build_assert_rs_0.location: rust/kernel/build_assert.rs:13
    ok 1 rust_doctest_kernel_build_assert_rs_0
    # rust_doctest_kernel_build_assert_rs_1.location: rust/kernel/build_assert.rs:56
    ok 2 rust_doctest_kernel_build_assert_rs_1
    # rust_doctest_kernel_init_rs_0.location: rust/kernel/init.rs:122
    ok 3 rust_doctest_kernel_init_rs_0
    ..
# rust_doctest_kernel_types_rs_2.location: rust/kernel/types.rs:150
    ok 59 rust_doctest_kernel_types_rs_2
# rust_doctests_kernel: pass:59 fail:0 skip:0 total:59
# 总计：pass:59 fail:0 skip:0 total:59
ok 1 rust_doctests_kernel

// 使用 `? <https://doc.rust-lang.org/reference/expressions/operator-expr.html#the-question-mark-operator>`_ 操作符的测试也如常支持，例如：

.. code-block:: rust

    /// ```
    /// # use kernel::{spawn_work_item, workqueue};
    /// spawn_work_item!(workqueue::system(), || pr_info!("x"))?;
    /// # Ok::<(), Error>(())
    /// ```

// 测试同样在 ``CLIPPY=1`` 下使用 Clippy 编译，就像正常的代码一样，因此也能从额外的 linting 中受益。
// 为了方便开发人员看到哪一行文档测试代码导致了失败，在日志中打印了一条包含原始测试位置（文件和行号）的 KTAP 诊断信息（而不是生成的 Rust 文件中的位置）：

    # rust_doctest_kernel_types_rs_2.location: rust/kernel/types.rs:150

// Rust 测试似乎使用 Rust 标准库（``core``）中的常规 ``assert!`` 和 ``assert_eq!`` 宏来断言。我们提供了一个自定义版本，将调用转发给 KUnit。重要的是，这些宏不需要传递上下文，不像 KUnit 测试所需的（即 ``struct kunit *``）。这使得它们更易于使用，并且文档的读者不需要关心使用的测试框架。此外，它可能允许我们在未来更容易地测试第三方代码。
// 当前的一个限制是 KUnit 不支持其他任务中的断言。因此，如果断言确实失败，我们现在只是向内核日志打印一个错误。此外，不运行非公共函数的文档测试。
// ``#[test]`` 测试
// 另外还有一些 ``#[test]`` 测试。这些可以通过 ``rusttest`` Make 目标来运行：

make LLVM=1 rusttest

// 这需要内核的 ``.config`` 并下载外部仓库。它在主机上运行 ``#[test]`` 测试（目前），因此这些测试所能测试的内容相当有限。
```
Kselftests
--------------

Kselftests 也可在 ``tools/testing/selftests/rust`` 文件夹中找到。
测试所需的内核配置选项列在 ``tools/testing/selftests/rust/config`` 文件中，可以借助 ``merge_config.sh`` 脚本来包含这些配置选项::

	./scripts/kconfig/merge_config.sh .config tools/testing/selftests/rust/config

Kselftests 在内核源代码树中构建，并旨在在一个运行相同内核的系统上执行。
一旦安装并启动了与源代码树匹配的内核，就可以使用以下命令编译和执行测试::

	make TARGETS="rust" kselftest

有关 Kselftests 的一般文档，请参阅 Documentation/dev-tools/kselftest.rst
