如何将dm-crypt和swsusp一起使用
==================================================

作者：Andreas Steinmetz <ast@domdv.de>



一些先决条件：
你了解dm-crypt的工作原理。如果不了解，请访问以下网页：
http://www.saout.de/misc/dm-crypt/
你已经阅读了Documentation/power/swsusp.rst并理解其内容
你阅读过Documentation/admin-guide/initrd.rst，并且知道initrd是如何工作的
你知道如何创建或修改initrd
现在你的系统已正确设置，除了交换设备(swap)和可能包含用于加密设置和/或救援目的的小型系统的引导分区外，磁盘已加密。你甚至可能已经有了一个执行当前加密设置的initrd
此时，你也想要加密你的交换区，同时仍然能够使用swsusp进行挂起。然而，这意味着你必须能够在恢复前输入密码，或者从外部设备（如PCMCIA闪存盘或USB棒）读取密钥(s)。因此，你需要一个initrd，它会设置dm-crypt，然后要求swsusp从加密的交换设备恢复
最重要的是，你要以这样的方式设置dm-crypt，使得你从中挂起到从中恢复的交换设备在initrd以及运行系统中始终具有相同的主/次设备号。最简单的方法是始终首先用dmsetup设置这个交换设备，以便它总是看起来像下面这样：

```
brw-------  1 root root 254, 0 Jul 28 13:37 /dev/mapper/swap0
```

现在设置你的内核使用/dev/mapper/swap0作为默认恢复分区，因此你的内核.config包含：

```
CONFIG_PM_STD_PARTITION="/dev/mapper/swap0"
```

准备你的引导加载程序使用你将要创建或修改的initrd。对于lilo，最简单的设置如下所示：

```
image=/boot/vmlinuz
initrd=/boot/initrd.gz
label=linux
append="root=/dev/ram0 init=/linuxrc rw"
```

最后，你需要创建或修改你的initrd。假设你创建了一个从PCMCIA闪存卡读取所需dm-crypt设置的initrd。该卡使用ext2文件系统格式化，当插入卡片时位于/dev/hde1上。该卡至少包含名为"swapkey"的加密交换设置文件。你的initrd中的/etc/fstab包含如下内容：

```
/dev/hda1   /mnt    ext3      ro                            0 0
none        /proc   proc      defaults,noatime,nodiratime   0 0
none        /sys    sysfs     defaults,noatime,nodiratime   0 0
```

/dev/hda1包含一个未加密的迷你系统，通过从PCMCIA闪存卡读取设置来设置所有加密设备。接下来是一个适用于你的initrd的/linuxrc，允许你从加密交换区恢复，并且如果未发生恢复，则继续引导你的mini系统/dev/hda1：

```sh
#!/bin/sh
PATH=/sbin:/bin:/usr/sbin:/usr/bin
mount /proc
mount /sys
mapped=0
noresume=`grep -c noresume /proc/cmdline`
if [ "$*" != "" ]
then
  noresume=1
fi
dmesg -n 1
/sbin/cardmgr -q
for i in 1 2 3 4 5 6 7 8 9 0
do
  if [ -f /proc/ide/hde/media ]
  then
    usleep 500000
    mount -t ext2 -o ro /dev/hde1 /mnt
    if [ -f /mnt/swapkey ]
    then
      dmsetup create swap0 /mnt/swapkey > /dev/null 2>&1 && mapped=1
    fi
    umount /mnt
    break
  fi
  usleep 500000
done
killproc /sbin/cardmgr
dmesg -n 6
if [ $mapped = 1 ]
then
  if [ $noresume != 0 ]
  then
    mkswap /dev/mapper/swap0 > /dev/null 2>&1
  fi
  echo 254:0 > /sys/power/resume
  dmsetup remove swap0
fi
umount /sys
mount /mnt
umount /proc
cd /mnt
pivot_root . mnt
mount /proc
umount -l /mnt
umount /proc
exec chroot . /sbin/init $* < dev/console > dev/console 2>&1
```

请忽略上面奇怪的循环，busybox的msh不知道let语句。那么，脚本中发生了什么？
首先，我们必须决定是否尝试恢复，或者不尝试
我们不会在使用"noresume"或任何参数（如"single"或"emergency"）作为引导参数时恢复
然后我们需要使用PCMCIA闪存卡上的设置数据设置dmcrypt。如果这成功，我们需要重置交换设备，如果我们不想恢复。行"echo 254:0 > /sys/power/resume"然后尝试从第一个设备映射器设备恢复
请注意，在/sys/power/resume中设置设备非常重要，无论是否恢复，否则稍后的挂起将会失败
如果恢复开始，脚本执行在这里终止
否则，我们只需移除加密的交换分区，然后让位于 /dev/hda1 上的迷你系统来设置整个加密环境（你可以根据自己的喜好修改这部分）。

接下来是众所周知的过程：更改根文件系统，并从那里继续引导。我倾向于在继续引导之前卸载 initrd，但你可根据自己的喜好来修改这一部分。

以下是详细的翻译：

否则，我们只是简单地移除加密的交换设备，让位于 /dev/hda1 的小型系统来搭建整个加密框架（你可以按照你的需求和喜好来调整这部分）。

紧接着，我们将进行熟知的流程：更换根文件系统并从此处继续启动。我个人倾向于在继续启动前先卸载 initrd，但是否这么做取决于你，你可以根据自己的喜好来调整这一步骤。
