使用kgdb、kdb及内核调试器内部机制
==================================

:作者: Jason Wessel

简介
====

内核有两个不同的调试前端（kdb和kgdb），它们与调试核心进行交互。如果你在编译时和运行时正确配置内核，可以使用任何一个调试前端，并且可以在它们之间动态转换。
kdb是一个简单的类似shell的接口，你可以在带有键盘或串行控制台的系统控制台上使用它。你可以用它来检查内存、寄存器、进程列表、dmesg，甚至设置断点以在某个位置停止。kdb不是源级调试器，尽管你可以设置断点并执行一些基本的内核运行控制。kdb主要用于做一些分析以帮助开发或诊断内核问题。如果代码是用“CONFIG_KALLSYMS”构建的，你可以通过名称访问内建内核或内核模块中的一些符号。
kgdb旨在作为Linux内核的源级调试器使用。它与gdb一起用于调试Linux内核。预期的是gdb可以用来“中断”到内核中，以检查内存、变量和查看调用堆栈信息，类似于应用程序开发者使用gdb调试应用程序的方式。可以在内核代码中设置断点并执行有限的执行步骤。
使用kgdb需要两台机器。其中一台是开发机，另一台是目标机。要调试的内核运行在目标机上。开发机运行一个针对包含符号的vmlinux文件的gdb实例（而不是像bzImage、zImage、uImage这样的引导映像）。在gdb中，开发者指定连接参数并连接到kgdb。开发者与gdb的连接类型取决于测试机内核中是否内置或加载了kgdb I/O模块。

编译内核
========

- 为了启用kdb的编译，你必须首先启用kgdb
- kgdb的测试编译选项在kgdb测试套件章节中有描述
kgdb的内核配置选项
-------------------

为了启用“CONFIG_KGDB”，你应该在
:menuselection:`内核黑客 --> 内核调试` 下选择
:menuselection:`KGDB: 内核调试器`
虽然不要求你的vmlinux文件中有符号，但如果没有符号数据，gdb往往不太有用，因此你应该启用“CONFIG_DEBUG_INFO”，它在配置菜单中被称为 :menuselection:`使用调试信息编译内核`
建议（但不是必须）启用“CONFIG_FRAME_POINTER”内核选项，它在配置菜单中被称为 :menuselection:`使用帧指针编译内核`。此选项会在编译的可执行文件中插入代码，这些代码会在不同位置保存帧信息到寄存器或堆栈中，这使得调试器如gdb在调试内核时能更准确地构建堆栈回溯。
如果你使用的架构支持内核选项“CONFIG_STRICT_KERNEL_RWX”，你应该考虑将其关闭。此选项会阻止使用软件断点，因为它将内核某些内存区域标记为只读。如果kgdb对您所使用的架构支持硬件断点，你可以开启“CONFIG_STRICT_KERNEL_RWX”选项使用硬件断点；否则你需要关闭这个选项。
接下来，您应该选择一个或多个I/O驱动程序来连接调试主机和被调试的目标。早期启动调试需要一个支持早期调试的KGDB I/O驱动程序，并且该驱动程序必须直接构建到内核中。KGDB I/O驱动程序配置是通过内核或模块参数进行的，您可以了解更多关于参数`kgdboc`的信息。
下面是一组`.config`符号的例子，用于启用或禁用KGDB：

  * `# CONFIG_STRICT_KERNEL_RWX is not set`
  * `CONFIG_FRAME_POINTER=y`
  * `CONFIG_KGDB=y`
  * `CONFIG_KGDB_SERIAL_CONSOLE=y`

内核配置选项：KDB
------------------

