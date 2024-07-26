### SPDX 许可证标识符: GPL-2.0
### 包含: <isonum.txt>

=======================
DPAA2 MAC / PHY 支持
=======================

:版权所有: © 2019 NXP

概述
------

DPAA2 MAC / PHY 支持由一系列API组成，这些API帮助DPAA2网络驱动（dpaa2-eth、dpaa2-ethsw）与PHY库交互。
DPAA2 软件架构
---------------------------

在其他DPAA2对象中，fsl-mc总线导出了DPNI对象（抽象了一个网络接口）和DPMAC对象（抽象了一个MAC）。dpaa2-eth驱动程序探测DPNI对象，并借助phylink连接和配置一个DPMAC对象。
数据连接可以在DPNI和DPMAC之间建立，也可以在两个DPNIs之间建立。根据连接类型，netif_carrier_[on/off]由dpaa2-eth驱动程序直接处理或由phylink处理。

```plaintext
MC固件提供的抽象链路状态信息来源

                                               +--------------------------------------+
  +------------+                  +---------+  |                           xgmac_mdio |
  | net_device |                  | phylink |--|  +-----+  +-----+  +-----+  +-----+  |
  +------------+                  +---------+  |  | PHY |  | PHY |  | PHY |  | PHY |  |
        |                             |        |  +-----+  +-----+  +-----+  +-----+  |
      +------------------------------------+   |                    外部MDIO总线 |
      |            dpaa2-eth               |   +--------------------------------------+
      +------------------------------------+
        |                             |                                           Linux
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        |                             |                                     MC 固件
        |              /|             V
  +----------+        / |       +----------+
  |          |       /  |       |          |
  |          |       |  |       |          |
  |   DPNI   |<------|  |<------|   DPMAC  |
  |          |       |  |       |          |
  |          |       \  |<---+  |          |
  +----------+        \ |    |  +----------+
                       \|    |
                             |
           +--------------------------------------+
           | MC固件轮询MAC PCS获取链路状态     |
           |  +-----+  +-----+  +-----+  +-----+  |
           |  | PCS |  | PCS |  | PCS |  | PCS |  |
           |  +-----+  +-----+  +-----+  +-----+  |
           |                    内部MDIO总线     |
           +--------------------------------------+
```

根据MC固件配置设置，每个MAC可能处于以下两种模式之一：

- DPMAC_LINK_TYPE_FIXED: 链路状态管理完全由MC固件通过轮询MAC PCS处理。无需注册phylink实例，dpaa2-eth驱动程序根本不会绑定到连接的dpmac对象。
- DPMAC_LINK_TYPE_PHY: MC固件等待链路状态更新事件，但实际上这些事件严格地在dpaa2-mac（基于phylink）与其连接的net_device驱动程序（dpaa2-eth、dpaa2-ethsw）之间传递，有效地绕过了固件。

实现
--------------

在探测时或当DPNI的端点动态更改时，dpaa2-eth负责判断对等对象是否为DPMAC，并且如果是，则使用dpaa2_mac_connect() API将其与PHYLINK集成，该API将执行以下操作：

- 在设备树中查找与PHYLINK兼容的绑定（phy-handle）
- 将创建一个与接收到的net_device关联的PHYLINK实例
- 使用phylink_of_phy_connect()连接到PHY

实现了以下phylink_mac_ops回调：

- .validate()将在phy_interface_t为RGMII_*时仅用MAC能力填充支持的链路模式（目前，这是驱动程序唯一支持的链路类型）
- .mac_config()将使用dpmac_set_link_state() MC固件API配置新配置下的MAC
- .mac_link_up() / .mac_link_down()将使用上述相同的API更新MAC链路
当dpaa2-eth驱动程序解绑或DPNI对象从DPMAC断开连接时，dpaa2-eth驱动程序调用dpaa2_mac_disconnect()，这反过来会从PHY断开连接并销毁PHYLINK实例。

对于DPNI-DPMAC连接，“ip link set dev eth0 up”将启动以下操作序列：

(1) 从.dev_open()调用phylink_start()
在PHYLINK连接的情况下，操作序列如下：

(2) 调用 `.mac_config()` 和 `.mac_link_up()` 回调函数由PHYLINK发起。
(3) 为了配置硬件MAC（HW MAC），调用MC固件API `dpmac_set_link_state()`。
(4) 固件最终将按照新的配置设置硬件MAC。
(5) 对于关联的 `net_device`，直接从PHYLINK调用 `netif_carrier_on()`。
(6) `dpaa2-eth` 驱动处理 `LINK_STATE_CHANGE` 中断，根据暂停帧设置启用/禁用接收尾丢弃功能。

```plaintext
+---------+               +---------+
| PHYLINK |-------------->|  eth0   |
+---------+           (5) +---------+
(1) ^  |
      |  |
      |  v (2)
+-----------------------------------+
|             dpaa2-eth             |
+-----------------------------------+
         |                    ^ (6)
         |                    |
         v (3)                |
+---------+---------------+---------+
|  DPMAC  |               |  DPNI   |
+---------+               +---------+
|            MC Firmware            |
+-----------------------------------+
         |
         |
         v (4)
+-----------------------------------+
|             HW MAC                |
+-----------------------------------+
```

对于DPNI-DPNI连接，常见的操作序列如下：

(1) 执行 `ip link set dev eth0 up`
(2) 在关联的 `fsl_mc_device` 上调用 `dpni_enable()` MC API。
(3) 执行 `ip link set dev eth1 up`
(4) 在关联的 `fsl_mc_device` 上调用 `dpni_enable()` MC API。
(5) 当前运行的链路状态变为UP时，两个 `dpaa2-eth` 驱动实例都会接收到 `LINK_STATE_CHANGED` 中断。
(6) 在 `link_state_update()` 中调用 `netif_carrier_on()` 以更新关联的 `net_device`。

```plaintext
+---------+               +---------+
|  eth0   |               |  eth1   |
+---------+               +---------+
      |  ^                     ^  |
      |  |                     |  |
(1) v  | (6)             (6) |  v (3)
+---------+               +---------+
|dpaa2-eth|               |dpaa2-eth|
+---------+               +---------+
      |  ^                     ^  |
      |  |                     |  |
(2) v  | (5)             (5) |  v (4)
+---------+---------------+---------+
|  DPNI   |               |  DPNI   |
+---------+               +---------+
|            MC Firmware            |
+-----------------------------------+
```

导出的API
----------

任何驱动DPMAC对象端点的DPAA2驱动都应服务 `_EVENT_ENDPOINT_CHANGED` 中断，并使用以下列出的API在必要时连接或断开与相关联的DPMAC的连接：

- `int dpaa2_mac_connect(struct dpaa2_mac *mac);`
- `void dpaa2_mac_disconnect(struct dpaa2_mac *mac);`

只有当对端的DPMAC不是 `TYPE_FIXED` 类型时才需要进行PHYLINK集成。这意味着它要么是 `TYPE_PHY` 类型，要么是 `TYPE_BACKPLANE` 类型（区别在于，在 `TYPE_BACKPLANE` 模式下，MC固件不会访问PCS寄存器）。可以使用以下辅助函数来检查这个条件：

- `static inline bool dpaa2_mac_is_type_phy(struct dpaa2_mac *mac);`

在连接到MAC之前，调用者必须分配并填充 `dpaa2_mac` 结构体，其中包含关联的 `net_device`、要使用的MC门户指针以及实际的 `fsl_mc_device` 结构（对应于DPMAC）。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
