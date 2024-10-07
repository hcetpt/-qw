============================
CD-ROM ioctl 调用总结
============================

- Edward A. Falk <efalk@google.com>

2004年11月

本文档试图描述由CD-ROM层支持的ioctl(2)调用。这些调用（截至Linux 2.6）主要实现在`drivers/cdrom/cdrom.c`和`drivers/block/scsi_ioctl.c`中。

ioctl值在`<linux/cdrom.h>`中列出。截至撰写本文时，它们如下：

	========================  ===============================================
	CDROMPAUSE		  暂停音频操作
	CDROMRESUME		  继续暂停的音频操作
	CDROMPLAYMSF		  播放音频MSF（struct cdrom_msf）
	CDROMPLAYTRKIND		  播放音频曲目/索引（struct cdrom_ti）
	CDROMREADTOCHDR		  读取TOC头部（struct cdrom_tochdr）
	CDROMREADTOCENTRY	  读取TOC条目（struct cdrom_tocentry）
	CDROMSTOP		  停止CD-ROM驱动器
	CDROMSTART		  启动CD-ROM驱动器
	CDROMEJECT		  弹出CD-ROM介质
	CDROMVOLCTRL		  控制输出音量（struct cdrom_volctrl）
	CDROMSUBCHNL		  读取子通道数据（struct cdrom_subchnl）
	CDROMREADMODE2		  读取CD-ROM模式2数据（2336字节）（struct cdrom_read）
	CDROMREADMODE1		  读取CD-ROM模式1数据（2048字节）（struct cdrom_read）
	CDROMREADAUDIO		  （struct cdrom_read_audio）
	CDROMEJECT_SW		  启用（1）/禁用（0）自动弹出
	CDROMMULTISESSION	  获取多会话光盘的最后一会话起始地址（struct cdrom_multisession）
	CDROM_GET_MCN		  获取“通用产品代码”（如果可用）（struct cdrom_mcn）
	CDROM_GET_UPC		  已弃用，请使用CDROM_GET_MCN代替
	CDROMRESET		  硬复位驱动器
	CDROMVOLREAD		  获取驱动器的音量设置（struct cdrom_volctrl）
	CDROMREADRAW		  以原始模式读取数据（2352字节）（struct cdrom_read）
	CDROMREADCOOKED		  以处理模式读取数据
	CDROMSEEK		  寻找MSF地址
	CDROMPLAYBLK		  仅限SCSI-CD（struct cdrom_blk）
	CDROMREADALL		  读取所有2646字节
	CDROMGETSPINDOWN	  返回4位的spindown值
	CDROMSETSPINDOWN	  设置4位的spindown值
	CDROMCLOSETRAY		  对应于CDROMEJECT
	CDROM_SET_OPTIONS	  设置行为选项
	CDROM_CLEAR_OPTIONS	  清除行为选项
	CDROM_SELECT_SPEED	  设置CD-ROM速度
	CDROM_SELECT_DISC	  选择光盘（针对点唱机）
	CDROM_MEDIA_CHANGED	  检查是否更换了介质
	CDROM_TIMED_MEDIA_CHANGE  检查自给定时间以来是否更换了介质（struct cdrom_timed_media_change_info）
	CDROM_DRIVE_STATUS	  获取托盘位置等信息
	CDROM_DISC_STATUS	  获取光盘类型等信息
	CDROM_CHANGER_NSLOTS	  获取插槽数量
	CDROM_LOCKDOOR		  锁定或解锁门
	CDROM_DEBUG		  开启或关闭调试消息
	CDROM_GET_CAPABILITY	  获取功能
	CDROMAUDIOBUFSIZ	  设置音频缓冲区大小
	DVD_READ_STRUCT		  读取结构
	DVD_WRITE_STRUCT	  写入结构
	DVD_AUTH		  认证
	CDROM_SEND_PACKET	  向驱动器发送一个数据包
	CDROM_NEXT_WRITABLE	  获取下一个可写块
	CDROM_LAST_WRITTEN	  获取光盘上最后一个已写块
	========================  ===============================================

以下信息是通过阅读内核源代码得出的。随着时间的推移可能会进行一些修正
--------------------------------------------------------------------------

