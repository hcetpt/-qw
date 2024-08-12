DMA 测试指南
=============

Andy Shevchenko <andriy.shevchenko@linux.intel.com>

本简短文档介绍了如何使用 dmatest 模块测试 DMA 驱动程序。dmatest 模块通过使用各种长度和源缓冲区及目标缓冲区的各种偏移量来测试 DMA 的内存复制（memcpy）、内存填充（memset）、异或（XOR）以及 RAID6 P+Q 操作。它将使用可重复的模式初始化两个缓冲区，并验证 DMA 引擎是否仅复制了请求的区域，而没有复制其他内容。它还会验证字节是否未被交换，且源缓冲区未被修改。
dmatest 模块可以配置为测试特定通道。它还可以同时测试多个通道，并可以启动多个线程竞争同一通道。
.. note::
  测试套件仅在具有以下至少一项功能的通道上工作：DMA_MEMCPY（内存到内存）、DMA_MEMSET（常量到内存或内存到内存，当被模拟时）、DMA_XOR、DMA_PQ。
.. note::
  如有任何相关问题，请使用官方邮件列表 dmaengine@vger.kernel.org。
第一部分 - 如何构建测试模块
=====================================

在 menuconfig 中有一个选项可以通过以下路径找到：

   设备驱动程序 -> DMA 引擎支持 -> DMA 测试客户端

在配置文件中，该选项被称为 CONFIG_DMATEST。dmatest 可以作为模块或内置于内核中构建。让我们考虑这两种情况。
第二部分 - 当 dmatest 作为模块构建时
==========================================

用法示例::

    % modprobe dmatest timeout=2000 iterations=1 channel=dma0chan0 run=1

…或者::

    % modprobe dmatest
    % echo 2000 > /sys/module/dmatest/parameters/timeout
    % echo 1 > /sys/module/dmatest/parameters/iterations
    % echo dma0chan0 > /sys/module/dmatest/parameters/channel
    % echo 1 > /sys/module/dmatest/parameters/run

…或者在内核命令行中::

    dmatest.timeout=2000 dmatest.iterations=1 dmatest.channel=dma0chan0 dmatest.run=1

多通道测试用法示例（5.0 内核新增）::

    % modprobe dmatest
    % echo 2000 > /sys/module/dmatest/parameters/timeout
    % echo 1 > /sys/module/dmatest/parameters/iterations
    % echo dma0chan0 > /sys/module/dmatest/parameters/channel
    % echo dma0chan1 > /sys/module/dmatest/parameters/channel
    % echo dma0chan2 > /sys/module/dmatest/parameters/channel
    % echo 1 > /sys/module/dmatest/parameters/run

.. note::
  对于所有测试，从 5.0 内核开始，无论是单通道还是多通道，必须在设置所有其他参数之后设置通道参数。此时会获取现有参数值供线程使用。所有其他参数都是共享的。因此，如果对任何其他参数进行了更改，并指定了额外的通道，则（共享）参数用于所有线程将使用新值。
指定通道后，每个线程都会被设置为待处理状态。当 run 参数设置为 1 时，所有线程开始执行。
.. hint::
  可通过运行以下命令获得可用通道的列表::

    % ls -1 /sys/class/dma/

一旦开始，将发出类似于“dmatest: 使用 dma0chan0 添加了 1 个线程”的消息。创建一个针对该特定通道的线程并处于待处理状态，一旦 run 设置为 1 时，待处理线程即开始。
请注意，运行新的测试不会停止正在进行的任何测试。
以下命令返回测试的状态：

    % cat /sys/module/dmatest/parameters/run

用户空间可以通过轮询 'run' 直到其为 false，或者使用等待参数来等待测试完成。在加载模块时指定 'wait=1' 会导致模块初始化暂停直到一次测试运行完成；而读取 `/sys/module/dmatest/parameters/wait` 会在返回之前等待任何正在运行的测试完成。例如，以下脚本会在退出前等待 42 次测试完成。请注意，如果将 'iterations' 设置为 'infinite'，则禁用等待。

示例：

    % modprobe dmatest run=1 iterations=42 wait=1
    % modprobe -r dmatest

…或：

    % modprobe dmatest run=1 iterations=42
    % cat /sys/module/dmatest/parameters/wait
    % modprobe -r dmatest

