SPDX 许可证标识符: GPL-2.0

=====================
为 CPUSets 设计的假 NUMA
=====================

:作者: David Rientjes <rientjes@cs.washington.edu>

使用 numa=fake 和 CPUSets 进行资源管理

本文档描述了如何将 numa=fake 的 x86_64 命令行选项与 cpusets 结合使用，以实现粗粒度内存管理。通过这个特性，你可以创建代表连续内存块的假 NUMA 节点，并将它们分配给 cpusets 及其关联的任务。这是一种限制特定类型任务可用系统内存数量的方法。
有关 cpusets 功能的更多信息，请参见 `Documentation/admin-guide/cgroup-v1/cpusets.rst`。
关于 numa=fake 命令行选项及其配置假节点的各种方式的更多信息，请参见 `Documentation/arch/x86/x86_64/boot-options.rst`。
为了介绍的目的，我们假设一个非常基础的 NUMA 模拟设置："numa=fake=4*512"。这将把我们的系统内存分成四个相等的 512MB 大小的部分，现在我们可以将这些部分分配给 cpusets 使用。随着你对这种资源控制组合的熟悉程度提高，你会确定一个更好的设置来减少你需要处理的节点数量。
一台机器可以按照如下方式进行拆分（由 dmesg 报告），使用 "numa=fake=4*512" ：

	模拟节点 0 在 0000000000000000-0000000020000000 (512MB)
	模拟节点 1 在 0000000020000000-0000000040000000 (512MB)
	模拟节点 2 在 0000000040000000-0000000060000000 (512MB)
	模拟节点 3 在 0000000060000000-0000000080000000 (512MB)
	...
在节点 0 上总页数: 130975
在节点 1 上总页数: 131072
在节点 2 上总页数: 131072
在节点 3 上总页数: 131072

根据 `Documentation/admin-guide/cgroup-v1/cpusets.rst` 中关于挂载 cpusets 文件系统的说明，你现在可以将假节点（即连续内存地址空间）分配给各个 cpusets ：

	[root@xroads /]# mkdir exampleset
	[root@xroads /]# mount -t cpuset none exampleset
	[root@xroads /]# mkdir exampleset/ddset
	[root@xroads /]# cd exampleset/ddset
	[root@xroads /exampleset/ddset]# echo 0-1 > cpus
	[root@xroads /exampleset/ddset]# echo 0-1 > mems

现在这个 cpuset ('ddset') 仅被允许访问假节点 0 和 1 的内存分配（共 1GB）。
你现在可以将任务分配给这些 cpusets 来根据分配给 mems 的假节点限制它们的内存资源：

	[root@xroads /exampleset/ddset]# echo $$ > tasks
	[root@xroads /exampleset/ddset]# dd if=/dev/zero of=tmp bs=1024 count=1G
	[1] 13425

注意 /proc/meminfo 中报告的系统内存使用情况在上述受限制的 cpuset 情况与不受限制的情况（即，在不将相同的 'dd' 命令分配到假 NUMA cpuset 的情况下运行）之间的差异：

	========	============	==========
	Name		Unrestricted	Restricted
	========	============	==========
	MemTotal	3091900 kB	3091900 kB
	MemFree		42113 kB	1513236 kB
	========	============	==========

这允许你对分配给特定 cpusets 的任务进行粗粒度内存管理。由于 cpusets 可以形成层次结构，因此你可以为各种类型的任务创建一些非常有趣的应用场景组合，以满足你的内存管理需求。
