SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_DBG_G_CHIP_INFO:

****************************
ioctl VIDIOC_DBG_G_CHIP_INFO
****************************

名称
====

VIDIOC_DBG_G_CHIP_INFO — 识别电视卡上的芯片

概览
========

.. c:macro:: VIDIOC_DBG_G_CHIP_INFO

``int ioctl(int fd, VIDIOC_DBG_G_CHIP_INFO, struct v4l2_dbg_chip_info *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_dbg_chip_info` 的指针
描述
===========

.. note::

    这是一个 :ref:`实验性` 接口，将来可能会发生变化。
此 ioctl 用于驱动程序调试目的，允许测试应用程序查询驱动程序关于电视卡上存在的芯片信息。常规应用程序不应使用它。如果您发现特定芯片的问题，请联系 linux-media 邮件列表（`https://linuxtv.org/lists.php <https://linuxtv.org/lists.php>`__）以便修复问题。
此外，Linux 内核必须使用 `CONFIG_VIDEO_ADV_DEBUG` 选项进行编译以启用此 ioctl。
要查询驱动程序，应用程序必须初始化 struct :c:type:`v4l2_dbg_chip_info` 中的 ``match.type`` 和 ``match.addr`` 或 ``match.name`` 字段，并通过指向该结构的指针调用 :ref:`VIDIOC_DBG_G_CHIP_INFO`。成功时，驱动程序将在 ``name`` 和 ``flags`` 字段中存储所选芯片的信息。
当 ``match.type`` 是 ``V4L2_CHIP_MATCH_BRIDGE`` 时，``match.addr`` 选择电视卡上的第 n 个桥接‘芯片’。可以通过从零开始并逐个递增 ``match.addr`` 直到 :ref:`VIDIOC_DBG_G_CHIP_INFO` 失败并返回 ``EINVAL`` 错误代码来枚举所有芯片。数字零始终选择桥接芯片本身，例如连接到 PCI 或 USB 总线的芯片。非零数字标识桥接芯片的特定部分，如 AC97 寄存器块。
当 ``match.type`` 是 ``V4L2_CHIP_MATCH_SUBDEV`` 时，``match.addr`` 选择第 n 个子设备。这允许您枚举所有子设备。
成功时，``name`` 字段将包含芯片名称，而 ``flags`` 字段将包含 ``V4L2_CHIP_FL_READABLE`` （如果驱动程序支持从设备读取寄存器）或 ``V4L2_CHIP_FL_WRITABLE`` （如果驱动程序支持向设备写入寄存器）。
我们建议使用 v4l2-dbg 工具而不是直接调用此 ioctl。它可以从 LinuxTV v4l-dvb 存储库获取；访问说明请参阅 `https://linuxtv.org/repo/ <https://linuxtv.org/repo/>`__。
```markdown
.. tabularcolumns:: |p{3.5cm}|p{3.5cm}|p{3.5cm}|p{6.6cm}|

.. _name-v4l2-dbg-match:

.. flat-table:: 结构体 v4l2_dbg_match
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``type``
      - 参见 :ref:`name-chip-match-types` 获取可能的类型列表
* - union {
      - （匿名）
    * - __u32
      - ``addr``
      - 根据 ``type`` 字段解释此编号以匹配芯片
* - char
      - ``name[32]``
      - 根据 ``type`` 字段解释此名称以匹配芯片。目前未使用
* - }
      -

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_dbg_chip_info

.. flat-table:: 结构体 v4l2_dbg_chip_info
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - struct v4l2_dbg_match
      - ``match``
      - 匹配芯片的方式，参见 :ref:`name-v4l2-dbg-match`
* - char
      - ``name[32]``
      - 芯片的名称
* - __u32
      - ``flags``
      - 由驱动程序设置。如果设置了 ``V4L2_CHIP_FL_READABLE``，则驱动程序支持从设备读取寄存器；如果设置了 ``V4L2_CHIP_FL_WRITABLE``，则支持写入寄存器
* - __u32
      - ``reserved[8]``
      - 预留字段，应用程序和驱动程序都必须将其设置为0

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _name-chip-match-types:

.. flat-table:: 芯片匹配类型
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_CHIP_MATCH_BRIDGE``
      - 0
      - 匹配卡片上的第n个芯片，对于桥接芯片为零。不匹配子设备
* - ``V4L2_CHIP_MATCH_SUBDEV``
      - 4
      - 匹配第n个子设备

返回值
======
成功时返回0，错误时返回-1，并且设置 ``errno`` 变量为适当的值。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
```
EINVAL
`match_type` 无效或无法匹配到设备
