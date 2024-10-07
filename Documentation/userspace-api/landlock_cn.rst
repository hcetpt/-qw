SPDX 许可证标识符: GPL-2.0  
版权所有 © 2017-2020 Mickaël Salaün <mic@digikod.net>  
版权所有 © 2019-2020 ANSSI  
版权所有 © 2021-2022 Microsoft Corporation

=====================================
Landlock：非特权访问控制
=====================================

作者: Mickaël Salaün  
日期: 2024年4月

Landlock 的目标是能够限制一组进程的环境权限（例如全局文件系统或网络访问）。由于 Landlock 是一个可堆叠的安全模块（LSM），它使得在现有的系统范围访问控制之外创建安全的沙箱成为可能。这种类型的沙箱预计有助于缓解用户空间应用程序中的漏洞或意外/恶意行为对安全的影响。Landlock 赋予任何进程，包括非特权进程，安全地限制自身的能力。

我们可以通过查看内核日志中的 "landlock: Up and running" 来快速确认运行中的系统已启用 Landlock（作为 root 用户）：
``dmesg | grep landlock || journalctl -kb -g landlock``
开发者也可以通过 :ref:`相关系统调用 <landlock_abi_versions>` 轻松检查 Landlock 支持情况。
如果当前不支持 Landlock，我们需要 :ref:`适当地配置内核 <kernel_support>`。

Landlock 规则
=============

一个 Landlock 规则描述了进程打算执行的对象上的操作。一组规则被聚合到一个规则集中，然后可以限制执行该规则集的线程及其未来的子进程。

目前存在的两种规则类型是：

文件系统规则
    对于这些规则，对象是一个文件层次结构，
    相关的文件系统操作由 `文件系统访问权限` 定义。
网络规则（自 ABI v4 开始）
    对于这些规则，对象是一个 TCP 端口，
    相关的操作由 `网络访问权限` 定义。

定义和强制执行安全策略
----------------------------------------

首先需要定义包含我们规则的规则集。
在这个示例中，规则集将包含仅允许文件系统读取操作并建立特定 TCP 连接的规则。文件系统写入操作和其他 TCP 操作将被禁止。
然后需要处理这两种类型的操作。这是为了向后和向前兼容性（即内核和用户空间可能不知道对方支持的限制），因此需要明确说明默认被拒绝的访问权限。
```c
// 定义一个landlock规则集属性结构体
struct landlock_ruleset_attr ruleset_attr = {
    .handled_access_fs =
        LANDLOCK_ACCESS_FS_EXECUTE |
        LANDLOCK_ACCESS_FS_WRITE_FILE |
        LANDLOCK_ACCESS_FS_READ_FILE |
        LANDLOCK_ACCESS_FS_READ_DIR |
        LANDLOCK_ACCESS_FS_REMOVE_DIR |
        LANDLOCK_ACCESS_FS_REMOVE_FILE |
        LANDLOCK_ACCESS_FS_MAKE_CHAR |
        LANDLOCK_ACCESS_FS_MAKE_DIR |
        LANDLOCK_ACCESS_FS_MAKE_REG |
        LANDLOCK_ACCESS_FS_MAKE_SOCK |
        LANDLOCK_ACCESS_FS_MAKE_FIFO |
        LANDLOCK_ACCESS_FS_MAKE_BLOCK |
        LANDLOCK_ACCESS_FS_MAKE_SYM |
        LANDLOCK_ACCESS_FS_REFER |
        LANDLOCK_ACCESS_FS_TRUNCATE |
        LANDLOCK_ACCESS_FS_IOCTL_DEV,
    .handled_access_net =
        LANDLOCK_ACCESS_NET_BIND_TCP |
        LANDLOCK_ACCESS_NET_CONNECT_TCP,
};
```

由于我们可能不知道应用程序将在哪个内核版本上运行，因此最好采取尽力而为的安全措施。实际上，无论用户使用的是哪个内核，我们都应尽量保护他们。
为了与旧版Linux兼容，我们检测可用的Landlock ABI版本，并仅使用可访问权限的子集：

