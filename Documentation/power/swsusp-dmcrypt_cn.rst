如何将 dm-crypt 和 swsusp 一起使用
=======================================

作者: Andreas Steinmetz <ast@domdv.de>



一些前提条件：
您了解 dm-crypt 的工作原理。如果不了解，请访问以下网页：
http://www.saout.de/misc/dm-crypt/
您已经阅读了 Documentation/power/swsusp.rst 并理解其内容
您已经阅读了 Documentation/admin-guide/initrd.rst 并了解 initrd 的工作原理
您知道如何创建或修改 initrd
现在您的系统已正确设置，除了交换设备（swap device）和可能包含用于加密设置或救援目的的小型系统的启动分区之外，磁盘都已加密。
此时，您想加密交换区，同时仍能使用 swsusp 进行挂起。但是这意味着您必须能够在恢复之前输入密码或从外部设备（如 PCMCIA 闪存盘或 USB 棒）读取密钥。因此，您需要一个 initrd，该 initrd 设置 dm-crypt 并请求 swsusp 从加密的交换区恢复。
最重要的是，您需要以这样的方式设置 dm-crypt，即您从中挂起/恢复的交换设备在 initrd 和运行中的系统中始终具有相同的主/次号。最简单的方法是始终首先通过 dmsetup 设置此交换设备，以便它总是看起来像下面这样：

```
brw-------  1 root root 254, 0 Jul 28 13:37 /dev/mapper/swap0
```

现在设置您的内核以使用 /dev/mapper/swap0 作为默认恢复分区，所以您的内核配置文件包含如下内容：

```
CONFIG_PM_STD_PARTITION="/dev/mapper/swap0"
```

准备您的引导加载程序以使用您将创建或修改的 initrd。对于 lilo，最简单的设置如下所示：

```
image=/boot/vmlinuz
initrd=/boot/initrd.gz
label=linux
append="root=/dev/ram0 init=/linuxrc rw"
```

最后，您需要创建或修改您的 initrd。假设您创建了一个从 PCMCIA 闪存卡读取所需的 dm-crypt 设置的 initrd。当插入卡片时，该卡格式化为 ext2 文件系统，并位于 /dev/hde1。该卡至少包含一个名为 "swapkey" 的文件，其中包含加密交换区的设置。您的 initrd 中的 /etc/fstab 包含类似以下的内容：

```
/dev/hda1   /mnt    ext3      ro                            0 0
none        /proc   proc      defaults,noatime,nodiratime   0 0
none        /sys    sysfs     defaults,noatime,nodiratime   0 0
```

/dev/hda1 包含一个未加密的小型系统，该系统通过从 PCMCIA 闪存卡读取设置来设置所有加密设备。接下来是一个用于您的 initrd 的 /linuxrc 脚本，它允许您从加密交换区恢复，并且如果未发生恢复，则继续使用 /dev/hda1 上的小型系统启动：

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

请忽略上面奇怪的循环，busybox 的 msh 不支持 let 命令。现在，脚本中发生了什么？
首先，我们需要决定是否尝试恢复。
如果我们使用 "noresume" 或任何其他 init 参数（如 "single" 或 "emergency"）启动，则不会恢复。
然后我们需要使用 PCMCIA 闪存卡上的设置数据设置 dm-crypt。如果设置成功，我们需要重置交换设备，除非我们不想恢复。"echo 254:0 > /sys/power/resume" 这一行试图从第一个设备映射器设备恢复。
请注意，在 /sys/power/resume 中设置设备非常重要，无论是否恢复，否则后续的挂起将会失败。
如果开始恢复，脚本执行在此处终止。
否则，我们只需移除加密的交换分区，并将整个加密设置工作留给位于 /dev/hda1 上的迷你系统（你可以根据自己的喜好来修改这部分）。接下来是大家熟知的过程：更改根文件系统并从那里继续启动。我个人倾向于在继续启动之前卸载 initrd（初始ram磁盘），但你可以根据自己的喜好来调整这一部分。
