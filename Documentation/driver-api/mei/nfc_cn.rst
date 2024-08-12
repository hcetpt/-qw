### SPDX 许可证标识符: GPL-2.0

#### MEI NFC
---

一些英特尔 8 和 9 系列芯片组支持通过英特尔管理引擎控制器连接的近场通信（NFC）设备。

MEI 客户端总线将 NFC 芯片暴露为 NFC 物理（phy）设备，并允许其与来自 Linux NFC 子系统的 Microread 和 NXP PN544 NFC 设备驱动程序绑定。
```dot
// 使用 DOT 语言绘制的 MEI NFC 图表
digraph NFC {
    cl_nfc -> me_cl_nfc;
    "drivers/nfc/mei_phy" -> cl_nfc [lhead=bus];
    "drivers/nfc/microread/mei" -> cl_nfc;
    "drivers/nfc/microread/mei" -> "drivers/nfc/mei_phy";
    "drivers/nfc/pn544/mei" -> cl_nfc;
    "drivers/nfc/pn544/mei" -> "drivers/nfc/mei_phy";
    "net/nfc" -> "drivers/nfc/microread/mei";
    "net/nfc" -> "drivers/nfc/pn544/mei";
    "neard" -> "net/nfc";
    cl_nfc [label="mei/bus(nfc)"];
    me_cl_nfc [label="me fw (nfc)"];
} 
```
**注释：**
- `cl_nfc` 代表 NFC 控制器层。
- `me_cl_nfc` 表示在管理引擎固件中的 NFC 功能。
- `drivers/nfc/mei_phy` 是指针对特定物理设备的驱动程序。
- `drivers/nfc/microread/mei` 和 `drivers/nfc/pn544/mei` 分别是 Microread 和 NXP PN544 的驱动程序。
- `net/nfc` 代表 NFC 网络栈。
- `neard` 是一个守护进程，用于处理 NFC 连接。
