SPDX 许可证标识符: GPL-2.0

================
Devlink 资源
================

`devlink` 提供了驱动程序注册资源的能力，这可以让管理员看到给定资源的设备限制以及当前使用了多少该资源。此外，这些资源可以可选地具有可配置的大小。这使得管理员能够限制使用的资源数量。例如，`netdevsim` 驱动程序将 `/IPv4/fib` 和 `/IPv4/fib-rules` 作为资源来限制给定设备的 IPv4 FIB 条目和规则的数量。

资源 ID
============

每个资源由一个 ID 表示，并包含有关其当前大小和相关子资源的信息。要访问子资源，你需要指定资源的路径。例如，`/IPv4/fib` 是 `IPv4` 资源下 `fib` 子资源的 ID。

通用资源
=================

通用资源用于描述多个设备驱动程序可以共享的资源，并且它们的描述必须添加到以下表格中：

.. list-table:: 通用资源列表
   :widths: 10 90

   * - 名称
     - 描述
   * - `physical_ports`
     - 交换机 ASIC 可以支持的物理端口的有限容量

示例用法
-------------

可以通过命令观察驱动程序暴露的资源，例如：

.. code:: shell

    $ devlink resource show pci/0000:03:00.0
    pci/0000:03:00.0:
      name kvd size 245760 unit entry
        resources:
          name linear size 98304 occ 0 unit entry size_min 0 size_max 147456 size_gran 128
          name hash_double size 60416 unit entry size_min 32768 size_max 180224 size_gran 128
          name hash_single size 87040 unit entry size_min 65536 size_max 212992 size_gran 128

某些资源的大小可以更改。示例如下：

.. code:: shell

    $ devlink resource set pci/0000:03:00.0 path /kvd/hash_single size 73088
    $ devlink resource set pci/0000:03:00.0 path /kvd/hash_double size 74368

更改不会立即生效，这可以通过 `size_new` 属性验证，该属性表示待处理的大小变化。例如：

.. code:: shell

    $ devlink resource show pci/0000:03:00.0
    pci/0000:03:00.0:
      name kvd size 245760 unit entry size_valid false
      resources:
        name linear size 98304 size_new 147456 occ 0 unit entry size_min 0 size_max 147456 size_gran 128
        name hash_double size 60416 unit entry size_min 32768 size_max 180224 size_gran 128
        name hash_single size 87040 unit entry size_min 65536 size_max 212992 size_gran 128

请注意，资源大小的更改可能需要重新加载设备才能生效。
