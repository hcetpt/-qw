交换分区挂起
=============

首先的一些警告
.. warning::

   **重要的警告**

   如果你在挂起和恢复之间触碰硬盘上的任何内容...
...你的数据可能会丢失
如果你在文件系统已经挂载后从initrd中恢复...
...根分区可能会丢失
[这实际上是与上面相同的情况]

   如果你有不支持（ ）的使用DMA的设备，你可能会遇到一些问题。如果你的磁盘驱动不支持挂起...(IDE支持)，这也可能导致一些问题。如果你在挂起和恢复之间更改内核命令行，它可能会做一些错误的事情。如果你在系统挂起时更改硬件...嗯，这不是一个好主意；但它可能只会导致系统崩溃
（ ）挂起/恢复支持是确保安全所必需的
如果你在软件挂起之前已经挂载了USB设备上的任何文件系统，
   恢复后它们将无法访问，并且你可能会丢失数据，就好像你拔掉了带有已挂载文件系统的USB设备一样；
   请参阅下面的常见问题解答以获取详细信息。（对于更传统的电源状态如“待机”，这并不适用，因为它们通常不会关闭USB。）

交换分区：
  你需要在内核命令行中添加resume=/dev/your_swap_partition或使用/sys/power/resume来指定
交换文件：
  如果使用交换文件，还可以使用resume_offset=<数字>在内核命令行中指定恢复偏移量，或者在/sys/power/resume_offset中指定
完成准备后，通过以下方式挂起：

	echo shutdown > /sys/power/disk; echo disk > /sys/power/state

- 如果你觉得ACPI在你的系统上工作得很好，你可以尝试：

	echo platform > /sys/power/disk; echo disk > /sys/power/state

- 如果你想将休眠图像写入交换区，然后挂起到RAM（前提是你的平台支持），你可以尝试：

	echo suspend > /sys/power/disk; echo disk > /sys/power/state

- 如果你有SATA磁盘，则需要最近的内核版本，这些内核支持SATA挂起。为了使挂起和恢复生效，请确保你的磁盘驱动程序被编译到内核中——而不是模块。[有一种方法可以使用模块化的磁盘驱动程序进行挂起/恢复，详情请参见常见问题解答，但你可能不应该这样做。]

如果你想将挂起图像的大小限制为N字节，在挂起前执行：

	echo N > /sys/power/image_size

(默认情况下，其大小大约受限于可用RAM的2/5)
恢复过程检查恢复设备是否存在，
如果找到，然后检查其内容以查找休眠图像的签名。
如果两者都找到，则恢复休眠图像。
- 恢复过程可以通过两种方式触发：

  1) 在晚期初始化期间： 如果在内核命令行中指定了resume=/dev/your_swap_partition，则晚期初始化会运行恢复过程。如果恢复设备尚未被探测，则恢复过程失败并继续启动过程。
2) 从initrd或initramfs手动执行： 可以通过init脚本使用/sys/power/resume文件来运行。至关重要的是，在重新挂载任何文件系统（即使是只读）之前完成此操作，否则数据可能会损坏。

关于Linux软件挂起的目标和实现的文章
================================================

作者：Gábor Kuti
最后修订日期：2003-10-20 修订者：Pavel Machek

想法和目标
--------------

如今，在许多笔记本电脑上都有一个挂起按钮。它将机器的状态保存到文件系统或分区，并切换到待机模式。之后，当恢复机器时，保存的状态会被加载回RAM中，机器可以继续工作。它有两个实际的好处。首先，我们节省了机器关闭和后来启动所需的时间，而且当使用电池供电时，能源成本确实很高。另一个好处是，我们不必中断正在运行的程序，因此长时间计算的进程就不需要设计为可中断的。
swsusp将机器的状态保存到活动交换空间中，然后重启或关机。您必须明确地使用`resume=`内核选项指定要从中恢复的交换分区。如果找到签名，则加载并恢复保存的状态。如果作为启动参数指定了`noresume`选项，则跳过恢复过程。如果作为启动参数指定了`hibernate=nocompress`选项，则不压缩地保存休眠图像。
在系统挂起期间，您不应该添加/移除任何硬件，或者写入文件系统等。
睡眠状态总结
====================

有三种不同的接口您可以使用，/proc/acpi应该像这样工作：

