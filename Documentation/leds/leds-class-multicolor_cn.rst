SPDX 许可证标识符：GPL-2.0

====================================
在 Linux 下处理多色 LED
====================================

描述
===========
多色类将单色 LED 分组，并允许控制最终组合颜色的两个方面：色调和亮度。前者通过 multi_intensity 数组文件进行控制，后者通过亮度文件进行控制。

多色类控制
========================
多色类呈现将颜色按数组中的索引分组的文件。这些文件是 LED 父节点下的子文件，该节点由 led_class 框架创建。led_class 框架在本目录中的 led-class.rst 中有文档说明。
每个彩色 LED 都将在 multi_* 文件下被索引。颜色的顺序将是任意的。可以读取 multi_index 文件来确定颜色名称到索引值的映射。
multi_index 文件是一个包含颜色字符串列表的数组，这些颜色按照 multi_* 数组文件中定义的顺序排列。
multi_intensity 是一个数组，可以读取或写入以获取各个颜色的强度。此数组内的所有元素必须按顺序写入，以便更新彩色 LED 的强度。

目录布局示例
========================
root:/sys/class/leds/multicolor:status# ls -lR
-rw-r--r--    1 root     root          4096 Oct 19 16:16 brightness
-r--r--r--    1 root     root          4096 Oct 19 16:16 max_brightness
-r--r--r--    1 root     root          4096 Oct 19 16:16 multi_index
-rw-r--r--    1 root     root          4096 Oct 19 16:16 multi_intensity

多色类亮度控制
===================================
每个 LED 的亮度级别根据彩色 LED 强度设置除以全局 max_brightness 设置再乘以请求的亮度计算得出。
led_brightness = brightness * multi_intensity/max_brightness

示例：
用户首先向 multi_intensity 文件写入每个 LED 的亮度级别，以实现从多色 LED 组获得特定颜色输出。
cat /sys/class/leds/multicolor:status/multi_index
green blue red

echo 43 226 138 > /sys/class/leds/multicolor:status/multi_intensity

红色 -
   强度 = 138
   max_brightness = 255
绿色 -
   强度 = 43
   max_brightness = 255
蓝色 -
   强度 = 226
   max_brightness = 255

用户可以通过写入全局 'brightness' 控制来控制该多色 LED 组的亮度。假设 max_brightness 为 255，用户可能想将 LED 颜色组调暗一半。用户会向全局亮度文件写入 128 的值，然后写入每个 LED 的值将基于此值进行调整。
cat /sys/class/leds/multicolor:status/max_brightness
255
echo 128 > /sys/class/leds/multicolor:status/brightness

调整后的红色值 = 128 * 138/255 = 69
调整后的绿色值 = 128 * 43/255 = 21
调整后的蓝色值 = 128 * 226/255 = 113

读取全局亮度文件将返回彩色 LED 组当前的亮度值。
cat /sys/class/leds/multicolor:status/brightness
128
