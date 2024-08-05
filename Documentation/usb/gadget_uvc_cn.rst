=======================
Linux UVC Gadget 驱动
=======================

概述
--------
UVC Gadget 驱动是一个用于USB连接的*设备*端硬件的驱动程序。它旨在运行于具有USB设备端硬件（如带有OTG端口的板卡）的Linux系统上。
在设备系统上，一旦驱动绑定后，它将表现为具有输出能力的V4L2设备。
在主机端（通过USB线缆连接后），运行UVC Gadget驱动并由相应的用户空间程序控制的设备应表现为符合UVC规范的摄像头，并能与任何设计用于处理此类摄像头的程序正常工作。运行在设备系统上的用户空间程序可以从多种来源排队图像缓冲区，以通过USB连接进行传输。通常这意味着从摄像头传感器外围设备转发缓冲区，但缓冲区的来源完全取决于用户空间配套程序。
配置设备内核
-----------------
为了支持UVC Gadget，需要选择Kconfig选项USB_CONFIGFS、USB_LIBCOMPOSITE、USB_CONFIGFS_F_UVC和USB_F_UVC。
通过configfs配置Gadget
---------------------------------------
UVC Gadget期望通过configfs使用UVC功能进行配置，这提供了相当大的灵活性，因为UVC设备的许多设置都可以通过这种方式控制。
并非所有可用属性都在这里描述。对于完整的枚举，请参阅Documentation/ABI/testing/configfs-usb-gadget-uvc。

假设条件
~~~~~~~~~~~
本节假定您已在`/sys/kernel/config`挂载了configfs，并创建了一个gadget作为`/sys/kernel/config/usb_gadget/g1`。
UVC 功能
~~~~~~~~~~~~~~~~

第一步是创建UVC功能：

.. code-block:: bash

	# 以下变量将在文档其余部分中被假定
	CONFIGFS="/sys/kernel/config"
	GADGET="$CONFIGFS/usb_gadget/g1"
	FUNCTION="$GADGET/functions/uvc.0"

	mkdir -p $FUNCTION

格式和帧
~~~~~~~~~~~~~~~~~~

您必须通过告诉Gadget支持哪些格式以及每种格式支持的帧大小和帧间隔来配置它。在当前实现中，没有方法让Gadget拒绝主机设置的格式，因此重要的是要准确完成此步骤，确保主机永远不会要求无法提供的格式。
格式在streaming/uncompressed和streaming/mjpeg configfs组下创建，帧大小在格式下创建，结构如下：

::

	uvc.0 +
	      |
	      + streaming +
			  |
			  + mjpeg +
			  |       |
			  |       + mjpeg +
			  |	       |
			  |	       + 720p
			  |	       |
			  |	       + 1080p
			  |
			  + uncompressed +
					 |
					 + yuyv +
						|
						+ 720p
						|
						+ 1080p

每个帧可以配置宽度、高度以及存储单个帧所需的最缓冲区大小，最后是该格式和帧大小支持的帧间隔。宽度和高度以像素为单位，帧间隔以100纳秒为单位。例如，要创建上述结构，并为每个帧大小设置2、15和100 fps的帧间隔，可以这样做：

.. code-block:: bash

	create_frame() {
		# 示例用法：
		# create_frame <width> <height> <group> <format name>

		WIDTH=$1
		HEIGHT=$2
		FORMAT=$3
		NAME=$4

		wdir=$FUNCTION/streaming/$FORMAT/$NAME/${HEIGHT}p

		mkdir -p $wdir
		echo $WIDTH > $wdir/wWidth
		echo $HEIGHT > $wdir/wHeight
		echo $(( $WIDTH * $HEIGHT * 2 )) > $wdir/dwMaxVideoFrameBufferSize
		cat <<EOF > $wdir/dwFrameInterval
	666666
	100000
	5000000
	EOF
	}

	create_frame 1280 720 mjpeg mjpeg
	create_frame 1920 1080 mjpeg mjpeg
	create_frame 1280 720 uncompressed yuyv
	create_frame 1920 1080 uncompressed yuyv

