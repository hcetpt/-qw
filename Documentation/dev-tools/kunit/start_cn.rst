### 开始使用

本页面概述了 kunit_tool 和 KUnit 框架，指导如何运行现有的测试以及如何编写一个简单的测试用例，并涵盖了用户在首次使用 KUnit 时可能遇到的常见问题。

#### 安装依赖项

KUnit 的依赖与 Linux 内核相同。只要能构建内核，就能运行 KUnit。

#### 使用 kunit_tool 运行测试

kunit_tool 是一个 Python 脚本，它可以配置和构建内核、运行测试并格式化测试结果。从内核仓库中，可以这样运行 kunit_tool：

```bash
./tools/testing/kunit/kunit.py run
```

**注意：**
你可能会看到如下错误：
```
"The source tree is not clean, please run 'make ARCH=um mrproper'"
```

这发生是因为内部 kunit.py 指定了 ``.kunit``（默认选项）作为通过命令 `make O=output/dir` 中的构建目录，通过参数 `--build_dir`。因此，在开始树外构建之前，源码树必须是干净的。
同样需要注意的是，在“内核的构建目录”部分中的 :doc:`管理指南 </admin-guide/README>` 中提到的注意事项，即该构建目录一旦使用，就必须用于所有 `make` 命令的调用。
好消息是确实可以通过运行 `make ARCH=um mrproper` 来解决这个问题，但请注意这样做会删除当前配置和所有生成的文件。

如果一切正常，你应该能看到如下输出：

```
配置 KUnit 内核 ...
构建 KUnit 内核 ...
启动 KUnit 内核 ...
测试将通过或失败
```

**注意：**
由于首次构建大量源代码，`构建 KUnit 内核` 步骤可能需要一些时间。
对于此包装器的详细信息，请参见：
《开发工具文档/kunit/run_wrapper.rst》
选择要运行的测试
-------------------

默认情况下，kunit_tool 会运行所有在最小配置下可到达的测试，
也就是说，大多数 kconfig 选项使用默认值。但是，你可以通过以下方式来选择要运行的测试：

- _`定制 Kconfig`_ 用于编译内核，或
- _`按名称过滤测试`_ 来选择具体要运行哪些已编译的测试
定制 Kconfig
~~~~~~~~~~~~
对于 `.kunitconfig` 的一个良好起点是 KUnit 默认的配置。
如果你还没有运行过 `kunit.py run`，你可以通过如下命令生成它：

.. code-block:: bash

	cd $LINUX_REPO_PATH
	tools/testing/kunit/kunit.py config
	cat .kunit/.kunitconfig

.. note ::
   `.kunitconfig` 文件位于 kunit.py 使用的 `--build_dir` 中，默认为 `.kunit` 目录。
在运行测试之前，kunit_tool 确保 `.kunitconfig` 中设置的所有配置项也在内核的 `.config` 中被设置。如果没有包含所使用选项的依赖项，它会给出警告。
有许多方法可以定制配置：

a. 编辑 `.kunit/.kunitconfig`。该文件应包含运行所需测试所需的 kconfig 选项列表及其依赖项。
你可能需要从 `.kunitconfig` 中移除 `CONFIG_KUNIT_ALL_TESTS`，因为它会启用大量额外的测试，而这些测试可能并不是你需要的。
如果你需要在除了 UML 之外的架构上运行，请参阅 :ref:`kunit-on-qemu`。
b. 在 `.kunit/.kunitconfig` 的基础上启用额外的 kconfig 选项。
例如，为了包括内核的链表测试，你可以运行：

	./tools/testing/kunit/kunit.py run \
		--kconfig_add CONFIG_LIST_KUNIT_TEST=y

c. 提供一个或多个来自源码树中的 `.kunitconfig` 文件路径。
例如，若要仅运行`FAT_FS`和`EXT4`测试，可以执行如下命令：

	./tools/testing/kunit/kunit.py run \
		--kunitconfig ./fs/fat/.kunitconfig \
		--kunitconfig ./fs/ext4/.kunitconfig

d. 如果您更改了`.kunitconfig`文件，`kunit.py`将会触发`config`文件的重建。但是您可以直接编辑`config`文件或使用类似`make menuconfig O=.kunit`这样的工具。只要它是`.kunitconfig`的超集，`kunit.py`就不会覆盖您的更改。
.. note ::

	要在找到满意的配置后保存`.kunitconfig`文件，请执行以下操作：

		make savedefconfig O=.kunit
		cp .kunit/defconfig .kunit/.kunitconfig

通过名称过滤测试
~~~~~~~~~~~~~~~~~~~~~~~
如果您想要比Kconfig提供的更具体，还可以在启动时通过传递一个glob过滤器（有关模式的说明请参阅手册页:manpage:`glob(7)`）来选择要执行哪些测试。
如果过滤器中有`.`（点），它将被解释为测试套件名与测试用例名之间的分隔符；否则，它将被解释为测试套件的名称。
假设我们正在使用默认配置：

a. 提供一个测试套件的名字，如`"kunit_executor_test"`，以运行其中的所有测试用例：

	./tools/testing/kunit/kunit.py run "kunit_executor_test"

b. 提供由其测试套件前缀的特定测试用例的名字，如`"example.example_simple_test"`，以专门运行该测试用例：

	./tools/testing/kunit/kunit.py run "example.example_simple_test"

