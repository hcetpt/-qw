=================
SPI NOR 框架
=================

如何提出新的闪存添加
-----------------------------------

大多数 SPI NOR 闪存符合 JEDEC JESD216 Serial Flash Discoverable Parameter (SFDP) 标准。SFDP 通过一组标准的内部只读参数表描述了串行闪存设备的功能和特性能力。
SPI NOR 驱动程序查询 SFDP 表以确定闪存的参数和设置。如果闪存定义了 SFDP 表，则很可能您根本不需要闪存条目，而是依赖于仅基于其 SFDP 数据探测闪存的通用闪存驱动程序。您只需在设备树中指定 "jedec,spi-nor" 的兼容性即可。
然而，在某些情况下，您需要定义一个明确的闪存条目。这通常发生在闪存具有 SFDP 表未涵盖的设置或支持时（例如，区块保护），或者当闪存包含错误的 SFDP 数据时。如果是后者，您需要实现 `spi_nor_fixups` 钩子来修正 SFDP 参数为正确的值。

最低测试要求
-----------------------------

执行以下所有测试，并将它们粘贴到提交的注释部分中，在 `---` 标记之后。
1) 指出您用于测试闪存的控制器以及闪存的操作频率，例如：

    此闪存位于 X 板上，并使用 Z（请填写兼容性）SPI 控制器以 Y 频率进行了测试。
2) 导出 sysfs 条目并打印 md5/sha1/sha256 SFDP 校验和：

    ```
    root@1:~# cat /sys/bus/spi/devices/spi0.0/spi-nor/partname
    sst26vf064b
    root@1:~# cat /sys/bus/spi/devices/spi0.0/spi-nor/jedec_id
    bf2643
    root@1:~# cat /sys/bus/spi/devices/spi0.0/spi-nor/manufacturer
    sst
    root@1:~# xxd -p /sys/bus/spi/devices/spi0.0/spi-nor/sfdp
    53464450060102ff00060110300000ff81000106000100ffbf0001180002
    0001fffffffffffffffffffffffffffffffffd20f1ffffffff0344eb086b
    083b80bbfeffffffffff00ffffff440b0c200dd80fd810d820914824806f
    1d81ed0f773830b030b0f7ffffff29c25cfff030c080ffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffff0004fff37f0000f57f0000f9ff
    7d00f57f0000f37f0000ffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    ffffbf2643ffb95ffdff30f260f332ff0a122346ff0f19320f1919ffffff
    ffffffff00669938ff05013506040232b03072428de89888a585c09faf5a
    ffff06ec060c0003080bffffffffff07ffff0202ff060300fdfd040700fc
    0300fefe0202070e
    root@1:~# sha256sum /sys/bus/spi/devices/spi0.0/spi-nor/sfdp
    428f34d0461876f189ac97f93e68a05fa6428c6650b3b7baf736a921e5898ed1  /sys/bus/spi/devices/spi0.0/spi-nor/sfdp
    ```

    请使用 `xxd -p` 导出 SFDP 表。这使我们能够进行逆向操作，并使用 `xxd -rp` 将十六进制转回二进制。虽然也可以接受使用 `hexdump -Cv` 导出 SFDP 数据，但不太推荐。
