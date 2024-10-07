SPDX 许可证标识符：GPL-2.0
.. _xfrm_device:

===============================================
XFRM 设备 - 卸载 IPsec 计算
===============================================

Shannon Nelson <shannon.nelson@oracle.com>
Leon Romanovsky <leonro@nvidia.com>

概述
========

IPsec 是一个用于保护网络流量的有用功能，但计算成本很高：一个 10Gbps 的链路很容易降低到不到 1Gbps 的速度，这取决于流量和链路配置。幸运的是，有些网卡提供了基于硬件的 IPsec 卸载，可以显著提高吞吐量并减少 CPU 利用率。XFRM 设备接口允许网卡驱动程序向内核栈提供硬件卸载的访问权限。
目前内核支持两种类型的硬件卸载：
* IPsec 加密卸载：
  * 网卡执行加密/解密
  * 内核处理其他所有事务
* IPsec 数据包卸载：
  * 网卡执行加密/解密
  * 网卡进行封装
  * 内核和网卡保持安全关联（SA）和策略同步
  * 网卡处理 SA 和策略状态
  * 内核与密钥管理器通信

用户空间通常通过 libreswan 或 KAME/raccoon 系统访问卸载，但在实验时使用 iproute2 的 'ip xfrm' 命令集也很方便。对于加密卸载的一个示例命令可能如下所示：

  ip x s add proto esp dst 14.0.0.70 src 14.0.0.52 spi 0x07 mode transport \
     reqid 0x07 replay-window 32 \
     aead 'rfc4106(gcm(aes))' 0x44434241343332312423222114131211f4f3f2f1 128 \
     sel src 14.0.0.52/24 dst 14.0.0.70/24 proto tcp \
     offload dev eth4 dir in

对于数据包卸载：

  ip x s add proto esp dst 14.0.0.70 src 14.0.0.52 spi 0x07 mode transport \
     reqid 0x07 replay-window 32 \
     aead 'rfc4106(gcm(aes))' 0x44434241343332312423222114131211f4f3f2f1 128 \
     sel src 14.0.0.52/24 dst 14.0.0.70/24 proto tcp \
     offload packet dev eth4 dir in

  ip x p add src 14.0.0.70 dst 14.0.0.52 offload packet dev eth4 dir in
  tmpl src 14.0.0.70 dst 14.0.0.52 proto esp reqid 10000 mode transport

是的，这看起来很丑陋，但这正是 shell 脚本或 libreswan 的用途所在。

需要实现的回调
======================

::

  /* 来自 include/linux/netdevice.h */
  struct xfrmdev_ops {
        /* 加密和数据包卸载回调 */
	int	(*xdo_dev_state_add) (struct xfrm_state *x, struct netlink_ext_ack *extack);
	void	(*xdo_dev_state_delete) (struct xfrm_state *x);
	void	(*xdo_dev_state_free) (struct xfrm_state *x);
	bool	(*xdo_dev_offload_ok) (struct sk_buff *skb,
				       struct xfrm_state *x);
	void    (*xdo_dev_state_advance_esn) (struct xfrm_state *x);
	void    (*xdo_dev_state_update_stats) (struct xfrm_state *x);

        /* 仅数据包卸载回调 */
	int	(*xdo_dev_policy_add) (struct xfrm_policy *x, struct netlink_ext_ack *extack);
	void	(*xdo_dev_policy_delete) (struct xfrm_policy *x);
	void	(*xdo_dev_policy_free) (struct xfrm_policy *x);
  };

提供 IPsec 卸载的网卡驱动程序需要实现与支持的卸载相关的回调，以便将卸载功能提供给网络栈的 XFRM 子系统。此外，特征位 NETIF_F_HW_ESP 和 NETIF_F_HW_ESP_TX_CSUM 将指示卸载可用性。

流程
====

在调用 register_netdev() 之前，驱动程序应在探测过程中设置本地数据结构和 XFRM 回调，并设置特征位。XFRM 代码的监听器将在 NETDEV_REGISTER 时完成设置：

		adapter->netdev->xfrmdev_ops = &ixgbe_xfrmdev_ops;
		adapter->netdev->features |= NETIF_F_HW_ESP;
		adapter->netdev->hw_enc_features |= NETIF_F_HW_ESP;

