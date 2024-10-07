如何一起使用 dm-crypt 和 swsusp
=======================================

作者：Andreas Steinmetz <ast@domdv.de>

一些前提条件：
- 您了解 dm-crypt 的工作原理。如果不了解，请访问以下网页：http://www.saout.de/misc/dm-crypt/
- 您已经阅读了 Documentation/power/swsusp.rst 并理解其内容
- 您已阅读了 Documentation/admin-guide/initrd.rst 并了解 initrd 的工作方式
- 您知道如何创建或修改 initrd

现在您的系统已正确设置，除了交换设备（swap）和可能包含用于加密设置和/或救援目的的小型系统的启动分区外，磁盘已加密。您甚至可能已经有了一个执行当前加密设置的 initrd。
此时，您想加密您的交换区，但仍然希望可以使用 swsusp 暂停。然而，这意味着您需要能够在恢复前输入密码或从外部设备（如 PCMCIA 闪存卡或 USB 闪存驱动器）读取密钥。因此，您需要一个 initrd，该 initrd 设置 dm-crypt 并要求 swsusp 从加密的交换设备中恢复。
最重要的是，您需要以这样的方式设置 dm-crypt，使得您从中暂停/恢复的交换设备在 initrd 中以及运行系统中的主/次号始终相同。最简单的方法是始终先用 dmsetup 设置此交换设备，以便它始终看起来像下面这样：

```
brw-------  1 root root 254, 0 Jul 28 13:37 /dev/mapper/swap0
```

现在将内核配置为使用 /dev/mapper/swap0 作为默认恢复分区，因此您的内核 .config 包含：

```
CONFIG_PM_STD_PARTITION="/dev/mapper/swap0"
```

准备您的引导加载程序以使用您将创建或修改的 initrd。对于 lilo，最简单的设置如下：

```
image=/boot/vmlinuz
initrd=/boot/initrd.gz
label=linux
append="root=/dev/ram0 init=/linuxrc rw"
```

最后，您需要创建或修改您的 initrd。假设您创建了一个从 PCMCIA 闪存卡读取所需 dm-crypt 设置的 initrd。当插入卡片时，卡片被格式化为 ext2 文件系统，并位于 /dev/hde1。卡片至少包含一个名为 "swapkey" 的文件，其中包含加密交换设置。您的 initrd 中的 /etc/fstab 包含类似以下的内容：

```
/dev/hda1   /mnt    ext3      ro                            0 0
none        /proc   proc      defaults,noatime,nodiratime   0 0
none        /sys    sysfs     defaults,noatime,nodiratime   0 0
```

/dev/hda1 包含一个未加密的小型系统，该系统通过从 PCMCIA 闪存卡读取设置来设置所有加密设备。接下来是一个 /linuxrc，允许您从加密交换区恢复并在不恢复的情况下继续引导到 /dev/hda1 上的小型系统：

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

请注意上面的奇怪循环，busybox 的 msh 不支持 let 命令。现在，脚本中发生了什么？
首先，我们需要决定是否尝试恢复。
如果以 "noresume" 或任何参数（如 "single" 或 "emergency"）作为引导参数启动，则我们不会恢复。
然后我们需要使用 PCMCIA 闪存卡上的设置数据设置 dmcrypt。如果成功，我们需要重置交换设备，除非我们不想恢复。行 "echo 254:0 > /sys/power/resume" 尝试从第一个设备映射器设备恢复。
注意，无论是否恢复，在 /sys/power/resume 设置设备非常重要，否则稍后的暂停会失败。
如果恢复开始，脚本执行在此处终止。
否则，我们只需移除加密的交换设备，并将其留给位于 /dev/hda1 的迷你系统来设置整个加密环境（你可以根据自己的喜好修改这一部分）。
接下来是众所周知的过程，即更改根文件系统并从那里继续启动。我倾向于在继续启动之前卸载 initrd，但你可以根据自己的喜好修改这一部分。
