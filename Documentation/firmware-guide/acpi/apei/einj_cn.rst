SPDX 许可证标识符: GPL-2.0

====================
APEI 错误注入 (EINJ)
====================

EINJ 提供了一种硬件错误注入机制。它对于调试和测试 APEI 和 RAS 特性非常有用。
首先需要检查你的 BIOS 是否支持 EINJ。为此，请查找类似于以下内容的早期引导信息：

```
ACPI: EINJ 0x000000007370A000 000150 (v01 INTEL           00000001 INTL 00000001)
```

这表明 BIOS 暴露了一个 EINJ 表，这是进行错误注入的机制。
或者，可以在 `/sys/firmware/acpi/tables` 中查找一个名为 "EINJ" 的文件，这是同一事物的不同表示形式。
如果上述内容不存在，并不一定意味着 EINJ 不受支持：在放弃之前，请进入 BIOS 设置查看 BIOS 是否有启用错误注入的选项。查找类似 WHEA 的选项。通常情况下，你需要先启用 ACPI5 支持选项，才能看到 BIOS 菜单中支持并暴露的 APEI、EINJ 等功能。

要使用 EINJ，请确保内核配置中启用了以下选项：

```
CONFIG_DEBUG_FS
CONFIG_ACPI_APEI
CONFIG_ACPI_APEI_EINJ
```

另外，为了（可选地）启用 CXL 协议错误注入，请设置：

```
CONFIG_ACPI_APEI_EINJ_CXL
```

EINJ 用户界面位于 `<debugfs挂载点>/apei/einj`。以下是属于该接口的文件：

- available_error_type

  此文件显示了哪些错误类型是受支持的：

  ================  ===================================
  错误类型值       错误描述
  ================  ===================================
  0x00000001       处理器可纠正
  0x00000002       处理器不可纠正非致命
  0x00000004       处理器不可纠正致命
  0x00000008       内存可纠正
  0x00000010       内存不可纠正非致命
  0x00000020       内存不可纠正致命
  0x00000040       PCI Express 可纠正
  0x00000080       PCI Express 不可纠正非致命
  0x00000100       PCI Express 不可纠正致命
  0x00000200       平台可纠正
  0x00000400       平台不可纠正非致命
  0x00000800       平台不可纠正致命
  ================  ===================================

  文件内容格式如上所示，但仅列出可用的错误类型。
- error_type

  设置将要注入的错误类型的值。可能的错误类型定义在上面的 `available_error_type` 文件中。
- error_inject

  向此文件写入任何整数以触发错误注入。确保已指定所有必要的错误参数，即此写操作应是注入错误时的最后一步。
- flags

  在内核版本 3.13 及以上版本中存在。用于指定 param{1..4} 中哪些是有效的，并应在注入过程中由固件使用。值是一个位掩码，如 ACPI 5.0 规范中对 SET_ERROR_TYPE_WITH_ADDRESS 数据结构所规定的：

    Bit 0
      处理器 APIC 字段有效（参见下面的 param3）
    Bit 1
      内存地址和掩码有效（param1 和 param2）
位 2
      PCIe (段、总线、设备、功能) 有效（参见下面的参数4）
如果设置为零，则模拟传统行为，其中注入类型仅指定一个位设置，并且参数1是复用的
- 参数1

  该文件用于设置第一个错误参数值。其效果取决于在 `error_type` 中指定的错误类型。例如，如果错误类型与内存相关，则 `参数1` 应是一个有效的物理内存地址。[除非设置了“标志” - 参见上面]

- 参数2

  与 `参数1` 的使用相同。例如，如果错误类型与内存相关，则 `参数2` 应是一个物理内存地址掩码。Linux 要求页面或更细粒度，例如 `0xfffffffffffff000`
- 参数3

  当 “标志” 中的 `0x1` 位被设置时，用于指定 APIC ID。
- 参数4

  当 “标志” 中的 `0x4` 位被设置时，用于指定目标 PCIe 设备。

- notrigger

  错误注入机制是一个两步过程。首先注入错误，然后执行某些操作来触发它。将 “notrigger” 设置为 1 可以跳过触发阶段，这 *可能* 允许用户通过简单访问目标 CPU、内存位置或设备来引发错误。这是否实际起作用取决于 BIOS 实际上在触发阶段中包含的操作。
从 ACPI 6.5 开始支持 CXL 错误类型（前提是存在 CXL 端口）。CXL 错误类型的 EINJ 用户界面位于 `<debugfs 挂载点>/cxl`。以下文件属于它：

- einj_types：

  提供与 `available_error_types` 相同的功能，但针对 CXL 错误类型。

- `$dport_dev/einj_inject`：

  将 CXL 错误类型注入由 `$dport_dev` 表示的 CXL 端口中，其中 `$dport_dev` 是 CXL 端口的名称（通常是 PCIe 设备名称）。
