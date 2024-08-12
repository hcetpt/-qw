### SPDX 许可证标识符：GPL-2.0

#### DVB-USB框架背后的想法
=================================

**注释：**

1) 本文档已经过时。请访问DVB Wiki（https://linuxtv.org/wiki）获取最新信息。
2) **已废弃：** 新的DVB USB驱动程序应当使用dvb-usb-v2框架。

2005年3月，我得到了一款新的Twinhan USB 2.0 DVB-T设备。他们提供了规格和固件。
出于浓厚的兴趣，我想将驱动程序（当然包含一些特殊处理）加入到dibusb中。
在阅读了一些规格并进行了一些USB探测后，我发现dibusb驱动程序将会变得一团糟。因此，我决定采用不同的方式：借助于一个DVB-USB框架。
该框架提供了通用功能（主要是内核API调用），包括：

- 运输流URB处理与dvb-demux-feed-control相结合（支持批量和等时性传输）
- 为DVB-API注册设备
- 如果适用，则注册I2C适配器
- 遥控/输入设备处理
- 请求和加载固件（目前仅针对Cypress USB控制器）
- 其他可以被多个驱动共享的功能/方法（例如用于批量控制命令的函数）
- TODO: 实现一个I2C分块器。它根据寄存器长度及可多写入、多读取值的数量创建设备特定的寄存器访问块
特定的DVB USB设备的源代码仅负责通过总线与设备通信。DVB-API功能与这些通信之间的连接是通过回调实现的，这些回调在每个设备驱动的静态设备描述（struct dvb_usb_device）中指定。
为了了解示例，请参阅drivers/media/usb/dvb-usb/vp7045*。
目标是将所有USB设备（dibusb、cinergyT2，也许还包括ttusb；flexcop-usb已经从通用的flexcop设备中受益）迁移到使用dvb-usb-lib。
TODO: 根据请求的馈送数量动态启用和禁用PID过滤器。
支持的设备
------------

请访问 LinuxTV DVB 维基页面以获取完整的卡片/驱动程序/固件列表：https://linuxtv.org。具体链接如下：
https://linuxtv.org/wiki/index.php/DVB_USB

0. 历史与新闻：

  * 2005-06-30
    - 添加了对 WideView WT-220U 的支持（感谢 Steve Chang）

  * 2005-05-30
    - 在 dvb-usb 框架中添加了基本的等时支持
    - 添加了对 Conexant Hybrid 参考设计和 Nebula DigiTV USB 的支持

  * 2005-04-17
    - 将所有 dibusb 设备移植到 dvb-usb 框架下使用

  * 2005-04-02
    - 重新启用了遥控代码并进行了改进

  * 2005-03-31
    - 将 Yakumo/Hama/Typhoon DVB-T USB2.0 设备移植到 dvb-usb

  * 2005-03-30
    - 第一次提交基于 dibusb 源代码的 dvb-usb 模块。
      首个设备是一个新的驱动程序，用于 TwinhanDTV Alpha/MagicBox II USB2.0 专用 DVB-T 设备
      （从 dvb-dibusb 改为 dvb-usb）

  * 2005-03-28
    - 添加了对 AVerMedia AverTV DVB-T USB2.0 设备的支持（感谢 Glen Harris 和 Jiun-Kuei Jung，AVerMedia 公司）

  * 2005-03-14
    - 添加了对 Typhoon/Yakumo/HAMA DVB-T 移动 USB2.0 的支持

  * 2005-02-11
    - 添加了对 KWorld/ADSTech Instant DVB-T USB2.0 的支持
      （非常感谢 Joachim von Caron）

  * 2005-02-02
    - 添加了对 Hauppauge Win-TV Nova-T USB2 的支持

  * 2005-01-31
    - USB1.1 设备上的失真流问题已解决

  * 2005-01-13
    - 将镜像的 pid_filter_table 移回到 dvb-dibusb
      HanfTek UMT-010 的第一个几乎可用版本
      发现 Yakumo/HAMA/Typhoon 是 HanfTek UMT-010 的前身

  * 2005-01-10
    - 完成了重构，现在一切都非常令人满意

  * 2005-01-01
    - 为一些奇怪的设备（如 Artec T1 AN2235 设备有时会装配 Panasonic 调谐器）实现了调谐器特殊处理。已实现调谐器探测
      （非常感谢 Gunnar Wittich）

  * 2004-12-29
    - 经过几天的努力，修复了 URB 不返回的错误

  * 2004-12-26
    - 重构了 dibusb 驱动程序，将其拆分为单独的文件
    - 启用了 I2C 探测功能

  * 2004-12-06
    - 实现了解调器 I2C 地址探测的可能性
    - 新增 USB ID（Compro、Artec）

  * 2004-11-23
    - 合并了来自 DiB3000MC_ver2.1 的更改
    - 修订了调试机制
    - 实现了提供完整 TS 对于 USB2.0 的可能性

  * 2004-11-21
    - dib3000mc/p 前端驱动程序的第一个可用版本

  * 2004-11-12
    - 添加了额外的遥控键（感谢 Uwe Hanke）
以下是提供的英文内容翻译成中文：

2004-11-07
- 添加了遥控器支持。感谢David Matthews。

2004-11-05
- 添加了对新设备（Grandtec/Avermedia/Artec）的支持。
- 将我的更改（针对dib3000mb/dibusb）合并到了FE_REFACTORING，因为它已成为主分支。
- 将传输控制（PID过滤，FIFO控制）从USB驱动程序移动到前端，这样似乎更合理（添加了xfer_ops结构）。
- 创建了一个用于前端的通用文件（mc/p/mb）。

2004-09-28
- 添加了对新设备（未知，供应商ID为Hyper-Paltek）的支持。

