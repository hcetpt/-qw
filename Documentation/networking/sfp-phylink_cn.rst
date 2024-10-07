SPDX 许可证标识符: GPL-2.0

=======
phylink
=======

概述
========

phylink 是一种机制，用于支持直接连接到 MAC 的热插拔网络模块，而无需在热插拔事件时重新初始化适配器。目前，phylink 支持传统的基于 phylib 的配置、固定链路配置以及 SFP（小型可插拔）模块。

操作模式
==================

phylink 有几种不同的操作模式，这些模式依赖于固件设置：
1. PHY 模式

   在 PHY 模式下，我们使用 phylib 读取当前的链路设置，并将它们传递给 MAC 驱动程序。我们期望 MAC 驱动程序按照指定的模式进行配置，而不启用任何链路协商功能。
2. 固定模式

   对于 MAC 驱动程序而言，固定模式与 PHY 模式相同。
3. 带内模式

   带内模式用于 802.3z、SGMII 和类似的接口模式。我们期望使用并遵循通过 SerDes 通道发送的带内协商或控制字。
举个例子，这意味着：

.. code-block:: none

  &eth {
    phy = <&phy>;
    phy-mode = "sgmii";
  };

不使用带内的 SGMII 信号。PHY 应当严格遵循其 :c:func:`mac_config` 函数中给出的设置。
链接应当在 :c:func:`mac_link_up` 和 :c:func:`mac_link_down` 函数中适当地强制打开或关闭。

.. code-block:: none

  &eth {
    managed = "in-band-status";
    phy = <&phy>;
    phy-mode = "sgmii";
  };

使用带内模式，在这种模式下，PHY 协商的结果通过 SGMII 控制字传递给 MAC，并且 MAC 应当确认该控制字。:c:func:`mac_link_up` 和 :c:func:`mac_link_down` 函数不得强制 MAC 一侧的链路上或下。

将网络驱动程序转换为 sfp/phylink 的简要指南
=========================================================

本指南简要描述了如何将网络驱动程序从 phylib 转换为 sfp/phylink 支持。请提交补丁以改进此文档。
1. 可选地将网络驱动程序的 phylib 更新函数拆分为两部分，分别处理链路断开和链路连接。这可以作为一个单独的准备提交来完成。
   一个较早的此类准备示例可以在 git 提交 `fc548b991fb0` 中找到，尽管当时是拆分为三部分；现在的链路连接部分包括根据链路设置配置 MAC。
   请参阅 :c:func:`mac_link_up` 获取更多信息。

2. 将以下内容替换为：

   ```
   select FIXED_PHY
   select PHYLIB
   ```

   替换为：

   ```
   select PHYLINK
   ```

   在驱动程序的 Kconfig 代码段中。

3. 向驱动程序的头文件列表中添加：

   ```
   #include <linux/phylink.h>
   ```

4. 向驱动程序的私有数据结构中添加：

   ```
   struct phylink *phylink;
   struct phylink_config phylink_config;
   ```

   我们将驱动程序的私有数据指针称为 `priv`，并将驱动程序的私有数据结构称为 `struct foo_priv`。

5. 替换以下函数：

   | 原始函数            | 替换函数                    |
   |-------------------|---------------------------|
   | phy_start(phydev) | phylink_start(priv->phylink) |
   | phy_stop(phydev)  | phylink_stop(priv->phylink)  |
   | phy_mii_ioctl(phydev, ifr, cmd) | phylink_mii_ioctl(priv->phylink, ifr, cmd) |
   | phy_ethtool_get_wol(phydev, wol) | phylink_ethtool_get_wol(priv->phylink, wol) |
   | phy_ethtool_set_wol(phydev, wol) | phylink_ethtool_set_wol(priv->phylink, wol) |
   | phy_disconnect(phydev) | phylink_disconnect_phy(priv->phylink) |

   请注意，某些函数必须在 rtnl 锁下调用，并且如果未这样做会发出警告。通常情况下这是正常的，除非这些函数是从驱动程序挂起/恢复路径调用的。

6. 添加或替换 ksettings 的获取/设置方法如下：

   ```c
   static int foo_ethtool_set_link_ksettings(struct net_device *dev,
                                             const struct ethtool_link_ksettings *cmd)
   {
       struct foo_priv *priv = netdev_priv(dev);

       return phylink_ethtool_ksettings_set(priv->phylink, cmd);
   }

   static int foo_ethtool_get_link_ksettings(struct net_device *dev,
                                             struct ethtool_link_ksettings *cmd)
   {
       struct foo_priv *priv = netdev_priv(dev);

       return phylink_ethtool_ksettings_get(priv->phylink, cmd);
   }
   ```

