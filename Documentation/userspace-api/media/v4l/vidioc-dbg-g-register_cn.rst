SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间: V4L

.. _VIDIOC_DBG_G_REGISTER:

**************************************************
ioctl VIDIOC_DBG_G_REGISTER, VIDIOC_DBG_S_REGISTER
**************************************************

名称
====

VIDIOC_DBG_G_REGISTER - VIDIOC_DBG_S_REGISTER - 读取或写入硬件寄存器

概述
====

.. c:macro:: VIDIOC_DBG_G_REGISTER

``int ioctl(int fd, VIDIOC_DBG_G_REGISTER, struct v4l2_dbg_register *argp)``

.. c:macro:: VIDIOC_DBG_S_REGISTER

``int ioctl(int fd, VIDIOC_DBG_S_REGISTER, const struct v4l2_dbg_register *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_dbg_register` 结构体的指针
描述
====

.. note::

    这是一个 :ref:`实验性` 接口，将来可能会发生变化。
为了调试驱动程序的目的，这些 ioctl 允许测试应用程序直接访问硬件寄存器。常规应用程序不应使用它们。
由于写入甚至读取寄存器可能会危及系统的安全性、稳定性和损坏硬件，因此这两个 ioctl 都需要超级用户权限。此外，Linux 内核必须以 ``CONFIG_VIDEO_ADV_DEBUG`` 选项进行编译才能启用这些 ioctl。
要写入一个寄存器，应用程序必须初始化一个 struct :c:type:`v4l2_dbg_register` 的所有字段（除了 ``size``），并用指向该结构的指针调用 ``VIDIOC_DBG_S_REGISTER``。``match.type`` 和 ``match.addr`` 或 ``match.name`` 字段选择电视卡上的一个芯片，``reg`` 字段指定一个寄存器编号，而 ``val`` 字段则指定要写入寄存器的值。
要读取一个寄存器，应用程序必须初始化 ``match.type``、``match.addr`` 或 ``match.name`` 和 ``reg`` 字段，并用指向该结构的指针调用 ``VIDIOC_DBG_G_REGISTER``。成功时，驱动程序会将寄存器值存储在 ``val`` 字段中，并将值的大小（以字节为单位）存储在 ``size`` 中。
当 ``match.type`` 是 ``V4L2_CHIP_MATCH_BRIDGE`` 时，``match.addr`` 选择电视卡上的第 n 个非子设备芯片。编号零始终选择主机芯片，例如连接到 PCI 或 USB 总线的芯片。可以通过 :ref:`VIDIOC_DBG_G_CHIP_INFO` ioctl 查看哪些芯片存在。
当 ``match.type`` 是 ``V4L2_CHIP_MATCH_SUBDEV`` 时，``match.addr`` 选择第 n 个子设备。
这些 ioctl 是可选的，并非所有驱动程序都支持它们。但是，当驱动程序支持这些 ioctl 时，它还必须支持 :ref:`VIDIOC_DBG_G_CHIP_INFO`。相反，它可以支持 ``VIDIOC_DBG_G_CHIP_INFO`` 但不支持这些 ioctl。
``VIDIOC_DBG_G_REGISTER`` 和 ``VIDIOC_DBG_S_REGISTER`` 在 Linux 2.6.21 中引入，但在内核 2.6.29 中更改为本文描述的 API。
我们建议使用 v4l2-dbg 工具而不是直接调用这些 ioctl。
它可以从 LinuxTV v4l-dvb 仓库获得；访问说明请见：[LinuxTV 仓库](https://linuxtv.org/repo/)

.. tabularcolumns:: |p{3.5cm}|p{3.5cm}|p{3.5cm}|p{6.6cm}|

.. c:type:: v4l2_dbg_match

.. flat-table:: 结构 v4l2_dbg_match
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``type``
      - 可能的类型列表，请参阅 :ref:`chip-match-types`
* - union {
      - （匿名）
    * - __u32
      - ``addr``
      - 根据 ``type`` 字段解释此编号来匹配芯片
* - char
      - ``name[32]``
      - 根据 ``type`` 字段解释此名称来匹配芯片。目前未使用
* - }
      -

.. c:type:: v4l2_dbg_register

.. flat-table:: 结构 v4l2_dbg_register
    :header-rows:  0
    :stub-columns: 0

    * - struct v4l2_dbg_match
      - ``match``
      - 匹配芯片的方式，请参阅 :c:type:`v4l2_dbg_match`
* - __u32
      - ``size``
      - 寄存器大小（字节）
* - __u64
      - ``reg``
      - 寄存器编号
* - __u64
      - ``val``
      - 从寄存器读取或写入到寄存器的值
```markdown
.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _chip-match-types:

.. flat-table:: 芯片匹配类型
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_CHIP_MATCH_BRIDGE``
      - 0
      - 匹配卡片上的第 n 个芯片，对于桥接芯片为零。不匹配子设备。
    * - ``V4L2_CHIP_MATCH_SUBDEV``
      - 4
      - 匹配第 n 个子设备。

返回值
======

成功时返回 0，失败时返回 -1 并且设置 ``errno`` 变量为适当的错误码。通用错误码在
:ref:`通用错误码 <gen-errors>` 章节中描述。

EPERM
    权限不足。执行这些 ioctl 需要 root 特权。
```
