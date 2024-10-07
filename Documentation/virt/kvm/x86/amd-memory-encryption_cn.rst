SPDX 许可声明标识符: GPL-2.0

======================================
安全加密虚拟化 (SEV)
======================================

概述
========

安全加密虚拟化 (SEV) 是 AMD 处理器上的一个特性。
SEV 是 AMD-V 架构的一个扩展，支持在管理程序的控制下运行虚拟机 (VM)。当启用时，虚拟机的内存内容将使用仅对该 VM 独有的密钥进行透明加密。
管理程序可以通过 CPUID 指令确定 SEV 的支持情况。CPUID 功能 0x8000001f 报告与 SEV 相关的信息如下：

	0x8000001f[eax]:
			第1位 表示支持 SEV
	    ..
	[ecx]:
			第31到0位 同时支持的加密虚拟机数量

如果存在对 SEV 的支持，可以通过模型特定寄存器 (MSR) 0xc001_0010 (MSR_AMD64_SYSCFG) 和 MSR 0xc001_0015 (MSR_K7_HWCR) 来确定是否可以启用它：

	0xc001_0010:
		第23位 1 = 可以启用内存加密
				 0 = 不能启用内存加密

	0xc001_0015:
		第0位 1 = 可以启用内存加密
				 0 = 不能启用内存加密

当 SEV 支持可用时，可以在执行 VMRUN 前通过设置 SEV 位来为特定 VM 启用它：

	VMCB[0x90]:
		第1位 1 = 启用 SEV
			 0 = 禁用 SEV

SEV 硬件使用地址空间标识符 (ASID) 将内存加密密钥与虚拟机关联。因此，启用 SEV 的虚拟机的 ASID 必须从 1 到 CPUID 0x8000001f[ecx] 字段定义的最大值。

KVM_MEMORY_ENCRYPT_OP ioctl
===============================

访问 SEV 的主要 ioctl 是 KVM_MEMORY_ENCRYPT_OP，其作用于 VM 文件描述符。如果 KVM_MEMORY_ENCRYPT_OP 的参数为 NULL，则 ioctl 在启用 SEV 时返回 0，在禁用时返回 "ENOTTY"（在某些旧版本的 Linux 中，ioctl 即使参数为 NULL 也会尝试正常运行，因此如果启用了 SEV，可能会返回 "EFAULT" 而不是零）。如果参数非 NULL，则 KVM_MEMORY_ENCRYPT_OP 的参数必须是 struct kvm_sev_cmd 类型：

       struct kvm_sev_cmd {
               __u32 id;
               __u64 data;
               __u32 error;
               __u32 sev_fd;
       };

`id` 字段包含子命令，`data` 字段指向另一个包含特定命令参数的结构体。`sev_fd` 应指向打开的 `/dev/sev` 设备的文件描述符（如果需要的话，请参见各个命令）。输出时，`error` 在成功时为零，或为错误代码。错误代码定义在 `<linux/psp-dev.h>` 中。

KVM 实现了以下命令来支持 SEV 客户机的常见生命周期事件，如启动、运行、快照、迁移和退役：
1. KVM_SEV_INIT2
----------------

KVM_SEV_INIT2 命令由管理程序用于初始化 SEV 平台上下文。在一个典型的工作流程中，此命令应该是发出的第一个命令。要接受此命令，必须已向 KVM_CREATE_VM ioctl 提供了 KVM_X86_SEV_VM 或 KVM_X86_SEV_ES_VM。反过来，使用这些机器类型创建的虚拟机在调用 KVM_SEV_INIT2 之前无法运行。
参数：`struct kvm_sev_init`（输入）

返回值：成功时返回 0，错误时返回负数

```c
    struct kvm_sev_init {
            __u64 vmsa_features;  /* VMSA 中 features 字段的初始值 */
            __u32 flags;          /* 必须为 0 */
            __u16 ghcb_version;   /* 允许的最大来宾 GHCB 版本 */
            __u16 pad1;
            __u32 pad2[8];
    };
```

如果虚拟机监控程序不支持 `flags` 或 `vmsa_features` 中设置的任何位，则视为错误。对于 SEV 虚拟机，`vmsa_features` 必须为 0，因为它们没有 VMSA；`ghcb_version` 也必须为 0，因为它们不会发出 GHCB 请求。如果其他类型来宾的 `ghcb_version` 为 0，则允许的最大来宾 GHCB 协议将默认为版本 2。

此命令替代了已弃用的 `KVM_SEV_INIT` 和 `KVM_SEV_ES_INIT` 命令。这些命令没有任何参数（`data` 字段未使用），并且仅适用于 `KVM_X86_DEFAULT_VM` 机器类型（0）。它们的行为如下：

