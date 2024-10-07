.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _闪光控制:

**************************
闪光控制参考
**************************

V4L2 闪光控制旨在为闪光控制器设备提供通用访问。闪光控制器设备通常用于数码相机中。该接口可以支持 LED 和氙气闪光设备。截至撰写本文时，尚无使用此接口的氙气闪光驱动程序。

.. _闪光控制用例:

支持的用例
==================

非同步 LED 闪光（软件闪光）
------------------------------------------

非同步 LED 闪光由主机直接控制，就像传感器一样。闪光必须在图像曝光开始前由主机启用，并且在曝光结束后禁用。主机完全负责闪光的时间。
例如这样的设备：诺基亚 N900
同步 LED 闪光（硬件闪光）
----------------------------------------

同步 LED 闪光由主机预先编程（功率和超时时间），但通过来自传感器到闪光设备的闪光信号由传感器控制。
传感器控制闪光的持续时间和时间。这些信息通常必须提供给传感器。
作为手电筒使用的 LED 闪光
------------------

LED 闪光可以与涉及摄像头的其他用例一起使用或单独使用作为手电筒。

.. _闪光控制ID:

闪光控制 ID
-----------------

``V4L2_CID_FLASH_CLASS (class)``
    闪光类描述符
``V4L2_CID_FLASH_LED_MODE (menu)``
    定义闪光 LED 的模式，即连接到闪光控制器的高功率白光 LED。在某些故障存在的情况下，可能无法设置此控制。请参阅 V4L2_CID_FLASH_FAULT

.. tabularcolumns:: |p{5.7cm}|p{11.8cm}|

.. 平坦表格::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_FLASH_LED_MODE_NONE``
      - 关闭
* - ``V4L2_FLASH_LED_MODE_FLASH``
      - 闪光模式
* - ``V4L2_FLASH_LED_MODE_TORCH``
      - 手电筒模式
参见 V4L2_CID_FLASH_TORCH_INTENSITY
``V4L2_CID_FLASH_STROBE_SOURCE (菜单)``
    定义闪光灯闪光的来源
.. tabularcolumns:: |p{7.5cm}|p{7.5cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_FLASH_STROBE_SOURCE_SOFTWARE``
      - 闪光通过使用 V4L2_CID_FLASH_STROBE 控制触发
* - ``V4L2_FLASH_STROBE_SOURCE_EXTERNAL``
      - 闪光由外部源触发。通常这是一个传感器，可以实现闪光开始与曝光开始的同步
``V4L2_CID_FLASH_STROBE (按钮)``
    闪光。当 V4L2_CID_FLASH_LED_MODE 设置为 V4L2_FLASH_LED_MODE_FLASH 并且 V4L2_CID_FLASH_STROBE_SOURCE 设置为 V4L2_FLASH_STROBE_SOURCE_SOFTWARE 时有效。在某些故障存在的情况下，可能无法设置此控制。参见 V4L2_CID_FLASH_FAULT
``V4L2_CID_FLASH_STROBE_STOP (按钮)``
    立即停止闪光
``V4L2_CID_FLASH_STROBE_STATUS (布尔值)``
    闪光状态：当前是否正在闪光
这是一个只读控制
``V4L2_CID_FLASH_TIMEOUT (integer)``
    闪光灯硬件超时时间。从闪光开始后经过此时间段，闪光将停止。

``V4L2_CID_FLASH_INTENSITY (integer)``
    当闪光灯处于闪光模式（V4L2_FLASH_LED_MODE_FLASH）时的闪光强度。单位应为毫安（mA），如果可能的话。

``V4L2_CID_FLASH_TORCH_INTENSITY (integer)``
    在手电筒模式（V4L2_FLASH_LED_MODE_TORCH）下闪光灯的强度。单位应为毫安（mA），如果可能的话。在某些故障存在的情况下，可能无法设置此控制。请参见 V4L2_CID_FLASH_FAULT。

``V4L2_CID_FLASH_INDICATOR_INTENSITY (integer)``
    指示灯的强度。指示灯可能完全独立于闪光灯。单位应为微安（uA），如果可能的话。

``V4L2_CID_FLASH_FAULT (bitmask)``
    与闪光灯相关的故障。这些故障会告知关于闪光芯片本身或连接到它的LED的具体问题。故障可能会阻止使用某些闪光控制。特别是，如果故障影响了闪光灯，则 V4L2_CID_FLASH_LED_MODE 将被设置为 V4L2_FLASH_LED_MODE_NONE。具体哪些故障有这种效果取决于芯片。读取故障会重置控制，并尽可能使芯片恢复到可用状态。

.. tabularcolumns:: |p{8.4cm}|p{9.1cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_FLASH_FAULT_OVER_VOLTAGE``
      - 闪光控制器对闪光灯的电压超过了特定于闪光控制器的限制。
      
    * - ``V4L2_FLASH_FAULT_TIMEOUT``
      - 闪光在用户设定的超时时间（由 V4L2_CID_FLASH_TIMEOUT 控制）到期时仍未关闭。并非所有闪光控制器在所有条件下都会设置此故障。
      
    * - ``V4L2_FLASH_FAULT_OVER_TEMPERATURE``
      - 闪光控制器过热。
      
    * - ``V4L2_FLASH_FAULT_SHORT_CIRCUIT``
      - 闪光控制器的短路保护已被触发。
      
    * - ``V4L2_FLASH_FAULT_OVER_CURRENT``
      - LED电源中的电流超过了特定于闪光控制器的限制。
* - ``V4L2_FLASH_FAULT_INDICATOR``
      - 闪光控制器检测到指示灯上的短路或开路情况
* - ``V4L2_FLASH_FAULT_UNDER_VOLTAGE``
      - 闪光控制器对闪光灯的供电电压低于特定于该控制器的最小限制
* - ``V4L2_FLASH_FAULT_INPUT_VOLTAGE``
      - 闪光控制器的输入电压低于使闪光灯在全电流下闪烁所需的最低电压。此状态将持续到此标志不再被设置为止
* - ``V4L2_FLASH_FAULT_LED_OVER_TEMPERATURE``
      - LED 的温度超过了允许的上限

``V4L2_CID_FLASH_CHARGE (布尔型)``
    启用或禁用氙气闪光电容器的充电

``V4L2_CID_FLASH_READY (布尔型)``
    闪光是否准备好进行闪烁？氙气闪光需要先给其电容器充电才能闪烁。LED 闪光通常在闪烁后需要一段冷却时间，在此期间无法再次闪烁。这是一个只读控制。
