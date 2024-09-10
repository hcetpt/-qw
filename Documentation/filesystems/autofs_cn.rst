=====================
autofs - 它是如何工作的
=====================

目的
====

autofs 的目标是提供按需挂载和无竞争的自动卸载各种其他文件系统。这提供了两个关键优势：

1. 无需等到所有可能需要的文件系统都挂载完毕再启动。尝试访问这些较慢文件系统的进程可能会被延迟，但其他进程可以自由继续。这对于网络文件系统（如NFS）或存储在具有换媒体机器人的介质上的文件系统尤为重要。
2. 文件系统的名字和位置可以存储在一个远程数据库中，并且可以随时更改。在访问时使用该数据库中的内容来提供访问目标。对文件系统中名称的解释甚至可以是程序化的而不是基于数据库的，例如允许通配符，并且可以根据首次访问名称的用户而变化。

上下文
======

“autofs” 文件系统模块只是 autofs 系统的一部分。还需要一个用户空间程序来查找名称并挂载文件系统。这通常是“automount”程序，尽管其他工具（包括“systemd”）也可以利用“autofs”。本文档仅描述内核模块及其与任何用户空间程序所需的交互。后续文本将此称为“automount 守护进程”或简称“守护进程”。“autofs”是一个Linux内核模块，它提供了“autofs”文件系统类型。可以挂载多个“autofs”文件系统，并且它们可以分别管理，或者由同一个守护进程统一管理。

内容
====

autofs 文件系统可以包含三种类型的对象：目录、符号链接和挂载陷阱。挂载陷阱是具有额外属性的目录，如下一节所述。
只有automount守护进程才能创建对象：符号链接通过常规的`symlink`系统调用来创建，而目录和挂载陷阱则通过`mkdir`创建。确定目录是否应为挂载陷阱是基于主映射表。autofs会咨询这个主映射表以确定哪些目录是挂载点。挂载点可以是*直接*/*间接*/*偏移*。
在大多数系统上，默认的主映射表位于*/etc/auto.master*。
如果未指定*直接*或*偏移*挂载选项（即认为挂载是*间接*的），那么根目录始终是一个普通目录；否则当根目录为空时它是挂载陷阱，不为空时是普通目录。请注意，*直接*和*偏移*被视为相同，因此简洁总结是根目录仅在文件系统以*直接*方式挂载且根目录为空时才是挂载陷阱。
在根目录中创建的目录仅在文件系统以*间接*方式挂载且这些目录为空时才被视为挂载陷阱。
树中的更深层目录则取决于*maxproto*挂载选项，特别是它是否小于五。
当*maxproto*为五时，树中任何更深一层的目录都不会是挂载陷阱，它们始终是普通目录。当*maxproto*为四（或三）时，这些目录在为空的情况下才是挂载陷阱。
因此：非空（即非叶子）目录永远不是挂载陷阱。空目录有时是挂载陷阱，有时则不是，这取决于它们在树中的位置（根、顶层还是更低层）、*maxproto*以及挂载是否为*间接*方式。

### 挂载陷阱

自动挂载系统的核心组成部分是Linux VFS提供的挂载陷阱。文件系统提供的任何目录都可以被指定为一个陷阱。这涉及两个独立的功能，它们协同工作使得自动挂载系统能够正常运作：

#### **DCACHE_NEED_AUTOMOUNT**

如果一个dentry设置了DCACHE_NEED_AUTOMOUNT标志（这个标志会在inode设置S_AUTOMOUNT时或者直接设置），那么它（潜在地）是一个挂载陷阱。对这个目录的任何访问（除了`stat`操作）通常会触发dentry操作`d_op->d_automount()`。该方法的任务是找到应该在这个目录上挂载的文件系统并返回它。VFS负责实际将该文件系统的根挂载到该目录上。
自动挂载系统本身不寻找文件系统，而是发送消息给自动挂载守护进程，要求其查找并挂载文件系统。然后自动挂载系统的`d_automount`方法等待守护进程报告一切准备就绪。此时它会返回`NULL`，表示挂载已经完成。VFS不会尝试挂载任何东西，而是沿着已存在的挂载点进行。

