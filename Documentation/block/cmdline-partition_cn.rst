==============================
嵌入式设备命令行分区解析
==============================

“blkdevparts”命令行选项添加了从内核命令行读取块设备分区表的支持。
它通常用于固定块（例如 eMMC）的嵌入式设备。
它没有主引导记录（MBR），因此节省了存储空间。可以通过块设备上的绝对地址轻松访问引导加载程序。
用户可以轻松更改分区。
该命令行的格式类似于 mtdparts：

blkdevparts=<blkdev-def>[;<blkdev-def>]
  <blkdev-def> := <blkdev-id>:<partdef>[,<partdef>]
    <partdef> := <size>[@<offset>](part-name)

<blkdev-id>
    块设备磁盘名称。嵌入式设备使用固定块设备
其磁盘名称也是固定的，例如：mmcblk0、mmcblk1、mmcblk0boot0
<size>
    分区大小，以字节为单位，例如：512、1m、1G
大小可以包含可选的后缀（大写或小写）：

      K、M、G、T、P、E
“-”用于表示剩余的所有空间
<offset>
    分区起始地址，以字节为单位
偏移量可能包含以下（大写或小写）可选后缀：

      K, M, G, T, P, E
(分区名称)
    分区名称。内核发送带有 "PARTNAME" 的 uevent。应用程序可以创建指向名为 "PARTNAME" 的块设备分区的链接。
用户空间的应用程序可以通过分区名称访问分区。
示例：

    eMMC 磁盘名称为 "mmcblk0" 和 "mmcblk0boot0"
启动参数 (`bootargs`) ：

    'blkdevparts=mmcblk0:1G(data0),1G(data1),-;mmcblk0boot0:1m(boot),-(kernel)'

  dmesg 输出 ：

    mmcblk0: p1(data0) p2(data1) p3()
    mmcblk0boot0: p1(boot) p2(kernel)
