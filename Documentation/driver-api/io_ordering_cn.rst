==============================================
对内存映射地址的I/O写操作进行排序
==============================================

在某些平台上，所谓的内存映射I/O是弱序的。在这种平台上，驱动程序编写者负责确保对其设备的内存映射地址的I/O写操作按预期顺序到达。这通常是通过读取一个“安全”的设备或桥接寄存器来实现的，这样可以导致I/O芯片组在执行任何读操作之前刷新待处理的写操作到设备。驱动程序通常会在由自旋锁保护的关键代码段退出前立即使用这种技术。这将确保后续对I/O空间的写操作只在所有之前的写操作之后发生（很像内存屏障指令mb()，只是针对I/O操作）。
下面是一个来自假设设备驱动程序的具体示例：

		..
CPU A:  spin_lock_irqsave(&dev_lock, flags)
	CPU A:  val = readl(my_status);
	CPU A:  ..
CPU A:  writel(newval, ring_ptr);
	CPU A:  spin_unlock_irqrestore(&dev_lock, flags)
		..
CPU B:  spin_lock_irqsave(&dev_lock, flags)
	CPU B:  val = readl(my_status);
	CPU B:  ..
CPU B:  writel(newval2, ring_ptr);
	CPU B:  spin_unlock_irqrestore(&dev_lock, flags)
		..

在上述情况下，设备可能会先收到newval2再收到newval，这可能会引起问题。不过修复它很简单：

		..
CPU A:  spin_lock_irqsave(&dev_lock, flags)
	CPU A:  val = readl(my_status);
	CPU A:  ..
CPU A:  writel(newval, ring_ptr);
	CPU A:  (void)readl(safe_register); /* 可能是一个配置寄存器？ */
	CPU A:  spin_unlock_irqrestore(&dev_lock, flags)
		..
CPU B:  spin_lock_irqsave(&dev_lock, flags)
	CPU B:  val = readl(my_status);
	CPU B:  ..
CPU B:  将newval2写入到ring_ptr；
CPU B:  从safe_register进行读取（可能是一个配置寄存器？）；
CPU B:  使用flags恢复中断并解锁dev_lock

这里，从safe_register的读操作会导致I/O芯片组先刷新任何待处理的写操作，然后才将读请求发送给芯片组，这样可以防止可能出现的数据损坏。
