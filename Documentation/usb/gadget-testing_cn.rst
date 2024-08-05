============= 
小工具测试
============= 

本文件总结了对由小工具提供的USB功能进行基本测试的相关信息。
.. contents

   1. ACM 功能
   2. ECM 功能
   3. ECM 子集功能
   4. EEM 功能
   5. FFS 功能
   6. HID 功能
   7. LOOPBACK 功能
   8. 大容量存储功能
   9. MIDI 功能
   10. NCM 功能
   11. OBEX 功能
   12. PHONET 功能
   13. RNDIS 功能
   14. 串行功能
   15. SOURCESINK 功能
   16. UAC1 功能（旧版实现）
   17. UAC2 功能
   18. UVC 功能
   19. 打印机功能
   20. UAC1 功能（新版API）
   21. MIDI2 功能


1. ACM 功能
=============

该功能由 usb_f_acm.ko 模块提供
特定于功能的configfs接口
------------------------------------

创建功能目录时要使用的名字是 "acm"
ACM功能在其功能目录中仅提供一个属性：

	port_num

该属性只读
系统中最多可以有4个ACM/通用串行/OBEX端口
测试ACM功能
------------------------

在主机上:

	cat > /dev/ttyACM<X>

在设备上:

	cat /dev/ttyGS<Y>

然后反过来

在设备上:

	cat > /dev/ttyGS<Y>

在主机上:

	cat /dev/ttyACM<X>

2. ECM 功能
=============

该功能由 usb_f_ecm.ko 模块提供
特定于功能的configfs接口
------------------------------------

创建功能目录时要使用的名字是 "ecm"
ECM功能在其功能目录中提供了以下属性：

	=============== ==================================================
	ifname		与此功能实例相关的网络设备接口名称
	qmult		高速和超速队列长度乘数
	host_addr	此USB以太网链路主机端的MAC地址
	dev_addr	此USB以太网链路设备端的MAC地址
	=============== ==================================================

创建完 functions/ecm.<instance name> 后，它们包含默认值：qmult为5，dev_addr和host_addr随机选择
ifname可以在功能未绑定时写入。写入必须是一个接口模式，如"usb%d"，这将导致网络核心选择下一个可用的usbX接口。默认情况下，它被设置为"usb%d"
测试ECM功能
------------------------

配置设备和主机的IP地址。然后：

在设备上:

	ping <主机的IP>

在主机上:

	ping <设备的IP>

3. ECM 子集功能
======================

该功能由 usb_f_ecm_subset.ko 模块提供
### 功能特定的configfs接口
------------------------------------

创建功能目录时所使用的功能名称是"geth"
ECM子集功能在其功能目录中提供了以下属性：

	=============== ==================================================
	ifname		与此功能实例相关的网络设备接口名称
	qmult		高速和超速下的队列长度乘数
	host_addr	此USB以太网链路主机端的MAC地址
	dev_addr	此USB以太网链路设备端的MAC地址
	=============== ==================================================

在创建了`functions/ecm.<实例名>`后，它们包含默认值：qmult为5，dev_addr和host_addr随机选择。
如果功能未绑定，则可以写入ifname。写入必须是一个接口模式，如"usb%d"，这将导致网络核心选择下一个可用的usbX接口。默认情况下，它设置为"usb%d"。
测试ECM子集功能
-------------------------------

配置设备和主机的IP地址。然后：

在设备上执行如下命令：

	ping <主机的IP>

在主机上执行如下命令：

	ping <设备的IP>

### 4. EEM功能
===============

该功能由`usb_f_eem.ko`模块提供。
功能特定的configfs接口
------------------------------------

创建功能目录时所使用的功能名称是"eem"
EEM功能在其功能目录中提供了以下属性：

	=============== ==================================================
	ifname		与此功能实例相关的网络设备接口名称
	qmult		高速和超速下的队列长度乘数
	host_addr	此USB以太网链路主机端的MAC地址
	dev_addr	此USB以太网链路设备端的MAC地址
	=============== ==================================================

