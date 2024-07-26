SPDX 许可证标识符: GPL-2.0

====================================
Linux 下的多色 LED 控制
====================================

描述
===========
多色类别将单色 LED 组合在一起，并允许控制最终组合颜色的两个方面：色调和亮度。前者通过 `multi_intensity` 数组文件进行控制，而后者则通过 `brightness` 文件进行控制。

多色类控制
========================
多色类别以数组索引的形式呈现颜色。这些文件是 LED 主节点下的子文件，该主节点由 `led_class` 框架创建。关于 `led_class` 框架的文档可以在本目录中的 `led-class.rst` 文件中找到。
每个彩色 LED 都会在 `multi_*` 文件中被索引。颜色的顺序是任意的。可以通过读取 `multi_index` 文件来确定颜色名称与索引值之间的对应关系。
`multi_index` 文件是一个数组，包含了在每个 `multi_*` 数组文件中定义的颜色字符串列表。
`multi_intensity` 是一个可以读取或写入的数组，用于设置各个颜色的强度。为了更新彩色 LED 的强度，必须按顺序写入此数组中的所有元素。

目录布局示例
========================
```
root:/sys/class/leds/multicolor:status# ls -lR
-rw-r--r--    1 root     root          4096 Oct 19 16:16 brightness
-r--r--r--    1 root     root          4096 Oct 19 16:16 max_brightness
-r--r--r--    1 root     root          4096 Oct 19 16:16 multi_index
-rw-r--r--    1 root     root          4096 Oct 19 16:16 multi_intensity
```

多色类亮度控制
===================================
每个 LED 的亮度级别是根据彩色 LED 强度设置除以全局 `max_brightness` 设置再乘以请求的亮度计算得出的。
```
led_brightness = brightness * multi_intensity / max_brightness
```

示例：
用户首先向 `multi_intensity` 文件写入每个 LED 必需的亮度级别，以便从多色 LED 组获得某种特定的颜色输出。
```
cat /sys/class/leds/multicolor:status/multi_index
green blue red
```

```
echo 43 226 138 > /sys/class/leds/multicolor:status/multi_intensity
```

红色 -
	强度 = 138
	max_brightness = 255
绿色 -
	强度 = 43
	max_brightness = 255
蓝色 -
	强度 = 226
	max_brightness = 255

用户可以通过写入全局 `brightness` 控制来调整该多色 LED 组的亮度。假设 `max_brightness` 为 255，用户可能想要将 LED 颜色组调暗至一半亮度。用户可以向全局亮度文件写入一个值 128，然后写入每个 LED 的值会基于这个值进行调整。
```
cat /sys/class/leds/multicolor:status/max_brightness
255
echo 128 > /sys/class/leds/multicolor:status/brightness
```

调整后的红色值 = 128 * 138/255 = 69
调整后的绿色值 = 128 * 43/255 = 21
调整后的蓝色值 = 128 * 226/255 = 113

读取全局亮度文件将返回当前彩色 LED 组的亮度值。
```
cat /sys/class/leds/multicolor:status/brightness
128
```