一般说明：

	除非另有说明，所有ioctl调用成功时返回0，在出错时返回-1，并将errno设置为适当的值。（某些ioctl调用返回非负的数据值。）

	除非另有说明，所有ioctl调用在尝试将数据从用户地址空间复制到内核地址空间失败时返回-1并将errno设置为EFAULT。
个别驱动程序可能返回此处未列出的错误码
除非另有说明，所有数据结构和常量都在`<linux/cdrom.h>`中定义
--------------------------------------------------------------------------

CDROMPAUSE
	暂停音频操作

用法::

	  ioctl(fd, CDROMPAUSE, 0);

输入:
	无

输出:
	无

错误返回:
	- ENOSYS	驱动器不支持音频

CDROMRESUME
	继续暂停的音频操作

用法::

	  ioctl(fd, CDROMRESUME, 0);

输入:
	无

输出:
	无

错误返回:
	- ENOSYS	驱动器不支持音频

CDROMPLAYMSF
	播放音频MSF（struct cdrom_msf）

用法::

	  struct cdrom_msf msf;

	  ioctl(fd, CDROMPLAYMSF, &msf);

输入:
	cdrom_msf结构体，描述要播放的一段音乐

输出:
	无

错误返回:
	- ENOSYS	驱动器不支持音频

注释:
	- MSF表示分钟-秒-帧
	- LBA表示逻辑块地址
	- 段落由开始时间和结束时间描述，每个时间都表示为分钟:秒:帧
一帧是秒的1/75

CDROMPLAYTRKIND  
播放音轨/索引

（struct cdrom_ti）

用法::

  struct cdrom_ti ti;

  ioctl(fd, CDROMPLAYTRKIND, &ti);

输入:
  描述要播放音乐片段的cdrom_ti结构体

输出:
  无

错误返回:
  - ENOSYS: 光驱不具备音频功能

注释:
  - 段落由开始时间和结束时间描述，每个时间由音轨和索引组成

CDROMREADTOCHDR  
读取TOC头信息

（struct cdrom_tochdr）

用法::

  cdrom_tochdr header;

  ioctl(fd, CDROMREADTOCHDR, &header);

输入:
  cdrom_tochdr结构体

输出:
  cdrom_tochdr结构体

错误返回:
  - ENOSYS: 光驱不具备音频功能

CDROMREADTOCENTRY  
读取TOC条目

（struct cdrom_tocentry）

用法::

  struct cdrom_tocentry entry;

  ioctl(fd, CDROMREADTOCENTRY, &entry);

输入:
  cdrom_tocentry结构体

输出:
  cdrom_tocentry结构体

错误返回:
  - ENOSYS: 光驱不具备音频功能
  - EINVAL: entry.cdte_format 不是 CDROM_MSF 或 CDROM_LBA
  - EINVAL: 请求的音轨超出范围
  - EIO: 读取TOC时发生I/O错误

注释:
  - TOC 表示目录表
  - MSF 表示分钟-秒-帧
  - LBA 表示逻辑块地址

CDROMSTOP  
停止光驱

用法::

  ioctl(fd, CDROMSTOP, 0);

输入:
  无

输出:
  无

错误返回:
  - ENOSYS: 光驱不具备音频功能

注释:
  - 此ioctl的确切解释取决于设备，但大多数似乎会降低光驱转速

CDROMSTART  
启动光驱

用法::

  ioctl(fd, CDROMSTART, 0);

输入:
  无

输出:
  无

错误返回:
  - ENOSYS: 光驱不具备音频功能

注释:
  - 此ioctl的确切解释取决于设备，但大多数似乎会提升光驱转速和/或关闭托盘

其他设备会完全忽略此ioctl。
### CDROMEJECT
- 弹出 CD-ROM 媒体

**用法:**

```c
ioctl(fd, CDROMEJECT, 0);
```

**输入:**
- 无

**输出:**
- 无

**错误返回:**
- `ENOSYS`：CD 驱动器不具备弹出功能
- `EBUSY`：其他进程正在访问驱动器，或门被锁定

**备注:**
- 参见下面的 `CDROM_LOCKDOOR`

### CDROMCLOSETRAY
- CDROMEJECT 的对应操作

**用法:**

```c
ioctl(fd, CDROMCLOSETRAY, 0);
```

**输入:**
- 无

**输出:**
- 无

**错误返回:**
- `ENOSYS`：CD 驱动器不具备关闭托盘功能
- `EBUSY`：其他进程正在访问驱动器，或门被锁定

