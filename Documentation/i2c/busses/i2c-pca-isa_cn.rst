=========================
内核驱动 i2c-pca-isa
=========================

支持的适配器：

此驱动程序支持使用 Philips PCA 9564 的 ISA 板卡
并行总线到 I2C 总线控制器

作者：Ian Campbell <icampbell@arcom.com>，Arcom 控制系统

模块参数
--------

* base int
    I/O 基础地址
* irq int
    中断请求 IRQ
* clock int
    如 PCA9564 数据手册表 1 中所述的时钟速率

描述
----

此驱动程序支持使用 Philips PCA 9564 的 ISA 板卡
并行总线到 I2C 总线控制器
