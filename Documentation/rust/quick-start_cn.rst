SPDX 许可证标识符: GPL-2.0

快速入门
-----------

本文档描述了如何开始使用 Rust 进行内核开发。

要求：构建
--------------

本节解释了如何获取用于构建所需的工具。
某些需求可能在 Linux 发行版中以如 ``rustc``、``rust-src``、``rust-bindgen`` 等名称提供。但是，截至撰写时，除非发行版跟踪最新版本，否则这些工具可能不够新。
为了轻松检查是否满足要求，可以使用以下目标：

```shell
make LLVM=1 rustavailable
```

这会触发 Kconfig 用来确定是否启用 ``RUST_IS_AVAILABLE`` 的相同逻辑；同时如果未启用也会解释原因。

rustc
******

需要特定版本的 Rust 编译器。较新版本可能或可能不适用，因为目前内核依赖于一些不稳定的 Rust 特性。
如果使用 ``rustup``，进入内核构建目录（或使用 ``--path=<build-dir>`` 参数给 ``set`` 子命令），然后运行：

```shell
rustup override set $(scripts/min-tool-version.sh rustc)
```

这将配置您的工作目录使用正确的 ``rustc`` 版本而不影响默认工具链。
请注意，覆盖仅适用于当前工作目录（及其子目录）。
如果不使用 ``rustup``，可以从以下网址获取独立安装程序：

```
https://forge.rust-lang.org/infra/other-installation-methods.html#standalone
```

Rust 标准库源码
************************

需要 Rust 标准库源码，因为构建系统会交叉编译 ``core`` 和 ``alloc``。
如果使用 ``rustup``，运行：

```shell
rustup component add rust-src
```

组件是按工具链安装的，因此升级 Rust 编译器版本后需要重新添加该组件。
否则，如果使用独立安装程序，可以将 Rust 源代码下载到工具链的安装文件夹中：

```shell
curl -L "https://static.rust-lang.org/dist/rust-src-$(scripts/min-tool-version.sh rustc).tar.gz" | 
	tar -xzf - -C "$(rustc --print sysroot)/lib" \
		"rust-src-$(scripts/min-tool-version.sh rustc)/rust-src/lib/" \
		--strip-components=3
```

在这种情况下，以后升级 Rust 编译器版本需要手动更新源代码树（可以通过删除 ``$(rustc --print sysroot)/lib/rustlib/src/rust`` 然后重新运行上述命令来完成）。
``libclang``（作为LLVM的一部分）被``bindgen``用来理解内核中的C代码，这意味着需要安装LLVM；就像在编译内核时设置``LLVM=1``一样。
Linux发行版可能已经有合适的版本可用，因此最好先检查一下。
也有一些针对不同系统和架构的二进制文件上传到了：

    https://releases.llvm.org/download.html

否则，构建LLVM需要相当长的时间，但这不是一个复杂的过程：

    https://llvm.org/docs/GettingStarted.html#getting-the-source-code-and-building-llvm

请参阅Documentation/kbuild/llvm.rst以获取更多信息以及获取预构建版本和发行包的方法。
bindgen
*******

内核中C部分的绑定是在构建时使用``bindgen``工具生成的。需要特定版本的bindgen。
通过以下命令安装它（注意这将从源码下载并构建该工具）：

    cargo install --locked --version $(scripts/min-tool-version.sh bindgen) bindgen-cli

``bindgen``需要找到合适的``libclang``才能正常工作。如果找不到（或者需要使用另一个``libclang``），可以通过调整环境变量来解决，这些环境变量是``clang-sys``（``bindgen``用来访问``libclang``的Rust绑定包）所理解的：

* 可以将``LLVM_CONFIG_PATH``指向一个``llvm-config``可执行文件
* 或者可以将``LIBCLANG_PATH``指向一个``libclang``共享库或包含它的目录
* 或者可以将``CLANG_PATH``指向一个``clang``可执行文件
详细信息，请参阅``clang-sys``的文档：

    https://github.com/KyleMayes/clang-sys#environment-variables

要求：开发
------------------------

本节解释了如何获取开发所需的工具。也就是说，在仅编译内核时不需要这些工具。
rustfmt
*******

``rustfmt``工具用于自动格式化所有Rust内核代码，包括生成的C绑定（详细信息请参见coding-guidelines.rst）。
如果使用的是``rustup``，其``default``配置文件已经安装了该工具，因此无需额外操作。如果使用的是其他配置文件，则可以手动安装该组件：

    rustup component add rustfmt

独立安装程序也包含了``rustfmt``。
``clippy`` 是一个 Rust 代码检查工具。运行它可以为 Rust 代码提供额外的警告。
可以通过向 `make` 传递 `CLIPPY=1` 来运行它（详细信息请参见 general-information.rst）。
如果使用了 `rustup`，其默认配置已经安装了该工具，因此无需额外操作。如果使用了其他配置，则可以手动安装该组件：

```bash
rustup component add clippy
```

独立安装程序也包含了 `clippy`。

cargo
*****

``cargo`` 是 Rust 的原生构建系统。目前，运行测试需要使用它，因为它用于构建包含内核中自定义 `alloc` 提供的功能的自定义标准库。可以使用 `rusttest` Make 目标来运行测试。
如果使用了 `rustup`，所有配置都已经安装了该工具，因此无需额外操作。
独立安装程序也包含了 `cargo`。

rustdoc
*******

``rustdoc`` 是 Rust 的文档生成工具。它可以为 Rust 代码生成漂亮的 HTML 文档（详细信息请参见 general-information.rst）。
``rustdoc`` 还用于测试文档注释中的示例（称为 doctest 或文档测试）。`rusttest` Make 目标使用了这一特性。
如果使用了 `rustup`，所有配置都已经安装了该工具，因此无需额外操作。
独立安装程序也包含了 `rustdoc`。
### rust-analyzer

`rust-analyzer <https://rust-analyzer.github.io/>`_ 语言服务器可以与多种编辑器配合使用，以实现语法高亮、自动补全、跳转到定义等功能。`rust-analyzer` 需要一个配置文件 `rust-project.json`，该文件可以通过以下命令生成：

```sh
make LLVM=1 rust-analyzer
```

#### 配置

需要在“基本设置”菜单中启用“Rust 支持”（`CONFIG_RUST`）。只有在找到合适的 Rust 工具链时（见上文），并且满足其他要求时，才会显示这个选项。之后，将显示依赖于 Rust 的其他选项。

接下来，请进入：

```
内核黑客
    -> 示例内核代码
        -> Rust 示例
```

并启用一些示例模块，既可以作为内置模块也可以作为可加载模块。

#### 构建

目前，使用完整的 LLVM 工具链构建内核是最受支持的配置。具体步骤如下：

```sh
make LLVM=1
```

对于某些配置，使用 GCC 也是可行的，但目前还非常实验性。

#### 黑客开发

为了更深入地研究，可以查看位于 `samples/rust/` 的示例源代码、位于 `rust/` 的 Rust 支持代码以及位于“内核黑客”菜单下的“Rust 黑客”。

如果使用 GDB/Binutils 并且 Rust 符号没有正确反混淆，原因可能是工具链尚不支持 Rust 的新 v0 命名方案。有几种解决方法：

- 安装更新的版本（GDB >= 10.2，Binutils >= 2.36）
- 某些版本的 GDB（例如原版 GDB 10.1）能够使用嵌入调试信息中的预反混淆名称（`CONFIG_DEBUG_INFO`）
