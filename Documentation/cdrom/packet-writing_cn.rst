包写入
==============

快速入门
---------------------

- 在块设备部分选择包支持，并在文件系统部分选择UDF支持。
- 编译并安装内核和模块，然后重启。
- 您需要 udftools 包（pktsetup、mkudffs、cdrwtool）
从 https://github.com/pali/udftools 下载。

- 获取一张新的 CD-RW 碟片并进行格式化（假设 CD-RW 是 hdc，请根据实际情况替换）：

	```shell
	# cdrwtool -d /dev/hdc -q
	```

- 设置您的刻录机：

	```shell
	# pktsetup dev_name /dev/hdc
	```

- 现在您可以挂载 `/dev/pktcdvd/dev_name` 并向其中复制文件。尽情享受吧：

	```shell
	# mount /dev/pktcdvd/dev_name /cdrom -t udf -o rw,noatime
	```

用于 DVD-RW 媒体的包写入
-------------------------------

如果 DVD-RW 碟片处于所谓的“受限重写”模式，则可以像 CD-RW 碟片一样对其进行写入。要将碟片置于受限重写模式，请运行：

	```shell
	# dvd+rw-format /dev/hdc
	```

然后您可以像使用 CD-RW 碟片一样使用该碟片：

	```shell
	# pktsetup dev_name /dev/hdc
	# mount /dev/pktcdvd/dev_name /cdrom -t udf -o rw,noatime
	```

用于 DVD+RW 媒体的包写入
-------------------------------

根据 DVD+RW 规范，支持 DVD+RW 碟片的驱动器应当实现“真正的随机写入，粒度为 2KB”，这意味着可以在这种碟片上放置任何块大小 >= 2KB 的文件系统。例如，可以执行以下操作：

	```shell
	# dvd+rw-format /dev/hdc   (仅当碟片从未被格式化时才需要)
	# mkudffs /dev/hdc
	# mount /dev/hdc /cdrom -t udf -o rw,noatime
	```

然而，有些驱动器并不遵循规范，期望主机以 32KB 边界对齐的方式进行写入。其他驱动器确实遵循规范，但如果写入未对齐到 32KB 则会遇到严重的性能问题。这两个问题都可以通过使用 pktcdvd 驱动器来解决，该驱动器始终生成对齐的写入：

	```shell
	# dvd+rw-format /dev/hdc
	# pktsetup dev_name /dev/hdc
	# mkudffs /dev/pktcdvd/dev_name
	# mount /dev/pktcdvd/dev_name /cdrom -t udf -o rw,noatime
	```

用于 DVD-RAM 媒体的包写入
--------------------------------

DVD-RAM 碟片是可随机写入的，因此使用 pktcdvd 驱动器并非必要。然而，使用 pktcdvd 驱动器可以像对 DVD+RW 媒体那样提高性能。

注意事项
--------------

- CD-RW 媒体通常不能被重写超过大约 1000 次，为了避免不必要的磨损，您应该始终使用 `noatime` 挂载选项。
- 缺陷管理（即自动重映射坏扇区）尚未实现，因此如果碟片磨损，您可能会遇到至少一些文件系统的损坏。
- 由于 pktcdvd 驱动器使碟片看起来像是具有 2KB 块大小的常规块设备，因此您可以在碟片上放置任何您喜欢的文件系统。例如，运行：

	```shell
	# /sbin/mke2fs /dev/pktcdvd/dev_name
	```

使用 pktcdvd 的 sysfs 接口
---------------------------------

自 Linux 2.6.20 起，pktcdvd 模块有一个 sysfs 接口，并可以通过它进行控制。“pktcdvd”工具就使用了这个接口。（参见 http://tom.ist-im-web.de/linux/software/pktcdvd ）

“pktcdvd”类似于 “pktsetup”，例如：

	```shell
	# pktcdvd -a dev_name /dev/hdc
	# mkudffs /dev/pktcdvd/dev_name
	# mount -t udf -o rw,noatime /dev/pktcdvd/dev_name /dvdram
	# cp files /dvdram
	# umount /dvdram
	# pktcdvd -r dev_name
	```

关于 sysfs 接口的描述请参阅文件：

  Documentation/ABI/testing/sysfs-class-pktcdvd

使用 pktcdvd 的 debugfs 接口
-----------------------------------

要以人类可读的形式读取 pktcdvd 设备信息，请执行：

	```shell
	# cat /sys/kernel/debug/pktcdvd/pktcdvd[0-7]/info
	```

关于 debugfs 接口的描述请参阅文件：

  Documentation/ABI/testing/debugfs-pktcdvd

链接
-----

更多信息，请参阅 http://fy.chalmers.se/~appro/linux/DVD+RW/ 关于 DVD 写入的信息。
