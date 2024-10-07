SPDX 许可证标识符: GPL-2.0

=====================================
德州仪器 TPS6594 PFSM 驱动程序
=====================================

作者: Julien Panis (jpanis@baylibre.com)

概述
========

严格来说，PFSM（预配置有限状态机）并不是硬件。它是一段代码。
TPS6594 PMIC（电源管理集成电路）集成了一个状态机来管理操作模式。根据当前的操作模式，一些电压域保持供电，而其他电压域可以关闭。
PFSM 驱动程序可用于触发已配置状态之间的转换。它还提供了对设备寄存器的读写访问功能。
支持的芯片
---------------

- tps6594-q1
- tps6593-q1
- lp8764-q1

驱动程序位置
==================

drivers/misc/tps6594-pfsm.c

驱动类型定义
==================

include/uapi/linux/tps6594_pfsm.h

驱动 IOCTL 命令
==================

:c:macro:: `PMIC_GOTO_STANDBY`
所有设备资源都断电。处理器关闭，没有任何电压域供电。

:c:macro:: `PMIC_GOTO_LP_STANDBY`
PMIC 的数字和模拟功能，如果不需要始终开启，则关闭（低功耗）。

:c:macro:: `PMIC_UPDATE_PGM`
触发固件更新。

:c:macro:: `PMIC_SET_ACTIVE_STATE`
操作模式之一。
PMIC 完全功能，并向所有 PDN 负载供电。
MCU 和主处理器部分的所有电压域均供电。

:c:macro:: `PMIC_SET_MCU_ONLY_STATE`
操作模式之一。
仅MCU安全岛分配的电源资源处于开启状态
:c:macro:: `PMIC_SET_RETENTION_STATE`
运行模式之一
根据设置的触发条件，某些DDR/GPIO电压域可以保持供电状态，而所有其他域则关闭以最小化整个系统的功耗
驱动程序使用
=============

查看可用的PFSM::

    # ls /dev/pfsm*

转储第0和第1页的寄存器内容::

    # hexdump -C /dev/pfsm-0-0x48

查看PFSM事件::

    # cat /proc/interrupts

用户空间代码示例
----------------------

samples/pfsm/pfsm-wakeup.c
