===== USB 串口 =====

简介
====

当前的 USB 串口驱动支持多种不同的 USB 到串口转换器产品，同时也支持一些从用户空间通过串口接口与设备通信的设备。关于不同设备的具体信息，请参阅下面各个产品的部分。

配置
====

目前，该驱动可以同时处理最多 256 个不同的串口接口。
该驱动使用的主设备号为 188，要使用此驱动，需要创建以下节点：

```
mknod /dev/ttyUSB0 c 188 0
mknod /dev/ttyUSB1 c 188 1
mknod /dev/ttyUSB2 c 188 2
mknod /dev/ttyUSB3 c 188 3

...

mknod /dev/ttyUSB254 c 188 254
mknod /dev/ttyUSB255 c 188 255
```

当设备连接并被驱动识别后，驱动会向系统日志打印出已绑定到哪些节点的信息。

支持的特定设备
===============

ConnectTech WhiteHEAT 4 端口转换器
----------------------------------

ConnectTech 提供了大量关于他们设备的信息，并提供了测试用的单元。该驱动得到了 Connect Tech Inc. 的官方支持。
[官方网站](http://www.connecttech.com)

对于该驱动有任何疑问或问题，请联系 Connect Tech 的技术支持部门：support@connecttech.com

HandSpring Visor、Palm USB 和 Clié USB 驱动
-----------------------------------------------

该驱动适用于所有 HandSpring USB、Palm USB 和 Sony Clié USB 设备。
仅当设备尝试连接到主机时，该设备才会作为有效的USB设备出现在主机上。发生这种情况时，设备会正确地枚举、分配端口，然后应该可以进行通信。当设备被移除或在设备上取消连接时，驱动程序会妥善清理。

**注释：**
为了与设备通信，必须先按下同步按钮，然后再尝试让任何程序与设备通信。
这与当前的pilot-xfer和其他包的文档相悖，但由于设备中的硬件限制，这是唯一可行的方法。
当设备连接后，尝试通过第二个端口与其通信（如果没有其他USB串行设备，则通常是/dev/ttyUSB1）。系统日志应该会告诉你哪个端口用于HotSync传输。"通用"端口可用于其他设备通信，例如PPP链接。
对于某些Sony Clié设备，必须使用/dev/ttyUSB0来与设备通信。这适用于所有OS版本3.5的设备，以及大多数已经通过闪存升级到新版本操作系统的设备。请参阅内核系统日志以获取正确的端口信息。
如果按下同步按钮后，系统日志中没有任何显示，请尝试重置设备，首先进行热重启，必要时再进行冷重启。有些设备需要这样操作才能正确地与USB端口通信。
未编译进内核的设备可以通过模块参数指定。例如，modprobe visor vendor=0x54c product=0x66。

关于这部分驱动程序有一个网页和邮件列表：
http://sourceforge.net/projects/usbvisor/

对于此驱动程序有任何问题或遇到问题，请联系Greg Kroah-Hartman，邮箱：greg@kroah.com

### PocketPC PDA 驱动程序
------------------------

此驱动程序可用于通过USB线缆/底座将Compaq iPAQ、HP Jornada、Casio EM500以及其他运行Windows CE 3.0或PocketPC 2002的PDA连接到计算机。
大多数ActiveSync支持的设备都可以直接使用。
对于其他设备，请使用模块参数指定产品和供应商ID。例如，modprobe ipaq vendor=0x3f0 product=0x1125。

驱动程序提供了一个串行接口（通常位于/dev/ttyUSB0），通过它可以运行ppp并建立到PDA的TCP/IP连接。一旦完成，就可以传输文件、备份数据、下载电子邮件等。使用USB的最大优势在于速度——我可以在我的iPAQ上实现73至113千字节/秒的下载/上传速度。
此驱动程序只是利用USB连接所需的组件之一。请访问http://synce.sourceforge.net，其中包含了必要的包和简单的分步指南。
一旦连接，您可以使用Win CE程序如ftpView、Pocket Outlook从PDA端以及xcerdisp、synce工具从Linux端。
要使用Pocket IE，请按照http://www.tekguru.co.uk/EM500/usbtonet.htm上的说明进行操作以在Win98上实现相同的功能。忽略代理服务器的部分；与Win98不同的是，Linux完全能够转发数据包。对于iPAQ来说至少还需要一个修改——通过前往“开始/设置/连接”菜单并取消勾选“自动同步...”框来禁用自动同步功能。进入“开始/程序/连接”，连接电缆，并选择“usbdial”（或您为新的USB连接命名的名称）。最终您应该会看到一个显示为已连接状态的“连接到usbdial”的窗口。
如果由于某些原因无法正常工作，请加载usbserial和ipaq模块，并将模块参数“debug”设置为1，然后检查系统日志。
您也可以尝试在尝试连接之前对您的PDA进行软重置。
根据您的PDA型号，可能会有其他功能可用。据Wes Cilldhaire <billybobjoehenrybob@hotmail.com>所述，在Toshiba E570上，如果您进入引导加载器（按住电源键的同时按下复位按钮，持续按住电源键直到显示引导加载器屏幕），然后将其放入底座同时加载ipaq驱动程序，在/dev/ttyUSB0上打开终端，它会为您提供一个“USB刷新”终端，可用于刷新ROM及微码...因此，您不再需要购买Toshiba价值350美元的串行线来进行刷新了！:D
**注意：**此方法未经测试。请自行承担风险。
对于驱动程序有任何疑问或问题，请联系Ganesh Varadarajan <ganesh@veritas.com>。

### Keyspan PDA串行适配器

---

单端口DB-9串行适配器，主要作为iMac的PDA适配器推广（大多在Macintosh目录中销售，透明白色/绿色适配器外壳）。
这是一个相对简单的设备。固件是自制的。
此驱动程序同样适用于Xircom/Entrega单端口串行适配器。
当前状态：

- **支持的功能:**
  - 基本输入/输出（已通过'cu'进行测试）
  - 当串行线路无法跟上时的阻塞写入
  - 改变波特率（最高至115200）
  - 获取/设置调制解调器控制针脚（TIOCM{GET,SET,BIS,BIC}）
  - 发送中断信号（尽管持续时间看起来存在问题）

- **不支持的功能:**
  - 设备字符串（内核记录的日志中有尾部二进制垃圾信息）
  - 设备ID不正确，可能会与其他Keyspan产品冲突
  - 改变波特率时应清除发送/接收队列以避免出现半字符

- **待办事项列表中的重要项目:**
  - 校验、每字符7位或8位、1或2个停止位
  - 硬件流控
  - 并非所有的标准USB描述符都被处理：
    - Get_Status, Set_Feature, O_NONBLOCK, select()

对于此驱动程序有任何疑问或问题，请联系Brian Warner at warner@lothar.com。

### Keyspan USA系列串行适配器

---

单端口、双端口和四端口适配器 - 驱动程序使用由Keyspan提供的固件，并在其支持下开发。
当前状态：

    已经支持了 USA-18X、USA-28X、USA-19、USA-19W 和 USA-49W，并且已经在不同的波特率下使用 8-N-1 字符设置进行了较为彻底的测试。其他字符长度和校验设置目前尚未进行测试。
USA-28 尚未得到支持，但实现起来应该相当直接。如果您需要这一功能，请联系维护者。
更多信息可参考：

        http://www.carnationsoftware.com/carnation/Keyspan.html

  对于此驱动有任何疑问或遇到问题，请联系 Hugh Blemings，邮箱：hugh@misc.nu。

FTDI 单端口串行驱动
------------------------

  这是一个单端口 DB-25 串行适配器。
支持的设备包括：

                - TripNav TN-200 USB GPS
                - Navis Engineering Bureau CH-4711 USB GPS

  对于此驱动有任何疑问或遇到问题，请联系 Bill Ryder。

ZyXEL omni.net lcd plus ISDN TA
-------------------------------

  这是一款 ISDN 调制解调器。无论是成功案例还是遇到的问题，请向 azummo@towertech.it 报告。

Cypress M8 CY4601 家族串行驱动
-------------------------------

  此驱动主要由 Neil "koyama" Whelchel 开发。自那以后，已经对该驱动进行了改进以支持动态串行线路设置和改进的线路处理。该驱动在很大程度上是稳定的，并已在多处理器机器上进行了测试（双 P2）。

    CY4601 家族支持的芯片组包括：

		CY7C63723、CY7C63742、CY7C63743、CY7C64013

    支持的设备包括：

		- DeLorme 的 USB Earthmate GPS（SiRF Star II LP 架构）
		- Cypress HID->COM RS232 适配器

		注：
			Cypress Semiconductor 表示与 HID->COM 设备无任何关联
大多数使用 CY4601 家族芯片组的设备应能与该驱动兼容。只要它们遵循 CY4601 USB 串行规范即可。
技术说明：

        Earthmate 默认以 4800 8N1 启动... 驱动程序在启动时会初始化为这种设置。usbserial 核心提供了其余的 termios 设置，以及一些自定义的 termios 以便输出格式正确且可解析。
要将设备置于 sirf 模式，可以发出 NMEA 命令：

		$PSRF100,<protocol>,<baud>,<databits>,<stopbits>,<parity>*CHECKSUM
		$PSRF100,0,9600,8,1,0*0C

		然后只需将端口的 termios 设置与此相匹配即可开始通信
据我所知，它支持几乎所有的 sirf 命令，这些命令在具有 2.31 固件版本的在线文档中都有记载，但存在一些未知的消息 ID。
HID->COM 适配器的最大波特率为 115200bps。请注意，该设备在提高线电压方面存在问题或无法正常工作。
这段英文可以翻译为：

---

**将能够正常工作在空调制解调器链接上，只要你没有尝试在不修改适配器以设置线路高电平的情况下连接两个设备。**

该驱动程序是SMP安全的。使用该驱动程序传输文件时性能相对较低。这正在改进中，但我愿意接受补丁。一个urb队列或数据包缓冲区可能符合要求。

如果你有任何问题、遇到问题、提供补丁、功能请求等，可以通过电子邮件联系我：

					dignome@gmail.com

		（你的问题/补丁也可以提交给usb-devel）

**Digi AccelePort 驱动程序**
----------------------

此驱动程序支持Digi AccelePort USB 2端口和4端口设备（含并行端口），以及2端口和4端口USB串行转换器。该驱动程序**尚不支持**Digi AccelePort USB 8端口设备。
此驱动程序与SMP和usb-uhci驱动程序兼容。它**不与**uhci驱动程序在SMP下兼容。
驱动程序通常工作正常，但我们仍需实现更多的ioctl命令，并完成最终测试和调试。USB 2端口上的并行端口作为串行到并行转换器受到支持；换句话说，在Linux上它看起来像是另一个USB串行端口，尽管物理上它确实是一个并行端口。Digi AccelePort USB 8端口**尚未得到支持**。
对于该驱动程序的问题或疑虑，请联系Peter Berger (pberger@brimson.com) 或 Al Borchers (alborchers@steinerpoint.com)。

**Belkin USB串行适配器F5U103**
--------------------------------

由Belkin制造的单端口DB-9/PS-2串行适配器，固件来自eTEK Labs。
Peracom单端口串行适配器也适用于此驱动程序，以及GoHubs适配器。
当前状态：

- 已测试且工作正常的包括：
  
  - 波特率：300-230400
  - 数据位：5-8
  - 停止位：1-2
  - 校验位：N, E, O, M, S
  - 握手：无，软件（XON/XOFF），硬件（CTSRTS, CTSDTR）[1]_
  - 断线：设置和清除
  - 线路控制：输入/输出查询和控制 [2]_

.. [1]
         硬件输入流控制仅在固件版本高于2.06时启用。阅读源代码注释，了解有关Belkin固件错误的描述。硬件输出流控制对所有固件版本均有效。
.. [2]
         输入（CTS, DSR, CD, RI）的查询显示最后报告的状态。输出（DTR, RTS）的查询显示最后请求的状态，可能不会反映通过自动硬件流控制设置的当前状态。
待办事项列表：
- 添加真实的调制解调器控制线查询功能。当前跟踪的是由中断报告的状态和请求的状态。
- 将UART错误条件下的错误报告添加回应用程序。
- 添加对冲洗（flush）ioctl的支持。
- 添加所有缺失的功能 :) 

