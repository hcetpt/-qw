SPDX 许可证标识符: GPL-2.0

============================
无需 kunit_tool 运行测试
============================

如果我们不想使用 kunit_tool（例如：我们希望与其他系统集成，
或在真实硬件上运行测试），我们可以将 KUnit 集成到任何内核中，读取结果，并手动解析。
.. 注意:: KUnit 不是为生产系统设计的。有可能测试会降低系统的稳定性或安全性。
配置内核
====================

KUnit 测试可以在没有 kunit_tool 的情况下运行。这在以下情况下很有用：

- 我们有一个现有的内核配置需要进行测试
- 需要在真实硬件上运行（或者使用 kunit_tool 不支持的模拟器/虚拟机）
- 希望与一些现有的测试系统集成
KUnit 通过 `CONFIG_KUNIT` 选项进行配置，个别测试也可以通过启用 `.config` 文件中的相应配置选项来构建。KUnit 测试通常（但并非总是）有以 `_KUNIT_TEST` 结尾的配置选项。大多数测试既可以作为模块构建，也可以直接构建到内核中。
.. 注意 ::

	可以通过启用 `KUNIT_ALL_TESTS` 配置选项来自动启用所有依赖条件满足的测试。这是快速测试当前配置适用的所有内容的好方法
一旦我们构建了内核（和/或模块），运行测试就很简单了。如果测试是内置的，它们将在内核启动时自动运行。结果将以 TAP 格式写入内核日志 (`dmesg`) 中。
如果测试作为模块构建，它们将在加载模块时运行
.. code-block :: bash

	# modprobe example-test

结果将以 TAP 格式出现在 `dmesg` 中。
### debugfs

KUnit 可以通过用户空间中的 debugfs 文件系统访问（更多关于 debugfs 的信息请参阅 `Documentation/filesystems/debugfs.rst`）。如果启用了 `CONFIG_KUNIT_DEBUGFS`，那么 KUnit 的 debugfs 文件系统将挂载在 `/sys/kernel/debug/kunit`。你可以使用这个文件系统来执行以下操作：

#### 获取测试结果

你可以使用 debugfs 来获取 KUnit 测试结果。测试结果可以从 debugfs 文件系统中以下只读文件获取：

```bash
/sys/kernel/debug/kunit/<test_suite>/results
```

测试结果将以 KTAP 文档的形式打印出来。需要注意的是，此文档与内核日志是分开的，因此可能会有不同的测试套件编号。

#### 在内核启动后运行测试

你可以使用 debugfs 文件系统来触发内置测试在启动后运行。要运行测试套件，可以使用以下命令写入 `/sys/kernel/debug/kunit/<test_suite>/run` 文件：

```bash
echo "任意字符串" > /sys/kernel/debug/kunit/<test_suite>/run
```

结果是，测试套件将运行，并且结果将被打印到内核日志中。
然而，对于使用 init 数据的 KUnit 套件来说，这一特性不可用，因为 init 数据可能在内核启动后就被丢弃了。使用 init 数据的 KUnit 套件应使用 `kunit_test_init_section_suites()` 宏定义。
此外，你不能使用此功能来并发运行测试。相反，一个测试会等待其他测试完成或失败后才运行。

**注意：**

对于测试编写者来说，为了使用此功能，测试需要正确初始化和/或清理任何数据，以便测试能够正确地第二次运行。
