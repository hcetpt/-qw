========================
内核驱动 i2c-viapro
========================

支持的适配器：
  * VIA Technologies, Inc. VT82C596A/B
    数据手册：有时可在 VIA 网站上获取

  * VIA Technologies, Inc. VT82C686A/B
    数据手册：有时可在 VIA 网站上获取

  * VIA Technologies, Inc. VT8231, VT8233, VT8233A
    数据手册：可应要求从 VIA 获取

  * VIA Technologies, Inc. VT8235, VT8237R, VT8237A, VT8237S, VT8251
    数据手册：可应要求并在签署保密协议（NDA）后从 VIA 获取

  * VIA Technologies, Inc. CX700
    数据手册：可应要求并在签署保密协议（NDA）后从 VIA 获取

  * VIA Technologies, Inc. VX800/VX820
    数据手册：可在 http://linux.via.com.tw 获取

  * VIA Technologies, Inc. VX855/VX875
    数据手册：可在 http://linux.via.com.tw 获取

  * VIA Technologies, Inc. VX900
    数据手册：可在 http://linux.via.com.tw 获取

作者：
	- Kyösti Mälkki <kmalkki@cc.hut.fi>,
	- Mark D. Studebaker <mdsxyz123@yahoo.com>,
	- Jean Delvare <jdelvare@suse.de>

模块参数
-----------------

* force: 整数
  强制启用 SMBus 控制器。危险！
* force_addr: 整数
  在给定地址处强制启用 SMBus。极其危险！

描述
-----------

i2c-viapro 是适用于带有受支持 VIA 南桥之一的主板的真实 SMBus 主机驱动。
您的 ``lspci -n`` 列表必须包含以下内容之一：

 ================   ======================
 设备 1106:3050   (VT82C596A 功能 3)
 设备 1106:3051   (VT82C596B 功能 3)
 设备 1106:3057   (VT82C686 功能 4)
 设备 1106:3074   (VT8233)
 设备 1106:3147   (VT8233A)
 设备 1106:8235   (VT8231 功能 4)
 设备 1106:3177   (VT8235)
 设备 1106:3227   (VT8237R)
 设备 1106:3337   (VT8237A)
 设备 1106:3372   (VT8237S)
 设备 1106:3287   (VT8251)
 设备 1106:8324   (CX700)
 设备 1106:8353   (VX800/VX820)
 设备 1106:8409   (VX855/VX875)
 设备 1106:8410   (VX900)
 ================   ======================

如果未出现上述任何一项，您应该在 BIOS 中查找诸如启用 ACPI/SMBus 甚至 USB 的设置。
除了最旧的芯片（VT82C596A/B、VT82C686A 和很可能还包括 VT8231），此驱动支持 I2C 块传输。此类传输主要用于读取和写入 EEPROM。
CX700/VX800/VX820 还似乎支持 SMBus PEC，尽管此驱动尚未实现该功能。
