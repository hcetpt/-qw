=======================
 dGPU 固件刷新
=======================

IFWI
----
对于使用 PSP（Platform Security Processor，平台安全处理器）来协调更新的 GPU（如 Navi3x 或更新的 GPU），支持刷新 dGPU 集成固件图像（IFWI）。对于支持的 GPU，`amdgpu` 会导出一系列可用于刷新过程的 sysfs 文件。IFWI 刷新过程如下：

1. 确认 IFWI 图像适用于系统中的 dGPU。
2. 将 IFWI 图像“写入”到 sysfs 文件 `psp_vbflash`。这会在内存中准备 IFWI。
3. 从 `psp_vbflash` sysfs 文件进行“读取”，以启动刷新过程。
4. 检查 `psp_vbflash_status` sysfs 文件，确定刷新过程何时完成。

USB-C PD 固件
------------
对于支持刷新更新的 USB-C PD 固件图像的 GPU，刷新过程通过 `usbc_pd_fw` sysfs 文件完成。
- 读取该文件将提供当前固件版本。
- 将存储在 `/lib/firmware/amdgpu` 中的固件有效负载名称写入 sysfs 文件，以启动刷新过程。
- 存储在 `/lib/firmware/amdgpu` 中的固件有效负载可以命名为任何名称，只要不与其他由 `amdgpu` 使用的现有二进制文件冲突即可。
sysfs 文件
-----------
.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_psp.c

这段文字的意思是，关于“sysfs 文件”的内容引用自 `amdgpu_psp.c` 这个内核文件。