在创建了`functions/eem.<实例名>`后，它们包含默认值：qmult为5，dev_addr和host_addr随机选择。
如果功能未绑定，则可以写入ifname。写入必须是一个接口模式，如"usb%d"，这将导致网络核心选择下一个可用的usbX接口。默认情况下，它设置为"usb%d"。
测试EEM功能
------------------------

配置设备和主机的IP地址。然后：

在设备上执行如下命令：

	ping <主机的IP>

在主机上执行如下命令：

	ping <设备的IP>

### 5. FFS功能
===============

该功能由`usb_f_fs.ko`模块提供。
功能特定的configfs接口
------------------------------------

创建功能目录时所使用的功能名称是"ffs"
功能目录有意为空且不可修改。
创建目录后，系统中会有一个新的FunctionFS实例（称为“设备”）。一旦“设备”可用，用户应遵循使用FunctionFS的标准程序（挂载它、运行实现特定功能的用户空间进程）。应该通过向`usb_gadget/<gadget>/UDC`写入合适的字符串来启用该设备。

FFS功能在其功能目录中仅提供一个属性：

    ready

该属性是只读的，并且指示功能是否已准备好（1）被使用，例如如果用户空间已经向ep0写入描述符和字符串，则可以启用该设备。

### 测试FFS功能

在设备上：启动功能的用户空间守护进程，启用设备

在主机上：使用设备提供的USB功能

### 6. HID功能

该功能由`usb_f_hid.ko`模块提供。
#### 功能特定的configfs接口

创建功能目录时要使用的名字是“hid”。

HID功能在其功能目录中提供以下属性：

    =============== ===================================================
    protocol       要使用的HID协议
    report_desc    在HID报告中使用的数据，除了通过`/dev/hidg<X>`传递的数据
    report_length  HID报告长度
    subclass       要使用的HID子类
    =============== ===================================================

对于键盘而言，协议和子类都是1，report_length为8，而report_desc如下所示：

  $ hd my_report_desc
  00000000  05 01 09 06 a1 01 05 07  19 e0 29 e7 15 00 25 01  |..........)...%.|
  00000010  75 01 95 08 81 02 95 01  75 08 81 03 95 05 75 01  |u.......u.....u.|
  00000020  05 08 19 01 29 05 91 02  95 01 75 03 91 03 95 06  |....).....u.....|
  00000030  75 08 15 00 25 65 05 07  19 00 29 65 81 00 c0     |u...%e....)e...|
  0000003f

这样的一串字节可以通过echo命令存储到属性中：

  $ echo -ne \\x05\\x01\\x09\\x06\\xa1....

#### 测试HID功能

设备：

- 创建设备
- 将设备连接到主机，最好是与控制设备不同的主机
- 运行一个向`/dev/hidg<N>`写入数据的程序，例如Documentation/usb/gadget_hid.rst中找到的用户空间程序：

  $ ./hid_gadget_test /dev/hidg0 keyboard

主机：

- 观察来自设备的按键输入

### 7. LOOPBACK功能

该功能由`usb_f_ss_lb.ko`模块提供。
#### 功能特定的configfs接口

创建功能目录时要使用的名字是“Loopback”。

LOOPBACK功能在其功能目录中提供以下属性：

    =============== =======================
    qlen           循环队列的深度
    bulk_buflen    缓冲区长度
    =============== =======================

#### 测试LOOPBACK功能

设备：运行设备

主机：test-usb（tools/usb/testusb.c）

### 8. 大容量存储功能

该功能由`usb_f_mass_storage.ko`模块提供。
#### 功能特定的configfs接口

创建功能目录时要使用的名字是“mass_storage”。
MAS_STORAGE 功能在其目录中提供了以下属性：
文件：

	=============== ==============================================
	stall		设置以允许功能暂停批量端点
在已知无法正确工作的某些 USB 设备上禁用
			您应该将其设置为 true
num_buffers	管线缓冲区的数量。有效数字
			为 2 到 4。仅在
			设置了 CONFIG_USB_GADGET_DEBUG_FILES 的情况下可用
=============== ==============================================