这一功能对于某些使用挂载陷阱的应用如NFS来说已经足够，后者创建陷阱以便服务器上的挂载点可以反映到客户端上。然而，这对自动挂载系统来说还不够。由于在目录上挂载文件系统被认为是“超越了`stat`”，如果没有某种方式避免陷入陷阱，自动挂载守护进程将无法在‘陷阱’目录上挂载文件系统。为此，还存在另一个标志：

#### **DCACHE_MANAGE_TRANSIT**

如果一个dentry设置了DCACHE_MANAGE_TRANSIT标志，则会调用两种非常不同但相关的功能，二者都使用dentry操作`d_op->d_manage()`：
首先，在检查是否有任何文件系统挂载在此目录之前，会以`rcu_walk`参数为`false`的方式调用`d_manage()`。它可能返回三种情况之一：

- 返回值为零表示此dentry没有特殊之处，应继续进行常规的挂载和自动挂载检查。
`autofs` 通常返回零，但首先会等待任何过期（已挂载文件系统的自动卸载）完成。这避免了竞态条件。

- 返回值 `-EISDIR` 告诉 VFS 忽略目录上的任何挂载，并且不考虑调用 `->d_automount()`。
这实际上禁用了 **DCACHE_NEED_AUTOMOUNT** 标志，导致该目录最终不会成为一个挂载陷阱。
当 `autofs` 检测到执行查找的进程是自动挂载守护进程，并且挂载已被请求但尚未完成时，它会返回 `-EISDIR`。它是如何确定这一点将在后面讨论。这使得自动挂载守护进程不会陷入挂载陷阱。
这里有一个微妙之处。有可能在第一个 `autofs` 文件系统下面再挂载一个第二个 `autofs` 文件系统，并且两个都由同一个守护进程管理。为了使守护进程能够在第二个上挂载某些内容，它必须能够“遍历”过第一个。这意味着 `d_manage` 不能总是为自动挂载守护进程返回 `-EISDIR`。只有在挂载已被请求但尚未完成时才应返回 `-EISDIR`。
如果 dentry 不应该是一个挂载陷阱（因为它是一个符号链接或不是空的），`d_manage` 也会返回 `-EISDIR`。
- 其他任何负数被视为错误并返回给调用者。
`autofs` 可以返回以下值：
   - `-ENOENT`：如果自动挂载守护进程未能挂载任何内容，
   - `-ENOMEM`：如果内存不足，
   - `-EINTR`：如果在等待过期完成时收到信号，
   - 或者自动挂载守护进程发送的其他任何错误。

第二种情况仅在“RCU-walk”期间发生，因此 `rcu_walk` 将被设置。
RCU-walk 是一种快速且轻量级的过程，用于遍历文件名路径（即像踮着脚尖行走）。由于 RCU-walk 无法处理所有情况，当它遇到困难时，会退回到“REF-walk”，后者较慢但更稳健。
RCU-walk 永远不会调用 `->d_automount`；文件系统必须已经挂载，否则 RCU-walk 无法处理该路径。
要确定一个挂载陷阱是否适用于 RCU-walk 模式，它会使用 `rcu_walk` 设置为 `true` 来调用 `->d_manage()`。
在这种情况下，`d_manage()` 必须避免阻塞，并尽可能避免获取自旋锁。其唯一目的是判断是否安全地进入任何已挂载的目录，唯一可能不安全的原因是正在执行或考虑挂载过期。
在 `rcu_walk` 的情况下，`d_manage()` 不能返回 -EISDIR 来告诉 VFS 这是一个不需要 `d_automount` 的目录。如果 `rcu_walk` 看到一个设置了 DCACHE_NEED_AUTOMOUNT 但没有挂载任何内容的 dentry，它将回退到 REF-walk。`d_manage()` 不能让 VFS 保持在 RCU-walk 模式中，而只能通过返回 `-ECHILD` 告诉它退出 RCU-walk 模式。
因此，当 `rcu_walk` 被设置时调用 `d_manage()` 应该根据认为进入已挂载文件系统不安全的原因返回 -ECHILD，否则返回 0。
autofs 如果文件系统的过期操作已被启动或正在考虑，则返回 `-ECHILD`，否则返回 0。

