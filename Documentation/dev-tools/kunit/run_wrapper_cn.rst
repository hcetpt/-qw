### 使用kunit_tool运行测试

=============================
通过kunit_tool运行测试
=============================

我们既可以使用kunit_tool来运行KUnit测试，也可以手动运行测试，然后再使用kunit_tool解析结果。要手动运行测试，请参阅：Documentation/dev-tools/kunit/run_manual.rst
只要我们可以构建内核，我们就可以运行KUnit。
kunit_tool是一个Python脚本，它可以配置和构建内核、运行测试，并格式化测试结果。
运行命令：

.. code-block::

	./tools/testing/kunit/kunit.py run

我们应该看到以下内容：

.. code-block::

	配置KUnit内核...
	构建KUnit内核...
	启动KUnit内核...

我们可能需要使用以下选项：

.. code-block::

	./tools/testing/kunit/kunit.py run --timeout=30 --jobs=`nproc --all`

- `--timeout` 设置了测试运行的最大时间
- `--jobs` 设置了构建内核的线程数
如果没有其他`.kunitconfig`文件（在构建目录中），kunit_tool将生成一个默认配置的`.kunitconfig`。
此外，它还会验证生成的`.config`文件是否包含`.kunitconfig`中的`CONFIG`选项。
还可以向kunit_tool传递一个单独的`.kunitconfig`片段。如果我们想要独立运行几组不同的测试，或者想要为某些子系统使用预定义的测试配置，这将非常有用。
使用不同的 ``.kunitconfig`` 文件（例如为了测试某个特定的子系统而提供的文件），可以通过以下方式传递：

.. code-block::

	./tools/testing/kunit/kunit.py run --kunitconfig=fs/ext4/.kunitconfig

要查看 kunit_tool 标志（可选命令行参数），可以运行：

.. code-block::

	./tools/testing/kunit/kunit.py run --help

创建一个 ``.kunitconfig`` 文件
=================================

如果我们想要运行一组特定的测试（而非 KUnit ``defconfig`` 中列出的那些测试），我们可以在 ``.kunitconfig`` 文件中提供 Kconfig 选项。对于默认的 `.kunitconfig`，参见：
https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/kunit/configs/default.config
`.kunitconfig` 是一种 `minconfig`（通过运行 `make savedefconfig` 生成的 `.config`），用于运行一组特定的测试。此文件包含常规内核配置以及特定的测试目标。`.kunitconfig` 还包含由测试所需的任何其他配置选项（例如：测试特性依赖项、启用或禁用某些代码块的配置、架构配置等）。
要创建一个 `.kunitconfig` 文件，可以使用 KUnit 的 `defconfig`：

.. code-block::

	cd $PATH_TO_LINUX_REPO
	cp tools/testing/kunit/configs/default.config .kunit/.kunitconfig

然后我们可以添加任何其他的 Kconfig 选项。例如：

.. code-block::

	CONFIG_LIST_KUNIT_TEST=y

kunit_tool 确保在运行测试之前，`.kunitconfig` 中的所有配置选项都设置在内核的 `.config` 文件中。如果未包含选项依赖项，它会发出警告。
.. note:: 从 `.kunitconfig` 中删除某些内容不会重建 `.config` 文件。只有当 `.kunitconfig` 不是 `.config` 的子集时，配置才会更新。
这意味着我们可以使用其他工具（例如：`make menuconfig`）来调整其他配置选项。
为了让 `make menuconfig` 能够工作，需要为它设置构建目录，因此默认情况下可以使用 `make O=.kunit menuconfig`。
配置、构建和运行测试
===================================

如果我们想手动更改 KUnit 构建过程，可以独立地运行 KUnit 构建过程的一部分。
当从一个 `.kunitconfig` 文件运行 kunit_tool 时，可以使用 `config` 参数生成一个 `.config` 文件：

.. code-block::

	./tools/testing/kunit/kunit.py config

要从当前的 `.config` 构建一个 KUnit 内核，可以使用 `build` 参数：

.. code-block::

	./tools/testing/kunit/kunit.py build

如果我们已经构建了一个内置 KUnit 测试的 UML 内核，可以使用 `exec` 参数运行内核并显示测试结果：