以及一个默认的 lun.0 目录，对应于 SCSI LUN #0。
可以通过 `mkdir` 命令添加一个新的 LUN ：

	$ mkdir functions/mass_storage.0/partition.5

LUN 编号不需要连续，但 LUN #0 是默认创建的。最多可以指定 8 个 LUN，并且它们都必须按照 `<名称>.<编号>` 的方案命名。这些编号可以是 0 到 8。可能一个很好的命名约定是将 LUN 命名为 "lun.<编号>"，尽管这不是强制性的。
在每个 LUN 目录中，有以下属性文件：

	=============== ==============================================
	file		LUN 的支持文件路径
如果 LUN 没有标记为可移动，则必须提供
ro		标志指定对 LUN 的访问应为
			只读。如果启用了 CD-ROM 模拟，或者当尝试以
			读写模式打开 "filename" 失败时，这将是隐含的
removable	标志指定 LUN 应被标识为
			可移动的
=============== ==============================================
翻译如下：

`cdrom`       标志，指定逻辑单元号（LUN）应报告为
              光盘驱动器（CD-ROM）

`nofua`       标志，指定SCSI WRITE(10,12)中的FUA标志

`forced_eject`此只写文件仅在功能启用时有用。它会强制使支持文件从LUN中脱离，
              不管主机是否允许这样做。
              写入任何非零字节数都将导致弹出。

===============
=============================================

测试大容量存储功能
-------------------

设备：连接设备并启用它
主机：使用`dmesg`查看USB驱动器出现（如果系统配置为自动挂载）

9. MIDI 功能
=============

该功能由`usb_f_midi.ko`模块提供
特定于功能的configfs接口
------------------------------------

创建功能目录时要使用的功能名称是“midi”。
MIDI功能在其功能目录中提供了以下属性：

	===============
	===================================
	`buflen`		MIDI缓冲区长度
	`id`			USB MIDI适配器的ID字符串
	`in_ports`		MIDI输入端口数量
	`index`		USB MIDI适配器的索引值
	`out_ports`		MIDI输出端口数量
	`qlen`		USB读取请求队列长度
	===============
	===================================

测试MIDI功能
-------------------------

有两种情况：从设备到主机播放MIDI文件以及从主机到设备播放MIDI文件。
1) 从设备到主机播放MIDI文件：

主机：

  $ `arecordmidi -l`
   端口    客户端名称                      端口名称
   14:0    MIDI通道                     MIDI通道端口-0
   24:0    MIDI设备                      MIDI设备 MIDI 1
  $ `arecordmidi -p 24:0 from_gadget.mid`

设备：

  $ `aplaymidi -l`
   端口    客户端名称                      端口名称
   20:0    f_midi                           f_midi

  $ `aplaymidi -p 20:0 to_host.mid`

2) 从主机到设备播放MIDI文件

设备：

  $ `arecordmidi -l`
   端口    客户端名称                      端口名称
   20:0    f_midi                           f_midi

  $ `arecordmidi -p 20:0 from_host.mid`

主机：

  $ `aplaymidi -l`
   端口    客户端名称                      端口名称
   14:0    MIDI通道                     MIDI通道端口-0
   24:0    MIDI设备                      MIDI设备 MIDI 1

  $ `aplaymidi -p 24:0 to_gadget.mid`

`from_gadget.mid`应该与`to_host.mid`声音相同。
`from_host.mid`应该与`to_gadget.mid`声音相同。
可以使用例如安装了timidity的设备将MIDI文件播放到扬声器/耳机：

  $ `aplaymidi -l`
   端口    客户端名称                      端口名称
   14:0    MIDI通道                     MIDI通道端口-0
   24:0    MIDI设备                      MIDI设备 MIDI 1
  128:0    TiMidity                         TiMidity端口 0
  128:1    TiMidity                         TiMidity端口 1
  128:2    TiMidity                         TiMidity端口 2
  128:3    TiMidity                         TiMidity端口 3

  $ `aplaymidi -p 128:0 file.mid`

可以使用aconnect工具逻辑地连接MIDI端口，例如：

  $ `aconnect 24:0 128:0` # 在主机上尝试

