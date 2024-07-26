I2C/SMBus 功能
=======================

简介
------------

由于并非每个 I2C 或 SMBus 适配器都实现了 I2C 规范中的所有功能，因此当客户端有选项连接到适配器时，它不能信任所需的所有功能都已实现：客户端需要某种方式来检查适配器是否具有所需的功功能。

功能常量
-----------------------

对于最新版本的功能常量列表，请查阅 `<uapi/linux/i2c.h>`！

  =============================== ==============================================
  I2C_FUNC_I2C                    纯粹的 I2C 级别命令（纯 SMBus 适配器通常无法执行这些命令）
  I2C_FUNC_10BIT_ADDR             处理 10 位地址扩展
  I2C_FUNC_PROTOCOL_MANGLING      知道 I2C_M_IGNORE_NAK、I2C_M_REV_DIR_ADDR 和 I2C_M_NO_RD_ACK 标志（这些标志修改了 I2C 协议！）
  I2C_FUNC_NOSTART                可以跳过重复的启动序列
  I2C_FUNC_SMBUS_QUICK            处理 SMBus write_quick 命令
  I2C_FUNC_SMBUS_READ_BYTE        处理 SMBus read_byte 命令
  I2C_FUNC_SMBUS_WRITE_BYTE       处理 SMBus write_byte 命令
  I2C_FUNC_SMBUS_READ_BYTE_DATA   处理 SMBus read_byte_data 命令
  I2C_FUNC_SMBUS_WRITE_BYTE_DATA  处理 SMBus write_byte_data 命令
  I2C_FUNC_SMBUS_READ_WORD_DATA   处理 SMBus read_word_data 命令
  I2C_FUNC_SMBUS_WRITE_WORD_DATA  处理 SMBus write_word_data 命令
  I2C_FUNC_SMBUS_PROC_CALL        处理 SMBus process_call 命令
  I2C_FUNC_SMBUS_READ_BLOCK_DATA  处理 SMBus read_block_data 命令
  I2C_FUNC_SMBUS_WRITE_BLOCK_DATA 处理 SMBus write_block_data 命令
  I2C_FUNC_SMBUS_READ_I2C_BLOCK   处理 SMBus read_i2c_block_data 命令
  I2C_FUNC_SMBUS_WRITE_I2C_BLOCK  处理 SMBus write_i2c_block_data 命令
  =============================== ==============================================

为了方便起见，还定义了一些上述标志的组合：

  =========================       ======================================
  I2C_FUNC_SMBUS_BYTE             处理 SMBus read_byte 和 write_byte 命令
  I2C_FUNC_SMBUS_BYTE_DATA        处理 SMBus read_byte_data 和 write_byte_data 命令
  I2C_FUNC_SMBUS_WORD_DATA        处理 SMBus read_word_data 和 write_word_data 命令
  I2C_FUNC_SMBUS_BLOCK_DATA       处理 SMBus read_block_data 和 write_block_data 命令
  I2C_FUNC_SMBUS_I2C_BLOCK        处理 SMBus read_i2c_block_data 和 write_i2c_block_data 命令
  I2C_FUNC_SMBUS_EMUL             处理所有 SMBus 命令，这些命令可以由真实的 I2C 适配器通过透明模拟层来模拟
  =========================       ======================================

在内核版本 3.5 之前，I2C_FUNC_NOSTART 是作为 I2C_FUNC_PROTOCOL_MANGLING 的一部分实现的。

适配器实现
----------------------

当你编写一个新的适配器驱动程序时，你将需要实现一个回调函数 `functionality`。下面给出一些典型的实现示例。

一个典型的仅 SMBus 适配器会列出其支持的所有 SMBus 交易。以下示例来自 i2c-piix4 驱动程序：

  ```c
  static u32 piix4_func(struct i2c_adapter *adapter)
  {
	return I2C_FUNC_SMBUS_QUICK | I2C_FUNC_SMBUS_BYTE |
	       I2C_FUNC_SMBUS_BYTE_DATA | I2C_FUNC_SMBUS_WORD_DATA |
	       I2C_FUNC_SMBUS_BLOCK_DATA;
  }
  ```

一个典型的全 I2C 适配器会使用以下内容（来自 i2c-pxa 驱动程序）：

  ```c
  static u32 i2c_pxa_functionality(struct i2c_adapter *adap)
  {
	return I2C_FUNC_I2C | I2C_FUNC_SMBUS_EMUL;
  }
  ```

I2C_FUNC_SMBUS_EMUL 包括所有 SMBus 交易（加上 I2C 块交易），这些交易可以通过 I2C_FUNC_I2C 由 i2c-core 在没有适配器驱动程序帮助的情况下进行模拟。其目的是让客户端驱动程序检查 SMBus 功能的支持，而无需关心这些功能是由底层适配器硬件实现的还是由 i2c-core 在 I2C 适配器之上用软件模拟的。

客户端检查
---------------

在客户端尝试连接到适配器之前，甚至在测试适配器上是否存在它支持的设备之前，它应该检查所需的功功能是否可用。典型的做法是（来自 lm75 驱动程序）：

  ```c
  static int lm75_detect(...)
  {
	(...)
	if (!i2c_check_functionality(adapter, I2C_FUNC_SMBUS_BYTE_DATA |
				     I2C_FUNC_SMBUS_WORD_DATA))
		goto exit;
	(...)
  }
  ```

在这里，lm75 驱动程序检查适配器是否能处理 SMBus 字节数据和 SMBus 字数据交易。如果不可以，那么该驱动程序将无法在这个适配器上工作，就没有必要继续下去。如果上述检查成功，那么驱动程序就知道它可以调用以下函数：i2c_smbus_read_byte_data()、i2c_smbus_write_byte_data()、i2c_smbus_read_word_data() 和 i2c_smbus_write_word_data()。一般而言，您通过 i2c_check_functionality() 测试的功能常量应与您的驱动程序调用的 i2c_smbus_* 函数完全匹配。

请注意，上述检查并不能说明这些功能是由底层适配器硬件实现的还是由 i2c-core 用软件模拟的。客户端驱动程序不必关心这一点，因为 i2c-core 将透明地在 I2C 适配器之上实现 SMBus 交易。

通过 /dev 检查
---------------------

如果您试图从用户空间程序访问适配器，您将必须使用 /dev 接口。当然，您仍然需要检查您需要的功能是否得到支持。这是通过 I2C_FUNCS ioctl 完成的。下面是从 i2cdetect 程序改编的一个示例：

  ```c
  int file;
  if ((file = open("/dev/i2c-0", O_RDWR)) < 0) {
	/* 进行某种错误处理 */
	exit(1);
  }
  if (ioctl(file, I2C_FUNCS, &funcs) < 0) {
	/* 进行某种错误处理 */
	exit(1);
  }
  if (!(funcs & I2C_FUNC_SMBUS_QUICK)) {
	/* 哎呀，所需的功功能（SMBus write_quick 函数）不可用！ */
	exit(1);
  }
  /* 现在可以安全地使用 SMBus write_quick 命令 */
  ```
