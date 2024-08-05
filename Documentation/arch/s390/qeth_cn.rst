=============================
IBM s390 QDIO 以太网驱动
=============================

OSA 和 HiperSockets 桥接端口支持
========================================

Uevents
-------

为了生成事件，设备必须被分配为主桥接端口或次级桥接端口的角色之一。更多信息，请参阅 "z/VM 连通性, SC24-6174"。
当在支持 OSA 或 HiperSockets 桥接功能的端口硬件上运行，并且配置的桥接端口设备通道状态发生变化时，将为相应的 ccwgroup 设备触发一个带有 ACTION=CHANGE 的 udev 事件。该事件具有以下属性：

BRIDGEPORT=statechange
  表明桥接端口设备的状态发生了变化
ROLE={primary|secondary|none}
  分配给端口的角色
STATE={active|standby|inactive}
  端口新采用的状态

当在启用了主机地址通知的 HiperSockets 桥接功能端口硬件上运行时，会触发一个带有 ACTION=CHANGE 的 udev 事件。
此事件会在主机或 VLAN 在由设备服务的网络中注册或注销时，为相应的 ccwgroup 设备触发。该事件具有以下属性：

BRIDGEDHOST={reset|register|deregister|abort}
  主机地址通知开始重新启动，新的主机或 VLAN 在桥接端口 HiperSockets 通道中注册或注销，或者地址通知被中止
VLAN=numeric-vlan-id
  事件发生的 VLAN ID。如果事件不涉及 VLAN，则不会包含
MAC=xx:xx:xx:xx:xx:xx
  正在注册或从 HiperSockets 通道注销的主机的 MAC 地址。如果事件报告的是 VLAN 的创建或销毁，则不会报告
NTOK_BUSID=x.y.zzzz
  设备总线 ID（CSSID, SSID 和设备编号）
翻译为中文：

NTOK_IID=xx 
设备 IID
NTOK_CHPID=xx 
设备 CHPID
NTOK_CHID=xxxx 
设备通道 ID

请注意，`NTOK_*` 属性所指的设备并不是操作系统所在系统连接的那个设备。