KDB比简单的基于内核调试核心上的gdbstub复杂得多。KDB必须实现一个shell，并在内核的其他部分添加一些辅助函数，负责打印出有趣的数据，如运行`lsmod`或`ps`时所看到的内容。为了将KDB构建到内核中，您需要遵循与KGDB相同的步骤。
KDB的主要配置选项是`CONFIG_KGDB_KDB`，在配置菜单中称为“KGDB_KDB: 包含KDB前端用于KGDB”。理论上，如果您计划在串行端口上使用KDB，在配置KGDB时已经选择了像`CONFIG_KGDB_SERIAL_CONSOLE`这样的I/O驱动程序。
如果您想使用PS/2风格的键盘与KDB一起工作，您需要选择`CONFIG_KDB_KEYBOARD`，在配置菜单中称为“KGDB_KDB: 键盘作为输入设备”。`CONFIG_KDB_KEYBOARD`选项不用于KGDB的gdb接口中的任何功能。`CONFIG_KDB_KEYBOARD`选项只与KDB一起工作。
下面是一组`.config`符号的例子，用于启用/禁用KDB：

  * `# CONFIG_STRICT_KERNEL_RWX is not set`
  * `CONFIG_FRAME_POINTER=y`
  * `CONFIG_KGDB=y`
  * `CONFIG_KGDB_SERIAL_CONSOLE=y`
  * `CONFIG_KGDB_KDB=y`
  * `CONFIG_KDB_KEYBOARD=y`

内核调试器启动参数
====================

本节描述了影响内核调试器配置的各种运行时内核参数。下一章涵盖了使用KDB和KGDB以及提供了一些配置参数的例子。
内核参数：kgdboc
-------------------

kgdboc驱动最初是一个缩写，意为“kgdb通过控制台”。今天它是配置如何从gdb通信到KGDB以及您想要使用的设备以与KDB shell交互的主要机制。
对于KGDB/GDB，kgdboc设计用于单个串行端口。它旨在涵盖您希望使用串行控制台作为主要控制台以及进行内核调试的情况。同样也可以在未指定为系统控制台的串行端口上使用KGDB。kgdboc可以配置为内建内核或可加载的内核模块。只有当您将kgdboc作为内置构建到内核中时，才能利用`kgdbwait`和早期调试。
可选地，您可以选择激活KMS（内核模式设置）集成。当您使用KMS与kgdboc并且拥有具有原子模式设置挂钩的视频驱动程序时，可以在图形控制台上进入调试器。当恢复内核执行时，将恢复先前的图形模式。这种集成可以作为一个有用的工具，有助于诊断崩溃或使用KDB进行内存分析，同时允许全图形控制台应用程序运行。
kgdboc参数
~~~~~~~~~~

用法如下：

    kgdboc=[kms][[,]kbd][[,]serial_device][,baud]

如果使用任何可选配置，则必须按照上面列出的顺序使用。
缩写：

- kms = 内核模式设置

- kbd = 键盘

您可以配置 kgdboc 使用键盘和/或串行设备，这取决于您是否使用 kdb 和/或 kgdb，在以下任一场景中。如果同时使用这些可选配置，则必须遵守上述列出的顺序。仅使用 kms 和 gdb 通常不是一个有用的组合。
使用可加载模块或内置
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. 作为内建到内核：

   使用内核启动参数：

	``kgdboc=<tty-device>,[baud]``

2. 作为内核可加载模块：

   使用命令：

	``modprobe kgdboc kgdboc=<tty-device>,[baud]``

以下是格式化 kgdboc 字符串的两个示例。第一个适用于 x86 目标，使用第一个串行端口。第二个示例适用于 ARM Versatile AB，使用第二个串行端口：
1. ``kgdboc=ttyS0,115200``

   2. ``kgdboc=ttyAMA1,115200``

通过 sysfs 在运行时配置 kgdboc
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在运行时，您可以通过向 sysfs 中回显参数来启用或禁用 kgdboc。以下是两个示例：

1. 在 ttyS0 上启用 kgdboc：

	``echo ttyS0 > /sys/module/kgdboc/parameters/kgdboc``

2. 禁用 kgdboc：

	``echo "" > /sys/module/kgdboc/parameters/kgdboc``

