```
SPDX 许可证标识符: GPL-2.0

==============================================================
Davicom DM9102(A)/DM9132/DM9801 快速以太网驱动程序 for Linux
==============================================================

注意：此驱动程序没有维护者
本程序是自由软件；您可以根据由自由软件基金会发布的 GNU 通用公共许可证的条款重新分发它和/或修改它；可以是许可证的第 2 版，也可以（根据您的选择）是任何更新的版本。
本程序是希望其有用而分发的，但没有任何保证，甚至不包含隐含的适销性或适合某一特定目的的保证。详情请参见 GNU 通用公共许可证。
此驱动程序为 Davicom DM9102(A)/DM9132/DM9801 以太网卡提供了内核支持（CNET 10/100 以太网卡也使用了 Davicom 芯片组，因此该驱动程序也支持 CNET 卡）。如果您没有将此驱动程序编译为模块，它将在启动时自动加载，并打印类似以下的一行信息：

	dmfe: Davicom DM9xxx 网络驱动程序，版本 1.36.4（2002-01-17）

如果您将此驱动程序编译为模块，则需要在启动时加载它。您可以通过以下命令加载它：

	insmod dmfe

这将自动检测设备模式。这是建议的加载模块方式。或者，您可以在加载模块时传递一个 mode= 设置，例如：

	insmod dmfe mode=0 # 强制 10M 半双工
	insmod dmfe mode=1 # 强制 100M 半双工
	insmod dmfe mode=4 # 强制 10M 全双工
	insmod dmfe mode=5 # 强制 100M 全双工

接下来，您应该通过类似以下命令配置网络接口：

	ifconfig eth0 172.22.3.18
			^^^^^^^^^^
			您的 IP 地址

然后您可能需要通过以下命令修改默认路由表：

	route add default gw 172.22.3.1 eth0

现在您的以太网卡应该已经启动并运行。

TODO:

- 实现 pci_driver::suspend() 和 pci_driver::resume() 电源管理方法
- 在 64 位系统上进行测试
- 在大端字节序系统上检查并修复
- 测试并确保所有情况下 PCI 延迟正确

作者：

Sten Wang <sten_wang@davicom.com.tw>：原始作者

贡献者：

- Marcelo Tosatti <marcelo@conectiva.com.br>
- Alan Cox <alan@lxorguk.ukuu.org.uk>
- Jeff Garzik <jgarzik@pobox.com>
- Vojtech Pavlik <vojtech@suse.cz>
```
