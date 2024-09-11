SPDX 许可证标识符: GPL-2.0

================
ADIS16475 驱动程序
================

此驱动程序支持 SPI 总线上的 Analog Devices 的 IMU（惯性测量单元）。
1. 支持的设备
====================

* `ADIS16465 <https://www.analog.com/ADIS16465>`_
* `ADIS16467 <https://www.analog.com/ADIS16467>`_
* `ADIS16470 <https://www.analog.com/ADIS16470>`_
* `ADIS16475 <https://www.analog.com/ADIS16475>`_
* `ADIS16477 <https://www.analog.com/ADIS16477>`_
* `ADIS16500 <https://www.analog.com/ADIS16500>`_
* `ADIS16505 <https://www.analog.com/ADIS16505>`_
* `ADIS16507 <https://www.analog.com/ADIS16507>`_

每个支持的设备都是一个高精度、微型微机电系统（MEMS）惯性测量单元（IMU），其中包括三轴陀螺仪和三轴加速度计。IMU 中的每个惯性传感器都结合了信号调理功能，以优化动态性能。工厂校准对每个传感器的灵敏度、偏置、对齐、线性加速度（陀螺仪偏置）和敲击点（加速度计位置）进行了表征。因此，每个传感器都有动态补偿公式，可以在广泛的条件下提供准确的传感器测量结果。

2. 设备属性
====================

加速度计和陀螺仪的测量值始终提供。此外，驱动程序还提供了获取由设备计算出的角度增量和速度增量测量值的能力。角度增量测量表示每次采样更新之间的角位移计算，而速度增量测量表示每次采样更新之间的线性速度变化计算。最后，温度数据提供了IMU设备内部粗略的温度测量值，这些数据对于监控热环境的相对变化非常有用。

每个惯性传感器（加速度计和陀螺仪）的信号链包括应用独特的校正公式，这些公式是从在−40°C到+85°C的温度范围内对偏置、灵敏度、对齐、线性加速度（陀螺仪）和敲击点（加速度计位置）进行广泛表征后得出的。虽然这些校正公式不可访问，但用户有机会通过 `calibbias` 属性单独调整每个传感器的偏置。

每个 IIO 设备，在 `/sys/bus/iio/devices/iio:deviceX` 下有一个设备文件夹，其中 X 是该设备的 IIO 索引。在这些文件夹中包含了一系列设备文件，具体取决于硬件设备的特性和功能。这些文件在 IIO ABI 文档中有统一的通用化和文档记录。

下表展示了位于特定设备文件夹路径 `/sys/bus/iio/devices/iio:deviceX` 中的与 ADIS16475 相关的设备文件：

**三轴加速度计相关的设备文件**

| 文件名 | 描述 |
| --- | --- |
| `in_accel_scale` | 加速度计通道的缩放系数 |
| `in_accel_x_calibbias` | X 轴加速度计通道的校准偏置 |
| `in_accel_x_raw` | X 轴加速度计通道的原始值 |
| `in_accel_y_calibbias` | Y 轴加速度计通道的校准偏置 |
| `in_accel_y_raw` | Y 轴加速度计通道的原始值 |
| `in_accel_z_calibbias` | Z 轴加速度计通道的校准偏置 |
| `in_accel_z_raw` | Z 轴加速度计通道的原始值 |
| `in_deltavelocity_scale` | 速度增量通道的缩放系数 |
| `in_deltavelocity_x_raw` | X 轴速度增量通道的原始值 |
| `in_deltavelocity_y_raw` | Y 轴速度增量通道的原始值 |
| `in_deltavelocity_z_raw` | Z 轴速度增量通道的原始值 |

**三轴陀螺仪相关的设备文件**

| 文件名 | 描述 |
| --- | --- |
| `in_anglvel_scale` | 陀螺仪通道的缩放系数 |
| `in_anglvel_x_calibbias` | X 轴陀螺仪通道的校准偏置 |
| `in_anglvel_x_raw` | X 轴陀螺仪通道的原始值 |
| `in_anglvel_y_calibbias` | Y 轴陀螺仪通道的校准偏置 |
| `in_anglvel_y_raw` | Y 轴陀螺仪通道的原始值 |
| `in_anglvel_z_calibbias` | Z 轴陀螺仪通道的校准偏置 |
| `in_anglvel_z_raw` | Z 轴陀螺仪通道的原始值 |
| `in_deltaangl_scale` | 角度增量通道的缩放系数 |
| `in_deltaangl_x_raw` | X 轴角度增量通道的原始值 |
| `in_deltaangl_y_raw` | Y 轴角度增量通道的原始值 |
| `in_deltaangl_z_raw` | Z 轴角度增量通道的原始值 |

**温度传感器相关的文件**

