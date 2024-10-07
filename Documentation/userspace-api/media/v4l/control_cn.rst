.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _control:

*************
用户控制
*************

设备通常具有一些用户可设置的控制项，例如亮度、饱和度等，在图形用户界面上会向用户展示。但是，不同的设备会有不同的可用控制项，并且可能值的范围以及默认值也会因设备而异。控制 ioctl 提供了信息和机制来创建一个良好的用户界面，使其能够正确地与任何设备一起工作。

所有控制项都通过一个 ID 值进行访问。V4L2 定义了多个用于特定目的的 ID。驱动程序也可以使用 `V4L2_CID_PRIVATE_BASE`  [#f1]_ 及更高的值来实现自定义控制。预定义的控制 ID 以 `V4L2_CID_` 为前缀，并列在 :ref:`control-id` 中。该 ID 在查询控制属性时以及获取或设置当前值时使用。

通常应用程序应该向用户提供控制项而不假设其用途。每个控制项都有一个名称字符串，用户应该能够理解。当用途不直观时，驱动程序编写者应提供用户手册、用户界面插件或特定于驱动程序的面板应用程序。预定义的 ID 是为了编程更改某些控制项而引入的，例如在切换频道时静音设备。

驱动程序可以在切换当前视频输入或输出、调谐器或调制器或音频输入或输出后枚举不同的控制项。不同之处在于其他边界、另一个默认值和当前值、步长或其他菜单项。具有特定 *自定义* ID 的控制项也可以更改名称和类型。

如果某个控制项不适用于设备的当前配置（例如，它不适用于当前视频输入），则驱动程序会设置 `V4L2_CTRL_FLAG_INACTIVE` 标志。

控制值全局存储，切换时不会改变，除了保持在报告的范围内。它们也不会在设备打开或关闭、调谐器无线电频率改变时改变，除非有应用程序请求。

V4L2 规定了一个事件机制来通知应用程序控制项值的变化（参见 :ref:`VIDIOC_SUBSCRIBE_EVENT`，事件 `V4L2_EVENT_CTRL`），面板应用程序可能希望利用这一点以始终反映正确的控制值。

所有控制项均使用机器字节序。
.. _control-id:

控制ID
===========

``V4L2_CID_BASE``
    首个预定义的ID，等同于``V4L2_CID_BRIGHTNESS``
``V4L2_CID_USER_BASE``
    ``V4L2_CID_BASE`` 的同义词
``V4L2_CID_BRIGHTNESS`` ``(整数)``
    图像亮度，更准确地说是黑电平
``V4L2_CID_CONTRAST`` ``(整数)``
    图像对比度或亮度增益
``V4L2_CID_SATURATION`` ``(整数)``
    图像色彩饱和度或色度增益
``V4L2_CID_HUE`` ``(整数)``
    色调或色彩平衡
``V4L2_CID_AUDIO_VOLUME`` ``(整数)``
    总体音量。注意一些驱动程序还提供OSS或ALSA混音器接口
``V4L2_CID_AUDIO_BALANCE`` ``(整数)``
    音频立体声平衡。最小值对应完全左声道，最大值对应右声道
``V4L2_CID_AUDIO_BASS`` ``(整数)``
    音频低音调节
``V4L2_CID_AUDIO_TREBLE`` ``(整数)``
    音频高音调节
``V4L2_CID_AUDIO_MUTE`` ``(布尔值)``
    静音音频，即把音量设置为零，但不影响``V4L2_CID_AUDIO_VOLUME``。像ALSA驱动一样，V4L2驱动在加载时必须静音以避免过多的噪音。实际上整个设备应该重置到低功耗状态。

``V4L2_CID_AUDIO_LOUDNESS`` ``(布尔值)``
    低音增强模式

``V4L2_CID_BLACK_LEVEL`` ``(整数)``
    另一个亮度名称（不是``V4L2_CID_BRIGHTNESS``的同义词）。这个控制已经被弃用，不应该在新的驱动和应用程序中使用。

``V4L2_CID_AUTO_WHITE_BALANCE`` ``(布尔值)``
    自动白平衡（摄像头）

``V4L2_CID_DO_WHITE_BALANCE`` ``(按钮)``
    这是一个动作控制。当被设置（其值被忽略）时，设备将进行一次白平衡调整并保持当前设置。
    与布尔值``V4L2_CID_AUTO_WHITE_BALANCE``不同，后者在激活后会持续调整白平衡。

``V4L2_CID_RED_BALANCE`` ``(整数)``
    红色色度平衡

``V4L2_CID_BLUE_BALANCE`` ``(整数)``
    蓝色色度平衡

``V4L2_CID_GAMMA`` ``(整数)``
    伽玛校正

``V4L2_CID_WHITENESS`` ``(整数)``
    灰阶设备的白度。这是``V4L2_CID_GAMMA``的同义词。这个控制已经被弃用，不应该在新的驱动和应用程序中使用。
``V4L2_CID_EXPOSURE`` ``(整数)``
    曝光（摄像头）。[单位？]

``V4L2_CID_AUTOGAIN`` ``(布尔值)``
    自动增益/曝光控制

``V4L2_CID_GAIN`` ``(整数)``
    增益控制
    主要用于控制例如电视调谐器和网络摄像头的增益。大多数设备仅通过此控制调整数字增益，但在某些设备上这可能还包括模拟增益。识别数字和模拟增益之间区别的设备使用控件 ``V4L2_CID_DIGITAL_GAIN`` 和 ``V4L2_CID_ANALOGUE_GAIN``。

.. _v4l2-cid-hflip:

``V4L2_CID_HFLIP`` ``(布尔值)``
    水平镜像画面

.. _v4l2-cid-vflip:

``V4L2_CID_VFLIP`` ``(布尔值)``
    垂直镜像画面

.. _v4l2-power-line-frequency:

``V4L2_CID_POWER_LINE_FREQUENCY`` ``(枚举)``
    启用电源频率滤波器以避免闪烁。``v4l2_power_line_frequency`` 枚举类型的可能值为：

    ==========================================  ==
    ``V4L2_CID_POWER_LINE_FREQUENCY_DISABLED``   0
    ``V4L2_CID_POWER_LINE_FREQUENCY_50HZ``       1
    ``V4L2_CID_POWER_LINE_FREQUENCY_60HZ``       2
    ``V4L2_CID_POWER_LINE_FREQUENCY_AUTO``       3
    ==========================================  ==

``V4L2_CID_HUE_AUTO`` ``(布尔值)``
    启用设备的自动色调控制。在启用自动色调控制的情况下设置 ``V4L2_CID_HUE`` 的效果是不确定的，驱动程序应忽略此类请求。

``V4L2_CID_WHITE_BALANCE_TEMPERATURE`` ``(整数)``
    此控制指定以开尔文为单位的颜色温度作为白平衡设置。驱动程序应该至少支持从 2800（白炽灯）到 6500（日光）。有关颜色温度的更多信息，请参阅
    `Wikipedia <http://en.wikipedia.org/wiki/Color_temperature>`__。

``V4L2_CID_SHARPNESS`` ``(整数)``
    调整相机中的锐度滤镜。最小值禁用滤镜，更高值提供更清晰的画面。

``V4L2_CID_BACKLIGHT_COMPENSATION`` ``(整数)``
    调整相机中的背光补偿。最小值禁用背光补偿。

``V4L2_CID_CHROMA_AGC`` ``(布尔值)``
    色度自动增益控制
``V4L2_CID_CHROMA_GAIN`` ``(整数)``
    调整色度增益控制（在色度自动增益控制禁用时使用）

``V4L2_CID_COLOR_KILLER`` ``(布尔)``
    启用颜色消除功能（即在视频信号较弱的情况下强制输出黑白图像）

.. _v4l2-colorfx:

``V4L2_CID_COLORFX`` ``(枚举)``
    选择一种颜色效果。定义了以下值：

.. tabularcolumns:: |p{5.7cm}|p{11.8cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths: 11 24

    * - ``V4L2_COLORFX_NONE``
      - 禁用颜色效果
    * - ``V4L2_COLORFX_ANTIQUE``
      - 老化（旧照片）效果
    * - ``V4L2_COLORFX_ART_FREEZE``
      - 冰霜颜色效果
    * - ``V4L2_COLORFX_AQUA``
      - 水彩，冷色调
    * - ``V4L2_COLORFX_BW``
      - 黑白
    * - ``V4L2_COLORFX_EMBOSS``
      - 浮雕效果，高光和阴影替换明暗边界，并将低对比度区域设置为灰色背景
    * - ``V4L2_COLORFX_GRASS_GREEN``
      - 草绿色
    * - ``V4L2_COLORFX_NEGATIVE``
      - 负片
* - ``V4L2_COLORFX_SEPIA``
      - 棕褐色调
* - ``V4L2_COLORFX_SKETCH``
      - 草图
* - ``V4L2_COLORFX_SKIN_WHITEN``
      - 皮肤美白
* - ``V4L2_COLORFX_SKY_BLUE``
      - 天蓝色
* - ``V4L2_COLORFX_SOLARIZATION``
      - 日光化，图像的部分色调被反转，只有高于或低于某个阈值的颜色值会被反转
* - ``V4L2_COLORFX_SILHOUETTE``
      - 剪影（轮廓）
* - ``V4L2_COLORFX_VIVID``
      - 鲜艳色彩
* - ``V4L2_COLORFX_SET_CBCR``
      - 用由 ``V4L2_CID_COLORFX_CBCR`` 控制确定的固定系数替换 Cb 和 Cr 色度分量
* - ``V4L2_COLORFX_SET_RGB``
      - 用由 ``V4L2_CID_COLORFX_RGB`` 控制确定的固定 RGB 分量替换 RGB 分量

``V4L2_CID_COLORFX_RGB`` （整数）
    确定用于 ``V4L2_COLORFX_SET_RGB`` 色彩效果的红色、绿色和蓝色系数
提供的32位值的[7:0]位被解释为蓝色分量，
[15:8]位作为绿色分量，[23:16]位作为红色分量，
[31:24]位必须为零。

``V4L2_CID_COLORFX_CBCR`` ``(整数)``
    确定用于`V4L2_COLORFX_SET_CBCR`颜色效果的Cb和Cr系数。提供的32位值的[7:0]位
    被解释为Cr分量，[15:8]位作为Cb分量，[31:16]位必须为零。

``V4L2_CID_AUTOBRIGHTNESS`` ``(布尔)``
    启用自动亮度调节。

``V4L2_CID_ROTATE`` ``(整数)``
    按指定角度旋转图像。常用的旋转角度为90、270和180度。将图像旋转到90和270度会反转显示窗口的高度和宽度。
    必须根据所选旋转角度使用`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl设置新的高度和宽度。

``V4L2_CID_BG_COLOR`` ``(整数)``
    设置当前输出设备的背景色。背景色需要以RGB24格式指定。提供的32位值被解释为0-7位为红色信息，
    8-15位为绿色信息，16-23位为蓝色信息，24-31位必须为零。

``V4L2_CID_ILLUMINATORS_1 V4L2_CID_ILLUMINATORS_2`` ``(布尔)``
    开启或关闭设备（通常是显微镜）的照明器1或2。

``V4L2_CID_MIN_BUFFERS_FOR_CAPTURE`` ``(整数)``
    这是一个只读控制项，应用程序可以读取它并将其作为提示来确定传递给REQBUFS的CAPTURE缓冲区数量。
    值是硬件正常工作所需的最小CAPTURE缓冲区数量。

``V4L2_CID_MIN_BUFFERS_FOR_OUTPUT`` ``(整数)``
    这是一个只读控制项，应用程序可以读取它并将其作为提示来确定传递给REQBUFS的OUTPUT缓冲区数量。
    值是硬件正常工作所需的最小OUTPUT缓冲区数量。

``V4L2_CID_ALPHA_COMPONENT`` ``(整数)``
    设置alpha颜色分量。当捕获设备（或mem-to-mem设备的捕获队列）生成包含alpha分量的帧格式（例如
    `打包的RGB图像格式 <pixfmt-rgb>`__），并且alpha值未由设备或mem-to-mem输入数据定义时，
    此控制项允许您选择所有像素的alpha分量值。
当输出设备（或内存到内存设备的输出队列）消耗一种不包含Alpha组件的帧格式，并且该设备支持Alpha通道处理时，此控制允许您设置所有像素的Alpha组件值以供设备进一步处理。

``V4L2_CID_LASTP1``
预定义控制ID的结束（目前为``V4L2_CID_ALPHA_COMPONENT`` + 1）

``V4L2_CID_PRIVATE_BASE``
第一个自定义（驱动程序特定）控制的ID。依赖于特定自定义控制的应用程序应检查驱动程序名称和版本，参见 :ref:`querycap`

应用程序可以通过 :ref:`VIDIOC_QUERYCTRL` 和 :ref:`VIDIOC_QUERYMENU <VIDIOC_QUERYCTRL>` 的ioctl调用来枚举可用的控制项，通过 :ref:`VIDIOC_G_CTRL <VIDIOC_G_CTRL>` 和 :ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` 的ioctl调用来获取和设置控制值。当设备有一个或多个控制项时，驱动程序必须实现``VIDIOC_QUERYCTRL``、``VIDIOC_G_CTRL``和``VIDIOC_S_CTRL``；当设备有一个或多个菜单类型控制项时，必须实现``VIDIOC_QUERYMENU``。

.. _enum_all_controls:

示例：枚举所有控制项
=================

.. code-block:: c

    struct v4l2_queryctrl queryctrl;
    struct v4l2_querymenu querymenu;

    static void enumerate_menu(__u32 id)
    {
	printf("  Menu items:\\n");

	memset(&querymenu, 0, sizeof(querymenu));
	querymenu.id = id;

	for (querymenu.index = queryctrl.minimum;
	     querymenu.index <= queryctrl.maximum;
	     querymenu.index++) {
	    if (0 == ioctl(fd, VIDIOC_QUERYMENU, &querymenu)) {
		printf("  %s\\n", querymenu.name);
	    }
	}
    }

    memset(&queryctrl, 0, sizeof(queryctrl));

    queryctrl.id = V4L2_CTRL_FLAG_NEXT_CTRL;
    while (0 == ioctl(fd, VIDIOC_QUERYCTRL, &queryctrl)) {
	if (!(queryctrl.flags & V4L2_CTRL_FLAG_DISABLED)) {
	    printf("Control %s\\n", queryctrl.name);

	    if (queryctrl.type == V4L2_CTRL_TYPE_MENU)
	        enumerate_menu(queryctrl.id);
        }

	queryctrl.id |= V4L2_CTRL_FLAG_NEXT_CTRL;
    }
    if (errno != EINVAL) {
	perror("VIDIOC_QUERYCTRL");
	exit(EXIT_FAILURE);
    }

示例：枚举所有控制项（包括复合控制项）
=============================================

.. code-block:: c

    struct v4l2_query_ext_ctrl query_ext_ctrl;

    memset(&query_ext_ctrl, 0, sizeof(query_ext_ctrl));

    query_ext_ctrl.id = V4L2_CTRL_FLAG_NEXT_CTRL | V4L2_CTRL_FLAG_NEXT_COMPOUND;
    while (0 == ioctl(fd, VIDIOC_QUERY_EXT_CTRL, &query_ext_ctrl)) {
	if (!(query_ext_ctrl.flags & V4L2_CTRL_FLAG_DISABLED)) {
	    printf("Control %s\\n", query_ext_ctrl.name);

	    if (query_ext_ctrl.type == V4L2_CTRL_TYPE_MENU)
	        enumerate_menu(query_ext_ctrl.id);
        }

	query_ext_ctrl.id |= V4L2_CTRL_FLAG_NEXT_CTRL | V4L2_CTRL_FLAG_NEXT_COMPOUND;
    }
    if (errno != EINVAL) {
	perror("VIDIOC_QUERY_EXT_CTRL");
	exit(EXIT_FAILURE);
    }

示例：枚举所有用户控制项（旧风格）
======================================

.. code-block:: c

    memset(&queryctrl, 0, sizeof(queryctrl));

    for (queryctrl.id = V4L2_CID_BASE;
	 queryctrl.id < V4L2_CID_LASTP1;
	 queryctrl.id++) {
	if (0 == ioctl(fd, VIDIOC_QUERYCTRL, &queryctrl)) {
	    if (queryctrl.flags & V4L2_CTRL_FLAG_DISABLED)
		continue;

	    printf("Control %s\\n", queryctrl.name);

	    if (queryctrl.type == V4L2_CTRL_TYPE_MENU)
		enumerate_menu(queryctrl.id);
	} else {
	    if (errno == EINVAL)
		continue;

	    perror("VIDIOC_QUERYCTRL");
	    exit(EXIT_FAILURE);
	}
    }

    for (queryctrl.id = V4L2_CID_PRIVATE_BASE;;
	 queryctrl.id++) {
	if (0 == ioctl(fd, VIDIOC_QUERYCTRL, &queryctrl)) {
	    if (queryctrl.flags & V4L2_CTRL_FLAG_DISABLED)
		continue;

	    printf("Control %s\\n", queryctrl.name);

	    if (queryctrl.type == V4L2_CTRL_TYPE_MENU)
		enumerate_menu(queryctrl.id);
	} else {
	    if (errno == EINVAL)
		break;

	    perror("VIDIOC_QUERYCTRL");
	    exit(EXIT_FAILURE);
	}
    }

示例：更改控制项
=================

.. code-block:: c

    struct v4l2_queryctrl queryctrl;
    struct v4l2_control control;

    memset(&queryctrl, 0, sizeof(queryctrl));
    queryctrl.id = V4L2_CID_BRIGHTNESS;

    if (-1 == ioctl(fd, VIDIOC_QUERYCTRL, &queryctrl)) {
	if (errno != EINVAL) {
	    perror("VIDIOC_QUERYCTRL");
	    exit(EXIT_FAILURE);
	} else {
	    printf("V4L2_CID_BRIGHTNESS is not supported\n");
	}
    } else if (queryctrl.flags & V4L2_CTRL_FLAG_DISABLED) {
	printf("V4L2_CID_BRIGHTNESS is not supported\n");
    } else {
	memset(&control, 0, sizeof (control));
	control.id = V4L2_CID_BRIGHTNESS;
	control.value = queryctrl.default_value;

	if (-1 == ioctl(fd, VIDIOC_S_CTRL, &control)) {
	    perror("VIDIOC_S_CTRL");
	    exit(EXIT_FAILURE);
	}
    }

    memset(&control, 0, sizeof(control));
    control.id = V4L2_CID_CONTRAST;

    if (0 == ioctl(fd, VIDIOC_G_CTRL, &control)) {
	control.value += 1;

	/* 驱动程序可能会限制该值或返回ERANGE，这里忽略 */

	if (-1 == ioctl(fd, VIDIOC_S_CTRL, &control)
	    && errno != ERANGE) {
	    perror("VIDIOC_S_CTRL");
	    exit(EXIT_FAILURE);
	}
    /* 如果V4L2_CID_CONTRAST不受支持则忽略 */
    } else if (errno != EINVAL) {
	perror("VIDIOC_G_CTRL");
	exit(EXIT_FAILURE);
    }

    control.id = V4L2_CID_AUDIO_MUTE;
    control.value = 1; /* 静音 */

    /* 忽略错误 */
    ioctl(fd, VIDIOC_S_CTRL, &control);

.. [#f1]
   使用``V4L2_CID_PRIVATE_BASE``存在问题，因为不同的驱动程序可能使用相同的``V4L2_CID_PRIVATE_BASE`` ID来表示不同的控制项。这使得程序设置此类控制项变得困难，因为该ID所表示的控制项含义取决于驱动程序。为了解决这个问题，驱动程序使用唯一的ID，并且内核将``V4L2_CID_PRIVATE_BASE`` ID映射到这些唯一ID上。可以将这些``V4L2_CID_PRIVATE_BASE`` ID视为实际ID的别名。
许多应用程序仍然使用``V4L2_CID_PRIVATE_BASE`` ID而不是使用带有``V4L2_CTRL_FLAG_NEXT_CTRL``标志的 :ref:`VIDIOC_QUERYCTRL` 来枚举所有ID，因此对``V4L2_CID_PRIVATE_BASE``的支持仍然存在。
