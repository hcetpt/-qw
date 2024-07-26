最小编译内核的要求
++++++++++++++++++++++++++++++++++++++++++

简介
====

本文档旨在提供运行当前内核版本所需的最低软件级别的列表。
此文档最初基于我为2.0.x内核的“更改”文件，因此同样要感谢该文件中提到的人们（Jared Mauch、Axel Boldt、Alessandro Sigala以及互联网上的无数其他用户）。
当前最小要求
******************************

在认为遇到bug之前，请至少升级到这些软件版本！如果你不确定当前正在运行哪个版本，建议的命令应该能告诉你。
再次提醒，这个列表假设你已经能够正常运行Linux内核。此外，并非所有工具对所有系统都是必需的；显然，如果你没有任何PC卡硬件，那么可能无需关心pcmciautils。
====================== ===============  ========================================
        程序        最小版本       检查版本的命令
====================== ===============  ========================================
GNU C                  5.1              gcc --version
Clang/LLVM（可选）  13.0.1           clang --version
Rust（可选）        1.78.0           rustc --version
bindgen（可选）     0.65.1           bindgen --version
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
grub                   0.93             grub --version 或者 grub-install --version
mcelog                 0.6              mcelog --version
iptables               1.4.2            iptables -V
openssl & libcrypto    1.0.0            openssl version
bc                     1.06.95          bc --version
Sphinx\ [#f1]_         2.4.4            sphinx-build --version
cpio                   任何版本         cpio --version
GNU tar                1.28             tar --version
gtags（可选）         6.6.5            gtags --version
mkimage（可选）     2017.01          mkimage --version
Python（可选）      3.5.x            python3 --version
====================== ===============  ========================================

.. [#f1] Sphinx仅用于构建内核文档

内核编译
**********

GCC
---

gcc版本要求可能根据你的计算机中的CPU类型而变化。

Clang/LLVM（可选）
---------------------

最新正式发布的clang和LLVM工具（根据`releases.llvm.org <https://releases.llvm.org>`_）支持构建内核。旧版本不一定能工作，并且我们可能会从内核中移除为了支持旧版本而存在的变通方法。请参阅关于:ref:`使用Clang/LLVM构建Linux<kbuild_llvm>`的附加文档。

Rust（可选）
-------------

需要特定版本的Rust工具链。新版本可能或不可能工作，因为内核依赖于一些不稳定的Rust特性。
每个Rust工具链都包含几个“组件”，其中一些是必需的（如``rustc``），而另一些则是可选的。``rust-src``组件（它是可选的）需要被安装来构建内核。其他组件对于开发很有用。
请参阅Documentation/rust/quick-start.rst以获取满足Rust支持构建要求的说明。特别是，“Makefile”目标``rustavailable``可用于检查为何Rust工具链可能未被检测到。

bindgen（可选）
------------------

``bindgen``用于生成内核C侧的Rust绑定。
依赖于 `libclang`
构建
----

你需要 GNU make 3.82 或更高版本来构建内核。
Bash
----

一些 Bash 脚本用于内核的构建，需要 Bash 4.2 或更新版本。
Binutils
--------

构建内核需要 Binutils 2.25 或更新版本。
pkg-config
----------

自 4.18 版本起，构建系统需要使用 pkg-config 来检查已安装的 kconfig 工具，并确定在 `make {g,x}config` 中使用的标志设置。之前虽然有使用 pkg-config，但没有进行验证或记录说明。
Flex
----

从 Linux 4.16 开始，构建系统在构建过程中生成词法分析器。这需要 flex 2.5.35 或更高版本。
Bison
-----

从 Linux 4.16 开始，构建系统在构建过程中生成解析器。这需要 bison 2.0 或更高版本。
pahole
------

从 Linux 5.2 开始，如果选择了 CONFIG_DEBUG_INFO_BTF，则构建系统会从 vmlinux 中的 DWARF 生成 BTF（BPF 类型格式），稍后也会从内核模块中生成。这需要 pahole v1.16 或更高版本。
它可以在 'dwarves' 或 'pahole' 发行包中找到，或者从 https://fedorapeople.org/~acme/dwarves/ 获取。
Perl
----

你需要 Perl 5 以及以下模块：`Getopt::Long`、`Getopt::Std`、`File::Basename` 和 `File::Find` 来构建内核。

BC
--

你需要 bc 来构建 3.10 及以上版本的内核。

OpenSSL
-------

模块签名和外部证书处理使用 OpenSSL 程序和加密库来进行密钥创建和签名生成。如果你启用了模块签名，那么你需要 OpenSSL 来构建 3.7 及以上版本的内核。你也需要 OpenSSL 的开发包来构建 4.3 及以上版本的内核。

Tar
---

如果你希望启用通过 sysfs 访问内核头文件（CONFIG_IKHEADERS），则需要 GNU tar。

gtags / GNU GLOBAL（可选）
------------------------------

内核构建要求使用 GNU GLOBAL 6.6.5 或更高版本来通过 `make gtags` 命令生成标签文件。这是由于它使用了 gtags 的 `-C (--directory)` 标志。

mkimage
-------

此工具在构建 Flat Image Tree (FIT) 时使用，FIT 在 ARM 平台上很常见。该工具可以通过 `u-boot-tools` 包获得或从 U-Boot 源代码中构建。详情请参阅 https://docs.u-boot.org/en/latest/build/tools.html#building-tools-for-linux 中的说明。

系统实用程序
**************

架构变更
---------------------

DevFS 已被 udev 替代（更多信息请参考 https://www.kernel.org/pub/linux/utils/kernel/hotplug/）。

已经实现了对 32 位 UID 的支持。尽情享受吧！

Linux 函数文档正在过渡到通过源代码中定义附近的特别格式化的注释进行内联文档描述。这些注释可以与 Documentation/ 目录中的 ReST 文件结合以生成丰富的文档，然后可以将其转换为 PostScript、HTML、LaTex、ePUB 和 PDF 文件。

为了将 ReST 格式的文档转换为你所选择的格式，你需要 Sphinx。

Util-linux
----------

新版本的 util-linux 提供了对更大磁盘的支持，支持新的挂载选项，能够识别更多受支持的分区类型等类似功能。

你可能想要升级。

Ksymoops
--------

如果发生了不可想象的事情，你的内核出现了崩溃，你可能需要 ksymoops 工具来解码它，但在大多数情况下，你不需要。
通常更倾向于使用 ``CONFIG_KALLSYMS`` 来构建内核，这样它能生成可读的转储文件，可以直接使用（这也会产生比ksymoops更好的输出）。如果由于某些原因你的内核没有使用 ``CONFIG_KALLSYMS`` 构建，并且你没有办法重新构建并使用该选项重现Oops错误，那么你仍然可以使用ksymoops来解码这个Oops错误。

### Mkinitrd

对 ``/lib/modules`` 文件树布局所做的更改也要求升级mkinitrd。

### E2fsprogs

最新版本的 ``e2fsprogs`` 修复了fsck和debugfs中的几个bug。显然，升级是个好主意。

### JFSutils

``jfsutils`` 包含了文件系统的工具。以下是一些可用的工具：

- ``fsck.jfs`` —— 初始化事务日志回放，并检查及修复JFS格式化的分区
- ``mkfs.jfs`` —— 创建JFS格式化的分区
- 此包中还包含其他文件系统工具

### Reiserfsprogs

reiserfsprogs包适用于reiserfs-3.6.x（Linux内核2.4.x）。这是一个组合包，包含了 ``mkreiserfs``、``resize_reiserfs``、``debugreiserfs`` 和 ``reiserfsck`` 的工作版本。这些工具在i386和alpha平台上都能运行。

### Xfsprogs

最新版本的 ``xfsprogs`` 包含了 ``mkfs.xfs``、``xfs_db`` 和 ``xfs_repair`` 等XFS文件系统的工具。它是架构独立的，任何2.0.0或之后的版本都应该能够正确地与这个版本的XFS内核代码一起工作（推荐使用2.6.0或更高版本，因为有一些重要的改进）。

### PCMCIAutils

PCMCIAutils取代了 ``pcmcia-cs``。它能够在系统启动时正确设置PCMCIA插槽，并加载用于16位PCMCIA设备的适当模块（如果内核是模块化的并且使用了hotplug子系统）。
### 配额工具
-----------

如果想要使用较新的版本 2 的配额格式，那么需要支持 32 位的用户 ID（uid）和组 ID（gid）。从版本 3.07 开始及之后的配额工具（quota-tools）都提供了这种支持。请使用上表中推荐的版本或更新的版本。

### Intel IA32 微码
--------------------

已经添加了一个驱动程序以允许更新 Intel IA32 微码，该微码作为一个常规的（杂项）字符设备访问。如果你没有使用 udev，可能需要执行以下操作：

  ```sh
  mkdir /dev/cpu
  mknod /dev/cpu/microcode c 10 184
  chmod 0644 /dev/cpu/microcode
  ```

以 root 身份执行这些命令后才能使用此功能。你可能还需要获取用户空间的 microcode_ctl 工具与之配合使用。

### udev
----

`udev` 是一个用于动态填充 `/dev` 目录的应用程序，仅包含实际存在的设备条目。`udev` 替代了 devfs 的基本功能，并且为设备提供了持久的命名机制。

### FUSE
----

需要 libfuse 2.4.0 或更高版本。最低版本是 2.3.0，但是 `direct_io` 和 `kernel_cache` 这两个挂载选项将无法工作。

### 网络
**********

#### 一般变化
---------------

如果你有高级网络配置需求，建议考虑使用 ip-route2 中的网络工具。

#### 包过滤 / 网络地址转换 (NAT)
-------------------
包过滤和 NAT 代码使用的是与之前的 2.4.x 内核系列相同的工具（iptables）。它仍然包含了与 2.2.x 版本的 ipchains 和 2.0.x 版本的 ipfwadm 向后兼容的模块。

#### PPP
---

PPP 驱动程序已重构以支持多链路，并使其可以在不同的媒体层上运行。如果你使用 PPP，请将 pppd 升级到至少 2.4.0 版本。
如果你没有使用 udev，必须创建设备文件 `/dev/ppp`，可以通过以下命令完成：

  ```sh
  mknod /dev/ppp c 108 0
  ```

以 root 身份执行这个命令。

### NFS-utils
---------

在古老的（2.4 及更早版本）内核中，NFS 服务器需要了解任何希望通过 NFS 访问文件的客户端信息。这些信息会由 `mountd` 在客户端挂载文件系统时或者由 `exportfs` 在系统启动时提供给内核。`exportfs` 会从 `/var/lib/nfs/rmtab` 文件中获取活动客户端的信息。
这种方法非常脆弱，因为它依赖于 rmtab 的准确性，而这并不总是容易实现的，特别是在尝试实现故障转移时。即使系统正常工作时，`rmtab` 也会积累许多旧的条目，而这些条目永远不会被移除。
使用现代内核，我们有了一个选项，即让内核在接收到未知主机的请求时通知mountd，并且mountd可以向内核提供适当的导出信息。这消除了对"rmtab"的依赖，并意味着内核只需要了解当前活跃的客户端。

为了启用这种新功能，您需要在运行exportfs或mountd之前执行以下操作：

```shell
mount -t nfsd nfsd /proc/fs/nfsd
```

建议所有NFS服务通过防火墙受到保护，以防止来自整个互联网的访问，如果可能的话。

mcelog
------

在x86内核中，当启用了`CONFIG_X86_MCE`时，需要mcelog工具来处理和记录机器检查事件。机器检查事件是由CPU报告的错误。强烈建议处理这些事件。

内核文档
*********

Sphinx
------

有关Sphinx的要求详情，请参阅：`Documentation/doc-guide/sphinx.rst <sphinxdoc>`中的`sphinx_install`部分。

rustdoc
-------

`rustdoc`用于生成Rust代码的文档。更多信息请参阅`Documentation/rust/general-information.rst`。

获取更新的软件
==============

内核编译
**********

gcc
---

- <ftp://ftp.gnu.org/gnu/gcc/>

Clang/LLVM
----------

- [获取LLVM](getting_llvm)

Rust
----

- `Documentation/rust/quick-start.rst`

bindgen
-------

- `Documentation/rust/quick-start.rst`

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
------------

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
*****

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
