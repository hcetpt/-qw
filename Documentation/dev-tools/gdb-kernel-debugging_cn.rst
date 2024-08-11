### 使用GDB调试内核和模块

#### 使用GDB调试内核及模块

Linux 内核调试器 kgdb、像 QEMU 这样的虚拟机监控程序或基于 JTAG 的硬件接口允许在运行时使用 GDB 调试 Linux 内核及其模块。GDB 配备了一个强大的 Python 脚本接口。内核提供了一系列辅助脚本，可以简化典型的内核调试步骤。这是一个简短的教程，介绍如何启用和使用这些脚本。它主要关注以 QEMU/KVM 虚拟机为目标的情况，但示例同样适用于其他 GDB 存根。

#### 要求

- GDB 7.2+（推荐：7.4+）且启用了 Python 支持（通常对于发行版来说是默认开启的）

#### 设置

- 创建一个用于 QEMU/KVM 的虚拟 Linux 机器（更多信息请参见 www.linux-kvm.org 和 www.qemu.org）。对于交叉开发，https://landley.net/aboriginal/bin 提供了可供使用的机器镜像和工具链。
- 使用 CONFIG_GDB_SCRIPTS 选项编译内核，但禁用 CONFIG_DEBUG_INFO_REDUCED。如果架构支持 CONFIG_FRAME_POINTER，则保持启用状态。
- 在虚拟机上安装该内核，必要时通过在内核命令行中添加 "nokaslr" 来禁用 KASLR。
  或者，QEMU 允许直接使用 -kernel、-append 和 -initrd 命令行参数来启动内核。这通常只在不依赖于模块的情况下才有用。有关此模式的更多详细信息，请参阅 QEMU 文档。在这种情况下，如果架构支持 KASLR，则应禁用 CONFIG_RANDOMIZE_BASE。
- 构建 GDB 脚本（从内核版本 v5.1 及更高版本开始需要）：

  ```
  make scripts_gdb
  ```

- 启用 QEMU/KVM 的 GDB 存根，可以通过以下方式之一实现：
  - 在虚拟机启动时，在 QEMU 命令行后追加 "-s"
  - 在运行时通过 QEMU 监控控制台发出 "gdbserver" 命令
- 切换到构建目录 `/path/to/linux-build`
- 启动 GDB：`gdb vmlinux`

  注意：某些发行版可能会限制自动加载 GDB 脚本到已知安全的目录。如果 GDB 报告拒绝加载 vmlinux-gdb.py，可以在 `~/.gdbinit` 文件中添加以下内容：

  ```
  add-auto-load-safe-path /path/to/linux-build
  ```

  更多详细信息，请参阅 GDB 帮助文档。
- 附加到启动的虚拟机：

  ```
  (gdb) target remote :1234
  ```

#### 使用 Linux 提供的 GDB 辅助工具的示例

- 加载模块（以及主内核）符号：

  ```
  (gdb) lx-symbols
  loading vmlinux
  scanning for modules in /home/user/linux/build
  loading @0xffffffffa0020000: /home/user/linux/build/net/netfilter/xt_tcpudp.ko
  loading @0xffffffffa0016000: /home/user/linux/build/net/netfilter/xt_pkttype.ko
  loading @0xffffffffa0002000: /home/user/linux/build/net/netfilter/xt_limit.ko
  loading @0xffffffffa00ca000: /home/user/linux/build/net/packet/af_packet.ko
  loading @0xffffffffa003c000: /home/user/linux/build/fs/fuse/fuse.ko
  ..
  loading @0xffffffffa0000000: /home/user/linux/build/drivers/ata/ata_generic.ko
  ```

- 对尚未加载的模块函数设置断点，例如：

  ```
  (gdb) b btrfs_init_sysfs
  Function "btrfs_init_sysfs" not defined
  Make breakpoint pending on future shared library load? (y or [n]) y
  Breakpoint 1 (btrfs_init_sysfs) pending
  ```

- 继续执行目标：

  ```
  (gdb) c
  ```

- 在目标上加载模块，并观察符号被加载以及断点命中情况：

  ```
  loading @0xffffffffa0034000: /home/user/linux/build/lib/libcrc32c.ko
  loading @0xffffffffa0050000: /home/user/linux/build/lib/lzo/lzo_compress.ko
  loading @0xffffffffa006e000: /home/user/linux/build/lib/zlib_deflate/zlib_deflate.ko
  loading @0xffffffffa01b1000: /home/user/linux/build/fs/btrfs/btrfs.ko

  Breakpoint 1, btrfs_init_sysfs () at /home/user/linux/fs/btrfs/sysfs.c:36
  36              btrfs_kset = kset_create_and_add("btrfs", NULL, fs_kobj);
  ```

- 查看目标内核的日志缓冲区：

  ```
  (gdb) lx-dmesg
  [     0.000000] Initializing cgroup subsys cpuset
  [     0.000000] Initializing cgroup subsys cpu
  [     0.000000] Linux version 3.8.0-rc4-dbg+ (..
  ```
命令行参数：root=/dev/sda2 resume=/dev/sda1 vga=0x314
    [     0.000000] e820: BIOS 提供的物理 RAM 映射:
    [     0.000000] BIOS-e820: [内存 0x0000000000000000-0x000000000009fbff] 可用
    [     0.000000] BIOS-e820: [内存 0x000000000009fc00-0x000000000009ffff] 预留
    ...

- 检查当前任务结构体字段（仅由 x86 和 arm64 支持）:

    (gdb) p $lx_current().pid
    $1 = 4998
    (gdb) p $lx_current().comm
    $2 = "modprobe\000\000\000\000\000\000\000"

- 使用每个 CPU 的函数来获取当前或指定 CPU 的信息:

    (gdb) p $lx_per_cpu("runqueues").nr_running
    $3 = 1
    (gdb) p $lx_per_cpu("runqueues", 2).nr_running
    $4 = 0

- 利用 container_of 辅助函数深入研究高精度定时器:

    (gdb) set $next = $lx_per_cpu("hrtimer_bases").clock_base[0].active.next
    (gdb) p *$container_of($next, "struct hrtimer", "node")
    $5 = {
      node = {
        node = {
          __rb_parent_color = 18446612133355256072,
          rb_right = 0x0 <irq_stack_union>,
          rb_left = 0x0 <irq_stack_union>
        },
        expires = {
          tv64 = 1835268000000
        }
      },
      _softexpires = {
        tv64 = 1835268000000
      },
      function = 0xffffffff81078232 <tick_sched_timer>,
      base = 0xffff88003fd0d6f0,
      state = 1,
      start_pid = 0,
      start_site = 0xffffffff81055c1f <hrtimer_start_range_ns+20>,
      start_comm = "swapper/2\000\000\000\000\000\000"
    }

命令和函数列表
-------------------

随着时间的推移，命令和方便函数的数量可能会有所变化，
以下只是初始版本的一个快照：

(gdb) apropos lx
函数 lx_current -- 返回当前任务
函数 lx_module -- 通过名称查找模块并返回模块变量
函数 lx_per_cpu -- 返回每个 CPU 的变量
函数 lx_task_by_pid -- 通过 PID 查找 Linux 任务并返回 task_struct 变量
函数 lx_thread_info -- 从任务变量计算 Linux thread_info
lx-dmesg -- 打印 Linux 内核日志缓冲区
lx-lsmod -- 列出当前加载的模块
lx-symbols -- （重新）加载 Linux 内核及当前已加载模块的符号

对于命令可以通过 "help <command-name>" 获取详细帮助，对于方便函数则使用 "help function <function-name>"。
