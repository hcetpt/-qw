============================
内核驱动 i2c-nvidia-gpu
============================

数据手册：未公开
作者：
	Ajay Gupta <ajayg@nvidia.com>

描述
-----------

i2c-nvidia-gpu 是一个为 NVIDIA Turing 及以后的 GPU 中包含的 I2C 控制器设计的驱动程序，它用于与 GPU 上的 Type-C 控制器通信。
如果你运行 `lspci -v` 显示的内容类似如下所示：

  01:00.3 串行总线控制器 [0c80]: NVIDIA 公司 设备 1ad9 (rev a1)

那么此驱动应该支持你的 GPU 的 I2C 控制器。