.. code-block::

	./tools/testing/kunit/kunit.py exec

在 **使用 kunit_tool 运行测试** 部分讨论的 `run` 命令相当于依次运行上述三个命令。
解析测试结果
==================

KUnit 测试输出以 TAP（Test Anything Protocol）格式显示结果。运行测试时，kunit_tool 解析这些输出并打印摘要。要查看原始的 TAP 格式的测试结果，可以传递 `--raw_output` 参数：

.. code-block::

	./tools/testing/kunit/kunit.py run --raw_output

如果我们有 KUnit 结果的原始 TAP 格式数据，可以使用 kunit_tool 的 `parse` 命令解析它们并打印人类可读的摘要。这接受一个文件名作为参数，或者从标准输入读取。

.. code-block:: bash

	# 从文件读取
	./tools/testing/kunit/kunit.py parse /var/log/dmesg
	# 从标准输入读取
	dmesg | ./tools/testing/kunit/kunit.py parse

过滤测试
==============

通过向 `exec` 或 `run` 命令传递 Bash 风格的 glob 过滤器，我们可以运行内核中构建的一组子测试。例如：如果我们只想运行 KUnit 资源测试，可以使用：

.. code-block::

	./tools/testing/kunit/kunit.py run 'kunit-resource*'

这里使用了标准的 glob 格式和通配符字符。
### 在 QEMU 上运行测试

`kunit_tool` 支持在 QEMU 以及通过 UML 运行测试。要在 QEMU 上运行测试，默认需要两个标志：

- `--arch`: 选择一组配置（如 Kconfig、QEMU 配置选项等），这些配置允许以最简方式在指定架构上运行 KUnit 测试。架构参数与传递给 Kbuild 中的 `ARCH` 变量的选项名称相同。并非所有架构目前都支持此标志，但我们可以通过 `--qemu_config` 来处理它。如果传入 `um`（或忽略此标志），则测试将通过 UML 运行。非 UML 架构，例如：i386、x86_64、arm 等，在 QEMU 上运行。
- `--cross_compile`: 指定 Kbuild 工具链。它传递与传递给 Kbuild 中的 `CROSS_COMPILE` 变量相同的参数。作为提醒，这将是工具链二进制文件（如 GCC）的前缀。例如：
  - 如果我们在系统上安装了 sparc 工具链，则为 `sparc64-linux-gnu`
  - 如果我们从 0-day 网站下载了 microblaze 工具链并将其放置在主目录下的名为 toolchains 的目录中，则为 `$HOME/toolchains/microblaze/gcc-9.2.0-nolibc/microblaze-linux/bin/microblaze-linux`

这意味着对于大多数架构，在 QEMU 下运行就像下面这样简单：

```bash
./tools/testing/kunit/kunit.py run --arch=x86_64
```

当进行交叉编译时，我们可能需要指定不同的工具链，例如：

```bash
./tools/testing/kunit/kunit.py run \
    --arch=s390 \
    --cross_compile=s390x-linux-gnu-
```

如果我们想要在一个不支持 `--arch` 标志的架构上运行 KUnit 测试，或者想要使用非默认配置在 QEMU 上运行 KUnit 测试，那么我们可以编写自己的 `QemuConfig`。

这些 `QemuConfig` 是用 Python 编写的。文件顶部有一行导入语句 `from ..qemu_config import QemuArchParams`。该文件必须包含一个名为 `QEMU_ARCH` 的变量，并且将一个 `QemuArchParams` 实例分配给它。参见示例：`tools/testing/kunit/qemu_configs/x86_64.py`。

一旦有了 `QemuConfig`，我们就可以使用 `--qemu_config` 标志将其传递给 `kunit_tool`。使用时，此标志会替代 `--arch` 标志。例如：使用 `tools/testing/kunit/qemu_configs/x86_64.py`，调用如下所示：

```bash
./tools/testing/kunit/kunit.py run \
    --timeout=60 \
    --jobs=12 \
    --qemu_config=./tools/testing/kunit/qemu_configs/x86_64.py
```

### 运行命令行参数