目前唯一支持的无压缩格式是YUYV，其详细信息见Documentation/userspace-api/media/v4l/pixfmt-packed-yuv.rst
颜色匹配描述符
~~~~~~~~~~~~~~~~~~~~~~~~~~
可以为创建的每个格式指定一些色彩计量信息
此步骤为可选项，如果省略此步骤，默认信息将被包含；这些默认值遵循UVC规范中“颜色匹配描述符”部分所定义的值。
为了创建一个颜色匹配描述符，需要创建一个configfs项，并将其三个属性设置为你期望的设置，然后从你希望与之关联的格式链接到它：

.. code-block:: bash

	# 创建一个新的颜色匹配描述符

	mkdir $FUNCTION/streaming/color_matching/yuyv
	pushd $FUNCTION/streaming/color_matching/yuyv

	echo 1 > bColorPrimaries
	echo 1 > bTransferCharacteristics
	echo 4 > bMatrixCoefficients

	popd

	# 从格式的配置项创建指向颜色匹配描述符的符号链接
	ln -s $FUNCTION/streaming/color_matching/yuyv $FUNCTION/streaming/uncompressed/yuyv

关于有效值的详细信息，请参阅UVC规范。请注意，默认的颜色匹配描述符存在，并被任何没有链接到不同颜色匹配描述符的格式使用。可以更改默认描述符的属性设置，因此请记住，如果你这样做，则会改变未链接到其他描述符的任何格式的默认值。

### 头部链接

UVC规范要求在格式和帧描述符之前提供头部，以详细说明诸如后面跟随的不同格式描述符的数量和累积大小等信息。这种操作和其他类似的操作可以通过在表示头部的configfs项与表示其他描述符的config项之间建立链接来实现，如下所示：

.. code-block:: bash

	mkdir $FUNCTION/streaming/header/h

	# 此部分链接格式描述符及其相关帧到头部
	cd $FUNCTION/streaming/header/h
	ln -s ../../uncompressed/yuyv
	ln -s ../../mjpeg/mjpeg

	# 此部分确保每个速度的描述符集都会传输相应的头部。如果不支持某个特定的速度，可以在这里跳过
	cd ../../class/fs
	ln -s ../../header/h
	cd ../../class/hs
	ln -s ../../header/h
	cd ../../class/ss
	ln -s ../../header/h
	cd ../../../control
	mkdir header/h
	ln -s header/h class/fs
	ln -s header/h class/ss

### 扩展单元支持

UVC扩展单元（XU）基本上提供了独立的单元，控制设置和获取请求可以针对该单元进行。这些控制请求的意义完全取决于具体实现，但可用于控制UVC规范之外的设置（例如启用或禁用视频效果）。一个XU可以插入到UVC单元链中或保持自由悬挂状态。

配置扩展单元涉及在适当的目录中创建条目并适当地设置其属性，如下所示：

.. code-block:: bash

	mkdir $FUNCTION/control/extensions/xu.0
	pushd $FUNCTION/control/extensions/xu.0

	# 设置处理单元的bUnitID作为此扩展单元的源
	echo 2 > baSourceID

	# 将此XU设置为默认输出终端的源。这将XU插入PU和OT之间的UVC链中，使得最终链为IT > PU > XU.0 > OT
	cat bUnitID > ../../terminal/output/default/baSourceID

	# 标记一些控制可用。bmControl字段是一个位图，其中每一位表示特定控制的可用性。例如，要标记第0、2和3个控制可用：
	echo 0x0d > bmControls

	# 设置GUID；这是一个标识XU的供应商特定代码
	echo -e -n "\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10" > guidExtensionCode

	popd

bmControls属性和baSourceID属性是多值属性。这意味着你可以写入多个以换行符分隔的值。例如，要标记第1、2、9和10个控制可用，你需要向bmControls写入两个值，如下所示：

.. code-block:: bash

	cat << EOF > bmControls
	0x03
	0x03
	EOF

baSourceID属性的多值特性暗示了XU可以有多个输入，尽管需要注意的是，目前这并没有显著的影响。

bControlSize属性反映了bmControls属性的大小，同样地，bNrInPins反映了baSourceID属性的大小。当你设置bmControls和baSourceID时，这两个属性都会自动增加或减少。也可以手动增加或减少bControlSize，这会产生截断条目至新大小的效果，或者用0x00填充条目，例如：

::

	$ cat bmControls
	0x03
	0x05

	$ cat bControlSize
	2

	$ echo 1 > bControlSize
	$ cat bmControls
	0x03

	$ echo 2 > bControlSize
	$ cat bmControls
	0x03
	0x00

