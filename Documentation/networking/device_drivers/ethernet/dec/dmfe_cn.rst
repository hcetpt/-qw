===============================
Linux 下的 Davicom DM9102(A)/DM9132/DM9901 快速以太网驱动程序
===============================

注意：此驱动程序没有维护者。
本程序为自由软件；您可以在 GNU 通用公共许可证（由自由软件基金会发布）条款下重新分发它和/或修改它；无论是第 2 版，还是（按您的选择）任何以后的版本。
本程序是希望它能有所帮助而分发的，但没有任何形式的担保，甚至不包含隐含的适销性或适用于特定目的的担保。有关详细信息，请参阅 GNU 通用公共许可证。
此驱动程序为 Davicom DM9102(A)/DM9132/DM9901 以太网卡提供了内核支持（CNET 10/100 以太网卡也使用了 Davicom 芯片组，因此该驱动程序同样支持 CNET 卡）。如果您没有将此驱动程序编译为模块，则在启动时会自动加载，并打印出类似以下内容的信息：

    dmfe: Davicom DM9xxx 网络驱动程序, 版本 1.36.4 (2002-01-17)

如果您已将此驱动程序编译为模块，则需要在启动时手动加载。您可以使用以下命令来加载它：

    insmod dmfe

这样它会自动检测设备模式。这是推荐的加载模块的方式。或者，您也可以在加载模块时传递一个 mode= 设置，例如：

    insmod dmfe mode=0 # 强制 10M 半双工
    insmod dmfe mode=1 # 强制 100M 半双工
    insmod dmfe mode=4 # 强制 10M 全双工
    insmod dmfe mode=5 # 强制 100M 全双工

接下来，您应该使用类似的命令配置您的网络接口：

    ifconfig eth0 172.22.3.18
                 ^^^^^^^^^^^
                您的 IP 地址

然后您可能需要通过命令修改默认路由表：

    route add default gw 172.22.3.18 eth0

现在您的以太网卡应该可以正常工作了。

待办事项：
- 实现 pci_driver::suspend() 和 pci_driver::resume() 的电源管理方法
- 在 64 位系统上进行测试
- 在大端序系统上检查并修复
- 测试并确保 PCI 延迟对于所有情况都是正确的

作者：
- Sten Wang <sten_wang@davicom.com.tw > : 原始作者

贡献者：
- Marcelo Tosatti <marcelo@conectiva.com.br>
- Alan Cox <alan@lxorguk.ukuu.org.uk>
- Jeff Garzik <jgarzik@pobox.com>
- Vojtech Pavlik <vojtech@suse.cz>
