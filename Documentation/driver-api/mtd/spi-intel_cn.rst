使用spi-intel升级BIOS

许多Intel CPU（如Baytrail和Braswell）包含SPI串行闪存主机控制器，用于存储BIOS和其他平台特定数据。由于SPI串行闪存的内容对于机器正常运行至关重要，通常会通过不同的硬件保护机制来防止意外（或故意）覆盖内容。并非所有制造商都会保护SPI串行闪存，主要是因为它允许直接从操作系统中升级BIOS映像。spi-intel驱动程序可以在某些保护位未设置和锁定的情况下读取和写入SPI串行闪存。如果它检测到任何这些位被设置，则整个MTD设备将被设置为只读以防止部分覆盖。默认情况下，该驱动程序将SPI串行闪存的内容暴露为只读，但可以通过内核命令行传递"spi_intel.writeable=1"来更改。

请注意，在SPI串行闪存上覆盖BIOS映像可能会导致机器无法启动，并且需要专用设备（如Dediprog）来恢复。已经提醒过您！

以下是直接从Linux升级MinnowBoard MAX BIOS的步骤：
1) 下载并解压缩最新的Minnowboard MAX BIOS SPI映像[1]。撰写本文时，最新映像是v92。
2) 安装mtd-utils包[2]。我们需要它来擦除SPI串行闪存。像Debian和Fedora这样的发行版已经预先打包好了名为"mtd-utils"的软件包。
3) 在内核命令行中添加"spi_intel.writeable=1"并重新启动板子（您也可以在modprobe时作为模块参数传递"writeable=1"来重新加载驱动程序）。
4) 当板子再次启动并运行后，找到正确的MTD分区（它命名为"BIOS"）：

    # cat /proc/mtd
    dev:    size   erasesize  name
    mtd0: 00800000 00001000 "BIOS"

    因此这里将是/dev/mtd0，但它可能有所不同。
5) 首先备份现有映像：

    # dd if=/dev/mtd0ro of=bios.bak
    16384+0 records in
    16384+0 records out
    8388608 bytes (8.4 MB) copied, 10.0269 s, 837 kB/s

6) 验证备份：

    # sha1sum /dev/mtd0ro bios.bak
    fdbb011920572ca6c991377c4b418a0502668b73  /dev/mtd0ro
    fdbb011920572ca6c991377c4b418a0502668b73  bios.bak

    SHA1校验和必须匹配。否则请不要再继续！
7) 擦除SPI串行闪存。在此步骤之后，请不要重新启动板子！否则它将不再启动：

    # flash_erase /dev/mtd0 0 0
    Erasing 4 Kibyte @ 7ff000 -- 100 % complete

8) 如果没有错误完成擦除后，您可以写入新的BIOS映像：

    # dd if=MNW2MAX1.X64.0092.R01.1605221712.bin of=/dev/mtd0

9) 验证SPI串行闪存的新内容与新BIOS映像相匹配：

    # sha1sum /dev/mtd0ro MNW2MAX1.X64.0092.R01.1605221712.bin
    9b4df9e4be2057fceec3a5529ec3d950836c87a2  /dev/mtd0ro
    9b4df9e4be2057fceec3a5529ec3d950836c87a2 MNW2MAX1.X64.0092.R01.1605221712.bin

    SHA1校验和应该匹配。
10) 现在您可以重启您的开发板并观察新的BIOS是否正确启动。

参考文献
--------

[1] https://firmware.intel.com/sites/default/files/MinnowBoard%2EMAX_%2EX64%2E92%2ER01%2Ezip

[2] http://www.linux-mtd.infradead.org/
