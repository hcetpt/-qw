=======================
早期用户空间支持
=======================

最后更新：2004-12-20 tlh

“早期用户空间”是一组库和程序，它们提供了在Linux内核启动过程中非常重要的各种功能，但这些功能不需要在内核内部运行。它主要包括以下几个关键组件：

- `gen_init_cpio`，一个用于构建包含根文件系统镜像的`cpio`格式归档文件的程序。这个归档文件会被压缩，并将压缩后的图像链接到内核映像中。
- `initramfs`，一段代码，在内核启动过程中中期解压压缩的`cpio`图像。
- `klibc`，一个用户空间的C库，目前单独打包，针对正确性和小尺寸进行了优化。

`initramfs`使用的`cpio`文件格式是“newc”（即“cpio -H newc”）格式，该格式在文件“buffer-format.txt”中有详细说明。有两种方式可以添加早期用户空间镜像：指定一个现有的`cpio`归档文件作为镜像或者让内核构建过程根据规范构建镜像。

**CPIO 归档方法**
-------------------

您可以创建一个包含早期用户空间镜像的`cpio`归档文件。您的`cpio`归档文件应该在`CONFIG_INITRAMFS_SOURCE`中指定，并且会直接使用。在`CONFIG_INITRAMFS_SOURCE`中只能指定一个`cpio`文件，并且不允许与目录和文件名组合使用。

**镜像构建方法**
---------------------

内核构建过程也可以从源组件构建早期用户空间镜像，而不是提供一个`cpio`归档文件。这种方法提供了一种即使由非特权用户构建镜像也能创建具有根所有者文件的镜像的方式。

镜像通过在`CONFIG_INITRAMFS_SOURCE`中指定一个或多个源来定义。源可以是目录或文件，但不包括`cpio`归档文件。

如果指定了一个源目录，则该目录及其所有内容都将被打包。指定的目录名称将映射到'/'。在打包目录时，可以进行有限的用户和组ID转换。
`INITRAMFS_ROOT_UID`可以设置为需要映射到用户root（0）的用户ID。`INITRAMFS_ROOT_GID`可以设置为需要映射到组root（0）的组ID。
源文件必须是按照`usr/gen_init_cpio`工具所需格式的指令（运行`usr/gen_init_cpio -h`来获取文件格式）。文件中的指令将直接传递给`usr/gen_init_cpio`。
当指定了目录和文件的组合时，`initramfs`镜像将是它们所有内容的集合。这样用户可以创建一个名为'root-image'的目录并将所有文件安装到其中。
由于非特权用户无法创建设备特殊文件，可以在名为'root-files'的文件中列出特殊文件。'root-image'和'root-files'都可以在`CONFIG_INITRAMFS_SOURCE`中列出，并且非特权用户可以通过这种方式构建完整的早期用户空间镜像。
从技术上讲，当指定目录和文件时，整个`CONFIG_INITRAMFS_SOURCE`被传递给`usr/gen_initramfs.sh`。这意味着`CONFIG_INITRAMFS_SOURCE`实际上可以解释为`gen_initramfs.sh`的任何合法参数。如果将目录作为参数指定，则会扫描其内容、执行uid/gid转换，并输出`usr/gen_init_cpio`文件指令。如果将文件作为参数指定给`usr/gen_initramfs.sh`，则文件的内容将简单地复制到输出中。从目录扫描和文件内容复制生成的所有输出指令由`usr/gen_init_cpio`处理。
另见`usr/gen_initramfs.sh -h`
这一切将导向何处？
==========================

klibc发行版包含了一些必要的软件以使早期用户空间变得有用。目前，klibc发行版独立于内核进行维护。
您可以从https://www.kernel.org/pub/linux/libs/klibc/ 获取klibc的较为不频繁的快照。

对于活跃用户来说，使用位于https://git.kernel.org/?p=libs/klibc/klibc.git 的klibc Git仓库更为合适。

独立的klibc发行版目前提供了以下三个组件，除了klibc库之外：

- `ipconfig`，一个配置网络接口的程序。它可以静态配置接口，或使用DHCP动态获取信息（即“IP自动配置”）
- `nfsmount`，一个可以挂载NFS文件系统的程序
- `kinit`，作为“粘合剂”，使用`ipconfig`和`nfsmount`来替代旧的IP自动配置支持，通过NFS挂载文件系统，并继续使用该文件系统作为根来启动系统
kinit 构建为单一的静态链接二进制文件以节省空间。最终，希望内核功能中的更多部分能够移至早期用户空间：

- 几乎所有的 `init/do_mounts*`（这部分已经开始实施）
- ACPI 表格解析
- 将那些不必在内核空间中运行的笨重子系统移到此处

如果 kinit 不符合您的当前需求，并且您有足够的存储空间，klibc 发行版包含了一个小型兼容 Bourne 的 shell（ash）以及许多其他工具，因此您可以替换 kinit 并构建完全满足您需求的自定义 initramfs 映像。
对于问题和帮助，您可以注册加入早期用户空间邮件列表：https://www.zytor.com/mailman/listinfo/klibc

它是如何工作的？
=================

目前内核有三种挂载根文件系统的方法：

a) 所需的所有设备和文件系统驱动程序都编译进了内核，不使用 initrd。`init/main.c:init()` 会调用 `prepare_namespace()` 来挂载最终的根文件系统，基于 `root=` 参数及可选的 `init=` 参数来运行 `init` 二进制文件，而不是在 `init/main.c:init()` 结尾处列出的默认 `init` 二进制文件。
b) 部分设备和文件系统驱动程序作为模块构建并存储在 initrd 中。initrd 必须包含一个名为 `/linuxrc` 的二进制文件，用于加载这些驱动模块。也可以通过 `linuxrc` 挂载最终的根文件系统并使用 `pivot_root` 系统调用。initrd 通过 `prepare_namespace()` 进行挂载和执行。
c) 使用 initramfs。必须跳过对 `prepare_namespace()` 的调用。这意味着一个二进制文件必须完成所有工作。该二进制文件可以通过修改 `usr/gen_init_cpio.c` 或者通过新的 initrd 格式（即 cpio 归档文件）放入 initramfs。它必须被命名为 `/init`。此二进制文件负责执行 `prepare_namespace()` 会做的所有事情。

为了保持向后兼容性，只有当 `/init` 二进制文件来自 initramfs cpio 归档时才会运行。如果不是这种情况，`init/main.c:init()` 会调用 `prepare_namespace()` 来挂载最终的根文件系统并执行预定义的 `init` 二进制文件之一。

— Bryan O'Sullivan <bos@serpentine.com>
