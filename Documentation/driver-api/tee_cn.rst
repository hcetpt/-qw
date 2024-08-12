SPDX 许可证标识符: GPL-2.0

===============================================
可信执行环境 (TEE) 驱动程序 API
===============================================

内核提供了一个 TEE 总线基础设施，在该基础设施中，可信应用通过全局唯一标识符 (UUID) 标识的设备表示，并且客户端驱动程序注册了支持的设备 UUID 表。TEE 总线基础设施注册了以下 API：

match()：
  遍历客户端驱动程序的 UUID 表以找到与设备 UUID 相对应的匹配项。如果找到匹配项，则通过客户端驱动程序注册的相应 probe API 对该特定设备进行探测。每当设备或客户端驱动程序在 TEE 总线上注册时，都会发生这一过程。
uevent()：
  在新的设备在 TEE 总线上注册时通知用户空间（udev），以便自动加载模块化的客户端驱动程序。
TEE 总线设备枚举特定于底层 TEE 实现，因此留给 TEE 驱动程序提供相应的实现。
然后，TEE 客户端驱动程序可以使用 `include/linux/tee_drv.h` 中列出的 API 与匹配的可信应用通信。

TEE 客户端驱动程序示例
-------------------------
假设一个 TEE 客户端驱动程序需要与具有 UUID `ac6a4085-0e82-4c33-bf98-8eb8e118b6c2` 的可信应用通信，那么驱动程序注册代码片段可能如下所示：

```c
static const struct tee_client_device_id client_id_table[] = {
	{UUID_INIT(0xac6a4085, 0x0e82, 0x4c33,
			   0xbf, 0x98, 0x8e, 0xb8, 0xe1, 0x18, 0xb6, 0xc2)},
	{}
};

MODULE_DEVICE_TABLE(tee, client_id_table);

static struct tee_client_driver client_driver = {
	.id_table	= client_id_table,
	.driver		= {
		.name		= DRIVER_NAME,
		.bus		= &tee_bus_type,
		.probe		= client_probe,
		.remove		= client_remove,
	},
};

static int __init client_init(void)
{
	return driver_register(&client_driver.driver);
}

static void __exit client_exit(void)
{
	driver_unregister(&client_driver.driver);
}

module_init(client_init);
module_exit(client_exit);
```