```c
int abi;

abi = landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION);
if (abi < 0) {
    // 如果Landlock未被处理，则优雅地降级
    perror("当前内核不支持使用Landlock");
    return 0;
}
switch (abi) {
case 1:
    // 对于ABI < 2，移除LANDLOCK_ACCESS_FS_REFER
    ruleset_attr.handled_access_fs &= ~LANDLOCK_ACCESS_FS_REFER;
    __attribute__((fallthrough));
case 2:
    // 对于ABI < 3，移除LANDLOCK_ACCESS_FS_TRUNCATE
    ruleset_attr.handled_access_fs &= ~LANDLOCK_ACCESS_FS_TRUNCATE;
    __attribute__((fallthrough));
case 3:
    // 对于ABI < 4，移除网络支持
    ruleset_attr.handled_access_net &=
        ~(LANDLOCK_ACCESS_NET_BIND_TCP |
          LANDLOCK_ACCESS_NET_CONNECT_TCP);
    __attribute__((fallthrough));
case 4:
    // 对于ABI < 5，移除LANDLOCK_ACCESS_FS_IOCTL_DEV
    ruleset_attr.handled_access_fs &= ~LANDLOCK_ACCESS_FS_IOCTL_DEV;
}
```

这样可以创建一个包容性的规则集，包含我们的规则：
```c
int ruleset_fd;

ruleset_fd = landlock_create_ruleset(&ruleset_attr, sizeof(ruleset_attr), 0);
if (ruleset_fd < 0) {
    perror("创建规则集失败");
    return 1;
}
```

现在我们可以使用返回的文件描述符来添加新规则到这个规则集中。该规则将只允许读取文件层次结构 `/usr`。如果没有其他规则，写操作将会被规则集拒绝。要将`/usr`添加到规则集中，我们需要使用`O_PATH`标志打开它，并用此文件描述符填充`struct landlock_path_beneath_attr`：
```c
int err;
struct landlock_path_beneath_attr path_beneath = {
    .allowed_access =
        LANDLOCK_ACCESS_FS_EXECUTE |
        LANDLOCK_ACCESS_FS_READ_FILE |
        LANDLOCK_ACCESS_FS_READ_DIR,
};

path_beneath.parent_fd = open("/usr", O_PATH | O_CLOEXEC);
if (path_beneath.parent_fd < 0) {
    perror("打开文件失败");
    close(ruleset_fd);
    return 1;
}
err = landlock_add_rule(ruleset_fd, LANDLOCK_RULE_PATH_BENEATH,
                        &path_beneath, 0);
close(path_beneath.parent_fd);
if (err) {
    perror("更新规则集失败");
    close(ruleset_fd);
    return 1;
}
```

对于网络访问控制，我们可以添加一组规则以允许特定端口上的特定动作：HTTPS连接：
```c
struct landlock_net_port_attr net_port = {
    .allowed_access = LANDLOCK_ACCESS_NET_CONNECT_TCP,
    .port = 443,
};

err = landlock_add_rule(ruleset_fd, LANDLOCK_RULE_NET_PORT,
                        &net_port, 0);
```

接下来需要限制当前线程获取更多特权（例如通过SUID二进制文件）。现在我们有了一个规则集，其中第一个规则允许对`/usr`进行读取访问，同时拒绝所有其他已处理的文件系统访问，第二个规则则允许HTTPS连接：
```c
if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) {
    perror("限制特权失败");
    close(ruleset_fd);
    return 1;
}
```

当前线程现在已经准备好使用规则集进行沙箱化：
```c
if (landlock_restrict_self(ruleset_fd, 0)) {
    perror("执行规则集失败");
    close(ruleset_fd);
    return 1;
}
close(ruleset_fd);
```

如果`landlock_restrict_self`系统调用成功，当前线程现在受到限制，并且这一策略也将强制应用于其随后创建的所有子线程。一旦线程受到Landlock限制，就无法移除其安全策略；只能添加更多的限制。这些线程现在处于一个新的Landlock域中，合并了其父域（如果有）和新的规则集。