### 第三部分 - 当内置于内核中

传递给内核命令行的模块参数将用于首次执行的测试。当用户获得控制后，可以使用相同的或不同的参数重新运行测试。详情请参阅上面的 `第二部分 - 当 dmatest 被构建为模块时` 部分。在这两种情况下，模块参数都作为实际测试案例的值使用。你始终可以通过运行以下命令在运行时检查它们：

    % grep -H . /sys/module/dmatest/parameters/*

### 第四部分 - 收集测试结果

测试结果将以如下格式打印到内核日志缓冲区：

    "dmatest: result <channel>: <test id>: '<error msg>' with src_off=<val> dst_off=<val> len=<val> (<err code>)"

输出示例：

    % dmesg | tail -n 1
    dmatest: result dma0chan0-copy0: #1: No errors with src_off=0x7bf dst_off=0x8ad len=0x3fea (0)

不同类型的错误信息格式是统一的。括号中的数字代表额外信息，如错误代码、错误计数器或状态。测试线程在完成时也会输出一条汇总行，列出执行的测试数量、失败的数量以及一个结果代码。

示例：

    % dmesg | tail -n 1
    dmatest: dma0chan0-copy0: summary 1 test, 0 failures 1000 iops 100000 KB/s (0)

数据不匹配错误的详细信息也会被输出，但不遵循上述格式。

### 第五部分 - 处理通道分配

#### 分配通道

不需要在开始测试运行前配置通道。尝试在未配置通道的情况下运行测试将导致对所有可用通道进行测试。

示例：

    % echo 1 > /sys/module/dmatest/parameters/run
    dmatest: 没有配置通道，继续使用任意通道

通过 "channel" 参数注册通道。可以按名称请求通道，一旦请求，该通道就会被注册，并且会在测试列表中添加一个待处理线程。

示例：

    % echo dma0chan2 > /sys/module/dmatest/parameters/channel
    dmatest: 使用 dma0chan2 添加了 1 个线程

可以通过重复上述示例来添加更多通道。读回 channel 参数会返回最后成功添加的通道名称。

示例：

    % echo dma0chan1 > /sys/module/dmatest/parameters/channel
    dmatest: 使用 dma0chan1 添加了 1 个线程
    % echo dma0chan2 > /sys/module/dmatest/parameters/channel
    dmatest: 使用 dma0chan2 添加了 1 个线程
    % cat /sys/module/dmatest/parameters/channel
    dma0chan2

另一种请求通道的方法是使用空字符串请求通道，这样做会请求测试所有可用的通道。

示例：

    % echo "" > /sys/module/dmatest/parameters/channel
    dmatest: 使用 dma0chan0 添加了 1 个线程
    dmatest: 使用 dma0chan3 添加了 1 个线程
    dmatest: 使用 dma0chan4 添加了 1 个线程
    dmatest: 使用 dma0chan5 添加了 1 个线程
    dmatest: 使用 dma0chan6 添加了 1 个线程
    dmatest: 使用 dma0chan7 添加了 1 个线程
    dmatest: 使用 dma0chan8 添加了 1 个线程

在任何时候，在测试配置期间，读取 "test_list" 参数将会打印当前待处理的测试列表。

示例：

    % cat /sys/module/dmatest/parameters/test_list
    dmatest: 使用 dma0chan0 的 1 个线程
    dmatest: 使用 dma0chan3 的 1 个线程
    dmatest: 使用 dma0chan4 的 1 个线程
    dmatest: 使用 dma0chan5 的 1 个线程
    dmatest: 使用 dma0chan6 的 1 个线程
    dmatest: 使用 dma0chan7 的 1 个线程
    dmatest: 使用 dma0chan8 的 1 个线程

注意：对于每次测试运行都需要配置通道，因为通道配置不会延续到下一次测试运行。
释放通道
-------------------

可以通过将 `run` 设置为 0 来释放通道
示例::

    % echo dma0chan1 > /sys/module/dmatest/parameters/channel
    dmatest: 使用 dma0chan1 添加了 1 个线程
    % cat /sys/class/dma/dma0chan1/in_use
    1
    % echo 0 > /sys/module/dmatest/parameters/run
    % cat /sys/class/dma/dma0chan1/in_use
    0

由先前测试运行分配的通道会在成功完成测试运行后请求新通道时自动释放
