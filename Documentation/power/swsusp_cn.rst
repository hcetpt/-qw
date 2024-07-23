在进行交换挂起之前
==================

首先，一些警告
.. warning::

   **重大警告**

   如果你在挂起到恢复期间对硬盘上的任何内容进行操作...
...你的数据将不复存在
如果你在文件系统已挂载后从initrd中恢复...
...根分区将丢失
[这实际上与上述情况相同]

   如果你有使用DMA的不受支持的设备，你可能会遇到一些问题。如果磁盘驱动程序不支持挂起...(IDE是支持的)，也可能导致一些问题。如果你在挂起和恢复之间更改内核命令行，可能会出现错误的操作。如果你在系统挂起时更换硬件...嗯，这不是个好主意；但它可能只会导致系统崩溃。
( ) 挂起/恢复支持是确保安全所必需的
如果你在软件挂起前有USB设备上的文件系统已挂载，
   恢复后它们将无法访问，你可能会丢失数据，就像你在有已挂载文件系统的USB设备上拔掉一样；
   详情请参阅下方的常见问题解答。(对于更传统的电源状态如"待机"，这并不适用，通常这些状态不会关闭USB。)

交换分区：
  需要在内核命令行中添加resume=/dev/your_swap_partition或使用/sys/power/resume指定它
交换文件：
  如果使用交换文件，也可以使用resume_offset=<数字>在内核命令行中指定恢复偏移量，或在/sys/power/resume_offset中指定它
完成准备后，通过以下方式挂起：

echo shutdown > /sys/power/disk; echo disk > /sys/power/state

- 如果你觉得ACPI在你的系统上工作得很好，你可以尝试：

echo platform > /sys/power/disk; echo disk > /sys/power/state

- 如果你想将休眠图像写入交换区，然后挂起到RAM（前提是你的平台支持），你可以尝试：

echo suspend > /sys/power/disk; echo disk > /sys/power/state

- 如果你有SATA磁盘，你需要具有SATA挂起支持的较新内核。为了使挂起和恢复工作，确保你的磁盘驱动程序是内建到内核中的--不是模块。[有一种方法可以使用模块化的磁盘驱动程序进行挂起/恢复，见常见问题解答，但你可能不应该这样做。]

如果你想将挂起图像大小限制为N字节，在挂起前执行：

echo N > /sys/power/image_size

(默认情况下，它被限制在可用RAM的大约2/5左右)
恢复过程检查恢复设备是否存在，
如果找到，然后检查内容中是否有休眠图像的签名。
如果两者都找到，它将恢复休眠图像。
- 恢复过程可能以两种方式触发：

1) 在lateinit期间： 如果在内核命令行上指定了resume=/dev/your_swap_partition，则lateinit运行恢复过程。如果恢复设备尚未被探测，恢复过程失败且启动继续。
2) 手动从initrd或initramfs中： 可以通过使用/sys/power/resume文件从初始化脚本中运行。至关重要的是，在重新挂载任何文件系统（即使是只读）之前完成此操作，否则数据可能会损坏。

关于Linux软件挂起的目标和实现的文章
================================================

作者：Gábor Kuti
最后修订日期：2003-10-20 由Pavel Machek

想法和目标
-------------------------

现在在许多笔记本电脑中常见的是，它们具有一个挂起按钮。它将机器的状态保存到文件系统或分区，然后切换到待机模式。稍后恢复机器时，将保存的状态加载回RAM中，机器可以继续其工作。它有两个实际的好处。首先，我们节省了机器关闭和后来启动所需的时间，当从电池运行时，能源成本非常高。另一个好处是，我们不必中断我们的程序，因此长时间计算的进程不应该需要被设计为可中断的。
swsusp将机器的状态保存到活动交换空间中，然后重启或关机。你必须明确地使用`resume=`内核选项指定要从中恢复的交换分区。如果找到签名，它会加载并恢复保存的状态。如果将`noresume`作为引导参数指定，它将跳过恢复过程。如果将`hibernate=nocompress`作为引导参数指定，它将在不压缩的情况下保存休眠图像。
同时在系统挂起期间，你不应添加/移除任何硬件，写入文件系统等。

睡眠状态概览
====================

有三种不同的接口你可以使用，/proc/acpi应该像这样工作：

