**rtla timerlat** 工具是 *timerlat* 跟踪器的接口。*timerlat* 跟踪器为每个 CPU 分派一个内核线程。这些线程设置周期性定时器来唤醒自己，然后再次休眠。在唤醒之后，它们收集并生成对操作系统定时器延迟调试有用的信息。

*timerlat* 跟踪器以两种方式输出信息。它周期性地在定时器 *IRQ* 处理程序和 *Thread* 处理程序处打印定时器延迟。此外，它还通过 **osnoise:** 的跟踪点启用最相关信息的追踪。
