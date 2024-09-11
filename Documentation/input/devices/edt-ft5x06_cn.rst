EDT ft5x06 基于 Polytouch 设备
----------------------------------

EDT "Polytouch" 系列电容式触摸屏的驱动程序 edt-ft5x06 非常有用。请注意，该驱动程序不适合基于 Focaltech ft5x06 的其他设备，因为它们包含特定厂商的固件。特别是，此驱动程序不适合 Nook 平板电脑。它已经在以下设备上进行了测试：
  * EP0350M06
  * EP0430M06
  * EP0570M06
  * EP0700M06

该驱动程序通过一组 sysfs 文件来配置触摸屏：

/sys/class/input/eventX/device/device/threshold:
    允许在 0 到 80 的范围内设置“点击”阈值
/sys/class/input/eventX/device/device/gain:
    允许在 0 到 31 的范围内设置灵敏度。注意，较低的值表示更高的灵敏度
/sys/class/input/eventX/device/device/offset:
    允许在 0 到 31 的范围内设置边缘补偿
/sys/class/input/eventX/device/device/report_rate:
    允许在 3 到 14 的范围内设置报告率

为了调试目的，如果内核中存在调试文件系统，该驱动程序会在调试文件系统中提供一些文件。在 /sys/kernel/debug/edt_ft5x06 中，您会找到以下文件：

num_x, num_y:
    （只读）包含 X 方向和 Y 方向上传感器字段的数量
mode:
    通过写入 "1" 或 "0" 可以在“工厂模式”和“操作模式”之间切换传感器。在工厂模式（1）下，可以获取传感器的原始数据。请注意，在工厂模式下不会传递常规事件，并且上述选项不可用
raw_data:
    包含 num_x * num_y 大小端 16 位值，描述每个传感器字段的原始值。请注意，每次对此文件进行读取调用时都会触发一个新的读取操作。建议提供一个足够大的缓冲区来容纳 num_x * num_y * 2 字节的数据

请注意，当设备不在工厂模式时，读取 raw_data 会导致 I/O 错误。同样地，当设备不在常规操作模式时，对参数文件进行读取或写入也会导致同样的问题。
