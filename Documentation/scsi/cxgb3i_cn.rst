SPDX 许可证标识符: GPL-2.0

=================================
适用于 Linux 的 Chelsio S3 iSCSI 驱动程序
=================================

介绍
============

基于 Chelsio T3 ASIC 的适配器（如 S310、S320、S302、S304、Mezz 卡等系列产品）支持 iSCSI 加速和 iSCSI 直接数据放置（DDP），其中硬件处理了昂贵的字节操作，例如 CRC 计算和验证，并直接将 DMA 发送到最终主机内存目的地：

- iSCSI PDU 摘要生成和验证

  在发送时，Chelsio S3 硬件计算并插入头部和数据摘要到 PDU 中；
  在接收时，Chelsio S3 硬件计算并验证 PDU 的头部和数据摘要。
- 直接数据放置（DDP）

  S3 硬件可以根据数据输入（Data-In）中的启动器任务标签（ITT）或数据输出（Data-Out）PDU 中的目标任务标签（TTT），直接将 iSCSI 数据输入或输出 PDU 的有效载荷放置到预先分配的最终目标主机内存缓冲区中。
- PDU 发送与恢复

  在发送时，S3 硬件从主机驱动程序接收完整的 PDU（头部+数据），计算并插入摘要，必要时将 PDU 分解为多个 TCP 分段，并将所有 TCP 分段发送到网络上。如果需要，它会处理 TCP 重传；
  在接收时，S3 硬件通过重新组装 TCP 分段、分离头部和数据、计算和验证摘要，然后将头部转发给主机来恢复 iSCSI PDU。如果可能的话，有效载荷数据将直接放置到预先分配的主机 DDP 缓冲区中。否则，有效载荷数据也会被发送到主机。
cxgb3i 驱动程序与 open-iscsi 启动器接口，并在适用的情况下通过 Chelsio 硬件提供 iSCSI 加速。

使用 cxgb3i 驱动程序
=======================

为了加速 open-iscsi 启动器，需要采取以下步骤：

1. 加载 cxgb3i 驱动程序：`modprobe cxgb3i`

   cxgb3i 模块向 open-iscsi 注册了一个新的传输层类 "cxgb3i"
   * 如果重新编译内核，cxgb3i 的选择位于：
   
     设备驱动程序
     SCSI 设备支持 --->
       [*] 低级 SCSI 驱动程序  --->
         <M>   Chelsio S3xx iSCSI 支持

2. 为新的传输层类 "cxgb3i" 创建一个接口文件，位于 /etc/iscsi/ifaces/ 下。
文件内容应如下格式：

```
iface.transport_name = cxgb3i
iface.net_ifacename = <ethX>
iface.ipaddress = <iscsi ip 地址>
```

   * 如果指定了 iface.ipaddress，则 <iscsi ip 地址> 需要与 ethX 的 IP 地址相同或在同一子网上。确保 IP 地址在网络中是唯一的。
3. 编辑 `/etc/iscsi/iscsid.conf`
   默认设置中的 `MaxRecvDataSegmentLength`（131072）太大；替换为不超过15360的值（例如8192）：

   ```
   node.conn[0].iscsi.MaxRecvDataSegmentLength = 8192
   ```

   * 如果 `MaxRecvDataSegmentLength` 太大，正常的登录会失败。会在 `dmesg` 中记录一条错误信息，格式如下：
     ```
     cxgb3i: ERR! MaxRecvSegmentLength <X> too big. Need to be <= <Y>.
     ```

4. 要将 open-iscsi 流量导向 cxgb3i 的加速路径，需要在大多数 iscsiadm 命令中指定 `-I <iface file name>` 选项。<iface file name> 是在步骤2中创建的传输接口文件。