在一个真正完美的世界里::

  将1写入/proc/acpi/sleep       # 用于待机
  将2写入/proc/acpi/sleep       # 用于挂起到RAM
  将3写入/proc/acpi/sleep       # 用于挂起到RAM，但更节能
  将4写入/proc/acpi/sleep       # 用于挂起到磁盘
  将5写入/proc/acpi/sleep       # 用于不友好的关机系统

也许还有::

  将4b写入/proc/acpi/sleep      # 通过s4bios挂起到磁盘

常见问题解答
==========================

问：
  好吧，我认为挂起服务器是一件非常愚蠢的事情，
  但是...（Diego Zuccato）：

答：
  你为你的服务器购买了新的UPS。如何在不使机器停机的情况下安装它？挂起到磁盘，重新布置电源线，恢复
你的服务器在UPS上。电源断了，UPS显示30秒后将失效。你该怎么做？挂起到磁盘
问：
  或许我遗漏了什么，但为什么常规的I/O路径不行？

答：
  我们确实使用常规的I/O路径。然而，我们不能在加载数据时将其恢复到原始位置。这将创建一个不一致的内核状态，这肯定会导致出错。
Instead, we load the image into unused memory and then atomically copy it back to its original location. This, of course, implies a maximum image size of half the amount of memory.

There are two solutions to this:

  * Require half of the memory to be free during suspend. That way, you can read "new" data onto free spots and then copy.
  * Assume we have a special "polling" IDE driver that only uses memory between 0-640KB. That way, I'd have to ensure that 0-640KB is free during suspending, but otherwise, it would work.

`suspend2` shares this fundamental limitation but does not include user data and disk caches in "used memory" by saving them in advance. This means that the limitation effectively disappears in practice.

**Q:** Does Linux support ACPI S4?

**A:** Yes. That's what `echo platform > /sys/power/disk` does.

**Q:** What is 'suspend2'?

**A:** `suspend2` is 'Software Suspend 2', a forked implementation of suspend-to-disk available as separate patches for 2.4 and 2.6 kernels from `swsusp.sourceforge.net`. It includes support for SMP, 4GB highmem, and preemption. It also has an extensible architecture that allows for arbitrary transformations on the image (compression, encryption) and arbitrary backends for writing the image (e.g., to swap or an NFS share [Work In Progress]). Questions regarding `suspend2` should be sent to the mailing list available through the `suspend2` website, not to the Linux Kernel Mailing List. We are working toward merging `suspend2` into the mainline kernel.

**Q:** What is the freezing of tasks and why are we using it?

**A:** The freezing of tasks is a mechanism by which user-space processes and some kernel threads are controlled during hibernation or system-wide suspend (on some architectures). See `freezing-of-tasks.txt` for details.

**Q:** What is the difference between "platform" and "shutdown"?

**A:** 
- **Shutdown:**
  - Save state in Linux, then tell BIOS to power down.
- **Platform:**
  - Save state in Linux, then tell BIOS to power down and blink "suspended LED."

"Platform" is actually the right thing to do where supported, but "shutdown" is most reliable (except on ACPI systems).

**Q:** I do not understand why you have such strong objections to the idea of selective suspend.

**A:** Conduct selective suspend during runtime power management, which is okay. But it's useless for suspend-to-disk. (And I don't see how you could use it for suspend-to-RAM, I hope you don't want that.)

Let's see, so you suggest:

  * SUSPEND all but swap device and parents.
  * Snapshot.
  * Write image to disk.
  * SUSPEND swap device and parents.
  * Power down.

Oh no, that does not work, if the swap device or its parents use DMA, you've corrupted data. You'd have to do:

  * SUSPEND all but swap device and parents.
  * FREEZE swap device and parents.
  * Snapshot.
  * UNFREEZE swap device and parents.
  * Write.
  * SUSPEND swap device and parents.

This means that you still need that FREEZE state, and you get more complicated code. (And I have not yet introduced details like system devices.)
Q: 
似乎没有普遍适用的行为区别来区分 SUSPEND 和 FREEZE。

A: 
当你被要求执行 FREEZE 时，选择 SUSPEND 总是正确的，但可能会不必要地缓慢。如果你希望你的驱动保持简单，速度可能对你来说并不重要，它总能稍后得到修正。
对于像磁盘这样的设备，速度确实很重要，你不想在 FREEZE 时进行停转。

Q: 
恢复后，系统大量分页，导致非常糟糕的交互性。

