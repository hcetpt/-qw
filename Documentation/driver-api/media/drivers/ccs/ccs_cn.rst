SPDX 许可证标识符: 仅 GPL-2.0 或 BSD-3-Clause

.. include:: <isonum.txt>

.. _媒体-ccs-驱动:

MIPI CCS 摄像头传感器驱动
=============================

MIPI CCS 摄像头传感器驱动是一个针对符合 `MIPI CCS <https://www.mipi.org/specifications/camera-command-set>`_ 规范的摄像头传感器的通用驱动。
此外，参见 :ref:`CCS 驱动 UAPI 文档 <媒体-ccs-uapi>`
CCS 静态数据
---------------

MIPI CCS 驱动支持所有符合 CCS 规范的设备的 CCS 静态数据，包括不仅仅限于符合 CCS 1.1 的设备，还包括 CCS 1.0 和 SMIA(++) 设备。
对于 CCS，文件名格式为：

	ccs/ccs-sensor-vvvv-mmmm-rrrr.fw（传感器）和
	ccs/ccs-module-vvvv-mmmm-rrrr.fw（模块）
对于 SMIA++ 符合性设备，相应的文件名为：

	ccs/smiapp-sensor-vv-mmmm-rr.fw（传感器）和
	ccs/smiapp-module-vv-mmmm-rrrr.fw（模块）
对于 SMIA（非++）符合性的设备，静态数据文件名为：

	ccs/smia-sensor-vv-mmmm-rr.fw（传感器）
其中 vvvv 或 vv 分别表示 MIPI 和 SMIA 制造商 ID，mmmm 表示型号 ID，而 rrrr 或 rr 表示修订号。
CCS 工具
~~~~~~~~~

`CCS 工具 <https://github.com/MIPI-Alliance/ccs-tools/>`_ 是一组用于处理 CCS 静态数据文件的工具。CCS 工具定义了一种人类可读的 CCS 静态数据 YAML 格式，并且包含一个程序将其转换为二进制格式。
寄存器定义生成器
-----------------------------

ccs-regs.asc 文件包含了 MIPI CCS 寄存器定义，用于生成 C 语言源代码文件，这些文件可以更好地被 C 语言编写的程序使用。由于生成的文件之间存在许多依赖关系，请不要手动修改它们，因为这容易出错且徒劳无功，而是应该更改生成这些文件的脚本。
用法
~~~~~

通常情况下，按照以下方式调用脚本来更新 CCS 驱动定义：

.. code-block:: none

	$ Documentation/driver-api/media/drivers/ccs/mk-ccs-regs -k \
		-e drivers/media/i2c/ccs/ccs-regs.h \
		-L drivers/media/i2c/ccs/ccs-limits.h \
		-l drivers/media/i2c/ccs/ccs-limits.c \
		-c Documentation/driver-api/media/drivers/ccs/ccs-regs.asc

CCS PLL 计算器
==================

CCS PLL 计算器用于计算给定传感器能力、板载配置以及用户指定配置下的 PLL 配置。由于这些配置的空间非常庞大，因此 PLL 计算器并不完全简单。然而，对于驱动来说，它相对容易使用。
PLL计算器所实现的PLL模型对应于MIPI CCS 1.1。

.. kernel-doc:: drivers/media/i2c/ccs-pll.h

**版权所有** |copy| 2020 英特尔公司