`kunit_tool` 提供了许多其他有用的命令行参数，可用于我们的测试环境。以下是常用的命令行参数：

- `--help`: 列出所有可用选项。要列出常用选项，请在命令前放置 `--help`。要列出特定于命令的选项，请在命令后放置 `--help`。
  - 注意：不同的命令（`config`、`build`、`run` 等）有不同的支持选项。
- `--build_dir`: 指定 `kunit_tool` 构建目录。它包括 `.kunitconfig`、`.config` 文件和编译后的内核。
- ``--make_options``: 指定在编译内核时（使用`build`或`run`命令）传递给`make`的附加选项。例如：
  为了启用编译器警告，我们可以传递`--make_options W=1`
- ``--alltests``: 启用预定义的一组选项以构建尽可能多的测试
  .. note:: 已启用选项的列表可以在`tools/testing/kunit/configs/all_tests.config`中找到
  如果你只想启用所有测试，并且其他依赖项已经满足，那么请在你的`.kunitconfig`文件中添加`CONFIG_KUNIT_ALL_TESTS=y`
- ``--kunitconfig``: 指定`.kunitconfig`文件的路径或目录。例如：

  - `lib/kunit/.kunitconfig`可以是文件的路径
  - `lib/kunit`可以是包含该文件的目录
  此文件用于构建和运行一组预定义的测试及其依赖项。例如，为特定子系统运行测试
- ``--kconfig_add``: 指定要追加到`.kunitconfig`文件中的附加配置选项。例如：

  .. code-block::

	./tools/testing/kunit/kunit.py run --kconfig_add CONFIG_KASAN=y

- ``--arch``: 在指定的架构上运行测试。架构参数与Kbuild的ARCH环境变量相同
  例如，i386、x86_64、arm、um等。非UML架构在qemu上运行
  默认值为`um`
- ``--cross_compile``: 指定 Kbuild 工具链。它传递与 Kbuild 使用的 ``CROSS_COMPILE`` 变量相同的参数。这将是工具链二进制文件（如 GCC）的前缀。例如：
  - 如果我们的系统上安装了sparc工具链，则为 ``sparc64-linux-gnu-``
  - 如果我们从0-day网站下载了microblaze工具链，并将其放置在我们家目录中名为toolchains的指定路径下，则为 ``$HOME/toolchains/microblaze/gcc-9.2.0-nolibc/microblaze-linux/bin/microblaze-linux``
- ``--qemu_config``: 指定包含自定义 QEMU 架构定义的文件路径。这应该是一个包含 `QemuArchParams` 对象的 Python 文件。
- ``--qemu_args``: 指定额外的 QEMU 参数，例如，``-smp 8``
- ``--jobs``: 指定同时运行的任务（命令）数量。默认情况下，此值设置为系统的内核数量。
- ``--timeout``: 指定所有测试运行的最大秒数。这不包括构建测试所花费的时间。
- ``--kernel_args``: 指定额外的内核命令行参数。可以重复使用。
- ``--run_isolated``: 如果设置，则为每个单独的测试套件/测试启动内核。
这些选项对于调试非隔离测试非常有用，这类测试可能会因为之前运行的内容而通过或失败。
- `--raw_output`: 如果设置，会生成内核的未格式化输出。可能的选项包括：

   - `all`: 若要查看完整的内核输出，请使用 `--raw_output=all`
- `kunit`: 这是默认选项，并过滤到KUnit输出。使用 `--raw_output` 或 `--raw_output=kunit`
- `--json`: 如果设置，将以JSON格式存储测试结果并打印到 `stdout`，或者如果指定了文件名，则保存到文件中
- `--filter`: 指定对测试属性的过滤条件，例如，`speed!=slow`
可以通过将输入用引号括起来并用逗号分隔过滤器来使用多个过滤器。示例：`--filter "speed>slow, module=example"`
- `--filter_action`: 如果设置为 `skip`，被过滤的测试在输出中将显示为已跳过，而不是不显示任何内容
- `--list_tests`: 如果设置，将列出所有将要运行的测试
- `--list_tests_attr`: 如果设置，将列出所有将要运行的测试及其所有属性
