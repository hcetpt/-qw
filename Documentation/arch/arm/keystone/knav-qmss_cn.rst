德州仪器Keystone Navigator队列管理子系统驱动程序

队列管理子系统(QMSS)驱动程序源代码路径：
  drivers/soc/ti/knav_qmss.c
  drivers/soc/ti/knav_qmss_acc.c

在Keystone SOC上找到的队列管理子系统(QMSS)是构成Keystone多核Navigator主干的主要硬件子系统之一。QMSS由队列管理器、打包数据结构处理器(PDSP)、链接RAM、描述符池和基础设施包DMA组成。
队列管理器是一个硬件模块，负责加速包队列的管理。通过向特定内存映射位置写入或读取描述符地址来对数据包进行排队/出队。PDSP执行与QMSS相关的功能，如累积、服务质量(QoS)或事件管理。链接RAM寄存器用于链接存储在描述符RAM中的描述符。描述符RAM可以配置为内部或外部内存。QMSS驱动程序管理PDSP设置、链接RAM区域、队列池管理（分配、推送、弹出和通知）以及描述符池管理。

knav qmss驱动程序为驱动程序提供了一组API以打开/关闭QMSS队列、分配描述符池、映射描述符、向队列中推送/弹出等。有关可用API的详细信息，请参阅include/linux/soc/ti/knav_qmss.h。

设备树文档可以在以下位置找到：
Documentation/devicetree/bindings/soc/ti/keystone-navigator-qmss.txt

使用PDSP固件的累加器QMSS队列
============================================
QMSS PDSP固件支持累加器通道，可以监控单个队列或多个连续队列。drivers/soc/ti/knav_qmss_acc.c是与累加器PDSP交互的驱动程序。这配置了设备树中定义的累加器通道（请参见设备树文档），每个通道监控1个或32个队列。关于固件的更多描述可在CPPI/QMSS低级驱动文档（docs/CPPI_QMSS_LLD_SDS.pdf）中找到，位于：

   git://git.ti.com/keystone-rtos/qmss-lld.git

k2_qmss_pdsp_acc48_k2_le_1_0_0_9.bin固件最多支持48个累加器通道。此固件可在firmware.git的ti-keystone文件夹下找到：

   git://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git

要使用它，请将固件图像复制到initramfs或ubifs文件系统的lib/firmware文件夹，并在文件系统中为k2_qmss_pdsp_acc48_k2_le_1_0_0_9.bin创建一个符号链接，然后启动内核。如果成功加载PDSP的固件，则会在启动日志中看到

"firmware file ks2_qmss_pdsp_acc48.bin downloaded for PDSP"

使用累加队列需要固件图像存在于文件系统中。如果SOC上的PDSP没有运行，驱动程序不会将累加队列添加到受支持的队列范围内。如果PDSP未运行时有打开累加队列的请求，API调用会失败。因此，在使用这些类型的队列之前，请确保将固件复制到文件系统中。
