========================
内核驱动 i2c-sis630
========================

支持的适配器：
  * Silicon Integrated Systems Corp（SiS）
    630 芯片组（数据手册：可在 http://www.sfr-fresh.com/linux 获取）
    730 芯片组
    964 芯片组
  * 可能还支持其他 SiS 芯片组？

作者：
        - Alexander Malysh <amalysh@web.de>
        - Amaury Decrême <amaury.decreme@gmail.com> - 支持 SiS964

模块参数
-----------------

==================      =====================================================
force = [1|0]           强制启用 SIS630。危险！
                        这对于未在上述列出的芯片组可能会有用，以检查是否适用于您的芯片组，
                        但是危险！

high_clock = [1|0]      强制将主机主时钟设置为 56KHz（默认值，即 BIOS 使用的值）。危险！这应该会稍微快一点，
			但会使某些系统冻结（例如我的笔记本电脑）
仅限 SIS630/730 芯片
==================      =====================================================


描述
-----------

此 SMBus 驱动已知可适用于上述列出的芯片组。
如果您在 `lspci` 输出中看到如下内容：

  00:00.0 主机桥接器：Silicon Integrated Systems [SiS] 630 主机 (版本 31)
  00:01.0 ISA 桥接器：Silicon Integrated Systems [SiS] 85C503/5513

或类似如下内容：

  00:00.0 主机桥接器：Silicon Integrated Systems [SiS] 730 主机 (版本 02)
  00:01.0 ISA 桥接器：Silicon Integrated Systems [SiS] 85C503/5513

或类似如下内容：

  00:00.0 主机桥接器：Silicon Integrated Systems [SiS] 760/M760 主机 (版本 02)
  00:02.0 ISA 桥接器：Silicon Integrated Systems [SiS] SiS964 [MuTIOL Media IO]
                            LPC 控制器 (版本 36)

那么此驱动程序适用于您的芯片组。

致谢
---------
Philip Edelbrock <phil@netroedge.com>
- 测试 SiS730 支持
Mark M. Hoffman <mhoffman@lightlink.com>
- 修复错误

对所有我可能遗漏的人；），谢谢！