A: 
尝试在恢复后运行以下命令：

    cat /proc/[0-9]*/maps | grep / | sed 's:.* /:/:' | sort -u | while read file
    do
      test -f "$file" && cat "$file" > /dev/null
    done

swapoff -a; swapon -a 也可能有用。

Q: 
swsusp 过程中设备发生了什么？它们似乎在系统挂起时被恢复了？

A: 
那是正确的。如果我们想要将镜像写入磁盘，我们需要恢复它们。整个序列如下：

      **挂起部分**

      正在运行的系统，用户请求挂起到磁盘

      用户进程停止

      挂起(PMSG_FREEZE)：设备被冻结以防止干扰状态快照

      状态快照：在禁用中断的情况下，复制整个使用中的内存

      恢复()：唤醒设备以便我们可以将镜像写入交换区

      将镜像写入交换区

      挂起(PMSG_SUSPEND)：挂起设备以便我们可以关闭电源

      关闭电源

      **恢复部分**

      （实际上非常相似）

      正在运行的系统，用户请求挂起到磁盘

      用户进程停止（通常情况下没有，但如果从 initrd 恢复，没人知道）

      从磁盘读取镜像

      挂起(PMSG_FREEZE)：设备被冻结以防止干扰镜像恢复

      镜像恢复：重写内存与镜像

      恢复()：唤醒设备以便系统可以继续

      解冻所有用户进程

Q: 
“加密挂起镜像”是做什么用的？

A: 
首先，这不是 dm-crypt 加密交换区的替代品。
它不能在计算机处于挂起状态时提供保护。相反，它在从挂起状态恢复后防止敏感数据泄露。
想象一下以下情况：你在运行一个应用程序时进行了挂起，该程序在内存中保存了敏感数据。应用程序本身阻止数据被交换出去。然而，挂起必须将这些数据写入交换区，以便以后能够恢复。如果没有挂起加密，你的敏感数据将以明文形式存储在磁盘上。这意味着，在恢复后，所有可以直接访问用于挂起的交换设备的应用程序都可以访问你的敏感数据。如果你恢复后不需要交换区，这些数据可能会长时间保留在磁盘上。因此，几周后你的系统可能遭到入侵，并且你认为已加密并受保护的敏感数据可能从交换设备中被检索和窃取。

为了防止这种情况，你应该使用“加密挂起镜像”。
在挂起过程中，会创建一个临时密钥，此密钥用于加密写入磁盘的数据。当数据在恢复期间重新读入内存后，临时密钥被销毁，这意味着所有在挂起期间写入磁盘的数据随后变得无法访问，因此无法在之后被窃取。
唯一需要你注意的是，你必须尽可能早地在常规引导过程中为用于挂起的交换分区调用 'mkswap'。这确保了任何因挂起错误或恢复失败而产生的临时密钥从交换设备中被擦除。
以下为翻译后的中文：

经验法则：在系统关闭或挂起时使用加密交换分区来保护您的数据。另外，使用加密的挂起映像防止敏感数据在恢复后被窃取。

问：
我可以在交换文件中挂起到内存吗？

答：
通常，可以。但是，这需要您使用“resume=”和“resume_offset=”内核命令行参数，因此从交换文件恢复不能从initrd或initramfs图像开始。请参阅swsusp-and-swap-files.txt以获取详细信息。

问：
swsusp支持的最大系统RAM大小是多少？

答：
它应该与高内存配合工作得不错。

问：
swsusp（到磁盘）是否只使用一个交换分区，还是可以使用多个交换分区（将它们聚合为一个逻辑空间）？

答：
仅使用一个交换分区，抱歉。

问：
如果我的应用程序（s）导致大量内存和交换空间被使用（超过总系统RAM的一半），在该应用程序运行时尝试挂起到磁盘是否很可能无用？

答：
不，只要您的应用程序没有调用mlock()，它应该可以正常工作。只需准备足够大的交换分区即可。

问：
对于调试挂起到磁盘的问题，哪些信息是有用的？

答：
嗯，屏幕上的最后消息总是有用的。如果有问题，通常是一些内核驱动程序，因此尽可能少地加载模块会帮助很多。我也更喜欢人们从控制台挂起，最好是在没有运行X的情况下。使用init=/bin/bash引导，然后使用swapon并手动启动挂起序列通常就可以解决问题。然后，尝试使用最新的vanilla内核是一个好主意。

