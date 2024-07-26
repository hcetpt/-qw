### SPDX 许可证标识符：GPL-2.0

=================
Devlink 区域
=================

`devlink` 区域使用户能够通过 devlink 访问驱动程序定义的地址区域。每个设备都可以创建并注册它所支持的地址区域。然后可以通过 devlink 区域接口访问这些区域。区域快照由驱动程序收集，并可通过读取或转储命令访问。这允许对创建的快照进行未来的分析。区域可能选择性地支持按需触发快照。
快照标识符的作用范围是针对 devlink 实例而非特定区域。在同一个 devlink 实例中所有具有相同快照 ID 的快照都对应于同一事件。
创建区域的主要好处在于提供对用户通常无法访问的内部地址区域的访问权限。区域也可以用于提供一种额外的方式来调试复杂的错误状态，但请参阅文档《Documentation/networking/devlink/devlink-health.rst》了解更多相关信息。

区域可以选择性地支持通过 `DEVLINK_CMD_REGION_NEW` netlink 消息按需捕获快照。希望允许请求快照的驱动程序必须在其 `devlink_region_ops` 结构中为该区域实现 `.snapshot` 回调。如果在 `DEVLINK_CMD_REGION_NEW` 请求中未设置快照 ID，则内核将分配一个并发送快照信息到用户空间。
区域可以选择性地允许直接从其内容中读取数据而无需快照。直接读取请求不是原子操作。特别是，大小为 256 字节或更大的读取请求将被拆分为多个部分。如果需要原子访问，请使用快照。希望为此类区域启用此功能的驱动程序应该在 `devlink_region_ops` 结构中实现 `.read` 回调。用户空间可以通过使用 `DEVLINK_ATTR_REGION_DIRECT` 属性而不是指定快照 ID 来请求直接读取。

#### 示例用法

```shell
$ devlink region help
$ devlink region show [DEV/REGION]
$ devlink region del DEV/REGION snapshot SNAPSHOT_ID
$ devlink region dump DEV/REGION [snapshot SNAPSHOT_ID]
$ devlink region read DEV/REGION [snapshot SNAPSHOT_ID] address ADDRESS length LENGTH

# 显示所有暴露的区域及其大小：
$ devlink region show
pci/0000:00:05.0/cr-space: 大小 1048576 快照 [1 2] 最大 8
pci/0000:00:05.0/fw-health: 大小 64 快照 [1 2] 最大 8

# 删除快照：
$ devlink region del pci/0000:00:05.0/cr-space snapshot 1

# 如果区域支持，则请求立即快照：
$ devlink region new pci/0000:00:05.0/cr-space
pci/0000:00:05.0/cr-space: 快照 5

# 转储快照：
$ devlink region dump pci/0000:00:05.0/fw-health snapshot 1
0000000000000000 0014 95dc 0014 9514 0035 1670 0034 db30
0000000000000010 0000 0000 ffff ff04 0029 8c00 0028 8cc8
0000000000000020 0016 0bb8 0016 1720 0000 0000 c00f 3ffc
0000000000000030 bada cce5 bada cce5 bada cce5 bada cce5

# 读取快照的特定部分：
$ devlink region read pci/0000:00:05.0/fw-health snapshot 1 address 0 length 16
0000000000000000 0014 95dc 0014 9514 0035 1670 0034 db30

# 不使用快照直接从区域读取：
$ devlink region read pci/0000:00:05.0/fw-health address 16 length 16
0000000000000010 0000 0000 ffff ff04 0029 8c00 0028 8cc8
``

由于区域很可能是非常特定于设备或驱动程序的，因此没有定义通用区域。有关特定驱动程序支持的特定区域的信息，请参阅驱动程序特定的文档文件。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
