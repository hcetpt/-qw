========================
内核驱动 i2c-ocores
========================

支持的适配器：
  * OpenCores.org 的 I2C 控制器，由 Richard Herveille 提供（参见数据手册链接）
    https://opencores.org/project/i2c/overview

作者：Peter Korsgaard <peter@korsgaard.com>

描述
-----------

i2c-ocores 是为 OpenCores.org 的 I2C 控制器 IP 核心由 Richard Herveille 设计的一个 I2C 总线驱动。
使用
-----

i2c-ocores 使用平台总线，因此您需要提供一个包含基地址和中断号的 `struct platform_device`。设备的 `dev.platform_data` 应该指向一个 `struct ocores_i2c_platform_data`（参见 `linux/platform_data/i2c-ocores.h`），其中描述了寄存器之间的距离和输入时钟速度。
还有一种可能，就是附加一个 `i2c_board_info` 列表，当创建 i2c-ocores 驱动时，它会将这些信息添加到总线上。
例如： 

  static struct resource ocores_resources[] = {
	[0] = {
		.start	= MYI2C_BASEADDR,
		.end	= MYI2C_BASEADDR + 8,
		.flags	= IORESOURCE_MEM,
	},
	[1] = {
		.start	= MYI2C_IRQ,
		.end	= MYI2C_IRQ,
		.flags	= IORESOURCE_IRQ,
	},
  };

  /* 可选的板载信息 */
  struct i2c_board_info ocores_i2c_board_info[] = {
	{
		I2C_BOARD_INFO("tsc2003", 0x48),
		.platform_data = &tsc2003_platform_data,
		.irq = TSC_IRQ
	},
	{
		I2C_BOARD_INFO("adv7180", 0x42 >> 1),
		.irq = ADV_IRQ
	}
  };

  static struct ocores_i2c_platform_data myi2c_data = {
	.regstep	= 2,		/* 寄存器之间两个字节 */
	.clock_khz	= 50000,	/* 输入时钟 50MHz */
	.devices	= ocores_i2c_board_info, /* 可选的设备列表 */
	.num_devices	= ARRAY_SIZE(ocores_i2c_board_info), /* 列表大小 */
  };

  static struct platform_device myi2c = {
	.name			= "ocores-i2c",
	.dev = {
		.platform_data	= &myi2c_data,
	},
	.num_resources		= ARRAY_SIZE(ocores_resources),
	.resource		= ocores_resources,
  };
