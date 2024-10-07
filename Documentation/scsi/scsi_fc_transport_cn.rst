SPDX 许可证标识符: GPL-2.0

=================
SCSI FC 传输层
=================

日期: 2008年11月18日

内核修订版本以支持特性::

  rports : <<待补充>>
  vports : 2.6.22
  bsg 支持 : 2.6.30 (?待定?)


简介
============

此文件记录了 SCSI FC 传输层的特性和组件。
它还提供了传输层与 FC LLDD（低级驱动程序）之间的 API 文档。
FC 传输层位于以下位置:

  drivers/scsi/scsi_transport_fc.c
  include/scsi/scsi_transport_fc.h
  include/scsi/scsi_netlink_fc.h
  include/scsi/scsi_bsg_fc.h

此文件位于 Documentation/scsi/scsi_fc_transport.rst


FC 远程端口 (rports)
========================

<<待补充>>

FC 虚拟端口 (vports)
=========================

概述
--------

新 FC 标准定义了一种机制，允许单个物理端口表现为多个通信端口。通过使用 N_Port ID 虚拟化 (NPIV) 机制，可以为与结构的点对点连接分配多个 N_Port_ID。每个 N_Port_ID 在结构上的其他端点看来就像是一个独立的端口，尽管它们共享一条到交换机的物理链路进行通信。每个 N_Port_ID 可以根据结构分区和阵列 LUN 掩码拥有结构的独特视图（就像普通的非 NPIV 适配器一样）。通过使用虚拟结构 (VF) 机制，在每个帧中添加一个结构头，可以使端口与结构端口交互，从而加入多个结构。端口将在其加入的每个结构上获得一个 N_Port_ID。每个结构都将有自己的独特视图和配置参数。NPIV 可以与 VF 结合使用，使端口在每个虚拟结构上获得多个 N_Port_ID。

现在，FC 传输层识别一个新的对象——vport。vport 是一个具有全局唯一世界端口名称 (wwpn) 和全局节点名称 (wwnn) 的实体。传输层还允许为 vport 指定 FC4，其中 FCP_Initiator 是预期的主要角色。一旦通过上述方法实例化，它将拥有一个独特的 N_Port_ID 以及对结构端点和存储实体的独特视图。

与物理适配器关联的 fc_host 将提供创建 vport 的能力。传输层将在 Linux 设备树中创建 vport 对象，并指示 fc_host 的驱动程序实例化虚拟端口。通常，驱动程序将在 vport 上创建一个新的 scsi_host 实例，从而为 vport 创建一个独特的 <H,C,T,L> 命名空间。

因此，无论 FC 端口是基于物理端口还是基于虚拟端口，每个端口都将表现为一个独特的 scsi_host，并且拥有自己的目标和 LUN 空间。
.. 注意::
    目前，传输层编写仅支持 NPIV 基础的 vports。然而，已经考虑了基于 VF 的 vports，并且如果需要的话，添加支持将是小改动。接下来的讨论将集中在 NPIV 上。
.. 注意::
    全局名称分配（及其唯一性保证）由控制 vport 的管理实体负责。例如，如果 vport 要与虚拟机相关联，XEN 管理工具将负责为 vport 创建 wwpn/wwnn，使用其自身的命名权限和 OUI。（注意：它已经为虚拟 MAC 地址做了这件事）
设备树和 Vport 对象:
-------------------------------

目前，设备树通常包含 scsi_host 对象，其下有 rports 和 scsi 目标对象。当前 FC 传输层创建 vport 对象并将其放置在对应于物理适配器的 scsi_host 对象之下。LLDD 将为 vport 分配一个新的 scsi_host 并将其对象链接到 vport 下面。

vport 下的 scsi_host 对象树的其余部分与非 NPIV 情况相同。目前，传输层编写得很容易让 vport 的父对象不是 scsi_host。
这可以在未来用于将对象链接到特定虚拟机的设备树。如果虚拟端口（vport）的父设备不是物理端口的 `scsi_host`，则会在物理端口的 `scsi_host` 中创建一个指向 vport 对象的符号链接。