3) 导出 debugfs 数据：

    ```
    root@1:~# cat /sys/kernel/debug/spi-nor/spi0.0/capabilities
    闪存支持的读取模式
     1S-1S-1S
      opcode       0x03
      模式周期数   0
      假周期数     0
     1S-1S-1S (快速读取)
      opcode       0x0b
      模式周期数   0
      假周期数     8
     1S-1S-2S
      opcode       0x3b
      模式周期数   0
      假周期数     8
     1S-2S-2S
      opcode       0xbb
      模式周期数   4
      假周期数     0
     1S-1S-4S
      opcode       0x6b
      模式周期数   0
      假周期数     8
     1S-4S-4S
      opcode       0xeb
      模式周期数   2
      假周期数     4
     4S-4S-4S
      opcode       0x0b
      模式周期数   2
      假周期数     4

    闪存支持的页编程模式
     1S-1S-1S
      opcode       0x02

    root@1:~# cat /sys/kernel/debug/spi-nor/spi0.0/params
    名称         sst26vf064b
    ID           bf 26 43 bf 26 43
    大小         8.00 MiB
    写入大小     1
    页大小       256
    地址字节数   3
    标志         HAS_LOCK | HAS_16BIT_SR | SOFT_RESET | SWP_IS_VOLATILE

    操作码
     读取       0xeb
      假周期数   6
     擦除       0x20
     编程       0x02
     8D 扩展    无

    协议
     读取       1S-4S-4S
     写入       1S-1S-1S
     寄存器     1S-1S-1S

    擦除命令
     20 (4.00 KiB) [0]
     d8 (8.00 KiB) [1]
     d8 (32.0 KiB) [2]
     d8 (64.0 KiB) [3]
     c7 (8.00 MiB)

    区域映射
     区域 (十六进制) | 擦除掩码 | 标志
     ------------------+------------+----------
     00000000-00007fff |     [01  ] |
     00008000-0000ffff |     [0 2 ] |
     00010000-007effff |     [0  3] |
     007f0000-007f7fff |     [0 2 ] |
     007f8000-007fffff |     [01  ] |
    ```

4) 使用 `mtd-utils` 并验证擦除、读取和页编程操作是否正常工作：

    ```
    root@1:~# dd if=/dev/urandom of=./spi_test bs=1M count=2
    2+0 记录输入
    2+0 记录输出
    2097152 字节 (2.1 MB, 2.0 MiB) 已复制，0.848566 秒，2.5 MB/秒

    root@1:~# mtd_debug erase /dev/mtd0 0 2097152
    从地址 0x00000000 在闪存中擦除了 2097152 字节

    root@1:~# mtd_debug read /dev/mtd0 0 2097152 spi_read
    从地址 0x00000000 在闪存中复制了 2097152 字节到 spi_read

    root@1:~# hexdump spi_read
    0000000 ffff ffff ffff ffff ffff ffff ffff ffff
    *
    0200000

    root@1:~# sha256sum spi_read
    4bda3a28f4ffe603c0ec1258c0034d65a1a0d35ab7bd523a834608adabf03cc5  spi_read

    root@1:~# mtd_debug write /dev/mtd0 0 2097152 spi_test
    从 spi_test 复制了 2097152 字节到地址 0x00000000 在闪存中

    root@1:~# mtd_debug read /dev/mtd0 0 2097152 spi_read
    从地址 0x00000000 在闪存中复制了 2097152 字节到 spi_read

    root@1:~# sha256sum spi*
    c444216a6ba2a4a66cccd60a0dd062bce4b865dd52b200ef5e21838c4b899ac8  spi_read
    c444216a6ba2a4a66cccd60a0dd062bce4b865dd52b200ef5e21838c4b899ac8  spi_test
    ```

    如果闪存默认被擦除且之前的擦除被忽略，我们将无法检测到它，因此请再次测试擦除：

    ```
    root@1:~# mtd_debug erase /dev/mtd0 0 2097152
    从地址 0x00000000 在闪存中擦除了 2097152 字节

    root@1:~# mtd_debug read /dev/mtd0 0 2097152 spi_read
    从地址 0x00000000 在闪存中复制了 2097152 字节到 spi_read

    root@1:~# sha256sum spi*
    4bda3a28f4ffe603c0ec1258c0034d65a1a0d35ab7bd523a834608adabf03cc5  spi_read
    c444216a6ba2a4a66cccd60a0dd062bce4b865dd52b200ef5e21838c4b899ac8  spi_test
    ```

    导出一些其他相关数据：

    ```
    root@1:~# mtd_debug info /dev/mtd0
    mtd.type = MTD_NORFLASH
    mtd.flags = MTD_CAP_NORFLASH
    mtd.size = 8388608 (8M)
    mtd.erasesize = 4096 (4K)
    mtd.writesize = 1
    mtd.oobsize = 0
    regions = 0
    ```
