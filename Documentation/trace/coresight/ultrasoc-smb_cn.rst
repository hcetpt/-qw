SPDX许可证标识符: GPL-2.0

======================================
UltraSoc - 系统级芯片上的硬件辅助追踪
======================================

   :作者:   刘琦 <liuqi115@huawei.com>
   :日期:   2023年1月

介绍
------------

UltraSoc SMB 是一个每 SCCL（超级CPU集群）的硬件。它提供了一种在共享系统内存区域中缓冲和存储CPU跟踪消息的方法。该设备充当Coresight接收设备，相应的跟踪生成器（ETM）作为源设备连接。

Sysfs 文件和目录
---------------------------

SMB设备出现在现有的Coresight总线上，与其他设备一起显示如下：

```
$# ls /sys/bus/coresight/devices/
ultra_smb0   ultra_smb1   ultra_smb2   ultra_smb3
```

`ultra_smb<N>` 名称表示与SCCL关联的SMB设备：

```
$# ls /sys/bus/coresight/devices/ultra_smb0
enable_sink   mgmt
$# ls /sys/bus/coresight/devices/ultra_smb0/mgmt
buf_size  buf_status  read_pos  write_pos
```

关键文件项包括：

   * `read_pos`: 显示读取指针寄存器的值
* `write_pos`: 显示写入指针寄存器的值
* `buf_status`: 显示状态寄存器的值，BIT(0)为零表示缓冲区为空
* `buf_size`: 显示每个设备的缓冲区大小

固件绑定
-----------------

该设备仅支持ACPI。其绑定描述了设备标识符、资源信息和图结构。该设备被识别为ACPI HID "HISI03A1"。设备资源通过 _CRS 方法分配。每个设备必须提供两个基地址；第一个是设备的配置基地址，第二个是共享系统内存的32位基地址。
示例如下：

```acpi
Device(USMB) {
  Name(_HID, "HISI03A1")
  Name(_CRS, ResourceTemplate() {
    QWordMemory (ResourceConsumer, , MinFixed, MaxFixed, NonCacheable,
                 ReadWrite, 0x0, 0x95100000, 0x951FFFFF, 0x0, 0x100000)
    QWordMemory (ResourceConsumer, , MinFixed, MaxFixed, Cacheable,
                 ReadWrite, 0x0, 0x50000000, 0x53FFFFFF, 0x0, 0x4000000)
  })
  Name(_DSD, Package() {
    ToUUID("ab02a46b-74c7-45a2-bd68-f7d344ef2153"),
    /* 使用CoreSight Graph ACPI绑定来描述连接拓扑 */
    Package() {
      0,
      1,
      Package() {
        1,
        ToUUID("3ecbc8b6-1d0e-4fb3-8107-e627f805c6cd"),
        8,
        Package() {0x8, 0, \_SB.S00.SL11.CL28.F008, 0},
        Package() {0x9, 0, \_SB.S00.SL11.CL29.F009, 0},
        Package() {0xa, 0, \_SB.S00.SL11.CL2A.F010, 0},
        Package() {0xb, 0, \_SB.S00.SL11.CL2B.F011, 0},
        Package() {0xc, 0, \_SB.S00.SL11.CL2C.F012, 0},
        Package() {0xd, 0, \_SB.S00.SL11.CL2D.F013, 0},
        Package() {0xe, 0, \_SB.S00.SL11.CL2E.F014, 0},
        Package() {0xf, 0, \_SB.S00.SL11.CL2F.F015, 0},
      }
    }
  })
}
```