* 对于 `KVM_SEV_INIT`，虚拟机类型为 `KVM_X86_SEV_VM`，对于 `KVM_SEV_ES_INIT`，虚拟机类型为 `KVM_X86_SEV_ES_VM`
* `struct kvm_sev_init` 中的 `flags` 和 `vmsa_features` 字段设置为零，`ghcb_version` 对于 `KVM_SEV_INIT` 设置为 0，对于 `KVM_SEV_ES_INIT` 设置为 1

如果不存在 `KVM_X86_SEV_VMSA_FEATURES` 属性，则虚拟机监控程序仅支持 `KVM_SEV_INIT` 和 `KVM_SEV_ES_INIT`。在这种情况下，请注意 `KVM_SEV_ES_INIT` 可能会根据 `kvm-amd.ko` 的 `debug_swap` 参数值设置调试交换 VMSA 特性（第 5 位）。

### 2. KVM_SEV_LAUNCH_START

`KVM_SEV_LAUNCH_START` 命令用于创建内存加密上下文。为了创建加密上下文，用户必须提供来宾策略、所有者的公钥 Diffie-Hellman (PDH) 键和会话信息。
参数：`struct kvm_sev_launch_start`（输入/输出）

返回值：成功时返回 0，错误时返回负数

```c
    struct kvm_sev_launch_start {
            __u32 handle;           /* 如果为零，则固件创建一个新的句柄 */
            __u32 policy;           /* 来宾的策略 */

            __u64 dh_uaddr;         /* 指向来宾所有者的 PDH 键的用户空间地址 */
            __u32 dh_len;

            __u64 session_addr;     /* 指向来宾会话信息的用户空间地址 */
            __u32 session_len;
    };
```

成功时，`handle` 字段包含一个新的句柄；在错误时，返回一个负数值。
`KVM_SEV_LAUNCH_START` 要求 `sev_fd` 字段有效。

更多详细信息，请参见 SEV 规范第 6.2 节。
3. KVM_SEV_LAUNCH_UPDATE_DATA
-----------------------------

KVM_SEV_LAUNCH_UPDATE_DATA 用于加密一个内存区域。它还会计算该内存内容的度量值。该度量值是内存内容的签名，可以发送给客户机所有者，作为证明内存已被固件正确加密的验证。
参数（输入）：struct kvm_sev_launch_update_data

返回值：成功时返回0，错误时返回负数

::

        struct kvm_sev_launch_update {
                __u64 uaddr;    /* 要加密的用户空间地址（必须是16字节对齐） */
                __u32 len;      /* 要加密的数据长度（必须是16字节对齐） */
        };

更多细节请参阅SEV规范第6.3节。
4. KVM_SEV_LAUNCH_MEASURE
-------------------------

KVM_SEV_LAUNCH_MEASURE 命令用于检索由 KVM_SEV_LAUNCH_UPDATE_DATA 命令加密的数据的度量值。客户机所有者可能会等到能够验证度量值后再向客户提供机密信息。由于客户机所有者知道启动时客户机的初始内容，因此可以通过将其与客户机所有者的预期进行比较来验证度量值。
如果在输入时 len 为零，则将度量值blob的长度写入 len，并且 uaddr 不被使用。
参数（输入）：struct kvm_sev_launch_measure

返回值：成功时返回0，错误时返回负数

::

        struct kvm_sev_launch_measure {
                __u64 uaddr;    /* 复制度量值的位置 */
                __u32 len;      /* 度量值blob的长度 */
        };

有关度量值验证流程的更多详细信息，请参阅SEV规范第6.4节。
5. KVM_SEV_LAUNCH_FINISH
------------------------

完成启动流程后，可以发出 KVM_SEV_LAUNCH_FINISH 命令使客户机准备好执行。
返回值：成功时返回0，错误时返回负数。

6. KVM_SEV_GUEST_STATUS
-----------------------

KVM_SEV_GUEST_STATUS 命令用于检索关于 SEV 启用客户机的状态信息。
参数（输出）：struct kvm_sev_guest_status

返回值：成功时返回0，错误时返回负数

::

        struct kvm_sev_guest_status {
                __u32 handle;   /* 客户机句柄 */
                __u32 policy;   /* 客户机策略 */
                __u8 state;     /* 客户机状态（见下面的枚举） */
        };

SEV 客户机状态：

::

        enum {
        SEV_STATE_INVALID = 0;
        SEV_STATE_LAUNCHING,    /* 客户机当前正在启动 */
        SEV_STATE_SECRET,       /* 客户机正在启动并且准备好接收密文数据 */
        SEV_STATE_RUNNING,      /* 客户机已完全启动并运行 */
        SEV_STATE_RECEIVING,    /* 客户机正从另一台SEV机器迁入 */
        SEV_STATE_SENDING       /* 客户机正迁出到另一台SEV机器 */
        };

