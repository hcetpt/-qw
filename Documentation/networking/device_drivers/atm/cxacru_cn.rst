SPDX 许可证标识符: GPL-2.0

========================
ATM cxacru 设备驱动程序
========================

此设备需要固件：http://accessrunner.sourceforge.net/

虽然它能够在不加载模块的情况下管理和维护ADSL连接，但在卸载驱动程序后，设备有时会停止响应，并且需要拔掉或断开设备电源来解决这个问题。请注意：已移除对 cxacru-cf.bin 的支持。因为它未能正确加载，因此对设备配置没有影响。修复它可能会导致在提供无效配置时现有设备无法工作。
存在一个脚本 cxacru-cf.py 可用于将现有文件转换为 sysfs 形式。
检测到的设备将以名为 "cxacru" 的 ATM 设备形式出现。在 /sys/class/atm/ 中，这些是名为 cxacruN 的目录，其中 N 是设备编号。一个名为 device 的符号链接指向 USB 接口设备的目录，该目录包含几个用于检索设备统计信息的 sysfs 属性文件：

* adsl_controller_version

* adsl_headend
* adsl_headend_environment

	- 关于远程前端的信息
* adsl_config

	- 配置写入接口
- 以十六进制格式写入参数 <index>=<value>，
	  用空格分隔，例如：

		"1=0 a=5"

	- 每次最多发送 7 个参数，并且当设置任何值时，调制解调器将重启 ADSL 连接。这些参数被记录以便将来参考
* downstream_attenuation (dB)
* downstream_bits_per_frame
* downstream_rate (kbps)
* downstream_snr_margin (dB)

	- 下行链路统计
* upstream_attenuation (dB)
* upstream_bits_per_frame
* upstream_rate (kbps)
* upstream_snr_margin (dB)
* transmitter_power (dBm/Hz)

	- 上行链路统计
* downstream_crc_errors
* downstream_fec_errors
* downstream_hec_errors
* upstream_crc_errors
* upstream_fec_errors
* upstream_hec_errors

	- 错误计数
* line_startable

	- 表明设备上的 ADSL 支持
	  已启用/可以启用，请参阅 adsl_start
* 线路状态

	 - "初始化中"
	 - "断开"
	 - "尝试激活"
	 - "训练中"
	 - "信道分析"
	 - "交换"
	 - "等待中"
	 - "连接"

	在"断开"和"尝试激活"之间变化
	如果没有信号
* 链接状态

	 - "未连接"
	 - "已连接"
	 - "已断开"

* MAC地址

* 调制方式

	 - ""（当未连接时）
	 - "ANSI T1.413"
	 - "ITU-T G.992.1 (G.DMT)"
	 - "ITU-T G.992.2 (G.LITE)"

* 启动尝试次数

	- 初始化ADSL的总尝试次数

为了启用/禁用ADSL，可以向adsl_state文件写入以下内容：

	 - "start"（启动）
	 - "stop"（停止）
	 - "restart"（停止，等待1.5秒，然后启动）
	 - "poll"（如果由于失败而禁用了状态轮询，则用于恢复状态轮询）

通过内核日志消息报告ADSL线路状态的变化：

	[4942145.150704] ATM设备 0: ADSL状态: 运行中
	[4942243.663766] ATM设备 0: ADSL线路: 断开
	[4942249.665075] ATM设备 0: ADSL线路: 尝试激活
	[4942253.654954] ATM设备 0: ADSL线路: 训练中
	[4942255.666387] ATM设备 0: ADSL线路: 信道分析
	[4942259.656262] ATM设备 0: ADSL线路: 交换
	[2635357.696901] ATM设备 0: ADSL线路: 连接 (下行速度8128 kb/s | 上行速度832 kb/s)