完整的代码可以在`samples/landlock/sandboxer.c`中找到。

### 最佳实践

建议尽可能多地设置文件层次结构叶子节点的访问权限。例如，最好能够将`~/doc/`设置为只读层次结构，将`~/tmp/`设置为读写层次结构，而不是将`~/`设置为只读层次结构，将`~/tmp/`设置为读写层次结构。
遵循这一良好实践会生成自给自足的层次结构，这些层次结构不依赖于它们的位置（即父目录）。这一点在我们希望允许链接或重命名时尤为重要。确实，每个目录具有一致的访问权限使得可以在不依赖目标目录访问权限的情况下更改该目录的位置（除了执行此操作所需的权限，请参阅“LANDLOCK_ACCESS_FS_REFER”文档）。
拥有自给自足的层次结构还有助于将所需的访问权限限制到最小的数据集。这也帮助避免了陷阱目录，即数据可以被链接进来但不能被链接出去的目录。然而，这取决于数据组织，而这可能不受开发人员控制。
在这种情况下，授予对`~/tmp/`的读写权限，而不是仅写入权限，可能会允许将`~/tmp/`移动到不可读取的目录中，但仍保持列出`~/tmp/`内容的能力。

文件路径访问权限层
-------------------

每当线程对自己实施规则集时，它都会用新的策略层更新其Landlock域。实际上，这种补充策略与可能已经限制该线程的其他规则集叠加在一起。这样，一个沙箱化的线程就可以安全地通过一个新的强制规则集为自己添加更多约束。
如果路径上的至少一个规则授予访问权限，则一个策略层就授予对该文件路径的访问权限。只有当所有强制策略层以及系统的其他访问控制（例如文件系统DAC、其他LSM策略等）都授予访问权限时，沙箱化线程才能访问文件路径。
绑定挂载和OverlayFS
-------------------

Landlock能够限制对文件层次结构的访问，这意味着这些访问权限可以通过绑定挂载传播（参见Documentation/filesystems/sharedsubtree.rst），但不能通过OverlayFS（参见Documentation/filesystems/overlayfs.rst）。
绑定挂载将源文件层次结构镜像到目的地。目的地层次结构由完全相同的文件组成，这些文件可以绑定Landlock规则，无论是通过源路径还是目的地路径。当这些规则在路径上出现时，它们会限制访问，这意味着它们可以同时限制多个文件层次结构的访问，无论这些层次结构是否是绑定挂载的结果。
一个OverlayFS挂载点包括上层和下层。这些层在一个合并目录中组合，形成挂载点的结果。这个合并层次结构可能包含来自上层和下层的文件，但在合并层次结构上所做的修改只反映在上层。从Landlock策略的角度来看，每个OverlayFS层及其合并层次结构都是独立的，并且包含自己的文件和目录集，这不同于绑定挂载。限制一个OverlayFS层的策略不会限制最终的合并层次结构，反之亦然。因此，Landlock用户只需要考虑他们想要允许访问的文件层次结构，而不管底层文件系统如何。

继承
------------

每个从`clone(2)`创建的新线程继承其父线程的Landlock域限制。这类似于seccomp的继承（参见
文档/userspace-api/seccomp_filter.rst) 或任何其他处理任务的 :manpage:`credentials(7)` 的 LSM。例如，一个进程的线程可以为自己应用 Landlock 规则，但这些规则不会自动应用于其他兄弟线程（与 POSIX 线程凭证更改不同，参见 :manpage:`nptl(7)`）。
当一个线程将自己沙箱化时，我们可以保证相关的安全策略将对该线程的所有后代持续强制执行。这允许为每个应用程序创建独立且模块化的安全策略，并且这些策略会根据其运行时父策略自动组合。

指针追踪限制
-------------

被沙箱化的进程比未沙箱化的进程拥有更少的权限，因此在操作另一个进程时必须受到额外的限制。
为了能够在目标进程上使用 :manpage:`ptrace(2)` 及相关系统调用，被沙箱化的进程应具有目标进程规则的一个子集，这意味着跟踪者必须位于被跟踪者的子域中。