.. note:: 

   如果您正在配置已配置或打开的 tty 控制台，则无需指定波特率
更多示例
^^^^^^^^^^^^^^^^

您可以根据是否使用 kdb 和/或 kgdb 来配置 kgdboc 使用键盘和/或串行设备，在以下任一场景中：
1. 仅通过串行端口使用 kdb 和 kgdb：

	``kgdboc=<serial_device>[,baud]``

   示例：

	``kgdboc=ttyS0,115200``

2. 使用键盘和串行端口的 kdb 和 kgdb：

	``kgdboc=kbd,<serial_device>[,baud]``

   示例：

	``kgdboc=kbd,ttyS0,115200``

3. 使用键盘的 kdb：

	``kgdboc=kbd``

4. 使用内核模式设置的 kdb：

	``kgdboc=kms,kbd``

5. 使用内核模式设置和通过串行端口的 kgdb 的 kdb：

	``kgdboc=kms,kbd,ttyS0,115200``

.. note:: 

   kgdboc 不支持通过 gdb 远程协议中断目标。除非您有一个将控制台输出分割到终端程序的代理，否则您必须手动发送 :kbd:`SysRq-G`。一个控制台代理为调试器提供了一个单独的 TCP 端口，并为“人类”控制台提供了一个单独的 TCP 端口。该代理可以为您发送 :kbd:`SysRq-G`

当不使用调试器代理与 kgdboc 配合使用时，您可能会在两个入口点之一连接调试器。如果您加载了 kgdboc 后发生异常，控制台上应打印一条消息表明它正在等待调试器。在这种情况下，您断开终端程序的连接，然后用调试器替换它。如果您想中断目标系统并强制进入调试会话，则必须发出 :kbd:`Sysrq` 序列，然后键入字母 :kbd:`g`。然后您断开终端会话并连接 gdb。如果您不喜欢这种情况，您的选择是修改 gdb 以便在初始连接时也能发送 :kbd:`SysRq-G`，或者使用允许未修改的 gdb 进行调试的调试器代理
内核参数：``kgdboc_earlycon``
-------------------------------------

如果您指定了内核参数 ``kgdboc_earlycon`` 并且您的串行驱动注册了一个支持轮询（不需要中断并实现了非阻塞读取()函数）的引导控制台，kgdb 将尝试使用引导控制台工作，直到它可以转换到由 ``kgdboc`` 参数指定的常规 tty 驱动
通常只有一个引导控制台（尤其是实现了读取()函数的），因此仅仅添加 ``kgdboc_earlycon`` 就足以使此功能生效。如果您有多个引导控制台，可以通过添加引导控制台的名称来进行区分。请注意，通过引导控制台层和 tty 层注册的名称对于同一端口来说并不相同
例如，在某个板子上为了明确可能需要这样做：

   ``kgdboc_earlycon=qcom_geni kgdboc=ttyMSM0``

如果设备上的唯一引导控制台是 "qcom_geni"，则可以简化为：

   ``kgdboc_earlycon kgdboc=ttyMSM0``

内核参数：``kgdbwait``
------------------------------

内核命令行选项 ``kgdbwait`` 使得 kgdb 在启动内核期间等待调试器连接。只有当您将 kgdb I/O 驱动编译到内核中并且指定了作为内核命令行选项的 I/O 驱动配置时，才能使用此选项
``kgdbwait`` 参数应始终跟在内核命令行中的 kgdb I/O 驱动配置参数之后，否则在要求内核使用它来等待之前 I/O 驱动不会被配置。
### 内核参数：`kgdbwait`

当使用此选项时，内核将在I/O驱动程序和架构允许的最早时机停止并等待。如果你将kgdb I/O驱动程序构建为可加载的内核模块，`kgdbwait`将不会执行任何操作。

### 内核参数：`kgdbcon`

`kgdbcon`功能允许你在gdb连接到内核时在gdb内部看到`printk()`消息。Kdb不使用`kgdbcon`功能。
Kgdb支持在调试器连接且运行时使用gdb串行协议将控制台消息发送给调试器。有两种方式来激活此功能：

