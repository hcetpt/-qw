====  
VFAT  
====  

## 使用 VFAT 文件系统

要使用 VFAT 文件系统，请使用文件系统类型 'vfat'。例如：

```
mount -t vfat /dev/fd0 /mnt
```

不需要特殊的分区格式化工具，如果你想在 Linux 内部进行格式化，`mkdosfs` 就可以很好地工作。

## VFAT 挂载选项

**uid=###**
设置此文件系统上所有文件的所有者。
默认值是当前进程的 UID。

**gid=###**
设置此文件系统上所有文件的所属组。
默认值是当前进程的 GID。

**umask=###**
权限掩码（用于文件和目录，参见 *umask(1)*）。
默认值是当前进程的 umask。

**dmask=###**
目录的权限掩码。
默认值是当前进程的 umask。

**fmask=###**
文件的权限掩码。
默认值是当前进程的 umask。

**allow_utime=###**
此选项控制mtime/atime的权限检查。
**-20**：如果当前进程属于文件组ID所在的组，
          则可以更改时间戳。
**-2**：其他用户可以更改时间戳。
默认值从dmask选项设置。如果目录可写，则也允许utime(2)操作，即 `~dmask & 022`。
通常，utime(2)会检查当前进程是否为文件的所有者，或者它具有CAP_FOWNER能力。但FAT文件系统在磁盘上没有uid/gid，因此常规检查过于僵化。通过此选项可以放宽这种限制。

**codepage=###**
设置用于将短文件名字符转换到FAT文件系统的代码页编号。
默认使用FAT_DEFAULT_CODEPAGE设置。

**iocharset=<name>**
用于在用户可见的文件名编码和16位Unicode字符之间进行转换的字符集。长文件名以Unicode格式存储在磁盘上，但Unix在很大程度上不知道如何处理Unicode。
默认使用FAT_DEFAULT_IOCHARSET设置。
**使用 UTF-8 翻译的选项**
   使用 `utf8` 选项

.. note:: 不推荐使用 ``iocharset=utf8``。如果不确定，应考虑使用 `utf8` 选项。

**utf8=<bool>**
   UTF-8 是文件系统安全版本的 Unicode，用于控制台。此选项可以启用或禁用文件系统的 UTF-8 支持。
   如果设置 `uni_xlate`，则禁用 UTF-8。
   默认情况下，使用 FAT_DEFAULT_UTF8 设置。

**uni_xlate=<bool>**
   将未处理的 Unicode 字符转换为特殊的转义序列。这允许你备份和恢复由任何 Unicode 字符创建的文件名。在 Linux 真正支持 Unicode 之前，这是一个替代方案。如果没有这个选项，在无法进行转换时会使用 '?'。转义字符是 ':'，因为它在 VFAT 文件系统中通常是非法的。使用的转义序列是 ':' 后跟四个十六进制的 Unicode 数字。

**nonumtail=<bool>**
   创建 8.3 别名时，默认情况下别名会以 '~1' 或波浪号后跟某个数字结尾。如果设置了此选项，并且目录中不存在 "longfile.txt"，那么 "longfilename.txt" 的短别名将是 "longfile.txt" 而不是 "longfi~1.txt"。

**usefree**
   使用存储在 FSINFO 中的“空闲簇”值。它将用于确定空闲簇的数量而无需扫描磁盘。但由于最近的 Windows 在某些情况下不会正确更新该值，因此默认情况下不使用它。如果你确定 FSINFO 中的“空闲簇”值是正确的，则可以通过此选项避免扫描磁盘。

**quiet**
   停止打印某些警告信息。

**check=s|r|n**
   大小写敏感性检查设置
**s**: 严格，区分大小写  
**r**: 宽松，不区分大小写  
**n**: 正常，默认设置，目前不区分大小写  

**nocase**  
此选项在 vfat 中已被弃用。请使用 `shortname=win95` 替代。  

**shortname=lower|win95|winnt|mixed**  
短名显示/创建设置  
**lower**: 转换为小写以进行显示，创建时模拟 Windows 95 规则  
**win95**: 模拟 Windows 95 规则进行显示/创建  
**winnt**: 模拟 Windows NT 规则进行显示/创建  
**mixed**: 显示时模拟 Windows NT 规则，创建时模拟 Windows 95 规则  
默认设置为 `mixed`  

**tz=UTC**  
将时间戳解释为 UTC 而不是本地时间  
此选项禁用了时间戳在本地时间（FAT 文件系统中使用的）与 UTC（Linux 内部使用的）之间的转换。这对于挂载设置为 UTC 的设备（如数码相机）特别有用，以避免本地时间的陷阱。  

