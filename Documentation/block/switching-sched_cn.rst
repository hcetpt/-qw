==切换调度器==

每个I/O队列都有一组与之关联的I/O调度器可调参数。这些参数控制着I/O调度器的工作方式。你可以在以下路径找到这些条目：

	/sys/block/<设备>/queue/iosched

假设你已经在/sys上挂载了sysfs。如果你没有挂载sysfs，可以通过以下命令进行挂载：

	# mount none /sys -t sysfs

可以实时地为特定块设备更改I/O调度器，选择mq-deadline、none、bfq或kyber调度器——这可能会提高该设备的吞吐量。
要设置特定的调度器，只需执行如下操作：

	echo SCHEDNAME > /sys/block/DEV/queue/scheduler

其中SCHEDNAME是已定义的I/O调度器名称，DEV是设备名（如hda、hdb、sga等）。
定义的调度器列表可通过执行“cat /sys/block/DEV/queue/scheduler”来查看——有效的名称将被列出，并且当前选定的调度器会用括号标出：

  # cat /sys/block/sda/queue/scheduler
  [mq-deadline] kyber bfq none
  # echo none >/sys/block/sda/queue/scheduler
  # cat /sys/block/sda/queue/scheduler
  [none] mq-deadline kyber bfq
