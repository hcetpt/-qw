SPDX 许可证标识符: GPL-2.0

==================================
Macintosh HFS 文件系统 for Linux
==================================

.. 注意:: 此文件系统没有维护者
HFS 代表 “分层文件系统”，是 Mac Plus 及其后续所有 Macintosh 型号使用的文件系统。早期的 Macintosh 型号使用 MFS（“Macintosh 文件系统”），该系统不受支持。MacOS 8.1 及更新版本支持一种名为 HFS+ 的文件系统，它与 HFS 类似，但在多个方面有所扩展。要从 Linux 访问此类文件系统，请使用 hfsplus 文件系统驱动程序。

挂载选项
==========

在挂载 HFS 文件系统时，接受以下选项：

  creator=cccc, type=cccc  
  指定由 MacOS Finder 显示的创建者/类型值，用于创建新文件。默认值: '????'  

uid=n, gid=n  
  指定拥有文件系统上所有文件的用户/组  
  默认: 挂载进程的用户/组 ID  

dir_umask=n, file_umask=n, umask=n  
  指定用于所有文件、所有目录或所有文件和目录的 umask  
  默认为挂载进程的 umask  

session=n  
  选择作为 HFS 文件系统挂载的 CD-ROM 会话  
  默认情况下，将此决定留给 CD-ROM 驱动程序。如果底层设备不是 CD-ROM，此选项将失败  

part=n  
  从设备中选择分区编号 n  
  对于 CD-ROM 来说才有意义，因为它们在 Linux 下不能被分区  
  对于磁盘设备，通用分区解析代码为我们完成了这项工作  
  默认情况下不解析分区表  

quiet  
  忽略无效的挂载选项而不是抱怨
### 写入 HFS 文件系统
==========================

HFS 不是 UNIX 文件系统，因此它不具备您通常期望的功能：

* 您不能修改文件的 set-uid、set-gid、sticky 或可执行位，也不能修改文件的 uid 和 gid。
* 您不能创建硬链接或符号链接、设备文件、套接字或 FIFO。

另一方面，HFS 支持每个文件的多个分支。这些非标准分支在普通文件系统的命名空间中表示为隐藏的附加文件，这有点笨拙，并且使得语义变得有些奇怪：

* 您不能创建、删除或重命名文件的资源分支或 Finder 的元数据。
* 然而，它们会随着相应的数据分支或目录一起被创建（带有默认值）、删除和重命名。
* 将文件复制到不同的文件系统会导致丢失对 MacOS 运行至关重要的属性。

### 创建 HFS 文件系统
========================

Robert Leslie 的 hfsutils 包含一个名为 hformat 的程序，可以用来创建 HFS 文件系统。详情请参见 <https://www.mars.org/home/rob/proj/hfs/>。

### 致谢
=======

HFS 驱动程序由 Paul H. Hargrove（hargrove@sccm.Stanford.EDU）编写。
Roman Zippel（roman@ardistech.com）重写了大量代码，并引入了从 Brad Boyer 的 hfsplus 驱动程序衍生出的 B 树例程。