c. 使用通配符字符(`*?[`)来运行任何匹配模式的测试用例，例如`"*.*64*"`来运行任何测试套件中包含`"64"`名字的测试用例：

	./tools/testing/kunit/kunit.py run "*.*64*"

无需KUnit包装器运行测试
======================
如果您不想使用KUnit包装器（例如：您希望待测代码能够集成到其他系统中，或者使用不同的/不支持的架构或配置），KUnit可以被包含在任何内核中，并且结果需要手动读取和解析。
.. note ::
   `CONFIG_KUNIT`不应该在一个生产环境中启用。
启用KUnit会禁用内核地址空间布局随机化(KASLR)，并且测试可能会影响内核状态，这不适合于生产环境。

配置内核
----------------------
为了启用KUnit本身，您需要启用`CONFIG_KUNIT` Kconfig选项（在`menuconfig`中的内核黑客/内核测试和覆盖下）。从那里，您可以启用任何KUnit测试。它们通常有以`_KUNIT_TEST`结尾的配置选项。
KUnit和KUnit测试可以被编译为模块。当模块加载时，模块中的测试就会运行。

无需KUnit包装器运行测试
-------------------------------------
构建并运行您的内核。在内核日志中，测试输出将以TAP格式打印出来。这只有在KUnit/测试被内置时才会默认发生。否则，需要加载模块。
.. note ::
   一些行和/或数据可能会混入TAP输出中。
### 编写您的第一个测试

在内核仓库中，让我们添加一些可以测试的代码。

1. 创建一个文件 `drivers/misc/example.h`，其中包含：

   ```c
   int misc_example_add(int left, int right);
   ```

2. 创建一个文件 `drivers/misc/example.c`，其中包含：

   ```c
   #include <linux/errno.h>
   #include "example.h"

   int misc_example_add(int left, int right)
   {
       return left + right;
   }
   ```

3. 在 `drivers/misc/Kconfig` 中添加以下行：

   ```kconfig
   config MISC_EXAMPLE
       bool "My example"
   ```

4. 在 `drivers/misc/Makefile` 中添加以下行：

   ```make
   obj-$(CONFIG_MISC_EXAMPLE) += example.o
   ```

现在我们准备编写测试用例了。

1. 在 `drivers/misc/example_test.c` 中添加以下测试用例：

   ```c
   #include <kunit/test.h>
   #include "example.h"

   /* 定义测试用例。 */

   static void misc_example_add_test_basic(struct kunit *test)
   {
       KUNIT_EXPECT_EQ(test, 1, misc_example_add(1, 0));
       KUNIT_EXPECT_EQ(test, 2, misc_example_add(1, 1));
       KUNIT_EXPECT_EQ(test, 0, misc_example_add(-1, 1));
       KUNIT_EXPECT_EQ(test, INT_MAX, misc_example_add(0, INT_MAX));
       KUNIT_EXPECT_EQ(test, -1, misc_example_add(INT_MAX, INT_MIN));
   }

   static void misc_example_test_failure(struct kunit *test)
   {
       KUNIT_FAIL(test, "This test never passes.");
   }

   static struct kunit_case misc_example_test_cases[] = {
       KUNIT_CASE(misc_example_add_test_basic),
       KUNIT_CASE(misc_example_test_failure),
       {}
   };

   static struct kunit_suite misc_example_test_suite = {
       .name = "misc-example",
       .test_cases = misc_example_test_cases,
   };
   kunit_test_suite(misc_example_test_suite);

   MODULE_LICENSE("GPL");
   ```

2. 在 `drivers/misc/Kconfig` 中添加以下行：

   ```kconfig
   config MISC_EXAMPLE_TEST
       tristate "Test for my example" if !KUNIT_ALL_TESTS
       depends on MISC_EXAMPLE && KUNIT
       default KUNIT_ALL_TESTS
   ```

   注意：如果您的测试不支持作为可加载模块构建（这不被推荐），请将 `tristate` 替换为 `bool`，并依赖于 `KUNIT=y` 而不是 `KUNIT`。

3. 在 `drivers/misc/Makefile` 中添加以下行：

   ```make
   obj-$(CONFIG_MISC_EXAMPLE_TEST) += example_test.o
   ```

4. 在 `.kunit/.kunitconfig` 中添加以下行：

   ```
   CONFIG_MISC_EXAMPLE=y
   CONFIG_MISC_EXAMPLE_TEST=y
   ```

5. 运行测试：

   ```bash
   ./tools/testing/kunit/kunit.py run
   ```

   您应该看到如下失败信息：

   ```
   ..
   [16:08:57] [PASSED] misc-example:misc_example_add_test_basic
   [16:08:57] [FAILED] misc-example:misc_example_test_failure
   [16:08:57] EXPECTATION FAILED at drivers/misc/example-test.c:17
   [16:08:57]      This test never passes
   ..
   ```

恭喜！您刚刚编写了第一个 KUnit 测试。

### 下一步
如果您对使用 KUnit 的一些更高级特性感兴趣，请参阅 `Documentation/dev-tools/kunit/run_wrapper.rst`。

如果您希望不使用 kunit.py 运行测试，请查阅 `Documentation/dev-tools/kunit/run_manual.rst`。

对于编写 KUnit 测试的更多信息（包括一些常用的测试技巧），请参见 `Documentation/dev-tools/kunit/usage.rst`。
