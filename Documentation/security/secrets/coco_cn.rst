SPDX 许可证标识符: GPL-2.0

==============================
机密计算中的秘密
==============================

本文档描述了从固件到操作系统，在EFI驱动程序和efi_secret内核模块中如何处理机密计算的秘密注入。
介绍
============

机密计算（如AMD SEV，即安全加密虚拟化）硬件允许客户机所有者将秘密注入到虚拟机内存中，并且主机/管理程序无法读取这些秘密。在SEV中，秘密注入是在虚拟机启动过程的早期进行的，在客户机开始运行之前。

efi_secret内核模块允许用户空间应用程序通过securityfs访问这些秘密。
秘密数据流
================

客户机固件可以为秘密注入预留一个指定的内存区域，并在EFI配置表中的``LINUX_EFI_COCO_SECRET_AREA_GUID``条目下（``adf956ad-e98c-484c-ae11-b51c7d336447``）发布其位置（基址GPA和长度）。此内存区域应由固件标记为``EFI_RESERVED_TYPE``，因此内核不应将其用于自身目的。

在虚拟机启动过程中，虚拟机管理器可能会向该区域注入秘密。在AMD SEV和SEV-ES中，这是通过使用``KVM_SEV_LAUNCH_SECRET``命令完成的（参见[sev]_）。注入的客户机所有者秘密数据结构应该是一个由GUID引导的秘密值表；二进制格式在``drivers/virt/coco/efi_secret/efi_secret.c``文件中的“EFI秘密区域结构”部分进行了描述。

在内核启动时，内核的EFI驱动程序会保存秘密区域的位置（从EFI配置表中获取），并存储在``efi.coco_secret``字段中。之后，它会检查秘密区域是否已填充：映射该区域并检查其内容是否以``EFI_SECRET_TABLE_HEADER_GUID``（``1e74f542-71dd-4d66-963e-ef4287ff173b``）开头。如果秘密区域已填充，EFI驱动程序将自动加载efi_secret内核模块，该模块通过securityfs将秘密暴露给用户空间应用程序。efi_secret文件系统接口的详细信息见[secrets-coco-abi]_。
应用示例
=========================

考虑一个对加密文件进行计算的客户机。客户机所有者使用秘密注入机制提供解密密钥（= 秘密）。

客户机应用程序从efi_secret文件系统读取秘密，然后将文件解密到内存中，并对内容执行所需的计算。

在这个例子中，主机无法从磁盘映像中读取文件，因为它们是加密的。主机也无法读取解密密钥，因为它通过秘密注入机制（= 安全通道）传递。
主机无法从内存中读取解密内容，因为这是机密（内存加密）的客户机。

以下是一个简单的示例，演示了在启动时注入包含4个秘密的EFI密钥区后，在客户机中使用efi_secret模块的方法：

    # ls -la /sys/kernel/security/secrets/coco
    total 0
    drwxr-xr-x 2 root root 0 Jun 28 11:54
    drwxr-xr-x 3 root root 0 Jun 28 11:54 .
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
    drwxr-xr-x 2 root root 0 Jun 28 11:55
    drwxr-xr-x 3 root root 0 Jun 28 11:54 .
    -r--r----- 1 root root 0 Jun 28 11:54 736870e5-84f0-4973-92ec-06879ce3da0b
    -r--r----- 1 root root 0 Jun 28 11:54 83c83f7f-1356-4975-8b7e-d3a0b54312c6
    -r--r----- 1 root root 0 Jun 28 11:54 9553f55d-3da2-43ee-ab5d-ff17f78864d2

参考文献
=========

更多关于SEV ``LAUNCH_SECRET`` 操作的信息，请参见 [sev-api-spec]_。
.. [sev] 文档/virt/kvm/x86/amd-memory-encryption.rst
.. [secrets-coco-abi] 文档/ABI/testing/securityfs-secrets-coco
.. [sev-api-spec] https://www.amd.com/system/files/TechDocs/55766_SEV-KM_API_Specification.pdf