**备注:**
- 参见下面的 `CDROM_LOCKDOOR`

### CDROMVOLCTRL
- 控制输出音量（使用 `struct cdrom_volctrl`）

**用法:**

```c
struct cdrom_volctrl volume;

ioctl(fd, CDROMVOLCTRL, &volume);
```

**输入:**
- 包含最多 4 个通道音量的 `cdrom_volctrl` 结构体

**输出:**
- 无

**错误返回:**
- `ENOSYS`：CD 驱动器不具备音频功能

### CDROMVOLREAD
- 获取驱动器的音量设置（使用 `struct cdrom_volctrl`）

**用法:**

```c
struct cdrom_volctrl volume;

ioctl(fd, CDROMVOLREAD, &volume);
```

**输入:**
- 无

**输出:**
- 当前的音量设置

**错误返回:**
- `ENOSYS`：CD 驱动器不具备音频功能

### CDROMSUBCHNL
- 读取子通道数据（使用 `struct cdrom_subchnl`）

**用法:**

```c
struct cdrom_subchnl q;

ioctl(fd, CDROMSUBCHNL, &q);
```

**输入:**
- `cdrom_subchnl` 结构体

**输出:**
- `cdrom_subchnl` 结构体

**错误返回:**
- `ENOSYS`：CD 驱动器不具备音频功能
- `EINVAL`：格式不是 `CDROM_MSF` 或 `CDROM_LBA`

**备注:**
- 格式会根据用户请求转换为 `CDROM_MSF` 或 `CDROM_LBA`

### CDROMREADRAW
- 以原始模式读取数据（2352 字节）（使用 `struct cdrom_read`）

**用法:**

```c
union {
    struct cdrom_msf msf;        // 输入
    char buffer[CD_FRAMESIZE_RAW];// 返回
} arg;
ioctl(fd, CDROMREADRAW, &arg);
```

**输入:**
- 指示要读取地址的 `cdrom_msf` 结构体
  - 只有起始值有意义

**输出:**
- 数据写入用户提供的地址
错误返回：
- EINVAL：地址小于0，或msf小于0:2:0
- ENOMEM：内存不足

注释：
- 自2.6.8.1版本起，<linux/cdrom.h>中的注释表明此ioctl接受一个cdrom_read结构，但实际源代码读取的是一个cdrom_msf结构，并将数据写入同一地址
- MSF值通过以下公式转换为LBA值：

```
lba = (((m * CD_SECS) + s) * CD_FRAMES + f) - CD_MSF_OFFSET;
```


### CDROMREADMODE1
读取CD-ROM模式1数据（2048字节）

（struct cdrom_read）

注释：
- 与CDROMREADRAW相同，只是块大小为CD_FRAMESIZE（2048字节）


### CDROMREADMODE2
读取CD-ROM模式2数据（2336字节）

（struct cdrom_read）

注释：
- 与CDROMREADRAW相同，只是块大小为CD_FRAMESIZE_RAW0（2336字节）


### CDROMREADAUDIO
（struct cdrom_read_audio）

用法：
```
struct cdrom_read_audio ra;

ioctl(fd, CDROMREADAUDIO, &ra);
```

输入：
- 包含读取起点和长度的cdrom_read_audio结构

输出：
- 音频数据，返回到由ra指示的缓冲区

错误返回：
- EINVAL：格式不是CDROM_MSF或CDROM_LBA
- EINVAL：nframes不在范围[1 75]内
- ENXIO：驱动器没有队列（可能意味着无效的fd）
- ENOMEM：内存不足


### CDROMEJECT_SW
启用（1）/禁用（0）自动弹出功能

用法：
```
int val;

ioctl(fd, CDROMEJECT_SW, val);
```

输入：
- 指定自动弹出标志的标记

输出：
- 无

错误返回：
- ENOSYS：驱动器不支持弹出功能
- EBUSY：光驱门被锁住


### CDROMMULTISESSION
获取多会话磁盘的上一会话开始地址

（struct cdrom_multisession）

用法：
```
struct cdrom_multisession ms_info;

ioctl(fd, CDROMMULTISESSION, &ms_info);
```

输入：
- 包含所需格式的cdrom_multisession结构

输出：
- cdrom_multisession结构填充了上一会话信息

