在旧内核中从用户空间控制I2C设备驱动程序绑定

.. NOTE::
   注意：本节内容仅适用于处理在2.6版本内核中发现的一些旧代码的情况。
   如果您使用的是较新的内核，可以安全地跳过本节。

直到2.6.32版本的内核为止，许多I2C驱动程序使用了由<linux/i2c.h>提供的辅助宏，这些宏创建了标准模块参数，允许用户控制驱动程序如何探测I2C总线并连接到设备。这些参数被称为`probe`（让驱动程序探测一个额外的地址）、`force`（强制将驱动程序连接到指定的设备）和`ignore`（阻止驱动程序探测特定地址）。

随着I2C子系统的转换为标准设备驱动程序绑定模型，很明显这些每个模块的参数已不再需要，并且可以实现集中式的方法。新的、基于sysfs的接口在`Documentation/i2c/instantiating-devices.rst`中的“方法4：从用户空间实例化”部分进行了描述。

以下是旧的模块参数到新接口的映射：

将驱动程序连接到I2C设备
-----------------------------

旧方法（模块参数）:

```shell
# modprobe <driver> probe=1,0x2d
# modprobe <driver> force=1,0x2d
# modprobe <driver> force_<device>=1,0x2d
```

新方法（sysfs接口）:

```shell
# echo <device> 0x2d > /sys/bus/i2c/devices/i2c-1/new_device
```

阻止驱动程序连接到I2C设备
------------------------------

旧方法（模块参数）:

```shell
# modprobe <driver> ignore=1,0x2f
```

新方法（sysfs接口）:

```shell
# echo dummy 0x2f > /sys/bus/i2c/devices/i2c-1/new_device
# modprobe <driver>
```

当然，在加载驱动程序之前实例化`dummy`设备是非常重要的。`dummy`设备将由i2c-core自身处理，从而防止其他驱动程序稍后绑定到它。如果问题地址处存在真实的设备，并且希望另一个驱动程序绑定到该设备，则只需传递该设备的名称而不是`dummy`。
