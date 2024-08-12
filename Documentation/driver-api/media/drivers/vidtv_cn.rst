SPDX 许可证标识符: GPL-2.0

================================
vidtv：虚拟数字电视驱动程序
================================

作者: Daniel W. S. Almeida <dwlsalmeida@gmail.com>，2020年6月
背景
----------

Vidtv 是一个虚拟的 DVB 驱动程序，旨在作为编写驱动程序的参考模板。它还验证了现有的媒体 DVB API，从而帮助用户空间应用程序的编写者。
目前，它包含以下部分：

- 一个模拟调谐器驱动程序，如果所选频率与特定传输系统有效频率表中的频率相差太远，则会报告不良信号质量
- 一个模拟解调器驱动程序，将不断轮询调谐器返回的模拟信号质量，模拟一个设备能够根据载噪比 (CNR) 水平失去或重新获取信号锁定的情况
- 一个模拟桥接驱动程序，该模块负责加载模拟调谐器和解调器模块，并实现解复用逻辑。此模块在初始化时接受参数，这些参数将决定模拟行为的方式
- 负责编码有效 MPEG 传输流的代码，然后将其传递给桥接驱动程序。这个模拟流包含一些硬编码的内容
目前，我们只有一个纯音频频道，其中包含一个 MPEG 基本流，该流又包含一个按照 SMPTE 302m 编码的正弦波
请注意，选择这种特定的编码器是因为它是将 PCM 音频数据编码到 MPEG 传输流中最简单的方法
构建 vidtv
--------------
vidtv 是一个测试驱动程序，因此在编译内核时默认情况下**不会**启用
为了启用 vidtv 的编译：

- 启用 **DVB_TEST_DRIVERS**，然后
- 启用 **DVB_VIDTV**

当作为模块编译时，期望得到以下 .ko 文件：

- dvb_vidtv_tuner.ko

- dvb_vidtv_demod.ko

- dvb_vidtv_bridge.ko

运行 vidtv
-------------
当作为模块编译时，运行如下命令：

```
modprobe vidtv
```

就这样！桥接驱动程序将在其自身的初始化过程中初始化调谐器和解调器驱动程序。
默认情况下，它将接受以下频率：

- 474 MHz 用于 DVB-T/T2/C；
- 11,362 GHz 用于 DVB-S/S2。
对于卫星系统，驱动程序模拟一个通用扩展
LNB（低噪声块下变频器），其频率位于 Ku 波段，范围从 10.7 GHz 到 12.75 GHz。
您可以选择定义一些命令行参数供 vidtv 使用。
### vidtv 的命令行参数
-------------------
以下是可提供给 vidtv 的所有参数列表：

- `drop_tslock_prob_on_low_snr`
    - 如果信号质量差时失去 TS 锁定的概率
    - 此概率被假的解调器驱动程序使用，以便在信号质量不佳时返回状态为 0。
- `recover_tslock_prob_on_good_snr`:
    - 当信号改善时恢复 TS 锁定的概率。此概率被假的解调器驱动程序使用，以便在信号质量改善时/如果改善返回状态为 0x1f。
- `mock_power_up_delay_msec`
    - 模拟上电延迟。默认值：0。
- `mock_tune_delay_msec`
    - 模拟调谐延迟。默认值：0。
- `vidtv_valid_dvb_t_freqs`
    - 要模拟的有效 DVB-T 频率，单位为 Hz。
- `vidtv_valid_dvb_c_freqs`
    - 要模拟的有效 DVB-C 频率，单位为 Hz。
以下是提供的英文文本翻译成中文：

`vidtv_valid_dvb_s_freqs`  
要在Ku波段模拟的有效DVB-S/S2频率，单位为千赫兹（kHz）。

`max_frequency_shift_hz`,  
调整频道时允许的最大偏移量，单位为赫兹（Hz）。

`si_period_msec`  
发送SI数据包的频率。默认值：40毫秒。

`pcr_period_msec`  
发送PCR数据包的频率。默认值：40毫秒。

`mux_rate_kbytes_sec`  
尝试通过插入TS空数据包来维持这个比特率（如果需要的话）。默认值：4096。

`pcr_pid`,  
所有频道的PCR PID。默认值：0x200。

`mux_buf_sz_pkts`,  
用于复用缓冲区的大小，以188字节为单位。

`vidtv`内部结构
------------------------
内核模块按以下方式划分：

`vidtv_tuner.[ch]`  
实现一个假的调谐器DVB驱动程序。

`vidtv_demod.[ch]`  
实现一个假的解调器DVB驱动程序。

