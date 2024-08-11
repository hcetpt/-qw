================
SMP IRQ 亲和性
================

变更日志：
	- 起始者：Ingo Molnar <mingo@redhat.com>
	- 更新者：Max Krasnyansky <maxk@qualcomm.com>

/proc/irq/IRQ#/smp_affinity 和 /proc/irq/IRQ#/smp_affinity_list 指定了给定的中断源允许的目标 CPU。它是一个允许的 CPU 的位掩码（smp_affinity）或 CPU 列表（smp_affinity_list）。不允许关闭所有 CPU，如果一个中断控制器不支持 IRQ 亲和性，则该值将不会从默认设置（即所有 CPU）改变。
/proc/irq/default_smp_affinity 指定了适用于所有非活动 IRQ 的默认亲和性掩码。一旦 IRQ 被分配/激活，其亲和性位掩码将被设置为默认掩码。之后可以按照上面描述的方式进行更改。
默认掩码是 0xffffffff。
下面是一个将 IRQ44（eth1）限制到 CPU0-3 然后限制到 CPU4-7 的示例（这是一个 8 核 SMP 机器）：

	[root@moon 44]# cd /proc/irq/44
	[root@moon 44]# cat smp_affinity
	ffffffff

	[root@moon 44]# echo 0f > smp_affinity
	[root@moon 44]# cat smp_affinity
	0000000f
	[root@moon 44]# ping -f h
	PING hell (195.4.7.3): 56 data bytes
	..
--- hell ping statistics ---
	6029 packets transmitted, 6027 packets received, 0% packet loss
	round-trip min/avg/max = 0.1/0.1/0.4 ms
	[root@moon 44]# cat /proc/interrupts | grep 'CPU\|44:'
		CPU0       CPU1       CPU2       CPU3      CPU4       CPU5        CPU6       CPU7
	44:       1068       1785       1785       1783         0          0           0         0    IO-APIC-level  eth1

如上所示，IRQ44 只被发送到了前四个处理器（0-3）。
现在让我们将这个 IRQ 限制到 CPU4-7：

	[root@moon 44]# echo f0 > smp_affinity
	[root@moon 44]# cat smp_affinity
	000000f0
	[root@moon 44]# ping -f h
	PING hell (195.4.7.3): 56 data bytes
	.
--- hell ping statistics ---
	2779 packets transmitted, 2777 packets received, 0% packet loss
	round-trip min/avg/max = 0.1/0.5/585.4 ms
	[root@moon 44]# cat /proc/interrupts | grep 'CPU\|44:'
		CPU0       CPU1       CPU2       CPU3      CPU4       CPU5        CPU6       CPU7
	44:       1068       1785       1785       1783      1784       1069        1070       1069   IO-APIC-level  eth1

这次 IRQ44 只被发送到了最后四个处理器，即 CPU0-3 的计数器没有变化。
下面是一个将同一个 IRQ（44）限制到 CPU 1024 到 1031 的示例：

	[root@moon 44]# echo 1024-1031 > smp_affinity_list
	[root@moon 44]# cat smp_affinity_list
	1024-1031

需要注意的是，如果使用位掩码来实现这一点，则需要有 32 个零位掩码跟随相关的位。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
