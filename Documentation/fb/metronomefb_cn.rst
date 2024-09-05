===========
Metronomefb
===========

维护者：Jaya Kumar <jayakumar.lkml@gmail.com>

最后修订日期：2008年3月10日

Metronomefb 是一个用于 Metronome 显示控制器的驱动程序。该控制器来自 E-Ink 公司，旨在驱动 E-Ink 的 Vizplex 显示介质。E-Ink 在这里提供了关于该控制器和显示介质的一些详细信息：http://www.e-ink.com/products/matrix/metronome.html。Metronome 通过 AMLCD 接口与主机 CPU 进行通信。主机 CPU 生成控制信息和帧缓冲区中的图像，并通过特定于主机的方法将这些信息传递给 AMLCD 接口。显示状态和错误状态分别通过单独的 GPIO 引脚获取。

Metronomefb 是平台无关的，依赖于一个特定于板卡的驱动程序来完成所有物理 I/O 操作。目前，已为 AM-200 EPD 开发套件中使用的 PXA 板实现了示例。这个示例是 am200epd.c。

Metronomefb 需要波形信息，这些信息通过 AMLCD 接口传递给 Metronome 控制器。波形信息预期通过用户空间通过固件类接口提供。波形文件可以被压缩，只要你的 udev 或 hotplug 脚本知道在传递之前需要解压缩即可。Metronomefb 会请求 metronome.wbf 文件，该文件通常位于 /lib/firmware/metronome.wbf，具体取决于你的 udev/hotplug 设置。我只测试了一个波形文件，其原始标签为 23P01201_60_WT0107_MTC。我不知道这些标签代表什么含义。在操作波形时应谨慎行事，因为可能会对显示介质产生永久性影响。我没有权限访问，也不确切知道波形在物理介质上具体做了什么。

Metronomefb 使用延迟 I/O 接口以提供可映射内存的帧缓冲区。它已经经过 tinyx（Xfbdev）的测试。目前已知它可以与 xeyes、xclock、xloadimage 和 xpdf 正常工作。