7. 将对以下内容的调用及其相关代码替换为：

   ```
   phy_dev = of_phy_connect(dev, node, link_func, flags, phy_interface);
   ```

   替换为：

   ```
   err = phylink_of_phy_connect(priv->phylink, node, flags);
   ```

   大部分情况下，`flags` 可以为零；如果 DT 节点 `node` 指定了 PHY，则这些标志将传递给此函数调用内部的 phy_attach_direct()。

   `node` 应该是包含网络 phy 属性、固定链接属性以及 sfp 属性的 DT 节点。
   固定链接的设置也应移除；这些由 phylink 内部处理。
`of_phy_connect()` 同样传递了一个用于链路更新的函数指针。这个函数被替换为下面第 (8) 点中描述的不同形式的 MAC 更新。

在 `phylink` 中，根据验证回调处理 PHY 的支持/通告设置，具体见下面第 (8) 点。
请注意，驱动程序不再需要存储 `phy_interface`，同时需要注意的是 `phy_interface` 变成了一个动态属性，就像速度、双工等设置一样。

最后，请注意 MAC 驱动程序不再直接访问 PHY；这是因为在 `phylink` 模型中，PHY 是动态的。

8. 在驱动程序中添加一个 `struct phylink_mac_ops` 实例，这是一个函数指针表，并实现这些函数。对于 `of_phy_connect` 的旧链路更新函数，它将变为三个方法：`mac_link_up`、`mac_link_down` 和 `mac_config`。如果已经执行了步骤 1，则功能会在那里被拆分。

重要的是，如果使用带内协商，`mac_link_up` 和 `mac_link_down` 不应阻止带内协商完成，因为这些函数是在带内链路状态变化时调用的——否则链路永远不会建立。

`mac_get_caps` 方法是可选的，如果提供，应该返回对于传递的 `interface` 模式所支持的 phylink MAC 功能。通常来说，没有实现此方法的必要。

`mac_link_state` 方法用于从 MAC 读取链路状态，并报告 MAC 当前使用的设置。这对于带内协商方法（如 1000base-X 和 SGMII）尤为重要。
### 翻译：

：c:func:`mac_link_up` 方法用于通知 MAC 链路已经建立。调用中包括了协商模式和接口，仅供参考。最终的链路参数（速度、双工模式和流控制/暂停设置）也会被提供，当 MAC 和 PCS 不是紧密集成时，或者设置不是来自带内协商时，这些参数应该用来配置 MAC。

：c:func:`mac_config` 方法用于更新 MAC 的请求状态，并且在修改 MAC 配置时应避免不必要的使链路断开。这意味着函数应该修改状态，并且只有在绝对需要改变 MAC 配置时才使链路断开。一个如何实现的例子可以在 ``drivers/net/ethernet/marvell/mvneta.c`` 中的 ：c:func:`mvneta_mac_config` 函数找到。

对于这些方法的更多信息，请参见 ：c:type:`struct phylink_mac_ops <phylink_mac_ops>` 中的内联文档。

9. 填充 ：c:type:`struct phylink_config <phylink_config>` 字段，引用与你的 ：c:type:`struct net_device <net_device>` 相关的 ：c:type:`struct device <device>`：

   ```c
   priv->phylink_config.dev = &dev.dev;
   priv->phylink_config.type = PHYLINK_NETDEV;
   ```

   填充你的 MAC 可以处理的各种速度、暂停和双工模式：

   ```c
   priv->phylink_config.mac_capabilities = MAC_SYM_PAUSE | MAC_10 | MAC_100 | MAC_1000FD;
   ```

10. 一些以太网控制器与 PCS（物理编码子层）块配对工作，PCS 可以处理编码/解码、链路建立检测和自动协商等功能。虽然有些 MAC 具有内部 PCS，其操作是透明的，但有些则需要专门的 PCS 配置才能使链路功能正常。在这种情况下，phylink 通过 ：c:type:`struct phylink_pcs <phylink_pcs>` 提供了 PCS 抽象。
    
    确定你的驱动程序是否有一个或多个内部 PCS 块，以及你的控制器是否可以使用内部连接到控制器的外部 PCS 块。
    
    如果你的控制器没有任何内部 PCS，则可以跳到步骤 11。
    
    如果你的以太网控制器包含一个或多个 PCS 块，在你的驱动程序私有数据结构中为每个 PCS 块创建一个 ：c:type:`struct phylink_pcs <phylink_pcs>` 实例：
    
    ```c
    struct phylink_pcs pcs;
    ```
    
    填充相关的 ：c:type:`struct phylink_pcs_ops <phylink_pcs_ops>` 来配置你的 PCS。创建一个 ：c:func:`pcs_get_state` 函数来报告带内的链路状态，一个 ：c:func:`pcs_config` 函数来根据 phylink 提供的参数配置你的 PCS，以及一个 ：c:func:`pcs_validate` 函数来向 phylink 报告所有可接受的配置参数：
    
    ```c
    struct phylink_pcs_ops foo_pcs_ops = {
            .pcs_validate = foo_pcs_validate,
            .pcs_get_state = foo_pcs_get_state,
            .pcs_config = foo_pcs_config,
    };
    ```
    
    安排将 PCS 链路状态中断转发到 phylink，通过以下方式：
    
    ```c
    phylink_pcs_change(pcs, link_is_up);
    ```
    
    其中 `link_is_up` 在链路当前处于活动状态时为真，否则为假。如果 PCS 无法提供这些中断，则应在创建 PCS 时设置 `pcs->pcs_poll = true;`。

