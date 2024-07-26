=========================
内核驱动 i2c-nforce2
=========================

支持的适配器：
  * nForce2 MCP                10de:0064
  * nForce2 Ultra 400 MCP      10de:0084
  * nForce3 Pro150 MCP         10de:00D4
  * nForce3 250Gb MCP          10de:00E4
  * nForce4 MCP                10de:0052
  * nForce4 MCP-04             10de:0034
  * nForce MCP51               10de:0264
  * nForce MCP55               10de:0368
  * nForce MCP61               10de:03EB
  * nForce MCP65               10de:0446
  * nForce MCP67               10de:0542
  * nForce MCP73               10de:07D8
  * nForce MCP78S              10de:0752
  * nForce MCP79               10de:0AA2

数据手册：
           没有公开，但似乎与AMD-8111 SMBus 2.0适配器相似
作者：
	- Hans-Frieder Vogt <hfvogt@gmx.net>,
	- Thomas Leibold <thomas@plx.com>,
        - Patrick Dreker <patrick@dreker.de>

描述
-----------

i2c-nforce2是为nVidia nForce2 MCP中包含的SMBus设计的驱动程序。
如果你的`lspci -v`列出的内容类似于以下内容：

  00:01.1 SMBus: nVidia Corporation: 未知设备 0064 (版本a2)
          子系统：华硕电脑股份有限公司: 未知设备 0c11
          标志：66MHz，快速设备选择，IRQ 5
          I/O端口位于c000 [大小=32]
          能力：<仅对root用户可用>

那么这个驱动应该能够支持你主板上的SMBus。
注意事项
-----

nForce2芯片组中的SMBus适配器似乎与AMD-8111南桥中的SMBus 2.0适配器非常相似。但是，我只能通过直接I/O访问使驱动程序工作，这与AMD-8111的EC接口不同。在华硕A7N8X上测试过。华硕A7N8X的ACPI DSDT表列出了两个SMBus，这两个都被此驱动支持。
