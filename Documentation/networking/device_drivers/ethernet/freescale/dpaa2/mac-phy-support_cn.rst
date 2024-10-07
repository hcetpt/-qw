SPDX 许可声明标识符: GPL-2.0
.. include:: <isonum.txt>

=======================
DPAA2 MAC / PHY 支持
=======================

:版权所有: |copy| 2019 NXP

概述
------
DPAA2 MAC / PHY 支持由一组API组成，这些API帮助DPAA2网络驱动（dpaa2-eth、dpaa2-ethsw）与PHY库进行交互。

DPAA2 软件架构
---------------------------
与其他DPAA2对象一样，fsl-mc总线导出了DPNI对象（抽象网络接口）和DPMAC对象（抽象MAC）。dpaa2-eth驱动会探测DPNI对象，并通过phylink连接和配置一个DPMAC对象。
数据连接可以在DPNI和DPMAC之间或两个DPNI之间建立。根据连接类型，netif_carrier_[on/off]由dpaa2-eth驱动直接处理或由phylink处理。
.. code-block:: none

  由MC固件呈现的抽象链路状态信息来源

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
        |                             |                                     MC固件
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
           +--------------------------------------

根据MC固件配置设置，每个MAC可能处于以下两种模式之一：

- DPMAC_LINK_TYPE_FIXED：链路状态管理完全由MC固件通过轮询MAC PCS来处理。无需注册phylink实例，dpaa2-eth驱动根本不会绑定到连接的dpmac对象。
- DPMAC_LINK_TYPE_PHY：MC固件等待链路状态更新事件，但实际上这些事件严格地在dpaa2-mac（基于phylink）与其附加的net_device驱动（dpaa2-eth、dpaa2-ethsw）之间传递，从而绕过了固件。

实现
--------------
在探测时或当DPNI的端点动态更改时，dpaa2-eth负责确定对等对象是否为DPMAC，并且如果是这种情况，则使用dpaa2_mac_connect() API将其与PHYLINK集成，该API将执行以下操作：

- 查找设备树以找到PHYLINK兼容的绑定（phy-handle）
- 创建与接收到的net_device关联的PHYLINK实例
- 使用phylink_of_phy_connect()连接到PHY

实现了以下phylink_mac_ops回调：

- .validate()仅当phy_interface_t是RGMII_*时（目前这是唯一支持的链路类型），将用MAC功能填充支持的链路模式
- .mac_config()将使用dpmac_set_link_state() MC固件API配置新的MAC配置
- .mac_link_up() / .mac_link_down()将使用上述相同的API更新MAC链接

在驱动程序解除绑定或DPNI对象从DPMAC断开连接时，dpaa2-eth驱动程序调用dpaa2_mac_disconnect()，这反过来会从PHY断开连接并销毁PHYLINK实例。
在DPNI-DPMAC连接的情况下，执行'ip link set dev eth0 up'将启动以下操作序列：

(1) 从.dev_open()调用phylink_start()
### 翻译

#### 第一部分：PHYLINK 连接序列

1. `ip link set dev eth0 up` 命令执行后：
   - (2) `.mac_config()` 和 `.mac_link_up()` 回调由 PHYLINK 调用。
   - (3) 为了配置硬件 MAC，调用 MC Firmware API `dpmac_set_link_state()`。
   - (4) 固件最终会将硬件 MAC 设置为新的配置。
   - (5) 直接从 PHYLINK 对关联的 `net_device` 调用 `netif_carrier_on()`。
   - (6) `dpaa2-eth` 驱动处理 `LINK_STATE_CHANGE` 中断，根据暂停帧设置启用或禁用 RX 尾丢弃。

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

#### 第二部分：DPNI-DPNI 连接操作序列

对于 DPNI-DPNI 连接，常见的操作序列如下：

1. `ip link set dev eth0 up`
2. 在关联的 `fsl_mc_device` 上调用 `dpni_enable()` MC API。
3. `ip link set dev eth1 up`
4. 在关联的 `fsl_mc_device` 上调用 `dpni_enable()` MC API。
5. `dpaa2-eth` 驱动的两个实例都会收到 `LINK_STATE_CHANGED` 中断，因为现在操作链接状态已变为 UP。
6. 在从 `link_state_update()` 出口的 `net_device` 上调用 `netif_carrier_on()`。

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

### 导出的 API

任何驱动 DPMAC 对象端点的 DPAA2 驱动应服务其 `_EVENT_ENDPOINT_CHANGED` 中断，并在必要时使用以下列出的 API 连接到或断开与关联的 DPMAC 的连接：

- `int dpaa2_mac_connect(struct dpaa2_mac *mac);`
- `void dpaa2_mac_disconnect(struct dpaa2_mac *mac);`

只有当关联的 DPMAC 不是 `TYPE_FIXED` 类型时才需要 PHYLINK 集成。这意味着它可能是 `TYPE_PHY` 或 `TYPE_BACKPLANE` 类型（区别在于 `TYPE_BACKPLANE` 模式下，MC 固件不访问 PCS 寄存器）。可以使用以下辅助函数检查此条件：

- `static inline bool dpaa2_mac_is_type_phy(struct dpaa2_mac *mac);`

在连接到 MAC 之前，调用者必须分配并填充 `dpaa2_mac` 结构体，包括关联的 `net_device`、要使用的 MC portal 指针以及实际的 `fsl_mc_device` 结构体。
当然，请提供你需要翻译的文本。