`vidtv_bridge.[ch]`  
实现一个桥接驱动程序。
MPEG相关的代码以如下方式划分：

vidtv_ts.[ch]
处理MPEG传输流（TS）数据包的代码，包括TS头部、适配字段、节目时钟参考（PCR）数据包和NULL数据包。
vidtv_psi.[ch]
这是PSI生成器。PSI数据包包含关于MPEG传输流的一般信息。需要一个PSI生成器以便用户空间应用程序可以获取传输流的信息，并最终调谐到一个（虚拟的）频道。
由于生成器是在一个单独的文件中实现的，因此可以在媒体子系统的其他地方重用它。
目前vidtv支持处理5个PSI表：PAT、PMT、SDT、NIT和EIT。
PAT和PMT的规范可以在*ISO 13818-1: 系统*中找到，而SDT、NIT、EIT的规范可以在*DVB系统的服务信息（SI）规范* *ETSI EN 300 468*中找到。
虽然这不是严格必需的，但在调试PSI表时使用真实的TS文件会有所帮助。目前vidtv试图复制这个文件中的PSI结构：`TS1Globo.ts <https://tsduck.io/streams/brazil-isdb-tb/TS1globo.ts>`_。
使用`DVBInspector <https://sourceforge.net/projects/dvbinspector/>`_是一种可视化流结构的好方法。
vidtv_pes.[ch]
实现了将编码器数据转换为MPEG传输流数据包的PES逻辑。这些数据包随后可以输入到TS多路复用器，并最终传送到用户空间。
vidtv_encoder.h
vidtv编码器的接口。可以通过实现在此文件中的调用来向该驱动程序添加新的编码器。
vidtv_s302m.[ch]
实现了一个S302M编码器，使得可以在生成的MPEG传输流中插入PCM音频数据。相关的规范可在线获取，即*SMPTE 302M-2007: 电视 - AES3数据映射到MPEG-2传输流*。
生成的 MPEG 基本流通过带有 S302M 注册描述符的私有流进行传输。
这应当能够将音频信号传递到用户空间，以便通过媒体软件对其进行解码和播放。相应的解码器位于 `libavcodec/s302m.c` 中，并且是实验性的。

`vidtv_channel.[ch]`
实现了一个“频道”抽象概念。
当 vidtv 启动时，它会创建一些硬编码的频道：

1. 它们的服务将被串联起来以填充服务描述表 (SDT)。
2. 它们的节目将被串联起来以填充节目关联表 (PAT)。

3. 它们的事件将被串联起来以填充事件信息表 (EIT)。

4. 对于 PAT 中的每个节目，都会创建一个节目映射表 (PMT) 段落。

5. 一个频道的 PMT 段落将被分配给它的流。

6. 每个流都将通过循环轮询其对应的编码器来生成传输流 (TS) 包。
这些包可能会由复用器交错处理，然后传输到桥接器。

`vidtv_mux.[ch]`
实现了一个基于 ffmpeg 实现（位于 "libavcodec/mpegtsenc.c"）的 MPEG 传输流复用器。

复用器运行一个循环，其职责包括：

1. 记录自上次迭代以来经过的时间量。
2. 轮询编码器以获取相当于‘已过时间’的数据量。
3. 如果需要，插入节目特定信息 (PSI) 和/或节目时钟参考 (PCR) 包。
#. 如果有必要，通过空包填充所产生的流以保持所选择的比特率。
#. 将生成的TS包传递给桥接驱动程序以便它们可以被传递给解复用器。

使用v4l-utils测试vidtv
----------------------

使用v4l-utils中的工具是测试和检查vidtv输出的好方法。它托管在这里：`v4l-utils文档 <https://linuxtv.org/wiki/index.php/V4l-utils>`_。
在其网页上提到：

v4l-utils是一系列用于处理媒体设备的包。
它托管在http://git.linuxtv.org/v4l-utils.git，并且大多数发行版都打包了它。
它提供了一系列库和实用工具，用于控制媒体板的多个方面。
首先安装v4l-utils，然后加载vidtv模块：

```
modprobe dvb_vidtv_bridge
```

如果驱动程序没有问题，它应该会加载并且其探测代码将会运行。这将加载调谐器和解调器驱动程序。
使用dvb-fe-tool
~~~~~~~~~~~~~~~~~

要检查解调器是否成功加载，可以运行以下命令：

```
$ dvb-fe-tool
设备：为DVB-T/T2/C/S/S2提供的虚拟解调器（/dev/dvb/adapter0/frontend0）功能：
    CAN_FEC_1_2
    CAN_FEC_2_3
    CAN_FEC_3_4
    CAN_FEC_4_5
    CAN_FEC_5_6
    CAN_FEC_6_7
    CAN_FEC_7_8
    CAN_FEC_8_9
    CAN_FEC_AUTO
    CAN_GUARD_INTERVAL_AUTO
    CAN_HIERARCHY_AUTO
    CAN_INVERSION_AUTO
    CAN_QAM_16
    CAN_QAM_32
    CAN_QAM_64
    CAN_QAM_128
    CAN_QAM_256
    CAN_QAM_AUTO
    CAN_QPSK
    CAN_TRANSMISSION_MODE_AUTO
DVB API版本 5.11，当前v5传输系统：DVBC/ANNEX_A
支持的传输系统：
    DVBT
    DVBT2
    [DVBC/ANNEX_A]
    DVBS
    DVBS2
当前标准的频率范围：
    起始：51.0 MHz
    终止：2.15 GHz
    步长：62.5 kHz
    容差：29.5 MHz
当前标准的符号率范围：
    起始：1.00 MBauds
    终止：45.0 MBauds
```

这将返回当前设置在解调器结构中的内容，例如：

```
static const struct dvb_frontend_ops vidtv_demod_ops = {
    .delsys = {
        SYS_DVBT,
        SYS_DVBT2,
        SYS_DVBC_ANNEX_A,
        SYS_DVBS,
        SYS_DVBS2,
    },

    .info = {
        .name                   = "虚拟解调器用于DVB-T/T2/C/S/S2",
        .frequency_min_hz       = 51 * MHz,
        .frequency_max_hz       = 2150 * MHz,
        .frequency_stepsize_hz  = 62500,
        .frequency_tolerance_hz = 29500 * kHz,
        .symbol_rate_min        = 1000000,
        .symbol_rate_max        = 45000000,

        .caps = FE_CAN_FEC_1_2 |
                FE_CAN_FEC_2_3 |
                FE_CAN_FEC_3_4 |
                FE_CAN_FEC_4_5 |
                FE_CAN_FEC_5_6 |
                FE_CAN_FEC_6_7 |
                FE_CAN_FEC_7_8 |
                FE_CAN_FEC_8_9 |
                FE_CAN_QAM_16 |
                FE_CAN_QAM_64 |
                FE_CAN_QAM_32 |
                FE_CAN_QAM_128 |
                FE_CAN_QAM_256 |
                FE_CAN_QAM_AUTO |
                FE_CAN_QPSK |
                FE_CAN_FEC_AUTO |
                FE_CAN_INVERSION_AUTO |
                FE_CAN_TRANSMISSION_MODE_AUTO |
                FE_CAN_GUARD_INTERVAL_AUTO |
                FE_CAN_HIERARCHY_AUTO,
    }

    ...
}
```
有关dvb-fe-tool的更多信息，请查阅在线文档：`dvb-fe-tool文档 <https://www.linuxtv.org/wiki/index.php/Dvb-fe-tool>`_

使用dvb-scan
~~~~~~~~~~~~~~

为了调整到一个频道并读取PSI表，我们可以使用dvb-scan
为此，你需要提供一个配置文件，通常称为“扫描文件”，这里有一个示例：

	[Channel]
	FREQUENCY = 474000000
	MODULATION = QAM/AUTO
	SYMBOL_RATE = 6940000
	INNER_FEC = AUTO
	DELIVERY_SYSTEM = DVBC/ANNEX_A

.. note::
	参数取决于你测试的视频标准。
.. note::
	vidtv是一个虚拟驱动程序，并不会验证扫描文件中的大部分信息。对于DVB-T/DVB-T2来说，仅指定'FREQUENCY'和'DELIVERY_SYSTEM'应该就足够了。然而，对于DVB-S/DVB-C，你还应提供'SYMBOL_RATE'。
你可以在网上浏览扫描表：`dvb-scan-tables
<https://git.linuxtv.org/dtv-scan-tables.git>`_
假设这个频道被命名为'channel.conf'，你可以这样运行：

	$ dvbv5-scan channel.conf
	dvbv5-scan ~/vidtv.conf
	ERROR    命令 BANDWIDTH_HZ (5) 在检索过程中未找到
	无法计算频率偏移。可能是带宽/符号率尚未可用。
扫描第1个频率 330000000
	    (0x00) 信号强度= -68.00dBm
	扫描第2个频率 474000000
	锁定   (0x1f) 信号强度= -34.45dBm C/N= 33.74dB UCB= 0
	服务 Beethoven，提供商 LinuxTV.org: 数字电视

关于dvb-scan的更多信息，请查阅在线文档：
`dvb-scan 文档 <https://www.linuxtv.org/wiki/index.php/Dvbscan>`_
使用 dvb-zap
~~~~~~~~~~~~~

dvbv5-zap 是一个命令行工具，可用于将MPEG-TS记录到磁盘上。其典型用途是调谐到一个频道并进入录制模式。下面的例子（取自文档）说明了这一点\ [1]_：

	$ dvbv5-zap -c dvb_channel.conf "beethoven" -o music.ts -P -t 10
	使用解复用器 'dvb0.demux0'
	从文件 'dvb_channel.conf' 中读取频道
	调谐至 474000000 Hz
	将所有PID传递给TS
	dvb_set_pesfilter 8192
	dvb_dev_set_bufsize: 缓冲区设置为 6160384
	锁定   (0x1f) 质量=良好 信号强度= -34.66dBm C/N= 33.41dB UCB= 0 postBER= 0 preBER= 1.05x10^-3 PER= 0
	锁定   (0x1f) 质量=良好 信号强度= -34.57dBm C/N= 33.46dB UCB= 0 postBER= 0 preBER= 1.05x10^-3 PER= 0
	开始将记录内容写入文件 'music.ts'
	接收了 24587768 字节 (2401 Kbytes/sec)
	锁定   (0x1f) 质量=良好 信号强度= -34.42dBm C/N= 33.89dB UCB= 0 postBER= 0 preBER= 2.44x10^-3 PER= 0

.. [1] 在这个例子中，它以所有节目ID的形式记录了10秒的内容，并存储在 music.ts 文件中。
可以通过使用识别MPEG-TS格式的一些播放器（如 ``mplayer`` 或 ``vlc``）来播放流的内容来观看该频道。
通过播放流的内容，可以直观地检查vidtv的工作情况，例如，要播放已录制的TS文件，可以运行：

	$ mplayer music.ts

或者，可以在一个终端上运行以下命令：

	$ dvbv5-zap -c dvb_channel.conf "beethoven" -P -r &

然后，在另一个终端上，通过DVR接口播放内容：

	$ mplayer /dev/dvb/adapter0/dvr0

有关dvb-zap的更多信息，请查阅在线文档：
`dvb-zap 文档
<https://www.linuxtv.org/wiki/index.php/Dvbv5-zap>`_
参见：`zap <https://www.linuxtv.org/wiki/index.php/Zap>`_

vidtv还有哪些需要改进的地方
-----------------------------------

添加 *debugfs* 集成
~~~~~~~~~~~~~~~~~~~~~~~~~

尽管前端驱动程序通过 .read_status 调用提供了DVBv5统计信息，但一个不错的补充是通过debugfs向用户空间提供额外的统计信息，debugfs是一种简单易用、基于RAM的文件系统，专门用于调试目的。
此逻辑将在单独的文件中实现，以避免污染前端驱动。这些统计信息是特定于驱动程序的，并且在测试期间可能非常有用。
Siano驱动程序是一个使用debugfs向用户空间传递特定于驱动程序的统计信息的例子，可以作为参考。
应该通过Kconfig选项进一步启用和禁用这一功能，以便于使用。

添加视频测试方法
~~~~~~~~~~~~~~~~~~~~~~~

目前，vidtv只能对PCM音频进行编码。实现一个简化的MPEG-2视频编码版本将非常棒，这样我们就可以测试视频了。首先需要研究的是*ISO 13818-2: 信息技术 —— 运动图像及其伴音的一般编码 —— 第2部分：视频*，它涵盖了MPEG传输流中的压缩视频编码。
这可能可选地使用Video4Linux2测试图案生成器（v4l2-tpg），它位于：

    drivers/media/common/v4l2-tpg/

添加白噪声模拟
~~~~~~~~~~~~~~~~~~~~~~~~~~

vidtv调谐器已经具有代码来判断所选频率是否远离有效频率表。这意味着解调器最终可能会失去信号锁定，因为调谐器会报告不良的信号质量。
一个很好的补充是在信号质量不佳时模拟一些噪声：

- 随机丢弃一些TS包。如果连续性计数器被更新但包没有传递给解复用器，这将触发连续性错误
- 按照实际情况更新错误统计（例如BER等）
- 在编码数据中模拟一些噪声

vidtv中使用的函数和结构体
---------------------------------------

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_bridge.h

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_channel.h

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_demod.h

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_encoder.h

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_mux.h

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_pes.h

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_psi.h

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_s302m.h

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_ts.h

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_tuner.h

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_common.c

.. kernel-doc:: drivers/media/test-drivers/vidtv/vidtv_tuner.c
