编程语言
====================

内核是用C编程语言编写的\[c-language\]
更确切地说，内核通常使用``gcc``\[gcc\]在``-std=gnu11``\[gcc-c-dialect-options\]下进行编译：即ISO C11的GNU方言
``clang``\[clang\]也得到支持，详情请参阅关于
:ref:`使用Clang/LLVM构建Linux<kbuild_llvm>`的文档
这种方言包含了许多对语言的扩展\[gnu-extensions\]，其中许多扩展在内核中作为常规做法被使用
属性
----------

内核中广泛使用的常见扩展之一是属性
\[gcc-attribute-syntax\]。属性允许为语言实体（如变量、函数或类型）引入实现定义的语义，而无需对语言做出重大的语法更改（例如添加新的关键字）\[n2049\]
在某些情况下，属性是可选的（即不支持它们的编译器仍然应该生成正确的代码，尽管可能较慢或不会执行那么多编译时检查/诊断）
内核定义了伪关键字（例如``__pure``），而不是直接使用GNU属性语法（例如``__attribute__((__pure__))``）
这样做是为了检测哪些特性可以使用和/或简化代码
请参阅``include/linux/compiler_attributes.h``获取更多信息
Rust
----

内核在``CONFIG_RUST``下对Rust编程语言\[rust-language\]提供了实验性支持。它使用``rustc``\[rustc\]在``--edition=2021``\[rust-editions\]下进行编译。版本是引入不向后兼容的小型语言更改的一种方式
除此之外，内核中还使用了一些不稳定特性\[rust-unstable-features\]。不稳定特性将来可能会发生变化，因此一个重要的目标是达到只使用稳定特性的阶段
请参阅 Documentation/rust/index.rst 以获取更多信息。
.. [c语言] http://www.open-std.org/jtc1/sc22/wg14/www/standards
.. [GCC] https://gcc.gnu.org
.. [Clang] https://clang.llvm.org
.. [GCC-C方言选项] https://gcc.gnu.org/onlinedocs/gcc/C-Dialect-Options.html
.. [GNU扩展] https://gcc.gnu.org/onlinedocs/gcc/C-Extensions.html
.. [GCC属性语法] https://gcc.gnu.org/onlinedocs/gcc/Attribute-Syntax.html
.. [n2049] http://www.open-std.org/jtc1/sc22/wg14/www/docs/n2049.pdf
.. [Rust语言] https://www.rust-lang.org
.. [rustc] https://doc.rust-lang.org/rustc/
.. [Rust版本] https://doc.rust-lang.org/edition-guide/editions/
.. [Rust不稳定特性] https://github.com/Rust-for-Linux/linux/issues/2
