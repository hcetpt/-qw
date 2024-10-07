低延迟、多声道音频使用JACK和emu10k1/emu10k2
==================================================

本文档是关于如何在JACK中使用基于emu10k1的设备来实现低延迟、多声道录音功能的指南。我最近的所有工作都是受到kX项目的启发，使Linux用户能够充分利用其硬件的能力。没有他们的工作，我永远不会发现这些硬件的真正实力。
[网址] http://www.kxproject.com
						— Lee Revell, 2005年3月30日

直到最近，Linux上的emu10k1用户还无法访问与Windows驱动程序中的"kX ASIO"功能相同的低延迟、多声道特性。自从ALSA 1.0.9开始，这种情况已经改变！

对于不熟悉kX ASIO的人来说，它包括了16个捕捉通道和16个播放通道。在2.6.9及更高版本的Linux内核中，延迟可以低至64帧（1.33毫秒）甚至32帧（0.66毫秒）。配置过程比在Windows上稍微复杂一些，因为你必须选择正确的设备供JACK使用。实际上，对于qjackctl用户来说，这是非常直观的——选择双工模式，然后为捕捉和播放选择多声道设备，将输入和输出通道设置为16，并将采样率设置为48000Hz。命令行如下所示：
::

  /usr/local/bin/jackd -R -dalsa -r48000 -p64 -n2 -D -Chw:0,2 -Phw:0,3 -S

这将为你提供16个输入端口和16个输出端口。
这16个输出端口映射到16个FX总线（或者对于Audigy来说，是前16个中的64个）。FX总线到物理输出的映射在sb-live-mixer.rst（或audigy-mixer.rst）中有描述。
这16个输入端口连接到16个物理输入。与普遍的看法相反，所有emu10k1卡都是多声道卡。哪些输入通道连接到了物理输入取决于具体的卡型号。建议进行试验和错误测试；一些热心的kX用户已经反向工程了这些卡的引脚图，并且可以在互联网上找到这些资料。Meterbridge在这里很有帮助，而kX论坛里也充满了有用的信息。
每个输入端口要么对应一个数字（SPDIF）输入，一个模拟输入，或者什么也没有。唯一的例外是SBLive! 5.1。在这种设备上，第二个和第三个输入端口连接到了中心/LFE输出。你仍然会看到16个捕捉通道，但只有14个可用作录音输入。

下表是从kxfxlib/da_asio51.cpp借用的，描述了JACK端口到FXBUS2（多轨录音输入）和EXTOUT（物理输出）通道的映射关系：
10k1 5.1 SBLive卡上的JACK（& ASIO）映射：

==============  ========        ============
JACK		Epilog		FXBUS2(nr)
==============  ========        ============
capture_1	asio14		FXBUS2(0xe)
capture_2	asio15		FXBUS2(0xf)
capture_3	asio0		FXBUS2(0x0)	
~capture_4	Center		EXTOUT(0x11)	// 映射到Center
~capture_5	LFE		EXTOUT(0x12)	// 映射到LFE
capture_6	asio3		FXBUS2(0x3)
capture_7	asio4		FXBUS2(0x4)
capture_8	asio5		FXBUS2(0x5)
capture_9	asio6		FXBUS2(0x6)
capture_10	asio7		FXBUS2(0x7)
capture_11	asio8		FXBUS2(0x8)
capture_12	asio9		FXBUS2(0x9)
capture_13	asio10		FXBUS2(0xa)
capture_14	asio11		FXBUS2(0xb)
capture_15	asio12		FXBUS2(0xc)
capture_16	asio13		FXBUS2(0xd)
==============  ========        ============

TODO: 描述如何结合使用ld10k1/qlo10k1和JACK
