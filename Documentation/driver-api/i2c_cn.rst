I\ :sup:`2`\ C 和 SMBus 子系统
=============================

I\ :sup:`2`\ C（或者不使用花哨的排版，即“I2C”）是“Inter-IC”总线的缩写，这是一种广泛用于低数据速率通信的简单总线协议。由于它也是一个注册商标，一些供应商可能会使用另一个名称（例如“双线接口”，TWI）来指代相同的总线。I2C只需要两个信号（SCL用于时钟，SDA用于数据），这节省了电路板空间并减少了信号质量问题。大多数I2C设备使用七位地址，并且总线速度最高可达400kHz；存在一个高速扩展（3.4MHz），但尚未得到广泛应用。I2C是一种多主控总线；采用开漏信号来仲裁多个主控器之间的通信，同时也用于握手和从较慢客户端同步时钟。

Linux的I2C编程接口支持总线交互的主控端和从属端。编程接口围绕两种类型的驱动程序和两种类型的设备构建。I2C“适配器驱动程序”抽象出控制器硬件；它绑定到一个物理设备（可能是PCI设备或平台设备），并为它管理的每个I2C总线段暴露一个 :c:type:`struct i2c_adapter <i2c_adapter>` 。在每个I2C总线段上都会有由 :c:type:`struct i2c_client <i2c_client>` 表示的I2C设备。这些设备将绑定到一个 :c:type:`struct i2c_driver <i2c_driver>` ，该驱动应遵循标准的Linux驱动模型。有各种函数可以执行不同的I2C协议操作；截至目前，所有这样的函数只能在任务上下文中使用。

系统管理总线（SMBus）是一种类似协议。大多数SMBus系统也符合I2C标准。对于SMBus，电气约束更严格，并且它标准化了一些特定的协议消息和习惯用法。支持I2C的控制器也可以支持大多数SMBus操作，但是SMBus控制器并不支持I2C控制器的所有协议选项。有各种函数可以执行不同的SMBus协议操作，要么使用I2C原语，要么通过向不支持这些I2C操作的i2c_adapter设备发送SMBus命令来实现。

.. kernel-doc:: include/linux/i2c.h
   :internal:

.. kernel-doc:: drivers/i2c/i2c-boardinfo.c
   :functions: i2c_register_board_info

.. kernel-doc:: drivers/i2c/i2c-core-base.c
   :export:

.. kernel-doc:: drivers/i2c/i2c-core-smbus.c
   :export:
