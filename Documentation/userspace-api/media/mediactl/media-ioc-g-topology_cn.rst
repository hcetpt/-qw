SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间: MC

.. _media_ioc_g_topology:

**************************
ioctl MEDIA_IOC_G_TOPOLOGY
**************************

名称
====

MEDIA_IOC_G_TOPOLOGY — 列出图结构和图元素属性

概述
========

.. c:macro:: MEDIA_IOC_G_TOPOLOGY

``int ioctl(int fd, MEDIA_IOC_G_TOPOLOGY, struct media_v2_topology *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`media_v2_topology` 结构体的指针
描述
===========

这个 ioctl 的典型用法是调用两次。在第一次调用时，定义在 :c:type:`media_v2_topology` 中的结构体应该被清零。返回时，如果没有错误发生，此 ioctl 将返回 `topology_version` 和实体、接口、pad 和链接的总数。
在第二次调用之前，用户空间应该分配数组来存储所需的图元素，并将指向它们的指针放入 ptr_entities、ptr_interfaces、ptr_links 和/或 ptr_pads 中，保持其他值不变。
如果 `topology_version` 保持不变，则 ioctl 应该使用媒体图元素填充所需的数组。

.. tabularcolumns:: |p{1.6cm}|p{3.4cm}|p{12.3cm}|

.. c:type:: media_v2_topology

.. flat-table:: struct media_v2_topology
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 2 8

    *  -  __u64
       -  ``topology_version``
       -  媒体图结构版本。当图创建时，该字段从零开始。每当添加或删除一个图元素时，该字段就会递增。
*  -  __u32
       -  ``num_entities``
       -  图中实体的数量

    *  -  __u32
       -  ``reserved1``
       -  应用程序和驱动程序应将其设置为 0
*  -  __u64
       -  ``ptr_entities``
       -  指向将存储实体数组的内存区域的指针，转换为 64 位整数。它可以为零。如果为零，ioctl 不会存储实体。它只会更新 ``num_entities``

    *  -  __u32
       -  ``num_interfaces``
       -  图中接口的数量

    *  -  __u32
       -  ``reserved2``
       -  应用程序和驱动程序应将其设置为 0
*  -  __u64
       -  ``ptr_interfaces``
       -  指向将存储接口数组的内存区域的指针，转换为 64 位整数。它可以为零。如果为零，ioctl 不会存储接口。它只会更新 ``num_interfaces``

    *  -  __u32
       -  ``num_pads``
       -  图中 pad 的总数

    *  -  __u32
       -  ``reserved3``
       -  应用程序和驱动程序应将其设置为 0
*  -  __u64
       -  ``ptr_pads``
       -  指向将存储 pad 数组的内存区域的指针，转换为 64 位整数。它可以为零。如果为零，ioctl 不会存储 pad。它只会更新 ``num_pads``

    *  -  __u32
       -  ``num_links``
       -  图中数据和接口链接的总数

    *  -  __u32
       -  ``reserved4``
       -  应用程序和驱动程序应将其设置为 0
*  -  `__u64`
       -  `ptr_links`
       -  指向将存储链接数组的内存区域的指针，转换为64位整数。它可以为零。如果为零，则ioctl不会存储链接，仅更新`num_links`

.. tabularcolumns:: |p{1.6cm}|p{3.2cm}|p{12.5cm}|

.. c:type:: media_v2_entity

.. flat-table:: struct media_v2_entity
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 2 8

    *  -  `__u32`
       -  `id`
       -  实体的唯一ID。不要期望设备每次实例化时ID都相同。换句话说，在应用程序中不要硬编码实体ID
*  -  `char`
       -  `name`\ [64]
       -  实体名称作为UTF-8终止字符串。这个名称在媒体拓扑结构中必须是唯一的
*  -  `__u32`
       -  `function`
       -  实体的主要功能，详情参见 :ref:`media-entity-functions`
*  -  `__u32`
       -  `flags`
       -  实体标志，详情参见 :ref:`media-entity-flag`。只有当`MEDIA_V2_ENTITY_HAS_FLAGS(media_version)`返回真时才有效。`media_version`定义在结构体 :c:type:`media_device_info` 中，并且可以通过 :ref:`MEDIA_IOC_DEVICE_INFO` 获取
*  -  `__u32`
       -  `reserved`\ [5]
       -  保留用于未来扩展。驱动程序和应用程序必须将此数组设为零
.. tabularcolumns:: |p{1.6cm}|p{3.2cm}|p{12.5cm}|

.. c:type:: media_v2_interface

.. flat-table:: struct media_v2_interface
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 2 8

    *  -  `__u32`
       -  `id`
       -  接口的唯一ID。不要期望设备每次实例化时ID都相同。换句话说，在应用程序中不要硬编码接口ID
*  -  `__u32`
       -  `intf_type`
       -  接口类型，详情参见 :ref:`media-intf-type`
*  -  `__u32`
       -  `flags`
       -  接口标志。目前未使用
*  -  `__u32`
       -  `reserved`\ [9]
       -  保留用于未来扩展。驱动程序和应用程序必须将此数组设为零
*  - `struct media_v2_intf_devnode`
  - `devnode`
  - 仅用于设备节点接口。详情请参见 :c:type:`media_v2_intf_devnode`

.. tabularcolumns:: |p{1.6cm}|p{3.2cm}|p{12.5cm}|

.. c:type:: media_v2_intf_devnode

.. flat-table:: struct media_v2_intf_devnode
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 2 8

    *  -  __u32
       -  `major`
       - 设备节点主编号
    *  -  __u32
       -  `minor`
       - 设备节点次编号

.. tabularcolumns:: |p{1.6cm}|p{3.2cm}|p{12.5cm}|

.. c:type:: media_v2_pad

.. flat-table:: struct media_v2_pad
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 2 8

    *  -  __u32
       -  `id`
       - 垫（pad）的唯一ID。不要期望该ID在设备的每个实例中都相同。换句话说，不要在应用程序中硬编码垫ID
    *  -  __u32
       -  `entity_id`
       - 该垫所属实体的唯一ID
    *  -  __u32
       -  `flags`
       - 垫标志，更多详情请参见 :ref:`media-pad-flag`
    *  -  __u32
       -  `index`
       - 垫索引，从0开始。只有当 `MEDIA_V2_PAD_HAS_INDEX(media_version)` 返回true时有效。`media_version` 定义在 :c:type:`media_device_info` 结构体中，并且可以通过 :ref:`MEDIA_IOC_DEVICE_INFO` 获取
    *  -  __u32
       -  `reserved`[4]
       - 为将来扩展保留。驱动程序和应用程序必须将此数组设置为零

.. tabularcolumns:: |p{1.6cm}|p{3.2cm}|p{12.5cm}|

.. c:type:: media_v2_link

.. flat-table:: struct media_v2_link
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 2 8

    *  -  __u32
       -  `id`
       - 链接的唯一ID。不要期望该ID在设备的每个实例中都相同。换句话说，不要在应用程序中硬编码链接ID
    *  -  __u32
       -  `source_id`
       - 在点对点链接中：源垫的唯一ID
在接口到实体链接中：接口的唯一ID
*  -  __u32
       -  ``sink_id``
       -  在端口到端口链接中：接收端口的唯一ID

在接口到实体链接中：实体的唯一ID
*  -  __u32
       -  ``flags``
       -  链接标志，更多详情请参见 :ref:`media-link-flag`
*  -  __u32
       -  ``reserved``\ [6]
       -  为未来扩展保留。驱动程序和应用程序必须将此数组设置为零

返回值
======

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量。通用错误代码描述见
:ref:`通用错误代码 <gen-errors>` 章节

ENOSPC
    当 `num_entities`, `num_interfaces`, `num_links` 或 `num_pads` 中的一个或多个非零但小于图中实际元素的数量时返回此错误。这可能发生在 `topology_version` 与上次调用此 ioctl 时相比有所改变的情况下。用户空间通常应释放指针区域、清零结构体元素并再次调用此 ioctl。
