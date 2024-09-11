SPDX 许可证标识符: GPL-2.0

==============================
机密计算的秘密
==============================

本文档描述了从固件到操作系统的机密计算秘密注入处理过程，涉及 EFI 驱动程序和 efi_secret 内核模块。
介绍
============

机密计算（coco）硬件如 AMD SEV（安全加密虚拟化）允许客户机所有者将秘密注入到虚拟机（VM）内存中，而主机/管理程序无法读取这些秘密。在 SEV 中，秘密注入是在虚拟机启动过程中早期执行的，在客户机开始运行之前。

efi_secret 内核模块允许用户空间应用程序通过 securityfs 访问这些秘密。
秘密数据流
================

客户机固件可以预留一个指定的内存区域用于秘密注入，并在 EFI 配置表中的 `LINUX_EFI_COCO_SECRET_AREA_GUID` （`adf956ad-e98c-484c-ae11-b51c7d336447`）条目下发布其位置（基址 GPA 和长度）。该内存区域应由固件标记为 `EFI_RESERVED_TYPE`，因此内核不应将其用于自身目的。

在虚拟机启动期间，虚拟机管理器可能会向该区域注入一个秘密。在 AMD SEV 和 SEV-ES 中，这是通过 `KVM_SEV_LAUNCH_SECRET` 命令完成的（见 [sev]_）。注入的客户机所有者秘密数据结构应该是一个由 GUID 引导的秘密值表；二进制格式在 `drivers/virt/coco/efi_secret/efi_secret.c` 的“EFI 秘密区域结构”部分中有描述。

在内核启动时，内核的 EFI 驱动程序会保存秘密区域的位置（取自 EFI 配置表）到 `efi.coco_secret` 字段中。之后它检查秘密区域是否已填充：映射该区域并检查其内容是否以 `EFI_SECRET_TABLE_HEADER_GUID` （`1e74f542-71dd-4d66-963e-ef4287ff173b`）开头。如果秘密区域已填充，则 EFI 驱动程序会自动加载 efi_secret 内核模块，该模块通过 securityfs 将秘密暴露给用户空间应用程序。efi_secret 文件系统接口的详细信息见 [secrets-coco-abi]_。
应用程序使用示例
=========================

考虑一个对加密文件进行计算的客户机。客户机所有者使用秘密注入机制提供解密密钥（= 秘密）。

客户机应用程序从 efi_secret 文件系统读取秘密，然后将文件解密到内存中，并对内容进行所需的计算。

在这个例子中，主机无法从磁盘镜像中读取文件，因为它们是加密的。主机也无法读取解密密钥，因为它通过秘密注入机制（= 安全通道）传递。
主机无法从内存中读取解密内容，因为这是一个机密（内存加密）的客户机。

以下是一个简单的示例，展示了如何在客户机中使用efi_secret模块。该客户机在启动时注入了一个包含4个秘密的EFI秘密区域：

	# ls -la /sys/kernel/security/secrets/coco
	total 0
	drwxr-xr-x 2 root root 0 Jun 28 11:54 .
	drwxr-xr-x 3 root root 0 Jun 28 11:54 ..
	-r--r----- 1 root root 0 Jun 28 11:54 736870e5-84f0-4973-92ec-06879ce3da0b
	-r--r----- 1 root root 0 Jun 28 11:54 83c83f7f-1356-4975-8b7e-d3a0b54312c6
	-r--r----- 1 root root 0 Jun 28 11:54 9553f55d-3da2-43ee-ab5d-ff17f78864d2
	-r--r----- 1 root root 0 Jun 28 11:54 e6f5a162-d67f-4750-a67c-5d065f2a9910

	# hd /sys/kernel/security/secrets/coco/e6f5a162-d67f-4750-a67c-5d065f2a9910
	00000000  74 68 65 73 65 2d 61 72  65 2d 74 68 65 2d 6b 61  |these-are-the-ka|
	00000010  74 61 2d 73 65 63 72 65  74 73 00 01 02 03 04 05  |ta-secrets......|
	00000020  06 07                                             |..|
	00000022

	# rm /sys/kernel/security/secrets/coco/e6f5a162-d67f-4750-a67c-5d065f2a9910

	# ls -la /sys/kernel/security/secrets/coco
	total 0
	drwxr-xr-x 2 root root 0 Jun 28 11:55 .
	drwxr-xr-x 3 root root 0 Jun 28 11:54 ..
	-r--r----- 1 root root 0 Jun 28 11:54 736870e5-84f0-4973-92ec-06879ce3da0b
	-r--r----- 1 root root 0 Jun 28 11:54 83c83f7f-1356-4975-8b7e-d3a0b54312c6
	-r--r----- 1 root root 0 Jun 28 11:54 9553f55d-3da2-43ee-ab5d-ff17f78864d2

参考文献
=========

更多关于SEV `LAUNCH_SECRET` 操作的信息，请参阅[sev-api-spec]_。
.. [sev] 文档/virt/kvm/x86/amd-memory-encryption.rst
.. [secrets-coco-abi] 文档/ABI/testing/securityfs-secrets-coco
.. [sev-api-spec] https://www.amd.com/system/files/TechDocs/55766_SEV-KM_API_Specification.pdf
