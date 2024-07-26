SPDX 许可证标识符: GPL-2.0

=====

phylink
=====

概述
=====

phylink 是一种机制，用于支持直接连接到介质访问控制（MAC）的热插拔网络模块，无需在热插事件时重新初始化适配器。phylink 目前支持传统的 phylib 基础设置、固定链路设置以及 SFP（小型可插拔）模块。
操作模式
=====

phylink 有几种不同的操作模式，这些模式取决于固件设置：
1. PHY 模式

   在 PHY 模式下，我们使用 phylib 来从 PHY 读取当前链路设置，并将它们传递给 MAC 驱动程序。我们期望 MAC 驱动程序配置指定的模式，且不启用链路上的任何协商功能。
2. 固定模式

   对于 MAC 驱动程序而言，固定模式与 PHY 模式相同。
3. 内带模式

   内带模式适用于 802.3z、SGMII 等类似的接口模式。我们期望使用并尊重通过 SerDes 通道发送的内带协商或控制字。

例如，以下代码：

```none
&eth {
    phy = <&phy>;
    phy-mode = "sgmii";
};
```

表示不使用内带 SGMII 信号。PHY 应当遵循其 `mac_config` 函数中给出的确切设置。链接应在 `mac_link_up` 和 `mac_link_down` 函数中适当地强制打开或关闭。

而以下代码：

```none
&eth {
    managed = "in-band-status";
    phy = <&phy>;
    phy-mode = "sgmii";
};
```

表示使用内带模式，在这种模式下，PHY 的协商结果通过 SGMII 控制字传递给 MAC，并且 MAC 预期会确认控制字。`mac_link_up` 和 `mac_link_down` 函数不应强制 MAC 一侧的链接打开和关闭。

将网络驱动程序转换为 sfp/phylink 的大致指南
=================================================

本指南简要描述了如何将网络驱动程序从 phylib 转换为 sfp/phylink 支持。请提交补丁以改进此文档。
1. 可选地将网络驱动程序的 phylib 更新函数拆分为处理链路断开和链路连接的两部分。这可以作为一个单独的预备提交来完成。
   一个较早的这种预备工作的示例可以在 Git 提交 `fc548b991fb0` 中找到，尽管当时是将其拆分为三部分；现在链接连接的部分还包括为链接设置配置 MAC。
   更多相关信息，请参见 :c:func:`mac_link_up`
2. 将以下内容替换为：

   替换前：
   
   ```
   select FIXED_PHY
   select PHYLIB
   ```

   替换后：
   
   ```
   select PHYLINK
   ```

   在驱动程序的 Kconfig 语句中进行替换。
3. 在驱动程序的头文件列表中添加：

   ```
   #include <linux/phylink.h>
   ```
4. 在驱动程序的私有数据结构中添加：

   ```
   struct phylink *phylink;
   struct phylink_config phylink_config;
   ```

   下文中我们将驱动程序的私有数据指针称为 `priv`，而驱动程序的私有数据结构称为 `struct foo_priv`。
5. 替换以下函数：

   | 原始函数            | 替换函数                        |
   |-------------------|-------------------------------|
   | phy_start(phydev)  | phylink_start(priv->phylink)  |
   | phy_stop(phydev)   | phylink_stop(priv->phylink)   |
   | phy_mii_ioctl(phydev, ifr, cmd) | phylink_mii_ioctl(priv->phylink, ifr, cmd) |
   | phy_ethtool_get_wol(phydev, wol) | phylink_ethtool_get_wol(priv->phylink, wol) |
   | phy_ethtool_set_wol(phydev, wol) | phylink_ethtool_set_wol(priv->phylink, wol) |
   | phy_disconnect(phydev)  | phylink_disconnect_phy(priv->phylink) |

   请注意，其中一些函数必须在 rtnl 锁定下调用，并且如果没有这样做会发出警告。通常情况下这都是适用的，除非这些函数是从驱动程序挂起/恢复路径中调用的。
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

7. 替换对以下函数的调用：

   替换前：
   
   ```
   phy_dev = of_phy_connect(dev, node, link_func, flags, phy_interface);
   ```

   替换后：
   
   ```
   err = phylink_of_phy_connect(priv->phylink, node, flags);
   ```

   大多数情况下，`flags` 可以设为零；如果在设备树 (DT) 节点 `node` 中指定了 PHY，则这些标志会被传递给此函数调用中的 `phy_attach_direct()` 函数。
   `node` 应该是包含网络 PHY 属性、固定链接属性以及 SFP 属性的设备树节点。
   固定链接的设置也应该被移除；这些由 phylink 内部处理。
