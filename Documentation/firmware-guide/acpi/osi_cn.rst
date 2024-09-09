... SPDX 许可证标识符: GPL-2.0

==========================
ACPI _OSI 和 _REV 方法
==========================

ACPI BIOS 可以使用“操作系统接口”方法 (_OSI) 来了解操作系统支持哪些功能。例如，如果 BIOS 的 AML 代码包含 _OSI("XYZ")，内核的 AML 解释器可以评估该方法，查看是否支持 'XYZ' 并向 BIOS 回答 YES 或 NO。
ACPI _REV 方法返回 “OSPM 支持的 ACPI 规范版本”。

本文档解释了 BIOS 和 Linux 应该如何以及为什么使用这些方法，并解释了它们被广泛误用的方式。

如何使用 _OSI
===============

Linux 运行在两类机器上 —— 那些经过 OEM 测试与 Linux 兼容的机器，以及那些从未经过 Linux 测试但安装了 Linux 替代原始操作系统（如 Windows 或 OSX）的机器。
更大的一组是仅测试运行 Windows 的系统。不仅如此，许多系统只测试过与一个特定版本的 Windows 兼容。
因此，尽管 BIOS 可能会使用 _OSI 查询正在运行的 Windows 版本，但实际上只有一条路径通过 BIOS 被测试过。
经验表明，通过未经测试的 BIOS 路径会使 Linux 暴露于一整类 BIOS 错误中。
出于这个原因，Linux _OSI 默认设置必须继续声称与所有版本的 Windows 兼容。
但是 Linux 实际上并不兼容 Windows，并且当 Linux 将最新版本的 Windows 添加到其 _OSI 字符串列表时，Linux 社区也遭受了退步问题。
因此，将来可能会对添加的字符串进行更严格的验证后再将其合并到上游。
但最终它们可能都会被添加。
如果OEM厂商希望使用同一BIOS镜像来支持Linux和Windows，他们通常需要为Linux做一些不同的事情，以应对Linux与Windows之间的差异。在这种情况下，OEM厂商应创建由Linux内核执行的自定义ACPI系统语言（ASL）代码，并对Linux内核驱动进行修改以执行这些自定义ASL代码。最简单的方法是引入一个设备特定方法（_DSM），该方法可以从Linux内核中调用。

在过去，内核支持过类似以下的机制：
_OSI("Linux-OEM-my_interface_name")
其中，“OEM”表示这是一个特定于OEM的钩子，“my_interface_name”描述了这个钩子，可能是某个特性、漏洞或修复。

然而，这种方法被其他BIOS供应商滥用，在完全不相关的系统上更改完全不相关的代码。这促使了对所有用途的重新评估，发现它们实际上并不需要用于任何原始目的。因此，默认情况下，内核不会响应任何自定义的Linux-*字符串。

在_OSI之前，还有_OSD。
==========================

ACPI 1.0规范指定了“_OS”，将其定义为“评估为标识操作系统的字符串的对象”。

ACPI BIOS流程会包括对_OSD的评估，内核中的ACPI机器语言（AML）解释器会返回一个标识操作系统的字符串：

Windows 98, SE: "Microsoft Windows"
Windows ME: "Microsoft WindowsME:Millennium Edition"
Windows NT: "Microsoft Windows NT"

其初衷是在需要运行多个操作系统的平台上，BIOS可以利用_OSD来启用操作系统可能支持的设备，或者启用必要的特性或漏洞修复，使平台兼容这些现有的操作系统。

但是_OSD存在根本性问题。首先，BIOS需要知道在其上运行的所有可能的操作系统版本名称，并且需要了解这些操作系统的所有特性。显然，更合理的方法是由BIOS向操作系统询问具体的功能，例如“是否支持某个特定接口”。因此，在ACPI 3.0中，_OSI诞生以取代_OSD。

_OSD被废弃了，但即使今天，许多BIOS仍然寻找_OSD "Microsoft Windows NT"，尽管安装那些旧操作系统的可能性似乎不大。

Linux回答“Microsoft Windows NT”是为了满足这种BIOS惯例。这是唯一可行的策略，因为现代Windows也是这样做的，否则可能会导致BIOS进入未经测试的路径。
_OSI 诞生，并立即被误用
=====================================

通过 _OSI，*BIOS* 提供描述接口的字符串，并询问操作系统：“是/否，你是否兼容这个接口？”

