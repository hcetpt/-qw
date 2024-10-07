SPDX 许可证标识符: GPL-2.0

================
CoreSight - Perf
================

    :作者: Carsten Haitzler <carsten.haitzler@arm.com>
    :日期: 2022年6月29日

Perf 能够本地访问 CoreSight 追踪数据并将其存储到输出的 perf 数据文件中。这些数据随后可以被解码，以提供追踪的指令，用于调试或性能分析目的。你可以使用类似下面的 perf record 命令来记录此类数据：

```
perf record -e cs_etm//u testbinary
```

这将运行某个测试二进制文件（testbinary），直到它退出，并记录一个 perf.data 追踪文件。如果 CoreSight 正常工作，该文件应包含 AUX 部分。你可以通过类似下面的命令将此文件的内容转储为可读文本：

```
perf report --stdio --dump -i perf.data
```

你应该会发现文件的一些部分包含 AUX 数据块，如下所示：

```
0x1e78 [0x30]: PERF_RECORD_AUXTRACE 大小: 0x11dd0  偏移: 0  引用: 0x1b614fc1061b0ad1  索引: 0  线程ID: 531230  CPU: -1

   . ... CoreSight ETM 追踪数据: 大小 73168 字节
           索引:0; ID:10;   I_ASYNC : 对齐同步
索引:12; ID:10;  I_TRACE_INFO : 追踪信息.; INFO=0x0 { CC.0 }
             索引:17; ID:10;  I_ADDR_L_64IS0 : 地址, 长, 64位, IS0.; 地址=0x0000000000000000;
             索引:26; ID:10;  I_TRACE_ON : 开启追踪
索引:27; ID:10;  I_ADDR_CTXT_L_64IS0 : 地址 & 上下文, 长, 64位, IS0.; 地址=0x0000FFFFB6069140; 上下文: AArch64,EL0, NS;
             索引:38; ID:10;  I_ATOM_F6 : 原子格式 6.; EEEEEEEEEEEEEEEEEEEEEEEE
             索引:39; ID:10;  I_ATOM_F6 : 原子格式 6.; EEEEEEEEEEEEEEEEEEEEEEEE
             索引:40; ID:10;  I_ATOM_F6 : 原子格式 6.; EEEEEEEEEEEEEEEEEEEEEEEE
             索引:41; ID:10;  I_ATOM_F6 : 原子格式 6.; EEEEEEEEEEEN
             ..
如果你看到上述内容，则表明你的系统正在正确地追踪 CoreSight 数据。
要编译支持 CoreSight 的 perf 工具，请在 tools/perf 目录下执行：

    make CORESIGHT=1

这需要 OpenCSD 来构建。你可以安装支持包，如 libopencsd 和 libopencsd-dev，或者下载并自行构建。上游 OpenCSD 位于：

  https://github.com/Linaro/OpenCSD

有关编译支持 CoreSight 的 perf 工具及其更详细使用的完整信息，请参阅：

  https://github.com/Linaro/OpenCSD/blob/master/HOWTO.md

内核 CoreSight 支持
--------------------

你还需要在内核配置中启用 CoreSight 支持。确保启用以下选项：

   CONFIG_CORESIGHT=y

还有其他一些 CoreSight 选项，你可能也需要启用，例如：

   CONFIG_CORESIGHT_LINKS_AND_SINKS=y
   CONFIG_CORESIGHT_LINK_AND_SINK_TMC=y
   CONFIG_CORESIGHT_CATU=y
   CONFIG_CORESIGHT_SINK_TPIU=y
   CONFIG_CORESIGHT_SINK_ETBV10=y
   CONFIG_CORESIGHT_SOURCE_ETM4X=y
   CONFIG_CORESIGHT_CTI=y
   CONFIG_CORESIGHT_CTI_INTEGRATION_REGS=y

请参考内核配置帮助获取更多信息。

Perf 测试 - 验证内核和用户空间的 perf CoreSight 功能
-----------------------------------------------------------

当你运行 perf 测试时，它会进行许多自检。其中一些测试会覆盖 CoreSight（仅在启用且在 ARM64 架构上）。你通常会在内核树中的 tools/perf 目录下运行 perf 测试。一些测试会检查内部的 perf 支持，例如：

   检查 Arm CoreSight 追踪数据记录和合成样本
   检查 Arm SPE 追踪数据记录和合成样本

其他一些测试则会实际使用 perf record 和一些测试二进制文件（位于 tests/shell/coresight 中）来收集追踪数据，以确保达到最低功能水平。启动这些测试的脚本也在同一目录下。这些测试看起来都像这样：

   CoreSight / ASM Pure Loop
   CoreSight / Memcpy 16k 10 Threads
   CoreSight / Thread Loop 10 Threads - Check TID
   等等

如果工具二进制文件不存在于 tests/shell/coresight/* 目录中，这些 perf record 测试将不会运行，并会被跳过。如果你的硬件不支持 CoreSight，则不要编译支持 CoreSight 的 perf 或删除这些二进制文件，以避免测试失败并使其被跳过。

这些测试将在当前工作目录（例如 tools/perf）中记录历史结果，并命名为 stats-*.csv，例如：

   stats-asm_pure_loop-out.csv
   stats-memcpy_thread-16k_10.csv
   等等

这些统计文件记录了 perf 数据输出中 AUX 数据部分的某些方面，计算了某些编码的数量（这是验证其工作的非常简单的方法）。CoreSight 的一个问题在于，当需要记录的数据量足够大时，由于处理器未能及时唤醒以读取所有缓冲区中的数据，可能会丢失一些数据。你会注意到每次运行 perf 测试时收集的数据量可能会有很大差异。
如果你希望查看这些变化随时间的发展情况，只需多次运行 `perf test`，所有这些 CSV 文件将会不断增加数据，以便你日后进行检查、绘图或用于判断情况是变好还是变坏。
这意味着有时这些测试会失败，因为它们无法捕获所需的所有数据。这是关于跟踪数据质量和数量随时间的变化，并观察 Linux 内核的更改何时提高了追踪质量。
请注意，某些测试运行时间较长，特别是在处理 perf 数据文件并将其内容转储以检查内部信息时。
你可以通过设置 `PERF_TEST_CORESIGHT_STATDIR` 环境变量来改变这些 CSV 日志的存储位置，例如：

   ```sh
   export PERF_TEST_CORESIGHT_STATDIR=/var/tmp
   perf test
   ```

这些测试还会将生成的 perf 输出数据存储在当前目录中，以便日后检查，例如：

   ```sh
   perf-asm_pure_loop-out.data
   perf-memcpy_thread-16k_10.data
   ...
   ```

你可以通过设置 `PERF_TEST_CORESIGHT_DATADIR` 环境变量来改变 perf 数据文件的存储位置，例如：

   ```sh
   export PERF_TEST_CORESIGHT_DATADIR=/var/tmp
   perf test
   ```

如果你希望将测试输出保存在当前工作目录之外的地方以供长期存储和检查，可以设置上述环境变量。