以下是在设备树中可以预期的内容：

### 物理端口的 Scsi_Host 示例：
```
/sys/devices/.../host17/
```

并且它有典型的子树结构：
```
/sys/devices/.../host17/rport-17:0-0/target17:0:0/17:0:0:0:
```

然后在物理端口上创建 vport：
```
/sys/devices/.../host17/vport-17:0-0
```

接着创建 vport 的 `Scsi_Host`：
```
/sys/devices/.../host17/vport-17:0-0/host18
```

然后树继续扩展，例如：
```
/sys/devices/.../host17/vport-17:0-0/host18/rport-18:0-0/target18:0:0/18:0:0:0:
```

以下是在 sysfs 树中可以预期的内容：

### Scsi_Hosts：
```
/sys/class/scsi_host/host17      物理端口的 scsi_host
/sys/class/scsi_host/host18      vport 的 scsi_host
```

### Fc_Hosts：
```
/sys/class/fc_host/host17        物理端口的 fc_host
/sys/class/fc_host/host18        vport 的 fc_host
```

### Fc_Vports：
```
/sys/class/fc_vports/vport-17:0-0    vport 的 fc_vport
```

### Fc_Rports：
```
/sys/class/fc_remote_ports/rport-17:0-0    物理端口上的 rport
/sys/class/fc_remote_ports/rport-18:0-0    vport 上的 rport
```

### 虚拟端口属性
新创建的 `fc_vport` 类对象具有以下属性：

#### node_name：（只读）
- vport 的 WWNN

#### port_name：（只读）
- vport 的 WWPN

#### roles：（只读）
- 表示在 vport 上启用的 FC4 角色

#### symbolic_name：（可读写）
- 这是一个字符串，附加到驱动程序的符号端口名称字符串上，并且注册到交换机以识别 vport。例如，虚拟化管理程序可以将此字符串设置为 "Xen Domain 2 VM 5 Vport 2"，这样可以在交换机管理界面上看到这些标识符来识别端口。

#### vport_delete：（只写）
- 写入 "1" 时，会删除 vport

#### vport_disable：（只写）
- 写入 "1" 时，会将 vport 切换到禁用状态。vport 仍然会实例化在 Linux 内核中，但不会在 FC 链路上活跃。
- 写入 "0" 时，会启用 vport

#### vport_last_state：（只读）
- 表示 vport 的前一个状态。请参阅下面的“虚拟端口状态”部分。

#### vport_state：（只读）
- 表示 vport 的当前状态。请参阅下面的“虚拟端口状态”部分。

#### vport_type：（只读）
- 反映创建虚拟端口所使用的 FC 机制。
目前仅支持 NPIV

对于 `fc_host` 类对象，为 vport 添加了以下属性：

- `max_npiv_vports`: 只读
  表示 `fc_host` 上驱动程序/适配器可以支持的最大 NPIV 基础的 vport 数量。
- `npiv_vports_inuse`: 只读
  表示在 `fc_host` 上已经实例化的 NPIV 基础的 vport 数量。
- `vport_create`: 只写
  提供一个“简单”的创建接口来在 `fc_host` 上实例化一个 vport。向该属性写入 `<WWPN>:<WWNN>` 字符串。传输层随后实例化 vport 对象，并调用 LLDD 创建具有 FCP_Initiator 角色的 vport。每个 WWN 指定为 16 个十六进制字符，并且 *不能* 包含任何前缀（例如 0x, x 等）。
- `vport_delete`: 只写
  提供一个“简单”的删除接口来拆除一个 vport。向该属性写入 `<WWPN>:<WWNN>` 字符串。传输层将定位具有相同 WWN 的 `fc_host` 上的 vport 并将其拆除。每个 WWN 指定为 16 个十六进制字符，并且 *不能* 包含任何前缀（例如 0x, x 等）。

Vport 状态
------------

Vport 实例化包括两个部分：

