SPDX 许可证标识符: GPL-2.0

====================================================
OP-TEE（开放便携可信执行环境）
====================================================

OP-TEE 驱动程序处理基于 OP-TEE [1] 的可信执行环境 (TEE)。目前，仅支持基于 ARM TrustZone 的 OP-TEE 解决方案。
与 OP-TEE 的最低级别通信基于 ARM SMC 调用约定 (SMCCC) [2]，这是驱动程序内部使用的 OP-TEE SMC 接口 [3] 的基础。在此基础上构建了 OP-TEE 消息协议 [4]。

OP-TEE SMC 接口提供了 SMCCC 所需的基本功能，并且包含了一些特定于 OP-TEE 的附加功能。最有趣的功能包括：

- `OPTEE_SMC_FUNCID_CALLS_UID`（SMCCC 的一部分）返回版本信息，然后由 `TEE_IOC_VERSION` 返回。
- `OPTEE_SMC_CALL_GET_OS_UUID` 返回特定的 OP-TEE 实现，用于区分例如 TrustZone OP-TEE 和运行在独立安全协处理器上的 OP-TEE。
- `OPTEE_SMC_CALL_WITH_ARG` 驱动 OP-TEE 消息协议。
- `OPTEE_SMC_GET_SHM_CONFIG` 允许驱动程序和 OP-TEE 约定用于 Linux 和 OP-TEE 之间共享内存的内存范围。

GlobalPlatform TEE 客户端 API [5] 是基于通用 TEE API 实现的。
不同组件间关系图示如下：

      用户空间                    内核                        安全世界
      ~~~~~~~~~~                  ~~~~~~                     ~~~~~~~~~~~~
   +--------+                                               +-------------+
   | 客户端  |                                               | 受信应用    |
   +--------+                                               +-------------+
      /\                                                      ||
      || +----------+                                           ||
      || |tee-      |                                           ||
      || |supplicant|                                           \/
      || +----------+                                     +-------------+
      \/      /\                                          | TEE 内部   |
   +-------+  ||                                          | API         |
   + TEE   |  ||            +--------+--------+           +-------------+
   | 客户端|  ||            | TEE    | OP-TEE |           | OP-TEE      |
   | API   |  \/            | 子系统 | 驱动程序|           | 受信操作系统|
   +-------+----------------+----+-------+----+-----------+-------------+
   |      通用 TEE API          |       |     OP-TEE 消息              |
   |      IOCTL (TEE_IOC_*)     |       |     SMCCC (OPTEE_SMC_CALL_*) |
   +-----------------------------+       +-------------------------------+

RPC（远程过程调用）是从安全世界到内核驱动或 tee-supplicant 的请求。一个 RPC 通过从 `OPTEE_SMC_CALL_WITH_ARG` 返回的一系列特殊 SMCCC 值来识别。意图发送给内核的 RPC 消息由内核驱动处理。其他 RPC 消息将被转发到 tee-supplicant，除了切换共享内存缓冲表示之外，驱动程序不再参与其中。

OP-TEE 设备枚举
-------------------------

OP-TEE 提供了一个伪受信应用：drivers/tee/optee/device.c，以支持设备枚举。换句话说，OP-TEE 驱动程序调用此应用以获取可以注册为 TEE 总线设备的受信应用列表。

OP-TEE 通知
--------------------

安全世界可以使用两种类型的通知来使普通世界意识到某个事件：
1. 使用 `OPTEE_RPC_CMD_NOTIFICATION` 发送的同步通知，参数为 `OPTEE_RPC_NOTIFICATION_SEND`。
2. 使用非安全边沿触发中断与非安全中断处理程序中的快速调用来传递异步通知。
同步通知受限于依赖RPC进行传递，
这仅在通过`OPTEE_SMC_CALL_WITH_ARG`调用进入安全世界时可用。这排除了此类通知在安全世界中断处理程序中的使用。
异步通知通过非安全边沿触发中断传递给在OP-TEE驱动中注册的中断处理程序。实际的通知值通过快速调用`OPTEE_SMC_GET_ASYNC_NOTIF_VALUE`获取。注意，一个中断可以代表多个通知。
有一个特殊的通知值`OPTEE_SMC_ASYNC_NOTIF_VALUE_DO_BOTTOM_HALF`具有特殊含义。当接收到此值时，表示普通世界应该执行一个yield调用`OPTEE_MSG_CMD_DO_BOTTOM_HALF`。这个调用是由辅助中断处理程序的线程完成的。这是OP-TEE OS在安全世界中实现上半部分和下半部分设备驱动风格的一个构建块。

### OPTEE_INSECURE_LOAD_IMAGE Kconfig 选项

---

OPTEE_INSECURE_LOAD_IMAGE Kconfig 选项启用了在内核启动后从内核加载BL32 OP-TEE镜像的能力，而不是在内核启动前从固件加载。这也要求在Arm Trusted Firmware中启用相应的选项。Arm Trusted Firmware文档[6]解释了启用此功能相关的安全威胁以及在固件和平台级别的缓解措施。
当使用此选项时，内核还有额外的攻击向量/缓解措施需要解决：

1. 启动链安全性
   * 攻击向量：替换根文件系统中的OP-TEE OS镜像以控制整个系统
   * 缓解措施：必须有验证内核和根文件系统的启动链安全性，否则攻击者可以通过修改根文件系统中的OP-TEE二进制文件来修改加载的OP-TEE二进制文件

2. 替代启动模式
   * 攻击向量：使用替代启动模式（例如恢复模式），OP-TEE驱动不会被加载，导致SMC漏洞暴露
### 减轻措施：如果设备有其他启动方法，例如恢复模式，应确保在这些模式下也应用相同的缓解措施。

3. 在调用SMC之前的攻击
* 攻击向量：在发出SMC调用以加载OP-TEE之前执行的代码可能会被利用，从而加载一个替代的操作系统镜像。
* 减轻措施：OP-TEE驱动程序必须在任何潜在攻击向量打开之前加载。这应包括挂载任何可修改的文件系统、打开网络端口或与外部设备（例如USB）通信。

4. 阻止SMC调用以加载OP-TEE
* 攻击向量：阻止驱动程序被探测，因此在需要时不会执行SMC调用来加载OP-TEE，从而使它在稍后被执行并加载一个修改过的操作系统。
* 减轻措施：建议将OP-TEE驱动程序作为内置驱动程序构建，而不是作为一个模块，以防止可能导致该模块未加载的漏洞。

### 参考资料
1. [https://github.com/OP-TEE/optee_os](https://github.com/OP-TEE/optee_os)
2. [http://infocenter.arm.com/help/topic/com.arm.doc.den0028a/index.html](http://infocenter.arm.com/help/topic/com.arm.doc.den0028a/index.html)
3. [drivers/tee/optee/optee_smc.h](drivers/tee/optee/optee_smc.h)
4. [drivers/tee/optee/optee_msg.h](drivers/tee/optee/optee_msg.h)
5. [http://www.globalplatform.org/specificationsdevice.asp](http://www.globalplatform.org/specificationsdevice.asp) 寻找“TEE Client API Specification v1.0”，然后点击下载
6. [https://trustedfirmware-a.readthedocs.io/en/latest/threat_model/threat_model.html](https://trustedfirmware-a.readthedocs.io/en/latest/threat_model/threat_model.html)