在一个真正完美的世界里::

  echo 1 > /proc/acpi/sleep       # 对于待机
  echo 2 > /proc/acpi/sleep       # 对于挂起到内存
  echo 3 > /proc/acpi/sleep       # 对于挂起到内存，但更加节能
  echo 4 > /proc/acpi/sleep       # 对于挂起到磁盘
  echo 5 > /proc/acpi/sleep       # 对于不友好的关机

也许还有::

  echo 4b > /proc/acpi/sleep      # 通过s4bios挂起到磁盘

常见问题解答
==========================

问：
  好吧，我认为挂起服务器真的很愚蠢，
  但是...（Diego Zuccato）:

答：
  您为服务器购买了新的UPS。如何在不使机器关闭的情况下安装它？挂起到磁盘，重新排列电源线，然后恢复
您的服务器连接到UPS上。电源断了，而UPS指示30秒后就会失效。您该怎么办？挂起到磁盘
问：
  或许我有所遗漏，但为什么常规的I/O路径不起作用？

答：
  我们确实使用常规的I/O路径。但是我们不能在加载数据的同时将其恢复到原始位置。这将创建一个不一致的内核状态，肯定会导致错误。
Instead, we load the image into unused memory and then atomically copy it back to its original location. This, of course, implies a maximum image size of half the amount of memory.

There are two solutions to this:

  * Require half of the memory to be free during suspension. That way, you can read "new" data onto free spots and then copy.
  * Assume we have a special "polling" IDE driver that only uses memory between 0-640KB. That way, I'd have to ensure that 0-640KB is free during suspension, but otherwise, it would work.

`suspend2` shares this fundamental limitation but does not include user data and disk caches in "used memory" by saving them in advance. This means that the limitation goes away in practice.

**Q:**
Does Linux support ACPI S4?

**A:**
Yes. That's what `echo platform > /sys/power/disk` does.

**Q:**
What is 'suspend2'?

**A:**
`suspend2` is 'Software Suspend 2', a forked implementation of suspend-to-disk available as separate patches for 2.4 and 2.6 kernels from `swsusp.sourceforge.net`. It includes support for SMP, 4GB highmem, and preemption. It also has an extensible architecture that allows for arbitrary transformations on the image (compression, encryption) and arbitrary backends for writing the image (e.g., to swap or an NFS share [Work In Progress]). Questions regarding `suspend2` should be sent to the mailing list available through the `suspend2` website, not to the Linux Kernel Mailing List. We are working toward merging `suspend2` into the mainline kernel.

**Q:**
What is the freezing of tasks and why are we using it?

**A:**
The freezing of tasks is a mechanism by which user-space processes and some kernel threads are controlled during hibernation or system-wide suspend (on some architectures). See `freezing-of-tasks.txt` for details.

**Q:**
What is the difference between "platform" and "shutdown"?

**A:**
**Shutdown:**
Save state in Linux, then tell BIOS to power down.

**Platform:**
Save state in Linux, then tell BIOS to power down and blink "suspended LED."

"Platform" is actually the right thing to do where supported, but "shutdown" is most reliable (except on ACPI systems).

**Q:**
I do not understand why you have such strong objections to the idea of selective suspend.

**A:**
Do selective suspend during runtime power management, that's okay. But it's useless for suspend-to-disk. (And I do not see how you could use it for suspend-to-RAM, I hope you do not want that.)

Let's see, so you suggest doing:

  * SUSPEND all but swap device and parents
  * SNAPSHOT
  * Write image to disk
  * SUSPEND swap device and parents
  * Power down

Oh no, that does not work; if the swap device or its parents use DMA, you've corrupted data. You'd have to do:

  * SUSPEND all but swap device and parents
  * FREEZE swap device and parents
  * SNAPSHOT
  * UNFREEZE swap device and parents
  * Write
  * SUSPEND swap device and parents

Which means that you still need that FREEZE state, and you get more complicated code. (And I have not yet introduced details like system devices.)
Q: 
似乎没有一般性的、有用的行为区别来区分 SUSPEND 和 FREEZE。
A: 
当你被要求执行 FREEZE 时做 SUSPEND 总是正确的，但这可能会不必要地慢。如果你希望你的驱动程序保持简单，那么这种缓慢可能对你来说并不重要。它总能在之后得到修正。对于像磁盘这样的设备，速度确实很重要，你不会希望在 FREEZE 时进行停转。
Q: 
恢复后，系统大量分页，导致非常糟糕的交互性。
A: 
尝试在恢复后运行以下命令：

    cat /proc/[0-9]*/maps | grep / | sed 's:.* /:/:' | sort -u | while read file
    do
      test -f "$file" && cat "$file" > /dev/null
    done