bNrInPins和baSourceID的功能与此相同。

### 配置摄像头终端和处理单元的支持控制

UVC链中的摄像头终端和处理单元也有bmControls属性，其功能类似于扩展单元中的同一字段。
与XU不同的是，这些单元中位标志的含义在UVC规范中有定义；你应该查阅“摄像头终端描述符”和“处理单元描述符”部分以了解标志的枚举。
以下是提供的英文内容翻译成中文：

```bash
# 设置处理单元的bmControls，将亮度、对比度和色调标记为可用控制项：
echo 0x05 > $FUNCTION/control/processing/default/bmControls

# 设置摄像头终端的bmControls，将绝对对焦和相对对焦标记为可用控制项：
echo 0x60 > $FUNCTION/control/terminal/camera/default/bmControls

# 如果不设置这些字段，则默认情况下摄像头终端的自动曝光模式控制以及处理单元的亮度控制将被标记为可用；
# 如果它们不受支持，应该将字段设置为0x00。
# 注意摄像头终端或处理单元的bmControls字段的大小由UVC规范固定，
# 因此bControlSize属性在这里是只读的。

自定义字符串支持
~~~~~~~~~~~~~~~~~~~~~~

为USB设备的各个部分提供文本描述的字符串描述符可以在USB配置文件系统中的常规位置定义，并且可以通过UVC功能根目录或从扩展单元目录链接到它们以将这些字符串分配为描述符：

```bash
# 在us-EN中创建一个字符串描述符，并从功能根目录链接到它。这里链接的名称很重要，
# 因为它声明了这个描述符是为接口关联描述符准备的；在功能根目录中的其他重要链接名称包括vs0_desc和vs1_desc，
# 分别代表VideoStreaming接口0/1的描述符。
mkdir -p $GADGET/strings/0x409/iad_desc
echo -n "Interface Associaton Descriptor" > $GADGET/strings/0x409/iad_desc/s
ln -s $GADGET/strings/0x409/iad_desc $FUNCTION/iad_desc

# 由于从扩展单元到字符串描述符的链接清楚地关联了两者，
# 这里链接的名称并不重要，可以自由设置。
mkdir -p $GADGET/strings/0x409/xu.0
echo -n "A Very Useful Extension Unit" > $GADGET/strings/0x409/xu.0/s
ln -s $GADGET/strings/0x409/xu.0 $FUNCTION/control/extensions/xu.0

中断端点
~~~~~~~~~~~~~~~~~~~~~~

视频控制接口有一个可选的中断端点，默认情况下是禁用的。该端点旨在支持UVC的延迟响应控制设置请求（这些请求应通过中断端点响应而不是占用端点0）。
目前，通过此端点发送数据的支持缺失，因此将其保持禁用状态以避免混淆。如果希望启用它，可以通过configfs属性进行：

```bash
echo 1 > $FUNCTION/control/enable_interrupt_ep

带宽配置
~~~~~~~~~~~~~~~~~~~~~~~

有三个属性用于控制USB连接的带宽。这些属性位于功能根目录下，并且可以根据限制进行设置：

```bash
# streaming_interval设置bInterval。值范围从1..255
echo 1 > $FUNCTION/streaming_interval

# streaming_maxpacket设置wMaxPacketSize。有效值为1024/2048/3072
echo 3072 > $FUNCTION/streaming_maxpacket

# streaming_maxburst设置bMaxBurst。有效值为1..15
echo 1 > $FUNCTION/streaming_maxburst

传递给这里的值将根据UVC规范（这取决于USB连接的速度）限制为有效值。要理解这些设置如何影响带宽，请参考UVC规范，
但大致的规则是增加streaming_maxpacket设置会提高带宽（从而提高最大可能的帧率），而同样对于streaming_maxburst而言，
只要USB连接运行在SuperSpeed模式下也是如此。增加streaming_interval会降低带宽和帧率。

用户空间应用
-------------------------
仅凭UVC Gadget驱动程序本身无法实现任何特别有趣的功能。它必须与一个用户空间程序配对，该程序响应UVC控制请求并填充要排队到驱动程序创建的V4L2设备的缓冲区。
如何实现这些功能取决于具体实现并且超出了本文档的范围，但是可以在https://gitlab.freedesktop.org/camera/uvc-gadget找到一个参考应用。
```