问：
如何让发行版能够提供具有模块化磁盘驱动程序（特别是SATA）的swsusp支持内核？

答：
嗯，这是可以做到的，加载驱动程序，然后从initrd向/sys/power/resume文件写入echo。一定要确保不挂载任何东西，即使是只读挂载，否则您将丢失数据。

问：
如何使挂起过程更详细？

答：
如果您想在虚拟终端上看到任何非错误的内核消息，这是内核在挂起期间切换到的，您必须将内核控制台日志级别设置为至少4（KERN_WARNING），例如通过以下方式实现：

# 保存旧的日志级别
read LOGLEVEL DUMMY < /proc/sys/kernel/printk
# 设置日志级别以便我们看到进度条
# 如果级别高于所需，我们保持不变
if [ $LOGLEVEL -lt 5 ]; then
	echo 5 > /proc/sys/kernel/printk
fi

IMG_SZ=0
read IMG_SZ < /sys/power/image_size
echo -n disk > /sys/power/state
RET=$?
#
# 这里的逻辑是：
# 如果image_size大于0（如果没有内核支持，IMG_SZ将为零），
# 那么尝试再次将image_size设置为零
这段代码和回答主要涉及Linux系统中的挂起到磁盘（suspend to disk）功能，以及与之相关的USB设备数据安全、LVM下的swap分区使用、不同内核版本间性能差异的讨论。以下是翻译后的中文内容：

代码翻译：
如果[$RET不等于0并且$IMG_SZ不等于0]；那么#尝试以最小图像大小再次挂起
                将0写入/sys/power/image_size
                将disk写入/sys/power/state
                RET=$?
        结束条件

#恢复之前的日志级别
将$LOGLEVEL写入/proc/sys/kernel/printk
退出$RET

问题：
如果我在USB设备上挂载了文件系统，并且挂起到磁盘，除非文件系统是以"sync"方式挂载的，否则我是否会丢失数据？

回答：
确实如此...如果你断开该设备，你可能会丢失数据。
事实上，即使使用"-o sync"，如果你的程序在缓冲区中有尚未写入你断开连接的磁盘的信息，或者在设备完成保存你写入的数据之前断开，你也可能丢失数据，
软件挂起通常会关闭USB控制器的电源，这相当于断开了所有连接到你系统的USB设备。
你的系统可能支持USB控制器在系统睡眠时的低功耗模式，保持连接，使用真正的睡眠模式如"suspend-to-RAM"或"standby"。（不要向/sys/power/state文件写入"disk"；写入"standby"或"mem"。）我们没有看到任何硬件可以通过软件挂起来使用这些模式，尽管理论上一些系统可能支持不会中断USB连接的"平台"模式。
记住，拔掉包含已挂载文件系统的磁盘驱动器总是一个坏主意。即使当你的系统处于睡眠状态时也是如此！最安全的做法是在挂起之前卸载所有可移动媒体（如USB、Firewire、CompactFlash、MMC、外部SATA，甚至IDE热插拔托架）上的文件系统；然后在恢复后重新挂载它们。
这个问题有一个解决方法。更多信息，请参阅Documentation/driver-api/usb/persist.rst

问题：
我可以使用LVM下的交换分区进行挂起到磁盘吗？

回答：
可以也不可以。你可以成功挂起，但是内核将无法自行恢复。你需要一个能够识别恢复情况的initramfs，激活包含交换卷的逻辑卷（但不要触碰任何文件系统！），并最终调用：

    echo -n "$major:$minor" > /sys/power/resume

其中$major和$minor分别是交换卷的主次设备号。
uswsusp也支持LVM。请参见http://suspend.sourceforge.net/

问题：
我从2.6.15升级内核到了2.6.16。两个内核都是使用类似的配置文件编译的。无论如何，我发现2.6.16上的挂起到磁盘（和恢复）比2.6.15慢得多。这可能是为什么？或者我如何加快速度？

回答：
这是因为挂起图像的大小现在大于2.6.15（通过保存更多数据，我们可以在恢复后获得更响应的系统）
有/sys/power/image_size控制旋钮来控制图像的大小。如果你将其设置为0（例如，作为root用户执行echo 0 > /sys/power/image_size），则应恢复2.6.15的行为。如果仍然太慢，请查看suspend.sf.net--用户空间挂起更快，并支持LZF压缩以进一步加速。