截断文件
---------

由 ``LANDLOCK_ACCESS_FS_WRITE_FILE`` 和 ``LANDLOCK_ACCESS_FS_TRUNCATE`` 覆盖的操作都会改变文件的内容，并且有时以非直观的方式重叠。建议始终同时指定这两个权限。
一个特别令人惊讶的例子是 :manpage:`creat(2)`。该系统调用的名字暗示它需要创建和写入文件的权限。然而，如果同名的现有文件已经存在，则还需要截断权限。
还应注意的是，截断文件不需要 ``LANDLOCK_ACCESS_FS_WRITE_FILE`` 权限。除了 :manpage:`truncate(2)` 系统调用外，还可以通过带有标志 ``O_RDONLY | O_TRUNC`` 的 :manpage:`open(2)` 来实现截断。
截断权限与打开的文件关联（见下文）。

与文件描述符关联的权限
------------------------------

在打开文件时，``LANDLOCK_ACCESS_FS_TRUNCATE`` 和 ``LANDLOCK_ACCESS_FS_IOCTL_DEV`` 权限的有效性将与新创建的文件描述符相关联，并用于后续的 :manpage:`ftruncate(2)` 和 :manpage:`ioctl(2)` 尝试。这种行为类似于为读取或写入打开文件，在 :manpage:`open(2)` 期间检查权限，但在随后的 :manpage:`read(2)` 和 :manpage:`write(2)` 调用期间不再检查权限。
因此，一个进程可能有多个指向同一文件的打开文件描述符，但Landlock在操作这些文件描述符时会强制执行不同的规则。当Landlock规则集被强制执行且进程保留了强制执行前后打开的文件描述符时，这种情况就会发生。同样，可以在进程间传递这样的文件描述符，并保持其Landlock属性，即使某些涉及的进程没有强制执行的Landlock规则集。

兼容性
======

向后和向前兼容性
------------------

Landlock旨在与内核的过去和未来版本兼容。这是通过系统调用属性及其相关位标志（特别是规则集的`handled_access_fs`）实现的。明确指定处理访问权限使内核和用户空间能够彼此之间有一个清晰的契约。这确保了系统更新不会使沙箱变得更严格，从而导致应用程序中断。开发者可以订阅`Landlock邮件列表<https://subspace.kernel.org/lists.linux.dev.html>`_来有意地更新并测试他们的应用程序以获取最新的功能。为了用户的利益，因为他们可能会使用不同的内核版本，强烈建议采用尽力而为的安全方法，在运行时检查Landlock ABI版本，并仅强制执行支持的功能。

Landlock ABI版本
------------------

可以通过sys_landlock_create_ruleset()系统调用来读取Landlock ABI版本：

```c
int abi;

abi = landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION);
if (abi < 0) {
    switch (errno) {
    case ENOSYS:
        printf("当前内核不支持Landlock。\n");
        break;
    case EOPNOTSUPP:
        printf("Landlock当前已禁用。\n");
        break;
    }
    return 0;
}
if (abi >= 2) {
    printf("Landlock支持LANDLOCK_ACCESS_FS_REFER。\n");
}
```

以下内核接口默认由第一个ABI版本支持。从特定版本开始支持的功能将明确标记出来。

内核接口
========

访问权限
--------

.. kernel-doc:: include/uapi/linux/landlock.h
    :identifiers: fs_access net_access

创建新的规则集
---------------

.. kernel-doc:: security/landlock/syscalls.c
    :identifiers: sys_landlock_create_ruleset

.. kernel-doc:: include/uapi/linux/landlock.h
    :identifiers: landlock_ruleset_attr

扩展规则集
------------

.. kernel-doc:: security/landlock/syscalls.c
    :identifiers: sys_landlock_add_rule

.. kernel-doc:: include/uapi/linux/landlock.h
    :identifiers: landlock_rule_type landlock_path_beneath_attr
                  landlock_net_port_attr

强制执行规则集
---------------

