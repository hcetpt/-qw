.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: MC

.. _媒体_ioc_enum_entities:

*******************************
ioctl MEDIA_IOC_ENUM_ENTITIES
*******************************

名称
====

MEDIA_IOC_ENUM_ENTITIES - 枚举实体及其属性

概览
========

.. c:macro:: MEDIA_IOC_ENUM_ENTITIES

``int ioctl(int fd, MEDIA_IOC_ENUM_ENTITIES, struct media_entity_desc *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`media_entity_desc` 的指针
描述
===========

为了查询实体的属性，应用程序需要设置结构体 :c:type:`media_entity_desc` 中的 `id` 字段，并使用指向该结构体的指针调用 `MEDIA_IOC_ENUM_ENTITIES` ioctl。驱动程序将填充结构体的其余部分，如果 `id` 无效，则返回 `EINVAL` 错误码。
.. _媒体-实体-id-标志-下一个:

可以通过将 `id` 与 `MEDIA_ENT_ID_FLAG_NEXT` 标志进行或运算来枚举实体。驱动程序将返回具有严格大于请求 `id` 的最小 `id` 的实体信息（即“下一个实体”），或者如果没有这样的实体，则返回 `EINVAL` 错误码。实体 `id` 可能不是连续的。应用程序不应尝试通过递增 `id` 直到收到错误的方式枚举实体。
.. c:type:: media_entity_desc

.. tabularcolumns:: |p{1.5cm}|p{1.7cm}|p{1.6cm}|p{1.5cm}|p{10.6cm}|

.. flat-table:: 结构体 media_entity_desc
    :header-rows:  0
    :stub-columns: 0
    :widths: 2 2 1 8

    *  -  __u32
       -  ``id``
       -
       -  实体 ID，由应用程序设置。当 ID 被与 `MEDIA_ENT_ID_FLAG_NEXT` 进行或运算时，驱动程序会清除该标志并返回具有更大 ID 的第一个实体的信息。不要期望设备每次实例化时 ID 都相同，换句话说，不要在应用程序中硬编码实体 ID。
*  -  char
       -  ``name``\ [32]
       -
       -  实体名称为 UTF-8 NULL 终止字符串。这个名称在媒体拓扑中必须是唯一的。
*  -  __u32
       -  ``type``
       -
       -  实体类型，详见 :ref:`媒体-实体-功能` 以获取详细信息。
*  -  __u32
       -  ``revision``
       -
       -  实体修订版本。始终为零（已废弃）。

    *  -  __u32
       -  ``flags``
       -
       -  实体标志，详见 :ref:`媒体-实体-标志` 以获取详细信息。
*  -  __u32
       -  ``group_id``
       -
       -  实体组 ID。始终为零（已废弃）。

    *  -  __u16
       -  ``pads``
       -
       -  垫数量。

    *  -  __u16
       -  ``links``
       -
       -  总出站链接数。此字段不包括入站链接。
*  -  __u32
       -  ``reserved[4]``
       -
       -  保留供将来扩展使用。驱动程序和应用程序必须将数组设置为零。

*  -  union {
       -  （匿名）

    *  -  struct
       -  ``dev``
       -
       -  对于创建单个设备节点的（子）设备有效

*  -
       -  __u32
       -  ``major``
       -  设备节点主号

*  -
       -  __u32
       -  ``minor``
       -  设备节点次号

*  -  __u8
       -  ``raw``\[184\]
       -
       -

    *  - }
       -

返回值
======

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量为适当的值。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
EINVAL
    结构 :c:type:`media_entity_desc` 中的 ``id`` 引用了一个不存在的实体。