对于本驱动程序有任何问题或遇到任何问题，请联系William Greathouse，邮箱：wgreathouse@smva.com

Empeg empeg-car Mark I/II 驱动程序
----------------------------------

这是一个实验性的驱动程序，用于为Empeg empeg-car MP3播放器的客户端同步工具提供连接支持。
提示：
    * 别忘了为ttyUSB{0,1,2,...}创建设备节点
    * 使用modprobe empeg命令（modprobe是您的好帮手）
    * 使用emptool --usb /dev/ttyUSB0命令（或者使用您命名的设备节点）

对于本驱动程序有任何问题或遇到任何问题，请联系Gary Brubaker，邮箱：xavyer@ix.netcom.com

MCT USB单端口串行适配器 U232
---------------------------------------

此驱动程序适用于Magic Control Technology Corp.的MCT USB-RS232转换器（25针，型号号U232-P25）。还有另一款9针的型号号U232-P9。更多关于此设备的信息可以在制造商网站上找到：http://www.mct.com.tw
该驱动程序总体上已经可以工作，但仍需进行更多的测试。
它源自Belkin USB串行适配器F5U103驱动程序，并且其待办事项列表同样适用于本驱动程序。
此驱动程序还被发现可以用于其他具有相同供应商ID但不同产品ID的产品。Sitecom的U232-P25串行转换器使用产品ID 0x230和供应商ID 0x711，可以与本驱动程序兼容。同时，D-Link的DU-H3SP USB BAY也可以与本驱动程序兼容。
对于本驱动程序有任何问题或遇到任何问题，请联系Wolfgang Grandegger，邮箱：wolfgang@ces.ch

