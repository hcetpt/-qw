======================
Linux ACM 驱动程序 v0.16
======================

版权所有 (c) 1999 Vojtech Pavlik <vojtech@suse.cz>

由 SuSE 赞助

0. 免责声明
~~~~~~~~~~~~~
本程序为自由软件；您可以在GNU通用公共许可证（由自由软件基金会发布）的条款下重新分发或修改它；可以是第2版，也可以是（根据您的选择）任何后续版本。
本程序以期望它可能有用的方式分发，但没有任何保证；甚至不包括适销性或适合特定目的的默示保证。有关详细信息，请参阅GNU通用公共许可证。
您应该随同此程序收到一份GNU通用公共许可证的副本；如果没有，请写信给自由软件基金会，Inc.，59 Temple Place, Suite 330, 波士顿, MA 02111-1307 美国。

如果您需要联系我（作者），可以通过电子邮件 - 将邮件发送到<vojtech@suse.cz>，或者通过纸质邮件：Vojtech Pavlik, Ucitelska 1576, 布拉格 8, 182 00 捷克共和国

为了您的方便，GNU通用公共许可证第2版已包含在包中：请参阅文件COPYING
1. 使用方法
~~~~~~~~
drivers/usb/class/cdc-acm.c 驱动程序适用于符合通用串行总线通信设备类抽象控制模型（USB CDC ACM）规范的USB调制解调器和USB ISDN终端适配器。
许多调制解调器都适用，以下是我所知道的一些：

	- 3Com OfficeConnect 56k
	- 3Com Voice FaxModem Pro
	- 3Com Sportster
	- MultiTech MultiModem 56k
	- Zoom 2986L FaxModem
	- Compaq 56k FaxModem
	- ELSA Microlink 56k

我知道有一款ISDN TA与acm驱动程序兼容：

	- 3Com USR ISDN Pro TA

一些手机也通过USB连接。以下是我所知可正常工作的手机：

	- SonyEricsson K800i

不幸的是，许多调制解调器和大多数ISDN TA使用专有接口，因此无法与这些驱动程序一起工作。购买前请检查是否符合ACM规范
要使用调制解调器，您需要加载以下模块：

	usbcore.ko
	uhci-hcd.ko ohci-hcd.ko 或 ehci-hcd.ko
	cdc-acm.ko

之后，调制解调器应可访问。您应该能够使用minicom、ppp和mgetty与它们一起工作
2. 验证其是否正常工作
~~~~~~~~~~~~~~~~~~~~~~~~~~

第一步是检查/sys/kernel/debug/usb/devices，它应该看起来像这样：

  T:  Bus=01 Lev=00 Prnt=00 Port=00 Cnt=00 Dev#=  1 Spd=12  MxCh= 2
  B:  Alloc=  0/900 us ( 0%), #Int=  0, #Iso=  0
  D:  Ver= 1.00 Cls=09(hub  ) Sub=00 Prot=00 MxPS= 8 #Cfgs=  1
  P:  Vendor=0000 ProdID=0000 Rev= 0.00
  S:  Product=USB UHCI Root Hub
  S:  SerialNumber=6800
  C:* #Ifs= 1 Cfg#= 1 Atr=40 MxPwr=  0mA
  I:  If#= 0 Alt= 0 #EPs= 1 Cls=09(hub  ) Sub=00 Prot=00 Driver=hub
  E:  Ad=81(I) Atr=03(Int.) MxPS=   8 Ivl=255ms
  T:  Bus=01 Lev=01 Prnt=01 Port=01 Cnt=01 Dev#=  2 Spd=12  MxCh= 0
  D:  Ver= 1.00 Cls=02(comm.) Sub=00 Prot=00 MxPS= 8 #Cfgs=  2
  P:  Vendor=04c1 ProdID=008f Rev= 2.07
  S:  Manufacturer=3Com Inc
S:  Product=3Com U.S. Robotics Pro ISDN TA
  S:  SerialNumber=UFT53A49BVT7
  C:  #Ifs= 1 Cfg#= 1 Atr=60 MxPwr=  0mA
  I:  If#= 0 Alt= 0 #EPs= 3 Cls=ff(vend.) Sub=ff Prot=ff Driver=acm
  E:  Ad=85(I) Atr=02(Bulk) MxPS=  64 Ivl=  0ms
  E:  Ad=04(O) Atr=02(Bulk) MxPS=  64 Ivl=  0ms
  E:  Ad=81(I) Atr=03(Int.) MxPS=  16 Ivl=128ms
  C:* #Ifs= 2 Cfg#= 2 Atr=60 MxPwr=  0mA
  I:  If#= 0 Alt= 0 #EPs= 1 Cls=02(comm.) Sub=02 Prot=01 Driver=acm
  E:  Ad=81(I) Atr=03(Int.) MxPS=  16 Ivl=128ms
  I:  If#= 1 Alt= 0 #EPs= 2 Cls=0a(data ) Sub=00 Prot=00 Driver=acm
  E:  Ad=85(I) Atr=02(Bulk) MxPS=  64 Ivl=  0ms
  E:  Ad=04(O) Atr=02(Bulk) MxPS=  64 Ivl=  0ms

存在这三行（以及“comm”和“data”类）非常重要，这意味着它是ACM设备。Driver=acm表示使用了acm驱动程序。如果只看到Cls=ff(vend.)，那么您就无法使用了，因为这是一个具有供应商特定接口的设备：

  D:  Ver= 1.00 Cls=02(comm.) Sub=00 Prot=00 MxPS= 8 #Cfgs=  2
  I:  If#= 0 Alt= 0 #EPs= 1 Cls=02(comm.) Sub=02 Prot=01 Driver=acm
  I:  If#= 1 Alt= 0 #EPs= 2 Cls=0a(data ) Sub=00 Prot=00 Driver=acm

在系统日志中，您应该看到：

  usb.c: USB新设备连接，分配设备号2
  usb.c: kmalloc IF c7691fa0, numif 1
  usb.c: kmalloc IF c7b5f3e0, numif 2
  usb.c: 跳过4个类/供应商特定接口描述符
  usb.c: 新设备字符串：制造商=1, 产品=2, 序列号=3
  usb.c: USB设备号2默认语言ID 0x409
  制造商: 3Com Inc
  产品: 3Com U.S. Robotics Pro ISDN TA
  序列号: UFT53A49BVT7
  acm.c: 探测配置1
  acm.c: 探测配置2
  ttyACM0: USB ACM 设备
  acm.c: acm_control_msg: rq: 0x22 val: 0x0 len: 0x0 结果: 0
  acm.c: acm_control_msg: rq: 0x20 val: 0x0 len: 0x7 结果: 7
  usb.c: acm驱动程序声称接口c7b5f3e0
  usb.c: acm驱动程序声称接口c7b5f3f8
  usb.c: acm驱动程序声称接口c7691fa0

如果所有这些看起来都正常，启动minicom并将其设置为与ttyACM设备通信，并尝试输入'at'。如果它响应'OK'，那么一切都正常运行。
