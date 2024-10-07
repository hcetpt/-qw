```plaintext
.. SPDX-License-Identifier: GPL-2.0

===============================================================
西部数据WD7193、WD7197和WD7296 SCSI卡的驱动程序
===============================================================

该卡需要固件，可以从西部数据提供的Windows NT驱动程序中提取，
该驱动程序可以从以下网址下载：
http://support.wdc.com/product/download.asp?groupid=801&sid=27&lang=en

文件或页面中没有任何许可信息，因此该固件可能无法添加到linux-firmware中。
此脚本会下载并提取固件，创建wd719x-risc.bin和d719x-wcs.bin文件。将它们放在/lib/firmware/目录下：

#!/bin/sh
wget http://support.wdc.com/download/archive/pciscsi.exe
lha xi pciscsi.exe pci-scsi.exe
lha xi pci-scsi.exe nt/wd7296a.sys
rm pci-scsi.exe
dd if=wd7296a.sys of=wd719x-risc.bin bs=1 skip=5760 count=14336
dd if=wd7296a.sys of=wd719x-wcs.bin bs=1 skip=20096 count=514
rm wd7296a.sys
```
