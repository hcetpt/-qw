==============================
Linux I2C 从设备 EEPROM 后端
==============================

由 Wolfram Sang <wsa@sang-engineering.com> 在 2014-20 年编写

此后端在连接的 I2C 总线上模拟了一个 EEPROM。用户可以通过位于 sysfs 中的以下文件访问其内存内容：

	/sys/bus/i2c/devices/<device-directory>/slave-eeprom

支持以下类型：24c02、24c32、24c64 和 24c512。也支持只读变体。实例化所需的名称形式为 'slave-<type>[ro]'。下面是一些示例：

24c02，读写，地址 0x64：
  # echo slave-24c02 0x1064 > /sys/bus/i2c/devices/i2c-1/new_device

24c512，只读，地址 0x42：
  # echo slave-24c512ro 0x1042 > /sys/bus/i2c/devices/i2c-1/new_device

如果有一个名为 'firmware-name' 的设备属性包含有效的文件名（仅限 DT 或 ACPI），您还可以在启动时预加载数据。
截至 2015 年，Linux 不支持对二进制 sysfs 文件进行 poll 操作，因此当其他主控制器更改内容时不会收到通知。
