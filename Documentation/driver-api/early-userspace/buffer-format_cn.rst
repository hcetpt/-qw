=======================
初始化内存文件系统缓冲区格式
=======================

Al Viro, H. Peter Anvin

最后修订：2002-01-13

从内核2.5.x开始，旧的“初始RAM磁盘”协议正在被新的“初始RAM文件系统”（initramfs）协议所取代或补充。initramfs的内容使用与initrd协议相同的内存缓冲区协议传递，但内容不同。initramfs缓冲区包含一个归档文件，该文件将扩展为RAM文件系统；本文档详细描述了initramfs缓冲区格式。
initramfs缓冲区格式基于“newc”或“crc”CPIO格式，并可以使用cpio(1)工具创建。CPIO归档文件可以使用gzip(1)进行压缩。因此，一个有效的initramfs缓冲区版本是一个单一的.cpio.gz文件。
initramfs缓冲区的完整格式由以下语法定义，其中：

* 表示“0个或多个实例”
(|) 表示可选内容
+ 表示连接
GZIP() 表示对操作数使用gzip(1)压缩
ALGN(n) 表示用空字节填充至n字节边界

initramfs := ("\0" | cpio_archive | cpio_gzip_archive)*

cpio_gzip_archive := GZIP(cpio_archive)

cpio_archive := cpio_file* + (<nothing> | cpio_trailer)

cpio_file := ALGN(4) + cpio_header + filename + "\0" + ALGN(4) + data

cpio_trailer := ALGN(4) + cpio_header + "TRAILER!!!\0" + ALGN(4)

用人类语言来说，initramfs缓冲区包含了一系列压缩和/或未压缩的CPIO归档文件（采用“newc”或“crc”格式）。成员之间可以任意添加零字节（用于填充）。
CPIO中的“TRAILER!!!”条目（CPIO归档结束标记）是可选的，但不会被忽略；请参阅下面的“硬链接处理”。

CPIO头结构如下（所有字段都包含完全左填充的十六进制ASCII数字，例如整数4780表示为ASCII字符串"000012ac")：

============= ================== ==============================================
Field name    Field size        Meaning
============= ================== ==============================================
c_magic       6 bytes           字符串"070701"或"070702"
c_ino         8 bytes           文件inode编号
c_mode        8 bytes           文件模式和权限
c_uid         8 bytes           文件uid
c_gid         8 bytes           文件gid
c_nlink       8 bytes           链接数量
c_mtime       8 bytes           修改时间
c_filesize    8 bytes           数据字段大小
c_maj         8 bytes           文件设备号的主要部分
c_min         8 bytes           文件设备号的次要部分
c_rmaj        8 bytes           设备节点引用的主要部分
c_rmin        8 bytes           设备节点引用的次要部分
c_namesize    8 bytes           文件名长度，包括最终的\0
c_chksum      8 bytes           如果c_magic为070702，则为数据字段的校验和；否则为零
============= ================== ==============================================

c_mode字段与Linux上stat(2)返回的st_mode内容相匹配，并编码文件类型和文件权限。
对于不是常规文件或符号链接的任何文件，c_filesize应为零。
c_chksum字段包含数据字段中所有字节的简单32位无符号总和。cpio(1)将其称为“crc”，这显然是不正确的（循环冗余校验是一种不同的且显著更强大的完整性检查），但是这是使用的算法。
如果文件名为"TRAILER!!!"，这实际上是归档结束标记；归档结束标记的c_filesize必须为零。

硬链接处理
======================

当看到非目录文件且c_nlink > 1时，会查找元组缓冲区中的(c_maj, c_min, c_ino)三元组。如果没有找到，它会被加入到元组缓冲区，并像通常一样创建条目；如果找到了，则创建硬链接而不是文件的第二个副本。不需要（但允许）包含文件内容的第二个副本；如果未包含文件内容，则c_filesize字段应设置为零以指示后面没有数据部分。如果存在数据，则会覆盖文件的前一个实例；这允许携带数据的文件实例出现在序列中的任何位置（据报道，GNU cpio仅将数据附加到最后一个文件实例。）

对于符号链接，c_filesize不能为零。
当看到“TRAILER!!!”归档结束标记时，会重置元组缓冲区。这允许独立生成的归档文件被串联起来。
为了合并来自不同来源的文件数据（而不必重新生成 (c_maj, c_min, c_ino) 字段），因此，可以使用以下任一方法：

a) 使用 "TRAILER!!!" 归档结束标记来分隔不同的文件数据源，或者

b) 确保所有非目录项的 c_nlink 值都等于 1