Inside Out Networks Edgeport驱动程序
-----------------------------------

此驱动程序支持所有由Inside Out Networks制造的设备，具体包括以下型号：

       - Edgeport/4
       - Rapidport/4
       - Edgeport/4t
       - Edgeport/2
       - Edgeport/4i
       - Edgeport/2i
       - Edgeport/421
       - Edgeport/21
       - Edgeport/8
       - Edgeport/8 Dual
       - Edgeport/2D8
       - Edgeport/4D8
       - Edgeport/8i
       - Edgeport/2 DIN
       - Edgeport/4 DIN
       - Edgeport/16 Dual

对于本驱动程序有任何问题或遇到任何问题，请联系Greg Kroah-Hartman，邮箱：greg@kroah.com

REINER SCT cyberJack PINPAD/E-COM USB 芯片卡读取器
-----------------------------------------------------

接口支持ISO 7816兼容的接触式芯片卡，例如GSM SIM卡。
当前状态：

这是此USB读卡器驱动程序的内核部分。
还有一个CT-API驱动程序的用户空间部分可用。下载站点待定。目前，您可以向维护者（linux-usb@sii.li）请求它。
对于该驱动程序的任何问题或遇到的问题，请联系 linux-usb@sii.li

Prolific PL2303 驱动程序
-----------------------

  此驱动程序支持所有包含Prolific的PL2303芯片的设备。这包括许多单端口USB到串行转换器、超过70%的USB GPS设备（2010年时）、以及一些USB不间断电源（UPS）。来自Aten（如UC-232）和IO-Data的设备与此驱动程序兼容，还包括DCU-11移动电话线缆。