针对 CXL 2.0+ 端口的错误注入可以使用 `<debugfs 挂载点>/apei/einj` 下的传统接口，而 CXL 1.1/1.0 端口的注入必须使用此文件。
基于 ACPI 4.0 规范的 BIOS 在控制错误注入位置方面有有限的选择。您的 BIOS 可能支持扩展（通过模块参数 `param_extension=1` 或引导命令行 `eij.param_extension=1` 启用）。这允许通过 `apei/einj` 中的 `参数1` 和 `参数2` 文件指定内存注入的地址和掩码。
基于 ACPI 5.0 规范的 BIOS 对注入目标有更多的控制权。对于处理器相关的错误（类型 0x1、0x2 和 0x4），您可以将标志设置为 `0x3`（`参数3` 用于位 0，`参数1` 和 `参数2` 用于位 1），以便在注入的错误签名中添加更多详细信息。实际传递的数据如下所示：

    memory_address = 参数1；
    memory_address_range = 参数2；
    apicid = 参数3；
    pcie_sbdf = 参数4；

对于内存错误（类型 0x8、0x10 和 0x20），地址使用 `参数1` 设置，掩码在 `参数2` 中指定（`0x0` 等同于全 1）。对于 PCI Express 错误（类型 0x40、0x80 和 0x100），段、总线、设备和功能使用 `参数1` 指定：

         31     24 23    16 15    11 10      8  7        0
	+-------------------------------------------------+
	| 段 | 总线  | 设备 | 功能 | 保留 |
	+-------------------------------------------------+

无论如何，您应该明白了，如果有疑问，请查看 `drivers/acpi/apei/einj.c` 中的代码。
ACPI 5.0 BIOS 还可能允许注入供应商特定的错误。
在这种情况下，一个名为 `vendor` 的文件将包含来自 BIOS 的识别信息，这些信息有望让希望使用特定供应商扩展的应用程序能够识别出它们正在运行的 BIOS 支持该扩展。所有供应商扩展的 `error_type` 中都设置了 `0x80000000` 位。一个名为 `vendor_flags` 的文件控制了 `param1` 和 `param2` 的解释（1 = PROCESSOR，2 = MEMORY，4 = PCI）。详情请参阅您的 BIOS 供应商文档（并预计如果供应商在使用此功能方面的创造力超出我们的预期，则此 API 可能会有所变化）。

错误注入示例：

```
# cd /sys/kernel/debug/apei/einj
# cat available_error_type       # 查看可以注入的错误类型
0x00000002  Processor Uncorrectable non-fatal
0x00000008  Memory Correctable
0x00000010  Memory Uncorrectable non-fatal
# echo 0x12345000 > param1      # 设置注入内存地址
# echo 0xfffffffffffff000 > param2  # 遮罩 - 此页面中的任何位置
# echo 0x8 > error_type          # 选择可校正内存错误
# echo 1 > error_inject          # 立即注入
```

您应该在 `dmesg` 中看到类似这样的输出：

```
[22715.830801] EDAC sbridge MC3: HANDLING MCE MEMORY ERROR
[22715.834759] EDAC sbridge MC3: CPU 0: Machine Check Event: 0 Bank 7: 8c00004000010090
[22715.834759] EDAC sbridge MC3: TSC 0
[22715.834759] EDAC sbridge MC3: ADDR 12345000 EDAC sbridge MC3: MISC 144780c86
[22715.834759] EDAC sbridge MC3: PROCESSOR 0:306e7 TIME 1422553404 SOCKET 0 APIC 0
[22716.616173] EDAC MC3: 1 CE memory read error on CPU_SrcID#0_Channel#0_DIMM#0 (channel:0 slot:0 page:0x12345 offset:0x0 grain:32 syndrome:0x0 -  area:DRAM err_code:0001:0090 socket:0 channel_mask:1 rank:0)
```

CXL 错误注入示例，其中 `$dport_dev=0000:e0:01.1`：

```
# cd /sys/kernel/debug/cxl/
# ls
0000:e0:01.1 0000:0c:00.0
# cat einj_types              # 查看可以注入的错误类型
0x00008000  CXL.mem Protocol Correctable
0x00010000  CXL.mem Protocol Uncorrectable non-fatal
0x00020000  CXL.mem Protocol Uncorrectable fatal
# cd 0000:e0:01.1             # 导航到要注入的 dport
# echo 0x8000 > einj_inject   # 注入错误
```

向 SGX 隔离区注入的特别说明：

可能有一个单独的 BIOS 设置选项来启用 SGX 注入。
注入过程包括设置某些特殊的内存控制器触发器，以便在下次写入目标地址时注入错误。但硬件阻止任何软件（甚至 BIOS SMM 模式）访问 SGX 隔离区内的页面。
以下序列可以使用：
1) 确定隔离区页面的物理地址。
2) 使用 "notrigger=1" 模式注入（这将设置注入地址，但实际上不会注入）。
3) 进入隔离区。
4) 将数据存储到与步骤 1 中的物理地址匹配的虚拟地址。
5) 对该虚拟地址执行 CLFLUSH。
6) 延迟 250 毫秒。
7) 从虚拟地址读取。这将触发错误。

有关 EINJ 的更多信息，请参阅 ACPI 规范版本 4.0 第 17.5 节和 ACPI 5.0 第 18.6 节。