在设备的MIDI端口与timidity的MIDI端口连接后，无论是在设备端通过`aplaymidi -l`播放的内容都可在主机的扬声器/耳机中听到。
10. NCM 功能
==============

该功能由`usb_f_ncm.ko`模块提供
### 功能特定的configfs接口
------------------------------------

创建功能目录时要使用的功能名称是"ncm"。
NCM功能在其功能目录中提供了以下属性：

	======================= ==================================================
	ifname			与此功能实例相关的网络设备接口名称
	qmult			高速和超速的队列长度乘数
	host_addr		此USB以太网链接主机端的MAC地址
	dev_addr		此USB以太网链接设备端的MAC地址
	max_segment_size	P2P连接所需的段大小。这将设置MTU为14字节
	======================= ==================================================

创建`functions/ncm.<instance name>`后，它们包含默认值：qmult为5，dev_addr和host_addr随机选择。
如果功能未绑定，则可以写入ifname。写入必须是一个接口模式，例如"usb%d"，这将导致网络核心选择下一个可用的usbX接口。默认情况下，它被设置为"usb%d"。
测试NCM功能
------------------------

配置设备和主机的IP地址。然后：

在设备上执行如下命令：

	ping <主机的IP>

在主机上执行如下命令：

	ping <设备的IP>

### 11. OBEX功能
=================

该功能由usb_f_obex.ko模块提供。
功能特定的configfs接口
------------------------------------

创建功能目录时要使用的功能名称是"obex"。
OBEX功能在其功能目录中仅提供一个属性：

	port_num

该属性为只读。
系统中最多可有4个ACM/通用串行/OBEX端口。
测试OBEX功能
-------------------------

在设备上执行如下命令：

	seriald -f /dev/ttyGS<Y> -s 1024

在主机上执行如下命令：

	serialc -v <供应商ID> -p <产品ID> -i<接口编号> -a1 -s1024 \
                -t<输出端点地址> -r<输入端点地址>

其中seriald和serialc是Felipe提供的工具，可以在以下位置找到：

	https://github.com/felipebalbi/usb-tools.git master

### 12. PHONET功能
===================

该功能由usb_f_phonet.ko模块提供。
功能特定的configfs接口
------------------------------------

创建功能目录时要使用的功能名称是"phonet"。
PHONET功能在其功能目录中仅提供一个属性：

	=============== ==================================================
	ifname		与此功能实例相关的网络设备接口名称
	=============== ==================================================

测试PHONET功能
---------------------------

没有特定硬件无法测试SOCK_STREAM协议，因此仅测试了SOCK_DGRAM。为了使后者工作，在过去我不得不应用这里提到的补丁：

http://www.spinics.net/lists/linux-usb/msg85689.html

需要这些工具：

git://git.gitorious.org/meego-cellular/phonet-utils.git

在主机上执行如下命令：

	$ ./phonet -a 0x10 -i usbpn0
	$ ./pnroute add 0x6c usbpn0
	$ ./pnroute add 0x10 usbpn0
	$ ifconfig usbpn0 up

在设备上执行如下命令：

	$ ./phonet -a 0x6c -i upnlink0
	$ ./pnroute add 0x10 upnlink0
	$ ifconfig upnlink0 up

然后可以使用测试程序：

	http://www.spinics.net/lists/linux-usb/msg85690.html

在设备上执行如下命令：

	$ ./pnxmit -a 0x6c -r

在主机上执行如下命令：

	$ ./pnxmit -a 0x10 -s 0x6c

结果应该有一些数据从主机发送到设备。
然后反过来：

在主机上：

    $ ./pnxmit -a 0x10 -r

在设备上：

    $ ./pnxmit -a 0x6c -s 0x10

13. RNDIS 功能
=============

该功能由 usb_f_rndis.ko 模块提供。
特定于功能的 configfs 接口
---------------------------------

创建功能目录时要使用的功能名称是 "rndis"。
RNDIS 功能在其功能目录中提供了以下属性：

    ================ ==================================================
    ifname          与该功能实例关联的网络设备接口名称
                    qmult        高速和超速下的队列长度乘数
    host_addr       此 USB 以太网链路中主机端的 MAC 地址
    dev_addr        此 USB 以太网链路中设备端的 MAC 地址
    ================ ==================================================