7. KVM_SEV_DBG_DECRYPT
----------------------

KVM_SEV_DBG_DECRYPT 命令可用于由虚拟机监控程序请求固件解密指定内存区域的数据。
参数（输入）：struct kvm_sev_dbg

返回值：成功时返回0，错误时返回负数

::

        struct kvm_sev_dbg {
                __u64 src_uaddr;        /* 待解密数据的用户空间地址 */
                __u64 dst_uaddr;        /* 目的地的用户空间地址 */
                __u32 len;              /* 待解密的内存区域长度 */
        };

如果客户机策略不允许调试，则命令会返回错误。
8. KVM_SEV_DBG_ENCRYPT
----------------------

KVM_SEV_DBG_ENCRYPT 命令可用于由虚拟机监控程序请求固件加密指定内存区域的数据。
### 参数 (输入): struct kvm_sev_dbg

返回值：成功时返回 0，错误时返回负数

```c
struct kvm_sev_dbg {
    __u64 src_uaddr;       /* 需要加密的数据的用户空间地址 */
    __u64 dst_uaddr;       /* 目标用户空间地址 */
    __u32 len;             /* 要加密的内存区域长度 */
};
```

该命令在访客策略不允许调试时返回错误。

### 9. KVM_SEV_LAUNCH_SECRET

`KVM_SEV_LAUNCH_SECRET` 命令可用于由虚拟机监控程序在验证测量结果后注入秘密数据。

参数 (输入): struct kvm_sev_launch_secret

返回值：成功时返回 0，错误时返回负数

```c
struct kvm_sev_launch_secret {
    __u64 hdr_uaddr;       /* 包含数据包头的用户空间地址 */
    __u32 hdr_len;

    __u64 guest_uaddr;     /* 注入秘密的访客内存区域地址 */
    __u32 guest_len;

    __u64 trans_uaddr;     /* 包含秘密的虚拟机监控程序内存区域地址 */
    __u32 trans_len;
};
```

### 10. KVM_SEV_GET_ATTESTATION_REPORT

`KVM_SEV_GET_ATTESTATION_REPORT` 命令可用于由虚拟机监控程序查询包含访客内存和 VMSA 的 SHA-256 摘要并通过 `KVM_SEV_LAUNCH` 命令传递并用 PEK 签名的证明报告。该命令返回的摘要应与访客所有者使用 `KVM_SEV_LAUNCH_MEASURE` 时使用的摘要匹配。

如果 `len` 在输入时为零，则测量 Blob 的长度将被写入 `len`，且 `uaddr` 不使用。

参数 (输入): struct kvm_sev_attestation

返回值：成功时返回 0，错误时返回负数

```c
struct kvm_sev_attestation_report {
    __u8 mnonce[16];       /* 将放置在报告中的随机 mnonce */

    __u64 uaddr;           /* 报告应该被复制到的用户空间地址 */
    __u32 len;
};
```

### 11. KVM_SEV_SEND_START

`KVM_SEV_SEND_START` 命令可用于由虚拟机监控程序创建一个出站访客加密上下文。

如果 `session_len` 在输入时为零，则访客会话信息的长度将被写入 `session_len`，其他所有字段不使用。

参数 (输入): struct kvm_sev_send_start

返回值：成功时返回 0，错误时返回负数

```c
struct kvm_sev_send_start {
    __u32 policy;          /* 访客策略 */

    __u64 pdh_cert_uaddr;  /* 平台 Diffie-Hellman 证书 */
    __u32 pdh_cert_len;

    __u64 plat_certs_uaddr;/* 平台证书链 */
    __u32 plat_certs_len;

    __u64 amd_certs_uaddr; /* AMD 证书 */
    __u32 amd_certs_len;

    __u64 session_uaddr;   /* 访客会话信息 */
    __u32 session_len;
};
```

### 12. KVM_SEV_SEND_UPDATE_DATA

`KVM_SEV_SEND_UPDATE_DATA` 命令可用于由虚拟机监控程序使用通过 `KVM_SEV_SEND_START` 创建的加密上下文来加密出站访客内存区域。

如果 `hdr_len` 或 `trans_len` 在输入时为零，则数据包头和传输区域的长度将分别被写入 `hdr_len` 和 `trans_len`，其他所有字段不使用。

参数 (输入): struct kvm_sev_send_update_data

返回值：成功时返回 0，错误时返回负数