- 与内核和 LLDD 的创建。这意味着所有传输层和驱动程序的数据结构都已构建，并创建了设备对象。这相当于在适配器上的驱动程序“附加”，并且独立于适配器的链路状态。
- 通过 ELS 流量等在 FC 链路上实例化 vport。这相当于“链路建立”并成功初始化链路。
更多详细信息可以在下面的接口部分找到，关于虚拟端口（Vport）创建的内容。

一旦虚拟端口（vport）与内核/LLDD实例化后，可以通过sysfs属性报告vport的状态。以下是一些存在的状态：

- `FC_VPORT_UNKNOWN` - 未知
  一个临时状态，通常仅在vport与内核和LLDD进行实例化时设置。

- `FC_VPORT_ACTIVE` - 激活
  vport已成功在FC链路上创建。它完全可用。

- `FC_VPORT_DISABLED` - 禁用
  vport已实例化，但处于“禁用”状态。vport没有在FC链路上实例化。这相当于一个物理端口，其链路是“断开”的。

- `FC_VPORT_LINKDOWN` - 链路断开
  vport不可操作，因为物理链路不可用。

- `FC_VPORT_INITIALIZING` - 初始化中
  vport正在FC链路上实例化的过程中。LLDD将在开始ELS流量以创建vport之前设置此状态。此状态将一直持续到vport成功创建（状态变为`FC_VPORT_ACTIVE`）或失败（状态为以下某个值）。由于此状态是过渡性的，因此不会保存在`vport_last_state`中。

- `FC_VPORT_NO_FABRIC_SUPP` - 不支持结构
  vport不可操作。遇到了以下条件之一：
  
  - FC拓扑不是点对点。
  - FC端口未连接到F_Port。
  - F_Port表明不支持NPIV。

- `FC_VPORT_NO_FABRIC_RSCS` - 没有结构资源
  vport不可操作。结构在FDISC过程中失败，并返回了一个状态，表明它没有足够的资源来完成该操作。
### FC_VPORT_FABRIC_LOGOUT - Fabric Logout
   vport 不可用。Fabric 已经注销了与 vport 关联的 N_Port_ID。

### FC_VPORT_FABRIC_REJ_WWN - Fabric 拒绝 WWN
   vport 不可用。Fabric 在 FDISC 过程中返回了一个状态，表明 WWN 无效。

### FC_VPORT_FAILED - VPort 失败
   vport 不可用。这是所有其他错误条件的汇总。

以下状态表显示了不同的状态转换：

| 状态          | 事件                          | 新状态           |
|---------------|-------------------------------|------------------|
| 无            | 初始化                       | 未知             |
|---------------|-------------------------------|------------------|
| 未知          | 链路断开                     | 链路断开         |
|               | 链路连接且循环               | 无 Fabric 支持   |
|               | 链路连接且无 Fabric           | 无 Fabric 支持   |
|               | 链路连接且 FLOGI 响应         | 无 Fabric 支持   |
|               | 表明无 NPIV 支持              |                  |
|               | 链路连接且发送 FDISC          | 初始化           |
|               | 禁用请求                     | 禁用             |
|---------------|-------------------------------|------------------|
| 链路断开      | 链路连接                     | 未知             |
|---------------|-------------------------------|------------------|
| 初始化        | FDISC ACC                    | 激活             |
|               | FDISC LS_RJT 无资源           | 无 Fabric 资源   |
|               | FDISC LS_RJT 无效 pname 或 nport_id | Fabric 拒绝 WWN  |
|               | FDISC LS_RJT 其他原因失败     | Vport 失败       |
|               | 链路断开                     | 链路断开         |
|               | 禁用请求                     | 禁用             |
|---------------|-------------------------------|------------------|
| 禁用          | 启用请求                     | 未知             |
|---------------|-------------------------------|------------------|
| 激活          | 收到 Fabric 的 LOGO           | Fabric 注销      |
|               | 链路断开                     | 链路断开         |
|               | 禁用请求                     | 禁用             |
|---------------|-------------------------------|------------------|
| Fabric 注销   | 链路仍连接                   | 未知             |
|---------------|-------------------------------|------------------|

以下 4 种错误状态具有相同的转换：

- 无 Fabric 支持：
- 无 Fabric 资源：
- Fabric 拒绝 WWN：
- Vport 失败：
  
  - 禁用请求：禁用
  - 链路断开：链路断开

