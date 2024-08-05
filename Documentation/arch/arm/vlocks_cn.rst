======================================
裸金属互斥的投票锁 (Voting Locks)
======================================

投票锁，或简称“vlocks”，提供了一种简单的低级互斥机制，对内存系统有着合理但最低限度的要求。
这些机制旨在用于在各中央处理器（CPU）之间协调关键活动，这些CPU在其他情况下是不一致的，在硬件没有提供其他支持此目的的机制且普通自旋锁无法使用的情况下。vlocks 利用了内存系统为单个内存位置写入操作提供的原子性。为了进行仲裁，每个CPU都会“为自己投票”，即通过将一个唯一数字存储到公共内存位置中。当所有投票都完成后，在该内存位置上看到的最终值就确定了胜者。

为了确保选举能够在有限时间内产生一个明确的结果，一个CPU只有在尚未选出胜者且选举看起来还未开始的情况下才会参与选举。

算法
---------

解释vlocks算法最简单的方法是通过一些伪代码:

```pseudo
int currently_voting[NR_CPUS] = { 0, };
int last_vote = -1; /* 尚未有投票 */

bool vlock_trylock(int this_cpu)
{
    /* 表明我们想要投票 */
    currently_voting[this_cpu] = 1;
    if (last_vote != -1) {
        /* 已经有人自愿参选 */
        currently_voting[this_cpu] = 0;
        return false; /* 不是我们自己 */
    }

    /* 让我们推荐自己 */
    last_vote = this_cpu;
    currently_voting[this_cpu] = 0;

    /* 然后等待其他人完成投票 */
    for_each_cpu(i) {
        while (currently_voting[i] != 0)
            /* 等待 */;
    }

    /* 结果 */
    if (last_vote == this_cpu)
        return true; /* 我们赢了 */
    return false;
}

bool vlock_unlock(void)
{
    last_vote = -1;
}
```

`currently_voting[]`数组为CPU提供了一种方法来确定选举是否正在进行中，其作用类似于Lamport面包店算法[1]中的“进入”数组。
然而，一旦选举开始，底层内存系统的原子性就被用来挑选胜者。这避免了需要静态优先级规则作为决胜手段，或是任何可能溢出的计数器的需求。

只要`last_vote`变量对所有CPU都是全局可见的，那么它将只包含一个值，并且一旦所有CPU清除了它们的`currently_voting`标志，这个值就不会改变。

特点和限制
------------------------

 * vlocks并非旨在实现公平。在竞争激烈的情况下，最有可能获胜的是最后一个尝试获取锁的CPU。
因此，vlocks最适合那些必须选择一个唯一胜者但具体哪个CPU获胜并不重要的情况。
* 与其他类似机制一样，vlocks对于大量CPU的情况不会扩展得很好。
vlocks 可以通过投票层级级联的方式进行扩展，以便在必要时实现更好的扩展性，如下所示是一个假设的例子，涉及 4096 个 CPU：

	/* 第一级：本地选举 */
	my_town = towns[(this_cpu >> 4) & 0xf];
	I_won = vlock_trylock(my_town, this_cpu & 0xf);
	if (I_won) {
		/* 我们赢得了城镇选举，现在尝试赢得州选举 */
		my_state = states[(this_cpu >> 8) & 0xf];
		I_won = vlock_lock(my_state, this_cpu & 0xf);
		if (I_won) {
			/* 继续向上 */
			I_won = vlock_lock(the_whole_country, this_cpu & 0xf);
			if (I_won) {
				/* ... */
			}
			vlock_unlock(the_whole_country);
		}
		vlock_unlock(my_state);
	}
	vlock_unlock(my_town);

ARM 实现
--------

当前的 ARM 实现 [2] 包含了一些超出基本算法之外的优化：

 * 通过将目前参与投票数组中的成员紧密排列在一起，我们可以用一次事务读取整个数组（前提是可能竞争锁的 CPU 数量足够小）。这减少了外部内存往返所需的次数。在 ARM 实现中，这意味着我们可以使用单一的加载和比较操作:: 

	LDR	Rt, [Rn]
	CMP	Rt, #0

   ...替代相当于以下代码的操作:: 

	LDRB	Rt, [Rn]
	CMP	Rt, #0
	LDRBEQ	Rt, [Rn, #1]
	CMPEQ	Rt, #0
	LDRBEQ	Rt, [Rn, #2]
	CMPEQ	Rt, #0
	LDRBEQ	Rt, [Rn, #3]
	CMPEQ	Rt, #0

   这样减少了快速路径的延迟，并且在有竞争的情况下还可能减少总线竞争。
优化依赖于 ARM 内存系统保证了不同大小的重叠内存访问之间的一致性，这一点类似于许多其他架构。需要注意的是我们并不关心目前参与投票数组中的哪个元素出现在寄存器 Rt 的哪位上，因此在此优化中不必担心字节序问题。
如果 CPU 数量太多以至于无法在一次事务中读取整个目前参与投票数组，则仍然需要多次事务。在这种情况下，实现使用了一个简单的循环来进行逐字的加载。所需的事务数量仍然少于逐字节加载的情况。
原则上，我们可以通过使用 LDRD 或 LDM 来进一步聚合，但为了保持代码简单，在初始实现中没有尝试这样做。
* 目前 vlocks 只用于协调那些还不能启用其缓存的 CPU 之间的同步。这意味着实现去除了许多在执行该算法时缓存内存中所需要的屏障。
紧密排列目前参与投票数组对于缓存内存不起作用，除非所有竞争锁的 CPU 都是缓存一致性的，因为来自一个 CPU 的缓存写回会覆盖其他 CPU 写入的值。（不过，如果所有 CPU 都是缓存一致性的，你可能应该使用标准的自旋锁）
* 用于 last_vote 变量的“尚无投票”值是 0（不是伪代码中的 -1）。这允许静态分配的 vlocks 仅通过将其放置在 .bss 中就可以被隐式初始化为未锁定状态。
为设置此变量的目的，给每个 CPU 的 ID 添加了一个偏移量，以确保没有 CPU 使用 0 作为其 ID。

尾声
----

最初由 Dave Martin 为 Linaro Limited 创建并记录，用于 ARM 基础的 big.LITTLE 平台，感谢 Nicolas Pitre 和 Achin Gupta 的审阅和建议。感谢 Nicolas 抓取相关邮件线程中的大部分文本并编写伪代码。
版权 (C) 2012-2013 Linaro Limited  
根据 GNU 通用公共许可协议第 2 版的条款进行分发，该条款定义于 linux/COPYING 中  
参考文献  
----------  

[1] Lamport, L. “迪杰斯特拉并发编程问题的新解决方案”，《ACM 通讯》17 卷 8 期（1974 年 8 月），453-455 页  
[https://en.wikipedia.org/wiki/Lamport%27s_bakery_algorithm](https://en.wikipedia.org/wiki/Lamport%27s_bakery_algorithm)

[2] linux/arch/arm/common/vlock.S, [www.kernel.org](http://www.kernel.org)
