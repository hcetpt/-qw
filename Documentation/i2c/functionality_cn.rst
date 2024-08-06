I2C/SMBus 功能
=======================

简介
------------

由于并非每个 I2C 或 SMBus 适配器都实现了 I2C 规范中的所有功能，因此客户端在选择连接到某个适配器时不能假定所需的所有功能都已经实现：客户端需要某种方式来检查适配器是否具有所需的必要功能。

功能常量
-----------------------

对于最新的功能常量列表，请查阅 `<uapi/linux/i2c.h>`！

  =============================== ==============================================
  I2C_FUNC_I2C                    纯粹的 I2C 级别命令（纯 SMBus 适配器通常无法执行这些操作）
  I2C_FUNC_10BIT_ADDR             支持 10 位地址扩展
  I2C_FUNC_PROTOCOL_MANGLING      理解 I2C_M_IGNORE_NAK、I2C_M_REV_DIR_ADDR 和 I2C_M_NO_RD_ACK 标志（这些标志修改了 I2C 协议！）
  I2C_FUNC_NOSTART                可以跳过重复启动序列
  I2C_FUNC_SMBUS_QUICK            处理 SMBus 的 write_quick 命令
  I2C_FUNC_SMBUS_READ_BYTE        处理 SMBus 的 read_byte 命令
  I2C_FUNC_SMBUS_WRITE_BYTE       处理 SMBus 的 write_byte 命令
  I2C_FUNC_SMBUS_READ_BYTE_DATA   处理 SMBus 的 read_byte_data 命令
  I2C_FUNC_SMBUS_WRITE_BYTE_DATA  处理 SMBus 的 write_byte_data 命令
  I2C_FUNC_SMBUS_READ_WORD_DATA   处理 SMBus 的 read_word_data 命令
  I2C_FUNC_SMBUS_WRITE_WORD_DATA  处理 SMBus 的 write_word_data 命令
  I2C_FUNC_SMBUS_PROC_CALL        处理 SMBus 的 process_call 命令
  I2C_FUNC_SMBUS_READ_BLOCK_DATA  处理 SMBus 的 read_block_data 命令
  I2C_FUNC_SMBUS_WRITE_BLOCK_DATA 处理 SMBus 的 write_block_data 命令
  I2C_FUNC_SMBUS_READ_I2C_BLOCK   处理 SMBus 的 read_i2c_block_data 命令
  I2C_FUNC_SMBUS_WRITE_I2C_BLOCK  处理 SMBus 的 write_i2c_block_data 命令
  =============================== ==============================================

为了方便起见，还定义了一些上述标志的组合：

  =========================       ======================================
  I2C_FUNC_SMBUS_BYTE             处理 SMBus 的 read_byte 和 write_byte 命令
  I2C_FUNC_SMBUS_BYTE_DATA        处理 SMBus 的 read_byte_data 和 write_byte_data 命令
  I2C_FUNC_SMBUS_WORD_DATA        处理 SMBus 的 read_word_data 和 write_word_data 命令
  I2C_FUNC_SMBUS_BLOCK_DATA       处理 SMBus 的 read_block_data 和 write_block_data 命令
  I2C_FUNC_SMBUS_I2C_BLOCK        处理 SMBus 的 read_i2c_block_data 和 write_i2c_block_data 命令
  I2C_FUNC_SMBUS_EMUL             处理所有可以由真正的 I2C 适配器通过透明模拟层模拟的 SMBus 命令
  =========================       ======================================

在内核版本 3.5 之前，I2C_FUNC_NOSTART 是作为 I2C_FUNC_PROTOCOL_MANGLING 的一部分实现的。

适配器实现
----------------------

当你编写一个新的适配器驱动程序时，你将必须实现一个功能回调 `functionality`。下面提供了一些典型的实现示例。
一个典型的仅 SMBus 的适配器会列出它支持的所有 SMBus 事务。以下示例来自 i2c-piix4 驱动程序：

  static u32 piix4_func(struct i2c_adapter *adapter)
  {
	return I2C_FUNC_SMBUS_QUICK | I2C_FUNC_SMBUS_BYTE |
	       I2C_FUNC_SMBUS_BYTE_DATA | I2C_FUNC_SMBUS_WORD_DATA |
	       I2C_FUNC_SMBUS_BLOCK_DATA;
  }

一个典型的全 I2C 适配器会使用如下设置（摘自 i2c-pxa 驱动程序）：

  static u32 i2c_pxa_functionality(struct i2c_adapter *adap)
  {
	return I2C_FUNC_I2C | I2C_FUNC_SMBUS_EMUL;
  }

I2C_FUNC_SMBUS_EMUL 包括了 i2c-core 可以使用 I2C_FUNC_I2C 无需适配器驱动程序帮助就能模拟的所有 SMBus 事务（增加了 I2C 块事务）。其目的是让客户端驱动程序能够检查 SMBus 功能的支持，而无需关心这些功能是通过适配器硬件实现还是通过 i2c-core 在 I2C 适配器之上通过软件模拟的。

客户端检查
---------------

在客户端尝试连接到适配器之前，甚至在进行测试以检查它所支持的设备是否存在于适配器上之前，它应该检查所需的功能是否存在。典型的检查方法是（摘自 lm75 驱动程序）：

  static int lm75_detect(...)
  {
	(...)
	if (!i2c_check_functionality(adapter, I2C_FUNC_SMBUS_BYTE_DATA |
				     I2C_FUNC_SMBUS_WORD_DATA))
		goto exit;
	(...)
  }

这里，lm75 驱动程序检查适配器是否可以处理 SMBus 字节数据和 SMBus 字数据事务。如果不可以，则该驱动程序在这个适配器上无法工作，没有必要继续进行下去。如果上面的检查成功，则驱动程序知道它可以调用以下函数：i2c_smbus_read_byte_data()、i2c_smbus_write_byte_data()、i2c_smbus_read_word_data() 和 i2c_smbus_write_word_data()。一般而言，您使用 i2c_check_functionality() 检查的功能常量应与您的驱动程序正在调用的 i2c_smbus_* 函数完全匹配。

请注意，上面的检查不会告诉您这些功能是由底层适配器在硬件中实现还是由 i2c-core 在软件中模拟。客户端驱动程序不必关心这一点，因为 i2c-core 会在 I2C 适配器之上透明地实现 SMBus 事务。

通过 /dev 进行检查
---------------------

如果您试图从用户空间程序访问适配器，您将不得不使用 /dev 接口。当然，您仍然需要检查所需的任何功能是否被支持。这是通过使用 I2C_FUNCS ioctl 完成的。下面是一个示例，改编自 i2cdetect 程序：

  int file;
  if ((file = open("/dev/i2c-0", O_RDWR)) < 0) {
	/* 一些错误处理 */
	exit(1);
  }
  if (ioctl(file, I2C_FUNCS, &funcs) < 0) {
	/* 一些错误处理 */
	exit(1);
  }
  if (!(funcs & I2C_FUNC_SMBUS_QUICK)) {
	/* 哎呀，所需的功能（SMBus write_quick 函数）不可用！ */
	exit(1);
  }
  /* 现在可以安全地使用 SMBus write_quick 命令 */
