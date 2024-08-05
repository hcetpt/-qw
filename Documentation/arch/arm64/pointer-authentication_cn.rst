==============================
AArch64 Linux中的指针认证
==============================

作者：Mark Rutland <mark.rutland@arm.com>

日期：2017-07-19

本文档简要介绍了在AArch64 Linux中提供指针认证功能。

架构概述
---------

ARMv8.3 指针认证扩展添加了可用于缓解某些类型的攻击（例如，攻击者可以篡改某些内存内容（如堆栈））的基本原语。
该扩展使用指针认证码（PAC）来确定指针是否被意外修改。PAC是从指针、另一个值（如堆栈指针）以及系统寄存器中持有的秘密密钥派生出来的。
该扩展添加了指令以将有效的PAC插入到指针中，并验证/从指针中移除PAC。PAC占据指针中的一些高位，这些高位的数量取决于配置的虚拟地址大小以及是否启用了指针标记。
该扩展从HINT编码空间分配了一部分这些指令。在没有该扩展（或被禁用）的情况下，这些指令会表现为NOPs。使用这些指令的应用程序和库无论扩展是否存在都能正确运行。
该扩展提供了五个独立的密钥来生成PACs——两个用于指令地址（APIAKey，APIBKey），两个用于数据地址（APDAKey，APDBKey），一个用于通用认证（APGAKey）。

基本支持
---------

当选择了CONFIG_ARM64_PTR_AUTH，并且存在相关的硬件支持时，内核将在执行exec*()时为每个进程分配随机密钥值。这些密钥由进程内的所有线程共享，并且在fork()时保留不变。
地址认证功能的存在通过HWCAP_PACA宣传，而通用认证功能则通过HWCAP_PACG宣传。
PAC在指针中占据的位数是55减去内核配置的虚拟地址大小。例如，在虚拟地址大小为48的情况下，PAC宽7位。
当选择了ARM64_PTR_AUTH_KERNEL时，内核将以保护函数返回的HINT空间指针认证指令进行编译。使用此选项构建的内核可以在具有或不具有指针认证支持的硬件上工作。
除了使用 `exec()` 外，密钥也可以通过 `PR_PAC_RESET_KEYS` 的 `prctl` 调用被重置为随机值。一个位掩码可以指定哪些密钥需要被重置，其中包括 `PR_PAC_APIAKEY`、`PR_PAC_APIBKEY`、`PR_PAC_APDAKEY`、`PR_PAC_APDBKEY` 和 `PR_PAC_APGAKEY`；如果设置为 0，则表示“所有密钥”。

**调试**

当选择了 `CONFIG_ARM64_PTR_AUTH` 配置，并且硬件支持地址认证时，内核将通过 `NT_ARM_PAC_MASK` 寄存器集（`struct user_pac_mask` 结构体）暴露 TTBR0 的 PAC 位的位置，用户空间可以通过 `PTRACE_GETREGSET` 获取这些信息。
该寄存器集仅在设置了 `HWCAP_PACA` 时才可访问。数据指针和指令指针分别暴露了不同的掩码，因为这两种类型的 PAC 位可能不同。需要注意的是，这些掩码适用于 TTBR0 地址，并不适用于 TTBR1 地址（例如内核指针）。

另外，如果还启用了 `CONFIG_CHECKPOINT_RESTORE` 配置，内核会暴露 `NT_ARM_PACA_KEYS` 和 `NT_ARM_PACG_KEYS` 寄存器集（`struct user_pac_address_keys` 和 `struct user_pac_generic_keys`）。这些可以用来获取和设置线程的密钥。

**虚拟化**

在 KVM 客户机中初始化每个虚拟 CPU 时，通过传递标志 `KVM_ARM_VCPU_PTRAUTH_ADDRESS` 和 `KVM_ARM_VCPU_PTRAUTH_GENERIC` 并请求启用这两个单独的 CPU 功能来启用指针认证。当前的 KVM 客户机实现是同时启用这两个功能，因此在启用指针认证之前会检查这两个用户空间标志。
单独的用户空间标志将允许未来添加支持以独立启用这两个特性而无需更改用户空间 ABI。

由于 Arm 架构规定指针认证特性与 VHE 特性一起实现，所以 KVM 的 arm64 指针认证代码依赖于 VHE 模式的存在。
此外，当没有设置这些 vCPU 功能标志时，KVM 将从 `KVM_GET/SET_REG_*` ioctl 中过滤掉指针认证系统密钥寄存器，并在 CPU 特征 ID 寄存器中屏蔽这些特性。任何尝试使用指针认证指令的行为都会导致向客户机注入一个未定义的异常。

**启用和禁用密钥**

`prctl PR_PAC_SET_ENABLED_KEYS` 允许用户程序控制特定任务中的哪些 PAC 密钥被启用。它接受两个参数：第一个参数是一个位掩码，包括 `PR_PAC_APIAKEY`、`PR_PAC_APIBKEY`、`PR_PAC_APDAKEY` 和 `PR_PAC_APDBKEY`，用于指定哪些密钥将受此 `prctl` 影响；第二个参数也是一个同样的位掩码，用于指定密钥是否应该被启用或禁用。例如：

```c
prctl(PR_PAC_SET_ENABLED_KEYS,
      PR_PAC_APIAKEY | PR_PAC_APIBKEY | PR_PAC_APDAKEY | PR_PAC_APDBKEY,
      PR_PAC_APIBKEY, 0, 0);
```

这个例子禁用了除 IB 密钥之外的所有密钥。

这样做的主要原因是使用户空间 ABI 能够利用 PAC 指令对函数指针和其他暴露在函数外部的指针进行签名和认证，同时还允许符合 ABI 的二进制文件与那些不进行指针签名或认证的传统二进制文件互操作。
这个想法是，在确认一个进程可能加载遗留二进制文件之后，动态加载器或早期启动代码会非常早地发出此 `prctl` 调用，但在执行任何 PAC 指令之前。
为了与之前的内核版本保持兼容，进程在启动时会启用 IA、IB、DA 和 DB，并且在 `exec()` 时重置为这种状态。通过 `fork()` 和 `clone()` 创建的进程会从调用进程继承启用密钥的状态。
建议避免禁用 IA 密钥，因为相比于禁用其他任何密钥，禁用 IA 密钥会有更高的性能开销。
