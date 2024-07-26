SPDX 许可证标识符: (GPL-2.0-only 或 BSD-2-Clause)

=================
设备链自检
=================

`devlink-selftests` API 允许在设备上执行自检测试。
测试掩码
==========
`devlink-selftests` 命令应与一个掩码一起运行，该掩码指示要执行的测试。

测试描述
=================
以下是驱动程序可能执行的一系列测试列表：

.. list-table:: 测试列表
   :widths: 5 90

   * - 名称
     - 描述
   * - ``DEVLINK_SELFTEST_FLASH``
     - 设备可能将固件存储在板载的非易失性内存中（例如：闪存）。这个特定的测试有助于对设备进行闪存自检。该测试的具体实现留给驱动程序/固件完成。

示例用法
-------------

.. code:: shell

    # 查询设备链设备支持的自检测试
    $ devlink dev selftests show DEV
    # 查询所有设备链设备支持的自检测试
    $ devlink dev selftests show
    # 在设备上执行自检测试
    $ devlink dev selftests run DEV id flash
