SPDX 许可声明标识符: GPL-2.0

====================================
Linux 下的多色 LED 控制
====================================

描述
===========
多色类将单色 LED 组合在一起，并允许控制最终组合颜色的两个方面：色调和亮度。前者通过 multi_intensity 数组文件进行控制，后者通过 brightness 文件进行控制。

多色类控制
========================
多色类呈现了将颜色作为数组中的索引分组的文件。这些文件是 LED 父节点下的子文件，该父节点由 led_class 框架创建。关于 led_class 框架的文档可以在本目录中的 led-class.rst 找到。
每个彩色 LED 将在 multi_* 文件中被索引。颜色的顺序是任意的。可以通过读取 multi_index 文件来确定颜色名称对应的索引值。
multi_index 文件是一个包含颜色字符串列表的数组，这些颜色按 multi_* 数组文件定义的方式排列。
multi_intensity 是一个可以读取或写入的数组，用于设置各个颜色的强度。此数组中的所有元素必须按顺序写入，以更新彩色 LED 的强度。

目录布局示例
========================
root:/sys/class/leds/multicolor:status# ls -lR
-rw-r--r--    1 root     root          4096 Oct 19 16:16 brightness
-r--r--r--    1 root     root          4096 Oct 19 16:16 max_brightness
-r--r--r--    1 root     root          4096 Oct 19 16:16 multi_index
-rw-r--r--    1 root     root          4096 Oct 19 16:16 multi_intensity

多色类亮度控制
===================================
每个 LED 的亮度级别是基于彩色 LED 强度设置除以全局最大亮度设置再乘以请求的亮度计算得出的。
led_brightness = brightness * multi_intensity / max_brightness

示例：
用户首先向 multi_intensity 文件写入每个 LED 必须达到某种颜色输出所需的亮度级别。
cat /sys/class/leds/multicolor:status/multi_index
green blue red

echo 43 226 138 > /sys/class/leds/multicolor:status/multi_intensity

红色：
    强度 = 138
    最大亮度 = 255
绿色：
    强度 = 43
    最大亮度 = 255
蓝色：
    强度 = 226
    最大亮度 = 255

用户可以通过写入全局的 'brightness' 控制来调整该多色 LED 组的亮度。假设最大亮度为 255，用户可能希望将 LED 颜色组调暗一半。用户可以向全局 brightness 文件写入一个值 128，然后每个 LED 的值将根据这个值进行调整。
cat /sys/class/leds/multicolor:status/max_brightness
255
echo 128 > /sys/class/leds/multicolor:status/brightness

调整后的红色值 = 128 * 138 / 255 = 69
调整后的绿色值 = 128 * 43 / 255 = 21
调整后的蓝色值 = 128 * 226 / 255 = 113

读取全局 brightness 文件将返回当前多色 LED 组的亮度值。
cat /sys/class/leds/multicolor:status/brightness
128