### 传输 <-> LLDD 接口

#### LLDD 对 Vport 的支持

LLDD 通过在传输模板中提供 vport_create() 函数来表示对 vport 的支持。此函数的存在将导致在 fc_host 上创建新的属性。作为物理端口完成初始化的一部分，它应该设置 max_npiv_vports 属性以指示驱动程序和/或适配器支持的最大 vport 数量。

#### Vport 创建

LLDD 的 vport_create() 语法如下：

```c
int vport_create(struct fc_vport *vport, bool disable)
```

其中：

- `vport`：新分配的 vport 对象。
- `disable`：如果为 `true`，则 vport 应在禁用状态下创建；如果为 `false`，则 vport 应在创建时启用。

当请求创建一个新的 vport（通过 sgio/netlink 或 fc_host 属性）时，传输层会验证 LLDD 是否可以支持另一个 vport（例如 max_npiv_vports > npiv_vports_inuse）。如果不支持，则创建请求将失败。如果有剩余空间，传输层将增加 vport 计数，创建 vport 对象，并调用 LLDD 的 vport_create() 函数，传入新分配的 vport 对象。

如上所述，vport 创建分为两个部分：

1. 内核和 LLDD 的创建。这意味着所有传输和驱动数据结构都已构建，并且设备对象已创建。这相当于在一个适配器上的“attach”操作，与适配器的链路状态无关。
通过 ELS 流量等在 FC 链路上实例化 vport
这相当于“链路建立”并成功初始化链路
LLDD 的 vport_create() 函数不会同步等待两部分完全完成再返回。它必须验证存在支持 NPIV 的基础设施，并在返回前完成 vport 创建的第一部分（数据结构构建）。我们不将 vport_create() 与链路侧操作挂钩，主要是因为：

- 链路可能处于断开状态。如果链路断开，这不是一个错误。这只是意味着 vport 处于不可操作状态，直到链路重新建立。
这与在创建 vport 后链路重新建立的行为一致。
- vport 可能以禁用状态创建。
- 这与以下模型一致：vport 等同于 FC 适配器。vport_create 类似于驱动程序附加到适配器，这与链路状态无关。

注意：
定义了特殊的错误代码来区分基础设施故障情况以便更快解决。

对于 LLDD 的 vport_create() 函数预期行为如下：

- 验证基础设施：

    - 如果驱动程序或适配器由于固件不当、最大 NPIV 数量虚假报告或其他资源不足而无法支持另一个 vport，则返回 VPCERR_UNSUPPORTED。
- 如果驱动程序验证 WWN 并发现其与适配器上已激活的 WWN 有重叠，则返回 VPCERR_BAD_WWN。
- 如果驱动程序检测到拓扑为环形、非结构化或 FLOGI 不支持 NPIV，则返回 VPCERR_NO_FABRIC_SUPP。
分配数据结构。如果遇到错误，例如内存不足的情况，则返回相应的负数 Exxx 错误代码。

- 如果角色是 FCP 发起者，则 LLDD 应该执行以下操作：
  - 调用 `scsi_host_alloc()` 来为 vport 分配一个 `scsi_host`。
- 调用 `scsi_add_host(new_shost, &vport->dev)` 启动 `scsi_host` 并将其绑定为 vport 设备的子设备。
- 初始化 `fc_host` 属性值。
- 根据禁用标志和链路状态触发进一步的 vport 状态转换，并返回成功（零）。

LLDD 实现者注意事项：

- 建议为物理端口和虚拟端口使用不同的 `fc_function_templates`。物理端口的模板应包含 `vport_create`、`vport_delete` 和 `vport_disable` 函数，而虚拟端口则不需要这些函数。
- 建议为物理端口和虚拟端口使用不同的 `scsi_host_templates`。通常，嵌入在 `scsi_host_template` 中的某些驱动程序属性仅适用于物理端口（如链路速度、拓扑设置等）。这确保了这些属性适用于各自的 `scsi_host`。

Vport 禁用/启用：