### 挂载点过期

VFS 有一种机制可以自动过期未使用的挂载点，类似于它可以过期 dcache 中任何未使用的 dentry 信息。
这由 MNT_SHRINKABLE 标志引导。这仅适用于通过 `d_automount()` 返回文件系统进行挂载的挂载点。由于 autofs 不返回这样的文件系统，而是将挂载留给 automount 守护进程，因此它也必须让 automount 守护进程参与卸载。这也意味着 autofs 对过期有更多的控制权。
VFS 还支持使用 MNT_EXPIRE 标志对 `umount` 系统调用进行挂载点“过期”。带有 MNT_EXPIRE 的卸载只有在之前有过尝试，并且自上次尝试以来文件系统未被激活且未被触及时才会成功。autofs 不依赖这一点，但它有自己的内部跟踪以确定文件系统是否最近被使用过。这允许 autofs 目录中的各个名称分别过期。
在协议版本 4 中，automount 守护进程可以在任何时候尝试卸载挂载在 autofs 文件系统上的任何文件系统，或者移除任何符号链接或空目录。如果卸载或移除成功，文件系统将恢复到挂载或创建之前的初始状态，因此对名称的任何访问都会触发正常的自动挂载处理。特别是，`rmdir` 和 `unlink` 不会在 dcache 中留下负项（negative entry），就像普通文件系统那样，因此尝试访问最近删除的对象会被传递给 autofs 处理。
在版本5中，除了从顶级目录卸载之外，这样做是不安全的。因为较低级别的目录永远不会成为挂载陷阱，其他进程会在文件系统卸载后立即看到一个空目录。因此，通常最安全的做法是使用下面描述的autofs过期协议。

通常，守护进程只想移除那些一段时间内未被使用的条目。为此，autofs为每个目录或符号链接维护了一个“last_used”时间戳。对于符号链接，它确实记录了最后一次该符号链接被“使用”或跟踪其指向的时间。对于目录，这个字段的用法略有不同。在挂载时以及在过期检查期间如果发现该目录正在使用（即有打开的文件描述符或进程的工作目录）时，会更新这个字段。此外，在路径遍历时也会进行更新。路径遍历期间的更新防止了频繁过期和立即挂载经常访问的自动挂载点。但是，在图形用户界面持续访问或应用程序频繁扫描autofs目录树的情况下，可能会积累一些实际上并未被使用的挂载点。为了应对这种情况，可以使用“strictexpire”autofs挂载选项来避免路径遍历期间的“last_used”更新，从而防止这些实际上未被使用的挂载点无法过期的情况。

守护进程能够通过一个`ioctl`请求autofs检查是否有任何内容需要过期，如后面所述。对于直接挂载，autofs会考虑整个挂载树是否可以卸载。而对于间接挂载，autofs会检查顶级目录中的每个名称，以确定其中是否有可以卸载并清理的内容。

对于间接挂载，有一个选项是考虑每个已挂载的叶子节点，而不是考虑顶级名称。这最初是为了与autofs第4版兼容，并且对于Sun格式的自动挂载映射应视为已弃用。然而，它可能再次用于amd格式的挂载映射（通常是间接映射），因为amd自动挂载器允许为单个挂载设置过期超时时间。但要实现这一点存在一些困难。

当autofs考虑某个目录时，它会检查“last_used”时间，并将其与挂载文件系统时设置的“超时”值进行比较，尽管在某些情况下会忽略这一检查。它还会检查该目录及其子目录是否正在使用。对于符号链接，仅考虑“last_used”时间。

如果两者似乎都支持过期该目录或符号链接，则会采取相应行动。

有两种方式可以让autofs考虑过期问题。第一种是使用**AUTOFS_IOC_EXPIRE** ioctl。这仅适用于间接挂载。如果它在根目录中找到了可过期的对象，它将返回该对象的名称。一旦返回了一个名称，自动挂载守护进程就需要正常卸载该名称下的所有文件系统。如上所述，对于非顶级挂载，在版本5的autofs中这样做是不安全的。因此，当前的`automount(8)`并不使用此ioctl。

