SPDX 许可标识符: GPL-2.0

=====================================
关于 [U]EFI x86_64 支持的通用说明
=====================================

在本文档中，EFI 和 UEFI 这两个术语可以互换使用。
尽管下面列出的工具并不是构建内核所必需的，
但对于具有 EFI 固件和规范的 x86_64 平台所需的引导加载程序支持及相关工具，我们列于下方：
1. UEFI 规范：http://www.uefi.org

2. 在 UEFI x86_64 平台上启动 Linux 内核需要引导加载程序的支持。可以使用带有 x86_64 支持的 Elilo。
3. 带有 EFI/UEFI 固件的 x86_64 平台
机制
--------

- 使用以下配置构建内核：

	CONFIG_FB_EFI=y
	CONFIG_FRAMEBUFFER_CONSOLE=y

  如果需要 EFI 运行时服务，则应选择以下配置：

	CONFIG_EFI=y
	CONFIG_EFIVAR_FS=y 或 m			# 可选

- 在磁盘上创建一个 VFAT 分区
- 将以下内容复制到 VFAT 分区：

	带有 x86_64 支持的 Elilo 引导加载程序、Elilo 配置文件、第一步中构建的内核映像及其相应的 initrd。有关构建 Elilo 及其依赖项的说明，请参阅 Elilo 的 SourceForge 项目。
- 启动到 EFI Shell 并通过选择第一步中构建的内核映像来调用 Elilo。
- 如果某些或全部的 EFI 运行时服务无法正常工作，你可以尝试以下内核命令行参数来禁用某些或全部的 EFI 运行时服务：
noefi
		禁用所有 EFI 运行时服务
	reboot_type=k
		禁用 EFI 重启运行时服务

- 如果 EFI 内存图中包含不在 E820 地图中的额外条目，
  你可以使用以下内核命令行参数将这些条目包括在内核可用物理 RAM 的内存图中：
add_efi_memmap
		包括 EFI 可用物理 RAM 的内存图