对于此驱动程序的任何问题或遇到的问题，请联系 Greg Kroah-Hartman (greg@kroah.com)

KL5KUSB105 芯片组 / PalmConnect USB 单端口适配器
--------------------------------------------------------

当前状态：

  该驱动程序是通过分析Palm在Windows下的USB总线事务来编写的，因此仍有许多功能缺失。值得注意的是，某些串行ioctl操作有时会被模拟或尚未实现。然而，有关DSR和CTS线路状态的信息支持已实现（虽然不够完美），所以您最喜爱的autopilot(1) 和 pilot-manager守护进程调用可以正常工作。支持高达115200波特率，但不支持握手协议（无论是软件还是硬件），因此在握手问题解决之前，在大量数据传输时降低使用速率是明智的选择。
请访问http://www.uuhaus.de/linux/palmconnect.html获取关于此驱动程序的最新信息。

Winchiphead CH341 驱动程序
------------------------

  本驱动程序适用于Winchiphead CH341 USB-RS232转换器。该芯片还实现了IEEE 1284并行端口、I2C和SPI，但这些功能目前尚不受支持。该驱动程序是通过对Windows驱动程序的行为进行分析得出的协议，目前没有数据手册可供参考。
制造商网站：http://www.winchiphead.com/
对于此驱动程序的任何问题或遇到的问题，请联系 frank@kingswood-consulting.co.uk

