===============================
Linux Gadget 串行驱动程序 v2.0
===============================

2004年11月20日

（2008年5月8日更新至v2.3版）


许可与免责声明
----------------------
本程序是自由软件；你可以按照自由软件基金会发布的GNU通用公共许可证的条款重新发布或修改它；可以是许可证的第2版，也可以是你选择的任何后续版本。
本程序以“按原样”提供，希望对您有所帮助，但不附带任何形式的保证；甚至不包括对适销性和特定目的适用性的默示保证。详情请参阅GNU通用公共许可证。
你应该随同本程序收到一份GNU通用公共许可证的副本；如果没有，请写信给自由软件基金会，Inc.，地址为59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
本文件及Gadget串行驱动程序本身均受版权所有 © 2004 Al Borchers (alborchers@steinerpoint.com)
如果您有关于此驱动程序的问题、遇到问题或有任何建议，请联系Al Borchers (alborchers@steinerpoint.com)

前提条件
-------------
Gadget串行驱动程序的版本适用于2.4 Linux内核，但本文档假设您使用的是2.6 Linux内核中的v2.3或更高版本的Gadget串行驱动程序。
本文档假设您熟悉Linux和Windows，并知道如何配置和构建Linux内核、运行标准工具、使用minicom和HyperTerminal以及操作USB和串行设备。它还假设您将Linux Gadget和USB驱动程序配置为模块。
在v2.3版本的驱动程序中，主次设备节点不再静态定义。您的基于Linux的系统应挂载sysfs在/sys目录下，并使用“mdev”（Busybox中）或“udev”来创建与/sys/class/tty文件匹配的/dev节点。

概述
--------
Gadget串行驱动程序是一个Linux USB Gadget驱动程序，即USB设备端驱动程序。它运行在一个具有USB设备硬件的Linux系统上；例如，PDA、嵌入式Linux系统或带有USB开发卡的PC。
Gadget串行驱动程序通过USB与主机PC上的CDC ACM驱动程序或通用USB串行驱动程序通信：

```
主机
--------------------------------------
| 主机侧操作系统 | CDC ACM | USB主机控制器 |
| (Linux或Windows) | 或 | 驱动程序 | USB |
| | 通用USB串行驱动 | 和 |--------|
| | | USB堆栈 | |
--------------------------------------         |
                                                  |
                                                  |
                                                  |
Gadget                                         |
--------------------------------------         |
| 设备侧Linux | Gadget | USB外设 |        |
| 操作系统 | 串行驱动 | 控制器 |        |
| | | 驱动程序 |--------|
| | | 和 | |
| | | USB堆栈 | |
--------------------------------------
```

在设备侧Linux系统上，Gadget串行驱动程序看起来像一个串行设备。
在主机端系统中，Gadget 串行设备看起来就像一个符合 CDC ACM 规范的类设备或是一个具有批量输入和输出端点的简单厂商特定设备，并且它被类似地当作其他串行设备来处理。
主机端驱动程序可以是任何符合 ACM 规范的驱动程序，或者是能够与具有简单批量输入/输出接口的设备通信的任何驱动程序。Gadget 串行设备已经通过 Linux 的 ACM 驱动、Windows 的 usbser.sys ACM 驱动以及 Linux 的通用串行驱动进行了测试。
当运行 Gadget 串行驱动程序和主机端的 ACM 或通用串行驱动程序时，你应该能够在主机和 Gadget 端系统之间像通过串行电缆连接一样进行通信。
Gadget 串行驱动程序仅提供简单的不可靠数据通信。目前它还没有处理流控制或许多正常串行设备具有的其他功能。

### 安装 Gadget 串行驱动程序

为了使用 Gadget 串行驱动程序，你必须为 Linux Gadget 端内核配置“支持 USB Gadgets”，选择“USB 外设控制器”（例如 net2280），以及“串行 Gadget”驱动程序。所有这些都在配置内核时列于“USB Gadget 支持”之下。然后重新构建并安装内核或模块。
然后你需要加载 Gadget 串行驱动程序。为了作为 ACM 设备加载它（推荐用于兼容性），执行以下操作：