运行 `swapoff -a; swapon -a` 也可能有用。
Q: 
在 swsusp 过程中设备发生了什么？它们似乎在系统挂起时被恢复了？

A: 
这是正确的。如果我们想要将镜像写入磁盘，就需要恢复它们。整个过程如下：

      **挂起部分**

      系统正在运行，用户请求挂起到磁盘。

      用户进程被停止。

      挂起(PMSG_FREEZE)：设备被冻结以防止它们干扰状态快照。

      状态快照：在禁用中断的情况下获取整个使用中的内存的副本。

      恢复()：设备被唤醒以便我们可以将镜像写入交换空间。

      将镜像写入交换空间。

      挂起(PMSG_SUSPEND)：为了能够关闭电源，设备被挂起。

      关闭电源。

      **恢复部分**

      （实际上非常相似）

      系统正在运行，用户请求挂起到磁盘。

      用户进程被停止（通常情况下没有进程，但如果是从 initrd 恢复，就不一定了）。

      从磁盘读取镜像。

      挂起(PMSG_FREEZE)：设备被冻结以防止它们干扰镜像恢复。

      镜像恢复：重写内存中的镜像。

      恢复()：设备被唤醒以便系统可以继续运行。

      恢复所有用户进程。

Q: 
这个“加密挂起镜像”是用来做什么的？

A: 
首先需要明确的是：这不是 dm-crypt 加密交换分区的替代品。它并不能保护你的计算机在挂起期间的安全。相反，它能保护在从挂起恢复后敏感数据不会泄露。
考虑以下情况：当一个保存有敏感数据的应用程序正在运行时，你进行了挂起操作。应用程序本身阻止了这些数据被换出到交换空间。然而，挂起必须将这些数据写入交换空间以便能够在之后恢复。如果没有启用挂起加密，那么你的敏感数据就会以明文的形式存储在磁盘上。这意味着在恢复后，所有直接访问用于挂起的交换分区的应用程序都能够访问这些敏感数据。如果你在恢复后不需要交换空间，那么这些数据可能会永久保留在磁盘上。因此，可能的情况是几周后你的系统遭到入侵，而你以为已经被加密和保护的敏感数据从交换分区中被检索并窃取。
为了避免这种情况发生，你应该使用“加密挂起镜像”。在挂起过程中会创建一个临时密钥，并使用该密钥对写入磁盘的数据进行加密。在恢复期间，当数据被重新读回内存时，临时密钥会被销毁，这意味着所有写入磁盘的挂起数据随后变得无法访问，因此它们不能在之后被盗取。唯一需要注意的是，在常规启动过程中尽可能早地为用于挂起的交换分区调用 `mkswap`。这可以确保任何由于挂起失败或恢复失败而产生的临时密钥从交换分区中被清除。
以下是对您提供的文本的中文翻译：

经验法则是，在系统关闭或挂起时使用加密交换分区来保护您的数据。此外，使用加密的挂起镜像来防止敏感数据在恢复后被盗。

问：
我可以将系统挂起到交换文件吗？

答：
通常来说，可以。但是，这需要您使用`resume=`和`resume_offset=`内核命令行参数，因此从交换文件恢复不能从initrd或initramfs映像启动。具体细节请参阅swsusp-and-swap-files.txt。

问：
swsusp支持的最大系统RAM大小是多少？

答：
它应该能够与高内存很好地工作。

问：
swsusp（到硬盘）是否只使用一个交换分区，还是它可以使用多个交换分区（将其合并为一个逻辑空间）？

答：
只能使用一个交换分区，抱歉。

问：
如果我的应用程序占用大量内存和交换空间（超过总系统RAM的一半），那么在该应用运行时尝试挂起到硬盘是否可能无用？

答：
不，只要您的应用程序没有调用mlock()锁定内存，它应该能正常工作。只需准备足够大的交换分区即可。

问：
对于调试挂起到硬盘的问题，哪些信息是有用的？

答：
屏幕上的最后消息总是有用的。如果出现问题，通常是一些内核驱动程序的问题，因此尽可能少加载模块会有很大帮助。我也更倾向于从控制台进行挂起操作，最好是在未运行X环境的情况下。通过以init=/bin/bash启动，然后手动执行swapon和挂起序列通常能解决问题。之后，使用最新的原生内核进行尝试也是一个好主意。