创建完 functions/rndis.<instance name> 后，它们包含默认值：qmult 是 5，dev_addr 和 host_addr 是随机选择的。
ifname 可以写入，如果功能未绑定。写入必须是一个接口模式，例如 "usb%d"，这将导致 net 核心选择下一个空闲的 usbX 接口。默认情况下，它被设置为 "usb%d"。
测试 RNDIS 功能
------------------------

配置设备和主机的 IP 地址。然后：

在设备上：

    ping <主机的 IP>

在主机上：

    ping <设备的 IP>

14. 串行 (SERIAL) 功能
====================

该功能由 usb_f_gser.ko 模块提供。
特定于功能的 configfs 接口
---------------------------------

创建功能目录时要使用的功能名称是 "gser"。
SERIAL 功能在其功能目录中仅提供一个属性：

    port_num

此属性只读。
系统中最多可以有 4 个 ACM/通用串行/OBEX 端口。
测试 SERIAL 功能
----------------------

在主机上：

    insmod usbserial
    echo VID PID >/sys/bus/usb-serial/drivers/generic/new_id

在主机上：

    cat > /dev/ttyUSB<X>

在目标上：

    cat /dev/ttyGS<Y>

然后反过来

在目标上：

    cat > /dev/ttyGS<Y>

在主机上：

    cat /dev/ttyUSB<X>

15. SOURCESINK 功能
====================

该功能由 usb_f_ss_lb.ko 模块提供。
特定于功能的 configfs 接口
---------------------------------

创建功能目录时要使用的功能名称是 "SourceSink"
SOURCESINK功能在其功能目录中提供了以下属性：

	=============== ==================================
	pattern		0（全零），1（mod63），2（无）
	isoc_interval	1..16
	isoc_maxpacket	0 - 1023（全速），0 - 1024（高速/超速）
	isoc_mult	0..2（仅高速/超速）
	isoc_maxburst	0..15（仅超速）
	bulk_buflen	缓冲区长度
	bulk_qlen	批量队列深度
	iso_qlen	等时队列深度
	=============== ==================================

测试SOURCESINK功能
-------------------------------

设备: 运行gadget

主机: test-usb（tools/usb/testusb.c）

16. UAC1功能（传统实现）
=========================================

此功能由usb_f_uac1_legacy.ko模块提供
特定于功能的configfs接口
------------------------------------

创建功能目录时使用的功能名称为“uac1_legacy”
uac1功能在其功能目录中提供了以下属性：

	=============== ====================================
	audio_buf_size	音频缓冲区大小
	fn_cap		捕获pcm设备文件名
	fn_cntl		控制设备文件名
	fn_play		播放pcm设备文件名
	req_buf_size	ISO OUT端点请求缓冲区大小
	req_count	ISO OUT端点请求计数
	=============== ====================================

这些属性具有合理的默认值
测试UAC1功能
-------------------------

设备: 运行gadget

主机::

	aplay -l # 应该列出我们的USB音频gadget

17. UAC2功能
=================

此功能由usb_f_uac2.ko模块提供
特定于功能的configfs接口
------------------------------------

创建功能目录时使用的功能名称为“uac2”
uac2功能在其功能目录中提供了以下属性：

	================ ====================================================
	c_chmask         捕获通道掩码
	c_srate          捕获采样率列表（以逗号分隔）
	c_ssize          捕获样本大小（字节）
	c_sync           捕获同步类型（异步/自适应）
	c_mute_present   捕获静音控制启用
	c_volume_present 捕获音量控制启用
	c_volume_min     捕获音量控制最小值（以1/256 dB）
	c_volume_max     捕获音量控制最大值（以1/256 dB）
	c_volume_res     捕获音量控制分辨率（以1/256 dB）
	c_hs_bint        捕获HS/SS的bInterval（1-4：固定，0：自动）
	fb_max           异步模式下的最大额外带宽
	p_chmask         播放通道掩码
	p_srate          播放采样率列表（以逗号分隔）
	p_ssize          播放样本大小（字节）
	p_mute_present   播放静音控制启用
	p_volume_present 播放音量控制启用
	p_volume_min     播放音量控制最小值（以1/256 dB）
	p_volume_max     播放音量控制最大值（以1/256 dB）
	p_volume_res     播放音量控制分辨率（以1/256 dB）
	p_hs_bint        播放HS/SS的bInterval（1-4：固定，0：自动）
	req_number       为捕获和播放预分配的请求数量
	function_name    接口名称
	c_terminal_type  捕获终端类型的代码
	p_terminal_type  播放终端类型的代码
	================ ====================================================

