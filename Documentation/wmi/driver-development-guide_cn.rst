SPDX 许可证标识符: GPL-2.0 或更高版本

============================
WMI 驱动开发指南
============================

WMI 子系统提供了一个丰富的驱动 API，用于实现 WMI 驱动，具体文档位于 `Documentation/driver-api/wmi.rst`。本文档将作为使用此 API 编写 WMI 驱动程序的入门指南。它旨在替代最初关于使用已弃用的基于 GUID 的 WMI 接口的 LWN 文章 [1]_。

获取 WMI 设备信息
--------------------------------

在开发 WMI 驱动之前，必须获取有关要处理的 WMI 设备的信息。可以使用 `lswmi <https://pypi.org/project/lswmi>`_ 工具通过以下命令提取详细的 WMI 设备信息：

::

  lswmi -V

输出结果将包含给定机器上所有可用 WMI 设备的信息以及一些额外信息。

为了进一步了解与 WMI 设备通信所使用的接口，可以使用 `bmfdec <https://github.com/pali/bmfdec>`_ 工具来解码描述 WMI 设备的二进制 MOF（管理对象格式）信息。
`wmi-bmof` 驱动程序向用户空间公开了这些信息，详见 `Documentation/wmi/devices/wmi-bmof.rst`。

为了检索解码后的二进制 MOF 信息，请使用以下命令（需要 root 权限）：

::

  ./bmf2mof /sys/bus/wmi/devices/05901221-D566-11D1-B2F0-00A0C9062910[-X]/bmof

有时，查看描述 WMI 设备所用的反汇编 ACPI 表格有助于理解 WMI 设备的工作原理。可以通过上述 `lswmi` 工具获取与特定 WMI 设备关联的 ACPI 方法路径。

基本 WMI 驱动结构
--------------------------

基本的 WMI 驱动围绕 `struct wmi_driver` 构建，并通过 `struct wmi_device_id` 表绑定到匹配的 WMI 设备：

::

  static const struct wmi_device_id foo_id_table[] = {
         { "936DA01F-9ABD-4D9D-80C7-02AF85C822A8", NULL },
         { }
  };
  MODULE_DEVICE_TABLE(wmi, foo_id_table);

  static struct wmi_driver foo_driver = {
        .driver = {
                .name = "foo",
                .probe_type = PROBE_PREFER_ASYNCHRONOUS,        /* 推荐 */
                .pm = pm_sleep_ptr(&foo_dev_pm_ops),            /* 可选 */
        },
        .id_table = foo_id_table,
        .probe = foo_probe,
        .remove = foo_remove,         /* 可选，推荐使用 devres */
        .notify = foo_notify,         /* 可选，用于事件处理 */
        .no_notify_data = true,       /* 可选，启用不包含附加数据的事件 */
        .no_singleton = true,         /* 新 WMI 驱动程序必需 */
  };
  module_wmi_driver(foo_driver);

`probe()` 回调函数会在 WMI 驱动程序与匹配的 WMI 设备绑定时被调用。通常在此函数中分配驱动程序特定的数据结构并初始化与其他内核子系统的接口。

`remove()` 回调函数会在 WMI 驱动程序与 WMI 设备解除绑定时被调用。为了注销与其他内核子系统的接口并释放资源，建议使用 `devres`。
这简化了 `probe` 过程中的错误处理，并且通常允许省略此回调函数，详细信息请参见 `Documentation/driver-api/driver-model/devres.rst`。

请注意，新的 WMI 驱动程序必须能够多次实例化，并且禁止使用任何已弃用的基于 GUID 的 WMI 函数。这意味着 WMI 驱动程序应准备好应对给定机器上存在多个匹配的 WMI 设备的情况。

因此，WMI 驱动程序应使用 `Documentation/driver-api/driver-model/design-patterns.rst` 中描述的状态容器设计模式。
WMI 方法驱动程序
------------------

WMI 驱动程序可以使用 `wmidev_evaluate_method()` 调用 WMI 设备方法。传递给此函数的 ACPI 缓冲区结构是设备特定的，通常需要一些调整才能正确工作。查看包含 WMI 设备的 ACPI 表通常是很有帮助的。传递给此函数的方法 ID 和实例编号也是设备特定的，查看解码后的二进制 MOF 通常足以找到正确的值。最大实例编号可以在运行时通过 `wmidev_instance_count()` 获取。请参阅 `drivers/platform/x86/inspur_platform_profile.c` 以获取一个示例 WMI 方法驱动程序。

WMI 数据块驱动程序
----------------------

WMI 驱动程序可以使用 `wmidev_block_query()` 查询 WMI 设备的数据块。返回的 ACPI 对象结构同样是设备特定的。某些 WMI 设备还允许使用 `wmidev_block_set()` 设置数据块。最大实例编号也可以使用 `wmidev_instance_count()` 获取。请参阅 `drivers/platform/x86/intel/wmi/sbl-fw-update.c` 以获取一个示例 WMI 数据块驱动程序。

WMI 事件驱动程序
-----------------

WMI 驱动程序可以通过在 `struct wmi_driver` 中的 `notify()` 回调函数接收 WMI 事件。WMI 子系统会负责相应地设置 WMI 事件。请注意，传递给此回调函数的 ACPI 对象结构是设备特定的，并且释放 ACPI 对象是由 WMI 子系统完成的，而不是由驱动程序完成的。WMI 驱动程序核心会确保 `notify()` 回调函数仅在 `probe()` 回调函数被调用后才被调用，并且在调用其 `remove()` 回调函数前后不会接收到任何事件。然而，WMI 驱动程序开发者应该意识到可能会同时接收到多个 WMI 事件，因此如果有必要的话，任何锁定机制需要由 WMI 驱动程序本身提供。
为了能够接收不包含任何额外事件数据的WMI事件，`struct wmi_driver`中的`no_notify_data`标志应设置为`true`。请参阅`drivers/platform/x86/xiaomi-wmi.c`以获取一个示例WMI事件驱动程序。

处理多个WMI设备
---------------------

许多固件供应商使用多个WMI设备来控制单个物理设备的不同方面。这使得开发WMI驱动程序变得复杂，因为这些驱动程序可能需要相互通信以向用户空间提供统一的接口。例如，当接收到WMI事件时，一个WMI事件设备可能需要与WMI数据块设备或WMI方法设备进行通信。在这种情况下，应开发两个WMI驱动程序，一个用于WMI事件设备，另一个用于其他WMI设备。

WMI事件设备驱动程序只有一个目的：接收WMI事件、验证任何附加的事件数据并调用通知链。另一个WMI驱动程序在探测过程中加入此通知链，从而每次接收到WMI事件时都会被通知。这个WMI驱动程序可能会进一步处理事件，例如通过输入设备。

对于其他WMI设备组合，可以使用类似的机制。

应避免的事情
---------------------

在开发WMI驱动程序时，应避免以下几点：

- 使用已废弃的基于GUID的WMI接口（该接口使用GUID而不是WMI设备结构）
- 在与WMI设备通信时绕过WMI子系统
- 不能多次实例化的WMI驱动程序

许多较旧的WMI驱动程序违反了列表中的一个或多个要点。原因是WMI子系统在过去二十年中发生了显著变化，因此较旧的WMI驱动程序中有很多遗留问题。

新的WMI驱动程序还必须符合`Documentation/process/coding-style.rst`中规定的Linux内核编码风格。checkpatch工具可以捕捉许多常见的编码风格违规，可以通过以下命令调用它：

::

  ./scripts/checkpatch.pl --strict <path to driver file>

参考文献
==========

.. [1] https://lwn.net/Articles/391230/
