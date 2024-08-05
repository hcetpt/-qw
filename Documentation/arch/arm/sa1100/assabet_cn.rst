英特尔 Assabet (SA-1110 评估) 板卡
============================================

请参阅：
http://developer.intel.com

同时，来自 John G Dorsey <jd5q@andrew.cmu.edu> 的一些注释：
http://www.cs.cmu.edu/~wearable/software/assabet.html

构建内核
-------------------

要使用当前默认设置构建内核，请执行以下操作：

```
make assabet_defconfig
make oldconfig
make zImage
```

构建完成的内核映像应位于 linux/arch/arm/boot/zImage
安装引导加载程序
-----------------------

有几个能够引导 Assabet 上的 Linux 的引导加载程序可供选择：

BLOB（http://www.lartmaker.nl/lartware/blob/）

   BLOB 是 LART 项目中使用的引导加载程序。已经有一些贡献的补丁被合并到 BLOB 中以添加对 Assabet 的支持。
康柏公司的 Bootldr + John Dorsey 为 Assabet 支持提供的补丁
（http://www.handhelds.org/Compaq/bootldr.html）
（http://www.wearablegroup.org/software/bootldr/）

   Bootldr 是康柏公司为 iPAQ Pocket PC 开发的引导加载程序。
John Dorsey 制作了附加补丁来为 Assabet 和 JFFS 文件系统提供支持。
RedBoot（http://sources.redhat.com/redboot/）

   RedBoot 是红帽基于 eCos 实时操作系统硬件抽象层开发的引导加载程序。它支持多种硬件平台，包括 Assabet。
目前推荐使用 RedBoot，因为它是在这些选项中唯一支持网络功能且维护最活跃的。
下面简要展示了如何使用 RedBoot 引导 Linux 的示例。但首先你需要在闪存中安装 RedBoot。一个已知可用的预编译 RedBoot 二进制文件可以从以下位置获取：

- ftp://ftp.netwinder.org/users/n/nico/
- ftp://ftp.arm.linux.org.uk/pub/linux/arm/people/nico/
- ftp://ftp.handhelds.org/pub/linux/arm/sa-1100-patches/

寻找 redboot-assabet*.tgz 文件。关于安装的信息可以在 redboot-assabet*.txt 中找到。
初始 RedBoot 配置
-----------------------------

这里使用的命令在《RedBoot 用户指南》中有解释，该指南可在线获取：http://sources.redhat.com/ecos/docs.html
请参考该指南获取详细说明。
如果你有一张 CF 网络卡（我的 Assabet 套件中包含了一张 Socket Communications Inc. 的 CF+ LP-E 卡），你应当考虑使用它进行 TFTP 文件传输。由于 RedBoot 无法动态检测它，所以你必须在 RedBoot 启动之前插入该卡。
初始化闪存目录:

	fis init -f

要初始化非易失性设置（例如，您是否想要使用BOOTP或
静态IP地址等），请使用以下命令:

	fconfig -i

将内核镜像写入闪存
------------------------

首先，必须将内核镜像加载到RAM中。如果您在TFTP服务器上有可用的zImage文件:

	load zImage -r -b 0x100000

如果您更倾向于通过串口使用Y-Modem上传:

	load -m ymodem -r -b 0x100000

要将其写入闪存:

	fis create "Linux kernel" -b 0x100000 -l 0xc0000

启动内核
------------

内核仍然需要一个文件系统来启动。可以按照如下方式加载ramdisk镜像:

	load ramdisk_image.gz -r -b 0x800000

同样地，可以用Y-Modem上传代替TFTP，只需将文件名替换为'-y ymodem'。
现在可以从闪存中获取内核:

	fis load "Linux kernel"

或者按先前所述的方式加载。要启动内核:

	exec -b 0x100000 -l 0xc0000

也可以将ramdisk镜像存储到闪存中，但下面提到的闪存上的文件系统有更好的解决方案。

使用JFFS2
------------

使用JFFS2（第二种日志式闪存文件系统）可能是将可写的文件系统存储到闪存中的最便捷的方式。JFFS2与MTD层一起使用，该层负责低级别的闪存管理。关于Linux MTD的更多信息可以在网上找到：  
http://www.linux-mtd.infradead.org/。该网站还提供了一个包含创建JFFS/JFFS2镜像信息的JFFS教程。
例如，可以从下面提到的预编译RedBoot镜像相同的FTP站点获取示例JFFS2镜像。
要加载此文件:

	load sample_img.jffs2 -r -b 0x100000

结果应该类似于:

	RedBoot> load sample_img.jffs2 -r -b 0x100000
	原始文件已加载 0x00100000-0x00377424

现在我们必须知道未分配的闪存大小:

	fis free

结果:

	RedBoot> fis free
	  0x500E0000 .. 0x503C0000

根据文件系统的大小和闪存类型的不同，上述值可能会有所不同。下面是一个使用示例，请适当替换您的值。
我们需要确定一些值:

未分配的闪存大小:	0x503c0000 - 0x500e0000 = 0x2e0000
文件系统镜像的大小:	0x00377424 - 0x00100000 = 0x277424

我们当然想要使文件系统镜像适应，但同时也要给它剩余的所有闪存空间。要写入它:

	fis unlock -f 0x500E0000 -l 0x2e0000
	fis erase -f 0x500E0000 -l 0x2e0000
	fis write -b 0x100000 -l 0x277424 -f 0x500E0000
	fis create "JFFS2" -n -f 0x500E0000 -l 0x2e0000

现在文件系统与Linux发现它们时的MTD“分区”相关联。从Redboot，'fis list' 命令显示它们:

	RedBoot> fis list
	Name              FLASH addr  Mem addr    Length      Entry point
	RedBoot           0x50000000  0x50000000  0x00020000  0x00000000
	RedBoot config    0x503C0000  0x503C0000  0x00020000  0x00000000
	FIS directory     0x503E0000  0x503E0000  0x00020000  0x00000000
	Linux kernel      0x50020000  0x00100000  0x000C0000  0x00000000
	JFFS2             0x500E0000  0x500E0000  0x002E0000  0x00000000

然而Linux应显示的内容类似:

	SA1100 flash: 探测32位闪存总线
	SA1100 flash: 在32位模式下找到2个x16设备在0x0处
	使用RedBoot分区定义
	在"SA1100 flash"上创建5个MTD分区:
	0x00000000-0x00020000 : "RedBoot"
	0x00020000-0x000e0000 : "Linux kernel"
	0x000e0000-0x003c0000 : "JFFS2"
	0x003c0000-0x003e0000 : "RedBoot config"
	0x003e0000-0x00400000 : "FIS directory"

这里重要的是我们感兴趣的分区的位置，即第三个分区。在Linux内部，这对应于/dev/mtdblock2
因此要使用存储在闪存中的内核及其根文件系统启动Linux，我们需要这个RedBoot命令:

	fis load "Linux kernel"
	exec -b 0x100000 -l 0xc0000 -c "root=/dev/mtdblock2"

当然，还可以使用其他文件系统，例如cramfs。您可能想要使用NFS上的根文件系统启动等等。这也可能更方便，在从ramdisk或NFS引导的情况下直接从Linux内核中刷新文件系统。Linux MTD代码库中有许多处理闪存内存的工具，例如擦除闪存。然后可以直接在新擦除的分区上挂载JFFS2，并直接复制文件。等等。

RedBoot脚本
--------------

如果每次Assabet重启时都必须键入上述所有命令，那么这些命令就没那么有用。因此，可以使用RedBoot的脚本功能自动化引导过程。
例如，我使用以下方式从网络上的TFTP服务器获取内核和ramdisk镜像来启动Linux:

	RedBoot> fconfig
	启动时运行脚本: false true
	启动脚本:
	输入脚本，以空行终止
	>> load zImage -r -b 0x100000
	>> load ramdisk_ks.gz -r -b 0x800000
	>> exec -b 0x100000 -l 0xc0000
	>>
	启动脚本超时（1000ms分辨率）: 3
	使用BOOTP进行网络配置: true
	GDB连接端口: 9000
	启动时网络调试: false
	更新RedBoot非易失性配置 - 确定吗（y/n）? y

然后，重新启动Assabet只需要等待登录提示即可。
尼古拉斯·皮特雷
nico@fluxnic.net

2001年6月12日


-rmk 树中的外设状态（更新于2001年10月14日）
-------------------------------------------------------

阿萨贝特:
串行端口：
  无线电：		TX、RX、CTS、DSR、DCD、RI
   - 电源管理：	未测试
- COM：		TX、RX、CTS、DSR、DCD、RTS、DTR、电源管理
   - 电源管理：	未测试
- I2C：		已实现，但未完全测试
- L3：		完全测试，通过
- 电源管理：	未测试
视频：
  - LCD：		完全测试。 电源管理

   （当连接 neponset 时，LCD 不喜欢被屏蔽）

  - 视频输出：		未完全

音频：
  UDA1341：
  -  播放：		完全测试，通过
-  录音：		已实现，但未测试
-  电源管理：	未测试
UCB1200：
  -  音频播放：	已实现，但未大量测试
-  音频录音：	已实现，但未大量测试
- 电信音频播放：已实施，但未经过重度测试
- 电信音频录音：已实施，但未经过重度测试
- POTS 控制：否
  - 触摸屏：是
  - PM：未测试
其他：
  - PCMCIA：
  - LPE：全面测试，通过
- USB：否
  - IRDA：
  - SIR：全面测试，通过
- FIR：全面测试，通过
- PM：未测试
Neponset：
串行端口：
  - COM1,2：TX、RX、CTS、DSR、DCD、RTS、DTR
  - PM：未测试
- USB：已实施，但未经过重度测试
- PCMCIA：已实施，但未经过重度测试
- CF:			已实施，但未经过大量测试
- PM:			未经过测试
更多内容可以在 -np （尼古拉斯·皮特的）代码库中找到