`of_phy_connect()`也被传递了一个用于链接更新的函数指针。
这个函数被一种不同的MAC更新形式所替代，如下在(8)中所述。
对于PHY支持/通告的操控是在phylink中进行的，基于验证回调（validate callback），详情请见下文(8)。
请注意，驱动程序不再需要存储“phy_interface”，同时请注意，“phy_interface”变成了一种动态属性，就像速度、双工等设置一样。
最后，请注意MAC驱动程序不再直接访问PHY；这是因为在phylink模型中，PHY可以是动态的。

8. 在驱动程序中添加一个`struct phylink_mac_ops <phylink_mac_ops>`实例，这是一个函数指针表，并实现这些函数。原本为`of_phy_connect`提供的旧链接更新函数现在变为三个方法：`mac_link_up`、`mac_link_down`以及`mac_config`。如果执行了步骤1，则功能已经在那一步中被拆分。
重要的是，如果使用了带内协商，在`mac_link_up`和`mac_link_down`中不应阻止带内协商完成，因为这些函数会在带内链接状态发生变化时被调用——否则链接将永远不会建立。
`mac_get_caps`方法是可选的，如果提供，应返回针对传递的`interface`模式所支持的phylink MAC能力。通常来说，没有实施此方法的必要。
`mac_link_state`方法用于从MAC读取链接状态，并报告MAC当前正在使用的设置。这对于像1000base-X和SGMII这样的带内协商方法尤为重要。
Phylink会结合`interface`的允许能力来使用这些能力，以确定允许的ethtool链接模式。
`:c:func:`mac_link_up` 方法用于通知介质访问控制层（MAC）链路已建立。此调用仅为了参考而包含了协商模式和接口信息。最终确定的链路参数（如速度、双工模式以及流控/暂停启用设置）也会被提供，当MAC与物理编码子层（PCS）不紧密集成时，或者当这些设置不是来自带内协商时，这些参数应被用来配置MAC。

`:c:func:`mac_config` 方法用于更新MAC至请求的状态，并且在修改MAC配置时应避免不必要的使链路下线。这意味着该函数应该修改状态，并且只在绝对必要更改MAC配置时才使链路下线。一个如何实现这一点的例子可以在 `drivers/net/ethernet/marvell/mvneta.c` 文件中的 `:c:func:`mvneta_mac_config` 函数中找到。

对于这些方法的更多信息，请参阅 `:c:type:`struct phylink_mac_ops <phylink_mac_ops>` 的内联文档。

9. 使用指向与您的 `:c:type:`struct net_device <net_device>` 关联的 `:c:type:`struct device <device>` 的引用填充 `:c:type:`struct phylink_config <phylink_config>` 的字段：

   ```c
   priv->phylink_config.dev = &dev.dev;
   priv->phylink_config.type = PHYLINK_NETDEV;
   ```

   填充您的MAC可以处理的各种速度、暂停和双工模式：

   ```c
   priv->phylink_config.mac_capabilities = MAC_SYM_PAUSE | MAC_10 | MAC_100 | MAC_1000FD;
   ```

10. 一些以太网控制器与物理编码子层（PCS）块配合工作，后者可以处理包括编码/解码、链路建立检测和自动协商在内的多种功能。虽然有些MAC具有内部PCS，其操作是透明的，但其他一些则需要专门的PCS配置才能使链路正常工作。在这种情况下，phylink通过 `:c:type:`struct phylink_pcs <phylink_pcs>` 提供了PCS抽象。
    
    确定您的驱动程序是否有一个或多个内部PCS模块，以及/或者您的控制器是否可以使用一个可能与控制器内部连接的外部PCS模块。
    
    如果您的控制器没有任何内部PCS，您可以跳到步骤11。
    
    如果您的以太网控制器包含一个或多个PCS模块，在您的驱动程序私有数据结构中为每个PCS模块创建一个 `:c:type:`struct phylink_pcs <phylink_pcs>` 实例：
    
    ```c
    struct phylink_pcs pcs;
    ```
    
    填充相关的 `:c:type:`struct phylink_pcs_ops <phylink_pcs_ops>` 来配置您的PCS。创建一个 `:c:func:`pcs_get_state` 函数来报告带内链路状态，一个 `:c:func:`pcs_config` 函数根据phylink提供的参数来配置您的PCS，以及一个 `:c:func:`pcs_validate` 函数向phylink报告所有接受的PCS配置参数：
    
    ```c
    struct phylink_pcs_ops foo_pcs_ops = {
            .pcs_validate = foo_pcs_validate,
            .pcs_get_state = foo_pcs_get_state,
            .pcs_config = foo_pcs_config,
    };
    ```
    
    安排将PCS链路状态中断转发给phylink，如下所示：
    
    ```c
    phylink_pcs_change(pcs, link_is_up);
    ```
    
    其中 `link_is_up` 在链路当前处于活动状态时为真，否则为假。如果PCS无法提供这些中断，则在创建PCS时应该设置 `pcs->pcs_poll = true;`

11. 如果您的控制器依赖于或接受存在一个由其自身驱动程序控制的外部PCS，那么在您的驱动程序私有数据结构中添加一个指向phylink_pcs实例的指针：
    
    ```c
    struct phylink_pcs *pcs;
    ```
    
    获取实际PCS实例的方式取决于平台，一些PCS位于MDIO总线上，可以通过传递指向相应的 `:c:type:`struct mii_bus <mii_bus>` 和PCS在该总线上的地址来获取。在这个例子中，我们假设控制器连接到了一个Lynx PCS实例：
    
    ```c
    priv->pcs = lynx_pcs_create_mdiodev(bus, 0);
    ```
    
    一些PCS可以根据固件信息获取：
    
    ```c
    priv->pcs = lynx_pcs_create_fwnode(of_fwnode_handle(node));
    ```
    
