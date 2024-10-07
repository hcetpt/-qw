SPDX 许可证标识符: GPL-2.0

=======================================
ARM 固件伪寄存器接口
=======================================

KVM 处理来宾请求的超调用服务。ARM 规范或 KVM（作为供应商服务）会定期提供新的超调用服务，前提是这些服务在虚拟化方面有意义。
这意味着，在两个不同版本的 KVM 上启动的来宾可能会观察到两个不同的“固件”版本。如果某个特定来宾依赖于某个超调用服务的特定版本，或者迁移导致意外地暴露给不知情的来宾，则可能会引发问题。
为了解决这种情况，KVM 暴露了一组“固件伪寄存器”，这些寄存器可以通过 GET/SET_ONE_REG 接口进行操作。这些寄存器可以由用户空间保存和恢复，并根据需要设置为方便的值。
以下定义了以下寄存器：

* KVM_REG_ARM_PSCI_VERSION：

  KVM 实现了 PSCI（电源状态协调接口）规范，以向来宾提供诸如 CPU 开关、复位和断电等服务。
- 仅当 vcpu 设置了 KVM_ARM_VCPU_PSCI_0_2 特性（并且已经初始化完毕）时有效
  - 在使用 GET_ONE_REG 时返回当前的 PSCI 版本（默认为 KVM 实现的最高 PSCI 版本且兼容 v0.2）
  - 允许通过 SET_ONE_REG 设置任何由 KVM 实现并兼容 v0.2 的 PSCI 版本
  - 影响整个虚拟机（即使寄存器视图是按 vcpu 的）

* KVM_REG_ARM_SMCCC_ARCH_WORKAROUND_1：
    存储 KVM 通过 HVC 调用向来宾提供的用于缓解 CVE-2017-5715 的固件支持的状态。缓解方法描述见 [1] 中的 SMCCC_ARCH_WORKAROUND_1
接受的值包括：

    KVM_REG_ARM_SMCCC_ARCH_WORKAROUND_1_NOT_AVAIL：
      KVM 不提供该缓解方法的固件支持。来宾的缓解状态未知
    KVM_REG_ARM_SMCCC_ARCH_WORKAROUND_1_AVAIL：
      缓解方法的 HVC 调用对来宾可用，并且对于缓解来说是必需的
    KVM_REG_ARM_SMCCC_ARCH_WORKAROUND_1_NOT_REQUIRED：
      缓解方法的 HVC 调用对来宾可用，但在当前 VCPU 上不需要

* KVM_REG_ARM_SMCCC_ARCH_WORKAROUND_2：
    存储 KVM 通过 HVC 调用向来宾提供的用于缓解 CVE-2018-3639 的固件支持的状态。缓解方法描述见 [1] 中的 SMCCC_ARCH_WORKAROUND_2
接受的值包括：

    KVM_REG_ARM_SMCCC_ARCH_WORKAROUND_2_NOT_AVAIL：
      缓解方法不可用。KVM 不提供该缓解方法的固件支持
KVM_REG_ARM_SMCCC_ARCH_WORKAROUND_2_UNKNOWN:
      该规避状态未知。KVM 不提供针对此规避的固件支持。

KVM_REG_ARM_SMCCC_ARCH_WORKAROUND_2_AVAIL:
      该规避措施可用，并且可以通过一个 vCPU 禁用。如果设置了 KVM_REG_ARM_SMCCC_ARCH_WORKAROUND_2_ENABLED，则该规避措施对当前 vCPU 是激活的。

KVM_REG_ARM_SMCCC_ARCH_WORKAROUND_2_NOT_REQUIRED:
      该规避措施在当前 vCPU 上始终是激活的，或者不需要。

位图功能固件寄存器
--------------------

与上述寄存器不同，以下寄存器以位图的形式向用户空间暴露超调用服务。这个位图被转换为可供客户机使用的服务。
每个服务调用所有者都有一个定义好的寄存器，并且可以通过 GET/SET_ONE_REG 接口访问。
默认情况下，这些寄存器设置为所支持功能的上限。这样，用户空间可以通过 GET_ONE_REG 发现所有可用的超调用服务。用户空间可以通过 SET_ONE_REG 将所需的位图写回。对于那些未被修改的寄存器（可能是因为用户空间不知道它们），其功能将原样暴露给客户机。
请注意，一旦任何一个 vCPU 至少运行过一次，KVM 将不再允许用户空间配置这些寄存器。相反，它会返回 -EBUSY 错误码。
伪固件位图寄存器如下：

* KVM_REG_ARM_STD_BMAP:
    控制 ARM 标准安全服务调用的位图。
    以下位是可接受的：

    Bit-0: KVM_REG_ARM_STD_BIT_TRNG_V1_0:
      该位表示 ARM 真随机数生成器（TRNG）规范 v1.0 (ARM DEN0098) 下提供的服务。

* KVM_REG_ARM_STD_HYP_BMAP:
    控制 ARM 标准虚拟化服务调用的位图。
以下位被接受：

    位-0: KVM_REG_ARM_STD_HYP_BIT_PV_TIME:
      该位表示由 ARM DEN0057A 定义的半虚拟化时间服务
* KVM_REG_ARM_VENDOR_HYP_BMAP:
    控制特定供应商的 Hypervisor 服务调用的位图
以下位被接受：

    位-0: KVM_REG_ARM_VENDOR_HYP_BIT_FUNC_FEAT
      该位表示 ARM_SMCCC_VENDOR_HYP_KVM_FEATURES_FUNC_ID 和
      ARM_SMCCC_VENDOR_HYP_CALL_UID_FUNC_ID 函数标识
位-1: KVM_REG_ARM_VENDOR_HYP_BIT_PTP:
      该位表示精密时间协议 KVM 服务
错误：

    =======  =============================================================
    -ENOENT   访问了未知寄存器
-EBUSY    在虚拟机启动后尝试对该寄存器进行 '写' 操作
-EINVAL   写入寄存器的位图无效
=======  =============================================================

.. [1] https://developer.arm.com/-/media/developer/pdf/ARM_DEN_0070A_Firmware_interfaces_for_mitigating_CVE-2017-5715.pdf
