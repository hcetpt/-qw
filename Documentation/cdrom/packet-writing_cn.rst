包写入
==============

快速入门
---------------------

- 在块设备部分选择包支持，并在文件系统部分选择UDF支持
- 编译并安装内核和模块，然后重启
- 您需要 udftools 包（pktsetup、mkudffs、cdrwtool）
从 https://github.com/pali/udftools 下载

- 获取一张新的 CD-RW 碟片并进行格式化（假设 CD-RW 是 hdc，请根据实际情况替换）:

```shell
# cdrwtool -d /dev/hdc -q
```

- 设置您的刻录机:

```shell
# pktsetup dev_name /dev/hdc
```

- 现在您可以挂载 `/dev/pktcdvd/dev_name` 并将文件复制到其中。尽情享受吧:

```shell
# mount /dev/pktcdvd/dev_name /cdrom -t udf -o rw,noatime
```

包写入 DVD-RW 媒体
-------------------------------

如果 DVD-RW 碟片处于所谓的“受限重写”模式，则可以像使用 CD-RW 碟片一样对其进行写入。要将碟片置于受限重写模式，运行:

```shell
# dvd+rw-format /dev/hdc
```

然后您可以像使用 CD-RW 碟片一样使用该碟片:

```shell
# pktsetup dev_name /dev/hdc
# mount /dev/pktcdvd/dev_name /cdrom -t udf -o rw,noatime
```

包写入 DVD+RW 媒体
-------------------------------

根据 DVD+RW 规范，支持 DVD+RW 碟片的驱动器应实现“真正的随机写入，粒度为 2KB”，这意味着可以在这样的碟片上放置任何块大小 >= 2KB 的文件系统。例如，应该能够做到:

```shell
# dvd+rw-format /dev/hdc   (仅当碟片从未被格式化时需要)
# mkudffs /dev/hdc
# mount /dev/hdc /cdrom -t udf -o rw,noatime
```

然而，有些驱动器并不遵循规范，期望主机在 32KB 边界处执行对齐写入。其他驱动器确实遵循规范，但如果写入未对齐至 32KB，则会出现严重的性能问题。
两个问题都可以通过使用 pktcdvd 驱动器来解决，该驱动器始终生成对齐写入:

```shell
# dvd+rw-format /dev/hdc
# pktsetup dev_name /dev/hdc
# mkudffs /dev/pktcdvd/dev_name
# mount /dev/pktcdvd/dev_name /cdrom -t udf -o rw,noatime
```

包写入 DVD-RAM 媒体
--------------------------------

DVD-RAM 碟片可以随机写入，因此使用 pktcdvd 驱动器并非必要。但是，使用 pktcdvd 驱动器可以像对 DVD+RW 媒体那样提高性能。

注释
-----

- 通常，CD-RW 媒体不能被重写超过大约 1000 次，因此为了避免不必要的媒体磨损，您应该始终使用 noatime 挂载选项
- 缺陷管理（即自动重新映射坏扇区）尚未实现，因此如果碟片磨损，您可能会遇到一些文件系统损坏
- 由于 pktcdvd 驱动器使碟片看起来像是一个具有 2KB 块大小的常规块设备，因此您可以在碟片上放置任何您喜欢的文件系统。例如，运行:

```shell
# /sbin/mke2fs /dev/pktcdvd/dev_name
```

在碟片上创建一个 ext2 文件系统
使用 pktcdvd 的 sysfs 接口
---------------------------------

自 Linux 2.6.20 起，pktcdvd 模块拥有一个 sysfs 接口，并可通过它进行控制。“pktcdvd”工具就使用了这个接口。（参见 http://tom.ist-im-web.de/linux/software/pktcdvd ）

“pktcdvd”与 “pktsetup”的工作方式类似，例如:

```shell
# pktcdvd -a dev_name /dev/hdc
# mkudffs /dev/pktcdvd/dev_name
# mount -t udf -o rw,noatime /dev/pktcdvd/dev_name /dvdram
# cp files /dvdram
# umount /dvdram
# pktcdvd -r dev_name
```

有关 sysfs 接口的描述，请参阅文件:

  Documentation/ABI/testing/sysfs-class-pktcdvd

使用 pktcdvd 的 debugfs 接口
-----------------------------------

要以人类可读的形式读取 pktcdvd 设备信息，请运行:

```shell
# cat /sys/kernel/debug/pktcdvd/pktcdvd[0-7]/info
```

有关 debugfs 接口的描述，请参阅文件:

  Documentation/ABI/testing/debugfs-pktcdvd

链接
-----

更多关于 DVD 写入的信息，请参阅 http://fy.chalmers.se/~appro/linux/DVD+RW/
