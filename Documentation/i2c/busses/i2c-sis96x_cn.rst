========================
内核驱动 i2c-sis96x
========================

替代了 2.4.x 版本的 i2c-sis645

支持的适配器：

  * Silicon Integrated Systems Corp（SiS）

    以下主机桥接器的任意组合：
	645, 645DX（又称为 646）、648、650、651、655、735、745、746

    和以下南桥：
	961, 962, 963(L)

作者：Mark M. Hoffman <mhoffman@lightlink.com>

描述
-----------

此 SMBus 专用驱动已知在具有上述命名芯片组组合的主板上正常工作。该驱动是在没有 SiS 提供适当数据手册的情况下开发的。假设 SMBus 寄存器与 SiS630 的兼容，尽管它们位于一个完全不同的位置。感谢 Alexander Malysh <amalysh@web.de> 提供了 SiS630 数据手册（和驱动程序）。
作为根用户运行命令 `lspci` 应该会产生如下所示的行：

  00:00.0 主机桥接器: Silicon Integrated Systems [SiS]: 未知设备 0645
  00:02.0 ISA 桥接器: Silicon Integrated Systems [SiS] 85C503/5513
  00:02.1 SMBus: Silicon Integrated Systems [SiS]: 未知设备 0016

或者可能产生这样的结果：

  00:00.0 主机桥接器: Silicon Integrated Systems [SiS]: 未知设备 0645
  00:02.0 ISA 桥接器: Silicon Integrated Systems [SiS]: 未知设备 0961
  00:02.1 SMBus: Silicon Integrated Systems [SiS]: 未知设备 0016

（版本高于 2.4.18 的内核可能会填充这些“未知”信息）

如果你无法看到这些信息，请查看 quirk_sis_96x_smbus
（drivers/pci/quirks.c）（如果南桥检测失败也请查看）

我怀疑此驱动也可以适用于以下 SiS 芯片组：635 和 635T。如果有人拥有这些芯片的主板，并且愿意冒着使原本稳定的内核崩溃的风险以促进进步，请联系我 mhoffman@lightlink.com 或通过 linux-i2c 邮件列表：<linux-i2c@vger.kernel.org>。也请发送错误报告和/或成功的案例。

待办事项
------

* 该驱动不支持 SMBus 块读写；如果找到需要它们的场景，我可能会添加它们。
致谢
---------

Mark D. Studebaker <mdsxyz123@yahoo.com>
 - 设计提示和错误修复

Alexander Maylsh <amalysh@web.de>
 - 同样提供了帮助，再加上一份重要的数据手册……几乎是我真正想要的那一份

Hans-Günter Lütke Uphues <hg_lu@t-online.de>
 - SiS735 的补丁

Robert Zwerus <arzie@dds.nl>
 - SiS645DX 的测试

Kianusch Sayah Karadji <kianusch@sk-tech.net>
 - SiS645DX/962 的补丁

Ken Healy
 - SiS655 的补丁

对于任何提供反馈的人，谢谢！