```shell
modprobe g_serial
```

为了作为厂商特定的批量输入/输出设备加载它，执行以下操作：

```shell
modprobe g_serial use_acm=0
```

这也会自动加载底层的 Gadget 外设控制器驱动程序。每次重启 Gadget 端 Linux 系统时都需要这样做。如果需要，你可以将这些命令添加到启动脚本中。
你的系统应该使用 mdev（来自 busybox）或 udev 来创建设备节点。设置好此 Gadget 驱动程序后，你应该能看到一个 `/dev/ttyGS0` 节点：

```shell
# ls -l /dev/ttyGS0
crw-rw----    1 root     root     253,   0 May  8 14:10 /dev/ttyGS0
#
```

请注意主设备号（上面的 253）是系统特定的。如果你需要手动创建 `/dev` 节点，正确的数字可以在 `/sys/class/tty/ttyGS0/dev` 文件中找到。
当你早期链接这个 Gadget 驱动程序，甚至是静态链接时，你可能希望在 `/etc/inittab` 中设置一个条目以在其上运行 “getty”。
`/dev/ttyGS0` 应该像大多数其他串行端口一样工作。
如果 Gadget 串行设备作为 ACM 设备加载，则你希望在主机端使用 Windows 或 Linux 的 ACM 驱动程序。如果 Gadget 串行设备作为批量输入/输出设备加载，则你希望在主机端使用 Linux 的通用串行驱动程序。请按照下面适当的说明来安装主机端驱动程序。
### 安装Windows主机ACM驱动程序
为了使用Windows ACM驱动程序，您必须有“linux-cdc-acm.inf”文件（随此文档提供），该文件支持所有近期版本的Windows。
当gadget串行驱动程序加载并且USB设备通过USB线缆连接到Windows主机时，Windows应该会识别gadget串行设备并请求安装驱动程序。告诉Windows在包含“linux-cdc-acm.inf”文件的文件夹中查找驱动程序。
例如，在Windows XP上，当gadget串行设备首次插入时，“发现新硬件向导”将启动。选择“从列表或指定位置安装（高级）”，然后在下一个屏幕上选择“包括这个位置在搜索中”并输入路径或浏览至包含“linux-cdc-acm.inf”文件的文件夹。
Windows会提示Gadget串行驱动程序未通过Windows徽标测试，但请选择“继续”并完成驱动程序安装。
在Windows XP上，在“设备管理器”（位于“控制面板”、“系统”、“硬件”下）展开“端口(COM和LPT)”条目，您应该能看到“Gadget Serial”被列为其一个COM端口的驱动程序。
要卸载Windows XP上的“Gadget Serial”驱动程序，请在“设备管理器”中右键点击“Gadget Serial”项并选择“卸载”。

### 安装Linux主机ACM驱动程序
为了使用Linux ACM驱动程序，您必须为Linux主机端内核配置“USB主机侧支持”以及“USB调制解调器(CDC ACM)支持”。
一旦gadget串行驱动程序加载并且USB设备通过USB线缆连接到Linux主机时，主机系统应该能识别gadget串行设备。例如，命令：

  `cat /sys/kernel/debug/usb/devices`

应该显示类似如下内容：

```
T:  Bus=01 Lev=01 Prnt=01 Port=01 Cnt=02 Dev#=  5 Spd=480 MxCh= 0
D:  Ver= 2.00 Cls=02(comm.) Sub=00 Prot=00 MxPS=64 #Cfgs=  1
P:  Vendor=0525 ProdID=a4a7 Rev= 2.01
S:  Manufacturer=Linux 2.6.8.1 with net2280
S:  Product=Gadget Serial
S:  SerialNumber=0
C:* #Ifs= 2 Cfg#= 2 Atr=c0 MxPwr=  2mA
I:  If#= 0 Alt= 0 #EPs= 1 Cls=02(comm.) Sub=02 Prot=01 Driver=acm
E:  Ad=83(I) Atr=03(Int.) MxPS=   8 Ivl=32ms
I:  If#= 1 Alt= 0 #EPs= 2 Cls=0a(data ) Sub=00 Prot=00 Driver=acm
E:  Ad=81(I) Atr=02(Bulk) MxPS= 512 Ivl=0ms
E:  Ad=02(O) Atr=02(Bulk) MxPS= 512 Ivl=0ms
```

