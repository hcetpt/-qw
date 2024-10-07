SPDX 许可证标识符: GPL-2.0

Rust
====

内核中与 Rust 相关的文档。要开始在内核中使用 Rust，请阅读 quick-start.rst 指南。
Rust 实验
--------------

Rust 支持在 v6.1 版本中合并到主线，以帮助确定 Rust 语言是否适合内核，即是否值得进行权衡。

目前，Rust 支持主要针对对 Rust 支持感兴趣的内核开发者和维护者，以便他们可以开始编写抽象和驱动程序，并帮助基础设施和工具的开发。

如果你是最终用户，请注意当前内核树中没有适合或打算用于生产环境的驱动程序/模块，并且 Rust 支持仍在开发/实验阶段，特别是在某些内核配置下。

.. only:: rustdoc 和 html

    你也可以浏览 `rustdoc 文档 <rustdoc/kernel/index.html>`_。

.. only:: 不是 rustdoc 和 html

    此文档不包括由 rustdoc 生成的信息。

.. toctree::
    :maxdepth: 1

    quick-start
    general-information
    coding-guidelines
    arch-support
    testing

.. only:: 子项目 和 html

   索引
   ======

   * :ref:`genindex`