.. kernel-doc:: security/landlock/syscalls.c
    :identifiers: sys_landlock_restrict_self

当前限制
========

文件系统拓扑修改
-------------------

使用文件系统限制进行沙箱化的线程无法修改文件系统拓扑，无论是通过`mount(2)`还是`pivot_root(2)`。然而，`chroot(2)`调用不会被拒绝。

特殊文件系统
--------------

Landlock可以根据规则集的处理访问权限限制对普通文件和目录的访问。然而，那些不是来自用户可见文件系统（例如管道、套接字），但仍然可以通过`/proc/<pid>/fd/*`访问的文件目前还不能显式地受到限制。类似地，一些特殊的内核文件系统（如nsfs），可以通过`/proc/<pid>/ns/*`访问，目前也不能显式地受到限制。然而，借助`ptrace限制`_，根据域层次结构自动限制对这些敏感`/proc`文件的访问。未来的Landlock演进仍有可能通过专用规则集标志显式限制此类路径。

规则集层
--------------

堆叠的规则集层数量有限制，最多16层。对于希望在其继承的16个规则集之外再强制执行新规则集的任务来说，这可能会成为一个问题。一旦达到此限制，sys_landlock_restrict_self()会返回E2BIG。因此，强烈建议在一个线程的生命周期中仔细构建规则集，特别是对于能够启动其他应用程序的应用程序（例如shell、容器管理器等）。

内存使用
------------

用于创建规则集的内核内存是被记账的，并且可以通过Documentation/admin-guide/cgroup-v1/memory.rst进行限制。

IOCTL支持
------------

`LANDLOCK_ACCESS_FS_IOCTL_DEV`权限限制了`ioctl(2)`的使用，但它仅适用于*新打开*的设备文件。这意味着特别像stdin、stdout和stderr这样的现有文件描述符不受影响。
用户应注意，TTY 设备传统上允许通过 `TIOCSTI` 和 `TIOCLINUX` IOCTL 命令控制同一 TTY 上的其他进程。在现代 Linux 系统中，这两个命令都需要 `CAP_SYS_ADMIN` 权限，但 `TIOCSTI` 的行为是可以配置的。

因此，在较旧的系统上，建议关闭继承的 TTY 文件描述符，或者在可能的情况下，从 `/proc/self/fd/*` 重新打开它们而不使用 `LANDLOCK_ACCESS_FS_IOCTL_DEV` 权限。

目前，Landlock 的 IOCTL 支持是粗粒度的，但未来可能会变得更加细粒度。在此之前，建议用户通过文件层次结构建立所需的保证，仅在确实需要的地方允许 `LANDLOCK_ACCESS_FS_IOCTL_DEV` 权限。

之前的限制
===========

文件重命名和链接（ABI < 2）
-----------------------------

由于 Landlock 针对的是非特权访问控制，因此需要正确处理规则的组合。这种属性也意味着规则的嵌套。正确处理多层规则集，每一层都能限制对文件的访问，还意味着从父级到其层次结构的规则集限制的继承。因为文件是通过其层次结构来识别和限制的，所以将一个文件从一个目录移动或链接到另一个目录意味着层次结构约束的传播，或者根据潜在丢失的约束来限制这些操作。为了防止通过重命名或链接进行权限提升，并出于简化的目的，Landlock 之前限制了在同一目录内的链接和重命名。

从 Landlock ABI 版本 2 开始，现在可以通过新的 `LANDLOCK_ACCESS_FS_REFER` 访问权限安全地控制重命名和链接。

文件截断（ABI < 3）
--------------------

在第三个 Landlock ABI 之前，无法拒绝文件截断操作，所以在仅支持第一个或第二个 ABI 的内核中，文件截断总是被允许的。

从 Landlock ABI 版本 3 开始，现在可以通过新的 `LANDLOCK_ACCESS_FS_TRUNCATE` 访问权限安全地控制截断。

网络支持（ABI < 4）
--------------------

