SPDX 许可证标识符: GPL-2.0

编码指南
=================

本文件描述了如何在内核中编写 Rust 代码。

样式与格式
------------------

代码应当使用 `rustfmt` 进行格式化。这样，偶尔为内核贡献代码的人不需要学习和记住额外的风格指南。更重要的是，审查者和维护者不需要花费时间指出样式问题，因此修改补丁以完成更改所需的时间可能会减少。
注意：注释和文档的约定不会被 `rustfmt` 检查。因此这些仍然需要处理。
使用 `rustfmt` 的默认设置。这意味着遵循惯用的 Rust 风格。例如，使用四个空格进行缩进而不是制表符。
让编辑器 / IDE 在输入时、保存时或提交时自动格式化是很方便的。但是，如果出于某种原因需要重新格式化整个内核的 Rust 源代码，则可以运行以下命令：

```
make LLVM=1 rustfmt
```

也可以检查所有内容是否已格式化（否则打印差异），例如对于持续集成(CI)，可以运行：

```
make LLVM=1 rustfmtcheck
```

就像 `clang-format` 对于内核其他部分一样，`rustfmt` 可以单独处理文件，并且不需要内核配置。有时它甚至可以在代码有错误的情况下工作。

注释
--------

“普通”注释（即 ``//``，而非以 ``///`` 或 ``//!`` 开头的代码文档）应像文档注释那样写成 Markdown 格式，即使它们不会被渲染。这提高了一致性，简化了规则，并允许更轻松地在这两种类型的注释之间移动内容。例如：

```rust
// `object` 现在可以被处理了
f(object);
```

此外，正如文档一样，注释在句子开头要大写，并以句号结尾（即使它只是一个句子）。这包括 ``// SAFETY:``、``// TODO:`` 和其他“标记”的注释，例如：

```rust
// FIXME: 应该妥善处理这个错误
```

注释不应用于文档目的：注释是用于实现细节，而不是用户。即使源文件的读者既是实现者又是 API 用户，这种区分也是有用的。实际上，有时候同时使用注释和文档是有帮助的。例如，为了列出待办事项或者对文档本身进行评论。对于后者，注释可以插入中间；也就是说，更接近要注释的文档行。对于任何其他情况，注释都写在文档之后，例如：

```rust
/// 返回一个新的 [`Foo`]
```
```rust
/// # 示例
///
/// 待办事项：找到一个更好的示例
/// 
/// ``` 
///     let foo = f(42);
/// ```
/// 需修复：使用可失败的方法
pub fn f(x: i32) -> Foo {
    // ...
}

一种特殊的注释是 ``// SAFETY:`` 注释。这些注释必须出现在每个 ``unsafe`` 块之前，并解释为什么块内的代码是正确的/合理的，即为什么在任何情况下都不会触发未定义行为，例如：

.. code-block:: rust

    // SAFETY: `p` 符合安全要求
    unsafe { *p = 0; }

``// SAFETY:`` 注释不应与代码文档中的 ``# Safety`` 部分混淆。``# Safety`` 部分指定了调用者（对于函数）或实现者（对于特质）需要遵守的契约。``// SAFETY:`` 注释展示了为什么一个调用（对于函数）或实现（对于特质）实际上遵循了 ``# Safety`` 部分或语言参考中声明的前提条件。

### 代码文档

Rust 内核代码不像 C 内核代码那样进行文档说明（即通过 kernel-doc）。相反，通常用于记录 Rust 代码的系统被采用：``rustdoc`` 工具，它使用 Markdown（一种轻量级标记语言）。
要学习 Markdown，有很多可用的指南。例如，可以参考：

    https://commonmark.org/help/

以下是一个文档良好的 Rust 函数示例：

.. code-block:: rust

    /// 返回包含的 [`Some`] 值，消耗 `self` 值，
    /// 不检查值是否不是 [`None`]
    ///
    /// # 安全性
    ///
    /// 在 [`None`] 上调用此方法是 *[未定义行为]*
    ///
    /// [未定义行为]: https://doc.rust-lang.org/reference/behavior-considered-undefined.html
    ///
    /// # 示例
    ///
    /// ```
    /// let x = Some("air");
    /// assert_eq!(unsafe { x.unwrap_unchecked() }, "air");
    /// ```
    pub unsafe fn unwrap_unchecked(self) -> T {
        match self {
            Some(val) => val,

            // SAFETY: 调用者必须遵守安全性契约
        }
    }
```
```rust
None => unsafe { hint::unreachable_unchecked() },
}
}

这个示例展示了几个 ``rustdoc`` 功能以及内核遵循的一些约定：

  - 第一段必须是一句话，简要描述所记录项的功能。进一步的解释应放在额外的段落中。
  - 不安全的函数必须在 ``# Safety`` 部分中记录其安全性前提条件。
  - 虽然这里没有展示，如果一个函数可能会引发恐慌（panic），则应在 ``# Panics`` 部分中描述触发恐慌的条件。
  - 请注意，引发恐慌应该非常罕见，并且只有在有充分理由的情况下才使用。在几乎所有情况下，应使用可失败的方法，通常返回一个 ``Result``。
  - 如果提供用法示例有助于读者理解，则必须写在一个名为 ``# Examples`` 的部分中。
  - Rust 项（函数、类型、常量等）必须适当链接（``rustdoc`` 将自动生成链接）。
  - 任何 ``unsafe`` 块之前必须有一个 ``// SAFETY:`` 注释，描述内部代码为什么是合理的。
  - 即使有时原因看起来微不足道，似乎不需要写注释，但这些注释不仅是记录考虑因素的好方法，更重要的是，它提供了一种方式来确保没有额外的隐式约束。

要了解更多关于如何编写 Rust 文档和附加功能的信息，请参阅 ``rustdoc`` 书籍：

	https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html

此外，内核支持通过在链接目标前加上 ``srctree/`` 来创建相对于源树的链接。例如：

.. code-block:: rust

	//! C 头文件：[`include/linux/printk.h`](srctree/include/linux/printk.h)

或：

.. code-block:: rust

	/// [`struct mutex`]: srctree/include/linux/mutex.h

命名
------

Rust 内核代码遵循常规的 Rust 命名约定：

	https://rust-lang.github.io/api-guidelines/naming.html

当将现有的 C 概念（如宏、函数、对象等）封装到 Rust 抽象中时，应尽可能使用与 C 侧接近的名字，以避免混淆并提高在 C 和 Rust 之间切换时的可读性。例如，C 中的宏如 ``pr_info`` 在 Rust 侧也使用相同的名字。
话虽如此，大小写应调整以遵循 Rust 的命名约定，并且由模块和类型引入的命名空间不应在项名称中重复。例如，封装如下常量时：

.. code-block:: c

	#define GPIO_LINE_DIRECTION_IN	0
	#define GPIO_LINE_DIRECTION_OUT	1

等效的 Rust 代码可能如下所示（忽略文档）：

.. code-block:: rust

	pub mod gpio {
	    pub enum LineDirection {
	        In = bindings::GPIO_LINE_DIRECTION_IN as _,
	        Out = bindings::GPIO_LINE_DIRECTION_OUT as _,
	    }
	}

也就是说，``GPIO_LINE_DIRECTION_IN`` 的等效物应称为 ``gpio::LineDirection::In``。特别地，不应命名为 ``gpio::gpio_line_direction::GPIO_LINE_DIRECTION_IN``。
```
当然，请提供您需要翻译的文本。
