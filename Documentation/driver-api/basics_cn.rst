驱动基础
=============

驱动的入口和出口点
----------------------------

.. kernel-doc:: include/linux/module.h
   :internal:

驱动设备表
-------------------

.. kernel-doc:: include/linux/mod_devicetable.h
   :internal:
   :no-identifiers: pci_device_id


延迟与调度例程
--------------------------------

.. kernel-doc:: include/linux/sched.h
   :internal:

.. kernel-doc:: kernel/sched/core.c
   :export:

.. kernel-doc:: kernel/sched/cpupri.c
   :internal:

.. kernel-doc:: kernel/sched/fair.c
   :internal:

.. kernel-doc:: include/linux/completion.h
   :internal:

时间和定时器例程
-----------------------

.. kernel-doc:: include/linux/jiffies.h
   :internal:

.. kernel-doc:: kernel/time/time.c
   :export:

.. kernel-doc:: kernel/time/timer.c
   :export:

高分辨率定时器
----------------------

.. kernel-doc:: include/linux/ktime.h
   :internal:

.. kernel-doc:: include/linux/hrtimer.h
   :internal:

.. kernel-doc:: kernel/time/hrtimer.c
   :export:

等待队列与唤醒事件
---------------------------

.. kernel-doc:: include/linux/wait.h
   :internal:

.. kernel-doc:: kernel/sched/wait.c
   :export:

内部函数
------------------

.. kernel-doc:: kernel/exit.c
   :internal:

.. kernel-doc:: kernel/signal.c
   :internal:

.. kernel-doc:: include/linux/kthread.h
   :internal:

.. kernel-doc:: kernel/kthread.c
   :export:

引用计数
------------------

.. kernel-doc:: include/linux/refcount.h
   :internal:

.. kernel-doc:: lib/refcount.c
   :export:

原子操作
-------

.. kernel-doc:: include/linux/atomic/atomic-instrumented.h
   :internal:

.. kernel-doc:: include/linux/atomic/atomic-arch-fallback.h
   :internal:

.. kernel-doc:: include/linux/atomic/atomic-long.h
   :internal:

内核对象操作
---------------------------

.. kernel-doc:: lib/kobject.c
   :export:

内核实用函数
------------------------

.. kernel-doc:: include/linux/kernel.h
   :internal:
   :no-identifiers: kstrtol kstrtoul

.. kernel-doc:: kernel/printk/printk.c
   :export:
   :no-identifiers: printk

.. kernel-doc:: kernel/panic.c
   :export:

设备资源管理
--------------------------

.. kernel-doc:: drivers/base/devres.c
   :export:
