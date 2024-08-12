### SPDX 许可证标识符：GPL-2.0

#### 英特尔® 主动管理技术（英特尔 AMT）
====================================

英特尔 ME 接口的显著用途之一是与实施在英特尔 ME 上运行的固件中的英特尔® 主动管理技术（英特尔 AMT）进行通信。
英特尔 AMT 提供了远程带外（OOB）管理主机的能力，即使主机处理器上运行的操作系统已崩溃或处于睡眠状态。
英特尔 AMT 的一些用途示例包括：
   - 监控硬件状态和平台组件
   - 远程关机/开机（适用于绿色计算或夜间 IT 维护）
   - 操作系统更新
   - 存储有用的平台信息，如软件资产
   - 内置硬件 KVM
   - 根据远程管理控制台设置的策略选择性地隔离以太网和 IP 协议流
   - 从远程管理控制台重定向 IDE 设备

英特尔 AMT (OOB) 通信基于 SOAP（从第 6.0 版开始废弃）通过 HTTP/S 或 WS-Management 协议通过 HTTP/S，这些协议来自远程管理控制台应用。
更多关于英特尔 AMT 的信息，请访问：
https://software.intel.com/sites/manageability/AMT_Implementation_and_Reference_Guide/default.htm

#### 英特尔 AMT 应用
----------------------

    1) 英特尔本地管理服务（英特尔 LMS）

       在平台上本地运行的应用程序通过 SOAP 通过 HTTP（从第 6.0 版开始废弃）或通过 WS-Management 通过 SOAP 通过 HTTP 与英特尔 AMT 第 2.0 版及后续版本通信的方式与网络应用程序相同。这意味着一些英特尔 AMT 功能可以通过使用与远程应用程序通过网络与英特尔 AMT 通信时相同的网络接口从本地应用程序访问。
当本地应用程序发送指向本地英特尔 AMT 主机名的消息时，监听指向该主机名的流量的英特尔 LMS 会拦截该消息并将其路由到英特尔 MEI。
更多信息：
       https://software.intel.com/sites/manageability/AMT_Implementation_and_Reference_Guide/default.htm
       在“关于英特尔 AMT”=> “本地访问”下。

       下载英特尔 LMS：
       https://github.com/intel/lms

       英特尔 LMS 使用定义的 GUID 通过英特尔 MEI 驱动程序打开与英特尔 LMS 固件功能的连接，然后使用一种称为英特尔 AMT 端口转发协议（英特尔 APF 协议）的协议与该功能通信。
该协议用于维持单个应用程序与英特尔 AMT 的多个会话。
请参阅英特尔 AMT 软件开发工具包 (SDK) 中的协议规范：
       https://software.intel.com/sites/manageability/AMT_Implementation_and_Reference_Guide/default.htm
       在“SDK 资源”=> “英特尔® vPro™ 网关 (MPS)” => “英特尔® vPro™ 网关开发者信息” => “英特尔 AMT 端口转发 (APF) 协议描述”

    2) 使用本地代理配置英特尔 AMT

       本地代理使 IT 人员能够在不需要安装额外数据的情况下开箱即用地配置英特尔 AMT。远程配置过程可能涉及 ISV 开发的远程配置代理，该代理运行在主机上。
更多信息：
       https://software.intel.com/sites/manageability/AMT_Implementation_and_Reference_Guide/default.htm
       在“英特尔 AMT 设置与配置”=> “支持设置与配置的 SDK 工具” => “使用本地代理示例”

#### 英特尔 AMT 操作系统健康看门狗
-----------------------------------

英特尔 AMT 看门狗是一个操作系统健康（挂起/崩溃）看门狗。
每当操作系统挂起或崩溃时，英特尔 AMT 将向此事件的任何订阅者发送一个事件。这种机制意味着 IT 可以知道平台何时崩溃，即使主机出现严重故障。
英特尔主动管理技术 (Intel AMT) 看门狗由两部分组成：
1) 固件特性 — 接收心跳信号，
       并在心跳停止时发送事件。
2) 英特尔管理引擎接口 (Intel MEI) iAMT 看门狗驱动程序 — 连接到看门狗特性，
       配置看门狗并发送心跳信号。
英特尔 iAMT 看门狗 MEI 驱动程序使用内核看门狗 API 来配置
英特尔 AMT 看门狗并向其发送心跳信号。看门狗的默认超时时间为 120 秒。
如果固件中未启用英特尔 AMT，则看门狗客户端不会在 ME 客户端总线上枚举，
且不会暴露看门狗设备。

---
linux-mei@linux.intel.com
