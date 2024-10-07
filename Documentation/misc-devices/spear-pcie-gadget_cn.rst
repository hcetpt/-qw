SPDX 许可证标识符: GPL-2.0

========================
Spear PCIe Gadget 驱动程序
========================

作者
======
Pratyush Anand (pratyush.anand@gmail.com)

位置
======
driver/misc/spear13xx_pcie_gadget.c

支持的芯片:
===============
SPEAr1300
SPEAr1310

Menuconfig 选项:
==================
设备驱动程序
    各种设备
        SPEAr13XX 平台的 PCIe Gadget 支持

目的
=======
此驱动程序具有多个节点，可以通过 configfs 接口进行读取/写入。
其主要目的是将选定的双模 PCIe 控制器配置为设备，
然后编程其各种寄存器以将其配置为特定类型的设备。
此驱动程序可用于展示 SPEAr 的 PCIe 设备能力。
不同节点的描述如下：

节点的读取行为:
-----------------------

=============== ==============================================================
link 			提供 LTSSM 状态
int_type 		支持的中断类型
no_of_msi 		如果主机未启用 MSI，则为零。正值表示授予的 MSI 向量数量
vendor_id 		返回已编程的供应商 ID（十六进制）
device_id 		返回已编程的设备 ID（十六进制）
bar0_size: 		返回 BAR0 的大小（十六进制）
bar0_address 	返回 BAR0 映射区域的地址（十六进制）
bar0_rw_offset 	返回 bar0_data 将返回值的 BAR0 偏移量
bar0_data 		返回 bar0_rw_offset 处的数据
=============== ==============================================================

节点的写入行为:
------------------------

=============== ================================================================
link 			写入 UP 以启用 LTSSM，写入 DOWN 以禁用
int_type 		写入要配置的中断类型（int_type 可以为 INTA、MSI 或 NO_INT）。
			仅在您已经编程了 no_of_msi 节点时选择 MSI
no_of_msi 		所需的 MSI 向量数量
=============== ================================================================
```
inta		写入1以断言INTA，写入0以撤销断言
send_msi	写入要发送的MSI向量
vendor_id	写入要编程的供应商ID（十六进制）
device_id	写入要编程的设备ID（十六进制）
bar0_size	写入bar0的大小（十六进制）。默认的bar0大小为1000（十六进制）字节
bar0_address	写入bar0映射区域的地址（十六进制）。（默认的bar0映射为SYSRAM1[E0800000]。始终在编程bar地址之前编程bar大小。内核可能会为了对齐而修改bar大小和地址，因此在写入后读回bar大小和地址进行交叉检查）
bar0_rw_offset	写入bar0的偏移量，用于在该偏移量处写入bar0_data的值
bar0_data	写入要在bar0_rw_offset处写入的数据
```

节点编程示例
=============

按照以下方式编程所有PCIe寄存器，使得当此设备连接到PCIe主机时，主机将此设备视为1MB RAM：
```
# mount -t configfs none /Config
```

对于第n个PCIe设备控制器：
```
# cd /config/pcie_gadget.n/
```

现在这个目录中包含所有节点。
以下是翻译：

将程序供应商 ID 设置为 0x104a：

    # echo 104A >> vendor_id

将设备 ID 设置为 0xCD80：

    # echo CD80 >> device_id

将 BAR0 大小设置为 1MB：

    # echo 100000 >> bar0_size

检查已编程的 BAR0 大小：

    # cat bar0_size

将 BAR0 地址设置为 DDR (0x2100000)。这是要使 PCIe 主机可见的内存的物理地址。同样，任何其他外设也可以使 PCIe 主机可见。例如，如果你将 UART 的基地址设置为 BAR0 地址，那么当这个设备连接到主机时，它将作为 UART 可见。

    # echo 2100000 >> bar0_address

将中断类型设置为 INTA：

    # echo INTA >> int_type

现在进行链路连接：

    # echo UP >> link

必须确保，在对小工具进行链路连接后，才初始化主机并开始在其端口上搜索 PCIe 设备。

    /*等待链路连接完成*/
    # cat link

等待直到返回 UP

为了激活 INTA：

    # echo 1 >> inta

为了去激活 INTA：

    # echo 0 >> inta

如果使用 MSI 作为中断，设置所需的 MSI 向量数量（比如 4）：

    # echo 4 >> no_of_msi

选择 MSI 作为中断类型：

    # echo MSI >> int_type

现在进行链路连接：

    # echo UP >> link

等待链路连接完成：

    # cat link

应用程序可以重复读取此节点，直到找到 UP 链路为止。在两次读取之间可以休眠

等待直到 MSI 被启用：

    # cat no_of_msi

应返回 4（请求的 MSI 向量的数量）

发送 MSI 向量 2：

    # echo 2 >> send_msi
    # cd -

希望这对你有帮助！如果有更多需要翻译的内容或其他问题，请告诉我。