1. 通过内核命令行选项激活：
   
   ```
   kgdbcon
   ```

2. 在配置I/O驱动程序之前使用sysfs：
   
   ```
   echo 1 > /sys/module/kgdb/parameters/kgdb_use_con
   ```

**注意**：

   如果你在此配置kgdb I/O驱动程序之后进行设置，则该设置直到下一次I/O重新配置时才生效。

**重要**：

   你不能在一个作为活动系统控制台的tty上同时使用`kgdboc`和`kgdbcon`。错误示例：

   ```
   console=ttyS0,115200 kgdboc=ttyS0 kgdbcon
   ```

可以在一个不是系统控制台的tty上同时使用此选项与`kgdboc`。

### 运行时参数：`kgdbreboot`

`kgdbreboot`功能允许你更改调试器处理重启通知的方式。你有三种选择。默认行为始终设置为0。

| 选项 | 命令                                                                                       | 描述                                        |
|------|--------------------------------------------------------------------------------------------|---------------------------------------------|
| 1    | `echo -1 > /sys/module/debug_core/parameters/kgdbreboot`                                  | 完全忽略重启通知                            |
| 2    | `echo 0 > /sys/module/debug_core/parameters/kgdbreboot`                                   | 向任何已连接的调试器客户端发送断开连接消息  |
| 3    | `echo 1 > /sys/module/debug_core/parameters/kgdbreboot`                                   | 在重启通知时进入调试器                      |

### 内核参数：`nokaslr`

如果你使用的架构默认启用了KASLR（内核地址空间布局随机化），你应该考虑关闭它。KASLR会随机化内核映像的虚拟地址，这可能会使从vmlinux符号表解析内核符号地址的gdb感到困惑。
### 使用kdb
#### 通过串口快速启动kdb
##### 快速示例：如何使用kdb
1. **配置kgdboc**：
   - 在启动时通过内核参数配置kgdboc：

     ```shell
     console=ttyS0,115200 kgdboc=ttyS0,115200 nokaslr
     ```

   - 或者

   - 在内核启动后配置kgdboc；假设您正在使用串口控制台：

     ```shell
     echo ttyS0 > /sys/module/kgdboc/parameters/kgdboc
     ```

2. **手动进入或等待内核调试器**：
   - 有几种方法可以手动进入内核调试器，所有这些都涉及到使用 `SysRq-G`，这意味着您必须在内核配置中启用 `CONFIG_MAGIC_SYSRQ=y`
     - 当以root身份登录或具有超级用户会话时，您可以运行：

       ```shell
       echo g > /proc/sysrq-trigger
       ```

     - 示例使用minicom 2.2：

       按键： `CTRL-A` `f` `g`

     - 当您已telnet到支持发送远程中断的终端服务器时：

       按键： `CTRL-]`

       输入： `send break`

       按键： `Enter` `g`

3. **从kdb提示符运行命令**：
   - 从kdb提示符，您可以运行 `help` 命令来查看可用命令的完整列表。
   - kdb中一些有用的命令包括：
     - `lsmod`：显示已加载的内核模块的位置
     - `ps`：仅显示活动进程
     - `ps A`：显示所有进程
     - `summary`：显示内核版本信息和内存使用情况
     - `bt`：获取当前进程的堆栈回溯（使用dump_stack()）
     - `dmesg`：查看内核日志缓冲区
     - `go`：继续系统运行

4. **完成kdb使用后的操作**：
   - 当您完成使用kdb后，需要考虑重启系统或使用 `go` 命令恢复正常的内核执行。如果您暂停内核运行了一段时间，依赖于及时网络连接或与实际时间相关的应用可能会受到影响，因此在使用内核调试器时应考虑到这一点。

