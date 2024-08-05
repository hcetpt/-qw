授权（或不授权）您的USB设备连接到系统
==============================================================

版权所有 (C) 2007 Inaky Perez-Gonzalez <inaky@linux.intel.com> 英特尔公司

此功能允许您控制USB设备是否可以（或不可以）在系统中使用。此功能将使您能够实施对用户空间完全控制的USB设备锁定。
目前，当USB设备连接时，它会被配置，并且其接口会立即提供给用户使用。通过这项修改，只有当root授权设备被配置时，才可能使用它。

使用方法
=====

授权一个设备连接：

	$ echo 1 > /sys/bus/usb/devices/DEVICE/authorized

取消授权一个设备：

	$ echo 0 > /sys/bus/usb/devices/DEVICE/authorized

将新连接到hostX的设备默认设置为未授权（即：锁定）：

	$ echo 0 > /sys/bus/usb/devices/usbX/authorized_default

解除锁定：

	$ echo 1 > /sys/bus/usb/devices/usbX/authorized_default

默认情况下，所有USB设备都是授权的。将“2”写入authorized_default属性会导致内核仅默认授权连接到内部USB端口的设备。

示例系统锁定（简陋版）
------------------------------

假设您希望实现一种锁定，使得仅类型为XYZ的设备可以连接（例如，它是一个带有可见USB端口的信息亭机器）：

  启动
  rc.local ->

   对于 host 在 /sys/bus/usb/devices/usb* 中的每个项
   do
      echo 0 > $host/authorized_default
   done

为新USB设备编写一个udev脚本：

如果 device_is_my_type $DEV
然后
   echo 1 > $device_path/authorized
结束

现在，device_is_my_type() 是锁定的关键部分。仅仅检查类、类型和协议是否匹配某些内容是您能做的最差（或最好，对于想要破坏它的人来说）的安全验证。如果您需要更安全的方法，请使用加密和证书认证等技术。对于存储密钥来说，一个简单的方法可能是：

函数 device_is_my_type()
{
   echo 1 > authorized		# 暂时授权它
                                # TODO: 确保没有人可以挂载它
   mount DEVICENODE /mntpoint
   sum=$(md5sum /mntpoint/.signature)
   如果 [ $sum = $(cat /etc/lockdown/keysum) ]
   那么
        echo "一切正常，已连接"
        umount /mntpoint
        # 其他操作以便其他人可以使用它
   否则
        echo 0 > authorized
   结束
}


当然，这是简陋的版本，您应该使用真正的证书验证和公钥基础设施（PKI），这样您就不依赖共享秘密等信息，但您已经明白了。任何有访问设备工具包的人可以伪造描述符和设备信息。不要信任这些。欢迎使用！

接口授权
-----------------------

有一种类似的方法来允许或拒绝特定的USB接口
这允许只阻止USB设备的一部分
授权一个接口：

	$ echo 1 > /sys/bus/usb/devices/INTERFACE/authorized

取消授权一个接口：

	$ echo 0 > /sys/bus/usb/devices/INTERFACE/authorized

对于特定USB总线的新接口的默认值也可以更改
默认允许接口：

	$ echo 1 > /sys/bus/usb/devices/usbX/interface_authorized_default

默认拒绝接口：

	$ echo 0 > /sys/bus/usb/devices/usbX/interface_authorized_default

默认情况下，interface_authorized_default位设置为1
因此所有接口都会默认被授权
注意：
  如果未授权的接口要被授权，则必须手动触发驱动程序探测，方法是在/sys/bus/usb/drivers_probe中写入INTERFACE

对于需要多个接口的驱动程序，应先授权所有需要的接口。之后，应该探测驱动程序。
这避免了副作用
