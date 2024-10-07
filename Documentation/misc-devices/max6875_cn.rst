=====================
内核驱动程序 max6875
=====================

支持的芯片：

  * Maxim MAX6874, MAX6875

    前缀: 'max6875'

    扫描地址: 无（见下文）

    数据手册: http://pdfserv.maxim-ic.com/en/ds/MAX6874-MAX6875.pdf

作者: Ben Gardner <bgardner@wabtec.com>

描述
-----------

Maxim MAX6875 是一个 EEPROM 可编程电源排序器/监视器。
它提供了定时输出，如果正确接线，可以作为看门狗使用。
它还提供 512 字节的用户 EEPROM 存储空间。
在复位时，MAX6875 会将配置 EEPROM 的内容读入其配置寄存器中。然后根据寄存器中的值开始运行。
Maxim MAX6874 是一种类似且大部分兼容的设备，具有更多的输入和输出：

===========  ===     ===    ====
-            vin     gpi    vout
===========  ===     ===    ====
MAX6874        6       4       8
MAX6875        4       3       5
===========  ===     ===    ====

更多信息请参阅数据手册。

Sysfs 条目
-------------

eeprom        - 512 字节的用户定义 EEPROM 空间

一般说明
---------------

MAX6875 的有效地址是 0x50 和 0x52。
MAX6874 的有效地址是 0x50、0x52、0x54 和 0x56。
该驱动程序不会探测任何地址，因此需要显式实例化设备。
示例::

  $ modprobe max6875
  $ echo max6875 0x50 > /sys/bus/i2c/devices/i2c-0/new_device

MAX6874/MAX6875 忽略地址位 0，因此此驱动程序可以连接到多个地址。例如，对于地址 0x50，它还会预留 0x51。
偶地址实例称为 'max6875'，奇地址实例称为 'dummy'

使用 i2c-dev 接口编程芯片
----------------------------

使用 i2c-dev 接口访问和编程芯片
读写操作根据地址范围有所不同
配置寄存器位于地址 0x00 - 0x45
使用 `i2c_smbus_write_byte_data()` 写入寄存器，
使用 `i2c_smbus_read_byte_data()` 读取寄存器
命令是寄存器编号
示例：

向寄存器 0x45 写入 1 的方法如下：

```c
i2c_smbus_write_byte_data(fd, 0x45, 1);
```

读取寄存器 0x45 的方法如下：

```c
value = i2c_smbus_read_byte_data(fd, 0x45);
```

配置 EEPROM 位于地址 0x8000 - 0x8045
用户 EEPROM 位于地址 0x8100 - 0x82ff
使用 `i2c_smbus_write_word_data()` 向 EEPROM 写入一个字节
命令是地址的高字节：0x80、0x81 或 0x82
数据字是地址的低位部分与数据左移8位进行或运算：

```c
cmd = address >> 8;
val = (address & 0xff) | (data << 8);
```

示例：

将0x5a写入地址0x8003：

```c
i2c_smbus_write_word_data(fd, 0x80, 0x5a03);
```

从EEPROM读取数据稍微复杂一些。
使用`i2c_smbus_write_byte_data()`设置读取地址，然后使用`i2c_smbus_read_byte()`或`i2c_smbus_read_i2c_block_data()`读取数据。

示例：

从偏移量0x8100开始读取数据时，首先设置地址：

```c
i2c_smbus_write_byte_data(fd, 0x81, 0x00);
```

然后读取数据：

```c
value = i2c_smbus_read_byte(fd);
```

或者：

```c
count = i2c_smbus_read_i2c_block_data(fd, 0x84, 16, buffer);
```

块读取应读取16个字节。
0x84是块读取命令。
更多详细信息请参阅数据手册。