第二种机制使用**AUTOFS_DEV_IOCTL_EXPIRE_CMD**或**AUTOFS_IOC_EXPIRE_MULTI** ioctl。这适用于直接和间接挂载。如果它选择了某个对象进行过期操作，它将使用下面描述的通知机制通知守护进程。这将一直阻塞直到守护进程确认过期通知为止。
这表明“`EXPIRE`”ioctl 必须从不同于处理通知的那个线程发送。
当 ioctl 阻塞时，条目将被标记为“即将过期”，并且 `d_manage` 将阻塞直到守护进程确认卸载已完成（包括移除可能需要的任何目录），或者已被中止。
与 autofs 通信：检测守护进程
===============================================

自动挂载守护进程和文件系统之间有几种通信形式。正如我们已经看到的那样，守护进程可以使用正常的文件系统操作来创建和删除目录和符号链接。
autofs 可以根据进程组 ID 号（参见 getpgid(1)）判断请求某个操作的进程是否是守护进程。
当一个 autofs 文件系统被挂载时，如果未提供 "pgrp=" 选项，则会记录挂载进程的 pgid；如果提供了该选项，则记录指定的数字。来自该进程组中的任何请求都将被视为来自守护进程。
如果守护进程需要停止并重新启动，可以通过 ioctl 提供一个新的 pgid，具体方法将在下面描述。
与 autofs 通信：事件管道
=========================================

当一个 autofs 文件系统被挂载时，必须通过 'fd=' 挂载选项传递管道的 'write' 端。autofs 将向此管道写入通知消息，供守护进程响应。
对于第 5 版，消息格式如下：

```c
    struct autofs_v5_packet {
        struct autofs_packet_hdr hdr;
        autofs_wqt_t wait_queue_token;
        __u32 dev;
        __u64 ino;
        __u32 uid;
        __u32 gid;
        __u32 pid;
        __u32 tgid;
        __u32 len;
        char name[NAME_MAX+1];
    };
```

报头的格式如下：

```c
    struct autofs_packet_hdr {
        int proto_version;        /* 协议版本 */
        int type;                 /* 包类型 */
    };
```

其中类型为以下之一：

- `autofs_ptype_missing_indirect`
- `autofs_ptype_expire_indirect`
- `autofs_ptype_missing_direct`
- `autofs_ptype_expire_direct`

这些消息可以指示某个名称不存在（有人尝试访问它但并不存在）或已被选中过期。
管道将设置为“包模式”（相当于使用 `O_DIRECT` 传递给 _pipe2(2)_），以便从管道读取时最多返回一个包，并且任何未读的部分将被丢弃。
`wait_queue_token` 是一个唯一编号，可用于标识特定请求以待确认。当消息通过管道发送时，受影响的 dentry 将被标记为“活跃”或“即将过期”，其他对该 dentry 的访问将阻塞，直到使用下面的某个 ioctl 并带有相关的 `wait_queue_token` 来确认消息。
与 autofs 通信：根目录 ioctl

=============================

autofs 文件系统的根目录将响应若干 ioctl 命令。发出 ioctl 的进程必须具有 CAP_SYS_ADMIN 权限，或者必须是自动挂载守护进程。可用的 ioctl 命令如下：

- **AUTOFS_IOC_READY**：
    已处理一个通知。ioctl 命令的参数是对应于所确认通知的“wait_queue_token”编号。
- **AUTOFS_IOC_FAIL**：
    类似于上面的情况，但表示失败，并带有错误代码 `ENOENT`。
- **AUTOFS_IOC_CATATONIC**：
    使 autofs 进入“僵化”模式，这意味着它停止向守护进程发送通知。如果写入管道失败也会进入此模式。
- **AUTOFS_IOC_PROTOVER**：
    返回正在使用的协议版本。
- **AUTOFS_IOC_PROTOSUBVER**：
    返回协议子版本，实际上是实现的版本号。
- **AUTOFS_IOC_SETTIMEOUT**：
    传递一个指向无符号长整型的指针。该值用于设置过期超时时间，并通过指针返回当前的超时值。
- **AUTOFS_IOC_ASKUMOUNT**：
    在指向的 `int` 中返回 1，表示文件系统可以卸载。这只是一个提示，因为情况随时可能改变。此调用可用于避免更耗时的完整卸载尝试。
- **AUTOFS_IOC_EXPIRE**：
    如上所述，此命令询问是否有适合过期的对象。需要一个指向数据包的指针：

    ```c
    struct autofs_packet_expire_multi {
        struct autofs_packet_hdr hdr;
        autofs_wqt_t wait_queue_token;
        int len;
        char name[NAME_MAX+1];
    };
    ```

    此结构体将被填充为可以卸载或移除的对象名称。如果没有可过期的对象，则将 `errno` 设置为 `EAGAIN`。尽管结构体中包含一个 `wait_queue_token`，但不会建立“等待队列”，也不需要确认。
**AUTOFS_IOC_EXPIRE_MULTI**：
这与 **AUTOFS_IOC_EXPIRE** 类似，不同之处在于它会发送通知给守护进程，并且会阻塞直到守护进程确认。

参数是一个整数，可以包含以下两个不同的标志：
- **AUTOFS_EXP_IMMEDIATE**：忽略 `last_used` 时间，并且如果对象当前未使用则使其过期。
- **AUTOFS_EXP_FORCED**：忽略当前使用状态，并且即使对象正在使用也使其过期。这假设守护进程请求这样做是因为它可以执行卸载操作。
- **AUTOFS_EXP_LEAVES**：选择一个叶节点而不是顶级名称来使其过期。当 *maxproto* 为 4 时这是安全的。

与 autofs 通信：字符设备 ioctl
=================================

有时无法打开 autofs 文件系统的根目录，特别是直接挂载的文件系统。如果自动挂载守护进程重新启动，则无法通过上述任何通信通道重新获得现有挂载的控制权。为此需求提供了一个“杂项”字符设备（主设备号 10，次设备号 235），可以直接与 autofs 文件系统通信。访问该设备需要具有 CAP_SYS_ADMIN 权限。

可以在该设备上使用的 'ioctl' 命令在单独的文档 `autofs-mount-control.txt` 中进行了描述，并在此处简要总结。每个 ioctl 都传递一个指向 `autofs_dev_ioctl` 结构的指针：

```c
        struct autofs_dev_ioctl {
                __u32 ver_major;
                __u32 ver_minor;
                __u32 size;             /* 包括此结构在内的总数据大小 */
                __s32 ioctlfd;          /* 自动挂载命令文件描述符 */

		/* 命令参数 */
		union {
			struct args_protover		protover;
			struct args_protosubver		protosubver;
			struct args_openmount		openmount;
			struct args_ready		ready;
			struct args_fail		fail;
			struct args_setpipefd		setpipefd;
			struct args_timeout		timeout;
			struct args_requester		requester;
			struct args_expire		expire;
			struct args_askumount		askumount;
			struct args_ismountpoint	ismountpoint;
		};

                char path[];
        };
```

对于 **OPEN_MOUNT** 和 **IS_MOUNTPOINT** 命令，目标文件系统由 `path` 标识。所有其他命令通过 `ioctlfd` 标识文件系统，`ioctlfd` 是打开根目录的文件描述符，并且可以由 **OPEN_MOUNT** 返回。

`ver_major` 和 `ver_minor` 是输入/输出参数，用于检查所请求的版本是否受支持，并报告内核模块可以支持的最大版本。
命令如下：

- **AUTOFS_DEV_IOCTL_VERSION_CMD**：
	此命令不做任何事情，除了验证和设置版本号。

- **AUTOFS_DEV_IOCTL_OPENMOUNT_CMD**：
	返回一个指向自动挂载文件系统根目录的打开文件描述符。文件系统通过名称和设备号来识别，设备号存储在 `openmount.devid` 中。
	现有文件系统的设备号可以在 `/proc/self/mountinfo` 中找到。