2004-09-20
- 添加了对新设备（Compro DVB-U2000）的支持，感谢Amaury Demol报告。
- 更改了USB TS传输方法（多个URBS，在设置新的PID前停止传输）。

2004-09-13
- 添加了对新设备（Artec T1 USB电视盒）的支持，感谢Christian Motschke报告。

2004-09-05
- 发布了dibusb设备和dib3000mb前端驱动程序（对于vp7041.c来说是旧闻）。

2004-07-15
- 偶然发现该设备使用TUA6010XS作为PLL。

2004-07-12
- 发现驱动程序还应与CTS便携式（中国电视系统）兼容。

2004-07-08
- 解决了firmware-extraction-2.422问题，现在驱动程序可以正确使用从2.422提取的固件。
- 对于2.6.4（DVB）的编译问题的#if语句。
- 更改了固件处理方式，请参阅vp7041.txt第1.1节。

2004-07-02
- 进行了一些调谐器修改，版本0.1，进行了清理，并首次公开。

2004-06-28
- 现在使用dvb_dmx_swfilter_packets，一切运行良好。

2004-06-27
- 能够观看并切换频道（预alpha版）。
- 尚未实现部分过滤。

2004-06-06
- 首次接收到TS数据包，但内核出现oops错误。

2004-05-14
- 固件加载器正在工作。

2004-05-11
- 开始编写驱动程序。

如何使用？
------------

固件
~~~~
大多数USB驱动程序需要在开始工作之前将固件下载到设备上。
请访问DVB-USB驱动程序的维基页面以了解您的设备所需的固件：
https://linuxtv.org/wiki/index.php/DVB_USB

编译
~~~~~
由于驱动程序位于Linux内核中，因此在您喜欢的配置环境中激活驱动程序应该就足够了。我建议将驱动程序编译为模块。热插拔会完成剩下的工作。
如果您使用的是dvb内核，请进入build-2.6目录，运行'make'，然后运行'insmod.sh load'。

加载驱动程序
~~~~~~~~~~~~
热插拔能够在需要时加载驱动程序（因为您插入了设备）。
如果您想要启用调试输出，则必须手动加载驱动程序，并且需要在dvb内核的CVS存储库中进行。
首先查看可用的调试级别：

.. code-block:: none

   # modinfo dvb-usb
   # modinfo dvb-usb-vp7045

   等等
.. code-block:: none

   modprobe dvb-usb debug=<level>
   modprobe dvb-usb-vp7045 debug=<level>
   等等
这应该能解决问题。
当驱动程序成功加载、固件文件位于正确的位置并且设备已连接时，“电源”LED应被打开。
此时，你应该能够启动一个支持dvb的应用程序。我使用 (t|s)zap、mplayer 和 dvbscan 来测试基本功能。VDR-xine 提供了长期的测试场景。

已知问题和bug
----------------------

- 不要在运行 DVB 应用程序时移除 USB 设备，否则你的系统可能会崩溃或无法正常工作。
添加设备支持
~~~~~~~~~~~~~~~~~~~~~~~~~~

待办事项

USB1.1 带宽限制
~~~~~~~~~~~~~~~~~~~~~~~~~~~

目前支持的许多设备都是 USB1.1 的，因此当它们连接到 USB2.0 集线器时，最大带宽大约为 5-6 MBit/s。这对于接收 DVB-T 信道的完整传输流（约为 16 MBit/s）是不够的。通常情况下，如果你只想看电视（这不适用于高清电视），这不是问题，但同时观看一个频道并录制同一频率上的另一个频道则无法很好地工作。这适用于所有 USB1.1 DVB-T 设备，而不仅仅是 dvb-usb 设备。

之前存在的问题，即在大量使用设备时传输流会受到扭曲，现在已经彻底解决。我所使用的所有 dvb-usb 设备（Twinhan、Kworld、DiBcom）现在与 VDR 配合得非常完美。有时我甚至能够录制一个频道并观看另一个频道。

评论
~~~~~~~~

欢迎提供补丁、评论和建议。

3. 致谢
-------------------

Amaury Demol (Amaury.Demol@parrot.com) 和 DiBcom 的 Francois Kanounnikoff 提供了规格、代码和帮助，这些构成了 dvb-dibusb、dib3000mb 和 dib3000mc 的基础。
David Matthews 确定了一个新的设备类型（Artec T1 with AN2235），并对 dibusb 进行了扩展以处理遥控事件。非常感谢。
Alex Woods 经常回答关于 USB 和 DVB 方面的问题，对此表示衷心感谢。
Bernd Wagner 在提交大量 bug 报告和讨论中提供了帮助。
Gunnar Wittich 和 Joachim von Caron 对于提供他们机器的 root 访问权限以便实现对新设备的支持表示信任。
艾伦·瑟德和迈克尔·赫奇森协助撰写了Nebula digitv驱动程序，
格伦·哈里斯指出了存在一个新的dibusb设备，以及来自AVerMedia的钟俊奎，他友好地提供了一个特殊的固件以使该设备能在Linux环境下正常运行，
来自Twinhan的陈珍妮、杰夫和杰克在撰写vp7045驱动程序方面给予了支持，
来自WideView的史蒂夫·张提供了新设备的信息及固件文件，
迈克尔·帕克斯顿提交了遥控按键映射，
一些在linux-dvb邮件列表上的朋友鼓励了我，
彼得·席尔德曼 >peter.schildmann-nospam-at-web.de< 开发了一个用户级别的固件加载器，这在编写vp7041驱动时节省了很多时间，
乌尔夫·赫尔曼诺在传统中文方面帮助了我，
安德烈·斯莫库顿和克里斯蒂安·弗罗梅尔在硬件方面支持我，并且非常耐心地听我讲述遇到的问题。