| 文件名 | 描述 |
| --- | --- |
| `in_temp0_raw` | 温度通道的原始值 |
| `in_temp0_scale` | 温度传感器通道的缩放系数 |

**其他设备文件**

| 文件名 | 描述 |
| --- | --- |
| `name` | IIO 设备的名称 |
| `sampling_frequency` | 当前选择的采样率 |
| `filter_low_pass_3db_frequency` | 加速度计和陀螺仪通道的带宽 |

**调试文件**

以下表格展示了位于特定设备调试文件夹路径 `/sys/kernel/debug/iio/iio:deviceX` 中的与 ADIS16475 相关的调试文件：

| 文件名 | 描述 |
| --- | --- |
| `serial_number` | 芯片的十六进制格式序列号 |
| `product_id` | 芯片特定的产品 ID（例如 16475, 16500, 16505 等） |
| `flash_count` | 在设备上执行的闪存写入次数 |
| `firmware_revision` | 包含固件版本的字符串，格式为 `##.##` |
| `firmware_date` | 包含固件日期的字符串，格式为 `mm-dd-yyyy` |

处理后的通道值
-------------------------

可以通过读取其 `_raw` 属性来获取一个通道的值。返回的值是设备报告的原始值。要获取通道的处理值，请应用以下公式：

```bash
processed value = (_raw + _offset) * _scale
```

其中 `_offset` 和 `_scale` 是设备属性。如果没有 `_offset` 属性，则假设其值为 0。
adis16475驱动程序提供了5种类型通道的数据，下表展示了处理值的测量单位，这些单位由IIO框架定义：

+-------------------------------------+---------------------------+
| 通道类型                            | 测量单位                  |
+-------------------------------------+---------------------------+
| X、Y 和 Z 轴上的加速度              | 米每平方秒                |
+-------------------------------------+---------------------------+
| X、Y 和 Z 轴上的角速度              | 弧度每秒                  |
+-------------------------------------+---------------------------+
| X、Y 和 Z 轴上的速度变化            | 米每秒                    |
+-------------------------------------+---------------------------+
| X、Y 和 Z 轴上的角度变化            | 弧度                      |
+-------------------------------------+---------------------------+
| 温度                               | 毫度摄氏度                |
+-------------------------------------+---------------------------+

使用示例
--------

显示设备名称：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> cat name
	adis16505-2

显示加速度计通道值：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> cat in_accel_x_raw
	-275924
	root:/sys/bus/iio/devices/iio:device0> cat in_accel_y_raw
	-30142222
	root:/sys/bus/iio/devices/iio:device0> cat in_accel_z_raw
	261265769
	root:/sys/bus/iio/devices/iio:device0> cat in_accel_scale
	0.000000037

- X轴加速度 = in_accel_x_raw * in_accel_scale = −0.010209188 m/s^2
- Y轴加速度 = in_accel_y_raw * in_accel_scale = −1.115262214 m/s^2
- Z轴加速度 = in_accel_z_raw * in_accel_scale = 9.666833453 m/s^2

显示陀螺仪通道值：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> cat in_anglvel_x_raw
	-3324626
	root:/sys/bus/iio/devices/iio:device0> cat in_anglvel_y_raw
	1336980
	root:/sys/bus/iio/devices/iio:device0> cat in_anglvel_z_raw
	-602983
	root:/sys/bus/iio/devices/iio:device0> cat in_anglvel_scale
	0.000000006

- X轴角速度 = in_anglvel_x_raw * in_anglvel_scale = −0.019947756 rad/s
- Y轴角速度 = in_anglvel_y_raw * in_anglvel_scale = 0.00802188 rad/s
- Z轴角速度 = in_anglvel_z_raw * in_anglvel_scale = −0.003617898 rad/s

设置加速度计通道的校准偏移：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> cat in_accel_x_calibbias
	0

	root:/sys/bus/iio/devices/iio:device0> echo 5000 > in_accel_x_calibbias
	root:/sys/bus/iio/devices/iio:device0> cat in_accel_x_calibbias
	5000

设置陀螺仪通道的校准偏移：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> cat in_anglvel_y_calibbias
	0

	root:/sys/bus/iio/devices/iio:device0> echo -5000 > in_anglvel_y_calibbias
	root:/sys/bus/iio/devices/iio:device0> cat in_anglvel_y_calibbias
	-5000

设置采样频率：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> cat sampling_frequency
	2000.000000

	root:/sys/bus/iio/devices/iio:device0> echo 1000 > sampling_frequency
	1000.000000

设置加速度计和陀螺仪的带宽：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> cat filter_low_pass_3db_frequency
	720

	root:/sys/bus/iio/devices/iio:device0> echo 360 > filter_low_pass_3db_frequency
	root:/sys/bus/iio/devices/iio:device0> cat filter_low_pass_3db_frequency
	360