- **AUTOFS_DEV_IOCTL_CLOSEMOUNT_CMD**：
	与 `close(ioctlfd)` 相同。

- **AUTOFS_DEV_IOCTL_SETPIPEFD_CMD**：
	如果文件系统处于僵化模式，可以通过将新的管道写端放入 `setpipefd.pipefd` 来重新建立与守护进程的通信。
	调用进程的进程组用于标识守护进程。

- **AUTOFS_DEV_IOCTL_REQUESTER_CMD**：
	`path` 应该是自动挂载文件系统中的一个名称。
	成功返回时，`requester.uid` 和 `requester.gid` 将是触发该挂载过程的进程的 UID 和 GID。

- **AUTOFS_DEV_IOCTL_ISMOUNTPOINT_CMD**：
	检查路径是否为特定类型的挂载点——详情请参阅单独的文档。

- **AUTOFS_DEV_IOCTL_PROTOVER_CMD**

- **AUTOFS_DEV_IOCTL_PROTOSUBVER_CMD**

- **AUTOFS_DEV_IOCTL_READY_CMD**

- **AUTOFS_DEV_IOCTL_FAIL_CMD**
	与同名的 **AUTOFS_IOC** ioctl 命令具有相同的功能，但 **FAIL** 可以在 `fail.status` 中指定一个明确的错误码，而不是默认假设为 `ENOENT`。

- **AUTOFS_DEV_IOCTL_CATATONIC_CMD**

- **AUTOFS_DEV_IOCTL_TIMEOUT_CMD**

- **AUTOFS_DEV_IOCTL_EXPIRE_CMD**
	此命令对应于 **AUTOFS_IOC_EXPIRE_MULTI**。

- **AUTOFS_DEV_IOCTL_ASKUMOUNT_CMD**

这些命令都与同名的 **AUTOFS_IOC** ioctl 命令具有相同的功能，除了 **FAIL** 可以在 `fail.status` 中指定一个明确的错误码，而不是默认假设为 `ENOENT`，并且 **EXPIRE** 命令对应于 **AUTOFS_IOC_EXPIRE_MULTI**。
### 猫僵直模式

如前所述，自动文件系统挂载可以进入“猫僵直”模式。这种情况发生在写入通知管道失败时，或者通过显式的 `ioctl` 请求进入该模式。当进入猫僵直模式时，管道会被关闭，并且任何待处理的通知都会用错误码 `ENOENT` 来确认。一旦进入猫僵直模式，尝试访问不存在的名称将返回 `ENOENT`，而尝试访问现有目录则会像来自守护进程的请求一样处理，因此不会触发挂载陷阱。

当文件系统挂载时，可以指定一个 _uid_ 和 _gid_，用于设置目录和符号链接的所有权。当文件系统处于猫僵直模式时，任何具有匹配 UID 的进程都可以在根目录中创建目录或符号链接，但在其他目录中不行。

只有通过 `/dev/autofs` 上的 **AUTOFS_DEV_IOCTL_OPENMOUNT_CMD** ioctl 命令才能退出猫僵直模式。

### “忽略”挂载选项

“忽略”挂载选项可用于向应用程序提供一个通用指示，表明在显示挂载信息时应忽略该挂载条目。在其他提供自动文件系统的操作系统中，基于内核挂载列表提供给用户空间的挂载列表允许使用一个无操作挂载选项（“ignore”是大多数常见操作系统中使用的）。这旨在让用户空间程序在读取挂载列表时排除自动文件系统挂载。

### 自动文件系统、命名空间和共享挂载

通过绑定挂载和命名空间，自动文件系统可以在一个或多个文件系统命名空间中的多个位置出现。为了使这种情况下工作合理，自动文件系统应该始终以“共享”方式挂载，例如：

```
mount --make-shared /autofs/mount/point
```

自动挂载守护进程只能管理自动文件系统的单个挂载位置，如果这些挂载不是“共享”的，则其他位置将无法按预期行为。特别是，对这些其他位置的访问可能会导致 `ELOOP` 错误：

```
Too many levels of symbolic links
```

希望这些翻译对你有帮助！如果有任何问题，请随时告诉我。
