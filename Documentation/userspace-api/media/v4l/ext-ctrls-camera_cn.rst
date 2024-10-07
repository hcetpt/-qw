SPDX 许可声明：GFDL-1.1-no-invariants-or-later

.. _camera-controls:

************************
相机控制参考
************************

Camera 类包括对设备的机械（或等效数字）功能的控制，例如可控镜头或传感器。
.. _camera-control-id:

相机控制 ID
==================

``V4L2_CID_CAMERA_CLASS (class)``
    相机类描述符。调用此控制的 :ref:`VIDIOC_QUERYCTRL` 将返回该控制类的描述。

.. _v4l2-exposure-auto-type:

``V4L2_CID_EXPOSURE_AUTO``
    (枚举)

枚举 v4l2_exposure_auto_type -
    启用曝光时间和/或光圈的自动调整。在启用这些功能时手动更改曝光时间或光圈的效果是未定义的，驱动程序应忽略此类请求。可能的值有：

.. tabularcolumns:: |p{7.1cm}|p{10.4cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_EXPOSURE_AUTO``
      - 自动曝光时间，自动光圈
    * - ``V4L2_EXPOSURE_MANUAL``
      - 手动曝光时间，手动光圈
    * - ``V4L2_EXPOSURE_SHUTTER_PRIORITY``
      - 手动曝光时间，自动光圈
    * - ``V4L2_EXPOSURE_APERTURE_PRIORITY``
      - 自动曝光时间，手动光圈

``V4L2_CID_EXPOSURE_ABSOLUTE (integer)``
    确定相机传感器的曝光时间。曝光时间受帧间隔限制。驱动程序应将值解释为 100 微秒单位，其中值 1 表示 1/10000 秒，10000 表示 1 秒，100000 表示 10 秒。

``V4L2_CID_EXPOSURE_AUTO_PRIORITY (boolean)``
    当 ``V4L2_CID_EXPOSURE_AUTO`` 设置为 ``AUTO`` 或 ``APERTURE_PRIORITY`` 时，此控制确定设备是否可以动态改变帧率。默认情况下此功能是禁用的（0），帧率必须保持恒定。

``V4L2_CID_AUTO_EXPOSURE_BIAS (integer menu)``
    确定自动曝光补偿，在 ``V4L2_CID_EXPOSURE_AUTO`` 控制设置为 ``AUTO``、``SHUTTER_PRIORITY`` 或 ``APERTURE_PRIORITY`` 时生效。它以 EV（曝光值）表示，驱动程序应将值解释为 0.001 EV 单位，其中值 1000 表示 +1 EV。
增加曝光补偿值相当于减少曝光值（EV），并将增加图像传感器上的光线量。相机通过调整绝对曝光时间和/或光圈来实现曝光补偿。
``V4L2_CID_EXPOSURE_METERING``
（枚举类型）

`enum v4l2_exposure_metering` — 确定相机如何测量帧曝光时可用的光线量。可能的值包括：

.. tabularcolumns:: |p{8.7cm}|p{8.7cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_EXPOSURE_METERING_AVERAGE``
      - 使用整个帧的光线信息并平均，不对计量区域的任何特定部分进行加权。
* - ``V4L2_EXPOSURE_METERING_CENTER_WEIGHTED``
      - 平均整个帧的光线信息，并优先考虑计量区域的中心。
* - ``V4L2_EXPOSURE_METERING_SPOT``
      - 只测量帧中心的一小块区域。
* - ``V4L2_EXPOSURE_METERING_MATRIX``
      - 多区域测光。在帧的多个点测量光线强度并将结果组合。区域选择算法和计算最终值时各个区域的重要性取决于设备。

``V4L2_CID_PAN_RELATIVE (整数)``
    此控制使相机按指定的数量水平旋转。
单位未定义。正值使相机向右移动（从上方看为顺时针），负值使相机向左移动。零值不会导致运动。这是一个只写控制。

``V4L2_CID_TILT_RELATIVE (整数)``
    此控制使相机按指定的数量垂直旋转。
单位未定义。正值使相机向上移动，负值使相机向下移动。零值不会导致运动。这是一个只写控制。

``V4L2_CID_PAN_RESET (按钮)``
    当设置此控制时，相机水平移动到默认位置。

``V4L2_CID_TILT_RESET (按钮)``
    当设置此控制时，相机垂直移动到默认位置。
``V4L2_CID_PAN_ABSOLUTE (整数)``
    此控制将相机水平转向指定的位置。正值使相机向右移动（从上方观察时为顺时针），负值使相机向左移动。驱动程序应将这些值解释为弧秒，有效值范围为-180 * 3600到+180 * 3600（包括两端）。

``V4L2_CID_TILT_ABSOLUTE (整数)``
    此控制将相机垂直转向指定的位置。正值使相机向上移动，负值使相机向下移动。驱动程序应将这些值解释为弧秒，有效值范围为-180 * 3600到+180 * 3600（包括两端）。

``V4L2_CID_FOCUS_ABSOLUTE (整数)``
    此控制将相机的焦点设置到指定的位置。单位未定义。正值使焦点更靠近相机，负值使焦点趋向于无穷远。

``V4L2_CID_FOCUS_RELATIVE (整数)``
    此控制将相机的焦点移动指定的距离。单位未定义。正值使焦点更靠近相机，负值使焦点趋向于无穷远。这是一个只写控制。

``V4L2_CID_FOCUS_AUTO (布尔)``
    启用连续自动对焦调整。当启用此功能时，手动对焦调整的效果是未定义的，驱动程序应忽略此类请求。

``V4L2_CID_AUTO_FOCUS_START (按钮)``
    启动单次自动对焦过程。当``V4L2_CID_FOCUS_AUTO``设置为``TRUE``（1）时设置此控制的效果是未定义的，驱动程序应忽略此类请求。

``V4L2_CID_AUTO_FOCUS_STOP (按钮)``
    中断由``V4L2_CID_AUTO_FOCUS_START``控制启动的自动对焦。仅在连续自动对焦禁用时（即``V4L2_CID_FOCUS_AUTO``设置为``FALSE``（0）时）才有效。

.. _v4l2-auto-focus-status:

``V4L2_CID_AUTO_FOCUS_STATUS (位掩码)``
    自动对焦状态。这是一个只读控制。
    设置``V4L2_LOCK_FOCUS``锁位的``V4L2_CID_3A_LOCK``控制可能停止更新``V4L2_CID_AUTO_FOCUS_STATUS``控制的值。
```markdown
.. tabularcolumns:: |p{6.8cm}|p{10.7cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_AUTO_FOCUS_STATUS_IDLE``
      - 自动对焦未激活
    * - ``V4L2_AUTO_FOCUS_STATUS_BUSY``
      - 正在进行自动对焦
    * - ``V4L2_AUTO_FOCUS_STATUS_REACHED``
      - 已完成对焦
    * - ``V4L2_AUTO_FOCUS_STATUS_FAILED``
      - 自动对焦失败，驱动程序不会从该状态转换，直到应用程序执行另一项操作

.. _v4l2-auto-focus-range:

``V4L2_CID_AUTO_FOCUS_RANGE``
    （枚举）

enum v4l2_auto_focus_range -
    确定镜头可调整的自动对焦距离范围

.. tabularcolumns:: |p{6.9cm}|p{10.6cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_AUTO_FOCUS_RANGE_AUTO``
      - 相机会自动选择对焦范围
    * - ``V4L2_AUTO_FOCUS_RANGE_NORMAL``
      - 正常距离范围，限于最佳自动对焦性能
    * - ``V4L2_AUTO_FOCUS_RANGE_MACRO``
      - 微距（特写）自动对焦。相机会使用其最小可能的距离进行自动对焦
    * - ``V4L2_AUTO_FOCUS_RANGE_INFINITY``
      - 镜头设置为对无限远的对象进行对焦

``V4L2_CID_ZOOM_ABSOLUTE (integer)``
    指定目标镜头的焦距作为绝对值。变焦单位是驱动程序特定的，其值应为正整数
```
``V4L2_CID_ZOOM_RELATIVE (整数)``
    指定相对于当前值的目标镜头焦距。正值将变焦镜头组向远摄方向移动，负值向广角方向移动。变焦单位取决于驱动程序。这是一个只写控制。

``V4L2_CID_ZOOM_CONTINUOUS (整数)``
    以指定速度移动目标镜头组，直到达到物理设备限制或收到停止移动的明确请求。正值将变焦镜头组向远摄方向移动。零值停止变焦镜头组的移动。负值将变焦镜头组向广角方向移动。变焦速度单位取决于驱动程序。

``V4L2_CID_IRIS_ABSOLUTE (整数)``
    此控制将相机的光圈设置为指定的值。单位未定义。较大的值使光圈开得更大，较小的值使其闭合。

``V4L2_CID_IRIS_RELATIVE (整数)``
    此控制根据指定的数量修改相机的光圈。单位未定义。正值使光圈进一步打开一档，负值使其进一步关闭一档。这是一个只写控制。

``V4L2_CID_PRIVACY (布尔)``
    阻止相机获取视频。当此控制设置为“TRUE”（1）时，相机无法捕捉任何图像。实现隐私保护的常见方法包括机械遮挡传感器和固件图像处理，但设备不限于这些方法。实现隐私控制的设备必须支持读取访问，并且可能支持写入访问。

``V4L2_CID_BAND_STOP_FILTER (整数)``
    打开或关闭相机传感器的带阻滤波器，或指定其强度。这种带阻滤波器可以用来滤除荧光灯成分等。

.. _v4l2-auto-n-preset-white-balance:

``V4L2_CID_AUTO_N_PRESET_WHITE_BALANCE``
    （枚举）

枚举 v4l2_auto_n_preset_white_balance -
    设置白平衡为自动、手动或预设。预设确定光源的颜色温度，作为相机进行白平衡调整的提示，从而获得最准确的颜色表现。以下列出的白平衡预设按颜色温度递增顺序排列。

.. tabularcolumns:: |p{7.4cm}|p{10.1cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_WHITE_BALANCE_MANUAL``
      - 手动白平衡
* - ``V4L2_WHITE_BALANCE_AUTO``
      - 自动白平衡调整
* - ``V4L2_WHITE_BALANCE_INCANDESCENT``
      - 白炽灯（钨丝灯）照明的白平衡设置。通常会使颜色变冷，并对应大约 2500...3500 K 的色温范围。
* - ``V4L2_WHITE_BALANCE_FLUORESCENT``
      - 荧光灯照明的白平衡预设。大约对应 4000...5000 K 的色温。
* - ``V4L2_WHITE_BALANCE_FLUORESCENT_H``
      - 使用此设置，相机将补偿荧光 H 灯的光线。
* - ``V4L2_WHITE_BALANCE_HORIZON``
      - 地平线日光的白平衡设置。大约对应 5000 K 的色温。
* - ``V4L2_WHITE_BALANCE_DAYLIGHT``
      - 晴朗天空下的日光白平衡预设。大约对应 5000...6500 K 的色温。
* - ``V4L2_WHITE_BALANCE_FLASH``
      - 使用此设置，相机将补偿闪光灯光。它略微使颜色变暖，并大致对应 5000...5500 K 的色温。
* - ``V4L2_WHITE_BALANCE_CLOUDY``
      - 阴天天空的白平衡预设。此选项大约对应 6500...8000 K 的色温范围。
* - ``V4L2_WHITE_BALANCE_SHADE``
      - 阴凉处或浓云密布的天空的白平衡预设。大约对应 9000...10000 K 的色温。
... _v4l2-wide-dynamic-range:

``V4L2_CID_WIDE_DYNAMIC_RANGE (布尔)``
    启用或禁用相机的宽动态范围功能。此功能可以在光照强度在场景中显著变化的情况下获得清晰图像，即同时存在非常暗和非常亮的区域。该功能通常通过组合两个曝光时间不同的连续帧来实现。[#f1]_

... _v4l2-image-stabilization:

``V4L2_CID_IMAGE_STABILIZATION (布尔)``
    启用或禁用图像稳定功能。

``V4L2_CID_ISO_SENSITIVITY (整数菜单)``
    确定图像传感器的ISO等效值，表示传感器对光线的敏感度。数值按照 :ref:`iso12232` 标准中的算术比例表示，其中传感器敏感度翻倍时，数值ISO值也会翻倍。
应用程序应将这些值解释为标准ISO值乘以1000，例如控制值800表示ISO 0.8。
驱动程序通常只支持标准ISO值的一部分。
当 ``V4L2_CID_ISO_SENSITIVITY_AUTO`` 控制设置为除 ``V4L2_CID_ISO_SENSITIVITY_MANUAL`` 之外的值时，设置此控制的效果是未定义的，驱动程序应忽略此类请求。

... _v4l2-iso-sensitivity-auto-type:

``V4L2_CID_ISO_SENSITIVITY_AUTO``
    (枚举)

枚举 v4l2_iso_sensitivity_type -
    启用或禁用自动ISO敏感度调整。

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_CID_ISO_SENSITIVITY_MANUAL``
      - 手动ISO敏感度
    * - ``V4L2_CID_ISO_SENSITIVITY_AUTO``
      - 自动ISO敏感度调整

... _v4l2-scene-mode:

``V4L2_CID_SCENE_MODE``
    (枚举)

枚举 v4l2_scene_mode -
    此控制允许选择场景程序，作为相机自动模式优化常见拍摄场景。在这些模式下，相机会确定最佳曝光、光圈、聚焦、测光、白平衡和等效敏感度。这些参数的控制受到场景模式控制的影响。每种模式的确切行为取决于相机规格。
当场景模式功能未被使用时，应将此控制设置为 `V4L2_SCENE_MODE_NONE` 以确保其他可能相关的控制可以访问。以下定义了几个场景程序：

.. raw:: latex

    \small

.. tabularcolumns:: |p{5.9cm}|p{11.6cm}|

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_SCENE_MODE_NONE``
      - 场景模式功能已禁用
* - ``V4L2_SCENE_MODE_BACKLIGHT``
      - 背光。补偿光源来自拍摄对象背后时的暗影，同时自动打开闪光灯
* - ``V4L2_SCENE_MODE_BEACH_SNOW``
      - 海滩和雪地。该模式补偿全白或明亮场景，这些场景在相机自动曝光基于平均亮度时容易显得灰暗且对比度低。为了补偿，该模式会自动略微过曝画面。白平衡也可能进行调整，以补偿反射雪看起来偏蓝而不是白色的情况
* - ``V4L2_SCENE_MODE_CANDLELIGHT``
      - 烛光。相机通常会提高ISO感光度并降低快门速度。此模式适用于场景中相对靠近的拍摄对象。为了保持光线氛围，闪光灯会被禁用
* - ``V4L2_SCENE_MODE_DAWN_DUSK``
      - 黎明和黄昏。在黄昏前后的低自然光条件下保留所见的颜色。相机可能会关闭闪光灯，并自动对焦到无穷远。它通常会增加饱和度并降低快门速度
* - ``V4L2_SCENE_MODE_FALL_COLORS``
      - 秋色。增加饱和度并调整白平衡以增强色彩。拍摄的秋叶照片会有更鲜艳的红色和黄色
* - ``V4L2_SCENE_MODE_FIREWORKS``
      - 烟花。使用长时间曝光来捕捉烟花绽放的光线。相机可能会启用图像稳定功能
* - ``V4L2_SCENE_MODE_LANDSCAPE``
      - 风景。相机可能会选择小光圈以提供较大的景深，并使用较长的曝光时间以帮助在昏暗光线下捕捉细节。焦点固定在无穷远处。适合拍摄远处和广阔的风景
* - ``V4L2_SCENE_MODE_NIGHT``
      - 夜景，也称为夜景风景。专为低光条件设计，可在黑暗区域保留细节而不使亮物过曝。相机通常设置为中等到高ISO感光度，并使用相对较长的曝光时间，同时关闭闪光灯。因此，图像噪声会增加，并有可能出现模糊图像
* - ``V4L2_SCENE_MODE_PARTY_INDOOR``
      - 派对和室内。专为捕捉由室内背景灯光及闪光灯照明的室内场景而设计。相机通常会增加ISO感光度，并根据低光条件调整曝光
* - ``V4L2_SCENE_MODE_PORTRAIT``
      - 人像。相机调整光圈以减少景深，有助于将主体与平滑的背景区分开来。大多数相机能够识别场景中的人脸并聚焦于它们。色彩色调经过调整以增强肤色。闪光灯的强度通常会减弱。
* - ``V4L2_SCENE_MODE_SPORTS``
      - 运动。显著提高ISO并使用快速快门速度来冻结快速移动的物体。在此模式下可能会看到图像噪点增加。
* - ``V4L2_SCENE_MODE_SUNSET``
      - 日落。保留日出和日落时所见的深色调，并提升饱和度。
* - ``V4L2_SCENE_MODE_TEXT``
      - 文本。应用额外的对比度和锐化效果，通常是黑白模式，优化阅读性。自动对焦可能切换到微距模式，并且此设置还可能涉及一些镜头畸变校正。

.. raw:: latex

    \normalsize

``V4L2_CID_3A_LOCK (bitmask)``
    此控制锁定或解锁自动对焦、曝光和白平衡。通过将相应的锁位设置为1可以独立暂停自动调整。相机将保留这些设置直到锁位被清除。以下锁位定义如下：

    当某个算法未启用时，驱动程序应忽略锁定请求并且不应返回错误。例如，当``V4L2_CID_AUTO_WHITE_BALANCE``控制设置为``FALSE``时，应用程序设置``V4L2_LOCK_WHITE_BALANCE``位。此控制的值可以通过曝光、白平衡或对焦控制进行更改。

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_LOCK_EXPOSURE``
      - 自动曝光调整锁定
* - ``V4L2_LOCK_WHITE_BALANCE``
      - 自动白平衡调整锁定
* - ``V4L2_LOCK_FOCUS``
      - 自动对焦锁定

``V4L2_CID_PAN_SPEED (integer)``
    此控制使相机以特定速度水平转动。
单位未定义。正值向右移动（从上方看是顺时针），负值向左移动。零值停止正在进行的动作，否则没有效果。
``V4L2_CID_TILT_SPEED (整数)``
    此控制以指定的速度垂直移动摄像头。单位未定义。正值使摄像头向上移动，负值使摄像头向下移动。零值会停止正在进行的运动，在没有运动时则无效果。
.. _v4l2-camera-sensor-orientation:

``V4L2_CID_CAMERA_ORIENTATION (菜单)``
    这个只读控制通过报告摄像头在设备上的安装位置来描述摄像头的方向。该控制值是恒定的，不可由软件修改。对于有明确方向的设备（如手机、笔记本电脑和便携设备），此控制特别有意义，因为它是相对于设备预期使用方向的位置来表示的。例如，安装在手机、平板或笔记本电脑用户面一侧的摄像头被称为具有 ``V4L2_CAMERA_ORIENTATION_FRONT`` 方向，而安装在正面相反一侧的摄像头则被称为具有 ``V4L2_CAMERA_ORIENTATION_BACK`` 方向。不直接连接到设备或可以自由移动的摄像头（如网络摄像头和数码相机）则被称为具有 ``V4L2_CAMERA_ORIENTATION_EXTERNAL`` 方向。
.. tabularcolumns:: |p{7.7cm}|p{9.8cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_CAMERA_ORIENTATION_FRONT``
      - 摄像头面向设备的用户面
* - ``V4L2_CAMERA_ORIENTATION_BACK``
      - 摄像头面向设备的背面
* - ``V4L2_CAMERA_ORIENTATION_EXTERNAL``
      - 摄像头未直接连接到设备且可自由移动
.. _v4l2-camera-sensor-rotation:

``V4L2_CID_CAMERA_SENSOR_ROTATION (整数)``
    此只读控制描述了捕捉到内存中的图像需要进行的逆时针旋转修正度数，以补偿摄像头传感器的安装旋转。
有关传感器安装旋转的确切定义，请参阅设备树绑定文件 `video-interfaces.txt` 中对 “rotation” 属性的详细描述。
下面是一些示例，假设场景是一个鲨鱼从左向右游过用户的前方：
    
                 0               X轴
               0 +------------------------------------->
                 !
                 !
                 !
                 !           |\____)\___
                 !           ) _____  __`<
                 !           |/     )/
                 !
                 !
                 !
                 V
               Y轴

示例一 - 网络摄像头

假设你可以在与鲨鱼一起游泳时带着笔记本电脑，笔记本电脑的摄像头模块安装在屏幕盖上朝向用户的一面，通常用于视频通话。捕捉的图像打算以横向模式（宽度 > 高度）显示在笔记本电脑屏幕上。
摄像头通常倒装以补偿镜头光学反转效果。在这种情况下，``V4L2_CID_CAMERA_SENSOR_ROTATION`` 控制的值为 0，无需旋转即可正确显示图像给用户。
如果摄像头传感器没有倒装，则需要补偿镜头光学反转效果，此时 ``V4L2_CID_CAMERA_SENSOR_ROTATION`` 控制的值为 180 度，因为捕捉到内存中的图像会旋转。::

                 +--------------------------------------+
                 !                                      !
                 !                                      !
                 !                                      !
                 !              __/(_____/|             !
                 !            >.___  ____ (             !
                 !                 \(    \|             !
                 !                                      !
                 !                                      !
                 !                                      !
                 +--------------------------------------+

需要应用 180 度的软件旋转修正才能正确显示图像。::

                 +--------------------------------------+
                 !                                      !
                 !                                      !
                 !                                      !
                 !             |\____)\___              !
                 !             ) _____  __`<            !
                 !             |/     )/                !
                 !                                      !
                 !                                      !
                 !                                      !
                 +--------------------------------------+

示例二 - 手机摄像头

携带手机去与鲨鱼一起游泳并用安装在设备背面的摄像头拍照更为方便，摄像头面向远离用户的一侧。捕捉的图像打算以纵向模式（高度 > 宽度）显示，以匹配设备屏幕的方向和拍摄照片时的设备使用方向。
相机传感器通常安装在其像素阵列的长边与设备的长边对齐，并且倒装以补偿镜头的光学倒转效果。
一旦图像被捕获到内存中，将会进行旋转，并且 `V4L2_CID_CAMERA_SENSOR_ROTATION` 的值将报告为 90 度旋转。 ::

                 +-------------------------------------+
                 |                 _ _                 |
                 |                \   /                |
                 |                 | |                 |
                 |                 | |                 |
                 |                 |  >                |
                 |                <  |                 |
                 |                 | |                 |
                 |                   .                 |
                 |                  V                  |
                 +-------------------------------------+

为了在设备屏幕上正确显示图像，需要应用逆时针方向的 90 度校正。 ::

                          +--------------------+
                          |                    |
                          |                    |
                          |                    |
                          |                    |
                          |                    |
                          |                    |
                          |   |\____)\___      |
                          |   ) _____  __`<    |
                          |   |/     )/        |
                          |                    |
                          |                    |
                          |                    |
                          |                    |
                          |                    |
                          +--------------------+

.. [#f1]
   如果将来需要更多选项，此控制可能会更改为菜单控制。
   ``V4L2_CID_HDR_SENSOR_MODE (menu)``
    更改传感器的 HDR 模式。通过使用两个不同的曝光时间段拍摄同一场景的两幅图像并将其合并，可以获得 HDR 图像。HDR 模式描述了这两个图像在传感器中如何合并。
由于不同传感器的模式有所不同，因此此控制不标准化菜单项，而是留给程序员处理。
