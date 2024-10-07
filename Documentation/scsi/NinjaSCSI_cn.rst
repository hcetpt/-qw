```spdx
许可标识符：GPL-2.0

=========================================
适用于 Linux 的 WorkBiT NinjaSCSI-3/32Bi 驱动程序
=========================================

1. 注释
==========

这是 Workbit 公司（http://www.workbit.co.jp/）为 Linux 开发的 NinjaSCSI-3 驱动程序。

2. 我的 Linux 环境
=======================

:Linux 内核: 2.4.7 / 2.2.19
:pcmcia-cs:    3.1.27
:gcc:          gcc-2.95.4
:PC 卡:      I-O data PCSC-F (NinjaSCSI-3)，I-O data CBSC-II 在 16 位模式下 (NinjaSCSI-32Bi)
:SCSI 设备:  I-O data CDPS-PX24 (CD-ROM 驱动器)，Media Intelligent MMO-640GT (光盘驱动器)

3. 安装
==========

(a) 检查你的 PC 卡是否确实是“NinjaSCSI-3”卡。
如果你已经安装了 pcmcia-cs，pcmcia-cs 会将你的卡报告为未知卡，并在控制台或日志文件中写入 ["WBT", "NinjaSCSI-3", "R1.0"] 或其他字符串。
你也可以使用 "cardctl" 程序（该程序包含在 pcmcia-cs 源代码中）来获取更多信息：
::

	# cat /var/log/messages
	..
Jan  2 03:45:06 lindberg cardmgr[78]: 在插槽 1 中发现不支持的卡
	Jan  2 03:45:06 lindberg cardmgr[78]:   产品信息: "WBT", "NinjaSCSI-3", "R1.0"
	..
# cardctl ident
	Socket 0:
	  无可用的产品信息
	Socket 1:
	  产品信息: "IO DATA", "CBSC16       ", "1"

(b) 获取 Linux 内核源代码，并将其解压到 /usr/src 目录下。
由于 NinjaSCSI 驱动程序需要 Linux 内核源代码中的某些 SCSI 头文件，因此我建议重新编译内核；这可以消除一些版本问题。
::

	$ cd /usr/src
	$ tar -zxvf linux-x.x.x.tar.gz
	$ cd linux
	$ make config
	..

(c) 如果你在 Kernel 2.2 下使用此驱动程序，请在一个目录中解压缩 pcmcia-cs 并进行编译和安装。此驱动程序需要 pcmcia-cs 的头文件。
```
```
$ cd /usr/src
$ tar zxvf cs-pcmcia-cs-3.x.x.tar.gz
..
(d) 将此驱动程序的存档解压到某个位置，然后编辑 Makefile，接着执行 make：

$ tar -zxvf nsp_cs-x.x.tar.gz
$ cd nsp_cs-x.x
$ emacs Makefile
..
$ make

(e) 将 nsp_cs.ko 复制到合适的位置，例如 /lib/modules/<内核版本>/pcmcia/
(f) 在 /etc/pcmcia/config 中添加以下行
如果您使用的是 pcmcia-cs-3.1.8 或更高版本，可以使用 "nsp_cs.conf" 文件
因此，您无需编辑文件。只需将其复制到 /etc/pcmcia/ 目录下：

device "nsp_cs"
  class "scsi" module "nsp_cs"

card "WorkBit NinjaSCSI-3"
  version "WBT", "NinjaSCSI-3", "R1.0"
  bind "nsp_cs"

card "WorkBit NinjaSCSI-32Bi (16bit)"
  version "WORKBIT", "UltraNinja-16", "1"
  bind "nsp_cs"

# OEM
card "WorkBit NinjaSCSI-32Bi (16bit) / IO-DATA"
  version "IO DATA", "CBSC16       ", "1"
  bind "nsp_cs"

# OEM
card "WorkBit NinjaSCSI-32Bi (16bit) / KME-1"
  version "KME    ", "SCSI-CARD-001", "1"
  bind "nsp_cs"
card "WorkBit NinjaSCSI-32Bi (16bit) / KME-2"
  version "KME    ", "SCSI-CARD-002", "1"
  bind "nsp_cs"
card "WorkBit NinjaSCSI-32Bi (16bit) / KME-3"
  version "KME    ", "SCSI-CARD-003", "1"
  bind "nsp_cs"
card "WorkBit NinjaSCSI-32Bi (16bit) / KME-4"
  version "KME    ", "SCSI-CARD-004", "1"
  bind "nsp_cs"

(f) 启动（或重新启动）pcmcia-cs：

# /etc/rc.d/rc.pcmcia start        (BSD 风格)

或者：

# /etc/init.d/pcmcia start         (SYSV 风格)

4. 历史
======

请参阅 README.nin_cs
5. 注意事项
==========

如果在对您的 SCSI 设备进行操作或暂停计算机时弹出卡片，您可能会遇到一些严重的错误，如磁盘崩溃。
当正确使用此驱动程序时，它可以正常工作。但我不能保证您的数据安全。使用此驱动程序时，请备份您的数据。
6. 已知问题
=============

在 2.4 内核中，无法使用 640MB 的光盘。此错误来自高级 SCSI 驱动程序
```
### 7. 测试
请给我发送一些关于此软件的报告（如 bug 报告等）。
当你发送报告时，请告诉我以下信息或更多：
- 显卡名称
- 内核版本
- 您的 SCSI 设备名称（硬盘、光驱等）

### 8. 版权
参见 GPL
2001年8月8日 yokota@netlab.is.tsukuba.ac.jp <YOKOTA Hiroshi>
