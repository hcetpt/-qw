SPDX 许可证标识符: （GPL-2.0-only 或 BSD-2-Clause）

=================
Devlink 自检
=================

``devlink-selftests`` API 允许在设备上执行自检。
测试掩码
==========
``devlink-selftests`` 命令应与一个掩码一起运行，该掩码指示要执行的测试。
测试描述
=================
以下是驱动程序可能执行的测试列表：
.. list-table:: 测试列表
   :widths: 5 90

   * - 名称
     - 描述
   * - ``DEVLINK_SELFTEST_FLASH``
     - 设备可能将固件存储在板载的非易失性内存中，例如闪存。此特定测试有助于在设备上运行闪存自检。测试的具体实现由驱动程序/固件完成。

示例用法
-------------

.. code:: shell

    # 查询 devlink 设备支持的自检
    $ devlink dev selftests show DEV
    # 查询所有 devlink 设备支持的自检
    $ devlink dev selftests show
    # 在设备上执行自检
    $ devlink dev selftests run DEV id flash