从 Landlock ABI 版本 4 开始，现在可以通过新的 `LANDLOCK_ACCESS_NET_BIND_TCP` 和 `LANDLOCK_ACCESS_NET_CONNECT_TCP` 访问权限限制 TCP 绑定和连接动作仅限于一组允许的端口。

IOCTL（ABI < 5）
----------------

在第五个 Landlock ABI 之前，无法拒绝 IOCTL 操作，因此当使用仅支持早期 ABI 的内核时，`ioctl(2)` 始终是被允许的。
从 Landlock ABI 版本 5 开始，可以使用新的 `LANDLOCK_ACCESS_FS_IOCTL_DEV` 权限限制 `manpage:ioctl(2)` 的使用。

.. _kernel_support:

内核支持
=========

构建时配置
------------

Landlock 最初是在 Linux 5.13 中引入的，但必须在构建时通过 `CONFIG_SECURITY_LANDLOCK=y` 进行配置。Landlock 也必须像其他安全模块一样在启动时启用。默认启用的安全模块列表由 `CONFIG_LSM` 设置。内核配置应包含 `CONFIG_LSM=landlock,[...]`，其中 `[...]` 是运行系统中可能有用的其他安全模块列表（参见 `CONFIG_LSM` 帮助）。

启动时配置
------------

如果当前内核没有在 `CONFIG_LSM` 中包含 `landlock`，可以通过向引导加载程序配置中的 `Documentation/admin-guide/kernel-parameters.rst` 添加 `lsm=landlock,[...]` 来启用 Landlock。
例如，如果当前内置配置是：

.. code-block:: console

    $ zgrep -h "^CONFIG_LSM=" "/boot/config-$(uname -r)" /proc/config.gz 2>/dev/null
    CONFIG_LSM="lockdown,yama,integrity,apparmor"

...且命令行不包含 `landlock`：

.. code-block:: console

    $ sed -n 's/.*\(\<lsm=\S\+\).*/\1/p' /proc/cmdline
    lsm=lockdown,yama,integrity,apparmor

...我们应该配置引导加载程序以设置一个扩展 `lsm` 列表的命令行，其前缀为 `landlock,`：

  lsm=landlock,lockdown,yama,integrity,apparmor

重启后，我们可以通过查看内核日志来检查 Landlock 是否已启动并运行：

.. code-block:: console

    # dmesg | grep landlock || journalctl -kb -g landlock
    [    0.000000] Command line: [...] lsm=landlock,lockdown,yama,integrity,apparmor
    [    0.000000] Kernel command line: [...] lsm=landlock,lockdown,yama,integrity,apparmor
    [    0.000000] LSM: initializing lsm=lockdown,capability,landlock,yama,integrity,apparmor
    [    0.000000] landlock: Up and running

内核可以在构建时配置为始终加载 `lockdown` 和 `capability` LSM。在这种情况下，即使引导加载程序中未配置这些 LSM，它们也会出现在 `LSM: initializing` 日志行的开头。

网络支持
------------

为了能够显式允许 TCP 操作（例如，使用 `LANDLOCK_ACCESS_NET_BIND_TCP` 添加网络规则），内核必须支持 TCP (`CONFIG_INET=y`)。否则，`sys_landlock_add_rule()` 将返回 `EAFNOSUPPORT` 错误，这可以安全地忽略，因为这种类型的 TCP 操作已经不可能实现。

问题与答案
============

用户空间沙箱管理器如何？
-------------------------------

使用用户空间进程强制对内核资源实施限制可能会导致竞态条件或不一致的评估（即《系统调用拦截安全工具的实际问题》中提到的操作系统代码和状态的错误镜像）。

命名空间和容器如何？
------------------------------

命名空间有助于创建沙箱，但它们不是为访问控制设计的，因此缺少此类用途的一些有用功能（例如，没有细粒度的限制）。此外，其复杂性可能导致安全问题，尤其是在不受信任的进程可以操纵它们的情况下（参见《控制用户命名空间的访问》）。

附加文档
============

* Documentation/security/landlock.rst
* https://landlock.io

.. 链接
.. _samples/landlock/sandboxer.c:
   https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/samples/landlock/sandboxer.c