显示序列号：

.. code-block:: bash

	root:/sys/kernel/debug/iio/iio:device0> cat serial_number
	0x04f9

显示产品ID：

.. code-block:: bash

	root:/sys/kernel/debug/iio/iio:device0> cat product_id
	16505

显示闪存计数：

.. code-block:: bash

	root:/sys/kernel/debug/iio/iio:device0> cat flash_count
	150

显示固件版本：

.. code-block:: bash

	root:/sys/kernel/debug/iio/iio:device0> cat firmware_revision
	1.6

显示固件日期：

.. code-block:: bash

	root:/sys/kernel/debug/iio/iio:device0> cat firmware_date
	06-27-2019

3. 设备缓冲区
==============

此驱动程序支持IIO缓冲区
所有设备都支持使用缓冲区获取原始加速度、陀螺仪和温度测量数据
以下设备家族还支持使用缓冲区获取速度变化、角度变化和温度测量数据：

- ADIS16477
- ADIS16500
- ADIS16505
- ADIS16507

但是，当使用缓冲区获取加速度或陀螺仪数据时，速度变化读数将不可用，反之亦然。

使用示例
--------

如果尚未设置设备触发器，则在current_trigger中设置设备触发器：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> cat trigger/current_trigger

	root:/sys/bus/iio/devices/iio:device0> echo adis16505-2-dev0 > trigger/current_trigger
	root:/sys/bus/iio/devices/iio:device0> cat trigger/current_trigger
	adis16505-2-dev0

选择要用于缓冲区读取的通道：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> echo 1 > scan_elements/in_deltavelocity_x_en
	root:/sys/bus/iio/devices/iio:device0> echo 1 > scan_elements/in_deltavelocity_y_en
	root:/sys/bus/iio/devices/iio:device0> echo 1 > scan_elements/in_deltavelocity_z_en
	root:/sys/bus/iio/devices/iio:device0> echo 1 > scan_elements/in_temp0_en

设置要存储在缓冲区中的样本数量：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> echo 10 > buffer/length

启用缓冲区读取：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> echo 1 > buffer/enable

获取缓冲区数据：

.. code-block:: bash

	root:/sys/bus/iio/devices/iio:device0> hexdump -C /dev/iio:device0
	..
00001680  01 1f 00 00 ff ff fe ef  00 00 47 bf 00 03 35 55  |..........G...5U|
	00001690  01 1f 00 00 ff ff ff d9  00 00 46 f1 00 03 35 35  |..........F...55|
	000016a0  01 1f 00 00 ff ff fe fc  00 00 46 cb 00 03 35 7b  |..........F...5{|
	000016b0  01 1f 00 00 ff ff fe 41  00 00 47 0d 00 03 35 8b  |.......A..G...5.|
	000016c0  01 1f 00 00 ff ff fe 37  00 00 46 b4 00 03 35 90  |.......7..F...5.|
	000016d0  01 1d 00 00 ff ff fe 5a  00 00 45 d7 00 03 36 08  |.......Z..E...6.|
	000016e0  01 1b 00 00 ff ff fe fb  00 00 45 e7 00 03 36 60  |..........E...6`|
	000016f0  01 1a 00 00 ff ff ff 17  00 00 46 bc 00 03 36 de  |..........F...6.|
	00001700  01 1a 00 00 ff ff fe 59  00 00 46 d7 00 03 37 b8  |.......Y..F...7.|
	00001710  01 1a 00 00 ff ff fe ae  00 00 46 95 00 03 37 ba  |..........F...7.|
	00001720  01 1a 00 00 ff ff fe c5  00 00 46 63 00 03 37 9f  |..........Fc..7.|
	00001730  01 1a 00 00 ff ff fe 55  00 00 46 89 00 03 37 c1  |.......U..F...7.|
	00001740  01 1a 00 00 ff ff fe 31  00 00 46 aa 00 03 37 f7  |.......1..F...7.|
	..

有关缓冲区数据结构的更多信息，请参阅``Documentation/iio/iio_devbuf.rst``

4. IIO 接口工具
==================

Linux内核工具
--------------

Linux内核提供了一些用户空间工具，可用于从IIO sysfs检索数据：

* lsiio：提供IIO设备和触发器列表的应用示例
* iio_event_monitor：读取IIO设备事件并打印的应用示例
* iio_generic_buffer：从缓冲区读取数据的应用示例
* iio_utils：通常用于访问sysfs文件的一组API

LibIIO
------

LibIIO是一个C/C++库，提供了对IIO设备的通用访问。该库抽象了硬件的低级细节，并提供了一个简单而完整的编程接口，可以用于高级项目。
关于LibIIO的更多信息，请参阅：
https://github.com/analogdevicesinc/libiio