12. 填充 `:c:func:`mac_select_pcs` 回调并将其添加到您的 `:c:type:`struct phylink_mac_ops <phylink_mac_ops>` 操作集中。此函数必须返回一个指向相关 `:c:type:`struct phylink_pcs <phylink_pcs>` 的指针，该指针将用于请求的链路配置：
    
    ```c
    static struct phylink_pcs *foo_select_pcs(struct phylink_config *config,
                                              phy_interface_t interface)
    {
            struct foo_priv *priv = container_of(config, struct foo_priv,
                                                 phylink_config);

            if ( /* 'interface' 需要一个PCS才能正常工作 */ )
                    return priv->pcs;

            return NULL;
    }
    ```
    
    可以查看 `:c:func:`mvpp2_select_pcs` 作为具有多个内部PCS的驱动程序的一个示例。

13. 填充所有 `:c:type:`phy_interface_t <phy_interface_t>`（即所有MAC到PHY链接模式），您的MAC可以输出。以下示例显示了一个MAC可以处理所有RGMII模式、SGMII和1000BaseX配置的情况：
    
    您必须根据您的MAC及其所有关联的PCS的能力来调整这些内容，而不仅仅是您希望使用的接口：
    
    ```c
    phy_interface_set_rgmii(priv->phylink_config.supported_interfaces);
    __set_bit(PHY_INTERFACE_MODE_SGMII,
              priv->phylink_config.supported_interfaces);
    __set_bit(PHY_INTERFACE_MODE_1000BASEX,
              priv->phylink_config.supported_interfaces);
    ```

14. 从探测函数中删除对PHY的of_parse_phandle()调用，为固定链接注册的of_phy_register_fixed_link()等，并替换为：
    
    ```c
    struct phylink *phylink;

    phylink = phylink_create(&priv->phylink_config, node, phy_mode, &phylink_ops);
    if (IS_ERR(phylink)) {
        err = PTR_ERR(phylink);
        goto fail_probe;
    }

    priv->phylink = phylink;
    ```
    
    并且适当安排在探测失败路径中销毁phylink以及在移除路径中也通过调用：
    
    ```c
    phylink_destroy(priv->phylink);
    ```

15. 安排将MAC链路状态中断转发给phylink，如下所示：
    
    ```c
    phylink_mac_change(priv->phylink, link_is_up);
    ```
    
    其中 `link_is_up` 在链路当前处于活动状态时为真，否则为假。
16. 确认驱动程序不要调用：

``netif_carrier_on()`` 
``netif_carrier_off()``

因为这些函数会干扰 phylink 对链路状态的跟踪，并导致 phylink 忽略通过以下方法的调用:
``c:func:`mac_link_up` 和 ``c:func:`mac_link_down```

网络驱动程序应该在其挂起/恢复路径中调用 ``phylink_stop()`` 和 ``phylink_start()``，这可以确保在必要时调用正确的 ``c:type:`struct phylink_mac_ops <phylink_mac_ops>``` 方法。

关于描述 DT 中 SFP 笼的信息，请参阅内核源码树中的绑定文档：
``Documentation/devicetree/bindings/net/sff,sfp.yaml``
