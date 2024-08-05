======================
STi ARM Linux 概览
======================

简介
------------

  ST 微电子的多媒体及应用处理器系列中的 CortexA9 系统芯片由 ARM Linux 的 'STi' 平台提供支持。目前，支持的配置包括 STiH407、STiH410 和 STiH418。
配置
------------

  STi 平台的配置通过 multi_v7_defconfig 支持。
布局
------

  多个机器家族（STiH407、STiH410 和 STiH418）的所有文件都位于 arch/arm/mach-sti 中的平台代码内。

  在 mach 文件夹中有一个通用板级文件 board-dt.c，它支持扁平设备树（Flattened Device Tree），这意味着它可以与任何兼容的带有设备树的板子一起工作。
文档作者
---------------

  Srinivas Kandagatla <srinivas.kandagatla@st.com>，版权所有 © 2013 ST 微电子