错误返回：
- EINVAL：格式不是CDROM_MSF或CDROM_LBA


### CDROM_GET_MCN
获取“通用产品代码”（如果可用）

（struct cdrom_mcn）

用法：
```
struct cdrom_mcn mcn;

ioctl(fd, CDROM_GET_MCN, &mcn);
```

输入：
- 无

输出：
- 通用产品代码

错误返回：
- ENOSYS：驱动器不支持读取MCN数据

注释：
- 源代码注释中提到：
```
虽然很少有音频光盘提供通用产品代码信息，该信息通常应该是盒子上的介质目录号。注意，光盘上的编码方式并不是所有光盘都一致！
```


### CDROM_GET_UPC
CDROM_GET_MCN（已废弃）

截至2.6.8.1版本未实现


### CDROMRESET
硬重置驱动器

用法：
```
ioctl(fd, CDROMRESET, 0);
```

输入：
- 无

输出：
- 无

错误返回：
- EACCES：访问被拒绝：需要CAP_SYS_ADMIN权限
- ENOSYS：驱动器不支持重置功能


### CDROMREADCOOKED
以处理模式读取数据

用法：
```
u8 buffer[CD_FRAMESIZE];

ioctl(fd, CDROMREADCOOKED, buffer);
```

输入：
- 无

输出：
- 2048字节的数据，处理模式

注释：
- 并非所有驱动器都实现了该功能


### CDROMREADALL
读取全部2646字节

与CDROMREADCOOKED相同，但读取2646字节
### CDROMSEEK
#### 寻道到指定的分钟-秒-扇区（MSF）地址

**用法示例：**

```c
struct cdrom_msf msf;

ioctl(fd, CDROMSEEK, &msf);
```

**输入参数：**
- 需要寻道到的 MSF 地址

**输出参数：**
- 无

---

### CDROMPLAYBLK
#### 仅适用于 SCSI 光驱

**结构体：**
- `struct cdrom_blk`

**用法示例：**

```c
struct cdrom_blk blk;

ioctl(fd, CDROMPLAYBLK, &blk);
```

**输入参数：**
- 播放区域

**输出参数：**
- 无

---

### CDROMGETSPINDOWN
#### 过时，仅适用于 IDE 光驱

**用法示例：**

```c
char spindown;

ioctl(fd, CDROMGETSPINDOWN, &spindown);
```

**输入参数：**
- 无

**输出参数：**
- 当前 4 位的停转值

---

### CDROMSETSPINDOWN
#### 过时，仅适用于 IDE 光驱

**用法示例：**

```c
char spindown;

ioctl(fd, CDROMSETSPINDOWN, &spindown);
```

**输入参数：**
- 控制停转的 4 位值（待补充更多细节）

**输出参数：**
- 无

---

### CDROM_SET_OPTIONS
#### 设置光驱的行为选项

**用法示例：**

```c
int options;

ioctl(fd, CDROM_SET_OPTIONS, options);
```

**输入参数：**
- 新的光驱选项值。逻辑或运算符组合如下：

| 选项代码 | 描述 |
| --- | --- |
| CDO_AUTO_CLOSE | 在首次打开时关闭托盘 |
| CDO_AUTO_EJECT | 在最后一次释放时打开托盘 |
| CDO_USE_FFLAGS | 在打开时使用 O_NONBLOCK 信息 |
| CDO_LOCK | 在文件打开时锁定托盘 |
| CDO_CHECK_TYPE | 在打开时检查数据类型 |

**输出参数：**
- 返回设置后的选项值。如果出错返回 -1。

**错误返回码：**
- `ENOSYS`：所选选项不被光驱支持

---

### CDROM_CLEAR_OPTIONS
#### 清除光驱的行为选项

**用法示例：**

与 `CDROM_SET_OPTIONS` 相同，但所选选项会被取消。

---

### CDROM_SELECT_SPEED
#### 设置 CD-ROM 的速度

**用法示例：**

```c
int speed;

ioctl(fd, CDROM_SELECT_SPEED, speed);
```

**输入参数：**
- 新的速度

**输出参数：**
- 无

**错误返回码：**
- `ENOSYS`：光驱不支持速度选择

---

### CDROM_SELECT_DISC
#### 选择光盘（适用于自动换盘机）

**用法示例：**

```c
int disk;

ioctl(fd, CDROM_SELECT_DISC, disk);
```

