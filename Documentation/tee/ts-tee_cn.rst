SPDX许可证标识符: GPL-2.0

=================================
TS-TEE（Trusted Services项目）
=================================

此驱动程序提供了对由Trusted Services实现的安全服务的访问。Trusted Services [1] 是TrustedFirmware.org的一个项目，提供了一个开发和部署FF-A [2] S-EL0安全分区（Secure Partitions）中设备的信任根（Root of Trust）服务的框架。该项目托管了Arm平台安全架构 [3] 的参考实现，适用于Arm A系列设备。FF-A安全分区（SP）通过FF-A驱动程序 [4] 访问，该驱动程序提供了此驱动程序所需的低级通信。在此基础上使用了Trusted Services远程过程调用（RPC）协议 [5]。为了从用户空间使用该驱动程序，提供了一个参考实现在 [6]，它是Trusted Services客户端库libts [7]的一部分。

所有Trusted Services（TS）SP都具有相同的FF-A UUID；它标识了TS RPC协议。一个TS SP可以承载一个或多个服务（例如PSA Crypto、PSA ITS等）。服务通过其服务UUID来识别；同一SP中不能存在两个相同类型的服务。在SP启动期间，SP中的每个服务都会被分配一个“接口ID”。这只是一个简短的ID，用于简化消息寻址。

通用TEE设计是与可信操作系统一次性共享内存，然后可以重用以与在可信操作系统上运行的多个应用程序进行通信。然而，在FF-A的情况下，内存共享是在端点级别进行的，即内存与特定的SP共享。用户空间必须能够根据其端点ID单独与每个SP共享内存；因此为每个发现的TS SP注册一个单独的TEE设备。打开SP相当于打开TEE设备并创建TEE上下文。一个TS SP承载一个或多个服务。打开服务相当于在给定的tee_context中打开一个会话。

包含Trusted Services组件的系统概述如下：

```
用户空间                      内核空间                       安全世界
~~~~~~~~~~~~                  ~~~~~~~~~~~~                   ~~~~~~~~~~~~
+--------+                                                +-------------+
| Client |                                                | Trusted     |
+--------+                                                | Services SP |
    /\                                                     +-------------+
    ||                                                        /\
    ||                                                        ||
    ||                                                        ||
    \/                                                        \/
+-------+                +----------+--------+           +-------------+
| libts |                |  TEE     | TS-TEE |           |  FF-A SPMC  |
|       |                |  subsys  | driver |           |   + SPMD    |
+-------+----------------+----+-----+--------+-----------+-------------+
|      通用TEE API          |     |  FF-A  |     TS RPC协议            |
|      IOCTL (TEE_IOC_*)    |     | 驱动程序 |  通过FF-A               |
+-----------------------------+     +--------+-------------------------+
```

参考文献
==========

[1] https://www.trustedfirmware.org/projects/trusted-services/

[2] https://developer.arm.com/documentation/den0077/

[3] https://www.arm.com/architecture/security-features/platform-security

[4] drivers/firmware/arm_ffa/

[5] https://trusted-services.readthedocs.io/en/v1.0.0/developer/service-access-protocols.html#abi

[6] https://git.trustedfirmware.org/TS/trusted-services.git/tree/components/rpc/ts_rpc/caller/linux/ts_rpc_caller_linux.c?h=v1.0.0

[7] https://git.trustedfirmware.org/TS/trusted-services.git/tree/deployments/libts/arm-linux/CMakeLists.txt?h=v1.0.0