这些属性具有合理的默认值
测试UAC2功能
-------------------------

设备: 运行gadget
主机: aplay -l # 应该列出我们的USB音频gadget

此功能不需要真实的硬件支持，它只是将音频数据流发送到/从主机。为了在设备侧实际听到声音，必须在设备侧使用类似的命令::

	$ arecord -f dat -t wav -D hw:2,0 | aplay -D hw:0,0 &

例如::

	$ arecord -f dat -t wav -D hw:CARD=UAC2Gadget,DEV=0 | \
	  aplay -D default:CARD=OdroidU3

18. UVC功能
================

此功能由usb_f_uvc.ko模块提供
特定于功能的configfs接口
------------------------------------

创建功能目录时使用功能名称为“uvc”
uvc功能在其功能目录中提供了以下属性：

	=================== ================================================
	streaming_interval  数据传输轮询端点的间隔
	streaming_maxburst  超速伴侣描述符中的bMaxBurst
	streaming_maxpacket 当选择此配置时，此端点能够发送或接收的最大数据包大小
	function_name       接口名称
	=================== ================================================

还有"control"和"streaming"子目录，每个子目录包含多个子目录。提供了一些合理的默认值，但是用户必须提供以下内容：

	================== ====================================================
	control header     在control/header中创建，从control/class/fs和/或control/class/ss链接
	streaming header   在streaming/header中创建，从streaming/class/fs和/或streaming/class/hs和/或streaming/class/ss链接
	format description 在streaming/mjpeg和/或streaming/uncompressed中创建
	frame description  在streaming/mjpeg/<format>和/或streaming/uncompressed/<format>中创建
	================== ====================================================

每个帧描述包含帧间隔规范，每个此类规范由多行组成，每行有一个间隔值。上述规则最好通过一个示例来说明::

  # mkdir functions/uvc.usb0/control/header/h
  # cd functions/uvc.usb0/control/
  # ln -s header/h class/fs
  # ln -s header/h class/ss
  # mkdir -p functions/uvc.usb0/streaming/uncompressed/u/360p
  # cat <<EOF > functions/uvc.usb0/streaming/uncompressed/u/360p/dwFrameInterval
  666666
  1000000
  5000000
  EOF
  # cd $GADGET_CONFIGFS_ROOT
  # mkdir functions/uvc.usb0/streaming/header/h
  # cd functions/uvc.usb0/streaming/header/h
  # ln -s ../../uncompressed/u
  # cd ../../class/fs
  # ln -s ../../header/h
  # cd ../../class/hs
  # ln -s ../../header/h
  # cd ../../class/ss
  # ln -s ../../header/h


测试UVC功能
------------------------

设备: 运行gadget，加载vivid模块::

  # uvc-gadget -u /dev/video<uvc视频节点#> -v /dev/video<vivid视频节点#>

其中uvc-gadget是这个程序：
	http://git.ideasonboard.org/uvc-gadget.git

并应用以下补丁：

	http://www.spinics.net/lists/linux-usb/msg99220.html

主机::

	luvcview -f yuv

19. PRINTER功能
====================

此功能由usb_f_printer.ko模块提供
特定于功能的configfs接口
------------------------------------

创建功能目录时使用功能名称为“printer”
打印机功能在其功能目录中提供了以下属性：

	==========	===========================================
	pnp_string	要以PnP字符串形式传递给主机的数据
	q_len		每个端点的请求数量
	==========	===========================================

