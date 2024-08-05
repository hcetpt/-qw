=============================
USB 7 段数字显示器
=============================

制造商：Delcom Engineering

设备信息
------------------
USB 厂商ID	0x0fc5
USB 产品ID	0x1227
6 位字符和 8 位字符显示器都有产品 ID，
根据 Delcom Engineering 的说法，无法从设备获取可查询的信息来区分它们。
设备模式
------------
默认情况下，驱动程序假设显示器只有 6 个字符
6 位字符的模式为：

	最高字节 MSB 0x06；最低字节 LSB 0x3f

对于 8 位字符显示器：

	最高字节 MSB 0x08；最低字节 LSB 0xff

设备可以接受“文本”，无论是原始模式、十六进制还是 ASCII 文本模式
原始模式手动控制每个段落，
十六进制模式期望每个字符的值在 0-15 之间，
ASCII 模式期望值在 '0'-'9' 和 'A'-'F' 之间
默认模式是 ASCII
设备操作
----------------
1. 打开设备：
	echo 1 > /sys/bus/usb/.../powered
2. 设置设备模式：
	echo $mode_msb > /sys/bus/usb/.../mode_msb
	echo $mode_lsb > /sys/bus/usb/.../mode_lsb
3. 设置文本模式：
	echo $textmode > /sys/bus/usb/.../textmode
4. 设置文本（例如）：
	echo "123ABC" > /sys/bus/usb/.../text (ASCII)
	echo "A1B2" > /sys/bus/usb/.../text (ASCII)
	echo -ne "\x01\x02\x03" > /sys/bus/usb/.../text (十六进制)
5. 设置小数点
设备有 6 或 8 个小数点
要设置第 n 个小数点，请计算 10 的 n 次方
	并将结果写入到 /sys/bus/usb/.../decimals
	要设置多个小数点，请将每个指数相加
例如，要设置第 0 个和第 3 个小数点
	echo 1001 > /sys/bus/usb/.../decimals
