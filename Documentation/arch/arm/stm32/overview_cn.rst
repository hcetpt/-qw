STM32 ARM Linux 概览
========================

简介
------------

STMicroelectronics 的 STM32 系列包括基于 Cortex-A 微处理器 (MPU) 和 Cortex-M 微控制器 (MCU) 的产品，这些产品得到了 ARM Linux “STM32” 平台的支持。

配置
------------

对于 MCU，使用提供的默认配置：
        make stm32_defconfig
对于 MPU，使用 multi_v7 配置：
        make multi_v7_defconfig

布局
------

所有多个机器家族的文件都位于 arch/arm/mach-stm32 中的平台代码中。

在 mach 文件夹中有一个支持 Flattened Device Tree 的通用板级文件 board-dt.c，这意味着它适用于任何带有设备树的兼容板卡。

作者
------

- Maxime Coquelin <mcoquelin.stm32@gmail.com>
- Ludovic Barre <ludovic.barre@st.com>
- Gerald Baeza <gerald.baeza@st.com>
