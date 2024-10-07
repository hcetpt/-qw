SPDX 许可证标识符: GPL-2.0

=====================
AdvanSys 驱动程序说明
=====================

AdvanSys（Advanced System Products, Inc.）制造了以下基于 RISC 的总线主控、快速（10 MHz）和超速（20 MHz）窄带（8位传输）SCSI 主机适配器，适用于 ISA、EISA、VL 和 PCI 总线，并且还制造了基于 RISC 的总线主控、超速（20 MHz）宽带（16位传输）SCSI 主机适配器，适用于 PCI 总线。

下面的 CDB 数值表示可以存储在 RISC 芯片缓存和板载 LRAM 中的 SCSI 命令描述块（CDB）请求的数量。一个 CDB 是一个单一的 SCSI 命令。驱动程序检测例程将显示每个检测到的适配器可用的 CDB 数量。可以通过更改 BIOS 中的“主机队列大小”适配器设置来降低驱动程序使用的 CDB 数量。

笔记本产品：
  - ABP-480 - 总线主控 CardBus（16个 CDB）

连接性产品：
   - ABP510/5150 - 总线主控 ISA（240个 CDB）
   - ABP5140 - 总线主控 ISA PnP（16个 CDB）
   - ABP5142 - 总线主控 ISA PnP 带软驱（16个 CDB）
   - ABP902/3902 - 总线主控 PCI（16个 CDB）
   - ABP3905 - 总线主控 PCI（16个 CDB）
   - ABP915 - 总线主控 PCI（16个 CDB）
   - ABP920 - 总线主控 PCI（16个 CDB）
   - ABP3922 - 总线主控 PCI（16个 CDB）
   - ABP3925 - 总线主控 PCI（16个 CDB）
   - ABP930 - 总线主控 PCI（16个 CDB）
   - ABP930U - 总线主控 PCI 超速（16个 CDB）
   - ABP930UA - 总线主控 PCI 超速（16个 CDB）
   - ABP960 - 总线主控 PCI MAC/PC（16个 CDB）
   - ABP960U - 总线主控 PCI MAC/PC 超速（16个 CDB）

单通道产品：
   - ABP542 - 总线主控 ISA 带软驱（240个 CDB）
   - ABP742 - 总线主控 EISA（240个 CDB）
   - ABP842 - 总线主控 VL（240个 CDB）
   - ABP940 - 总线主控 PCI（240个 CDB）
   - ABP940U - 总线主控 PCI 超速（240个 CDB）
   - ABP940UA/3940UA - 总线主控 PCI 超速（240个 CDB）
   - ABP970 - 总线主控 PCI MAC/PC（240个 CDB）
   - ABP970U - 总线主控 PCI MAC/PC 超速（240个 CDB）
   - ABP3960UA - 总线主控 PCI MAC/PC 超速（240个 CDB）
   - ABP940UW/3940UW - 总线主控 PCI 超宽（253个 CDB）
   - ABP970UW - 总线主控 PCI MAC/PC 超宽（253个 CDB）
   - ABP3940U2W - 总线主控 PCI LVD/超速2宽（253个 CDB）

多通道产品：
   - ABP752 - 双通道总线主控 EISA（每通道240个 CDB）
   - ABP852 - 双通道总线主控 VL（每通道240个 CDB）
   - ABP950 - 双通道总线主控 PCI（每通道240个 CDB）
   - ABP950UW - 双通道总线主控 PCI 超宽（每通道253个 CDB）
   - ABP980 - 四通道总线主控 PCI（每通道240个 CDB）
   - ABP980U - 四通道总线主控 PCI 超速（每通道240个 CDB）
   - ABP980UA/3980UA - 四通道总线主控 PCI 超速（每通道16个 CDB）
   - ABP3950U2W - 总线主控 PCI LVD/超速2宽和超宽（253个 CDB）
   - ABP3950U3W - 总线主控 PCI 双 LVD2/超速3宽（253个 CDB）

驱动程序编译时选项和调试
=========================================

可以在源文件中定义以下常量：
1. ADVANSYS_ASSERT - 启用驱动断言（默认：启用）

   启用此选项会向驱动程序中添加断言逻辑语句。如果断言失败，将在控制台上显示一条消息，但系统将继续运行。任何遇到的断言都应报告给负责驱动程序的人。断言语句可能会主动检测驱动程序中的问题并有助于修复这些问题。启用断言会增加驱动程序执行的小开销。
2. ADVANSYS_DEBUG - 启用驱动调试（默认：禁用）

   启用此选项会在驱动程序中添加跟踪函数，并且可以在启动时设置驱动程序跟踪级别。此选项对于调试驱动程序非常有用，但它会增加驱动程序执行映像的大小并增加驱动程序执行的开销。

调试输出的数量可以通过全局变量 'asc_dbglvl' 控制。数值越高，输出越多，默认调试级别为 0。

如果驱动程序在启动时加载并且系统中包含 LILO 驱动程序选项，则可以通过指定第五个（ASC_NUM_IOPORT_PROBE + 1）I/O 端口来更改调试级别。伪 I/O 端口的前三个十六进制数字必须设置为 'deb'，第四个十六进制数字指定调试级别：0 - F。

以下命令行将在 0x330 寻找适配器并设置调试级别为 2：

      linux advansys=0x330,0,0,0,0xdeb2

   如果驱动程序作为可加载模块构建，可以在加载驱动程序时定义此变量。以下 insmod 命令将调试级别设置为 1：

      insmod advansys.o asc_dbglvl=1

   调试消息级别：

      ==== ==================
      0    仅错误
      1    高级跟踪
      2-N  详细跟踪
      ==== ==================

   若要启用控制台上的调试输出，请确保：

   a. 系统和内核日志记录已启用（syslogd、klogd 运行）
   b. 内核消息被路由到控制台输出。检查 /etc/syslog.conf 是否有类似于此的条目：

           kern.*                  /dev/console

   c. 使用适当的 -c 参数启动 klogd（例如 klogd -c 8）

   这将导致 printk() 消息显示在当前控制台上。详情请参阅 klogd(8) 和 syslogd(8) 手册页。
   
   或者，您可以使用此程序启用 printk() 到控制台。但是，这不是官方的做法。
调试输出记录在 `/var/log/messages` 中：

```c
main()
{
        syscall(103, 7, 0, 0);
}
```

将 `kernel/printk.c` 中的 `LOG_BUF_LEN` 增加到类似 40960 的值，可以允许更多的调试信息被内核缓冲，并写入控制台或日志文件。

3. ADVANSYS_STATS - 启用统计（默认：启用）

启用此选项会通过 `/proc` 添加统计收集和显示功能到驱动程序。这些信息对于监控驱动程序和设备性能非常有用。它会增加驱动程序执行映像的大小，并给驱动程序的执行带来轻微的开销。
统计信息是按适配器维护的。维护了驱动程序入口点调用次数和传输大小计数。
统计信息仅适用于大于等于 v1.3.0 并配置了 `CONFIG_PROC_FS`（`/proc` 文件系统）的内核。
AdvanSys SCSI 适配器文件具有以下路径格式：
```
/proc/scsi/advansys/{0,1,2,3,...}
```
这些信息可以用 `cat` 显示。例如：
```
cat /proc/scsi/advansys/0
```
当 `ADVANSYS_STATS` 未定义时，AdvanSys 的 `/proc` 文件中只包含适配器和设备的配置信息。

### 驱动程序 LILO 选项

如果按照“添加AdvanSys驱动程序到Linux”的部分（B.4）修改了 `init/main.c`，则驱动程序将识别 `advansys` LILO 命令行和 `/etc/lilo.conf` 选项。
此选项可用于禁用 I/O 端口扫描或限制扫描范围为 1-4 个 I/O 端口。无论选项设置如何，EISA 和 PCI 板卡仍会被搜索并检测。此选项仅影响 ISA 和 VL 板卡的搜索。

示例：
1. 禁用 I/O 端口扫描：
   ```
   boot::
       linux advansys=
   ```
   或者：
   ```
   boot::
       linux advansys=0x0
   ```

2. 限制 I/O 端口扫描到一个 I/O 端口：
   ```
   boot::
       linux advansys=0x110
   ```

3. 限制 I/O 端口扫描到四个 I/O 端口：
   ```
   boot::
       linux advansys=0x110,0x210,0x230,0x330
   ```

对于可加载模块，可以通过在加载驱动程序时设置 `asc_iopflag` 变量和 `asc_ioport` 数组来实现相同的效果，例如：
```
insmod advansys.o asc_iopflag=1 asc_ioport=0x110,0x330
```

如果定义了 `ADVANSYS_DEBUG`，可以添加第五个（`ASC_NUM_IOPORT_PROBE + 1`）I/O 端口以指定驱动程序的调试级别。有关更多信息，请参阅上面的“驱动程序编译时选项和调试”部分。

### 致谢（按时间顺序）

Bob Frey <bfrey@turbolinux.com.cn> 编写了 AdvanSys SCSI 驱动程序，并维护到了 3.3F 版本。他继续回答问题并帮助维护该驱动程序。
Nathan Hartwell <mage@cdc3.cdc.net> 提供了针对 Linux v1.3.X 变更的指导和基础，这些变更被包含在 1.2 版本中。

Thomas E Zerucha <zerucha@shell.portal.com> 指出了 advansys_biosparam() 中的一个 bug，并在 1.3 版本中修复了该 bug。

Erik Ratcliffe <erik@caldera.com> 在 Caldera 发布版中测试了 AdvanSys 驱动程序。

Rik van Riel <H.H.vanRiel@fys.ruu.nl> 提供了一个针对 AscWaitTixISRDone() 的补丁，他发现这个补丁对于使驱动程序与 SCSI-1 磁盘兼容是必要的。

Mark Moran <mmoran@mmoran.com> 帮助测试了 3.1A 驱动程序中的 Ultra-Wide 支持。

Doug Gilbert <dgilbert@interlog.com> 对驱动程序进行了改进并提出了建议，并进行了大量测试。

Ken Mort <ken@mort.net> 报告了一个在 3.2K 中已修复的 DEBUG 编译 bug。

Tom Rini <trini@kernel.crashing.org> 提供了 CONFIG_ISA 补丁，并帮助处理了 PowerPC 宽板和窄板的支持。

Philip Blundell <philb@gnu.org> 提供了一个 advansys_interrupts_enabled 补丁。

Dave Jones <dave@denial.force9.co.uk> 报告了当 3.2M 驱动程序中未定义 CONFIG_PROC_FS 时生成的编译器警告。
杰瑞·奎因 <jlquinn@us.ibm.com> 修复了 PowerPC 平台对宽卡的支持（字节序问题）
布赖恩·亨德森 <bryanh@giraffe-data.com> 帮助调试了窄卡错误处理
曼努埃尔·维洛索 <veloso@pobox.com> 在 PowerPC 窄板支持方面做了大量工作，并修复了 AscGetEEPConfig() 中的一个 bug
阿纳尔多·卡瓦略·德梅洛 <acme@conectiva.com.br> 进行了 save_flags/restore_flags 的修改
安迪·凯尔纳 <AKellner@connectcom.net> 继续为 ConnectCom 开发 Advansys SCSI 驱动（版本 > 3.3F）
肯·威瑟罗 在开发 3.4 版本期间进行了广泛的测试