当新的 SA 设置带有“卸载”请求时，驱动程序的 xdo_dev_state_add() 将被赋予要卸载的新 SA 以及指示它是用于 Rx 还是 Tx 的信息。驱动程序应执行以下操作：

	- 验证算法是否支持卸载
	- 存储 SA 信息（密钥、盐、目标 IP、协议等）
	- 启用硬件卸载
	- 返回状态值：

		===========   ===================================
		0             成功
		-EOPNETSUPP   不支持卸载，尝试 SW IPsec，
                              在数据包卸载模式下不适用
		其他         拒绝请求
		===========   ===================================

驱动程序还可以在 SA 中设置一个卸载句柄，这是一个不透明的 void 指针，可用于在快速路径卸载请求中传递上下文：

		xs->xso.offload_handle = context;

当网络栈准备发送 IPsec 数据包时，它首先通过 xdo_dev_offload_ok() 调用驱动程序，传入 skb 和预期的卸载状态，询问驱动程序是否能够处理卸载。这可以检查数据包信息以确保卸载可以支持（例如 IPv4 或 IPv6，没有 IPv4 选项等），并返回 true 或 false 表示其支持情况。

加密卸载模式：
当准备发送时，驱动程序需要检查 Tx 数据包中的卸载信息，包括不透明的上下文，并相应地设置数据包发送：

		xs = xfrm_input_state(skb);
		context = xs->xso.offload_handle;
		设置 HW 发送

堆栈已经在数据包数据中插入了适当的 IPsec 头，卸载只需进行加密并修复头值即可。
当接收到一个数据包且硬件已指示其卸载了解密时，驱动程序需要将解码后的 SA 引用添加到数据包的 skb 中。此时数据应该已被解密，但 IPsec 头仍然在数据包数据中；它们会在 xfrm_input() 中被移除。
查找并持有用于接收skb的安全关联（SA）：

- 从数据包头中获取SPI、协议和目标IP。
- 通过（SPI，协议，目标IP）找到xs。
- 调用 `xfrm_state_hold(xs)`。

将状态信息存储到skb中：

- `sp = secpath_set(skb)`；如果 `sp` 为空则返回。
- `sp->xvec[sp->len++] = xs`；
- `sp->olen++`；

指示卸载的成功或错误状态：

- `xo = xfrm_offload(skb)`；
- 设置 `xo->flags = CRYPTO_DONE`；
- 设置 `xo->status = crypto_status`；

将数据包传递给 `napi_gro_receive()` 以进行常规处理。

在ESN模式下，`xdo_dev_state_advance_esn()` 函数由 `xfrm_replay_advance_esn()` 调用。驱动程序会检查数据包的序列号，并在需要时更新硬件ESN状态机。

卸载模式：
- 硬件添加和删除XFRM头。因此，在接收路径中，如果硬件报告成功，则绕过XFRM堆栈。在发送路径中，数据包在没有额外头部的情况下离开内核且未加密，硬件负责执行加密操作。
- 当用户移除SA时，驱动程序的 `xdo_dev_state_delete()` 和 `xdo_dev_policy_delete()` 函数被调用来禁用卸载。随后，当所有状态和策略的引用计数被清除后，垃圾收集例程会调用 `xdo_dev_state_free()` 和 `xdo_dev_policy_free()` 来释放剩余资源。
- 驱动程序如何使用这些函数取决于特定硬件的需求。
- 当网卡设置为DOWN状态时，XFRM堆栈的网卡监听器会调用 `xdo_dev_state_delete()`、`xdo_dev_policy_delete()`、`xdo_dev_state_free()` 和 `xdo_dev_policy_free()` 来处理任何剩余的已卸载状态。
- 在硬件处理数据包的结果中，XFRM核心无法精确计算硬限制和软限制。
- 硬件/驱动程序负责在调用 `xdo_dev_state_update_stats()` 时提供准确的数据。如果发生其中一个限制，驱动程序需要调用 `xfrm_state_check_expire()` 来确保XFRM执行重新密钥交换序列。