测试PRINTER（打印机）功能
----------------------------

最基础的测试方法如下：

设备：运行gadget（小工具）：

	# ls -l /devices/virtual/usb_printer_gadget/

应当会显示g_printer<number>
如果udev处于活动状态，那么/dev/g_printer<number>应当自动出现
主机：

如果udev处于活动状态，例如/dev/usb/lp0应当会出现
从主机到设备的传输：

设备：

	# cat /dev/g_printer<number>

主机：

	# cat > /dev/usb/lp0

从设备到主机的传输：

	# cat > /dev/g_printer<number>

主机：

	# cat /dev/usb/lp0

更高级的测试可以通过Documentation/usb/gadget_printer.rst中描述的prn_example来进行。

20. UAC1功能（虚拟ALSA卡，使用u_audio API）
========================================================

此功能由usb_f_uac1.ko模块提供。
它将创建一个虚拟ALSA卡，并且音频流简单地从该卡中接收和发送。
特定于功能的configfs接口
------------------------------------

创建功能目录时使用的功能名称为"uac1"。
uac1功能在其功能目录中提供了以下属性：

	================ ====================================================
	c_chmask         捕获通道掩码
	c_srate          捕获采样率列表（逗号分隔）
	c_ssize          捕获样本大小（字节）
	c_mute_present   捕获静音控制启用
	c_volume_present 捕获音量控制启用
	c_volume_min     捕获音量控制最小值（1/256 dB）
	c_volume_max     捕获音量控制最大值（1/256 dB）
	c_volume_res     捕获音量控制分辨率（1/256 dB）
	p_chmask         播放通道掩码
	p_srate          播放采样率列表（逗号分隔）
	p_ssize          播放样本大小（字节）
	p_mute_present   播放静音控制启用
	p_volume_present 播放音量控制启用
	p_volume_min     播放音量控制最小值（1/256 dB）
	p_volume_max     播放音量控制最大值（1/256 dB）
	p_volume_res     播放音量控制分辨率（1/256 dB）
	req_number       为捕获和播放预分配的请求数量
	function_name    接口名称
	================ ====================================================

这些属性具有合理的默认值。
测试UAC1功能
-------------------------

设备：运行gadget（小工具）
主机：aplay -l # 应当列出我们的USB音频小工具

此功能不需要真实的硬件支持，它只是向/从主机发送/接收音频数据流。为了在设备侧实际听到声音，必须在设备侧使用类似的命令：

	$ arecord -f dat -t wav -D hw:2,0 | aplay -D hw:0,0 &

例如：

	$ arecord -f dat -t wav -D hw:CARD=UAC1Gadget,DEV=0 | \
	  aplay -D default:CARD=OdroidU3


21. MIDI2功能
==================

此功能由usb_f_midi2.ko模块提供。
它将创建包含UMP rawmidi设备的虚拟ALSA卡，其中UMP包被循环回送。此外，还会创建一个legacy rawmidi设备。UMP rawmidi与ALSA序列器客户端绑定。
特定功能的configfs接口
------------------------------------

创建功能目录时使用的功能名称是"midi2"
midi2功能在其功能目录中提供了以下属性作为卡片顶层信息：

	=============	=================================================
	process_ump	处理UMP流消息的布尔标志（0 或 1）
	static_block	静态块的布尔标志（0 或 1）
	iface_name	可选的接口名称字符串
	=============	=================================================

该目录包含一个名为"ep.0"的子目录，它提供了UMP端点（即一对USB MIDI端点）的属性：

	=============	=================================================
	protocol_caps	MIDI协议能力；1：MIDI 1.0，2：MIDI 2.0，或 3：两种协议
	protocol	默认MIDI协议（1 或 2）
	ep_name		UMP端点名称字符串
	product_id	产品ID字符串
	manufacturer	制造商ID编号（24位）
	family		设备家族ID编号（16位）
	model		设备型号ID编号（16位）
	sw_revision	软件版本号（32位）
	=============	=================================================

