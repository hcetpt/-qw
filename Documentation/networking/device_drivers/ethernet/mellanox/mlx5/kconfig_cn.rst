```plaintext
SPDX 许可证标识符：GPL-2.0 或 Linux-OpenIB
.. include:: <isonum.txt>

=======================================
启用驱动程序和 kconfig 选项
=======================================

:版权所有: |copy| 2023, NVIDIA CORPORATION 及其关联公司。保留所有权利。
| mlx5 核心是模块化的，大多数主要的 mlx5 核心驱动功能可以通过内核 Kconfig 标志在构建时选择（编译进/出）
| 基本功能、以太网网络设备接收/发送卸载和 XDP 可通过最基本的标志获得
| CONFIG_MLX5_CORE=y/m 和 CONFIG_MLX5_CORE_EN=y
| 对于高级功能列表，请参见下面
**CONFIG_MLX5_BRIDGE=(y/n)**

|    启用以太网桥接 (BRIDGE) 卸载支持 :ref:`<mlx5_bridge_offload>`
|    这将提供能力，将 mlx5 上行链路及虚拟功能 (VF)
|    端口的代表添加到桥接器，并为这些端口之间的流量卸载规则
|    支持 VLAN（干线和接入模式）
**CONFIG_MLX5_CORE=(y/m/n)** （模块 mlx5_core.ko）

|    通过在内核配置中选择 CONFIG_MLX5_CORE=y/m 来启用驱动程序
|    这将为 mlx5 ulps 提供 mlx5 核心驱动接口（mlx5e, mlx5_ib）
**CONFIG_MLX5_CORE_EN=(y/n)**

|    选择此选项将允许基本的以太网网络设备支持，包括所有标准的接收/发送卸载
```
下面是提供的英文配置选项及其中文翻译：

**CONFIG_MLX5_CORE_EN_DCB=(y/n)**:

|    启用 `数据中心桥接 (DCB) 支持 <https://enterprise-support.nvidia.com/s/article/howto-auto-config-pfc-and-ets-on-connectx-4-via-lldp-dcbx>`_

**CONFIG_MLX5_CORE_IPOIB=(y/n)**

|    IPoIB 卸载与加速支持
|    需要 CONFIG_MLX5_CORE_EN 来为 RDMA 的 IPoIB ULP 网络设备提供加速接口

**CONFIG_MLX5_CLS_ACT=(y/n)**

|    启用 TC 分类器操作卸载（NET_CLS_ACT）支持
|    在原生 NIC 模式和 Switchdev SRIOV 模式下均有效
|    基于流的分类器，例如通过 `tc-flower(8)` 注册的分类器，由设备处理而非主机。随后会立即执行覆盖匹配分类结果的操作，这是因为进行了卸载

**CONFIG_MLX5_EN_ARFS=(y/n)**

|    启用硬件加速接收流导向 (arfs) 支持以及 n-tuple 过滤
|    https://enterprise-support.nvidia.com/s/article/howto-configure-arfs-on-connectx-4

**CONFIG_MLX5_EN_IPSEC=(y/n)**

|    启用 :ref:`IPSec XFRM 加密卸载加速 <xfrm_device>`

**CONFIG_MLX5_MACSEC=(y/n)**

|    构建 NIC 中的 MACsec 加密卸载加速支持
**CONFIG_MLX5_EN_RXNFC=(y/n)**

|   启用 ethtool 网络流分类接收，允许用户定义的流规则通过 ethtool 的 set/get_rxnfc API 将流量导向任意的接收队列
**CONFIG_MLX5_EN_TLS=(y/n)**

|   TLS 加密卸载加速
**CONFIG_MLX5_ESWITCH=(y/n)**

|   ConnectX 网卡中的以太网 SRIOV E-Switch 支持。E-Switch 提供内部 SRIOV 数据包转向和交换功能，适用于已启用的虚拟功能（VF）和物理功能（PF），支持两种模式：
|           1) `传统 SRIOV 模式（基于 L2 MAC VLAN 转向）<https://enterprise-support.nvidia.com/s/article/HowTo-Configure-SR-IOV-for-ConnectX-4-ConnectX-5-ConnectX-6-with-KVM-Ethernet>`_
|           2) :ref:`Switchdev 模式（eswitch 卸载）<switchdev>`
**CONFIG_MLX5_FPGA=(y/n)**

|   构建 Mellanox Technologies 的 Innova 家族网络卡的支持
|   Innova 网络卡由一个 ConnectX 芯片和一个 FPGA 芯片组成。如果选择此选项，mlx5_core 驱动程序将包含 Innova FPGA 核心，并允许构建特定于沙盒的客户端驱动程序
**CONFIG_MLX5_INFINIBAND=(y/n/m)** (模块 mlx5_ib.ko)

|   提供低级别的 InfiniBand/RDMA 和 `RoCE <https://enterprise-support.nvidia.com/s/article/recommended-network-configuration-examples-for-roce-deployment>`_ 支持
**CONFIG_MLX5_MPFS=(y/n)**

|   ConnectX 网卡中的以太网多物理功能交换 (MPFS) 支持
|   当启用 `多主机 <https://www.nvidia.com/en-us/networking/multi-host/>`_ 配置时，MPFS 是必需的，它允许将用户配置的单播 MAC 地址传递给请求的物理功能（PF）
**CONFIG_MLX5_SF=(y/n)**

|    构建子功能的支持
|    子功能比 PCI SRIOV 虚拟功能（VF）更轻量级。选择此选项
|    将会启用创建子功能设备的支持。

**CONFIG_MLX5_SF_MANAGER=(y/n)**

|    构建 NIC 中子功能端口的支持。Mellanox 子功能
|    端口通过 devlink 进行管理。子功能支持 RDMA、网络设备
|    和 vdpa 设备。它与 SRIOV VF 类似，但不需要
|    SRIOV 支持。

**CONFIG_MLX5_SW_STEERING=(y/n)**

|    构建 NIC 中软件管理的转向支持。

**CONFIG_MLX5_TC_CT=(y/n)**

|    支持通过 tc ct 操作卸载连接跟踪规则

**CONFIG_MLX5_TC_SAMPLE=(y/n)**

|    支持通过 tc sample 操作卸载采样规则

**CONFIG_MLX5_VDPA=(y/n)**

|    支持 Mellanox VDPA 驱动程序的库。提供了所有类型 VDPA 驱动程序共有的代码。计划中的驱动程序包括：
|    网络、块设备

**CONFIG_MLX5_VDPA_NET=(y/n)**

|    为 ConnectX6 及更新型号提供的 VDPA 网络驱动程序。提供对 virtio 网络数据路径的卸载，使得放置在环上的描述符
|    由硬件执行。根据实际使用的设备和固件版本，它还支持多种无状态卸载。

**CONFIG_MLX5_VFIO_PCI=(y/n)**

|    为使用 VFIO 框架的 MLX5 设备提供迁移支持。

**外部选项** （如果需要对应的 mlx5 特性，请选择）

- CONFIG_MLXFW: 选择后，将启用 mlx5 固件刷新支持（通过 devlink 和 ethtool）。
- CONFIG_PTP_1588_CLOCK：当选择此项时，将启用 mlx5 的 PTP 支持
- CONFIG_VXLAN：当选择此项时，将启用 mlx5 的 VXLAN 支持