**输入参数：**
- 要加载到驱动器中的光盘编号

**输出参数：**
- 无

**错误返回码：**
- `EINVAL`：光盘编号超出驱动器容量

---

### CDROM_MEDIA_CHANGED
#### 检查媒体是否已更换

**用法示例：**

```c
int slot;

ioctl(fd, CDROM_MEDIA_CHANGED, slot);
```

**输入参数：**
- 要测试的槽号，除了自动换盘机外通常为零。也可以是特殊值 `CDSL_NONE` 或 `CDSL_CURRENT`

**输出参数：**
- 如果媒体已更换则返回 0 或 1；如果出错返回 -1
错误返回值：
- ENOSYS：驱动器无法检测介质更换
- EINVAL：插槽编号超出驱动器容量
- ENOMEM：内存不足

### CDROM_DRIVE_STATUS
获取托盘位置等信息
用法：

```c
int slot;
ioctl(fd, CDROM_DRIVE_STATUS, &slot);
```

输入：
要测试的插槽编号，通常为零（除自动换片机外）
也可以是特殊值 `CDSL_NONE` 或 `CDSL_CURRENT`

输出：
ioctl 返回值将是以下值之一：

```c
// 从 <linux/cdrom.h> 定义
CDS_NO_INFO      无信息
CDS_NO_DISC      没有光盘
CDS_TRAY_OPEN    托盘打开
CDS_DRIVE_NOT_READY 驱动器未准备好
CDS_DISC_OK      光盘正常
-1               错误
```

错误返回值：
- ENOSYS：驱动器无法检测驱动器状态
- EINVAL：插槽编号超出驱动器容量
- ENOMEM：内存不足

### CDROM_DISC_STATUS
获取光盘类型等信息
用法：

```c
ioctl(fd, CDROM_DISC_STATUS, 0);
```

输入：
无

输出：
ioctl 返回值将是以下值之一：

```c
// 从 <linux/cdrom.h> 定义
CDS_NO_INFO     无信息
CDS_AUDIO       音频光盘
CDS_MIXED       混合光盘
CDS_XA_2_2      XA模式2.2
CDS_XA_2_1      XA模式2.1
CDS_DATA_1      数据光盘
```

错误返回值：
目前没有

备注：
- 代码注释中提到：

    好了，问题就在这里开始。当前 CDROM_DISC_STATUS ioctl 接口是有缺陷的。它错误地假设所有的光盘要么全是数据盘，要么全是音频盘等等。虽然这通常是正确的，但也很常见的是光盘上有一些数据轨道和一些音频轨道。为了应对这种情况，我宣布如果光盘上有任何数据轨道，那么将返回数据光盘；如果有任何XA轨道，那么将返回XA光盘。我可以简化这个接口，将这些返回值合并到上面，但这更清楚地展示了当前接口的问题。可惜这个接口没有设计成使用位掩码…… —— Erik

    现在我们有了 CDS_MIXED 选项：混合类型的光盘。用户级别的程序员可能会觉得 ioctl 并不是很有用。—— david

### CDROM_CHANGER_NSLOTS
获取插槽数量
用法：

```c
ioctl(fd, CDROM_CHANGER_NSLOTS, 0);
```

输入：
无

输出：
ioctl 返回值将是 CD 更换器中的插槽数量。通常对于非多碟设备为1

错误返回值：
无

### CDROM_LOCKDOOR
锁定或解锁门
用法：

```c
int lock;
ioctl(fd, CDROM_LOCKDOOR, &lock);
```

输入：
门锁标志，1=锁定，0=解锁

输出：
无

错误返回值：
- EDRIVE_CANT_DO_THIS：门锁功能不支持
### EBUSY

当多个用户打开驱动器且没有CAP_SYS_ADMIN权限时尝试解锁。

#### 注释：
截至2.6.8.1版本，锁标志是一个全局锁，意味着所有CD驱动器将一起锁定或解锁。这可能是一个bug。
`EDRIVE_CANT_DO_THIS` 值定义在 `<linux/cdrom.h>` 中，并且目前（2.6.8.1）与 `EOPNOTSUPP` 相同。

### CDROM_DEBUG
开启或关闭调试信息。

#### 用法：
```c
int debug;
ioctl(fd, CDROM_DEBUG, debug);
```

