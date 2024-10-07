SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: MC

.. _media_ioc_enum_links:

**************************
ioctl MEDIA_IOC_ENUM_LINKS
**************************

名称
====

MEDIA_IOC_ENUM_LINKS - 列出给定实体的所有端口和链接

概要
========

.. c:macro:: MEDIA_IOC_ENUM_LINKS

``int ioctl(int fd, MEDIA_IOC_ENUM_LINKS, struct media_links_enum *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`media_links_enum` 结构体的指针
描述
===========

为了列出给定实体的端口和/或链接，应用程序需要设置一个 :c:type:`media_links_enum` 结构体的 `entity` 字段，并初始化由 `pads` 和 `links` 字段指向的 :c:type:`media_pad_desc` 和 :c:type:`media_link_desc` 结构体数组。然后调用带有此结构体指针的 `MEDIA_IOC_ENUM_LINKS` ioctl。

如果 `pads` 字段不为 NULL，则驱动程序会用有关该实体端口的信息填充 `pads` 数组。数组必须有足够的空间来存储所有实体的端口。端口数量可以通过 :ref:`MEDIA_IOC_ENUM_ENTITIES` 获取。

如果 `links` 字段不为 NULL，则驱动程序会用有关该实体输出链接的信息填充 `links` 数组。数组必须有足够的空间来存储所有实体的输出链接。输出链接的数量可以通过 :ref:`MEDIA_IOC_ENUM_ENTITIES` 获取。

在枚举过程中，仅返回从实体的源端口发出的前向链接。
.. c:type:: media_links_enum

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct media_links_enum
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    *  -  __u32
       -  ``entity``
       -  实体 ID，由应用程序设置
    *  -  struct :c:type:`media_pad_desc`
       -  \*\ ``pads``
       -  指向由应用程序分配的端口数组的指针。如果为 NULL 则忽略
    *  -  struct :c:type:`media_link_desc`
       -  \*\ ``links``
       -  指向由应用程序分配的链接数组的指针。如果为 NULL 则忽略
    *  -  __u32
       -  ``reserved[4]``
       -  保留用于将来扩展。驱动程序和应用程序必须将数组设置为零
.. c:type:: media_pad_desc

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: 结构体 media_pad_desc
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    *  -  __u32
       -  ``entity``
       -  此端口所属实体的ID
*  -  __u16
       -  ``index``
       -  端口索引，从0开始
*  -  __u32
       -  ``flags``
       -  端口标志，更多详情请参见 :ref:`media-pad-flag`
*  -  __u32
       -  ``reserved[2]``
       -  为将来扩展保留。驱动程序和应用程序必须将数组设置为零

.. c:type:: media_link_desc

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: 结构体 media_link_desc
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    *  -  结构体 :c:type:`media_pad_desc`
       -  ``source``
       -  此链接的起始端口
*  -  结构体 :c:type:`media_pad_desc`
       -  ``sink``
       -  此链接的目标端口
*  -  __u32
       -  ``flags``
       -  链接标志，更多详情请参见 :ref:`media-link-flag`
*  -  __u32
       -  ``reserved[2]``
       -  为将来扩展保留。驱动程序和应用程序必须将数组设置为零

返回值
======

成功时返回0，失败时返回-1，并且设置 ``errno`` 变量为相应的错误码。通用错误码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

EINVAL
    结构体 :c:type:`media_links_enum` 的 ``id`` 引用了一个不存在的实体
当然，请提供您需要翻译的文本。