```c
struct kvm_sev_launch_send_update_data {
    __u64 hdr_uaddr;       /* 包含数据包头的用户空间地址 */
    __u32 hdr_len;

    __u64 guest_uaddr;     /* 需要加密的源内存区域地址 */
    __u32 guest_len;

    __u64 trans_uaddr;     /* 目标内存区域地址 */
    __u32 trans_len;
};
```

### 13. KVM_SEV_SEND_FINISH

迁移流程完成后，虚拟机监控程序可以发出 `KVM_SEV_SEND_FINISH` 命令以删除加密上下文。

返回值：成功时返回 0，错误时返回负数

### 14. KVM_SEV_SEND_CANCEL

在 `SEND_START` 完成之后但在 `SEND_FINISH` 之前，源 VMM 可以发出 `SEND_CANCEL` 命令以停止迁移。这是必要的，以便取消的迁移可以在稍后重新启动并指向新的目标。
返回值：成功时返回0，错误时返回负数。

15. KVM_SEV_RECEIVE_START
-------------------------
KVM_SEV_RECEIVE_START 命令用于为传入的 SEV 客户机创建内存加密上下文。为了创建加密上下文，用户必须提供客户机策略、平台公钥 Diffie-Hellman（PDH）密钥和会话信息。
参数：结构体 kvm_sev_receive_start（输入/输出）

返回值：成功时返回0，错误时返回负数。

```c
struct kvm_sev_receive_start {
        __u32 handle;           /* 如果为零，则固件将创建一个新的句柄 */
        __u32 policy;           /* 客户机的策略 */

        __u64 pdh_uaddr;        /* 指向 PDH 密钥的用户空间地址 */
        __u32 pdh_len;

        __u64 session_uaddr;    /* 指向客户机会话信息的用户空间地址 */
        __u32 session_len;
};
```

成功时，“handle”字段包含一个新句柄；错误时，返回负数。
更多详细信息，请参阅 SEV 规范第 6.12 节。

16. KVM_SEV_RECEIVE_UPDATE_DATA
-------------------------------
KVM_SEV_RECEIVE_UPDATE_DATA 命令可用于由虚拟机监控程序将传入的数据缓冲区复制到使用 KVM_SEV_RECEIVE_START 创建的加密上下文中的客户机内存区域。
参数（输入）：结构体 kvm_sev_receive_update_data

返回值：成功时返回0，错误时返回负数。

```c
struct kvm_sev_launch_receive_update_data {
        __u64 hdr_uaddr;        /* 包含数据包头的用户空间地址 */
        __u32 hdr_len;

        __u64 guest_uaddr;      /* 目标客户机内存区域 */
        __u32 guest_len;

        __u64 trans_uaddr;      /* 传入缓冲区的内存区域 */
        __u32 trans_len;
};
```

17. KVM_SEV_RECEIVE_FINISH
--------------------------
在迁移流程完成后，虚拟机监控程序可以发出 KVM_SEV_RECEIVE_FINISH 命令，使客户机准备好执行。
返回值：成功时返回0，错误时返回负数。

设备属性 API
============
SEV 实现的属性可以通过在 `/dev/kvm` 设备节点上使用 `KVM_HAS_DEVICE_ATTR` 和 `KVM_GET_DEVICE_ATTR` ioctl 来获取，并且使用组 `KVM_X86_GRP_SEV`。
目前仅实现了一个属性：

* `KVM_X86_SEV_VMSA_FEATURES`：返回 `KVM_SEV_INIT2` 中 `vmsa_features` 可接受的所有位集合。

固件管理
==========
SEV 客户机密钥管理由一个称为 AMD 安全处理器（AMD-SP）的独立处理器处理。运行在 AMD-SP 内部的固件提供了安全的密钥管理接口来执行常见的虚拟机监控程序活动，例如加密引导代码、快照、迁移和调试客户机。更多信息请参阅 SEV 密钥管理规范 [api-spec]_。

AMD-SP 固件可以通过使用其自身的非易失性存储器进行初始化，或者操作系统可以使用 `ccp` 模块的 `init_ex_path` 参数来管理固件的非易失性存储器。如果由 `init_ex_path` 指定的文件不存在或无效，操作系统将创建或覆盖该文件，使用 PSP 非易失性存储器。

参考文献
==========
更多详细信息，请参阅以下文档：
- [white-paper]_ https://developer.amd.com/wordpress/media/2013/12/AMD_Memory_Encryption_Whitepaper_v7-Public.pdf
- [api-spec]_ https://support.amd.com/TechDocs/55766_SEV-KM_API_Specification.pdf
- [amd-apm]_ https://support.amd.com/TechDocs/24593.pdf （第 15.34 节）
- [kvm-forum]_ https://www.linux-kvm.org/images/7/74/02x08A-Thomas_Lendacky-AMDs_Virtualizatoin_Memory_Encryption_Technology.pdf
