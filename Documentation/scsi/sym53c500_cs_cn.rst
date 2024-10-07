.. SPDX-License-Identifier: GPL-2.0

=======================
sym53c500_cs 驱动程序
=======================

sym53c500_cs 驱动程序最初是作为 David Hinds 的 pcmcia-cs 包的附加部分，由 Tom Corner（tcorner@via.at）编写。早就需要对其进行重写，当前版本解决了以下问题：

	(1) 2.4 和 2.6 内核之间的大量更改
(2) 内核之外已弃用的 PCMCIA 支持
所有 USE_BIOS 代码已被删除。这些代码从未被使用过，而且无论如何也无法工作。USE_DMA 代码同样被移除了。衷心感谢 YOKOTA Hiroshi（nsp_cs 驱动程序）和 David Hinds（qlogic_cs 驱动程序），他们的一些代码片段被我无耻地借用到了这项工作中。还要感谢 Christoph Hellwig 在我摸索过程中耐心的指导。
Symbios Logic 53c500 芯片被用于“较新”（约 1997 年）版本的 New Media Bus Toaster PCMCIA SCSI 控制器中。想必还有其他产品使用了这种芯片，但我从未见过（更不用说亲手操作过）。
多年来，这个驱动程序的 pcmcia-cs 版本有过多次下载记录，我想对那些用户来说它应该有用。对 Tom Corner 来说它有用，对我来说也有用。但你的使用效果可能会有所不同。
Bob Tracy（rct@frus.com）