LLDD 的 `vport_disable()` 语法如下：

```c
int vport_disable(struct fc_vport *vport, bool disable)
```

其中：

- `vport`：要启用或禁用的 vport。
- `disable`：如果为 "true"，则禁用 vport；如果为 "false"，则启用 vport。

当请求更改 vport 的禁用状态时，传输层将根据现有的 vport 状态验证该请求。
如果请求是禁用 vport，并且 vport 已经被禁用，请求将会失败。同样地，如果请求是启用 vport，并且 vport 不在禁用状态，请求也会失败。如果请求对 vport 状态有效，传输层将调用 LLDD 来改变 vport 的状态。

在 LLDD 内部，如果一个 vport 被禁用，它仍然会与内核和 LLDD 保持实例化状态，但不会在 FC 链路上以任何方式激活或可见。（参见 Vport 创建和两阶段实例化讨论）该 vport 将保持在这种状态下，直到被删除或重新启用。当启用一个 vport 时，LLDD 会在 FC 链路上重新实例化该 vport —— 实质上是重启 LLDD 状态机（参见上面的 Vport 状态）。

Vport 删除：

LLDD 中 vport_delete() 的语法如下：

```c
int vport_delete(struct fc_vport *vport)
```

其中：

- `vport`：要删除的 vport

当请求删除一个 vport（通过 sgio/netlink 或者通过 fc_host 或 fc_vport 的 vport_delete 属性），传输层将调用 LLDD 在 FC 链路上终止该 vport 并拆除所有其他数据结构和引用。如果 LLDD 成功完成，传输层将拆除 vport 对象并完成 vport 的移除。如果 LLDD 删除请求失败，vport 对象将保留，但处于不确定状态。

在 LLDD 内部，应遵循 scsi_host 拆除的正常代码路径。例如，如果 vport 具有 FCP 发起者角色，LLDD 将调用 fc_remove_host() 来移除 vport 的 scsi_host，随后调用 scsi_remove_host() 和 scsi_host_put() 来处理 vport 的 scsi_host。

其他：
fc_host port_type 属性：
新增了一个 fc_host port_type 值 —— FC_PORTTYPE_NPIV。此值必须设置在所有基于 vport 的 fc_hosts 上。通常，在物理端口上，port_type 属性会根据拓扑类型和网络的存在情况设置为 NPORT、NLPORT 等。由于这些不适用于 vport，因此报告用于创建 vport 的 FC 机制更有意义。

驱动卸载：
FC 驱动程序需要在调用 scsi_remove_host() 之前调用 fc_remove_host()。这使得 fc_host 可以在 scsi_host 被拆除前先拆除所有远程端口。fc_remove_host() 调用已更新为移除 fc_host 的所有 vport。

传输提供的函数
----------------

以下函数由 FC-传输提供给 LLD 使用：
- `fc_vport_create`：创建一个 vport
- `fc_vport_terminate`：分离并移除一个 vport

详细信息：
```c
/**
 * fc_vport_create - Admin App 或 LLDD 请求创建一个 vport
 * @shost:     虚拟端口连接到的 scsi 主机
```
```c
// * @ids:       全局名称、FC4端口角色等虚拟端口信息
// *
//     * 注意：
//     *     该例程假设在进入时没有锁定
// */
struct fc_vport *
fc_vport_create(struct Scsi_Host *shost, struct fc_vport_identifiers *ids)

/**
// * fc_vport_terminate - 管理应用程序或LLDD请求终止一个vport
// * @vport:      要终止的fc_vport
// *
// * 调用LLDD的vport_delete()函数，然后释放并移除shost和对象树中的vport
// *
// * 注意：
// *      该例程假设在进入时没有锁定
// */
int
fc_vport_terminate(struct fc_vport *vport)


// FC BSG支持（CT和ELS直通，以及更多）
// ===================================
// << 尚未提供 >>






// 致谢
// =====
// 以下人员对本文档做出了贡献：




// James Smart
// james.smart@broadcom.com
```

这段代码注释已经被翻译成中文。如果有任何进一步的问题或需要修改的地方，请告诉我！
