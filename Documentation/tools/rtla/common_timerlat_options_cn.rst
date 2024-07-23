**-a**, **--auto** *us*

设置自动跟踪模式。此模式在调试系统时设置了一些常用选项。它等同于使用**-T** *us* **-s** *us* **-t**。默认情况下，*timerlat*追踪器为*timerlat*线程使用FIFO:95，因此等效于**-P** *f:95*

**-p**, **--period** *us*

设置*timerlat*追踪器的周期（以微秒为单位）

**-i**, **--irq** *us*

如果*IRQ*延迟高于参数中指定的微秒值，则停止追踪

**-T**, **--thread** *us*

如果*Thread*延迟高于参数中指定的微秒值，则停止追踪

**-s**, **--stack** *us*

如果*Thread*延迟高于参数中指定的微秒值，在*IRQ*处保存堆栈跟踪

**-t**, **--trace** \[*file*\]

将停止的追踪保存到\[*file|timerlat_trace.txt*\]

**--dma-latency** *us*

设置/dev/cpu_dma_latency为*us*，旨在限制从空闲状态退出的延迟
*cyclictest*默认将此值设置为*0*，使用**--dma-latency** *0*可获得类似结果

**-k**, **--kernel-threads**

使用timerlat内核空间线程，与**-u**相反

**-u**, **--user-threads**

设置timerlat在没有工作负载的情况下运行，然后将用户空间工作负载调度到等待timerlat_fd上。一旦工作负载被唤醒，它会再次进入睡眠状态，从而将内核到用户和用户到内核的测量值添加到追踪器输出中。除非用户指定**-k**，否则将使用**--user-threads**。
设置 **-U**, **--user-load**

        设置 `timerlat` 在无工作负载的情况下运行，等待用户调度一个每核（per-cpu）任务，该任务等待在 `tracing/osnoise/per_cpu/cpu$ID/timerlat_fd` 上的新周期。
请参阅 `linux/tools/rtla/sample/timerlat_load.py` 以获取用户工作负载代码的示例。