#### 通过连接键盘的控制台快速启动kdb
##### 快速示例：如何使用kdb与键盘
1. **配置kgdboc**：
   - 在启动时通过内核参数配置kgdboc：

     ```shell
     kgdboc=kbd
     ```

   - 或者

   - 在内核启动后配置kgdboc：

     ```shell
     echo kbd > /sys/module/kgdboc/parameters/kgdboc
     ```

2. **手动进入或等待内核调试器**：
   - 有几种方法可以手动进入内核调试器，所有这些都涉及到使用 `SysRq-G`，这意味着您必须在内核配置中启用 `CONFIG_MAGIC_SYSRQ=y`
     - 当以root身份登录或具有超级用户会话时，您可以运行：

       ```shell
       echo g > /proc/sysrq-trigger
       ```

     - 示例使用笔记本电脑键盘：

       按住： `Alt`

       按住： `Fn`

       按下并释放标有 `SysRq` 的键

       释放： `Fn`

       按下并释放： `g`

       释放： `Alt`

     - 示例使用PS/2 101键键盘：

       按住： `Alt`

       按下并释放标有 `SysRq` 的键

       按下并释放： `g`

       释放： `Alt`

3. **输入kdb命令**：
   - 现在输入一个kdb命令，如 `help`、`dmesg`、`bt` 或 `go` 来继续内核执行。

### 使用kgdb/gdb
#### 为了使用kgdb，必须通过向其中一个kgdb I/O驱动程序传递配置信息来激活它
- 如果不传递任何配置信息，kgdb将不会做任何事情。只有当加载并配置了一个kgdb I/O驱动程序时，kgdb才会主动连接到内核陷阱钩子。如果您取消配置了一个kgdb I/O驱动程序，kgdb将取消注册所有内核钩点。
- 所有的kgdb I/O驱动程序都可以在运行时重新配置，如果启用了 `CONFIG_SYSFS` 和 `CONFIG_MODULES`，则可以通过向 `/sys/module/<driver>/parameter/<option>` 写入新的配置字符串来实现。可以通过传递空字符串来取消配置驱动程序。您不能在调试器连接时更改配置。请确保在尝试取消配置kgdb I/O驱动程序之前使用 `detach` 命令断开调试器。

#### 通过串口与gdb连接
1. **配置kgdboc**：
   - 在启动时通过内核参数配置kgdboc：

     ```shell
     kgdboc=ttyS0,115200
     ```

   - 或者

   - 在内核启动后配置kgdboc：

     ```shell
     echo ttyS0 > /sys/module/kgdboc/parameters/kgdboc
     ```

2. **停止内核执行（进入调试器）**：
   - 为了通过kgdboc与gdb连接，首先必须停止内核。有几种方法可以停止内核，包括将kgdbwait作为启动参数、通过 `SysRq-G` 或运行内核直到它出现异常并等待调试器连接。
- 当以根用户或超级用户会话登录时，你可以运行：

  
  echo g > /proc/sysrq-trigger
  

- Minicom 2.2 示例

  按：:kbd:`CTRL-A` :kbd:`f` :kbd:`g`

- 当你通过telnet连接到支持发送远程中断的终端服务器时

  按：:kbd:`CTRL-]`

  输入：``send break``

  按：:kbd:`Enter` :kbd:`g`

3. 从gdb连接

   直接连接端口示例：

   
           % gdb ./vmlinux
           (gdb) set serial baud 115200
           (gdb) target remote /dev/ttyS0
   

   通过TCP端口2012连接到终端服务器的kgdb示例：

   
           % gdb ./vmlinux
           (gdb) target remote 192.168.2.2:2012
   

   连接后，你可以像调试应用程序一样调试内核。
   如果你在连接过程中遇到问题，或者在调试时出现问题，通常你需要让gdb对其目标通信进行详细输出。你可以在发出``target remote``命令之前输入：

   
   set debug remote 1
   

   如果你在gdb中继续执行，并需要再次“中断”，则需要再次按下 :kbd:`SysRq-G`。可以通过在``sys_sync``处设置断点来轻松创建一个简单的入口点，之后可以从shell或脚本运行``sync``来中断到调试器。

kgdb与kdb的互操作性
=============================

可以动态地在kdb和kgdb之间切换。调试核心将记住你上次使用的是哪一个，并自动启动相同模式。

从kgdb切换到kdb
-------------------

从kgdb切换到kdb有两种方式：你可以使用gdb发出维护数据包，或者盲目地输入命令``$3#33``。
每当内核调试器在kgdb模式下停止时，它会打印消息``KGDB or $3#33 for KDB``。需要注意的是，你必须一次性正确输入这个序列。不能使用退格或删除键，因为kgdb会将其解释为调试流的一部分。

1. 通过盲目输入从kgdb切换到kdb：

   $3#33

2. 使用gdb从kgdb切换到kdb：

   maintenance packet 3
   
   .. note::
     
     现在你必须终止gdb。通常情况下，你按 :kbd:`CTRL-Z` 并发出命令：
     
	 kill -9 %

从kdb切换到kgdb
-------------------

有两种方式可以从kdb切换到kgdb。你可以手动通过在kdb shell提示符下发出kgdb命令进入kgdb模式，或者在kdb shell提示符活动时连接gdb。kdb shell会寻找gdb远程协议中的典型第一个命令，如果它看到这些命令之一，它会自动切换到kgdb模式。

1. 在kdb中发出命令：

   kgdb

   然后断开终端程序并用gdb代替它进行连接。

2. 在kdb提示符下，断开终端程序并用gdb代替它进行连接。

从gdb运行kdb命令
-----------------

可以从gdb使用gdb监视器命令运行一组有限的kdb命令。你不希望执行任何运行控制或断点操作，因为这可能会干扰内核调试器的状态。如果你已经连接了gdb，则应该使用gdb来进行断点和运行控制操作。更有用的命令可能是像lsmod、dmesg、ps或一些内存信息命令。要查看所有可运行的kdb命令，可以运行``monitor help``。
示例：

    (gdb) monitor ps
    1 idle process (state I) and
    27 sleeping system daemon (state M) processes suppressed,
    use 'ps A' to see all
Task Addr       Pid   Parent [*] cpu State Thread     Command

    0xc78291d0        1        0  0    0   S  0xc7829404  init
    0xc7954150      942        1  0    0   S  0xc7954384  dropbear
    0xc78789c0      944        1  0    0   S  0xc7878bf4  sh
    (gdb)

kgdb测试套件
==============

当在内核配置中启用了kgdb时，也可以选择启用配置参数``KGDB_TESTS``。启用此选项将启用一个特殊的kgdb I/O模块，该模块旨在测试kgdb内部功能。
### kgdb测试主要面向开发者，用于测试kgdb内部机制以及为新架构开发特定的实现。这些测试并不适合Linux内核的最终用户。主要文档来源是查看`drivers/misc/kgdbts.c`文件。

kgdb测试套件可以在编译时通过设置内核配置参数`KGDB_TESTS_ON_BOOT`来运行核心测试集。这一选项主要针对自动化回归测试，并不需要修改内核启动配置参数。如果启用了这一选项，可以通过在内核启动参数中指定`kgdbts=`来禁用kgdb测试套件。

#### 内核调试器内部机制

##### 架构特定性

内核调试器由多个组件构成：

1. **调试核心**
   - 调试核心位于`kernel/debugger/debug_core.c`中，它包括：
     - 一个通用的操作系统异常处理器，包括在多CPU系统中同步处理器到停止状态的功能。
     - 与kgdb I/O驱动程序通信的API。
     - 调用特定于架构的kgdb实现的API。
     - 在使用调试器时执行安全内存读写操作的逻辑。
     - 除非被特定架构覆盖，否则提供完整的软件断点实现。
     - 调用kdb或kgdb前端到调试核心的API。
     - 用于原子内核模式设置的结构和回调API。
       > 注意: `kgdboc`是调用kms回调的地方。
2. **kgdb特定于架构的实现**
   - 这一实现在`arch/*/kernel/kgdb.c`中通常可以找到。例如，在`arch/x86/kernel/kgdb.c`中包含了实现硬件断点以及在这个架构上动态注册和注销陷阱处理器的具体细节。
   - 特定于架构的部分实现了以下功能：
     - 包含特定于架构的陷阱捕获器，用于调用`kgdb_handle_exception()`以开始kgdb的工作。
     - 从gdb特定的包格式到`struct pt_regs`的转换。
     - 注册和注销特定于架构的陷阱钩子。
     - 任何特殊的异常处理和清理工作。
     - NMI异常处理和清理工作。
     - （可选）硬件断点支持。
3. **gdbstub前端（即kgdb）**
   - gdbstub位于`kernel/debug/gdbstub.c`中，它包含了：
     - 实现gdb串行协议的所有逻辑。
4. **kdb前端**
   - kdb调试shell被分解为多个组成部分。kdb核心位于`kernel/debug/kdb`中。在其他一些内核组件中有一些辅助函数，使得kdb能够在不引起内核死锁的情况下检查并报告有关内核的信息。kdb核心实现了以下功能：
     - 简单的shell。
     - kdb核心命令集。
     - 注册额外的kdb shell命令的注册API。
一个很好的自包含kdb模块的例子是`ftdump`命令，用于转储ftrace缓冲区。请参见：`kernel/trace/trace_kdb.c`

-  若要了解如何动态注册一个新的kdb命令，请构建来自`samples/kdb/kdb_hello.c`的kdb_hello.ko内核模块。为了构建这个示例，你可以在内核配置中设置`CONFIG_SAMPLES=y`和`CONFIG_SAMPLE_KDB=m`。之后运行`modprobe kdb_hello`，当你下次进入kdb shell时，就可以运行`hello`命令。

- `kdb_printf()`的实现可以直接向I/O驱动程序发送消息，绕过内核日志。
- kdb shell中的SW/HW断点管理。

5. kgdb I/O驱动程序

每个kgdb I/O驱动程序必须提供以下内容的实现：

- 通过内置或模块进行配置
- 动态配置和kgdb钩子注册调用
- 读写字符接口
- 用于从kgdb核心卸载的清理处理程序
- （可选）早期调试方法

任何给定的kgdb I/O驱动程序都必须与硬件紧密配合，并且必须以不会启用中断或更改系统上下文其他部分的方式操作，除非完全恢复这些状态。当kgdb核心需要输入时，它会反复“轮询”kgdb I/O驱动程序获取字符。如果当前没有数据可用，则期望I/O驱动程序立即返回。这样做允许将来有可能以某种方式触碰看门狗硬件，使得启用这些功能时目标系统不会重置。

如果你打算为新的架构添加特定于kgdb的支持，在特定架构的Kconfig文件中定义`HAVE_ARCH_KGDB`。这将为该架构启用kgdb，此时你必须创建一个特定于架构的kgdb实现。

在每个架构的`asm/kgdb.h`文件中都需要设置几个标志。这些包括：

- `NUMREGBYTES`: 所有寄存器的大小（字节数），以便确保它们都能装入一个数据包中
- `BUFMAX`: GDB将读取的缓冲区的大小（字节数）。此值必须大于`NUMREGBYTES`
- `CACHE_FLUSH_IS_SAFE`: 如果总是安全地调用flush_cache_range或flush_icache_range，则设置为1。在某些架构上，由于我们使其他CPU处于挂起状态，这些函数可能不适合SMP环境

对于通用后端（位于`kernel/kgdb.c`中）中的一些函数，除非标记为（可选），否则必须由特定于架构的后端提供，否则如果架构不需要提供特定实现，则可以使用默认函数。
  
kgdboc内部机制
-----------------

kgdboc和UARTs
~~~~~~~~~~~~~~

kgdboc驱动实际上是一个非常轻量级的驱动，依赖于底层硬件驱动具有“轮询钩子”，tty驱动程序就连接到这些钩子上。在kgdboc的初始实现中，对serial_core进行了修改，使其暴露了一个低级别的UART钩子，用于在原子上下文中执行轮询模式下的单个字符读写。当kgdb向调试器发出I/O请求时，kgdboc会调用serial core中的回调函数，而serial core又会使用UART驱动中的回调函数。

当使用kgdboc与UART时，UART驱动程序必须在struct uart_ops中实现两个回调函数。
来自`drivers/8250.c`的例子：


    #ifdef CONFIG_CONSOLE_POLL
        .poll_get_char = serial8250_get_poll_char,
        .poll_put_char = serial8250_put_poll_char,
    #endif


任何围绕创建轮询驱动的具体实现都应该使用`#ifdef CONFIG_CONSOLE_POLL`，如上所示。需要注意的是，轮询钩子必须以能够从原子上下文中被调用的方式来实现，并且在返回时必须恢复UART芯片的状态，以便当调试器脱离时系统能恢复正常。对于你考虑使用的任何类型的锁都要非常小心，因为在这里失败很可能意味着需要按下复位按钮。
kgdboc和键盘
~~~~~~~~~~~~~~~~~~~~~~~~

kgdboc驱动包含了配置与连接的键盘通信的逻辑。只有当内核配置中的`CONFIG_KDB_KEYBOARD=y`被设置时，键盘基础设施才会被编译进内核中。
PS/2类型键盘的核心轮询驱动位于`drivers/char/kdb_keyboard.c`。当kgdboc填充数组`kdb_poll_funcs[]`中的回调函数时，此驱动程序将被挂接到调试核心。`kdb_get_kbd_char()`是最高级别的函数，用于轮询硬件以获取单个字符输入。
kgdboc和kms
~~~~~~~~~~~~~~~~~~

kgdboc驱动包含了请求图形显示切换到文本上下文的逻辑，当你使用`kgdboc=kms,kbd`时，前提是你的视频驱动支持帧缓冲控制台和原子内核模式设置。
每当进入内核调试器时，它都会调用`kgdboc_pre_exp_handler()`，该函数进而调用虚拟控制台层中的`con_debug_enter()`。在恢复内核执行时，内核调试器会调用`kgdboc_post_exp_handler()`，该函数进而调用`con_debug_leave()`。
任何想要与内核调试器兼容并且实现原子kms回调的视频驱动都必须实现`mode_set_base_atomic`、`fb_debug_enter`和`fb_debug_leave`操作。对于`fb_debug_enter`和`fb_debug_leave`，可以选择使用通用的drm帧缓冲辅助函数或者为硬件实现自定义的功能。下面的示例展示了`mode_set_base_atomic`操作在`drivers/gpu/drm/i915/intel_display.c`中的初始化：


    static const struct drm_crtc_helper_funcs intel_helper_funcs = {
    [...]
            .mode_set_base_atomic = intel_pipe_set_base_atomic,
    [...]
    };


下面是i915驱动如何在`drivers/gpu/drm/i915/intel_fb.c`中初始化`fb_debug_enter`和`fb_debug_leave`函数来使用通用drm辅助函数的示例：


    static struct fb_ops intelfb_ops = {
    [...]
           .fb_debug_enter = drm_fb_helper_debug_enter,
           .fb_debug_leave = drm_fb_helper_debug_leave,
    [...]
    };


致谢
=======

以下人员为本文档做出了贡献：

1. Amit Kale <amitkale@linsyssoft.com>

2. Tom Rini <trini@kernel.crashing.org>

2008年3月，本文档由以下人员进行了全面重写：

-  Jason Wessel <jason.wessel@windriver.com>

2010年1月，本文档更新以包含kdb：
-  Jason Wessel <jason.wessel@windriver.com>