**time_offset=minutes**  
设置从本地时间到 UTC 的时间戳转换偏移量。即从每个时间戳中减去 `<minutes>` 分钟，将其转换为 Linux 内部使用的 UTC 时间。当 `sys_tz` 设置的时间区与文件系统使用的时间区不一致时，此选项非常有用。请注意，即使在这种情况下，此选项仍不能在所有情况下提供正确的时间戳，特别是在夏令时存在的情况下，不同夏令时设置的时间戳会相差一小时。
**showexec**
如果设置，文件的执行权限位仅在文件扩展名为 .EXE、.COM 或 .BAT 时才被允许。默认情况下未设置。

**debug**
可以设置，但当前实现中未使用。

**sys_immutable**
如果设置，FAT 文件系统中的 ATTR_SYS 属性将被视为 Linux 中的 IMMUTABLE 标志处理。默认情况下未设置。

**flush**
如果设置，文件系统将在比正常情况更早的时候尝试将数据刷新到磁盘。默认情况下未设置。

**rodir**
FAT 文件系统具有 ATTR_RO（只读）属性。在 Windows 系统中，目录的 ATTR_RO 属性会被忽略，仅作为应用程序标志使用（例如，自定义文件夹会设置此属性）。
如果您希望即使对于目录也使用 ATTR_RO 作为只读标志，请设置此选项。

**errors=panic|continue|remount-ro**
指定 FAT 文件系统在遇到严重错误时的行为：引发恐慌、继续运行不做任何操作或以只读模式重新挂载分区（默认行为）。

**discard**
如果设置，当块被释放时向块设备发送丢弃/TRIM 命令。这对于 SSD 设备和稀疏/薄配置的逻辑单元号（LUN）非常有用。

**nfs=stale_rw|nostale_ro**
仅在您希望通过 NFS 导出 FAT 文件系统时启用。
- **stale_rw**：此选项通过 *i_logstart* 维护一个目录 *inode* 的索引（缓存），用于 NFS 相关代码来提高查找速度。支持完整的文件操作（读/写），但在 NFS 服务器上进行缓存驱逐时，可能会导致 ESTALE 问题。
**nostale_ro**：此选项基于文件在 MS-DOS 目录项中的磁盘位置来确定 *inode* 编号和文件句柄。
这确保了文件从 inode 缓存中被驱逐后不会返回 ESTALE。然而，这也意味着诸如重命名、创建和删除等操作可能导致先前指向一个文件的文件句柄指向另一个不同的文件，从而可能引起数据损坏。因此，出于这个原因，此选项也会以只读方式挂载文件系统。
为了保持向后兼容性，``'-o nfs'`` 也被接受，默认为 "stale_rw"。

**dos1xfloppy** **<bool>: 0,1,yes,no,true,false**
如果设置，则使用根据支持设备大小确定的回退默认 BIOS 参数块配置。这些静态参数与 DOS 1.x 对于 160 KiB、180 KiB、320 KiB 和 360 KiB 软盘及软盘映像所假设的默认值相匹配。

### 限制
使用 `fallocate` 且带有 `FALLOC_FL_KEEP_SIZE` 标志时，在卸载或驱逐时会丢弃已分配的文件区域。
因此，用户应假设在内存压力导致 inode 从内存中被驱逐时，`fallocate` 区域可能会在最后关闭时被丢弃。因此，对于任何依赖 `fallocate` 区域的情况，用户应在重新打开文件后重新检查 `fallocate`。

### 待办事项
需要摆脱原始扫描功能。相反，始终使用获取下一个目录项的方法。唯一还使用原始扫描的是目录重命名代码。

### 可能的问题
- `vfat_valid_longname` 没有正确检查保留名称。
- 当卷名与文件系统根目录中的目录名相同，有时该目录名会显示为空文件。
- `autoconv` 选项无法正常工作。
测试套件
==========
如果您计划对 vfat 文件系统进行任何修改，请获取随 vfat 发行版提供的测试套件，地址如下：

`<http://web.archive.org/web/*/http://bmrc.berkeley.edu/people/chaffee/vfat.html>`_

此套件测试了 vfat 文件系统的许多部分，并欢迎针对新功能或未测试功能添加更多测试。

关于 vfat 文件系统结构的说明
=============================================
本文档由 Galen C. Hunt (gchunt@cs.rochester.edu) 提供，并由 Gordon Chaffee 轻微注释。
本文档提供了我对用于 Windows NT 3.5 和 Windows 95 的扩展 FAT 文件系统的粗略技术概述。我不保证以下内容完全正确，但看起来是这样。

扩展的 FAT 文件系统几乎与 DOS 版本（包括 *6.223410239847*）中使用的 FAT 文件系统相同。主要的变化是增加了长文件名。