每个端点子目录都包含一个名为"block.0"的子目录，表示第0块的信息的功能块。
其属性为：

	=================	===============================================
	name			功能块名称字符串
	direction		此FB的方向
				1：输入，2：输出，或 3：双向
	first_group		第一个UMP组编号（0-15）
	num_groups		此FB中的组数（1-16）
	midi1_first_group	用于MIDI 1.0的第一个UMP组编号（0-15）
	midi1_num_groups	用于MIDI 1.0的组数（0-16）
	ui_hint			此FB的UI提示
				0：未知，1：接收器，2：发送器，3：两者
	midi_ci_verison		支持的MIDI-CI版本号（8位）
	is_midi1		旧版MIDI 1.0设备（0-2）
				0：MIDI 2.0设备，
				1：无限制的MIDI 1.0，或
				2：低速MIDI 1.0
	sysex8_streams		SysEx8流的最大数量（8位）
	active			FB活动的布尔标志（0 或 1）
	=================	===============================================

如果需要多个功能块，可以通过创建带有相应功能块编号（1、2、...）的"block.<num>"子目录来添加更多功能块。这些FB子目录也可以动态移除。请注意，功能块编号必须连续。
同样地，如果需要多个UMP端点，可以通过创建"ep.<num>"子目录来添加更多端点。编号也必须连续。
为了模拟不支持UMP v1.1的老式MIDI 2.0设备，可以将0传递给`process_ump`标志。这样，所有UMP v1.1请求都将被忽略。
测试MIDI2功能
--------------------------

在设备上：运行gadget，并执行以下命令：

  $ cat /proc/asound/cards

会显示包含MIDI2设备的新声卡
另一方面，在主机上执行：

  $ cat /proc/asound/cards

会根据USB音频驱动程序配置显示包含MIDI1或MIDI2设备的新声卡。
在双方，当主机启用了ALSA音序器时，你可以找到UMP MIDI客户端，例如"MIDI 2.0 Gadget"。
由于驱动程序只是简单地回环数据，因此无需实际设备来进行测试。
要测试从gadget到主机的MIDI输入（例如，模拟MIDI键盘），可以发送如下MIDI流：
在设备端上:

  $ aconnect -o
  ...
客户端 20: 'MIDI 2.0 设备' [类型=内核,card=1]
      0 'MIDI 2.0        '
      1 '组 1 (MIDI 2.0 设备 I/O)'
  $ aplaymidi -p 20:1 to_host.mid

在主机上:

  $ aconnect -i
  ...
客户端 24: 'MIDI 2.0 设备' [类型=内核,card=2]
      0 'MIDI 2.0        '
      1 '组 1 (MIDI 2.0 设备 I/O)'
  $ arecordmidi -p 24:1 from_gadget.mid

如果你有一个支持UMP的应用程序，你也可以使用UMP端口来发送/接收原始的UMP数据包。例如，具有UMP支持的aseqdump程序可以从UMP端口接收数据。在主机上：

  $ aseqdump -u 2 -p 24:1
  等待数据。按Ctrl+C结束
源  组    事件                      通道  数据
   24:1   组  0, 音色改变              0, 音色 0, 银行选择 0:0
   24:1   组  0, 通道压力               0, 值 0x80000000

为了测试从设备到主机的MIDI输出（例如，模拟MIDI合成器），只需反过来操作即可。
在设备端上:

  $ arecordmidi -p 20:1 from_host.mid

在主机上:

  $ aplaymidi -p 24:1 to_gadget.mid

主机上的备用设置0上的MIDI 1.0访问是被支持的，并且它在设备上被转换为UMP数据包。它仅绑定到功能块0。
当前的操作模式可以在ALSA控制元素 "操作模式"（SND_CTL_IFACE_RAWMIDI）中观察到。例如：

  $ amixer -c1 contents
  numid=1,iface=RAWMIDI,name='操作模式'
    ; 类型=INTEGER,访问=r--v----,值=1,最小=0,最大=2,步长=0
    : 值=2

其中 0 = 未使用, 1 = MIDI 1.0 (备用设置 0), 2 = MIDI 2.0 (备用设置 1)
上面的例子显示它正在运行在2，即MIDI 2.0模式下。
