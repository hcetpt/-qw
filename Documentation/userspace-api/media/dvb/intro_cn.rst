SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _dvb_introduction:

************
简介
************

.. _requisites:

所需知识
=====================

阅读本文档的人员需要具备一定的数字视频广播（数字电视）方面的知识，并且应该熟悉 MPEG2 规范 ISO/IEC 13818（即 ITU-T H.222）的第一部分，即您应该知道什么是节目/传输流（PS/TS），以及分组化基本流（PES）或 I 帧的含义。各种数字电视标准文档可以从以下网站下载：

- 欧洲标准（DVB）: http://www.dvb.org 和/或 http://www.etsi.org
- 美国标准（ATSC）: https://www.atsc.org/standards/
- 日本标准（ISDB）: http://www.dibeg.org/

还需要了解如何访问 Linux 设备并使用 ioctl 调用。这包括对 C 或 C++ 的知识。

.. _history:

历史
=======

1999 年末，我们在 Convergence 使用的第一个数字电视卡 API 是 Video4Linux API 的扩展，该 API 主要为帧抓取卡开发。因此，它并不真正适合用于数字电视卡及其新功能，例如录制 MPEG 流和同时过滤多个节和 PES 数据流。

2000 年初，Nokia 向 Convergence 提出了一个新的标准 Linux 数字电视 API 的提案。作为基于开放标准终端开发的承诺，Nokia 和 Convergence 将其提供给所有 Linux 开发者，并于 2000 年 9 月在 https://linuxtv.org 发布。通过 Siemens/Hauppauge DVB PCI 卡的 Linux 驱动程序，Convergence 提供了 Linux 数字电视 API 的第一个实现。在早期，Convergence 是 Linux 数字电视 API 的维护者。

现在，该 API 由 LinuxTV 社区（即本文档的读者）维护。Linux 数字电视 API 不断地与内核子系统的改进一起进行审查和改进。

.. _overview:

概述
=======

.. _stb_components:

.. kernel-figure:: dvbstb.svg
    :alt:   dvbstb.svg
    :align: center

    数字电视卡/机顶盒的组件

数字电视卡或机顶盒（STB）通常包含以下主要硬件组件：

前端，包括调谐器和数字电视解调器
   在这里，来自卫星天线、天线或直接来自有线电视的原始信号到达数字电视硬件。前端将此信号下变频并解调成 MPEG 传输流（TS）。在卫星前端的情况下，这包括一个卫星设备控制（SEC）设施，允许控制低噪声块（LNB）极化、多馈电开关或天线旋转器。
有条件接入（CA）硬件，如 CI 适配器和智能卡插槽
   完整的 TS 会通过有条件接入硬件。用户有权访问的节目（受智能卡控制）会被实时解码并重新插入到 TS 中。

.. note::

      并非每个数字电视硬件都提供有条件接入硬件。
解复用器，用于过滤输入的数字电视MPEG-TS流  
解复用器将TS（传输流）拆分成其组成部分，如音频和视频流。通常包含多个这样的音频和视频流，并且还包含有关此提供商提供的节目或其它流的信息的数据流。

音频和视频解码器  
解复用器的主要目标是音频和视频解码器。解码后，它们将未压缩的音频和视频传递给计算机屏幕或电视机。

.. note::

      现代硬件通常不需要单独的解码器硬件，因为这种功能可以由主CPU、系统的图形适配器或嵌入在系统级芯片（SoC）集成电路中的信号处理硬件提供。
对于某些用途（例如仅数据用途，如“通过卫星上网”），可能也不需要解码器。
:ref:`stb_components` 显示了这些组件之间控制和数据流的简要示意图。
.. _dvb_devices:

Linux数字电视设备
==================

Linux数字电视API使您能够通过目前六个Unix风格的字符设备来控制这些硬件组件，这些设备分别用于视频、音频、前端、解复用、CA以及IP-over-DVB网络。视频和音频设备控制MPEG2解码硬件，前端设备控制调谐器和数字电视解调器。解复用设备让您能够控制硬件的PES和section滤波器。如果硬件不支持这些滤波，则可以在软件中实现这些滤波器。最后，CA设备控制所有硬件的条件访问功能。这取决于平台的安全需求，以及是否以及如何通过该设备向应用程序提供CA功能。
所有设备都可以在 ``/dev`` 目录下的 ``/dev/dvb`` 中找到。各个设备的名称如下：

-  ``/dev/dvb/adapterN/audioM``，

-  ``/dev/dvb/adapterN/videoM``，

-  ``/dev/dvb/adapterN/frontendM``，

-  ``/dev/dvb/adapterN/netM``，

-  ``/dev/dvb/adapterN/demuxM``，

-  ``/dev/dvb/adapterN/dvrM``，

-  ``/dev/dvb/adapterN/caM``，

其中 ``N`` 表示系统中从0开始编号的数字电视卡，而 ``M`` 表示每个适配器内从0开始编号的各类型设备。在接下来的讨论中，我们将省略 “``/dev/dvb/adapterN/``” 部分。
关于所有设备的数据结构和函数调用的更多细节将在后续章节中描述。
.. _include_files:

API头文件
=================

对于每个数字电视设备，都存在一个对应的头文件。数字电视API头文件应该以部分路径的方式包含在应用程序源代码中，例如：

.. code-block:: c

    #include <linux/dvb/ca.h>
    #include <linux/dvb/dmx.h>
    #include <linux/dvb/frontend.h>
    #include <linux/dvb/net.h>

为了使应用程序能够支持不同的API版本，存在一个额外的头文件 ``linux/dvb/version.h``，定义了常量 ``DVB_API_VERSION``。本文档描述的是 ``DVB_API_VERSION 5.10``。
当然，请提供您需要翻译的文本。