这些名称支持最多 255 个字符，包括空格和小写字母，而传统的 8.3 短名称只支持 8.3 字符。
以下是当前 Windows 95 文件系统中传统 FAT 目录条目的描述：

```c
struct directory { // 短 8.3 名称
        unsigned char name[8];          // 文件名
        unsigned char ext[3];           // 文件扩展名
        unsigned char attr;             // 属性字节
        unsigned char lcase;            // 基名和扩展名的小写形式
        unsigned char ctime_ms;         // 创建时间，毫秒
        unsigned char ctime[2];         // 创建时间
        unsigned char cdate[2];         // 创建日期
        unsigned char adate[2];         // 最后访问日期
        unsigned char reserved[2];      // 预留值（忽略）
        unsigned char time[2];          // 时间戳
        unsigned char date[2];          // 日期戳
        unsigned char start[2];         // 起始簇号
        unsigned char size[4];          // 文件大小
};
```

`lcase` 字段指定了 8.3 名称的基名和/或扩展名是否应大写。这个字段似乎不被 Windows 95 使用，但被 Windows NT 使用。从 Windows NT 到 Windows 95 的文件名大小写兼容性并不完全一致。反过来也是如此。符合 8.3 命名空间且在 Windows NT 上写入为小写的文件名在 Windows 95 上会显示为大写。
.. note:: 注意 `start` 和 `size` 值实际上是小端整数。此结构中的字段描述是公开的知识，可以在其他地方找到。
在扩展的 FAT 系统中，Microsoft 为具有扩展名称的任何文件插入了额外的目录条目。（任何合法地适合旧的 8.3 编码方案的名称没有额外的条目。）我将这些额外的条目称为槽。基本上，一个槽是一个特别格式化的目录条目，可以容纳最多 13 个字符的文件扩展名称。可以把槽看作是对相应文件目录条目的额外标签。Microsoft 更喜欢将文件的 8.3 条目称为别名，将扩展槽目录条目称为文件名。
槽目录条目的 C 结构如下：

```c
struct slot { // 最多 13 个字符的长名称
        unsigned char id;               // 槽的序列号
        unsigned char name0_4[10];      // 名称中的前 5 个字符
        unsigned char attr;             // 属性字节
        unsigned char reserved;         // 总是 0
        unsigned char alias_checksum;   // 8.3 别名的校验和
        unsigned char name5_10[12];     // 名称中的另外 6 个字符
        unsigned char start[2];         // 起始簇号
        unsigned char name11_12[4];     // 名称中的最后 2 个字符
};
```

如果槽的布局看起来有些奇怪，那只是因为 Microsoft 努力保持与旧软件的兼容性。为了达到这一目的，采取了一些措施：

1) 槽目录条目的属性字节始终设置为 0x0f。这对应于具有“隐藏”、“系统”、“只读”和“卷标”属性的旧目录条目。大多数旧软件会忽略设置了“卷标”位的任何目录条目。真正的卷标条目不会设置其他三个位。
2) 起始簇始终设置为 0，这是 DOS 文件不可能出现的值。
由于扩展的FAT系统与旧版本兼容，旧软件可以修改目录项。必须采取措施确保槽的有效性。扩展的FAT系统可以通过以下方式验证一个槽是否确实属于一个8.3目录项：

1) 定位。文件的槽总是紧接在对应的8.3目录项之前。此外，每个槽都有一个标识其在扩展文件名中顺序的ID。以下是“My Big File.Extension which is long”文件的8.3目录项及其对应长名称槽的一个简化的视图：

                <前面的文件...>
                <槽#3, ID = 0x43, 字符 = "h is long">
                <槽#2, ID = 0x02, 字符 = "xtension whic">
                <槽#1, ID = 0x01, 字符 = "My Big File.E">
                <目录项, 名称 = "MYBIGFIL.EXT">

.. note:: 注意槽是按从后往前的顺序存储的。槽编号从1到N。第N个槽通过与0x40进行“或”操作来标记为最后一个槽。

2) 校验和。每个槽都有一个别名校验值（alias_checksum）。校验和是根据8.3名称使用以下算法计算得出的：

                for (sum = i = 0; i < 11; i++) {
                        sum = (((sum&1)<<7)|((sum&0xfe)>>1)) + name[i]
                }

3) 如果最终槽中有空闲空间，在最后一个字符之后存储一个Unicode ``NULL (0x0000)``。之后，最终槽中所有未使用的字符设置为Unicode 0xFFFF。

最后需要注意的是，扩展名称是以Unicode存储的。每个Unicode字符占用两字节或四字节，采用UTF-16LE编码。