如果Linux主机配置正确，ACM驱动程序应该会自动加载。“lsmod”命令应该会显示“acm”模块已加载。

### 安装Linux主机通用USB串行驱动程序
为了使用Linux通用USB串行驱动程序，您必须为Linux主机端内核配置“USB主机侧支持”、“USB串行转换器支持”以及“USB通用串行驱动程序”。
一旦gadget串行驱动程序加载并且USB设备通过USB线缆连接到Linux主机时，主机系统应该能识别gadget串行设备。例如，命令：

  `cat /sys/kernel/debug/usb/devices`

应该显示类似如下内容：

```
T:  Bus=01 Lev=01 Prnt=01 Port=01 Cnt=02 Dev#=  6 Spd=480 MxCh= 0
D:  Ver= 2.00 Cls=ff(vend.) Sub=00 Prot=00 MxPS=64 #Cfgs=  1
P:  Vendor=0525 ProdID=a4a6 Rev= 2.01
S:  Manufacturer=Linux 2.6.8.1 with net2280
S:  Product=Gadget Serial
S:  SerialNumber=0
C:* #Ifs= 1 Cfg#= 1 Atr=c0 MxPwr=  2mA
I:  If#= 0 Alt= 0 #EPs= 2 Cls=0a(data ) Sub=00 Prot=00 Driver=serial
E:  Ad=81(I) Atr=02(Bulk) MxPS= 512 Ivl=0ms
E:  Ad=02(O) Atr=02(Bulk) MxPS= 512 Ivl=0ms
```

您需要加载usbserial驱动程序并显式设置其参数以配置它来识别gadget串行设备，例如：

  `echo 0x0525 0xA4A6 >/sys/bus/usb-serial/drivers/generic/new_id`

传统的方法是使用模块参数：

  `modprobe usbserial vendor=0x0525 product=0xA4A6`

如果一切正常，usbserial会在系统日志中打印一条消息，内容类似于“Gadget Serial转换器现已连接至ttyUSB0”。
通过 Minicom 或 HyperTerminal 进行测试
-------------------------------------
一旦设备串行驱动程序和主机驱动程序都已安装，
并且通过 USB 线将设备连接到主机，您应该能够
在设备和主机系统之间通过 USB 进行通信。
您可以使用 Minicom 或 HyperTerminal 来尝试这一点。

在设备端运行 “minicom -s” 来配置一个新的 Minicom 会话。
在“串行端口设置”下，将“/dev/ttygserial” 设置为
“串行设备”。设置波特率、数据位、校验位以及停止位，
分别为 9600、8、无以及 1 —— 这些设置大多不重要。
在“调制解调器和拨号”下删除所有调制解调器和拨号字符串。

对于运行了 ACM 驱动程序的 Linux 主机，类似地配置 Minicom，
但使用 “/dev/ttyACM0” 作为“串行设备”。（如果还有其他
ACM 设备连接，请适当更改设备名称。）

对于运行了通用 USB 串行驱动程序的 Linux 主机，类似地配置
Minicom，但使用 “/dev/ttyUSB0” 作为“串行设备”。
（如果有其他 USB 串行设备连接，请适当更改设备名称。）

对于 Windows 主机，配置一个新的 HyperTerminal 会话以使用
分配给设备串行的 COM 端口。当 HyperTerminal 连接到设备串行
设备时，“端口设置” 将自动设置，因此您可以保留默认值——
这些设置大多不重要。

配置并运行 Minicom 在设备端，并在主机端配置并运行 Minicom
或 HyperTerminal 后，您应该能够在设备端与主机端之间发送数据。
在设备端终端窗口上键入的任何内容都应该出现在主机端的终端
窗口中，反之亦然。