#### 输入：
- 调试标志：0 = 禁用，1 = 启用

#### 输出：
- ioctl 返回值将是新的调试标志

#### 错误返回：
- `EACCES`：访问被拒绝：需要 `CAP_SYS_ADMIN` 权限

### CDROM_GET_CAPABILITY
获取设备功能。

#### 用法：
```c
ioctl(fd, CDROM_GET_CAPABILITY, 0);
```

#### 输入：
- 无

#### 输出：
- ioctl 返回值是当前设备的功能标志。参见 `CDC_CLOSE_TRAY`, `CDC_OPEN_TRAY` 等

### CDROMAUDIOBUFSIZ
设置音频缓冲区大小。

#### 用法：
```c
int val;
ioctl(fd, CDROMAUDIOBUFSIZ, val);
```

#### 输入：
- 新的音频缓冲区大小

#### 输出：
- ioctl 返回值是新的音频缓冲区大小，如果出错则返回 -1

#### 错误返回：
- `ENOSYS`：此驱动程序不支持该功能

#### 注释：
并非所有驱动程序都支持此功能。

### DVD_READ_STRUCT
读取结构信息。

#### 用法：
```c
dvd_struct s;
ioctl(fd, DVD_READ_STRUCT, &s);
```

#### 输入：
- `dvd_struct` 结构体，包含：
    - `type`：指定所需的信息类型，可以是 `DVD_STRUCT_PHYSICAL`, `DVD_STRUCT_COPYRIGHT`, `DVD_STRUCT_DISCKEY`, `DVD_STRUCT_BCA`, `DVD_STRUCT_MANUFACT`
    - `physical.layer_num`：所需的层号，从 0 开始计数
    - `copyright.layer_num`：所需的层号，从 0 开始计数
    - `disckey.agid`

#### 输出：
- `dvd_struct` 结构体，包含：
    - `physical`：对于 `type == DVD_STRUCT_PHYSICAL`
    - `copyright`：对于 `type == DVD_STRUCT_COPYRIGHT`
    - `disckey.value`：对于 `type == DVD_STRUCT_DISCKEY`
    - `bca.{len,value}`：对于 `type == DVD_STRUCT_BCA`
    - `manufact.{len,value}`：对于 `type == DVD_STRUCT_MANUFACT`

#### 错误返回：
- `EINVAL`：`physical.layer_num` 超过层数
- `EIO`：从驱动器收到无效响应

### DVD_WRITE_STRUCT
写入结构信息。

#### 说明：
截至2.6.8.1版本，此功能未实现。

### DVD_AUTH
认证信息。

#### 用法：
```c
dvd_authinfo ai;
ioctl(fd, DVD_AUTH, &ai);
```

#### 输入：
- `dvd_authinfo` 结构体。参见 `<linux/cdrom.h>`

#### 输出：
- `dvd_authinfo` 结构体

#### 错误返回：
- `ENOTTY`：`ai.type` 不被识别

### CDROM_SEND_PACKET
向驱动器发送一个数据包。

#### 用法：
```c
struct cdrom_generic_command cgc;
ioctl(fd, CDROM_SEND_PACKET, &cgc);
```

#### 输入：
- 包含要发送的数据包的 `cdrom_generic_command` 结构体

#### 输出：
- 无
- 包含结果的 `cdrom_generic_command` 结构体
错误返回：
    - EIO

        命令失败
    - EPERM

        操作不允许，原因可能是尝试在一个只读打开的驱动器上执行写命令，或者是因为该命令需要 CAP_SYS_RAWIO 权限
    - EINVAL

        cgc.data_direction 未设置

CDROM_NEXT_WRITABLE
获取下一个可写块

用法示例：

```c
    long next;

    ioctl(fd, CDROM_NEXT_WRITABLE, &next);
```

输入：
    无

输出：
    下一个可写块

注意事项：
    如果设备不直接支持此 ioctl，则 ioctl 返回 CDROM_LAST_WRITTEN + 7

CDROM_LAST_WRITTEN
获取光盘上最后写入的块

用法示例：

```c
    long last;

    ioctl(fd, CDROM_LAST_WRITTEN, &last);
```

输入：
    无

输出：
    光盘上最后写入的块

注意事项：
    如果设备不直接支持此 ioctl，则结果从光盘的目录表中得出。如果无法读取目录表，则此 ioctl 返回错误。
