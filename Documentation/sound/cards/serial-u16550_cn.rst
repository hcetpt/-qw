===============================
串行UART 16450/16550 MIDI驱动程序
===============================

适配器模块参数允许您选择以下选项之一：

* 0 - 支持Roland Soundcanvas（默认）
* 1 - 支持Midiator MS-124T（1）
* 2 - 支持Midiator MS-124W S/A模式（2）
* 3 - 支持MS-124W M/B模式（3）
* 4 - 支持多个输入的通用设备（4）

对于Midiator MS-124W，您必须将物理M-S和A-B开关设置为与所选驱动程序模式匹配。在Roland Soundcanvas模式下，支持多个ALSA原始MIDI子流（midiCnD0-midiCnD15）。每当您写入不同的子流时，驱动程序会发送非标准的MIDI命令序列F5 NN，其中NN是子流号加1。Roland模块使用此命令在不同的“部分”之间切换，因此此功能可以让您将每个部分视为独立的原始MIDI子流。驱动程序不提供发送F5 00（无选择）或完全不发送F5 NN命令序列的方法；也许应该提供。

简单的串行转换器用法示例：
::

	/sbin/setserial /dev/ttyS0 uart none
	/sbin/modprobe snd-serial-u16550 port=0x3f8 irq=4 speed=115200

Roland SoundCanvas带有4个MIDI端口的用法示例：
::

	/sbin/setserial /dev/ttyS0 uart none
	/sbin/modprobe snd-serial-u16550 port=0x3f8 irq=4 outs=4

在MS-124T模式下，支持一个原始MIDI子流（midiCnD0）；outs模块参数自动设置为1。驱动程序将相同的数据发送到所有四个MIDI输出连接器。将A-B开关和速度模块参数设置为匹配（A=19200，B=9600）。
MS-124T的A-B开关处于A位置的用法示例：
::

	/sbin/setserial /dev/ttyS0 uart none
	/sbin/modprobe snd-serial-u16550 port=0x3f8 irq=4 adaptor=1 \
			speed=19200

在MS-124W S/A模式下，支持一个原始MIDI子流（midiCnD0）；outs模块参数自动设置为1。驱动程序以全MIDI速度将相同的数据发送到所有四个MIDI输出连接器。
S/A模式的用法示例：
::

	/sbin/setserial /dev/ttyS0 uart none
	/sbin/modprobe snd-serial-u16550 port=0x3f8 irq=4 adaptor=2

在MS-124W M/B模式下，驱动程序支持16个ALSA原始MIDI子流；outs模块参数自动设置为16。子流号给出了数据应发送到哪些MIDI输出连接器的位掩码，其中midiCnD1发送到输出1，midiCnD2发送到输出2，midiCnD4发送到输出3，midiCnD8发送到输出4。因此，midiCnD15将数据发送到所有4个端口。作为特殊情况，midiCnD0也将数据发送到所有端口，因为不发送数据到任何端口是没有意义的。M/B模式有额外的开销来选择每个字节的MIDI输出，因此所有四个MIDI输出的总数据率最多为每520微秒一个字节，而每个端口的全MIDI数据率为每320微秒一个字节。
M/B模式的用法示例：
::

	/sbin/setserial /dev/ttyS0 uart none
	/sbin/modprobe snd-serial-u16550 port=0x3f8 irq=4 adaptor=3

目前不支持MS-124W硬件的M/A模式。此模式允许MIDI输出独立工作，并且吞吐量是M/B模式的两倍，但不允许同时将同一个字节发送到多个MIDI输出。M/A协议要求驱动程序在时间约束下摆弄调制解调器控制线，因此实现起来比其他模式稍微复杂一些。

除了MS-124W和MS-124T之外，目前不支持其他Midiator型号。请注意，后缀字母很重要；MS-124和MS-124B不兼容，其他已知型号MS-101、MS-101B、MS-103和MS-114也不兼容。我确实有一些文档（tim.mann@compaq.com），部分涵盖了这些型号，但没有实际设备进行实验。MS-124W的支持经过了实际设备测试。MS-124T的支持未经测试，但应该可以正常工作。
通用驱动程序通过单个串行端口支持多个输入和输出子流。类似于Roland Sound Canvas模式，使用F5 NN来选择合适的输入或输出流（取决于数据方向）。此外，CTS信号用于调节数据流。输入的数量由ins参数指定。
