SPDX 许可证标识符: GPL-2.0

======================================
Macintosh HFSPlus 文件系统 for Linux
======================================

HFSPlus 是一个首先在 MacOS 8.1 中引入的文件系统。
HFSPlus 对 HFS 进行了多项扩展，包括 32 位分配块、255 字符的 Unicode 文件名和 2^63 字节的文件大小。

挂载选项
========

当挂载 HFSPlus 文件系统时，接受以下选项：

  creator=cccc, type=cccc
   指定由 MacOS Finder 显示的创建者/类型值，用于创建新文件。默认值: '????'
uid=n, gid=n
   指定拥有文件系统上所有具有未初始化权限结构的文件的用户/组
默认: 挂载过程的用户/组 ID
umask=n
   指定用于具有未初始化权限结构的文件和目录的 umask（八进制表示）
默认: 挂载过程的 umask
session=n
   选择要作为 HFSPlus 文件系统挂载的 CD-ROM 会话。默认情况下，将此决定留给 CD-ROM 驱动程序。此选项仅适用于底层设备为 CD-ROM 的情况
part=n
   从设备中选择分区号 n。此选项仅对 CD-ROM 有意义，因为它们在 Linux 下不能被分区
对于磁盘设备，通用分区解析代码会为我们处理这一点。默认情况下不解析分区表
分解
分解文件名字符  
nodecompose  
不分解文件名字符  
force  
用于强制写入访问那些被标记为日志记录或锁定的卷。使用时需自担风险。  
nls=cccc  
在显示文件名时使用的编码  

参考
==========

内核源码： `<file:fs/hfsplus>`  

Apple 技术说明 1150 <https://developer.apple.com/legacy/library/technotes/tn/tn1150.html>