例如，_OSI("3.0 热模型") 如果操作系统知道如何处理 ACPI 3.0 规范中所做的热扩展，则会返回 TRUE。旧的操作系统如果不知道这些扩展则会回答 FALSE，而新的操作系统可能能够返回 TRUE。

对于特定于操作系统的接口，ACPI 规范规定 BIOS 和操作系统应该就类似 "Windows-interface_name" 形式的字符串达成一致。
但两件糟糕的事情发生了。首先，Windows 生态系统没有按照设计使用 _OSI，而是将其作为 _OS 的直接替代品——识别操作系统版本，而不是操作系统支持的接口。实际上，从一开始，ACPI 3.0 规范本身就在示例代码中将这种误用编入了代码，使用了 _OSI("Windows 2001")。
这种误用被采纳并一直延续至今。
Linux 别无选择，也必须对 _OSI("Windows 2001") 及其后续版本返回 TRUE。否则几乎可以肯定会导致那些仅在 _OSI 返回 TRUE 的情况下进行测试的 BIOS 出现问题。
这一策略存在问题，因为 Linux 从未完全兼容最新版本的 Windows，有时需要一年多的时间来解决不兼容的问题。
不甘落后，Linux 社区通过返回 _OSI("Linux") 的 TRUE 值使情况变得更糟。这样做比 Windows 对 _OSI 的误用更糟糕，因为 "Linux" 甚至不包含任何版本信息。
_OSI("Linux") 导致一些 BIOS 因 BIOS 编写者未经过测试的 BIOS 流程而出错。但是有些 OEM 在经过测试的流程中使用 _OSI("Linux") 来支持真正的 Linux 特性。2009 年，Linux 移除了 _OSI("Linux")，并添加了一个命令行参数来为仍然需要它的遗留系统恢复它。此外，所有调用它的 BIOS 都会打印 BIOS_BUG 警告。
任何 BIOS 都不应使用 _OSI("Linux")。
结果是为 Linux 制定了一种策略，以最大限度地与在 Windows 机器上测试过的 ACPI BIOS 兼容。存在过度强调这种兼容性的风险；但替代方案往往是灾难性的失败，因为 BIOS 会采取从未在任何操作系统下验证过的路径。

自 `_OSI("Linux")` 被移除后，一些 BIOS 开发者使用 `_REV` 来在同一 BIOS 中支持 Linux 和 Windows 的差异。`_REV` 在 ACPI 1.0 中被定义为返回操作系统支持的 ACPI 版本和操作系统 AML 解释器的版本。现代 Windows 返回 `_REV = 2`。Linux 使用 `ACPI_CA_SUPPORT_LEVEL`，该值会根据所支持的规范版本递增。不幸的是，`_REV` 也被误用。例如，某些 BIOS 会检查 `_REV = 3` 并为 Linux 执行某些操作，但当 Linux 返回 `_REV = 4` 时，这种支持就失效了。

为了解决这个问题，从 2015 年中期开始，Linux 总是返回 `_REV = 2`。ACPI 规范也将更新，表明 `_REV` 已被弃用，并总是返回 2。

苹果 Mac 和 `_OSI("Darwin")`
==============================

在苹果的 Mac 平台上，ACPI BIOS 会调用 `_OSI("Darwin")` 来确定机器是否运行着苹果的 macOS 系统。类似于 Linux 的 `_OSI("*Windows*")` 策略，Linux 默认回答 `_OSI("Darwin")` 为 YES，以启用对硬件的完全访问以及 macOS 下经过验证的 BIOS 路径。

就像在 Windows 测试平台上一样，这种策略也存在风险。从 Linux-3.18 开始，内核对 `_OSI("Darwin")` 回答为 YES，以启用 Mac 的 Thunderbolt 支持。此外，如果内核检测到 `_OSI("Darwin")` 被调用，它还会禁用所有 `_OSI("*Windows*")`，以防止编写不当的 Mac BIOS 进入未经测试的路径组合。
Linux-3.18 默认设置的更改导致了 Mac 笔记本电脑上的功耗回归，而且 3.18 的实现不允许通过命令行 "acpi_osi=!Darwin" 来更改默认设置。Linux-4.7 修复了使用 acpi_osi=!Darwin 作为变通方法的能力，我们希望在 Linux-4.11 中看到对 Mac 雷电（Thunderbolt）电源管理的支持。