Moschip MCS7720, MCS7715 驱动程序
-------------------------------

  这些芯片出现在多个制造商销售的设备中，例如Syba和Cables Unlimited。可能还有其他厂商。MCS7720提供两个串行端口，而MCS7715则提供一个串行端口和一个标准PC并行端口。
对MCS7715的并行端口支持需要单独启用选项，并且只有在Device Drivers配置菜单顶层启用了并行端口支持后才会出现。目前仅支持并行端口的兼容模式（无ECP/EPP）。
待办事项：
    - 实现并行端口的 ECP/EPP 模式
- 当前高于 115200 的波特率存在问题
- 基于 Moschip MCS7703 的单串口设备可能只需在 usb_device_id 表中简单添加即可与本驱动程序兼容。由于我没有这类设备，因此无法确定
通用串口驱动程序
---------------------

  如果您的设备不属于上述列出的设备，或者不与上述模型兼容，您可以尝试使用“通用”接口。此接口不提供发送到设备的任何类型的控制消息，并且不支持任何形式的设备流控。对您的设备的要求仅仅是它至少有一个批量输入端点或一个批量输出端点
要使通用驱动程序识别您的设备，请提供以下命令：

    echo <vid> <pid> > /sys/bus/usb-serial/drivers/generic/new_id

  其中 <vid> 和 <pid> 分别替换为您设备的供应商 ID 和产品 ID 的十六进制表示形式
如果将驱动程序编译为模块，您也可以在加载模块时提供一个 ID：

    insmod usbserial vendor=0x#### product=0x####

  此驱动程序已成功用于连接 NetChip USB 开发板，从而无需编写自定义驱动程序就可以开发 USB 固件
对于与此驱动程序相关的任何问题或遇到的问题，请联系 Greg Kroah-Hartman，邮箱地址：greg@kroah.com


联系方式
======

  如果有人在使用这些驱动程序或上述指定的任何产品时遇到问题，请联系上面列出的特定驱动程序作者，或者加入 Linux-USB 邮件列表（加入邮件列表的信息以及可搜索归档的链接位于 http://www.linux-usb.org/ ）

Greg Kroah-Hartman
greg@kroah.com