11. 如果你的控制器依赖于或接受外部 PCS 的存在，该 PCS 由其自己的驱动程序控制，在你的驱动程序私有数据结构中添加一个指向 phylink_pcs 实例的指针：
    
    ```c
    struct phylink_pcs *pcs;
    ```
    
    获取实际 PCS 实例的方式取决于平台，一些 PCS 位于 MDIO 总线上，可以通过传递指向相应的 ：c:type:`struct mii_bus <mii_bus>` 和 PCS 在该总线上的地址来获取。在这个例子中，我们假设控制器连接到一个 Lynx PCS 实例：
    
    ```c
    priv->pcs = lynx_pcs_create_mdiodev(bus, 0);
    ```
    
    一些 PCS 可以基于固件信息来获取：
    
    ```c
    priv->pcs = lynx_pcs_create_fwnode(of_fwnode_handle(node));
    ```

12. 填充 ：c:func:`mac_select_pcs` 回调并将其添加到你的 ：c:type:`struct phylink_mac_ops <phylink_mac_ops>` 操作集中。此函数必须返回一个指向相关 ：c:type:`struct phylink_pcs <phylink_pcs>` 的指针，该指针将用于请求的链路配置：
    
    ```c
    static struct phylink_pcs *foo_select_pcs(struct phylink_config *config,
                                              phy_interface_t interface)
    {
            struct foo_priv *priv = container_of(config, struct foo_priv,
                                                 phylink_config);

            if ( /* 'interface' 需要一个 PCS 才能正常工作 */ )
                    return priv->pcs;

            return NULL;
    }
    ```
    
    查看 ：c:func:`mvpp2_select_pcs` 以获取具有多个内部 PCS 的驱动程序示例。

13. 填充所有 ：c:type:`phy_interface_t <phy_interface_t>`（即所有 MAC 到 PHY 的链路模式），你的 MAC 可以输出。下面的例子展示了一个 MAC 可以处理所有 RGMII 模式、SGMII 和 1000BaseX 的配置：
    
    ```c
    phy_interface_set_rgmii(priv->phylink_config.supported_interfaces);
    __set_bit(PHY_INTERFACE_MODE_SGMII,
              priv->phylink_config.supported_interfaces);
    __set_bit(PHY_INTERFACE_MODE_1000BASEX,
              priv->phylink_config.supported_interfaces);
    ```
    
    你必须根据你的 MAC 和所有与此 MAC 关联的 PCS 的能力进行调整，而不仅仅是你想使用的接口。

14. 从探测函数中移除对 PHY 的 of_parse_phandle() 调用、对固定链路的 of_phy_register_fixed_link() 调用等，并替换为：
    
    ```c
    struct phylink *phylink;

    phylink = phylink_create(&priv->phylink_config, node, phy_mode, &phylink_ops);
    if (IS_ERR(phylink)) {
            err = PTR_ERR(phylink);
            fail probe;
    }

    priv->phylink = phylink;
    ```
    
    并在适当的探测失败路径和移除路径中安排销毁 phylink，通过调用：
    
    ```c
    phylink_destroy(priv->phylink);
    ```

15. 安排将 MAC 链路状态中断转发到 phylink，通过以下方式：
    
    ```c
    phylink_mac_change(priv->phylink, link_is_up);
    ```
    
    其中 `link_is_up` 在链路当前处于活动状态时为真，否则为假。
16. 验证驱动程序是否调用了以下函数：

```
netif_carrier_on()
netif_carrier_off()
```

因为这些调用会干扰 phylink 对链路状态的跟踪，并导致 phylink 忽略通过 :c:func:`mac_link_up` 和 :c:func:`mac_link_down` 方法的调用。

网络驱动程序应通过其挂起/恢复路径调用 phylink_stop() 和 phylink_start()，这可以确保在必要时调用适当的 :c:type:`struct phylink_mac_ops <phylink_mac_ops>` 方法。

关于 DT 中 SFP 笼子的详细信息，请参阅内核源代码树中的绑定文档：
``Documentation/devicetree/bindings/net/sff,sfp.yaml``