问：
如何让发行版提供支持swsusp的内核以及模块化的磁盘驱动程序（特别是SATA驱动程序）？

答：
这确实是可以做到的，先加载驱动程序，然后从initrd向/sys/power/resume文件写入。务必不要挂载任何东西，即使是只读挂载，否则您可能会丢失数据。

问：
如何使挂起过程更加详细？

答：
如果您希望在挂起过程中看到虚拟终端上非错误的内核消息，您需要将内核控制台日志级别设置为至少4（KERN_WARNING），例如通过以下方式实现：

```bash
# 保存原有的日志级别
read LOGLEVEL DUMMY < /proc/sys/kernel/printk
# 设置日志级别以便能看到进度条
# 如果级别已经高于所需，我们保持不变
if [ $LOGLEVEL -lt 5 ]; then
    echo 5 > /proc/sys/kernel/printk
fi

IMG_SZ=0
read IMG_SZ < /sys/power/image_size
echo -n disk > /sys/power/state
RET=$?
#
# 这里的逻辑是：
# 如果image_size大于0（如果没有内核支持，IMG_SZ将是零），
# 那么尝试再次将image_size设为零
```
这段代码和其解释可以翻译为：

```bash
# 如果返回值不为0，并且镜像大小不为0，则尝试使用最小镜像大小再次挂起到磁盘
if [ $RET -ne 0 -a $IMG_SZ -ne 0 ]; then
    # 设置镜像大小为0
    echo 0 > /sys/power/image_size
    # 尝试挂起到磁盘
    echo -n disk > /sys/power/state
    RET=$?
fi

# 恢复之前的日志级别
echo $LOGLEVEL > /proc/sys/kernel/printk
# 退出并返回状态码
exit $RET
```

**问题：**
如果我在USB设备上挂载了一个文件系统，当挂起到磁盘时，除非该文件系统是以“sync”方式挂载的，否则我可能会丢失数据吗？

**回答：**
确实如此……如果你断开该设备的连接，你可能会丢失数据。实际上，即使使用了"-o sync"选项，如果程序中有尚未写入到磁盘的数据（而你又断开了磁盘），或者在设备完成保存你写入的数据之前就断开了连接，你仍然可能会丢失数据。
软件挂起通常会关闭USB控制器的电源，这相当于断开所有连接到系统的USB设备。你的系统可能支持USB控制器的低功耗模式，以保持连接，在系统睡眠时使用真正的睡眠模式，如“suspend-to-RAM”或“standby”。（不要写“disk”到/sys/power/state文件中；而应写“standby”或“mem”。）我们没有看到任何硬件可以通过软件挂起到这些模式，尽管理论上一些系统可能支持不会断开USB连接的“平台”模式。
记住，从包含已挂载文件系统的磁盘驱动器拔出总是不好的主意。即使你的系统处于睡眠状态，也是如此！最安全的做法是在挂起之前卸载所有可移动媒体上的文件系统（如USB、Firewire、CompactFlash、MMC、外部SATA或IDE热插拔托架），然后在恢复后重新挂载它们。
这个问题有一个解决方法。更多信息，请参阅Documentation/driver-api/usb/persist.rst。

**问题：**
我可以使用LVM下的交换分区进行挂起到磁盘吗？

**回答：**
是也不是。你可以成功地挂起，但内核将无法自己恢复。你需要一个能够识别恢复情况的initramfs，激活包含交换卷的逻辑卷（但不要触碰任何文件系统！），最终调用以下命令：

    echo -n "$major:$minor" > /sys/power/resume

其中$major和$minor分别是交换卷的主要和次要设备号。
uswsusp也支持LVM。更多信息请见http://suspend.sourceforge.net/

**问题：**
我从2.6.15升级到了2.6.16的内核，两个内核都是用相似的配置文件编译的。不过我发现2.6.16相比2.6.15在挂起到磁盘（以及恢复）方面慢得多。这是为什么？有什么办法可以加快速度吗？

**回答：**
这是因为挂起镜像的大小现在比2.6.15大（通过保存更多数据，我们可以得到更响应的系统恢复后）
有一个/sys/power/image_size的控制开关来控制镜像的大小。如果你将其设置为0（例如，作为root用户执行`echo 0 > /sys/power/image_size`），2.6.15的行为应该会被恢复。如果它仍然太慢，可以参考suspend.sf.net -- 用户空间挂起更快，并支持LZF压缩以进一步加快速度。
