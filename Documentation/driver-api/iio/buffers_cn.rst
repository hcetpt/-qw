### 缓冲区

* `struct iio_buffer` — 通用缓冲区结构
* `:c:func:`iio_validate_scan_mask_onehot` — 验证恰好选择了一个通道
* `:c:func:`iio_buffer_get` — 获取缓冲区的引用
* `:c:func:`iio_buffer_put` — 释放对缓冲区的引用

工业I/O (Industrial I/O) 核心提供了一种基于触发源进行连续数据捕获的方式。可以从 `/dev/iio:device{X}` 字符设备节点同时读取多个数据通道，从而减少CPU负载。

#### IIO缓冲区sysfs接口
一个IIO缓冲区在其下具有相关的属性目录：`/sys/bus/iio/iio:device{X}/buffer/*`。以下是一些现有的属性：

* `length`，缓冲区能够存储的数据样本（容量）总数
* `enable`，激活缓冲区捕获

#### IIO缓冲区设置
与放置在缓冲区中的通道读数相关联的元信息称为扫描元素。配置扫描元素的重要参数通过 `/sys/bus/iio/iio:device{X}/scan_elements/` 目录暴露给用户空间应用程序。此目录包含如下形式的属性：

* `enable`，用于启用一个通道。如果且仅当其属性非零时，触发式捕获将包含该通道的数据样本
* `index`，通道的扫描索引
* `type`，描述了扫描元素数据在缓冲区内的存储方式以及从用户空间读取的形式。格式为 [be|le]:[s|u]bits/storagebits[Xrepeat][>>shift]
  * *be* 或 *le*，指定大端或小端
  * *s* 或 *u*，指定是否为带符号（二进制补码）或无符号
  * *bits*，有效数据位的数量
* *storagebits*，是指数据在缓冲区中占用的位数（填充后）。
* *repeat*，指定了位数/存储位数的重复次数。当 *repeat* 元素为 0 或 1 时，则省略 *repeat* 的值。
* *shift*，如果指定，是在屏蔽未使用的位之前需要进行的移位操作。

例如，一个 3 轴加速度计驱动，其分辨率为 12 位，数据存储在两个 8 位寄存器中如下所示：

        7   6   5   4   3   2   1   0
      +---+---+---+---+---+---+---+---+
      |D3 |D2 |D1 |D0 | X | X | X | X | （低位字节，地址 0x06）
      +---+---+---+---+---+---+---+---+

        7   6   5   4   3   2   1   0
      +---+---+---+---+---+---+---+---+
      |D11|D10|D9 |D8 |D7 |D6 |D5 |D4 | （高位字节，地址 0x07）
      +---+---+---+---+---+---+---+---+

对于每个轴，其扫描元素类型将是这样的：

      $ cat /sys/bus/iio/devices/iio:device0/scan_elements/in_accel_y_type
      le:s12/16>>4

用户空间的应用程序将把从缓冲区读取的数据样本解释为小端序的两个字节的有符号数据，在屏蔽出 12 位有效数据之前需要进行 4 位右移操作。

为了实现缓冲支持，驱动程序应该初始化以下字段在 `iio_chan_spec` 定义中：

   struct iio_chan_spec {
   /* 其他成员 */
           int scan_index;
           struct {
                   char sign; 
                   u8 realbits;
                   u8 storagebits;
                   u8 shift;
                   u8 repeat;
                   enum iio_endian endianness;
                  } scan_type;
          };

实现上述加速度计的驱动程序将具有以下通道定义：

   struct iio_chan_spec accel_channels[] = {
           {
                   .type = IIO_ACCEL,
		   .modified = 1,
		   .channel2 = IIO_MOD_X,
		   /* 其他内容在这里 */
		   .scan_index = 0,
		   .scan_type = {
		           .sign = 's',
			   .realbits = 12,
			   .storagebits = 16,
			   .shift = 4,
			   .endianness = IIO_LE,
		   },
           }
           /* 对于 Y 轴（channel2 = IIO_MOD_Y, scan_index = 1）
            * 和 Z 轴（channel2 = IIO_MOD_Z, scan_index = 2）类似
            */
    }

这里 **scan_index** 定义了启用的通道在缓冲区中的顺序。**scan_index** 较低的通道将位于较高索引通道之前。每个通道需要有一个唯一的 **scan_index**。

将 **scan_index** 设置为 -1 可以用来表示特定通道不支持缓冲捕获。在这种情况下，不会为此通道在 scan_elements 目录中创建条目。

更多信息
=========
.. kernel-doc:: include/linux/iio/buffer.h
.. kernel-doc:: drivers/iio/industrialio-buffer.c
   :export:
