### SPDX 许可证标识符：GPL-2.0

#### 早期打印说明

这是一个简要教程，介绍如何在x86系统上使用earlyprintk=dbgp启动选项与USB2调试端口密钥和调试线缆。您需要两台计算机、特殊的“USB调试密钥”设备以及两条USB线缆，连接方式如下所示：

```
[主机/目标] <-------> [USB调试密钥] <-------> [客户端/控制台]
```

##### 硬件要求

1. **主机/目标系统需要具备USB调试端口功能**  
   您可以通过检查`lspci -vvv`输出中的“调试端口”位来确认此功能：
   ```shell
   # lspci -vvv
   ..
   00:1d.7 USB 控制器: Intel Corporation 82801H (ICH8 家族) USB2 EHCI 控制器 #1 (rev 03) (prog-if 20 [EHCI])
                 子系统: Lenovo ThinkPad T61
                 控制: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR+ FastB2B- DisINTx-
                 状态: Cap+ 66MHz- UDF- FastB2B+ ParErr- DEVSEL=中等 >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
                 延迟: 0
                 中断: 针脚 D 连接到 IRQ 19
                 区域 0: 内存位于 fe227000 (32 位, 非预取) [大小 = 1K]
                 功能: [50] 电源管理版本 2
                       标志: PMEClk- DSI- D1- D2- 辅助电流 = 375mA PME(D0+,D1-,D2-,D3hot+,D3cold+)
                       状态: D0 PME-启用- DSel=0 DScale=0 PME+
                 功能: [58] 调试端口: BAR=1 偏移 = 00a0
                              ^^^^^^^^^^^ <==================== [ 在这里 ]
                 使用的内核驱动程序: ehci_hcd
                 内核模块: ehci-hcd
   ..
   ```

   **注意:** 如果您的系统没有列出调试端口功能，则可能无法使用USB调试密钥。

2. **您还需要一个NetChip USB调试线缆/密钥**  
   可以从以下网址获取:
   ```
   http://www.plxtech.com/products/NET2000/NET20DC/default.asp
   ```
   这是一个带有两个USB接口的小型蓝色塑料连接器；它通过其USB接口供电。
   
3. **您需要第二台用作客户端/控制台的系统，并且该系统需要有高速USB 2.0端口**  
   
4. **NetChip设备必须直接插入“主机/目标”系统的物理调试端口中。不能在物理调试端口与“主机/目标”系统之间使用USB集线器。**
   EHCI调试控制器绑定到特定的物理USB端口，而NetChip设备仅在此端口中作为早期打印设备工作。EHCI主机控制器在电气上被设计为EHCI调试控制器连接到第一个物理端口，并且无法通过软件更改这一点。
   
   您可以通过实验找到物理端口，即尝试系统上的每个物理端口并重新启动。或者，您可以尝试使用`lsusb`或查看当您将USB设备插入“主机/目标”系统的各种端口时由USB堆栈发出的内核信息消息。
一些硬件供应商并未通过物理连接器公开 USB 调试端口，如果你遇到这样的设备，请向硬件供应商提出投诉，因为没有理由不将此端口连接到一个物理可访问的端口上。

e) 还需要指出的是，许多版本的 NetChip 设备要求“客户端/控制台”系统必须插入设备的右侧（当产品标志面向上并从左至右可读时）。原因是5伏电源仅从设备的一侧获取，并且这一侧不能被重启。

软件需求
=========

a) 在主机/目标系统上：

    您需要启用以下内核配置选项：

      CONFIG_EARLY_PRINTK_DBGP=y

    并且您需要添加启动命令行："earlyprintk=dbgp"
.. note::
      如果您使用的是 Grub，将其附加到 /etc/grub.conf 中的 'kernel' 行。如果您在基于 BIOS 固件的系统上使用 Grub2，则将其附加到 /boot/grub2/grub.cfg 中的 'linux' 行。如果您在基于 EFI 固件的系统上使用 Grub2，则将其附加到 /boot/grub2/grub.cfg 或 /boot/efi/EFI/<distro>/grub.cfg 中的 'linux' 或 'linuxefi' 行。
在具有多个 EHCI 调试控制器的系统上，您必须指定正确的 EHCI 调试控制器编号。EHCIs 控制器的顺序来自于 PCI 总线枚举。默认情况下，不带数字参数的默认值是 "0" 或第一个 EHCI 调试控制器。要使用第二个 EHCI 调试控制器，您可以使用命令行："earlyprintk=dbgp1"

    .. note::
      通常，在常规控制台启动后，早期打印控制台会被关闭 - 使用 "earlyprintk=dbgp,keep" 可以保持此通道在早期引导之后仍然打开。这对于调试 Xorg 下的崩溃等问题非常有用。
b) 在客户端/控制台系统上：

    您应该启用以下内核配置选项：

      CONFIG_USB_SERIAL_DEBUG=y

    使用修改后的内核重新启动后，您应该会得到一个 /dev/ttyUSBx 设备。
现在这个内核消息通道已经准备好使用：启动您最喜欢的终端仿真器（如 minicom 等）并设置它以使用 /dev/ttyUSB0 - 或者使用原始的 'cat /dev/ttyUSBx' 来查看原始输出。
c) 对于基于 Nvidia 南桥的系统：内核将尝试探测并找出哪个端口连接了调试设备。

测试
====

您可以通过使用 earlyprintk=dbgp,keep 并在主机/目标系统上触发内核消息来测试输出。例如，可以通过执行以下操作来触发一个无害的内核消息：

     echo h > /proc/sysrq-trigger

在主机/目标系统上，您应该在 "dmesg" 输出中看到以下帮助行：

     SysRq : HELP : loglevel(0-9) reBoot Crashdump terminate-all-tasks(E) memory-full-oom-kill(F) kill-all-tasks(I) saK show-backtrace-all-active-cpus(L) show-memory-usage(M) nice-all-RT-tasks(N) powerOff show-registers(P) show-all-timers(Q) unRaw Sync show-task-states(T) Unmount show-blocked-tasks(W) dump-ftrace-buffer(Z)

在客户端/控制台系统上执行：

       cat /dev/ttyUSB0

您应该会在主机系统上触发帮助行后不久，在此显示该帮助行。
如果不起作用，请在 linux-kernel@vger.kernel.org 邮件列表上询问或联系 x86 维护者。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
