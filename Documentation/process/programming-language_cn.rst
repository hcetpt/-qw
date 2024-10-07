编程语言
====================

内核是用C编程语言编写的 [_c-language]。
更确切地说，内核通常是使用 ``gcc`` [_gcc] 编译的，并且编译选项为 ``-std=gnu11`` [_gcc-c-dialect-options]：即ISO C11的GNU方言。
``clang`` [_clang] 也得到了支持，详见关于 :ref:`使用Clang/LLVM构建Linux <kbuild_llvm>` 的文档。
这种方言包含了许多对语言的扩展 [_gnu-extensions]，并且其中许多扩展在内核中被常规地使用。
属性
----------

在整个内核中常用的一个扩展就是属性 [_gcc-attribute-syntax]。属性允许为语言实体（如变量、函数或类型）引入实现定义的语义，而无需对语言进行重大语法更改（例如添加新关键字）[_n2049]。
在某些情况下，属性是可选的（即不支持它们的编译器仍应生成正确的代码，即使速度较慢或不能执行尽可能多的编译时检查/诊断）。
内核定义了伪关键字（如 ``__pure``），而不是直接使用GNU属性语法（如 ``__attribute__((__pure__))``），以便检测哪些功能可以使用和/或缩短代码。
请参阅 ``include/linux/compiler_attributes.h`` 获取更多信息。
Rust
----

内核在 ``CONFIG_RUST`` 下实验性地支持Rust编程语言 [_rust-language]。它使用 ``rustc`` [_rustc] 编译，并且编译选项为 ``--edition=2021`` [_rust-editions]。版本是一种引入不向后兼容的小改动的方法。
除此之外，内核还使用了一些不稳定的功能 [_rust-unstable-features]。由于不稳定的功能将来可能会改变，因此达到只使用稳定功能的目标非常重要。
请参阅Documentation/rust/index.rst以获取更多信息
.. [c语言] http://www.open-std.org/jtc1/sc22/wg14/www/standards
.. [gcc] https://gcc.gnu.org
.. [clang] https://clang.llvm.org
.. [gcc-c方言选项] https://gcc.gnu.org/onlinedocs/gcc/C-Dialect-Options.html
.. [GNU扩展] https://gcc.gnu.org/onlinedocs/gcc/C-Extensions.html
.. [gcc属性语法] https://gcc.gnu.org/onlinedocs/gcc/Attribute-Syntax.html
.. [n2049] http://www.open-std.org/jtc1/sc22/wg14/www/docs/n2049.pdf
.. [Rust语言] https://www.rust-lang.org
.. [rustc] https://doc.rust-lang.org/rustc/
.. [Rust版本] https://doc.rust-lang.org/edition-guide/editions/
.. [Rust不稳定特性] https://github.com/Rust-for-Linux/linux/issues/2
