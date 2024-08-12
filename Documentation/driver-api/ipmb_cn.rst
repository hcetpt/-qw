==============================
针对Satellite MC的IPMB驱动
==============================

智能平台管理总线（IPMB）是一种I2C总线，它为机箱内的不同板卡之间提供了一种标准化的互联方式。这种互联发生在基板管理控制器（BMC）与机箱电子设备之间，并且IPMB还与通过IPMB总线的消息协议相关联。
使用IPMB的设备通常是执行管理功能（如服务前面板接口、监控基板、在系统机箱中热插拔磁盘驱动器等）的管理控制器。
当系统中实现了IPMB时，BMC充当控制器的角色，以便系统软件能够访问IPMB。BMC通过IPMB向设备（通常是Satellite Management Controller或Satellite MC）发送IPMI请求，并且该设备会将响应发回给BMC。
有关IPMB及其消息格式的更多信息，请参阅IPMB和IPMI规范。

### Satellite MC的IPMB驱动

**ipmb-dev-int** - 这是Satellite MC上所需的驱动程序，用于接收来自BMC的IPMB消息并发送响应。此驱动程序与I2C驱动程序和用户空间程序（例如OpenIPMI）一起工作：

1. 它是一个I2C从设备后端驱动程序。因此，它定义了一个回调函数来设置Satellite MC作为I2C从设备。
这个回调函数处理接收到的IPMI请求。
2. 它定义了读写函数，以使用户空间程序（如OpenIPMI）能够与内核进行通信。

### 加载IPMB驱动程序

需要在启动时或手动加载此驱动程序。
首先，请确保您的配置文件中有以下内容：
```
CONFIG_IPMB_DEVICE_INTERFACE=y
```

1) 如果您希望在启动时加载驱动程序：

a) 在适当的 SMBus 下向您的 ACPI 表中添加以下条目：

     设备 (SMB0) // 示例 SMBus 主控制器
     {
     名称 (_HID, "<Vendor-Specific HID>") // 厂商特定的 HID
     名称 (_UID, 0) // 特定主控制器的唯一标识符
     :
     :
       设备 (IPMB)
       {
         名称 (_HID, "IPMB0001") // IPMB 设备接口
         名称 (_UID, 0) // 设备的唯一标识符
       }
     }

b) 设备树示例：

     &i2c2 {
            状态 = "正常";

            ipmb@10 {
                    兼容性 = "ipmb-dev";
                    寄存器 = <0x10>;
                    i2c-协议;
            };
     };

如果使用原始的 I2C 块而非 SMBus 进行数据传输，则需要像上面那样定义 "i2c-协议"

2) 手动从 Linux 加载模块：

     `modprobe ipmb-dev-int`

实例化设备
--------------

加载驱动程序后，您可以按照 'Documentation/i2c/instantiating-devices.rst' 中所述实例化设备。
如果您有多个 BMC，并且每个 BMC 都通过不同的 I2C 总线连接到您的卫星管理控制器（Satellite MC），则可以为这些 BMC 中的每一个实例化一个设备。
实例化设备的名称包含与其关联的 I2C 总线编号，如下所示：

  BMC1 ------ IPMB/I2C 总线 1 ---------|   /dev/ipmb-1
				卫星管理控制器
  BMC1 ------ IPMB/I2C 总线 2 ---------|   /dev/ipmb-2

例如，您可以在用户空间中以 7 位地址 0x10 在总线 2 上实例化 ipmb-dev-int 设备：

  # echo ipmb-dev 0x1010 > /sys/bus/i2c/devices/i2c-2/new_device

这将创建设备文件 /dev/ipmb-2，该文件可以被用户空间程序访问。在运行用户空间程序之前，需要实例化设备。
