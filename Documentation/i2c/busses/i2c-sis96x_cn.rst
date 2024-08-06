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

此 SMBus 专用驱动程序已知可在具有上述芯片组组合的主板上正常工作。该驱动程序是在没有 SiS 正式数据手册的情况下开发的。假设 SMBus 寄存器与 SiS630 的兼容，尽管它们位于一个完全不同的位置。感谢 Alexander Malysh <amalysh@web.de> 提供了 SiS630 的数据手册（和驱动程序）。
使用 `root` 用户运行命令 `lspci` 应该会生成类似下面的行： 

  00:00.0 主机桥接器: Silicon Integrated Systems [SiS]: 未知设备 0645
  00:02.0 ISA 桥接器: Silicon Integrated Systems [SiS] 85C503/5513
  00:02.1 SMBus: Silicon Integrated Systems [SiS]: 未知设备 0016

或者可能是这个：

  00:00.0 主机桥接器: Silicon Integrated Systems [SiS]: 未知设备 0645
  00:02.0 ISA 桥接器: Silicon Integrated Systems [SiS]: 未知设备 0961
  00:02.1 SMBus: Silicon Integrated Systems [SiS]: 未知设备 0016

（内核版本在 2.4.18 之后可能会填充“未知”项）

如果您看不到这些信息，请查看 quirk_sis_96x_smbus
（drivers/pci/quirks.c）（如果南桥检测失败也请查看）

我怀疑此驱动程序也可以为以下 SiS 芯片组工作：635 和 635T。如果有人拥有这些芯片的主板并且愿意冒着使原本稳定的内核崩溃的风险来推进这一驱动程序的发展，请联系我 mhoffman@lightlink.com 或者通过 linux-i2c 邮件列表：<linux-i2c@vger.kernel.org>。也请发送错误报告和成功案例。

待办事项
------

* 驱动程序不支持 SMBus 块读写；如果发现需要这种功能的情况，我可能会添加它们。

致谢
---------

Mark D. Studebaker <mdsxyz123@yahoo.com>
 - 设计提示和修复错误

Alexander Maylsh <amalysh@web.de>
 - 同上，再加上一份重要的数据手册...几乎是我真正想要的那一份

Hans-Günter Lütke Uphues <hg_lu@t-online.de>
 - 为 SiS735 提供补丁

Robert Zwerus <arzie@dds.nl>
 - 为 SiS645DX 进行测试

Kianusch Sayah Karadji <kianusch@sk-tech.net>
 - 为 SiS645DX/962 提供补丁

Ken Healy
 - 为 SiS655 提供补丁

对于所有给我反馈的人，非常感谢！
