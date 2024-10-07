.. _changes:

编译内核的最低要求
++++++++++++++++++++++++++++++++++++++++++

简介
=====

本文档旨在提供运行当前内核版本所需的最低软件级别的列表。本文档最初基于我为2.0.x内核编写的“Changes”文件，因此需要感谢与该文件相关的所有人（Jared Mauch、Axel Boldt、Alessandro Sigala以及无数其他用户）。
当前最低要求
******************************

在认为遇到bug之前，请至少升级到以下软件版本！如果你不确定当前正在运行的版本是什么，建议使用的命令应该可以告诉你。再次提醒，这个列表假设你已经在功能上运行了一个Linux内核。另外，并非所有工具在所有系统上都是必需的；显然，如果你没有任何PC卡硬件，那么你可能不需要关心pcmciautils。

====================== ===============  ========================================
        程序        最低版本       检查版本的命令
====================== ===============  ========================================
GNU C                  5.1              gcc --version
Clang/LLVM（可选）     13.0.1           clang --version
Rust（可选）           1.78.0           rustc --version
bindgen（可选）        0.65.1           bindgen --version
GNU make               3.82             make --version
bash                   4.2              bash --version
binutils               2.25             ld -v
flex                   2.5.35           flex --version
bison                  2.0              bison --version
pahole                 1.16             pahole --version
util-linux             2.10o            mount --version
kmod                   13               depmod -V
e2fsprogs              1.41.4           e2fsck -V
jfsutils               1.1.3            fsck.jfs -V
reiserfsprogs          3.6.3            reiserfsck -V
xfsprogs               2.6.0            xfs_db -V
squashfs-tools         4.0              mksquashfs -version
btrfs-progs            0.18             btrfsck
pcmciautils            004              pccardctl -V
quota-tools            3.09             quota -V
PPP                    2.4.0            pppd --version
nfs-utils              1.0.5            showmount --version
procps                 3.2.0            ps --version
udev                   081              udevd --version
grub                   0.93             grub --version || grub-install --version
mcelog                 0.6              mcelog --version
iptables               1.4.2            iptables -V
openssl & libcrypto    1.0.0            openssl version
bc                     1.06.95          bc --version
Sphinx\ [#f1]_         2.4.4            sphinx-build --version
cpio                   任何版本          cpio --version
GNU tar                1.28             tar --version
gtags（可选）          6.6.5            gtags --version
mkimage（可选）        2017.01          mkimage --version
Python（可选）         3.5.x            python3 --version
====================== ===============  ========================================

.. [#f1] Sphinx仅用于构建内核文档

内核编译
**********

GCC
---

GCC版本要求可能会根据你的计算机中CPU的类型而有所不同。

Clang/LLVM（可选）
---------------------

最新正式发布的Clang和LLVM工具（根据`releases.llvm.org <https://releases.llvm.org>`_）支持构建内核。旧版本不一定能工作，我们可能会从内核中移除用于支持旧版本的变通方法。请参阅关于使用Clang/LLVM构建Linux的更多文档：:ref:`Building Linux with Clang/LLVM <kbuild_llvm>`。

Rust（可选）
-------------

需要特定版本的Rust工具链。新版本可能或不可能工作，因为内核依赖于一些不稳定的Rust特性。每个Rust工具链包含多个“组件”，其中一些是必需的（如`rustc`），一些是可选的。`rust-src`组件（可选）需要安装以构建内核。其他组件对于开发有用。请参阅Documentation/rust/quick-start.rst以获取满足Rust支持构建要求的说明。特别是，`Makefile`目标`rustavailable`有助于检查为什么Rust工具链可能未被检测到。

bindgen（可选）
------------------

`bindgen`用于生成内核C侧的Rust绑定。
依赖于 `libclang`

Make
----
构建内核需要 GNU Make 3.82 或更高版本。

Bash
----
构建内核时会使用一些 Bash 脚本，需要 Bash 4.2 或更新版本。

Binutils
--------
构建内核需要 Binutils 2.25 或更高版本。

pkg-config
----------
从 4.18 版本开始，构建系统需要 pkg-config 来检查已安装的 kconfig 工具，并确定用于 `make {g,x}config` 的标志设置。此前虽然在使用 pkg-config，但并未进行验证或记录。

Flex
----
自 Linux 4.16 开始，构建系统在构建过程中生成词法分析器。这需要 Flex 2.5.35 或更高版本。

Bison
-----
自 Linux 4.16 开始，构建系统在构建过程中生成解析器。这需要 Bison 2.0 或更高版本。

pahole
------
自 Linux 5.2 开始，如果选择了 CONFIG_DEBUG_INFO_BTF，构建系统将从 vmlinux 中生成 BTF（BPF 类型格式），稍后也会从内核模块中生成。这需要 pahole v1.16 或更高版本。
可以在发行版包 `dwarves` 或 `pahole` 中找到，也可以从 https://fedorapeople.org/~acme/dwarves/ 获取。
Perl
----

您需要 Perl 5 及以下模块：``Getopt::Long``，``Getopt::Std``，``File::Basename`` 和 ``File::Find`` 来构建内核。

BC
--

您需要 bc 来构建 3.10 及以上版本的内核。

OpenSSL
-------

模块签名和外部证书处理使用 OpenSSL 程序和加密库来进行密钥创建和签名生成。如果您启用了模块签名，则需要 OpenSSL 来构建 3.7 及以上版本的内核。您还需要 OpenSSL 开发包来构建 4.3 及以上版本的内核。

Tar
---

如果您希望启用通过 sysfs 访问内核头文件（CONFIG_IKHEADERS），则需要 GNU tar。

gtags / GNU GLOBAL（可选）
-----------------------------

内核构建需要 GNU GLOBAL 6.6.5 或更高版本通过 ``make gtags`` 生成标签文件。这是由于其使用了 gtags 的 ``-C (--directory)`` 标志。

mkimage
-------

此工具用于构建 Flat Image Tree（FIT），常见于 ARM 平台。该工具可以通过 ``u-boot-tools`` 包获得，也可以从 U-Boot 源代码构建。详见 https://docs.u-boot.org/en/latest/build/tools.html#building-tools-for-linux

系统实用程序
*************

架构变更
---------------------

DevFS 已被 udev 替代（https://www.kernel.org/pub/linux/utils/kernel/hotplug/）

现在支持 32 位 UID。祝您使用愉快！

Linux 函数文档正在过渡到通过源码中定义附近的特别格式化注释来实现内联文档。这些注释可以与 Documentation/ 目录中的 ReST 文件结合以生成丰富文档，然后可以转换为 PostScript、HTML、LaTex、ePUB 和 PDF 文件。为了将 ReST 格式的文档转换为您所需格式，您需要 Sphinx。

Util-linux
----------

新版本的 util-linux 提供对更大磁盘的支持，支持挂载的新选项，识别更多支持的分区类型等类似功能。您可能需要升级。

Ksymoops
--------

如果内核出现不可预见的问题并且崩溃，您可能需要 ksymoops 工具来解码它，但在大多数情况下您不需要。
通常情况下，建议使用 ``CONFIG_KALLSYMS`` 构建内核，以便生成可读的转储文件，这些文件可以直接使用（这也比使用ksymoops生成的输出更好）。如果由于某些原因您的内核没有使用 ``CONFIG_KALLSYMS`` 构建，并且您无法重新构建并在使用该选项的情况下重现Oops错误，那么您仍然可以使用ksymoops解码这个Oops。

Mkinitrd
--------

对 ``/lib/modules`` 文件树布局所做的更改还要求升级mkinitrd。

E2fsprogs
---------

最新版本的 ``e2fsprogs`` 修复了fsck和debugfs中的几个bug。显然，升级是个好主意。

JFSutils
--------

``jfsutils`` 包含了文件系统的相关工具。以下是一些可用的工具：

- ``fsck.jfs`` - 启动事务日志回放，并检查和修复JFS格式化的分区
- ``mkfs.jfs`` - 创建JFS格式化的分区
- 此包中还包含其他文件系统工具

Reiserfsprogs
-------------

reiserfsprogs包应用于reiserfs-3.6.x（Linux内核2.4.x）。这是一个组合包，包含了 ``mkreiserfs``、``resize_reiserfs``、``debugreiserfs`` 和 ``reiserfsck`` 的工作版本。这些工具在i386和alpha平台上均能运行。

Xfsprogs
--------

最新版本的 ``xfsprogs`` 包含了 ``mkfs.xfs``、``xfs_db`` 和 ``xfs_repair`` 等工具，适用于XFS文件系统。它是架构无关的，从2.0.0及以后的任何版本都应与这个版本的XFS内核代码（建议使用2.6.0或更高版本，因为有一些显著改进）兼容。

PCMCIAutils
-----------

PCMCIAutils替换了 ``pcmcia-cs``。它在系统启动时正确设置PCMCIA插槽，并在内核模块化且使用热插拔子系统的情况下加载16位PCMCIA设备所需的模块。
### 配额工具
-------------

如果您希望使用较新的版本 2 配额格式，则需要支持 32 位的 uid 和 gid。配额工具版本 3.07 及以上版本具有此支持。请使用上表中推荐的版本或更新的版本。

### Intel IA32 微码
--------------------

已添加一个驱动程序以允许更新 Intel IA32 微码，作为常规（杂项）字符设备访问。如果您没有使用 udev，则可能需要执行以下操作：

```shell
mkdir /dev/cpu
mknod /dev/cpu/microcode c 10 184
chmod 0644 /dev/cpu/microcode
```

作为 root 用户执行上述命令后才能使用此功能。您可能还需要获取用户空间中的 microcode_ctl 工具来配合使用。

### udev
----

`udev` 是一个用于动态填充 `/dev` 目录的应用程序，仅包含实际存在的设备条目。`udev` 替代了 devfs 的基本功能，并允许为设备提供持久命名。

### FUSE
----

需要 libfuse 2.4.0 或更高版本。最低版本为 2.3.0，但 `direct_io` 和 `kernel_cache` 挂载选项将无法工作。

### 网络
**********

#### 通用更改
---------------

如果您有高级网络配置需求，建议考虑使用 ip-route2 中的网络工具。

#### 包过滤 / NAT
-------------------
包过滤和 NAT 代码使用与之前的 2.4.x 内核系列相同的工具（iptables）。它仍然包含向后兼容模块，支持 2.2.x 风格的 ipchains 和 2.0.x 风格的 ipfwadm。

#### PPP
---

PPP 驱动已经重构以支持多链路，并能够在多种媒体层上运行。如果您使用 PPP，请将 pppd 升级到至少 2.4.0 版本。

如果您没有使用 udev，必须创建设备文件 `/dev/ppp`，可以通过以下命令创建：

```shell
mknod /dev/ppp c 108 0
```

作为 root 用户执行上述命令。

### NFS-utils
---------

在古老的（2.4 及更早版本）内核中，NFS 服务器需要知道任何希望通过 NFS 访问文件的客户端信息。这些信息会在客户端挂载文件系统时由 `mountd` 提供给内核，或者在系统启动时通过 `exportfs` 提供。`exportfs` 会从 `/var/lib/nfs/rmtab` 获取活动客户端的信息。

这种方法相当脆弱，因为它依赖于 `rmtab` 的正确性，这并不总是容易实现，特别是在尝试实现故障转移时。即使系统正常工作，`rmtab` 也会出现很多旧条目而无法删除。
使用现代内核时，我们有一个选项，即当内核从一个未知主机接收到请求时，可以让内核通知mountd，然后mountd可以向内核提供适当的导出信息。这消除了对“rmtab”的依赖，并意味着内核只需要知道当前活跃的客户端。

要启用此新功能，您需要在运行exportfs或mountd之前执行以下命令：

  mount -t nfsd nfsd /proc/fs/nfsd

建议所有NFS服务都通过防火墙来防止来自互联网的大规模攻击，如果可能的话。

mcelog
------

在x86内核中，当启用了“CONFIG_X86_MCE”时，需要mcelog工具来处理和记录机器检查事件。机器检查事件是由CPU报告的错误。处理它们是强烈推荐的。

内核文档
*********

Sphinx
------

有关Sphinx要求的详细信息，请参阅：:ref:`sphinx_install` 在 :ref:`Documentation/doc-guide/sphinx.rst <sphinxdoc>` 中。

rustdoc
-------

`rustdoc`用于生成Rust代码的文档。请参阅Documentation/rust/general-information.rst获取更多信息。

获取更新软件
=============

内核编译
**********

gcc
---

- <ftp://ftp.gnu.org/gnu/gcc/>

Clang/LLVM
----------

- :ref:`获取LLVM <getting_llvm>`

Rust
----

- Documentation/rust/quick-start.rst

bindgen
-------

- Documentation/rust/quick-start.rst

Make
----

- <ftp://ftp.gnu.org/gnu/make/>

Bash
----

- <ftp://ftp.gnu.org/gnu/bash/>

Binutils
--------

- <https://www.kernel.org/pub/linux/devel/binutils/>

Flex
----

- <https://github.com/westes/flex/releases>

Bison
-----

- <ftp://ftp.gnu.org/gnu/bison/>

OpenSSL
-------

- <https://www.openssl.org/>

系统实用程序
*************

Util-linux
----------

- <https://www.kernel.org/pub/linux/utils/util-linux/>

Kmod
----

- <https://www.kernel.org/pub/linux/utils/kernel/kmod/>
- <https://git.kernel.org/pub/scm/utils/kernel/kmod/kmod.git>

Ksymoops
--------

- <https://www.kernel.org/pub/linux/utils/kernel/ksymoops/v2.4/>

Mkinitrd
--------

- <https://code.launchpad.net/initrd-tools/main>

E2fsprogs
---------

- <https://www.kernel.org/pub/linux/kernel/people/tytso/e2fsprogs/>
- <https://git.kernel.org/pub/scm/fs/ext2/e2fsprogs.git>

JFSutils
--------

- <https://jfs.sourceforge.net/>

Reiserfsprogs
-------------

- <https://git.kernel.org/pub/scm/linux/kernel/git/jeffm/reiserfsprogs.git>

Xfsprogs
--------

- <https://git.kernel.org/pub/scm/fs/xfs/xfsprogs-dev.git>
- <https://www.kernel.org/pub/linux/utils/fs/xfs/xfsprogs/>

Pcmciautils
-----------

- <https://www.kernel.org/pub/linux/utils/kernel/pcmcia/>

Quota-tools
-----------

- <https://sourceforge.net/projects/linuxquota/>

Intel P6 微码
--------------

- <https://downloadcenter.intel.com/>

udev
----

- <https://www.freedesktop.org/software/systemd/man/udev.html>

FUSE
----

- <https://github.com/libfuse/libfuse/releases>

mcelog
------

- <https://www.mcelog.org/>

cpio
----

- <https://www.gnu.org/software/cpio/>

网络
******

PPP
---

- <https://download.samba.org/pub/ppp/>
- <https://git.ozlabs.org/?p=ppp.git>
- <https://github.com/paulusmack/ppp/>

NFS-utils
---------

- <https://sourceforge.net/project/showfiles.php?group_id=14>
- <https://nfs.sourceforge.net/>

Iptables
--------

- <https://netfilter.org/projects/iptables/index.html>

Ip-route2
---------

- <https://www.kernel.org/pub/linux/utils/net/iproute2/>

OProfile
--------

- <https://oprofile.sf.net/download/>

内核文档
*********

Sphinx
------

- <https://www.sphinx-doc.org/>
