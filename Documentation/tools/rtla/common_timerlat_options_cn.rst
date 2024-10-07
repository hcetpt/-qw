**-a**, **--auto** *us*

        设置自动跟踪模式。此模式会设置一些调试系统时常用的选择。等同于使用 **-T** *us* **-s** *us* **-t**。默认情况下，*timerlat* 跟踪器为 *timerlat* 线程使用 FIFO:95，因此等同于 **-P** *f:95*。

**-p**, **--period** *us*

        设置 *timerlat* 跟踪器的周期（以微秒为单位）。

**-i**, **--irq** *us*

        如果 *IRQ* 延迟高于参数值（以微秒为单位），则停止跟踪。

**-T**, **--thread** *us*

        如果 *Thread* 延迟高于参数值（以微秒为单位），则停止跟踪。

**-s**, **--stack** *us*

        如果 *Thread* 延迟高于参数值（以微秒为单位），则在 *IRQ* 处保存堆栈跟踪。

**-t**, **--trace** \[*file*\]

        将停止的跟踪信息保存到 [*file|timerlat_trace.txt*]。

**--dma-latency** *us*

        设置 /dev/cpu_dma_latency 为 *us*，旨在限制从空闲状态退出的延迟。
        *cyclictest* 默认将这个值设置为 *0*，使用 **--dma-latency** *0* 可获得类似的结果。

**-k**, **--kernel-threads**

        使用 *timerlat* 内核空间线程，与 **-u** 相对。

**-u**, **--user-threads**

        设置 *timerlat* 在没有工作负载的情况下运行，并分派用户空间工作负载等待在 timerlat_fd 上。一旦工作负载被唤醒，它又进入睡眠状态，从而将内核到用户和用户到内核的时间加入到跟踪输出中。除非用户指定 **-k**，否则将使用 **--user-threads**。
**-U**, **--user-load**

        设置 timerlat 以空载模式运行，等待用户派遣一个每核任务，该任务会在 tracing/osnoise/per_cpu/cpu$ID/timerlat_fd 上等待新的周期
请参阅 linux/tools/rtla/sample/timerlat_load.py 以获取用户负载代码的示例
