SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_SUBDEV_G_ROUTING:

*******************************************************
ioctl VIDIOC_SUBDEV_G_ROUTING, VIDIOC_SUBDEV_S_ROUTING
*******************************************************

名称
====

VIDIOC_SUBDEV_G_ROUTING - VIDIOC_SUBDEV_S_ROUTING - 获取或设置媒体实体中媒体接口之间的流路由

概要
====

.. c:macro:: VIDIOC_SUBDEV_G_ROUTING

``int ioctl(int fd, VIDIOC_SUBDEV_G_ROUTING, struct v4l2_subdev_routing *argp)``

.. c:macro:: VIDIOC_SUBDEV_S_ROUTING

``int ioctl(int fd, VIDIOC_SUBDEV_S_ROUTING, struct v4l2_subdev_routing *argp)``

参数
=========

``fd``
    由 :ref:`open() <func-open>` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_subdev_routing` 的指针

描述
===========

这些 ioctl 用于获取和设置媒体实体中的路由。路由配置决定了实体内部的数据流动。
驱动程序使用 ``VIDIOC_SUBDEV_G_ROUTING`` ioctl 报告它们当前的路由表，应用程序可以通过 ``VIDIOC_SUBDEV_S_ROUTING`` ioctl 启用或禁用路由，通过添加或移除路由以及设置或清除结构体 :c:type:`v4l2_subdev_route` 中 `flags` 字段的标志来实现。
与 ``VIDIOC_SUBDEV_G_ROUTING`` 类似，``VIDIOC_SUBDEV_S_ROUTING`` 也会将路由返回给用户。
当调用 ``VIDIOC_SUBDEV_S_ROUTING`` 时，所有流配置都会被重置。
这意味着用户空间必须在调用 ioctl（例如，使用 ``VIDIOC_SUBDEV_S_FMT``）之后重新配置所有流格式和选择。
只有同时具有输入接口和输出接口的子设备才能支持路由。
`len_routes` 字段表示用户空间分配的 `routes` 数组中可以容纳的路由数量。对于这两个 ioctl，应用程序需要设置此字段以指示内核可以返回多少条路由，并且该字段不会被内核修改。
```num_routes```字段表示路由表中的路由数量。对于```VIDIOC_SUBDEV_S_ROUTING```，该值由用户空间设置为应用程序存储在```routes```数组中的路由数量。对于这两个ioctl命令，内核返回的```num_routes```表示子设备路由表中存储的路由数量。这可能比应用程序为```VIDIOC_SUBDEV_S_ROUTING```设置的```num_routes```值更小或更大，因为驱动程序可能会调整请求的路由表。

内核可以从这两个ioctl命令中返回一个大于```len_routes```的```num_routes```值。这表明路由表中的路由数量超过了```routes```数组的容量。在这种情况下，内核会用子设备路由表中的前```len_routes```条目填充```routes```数组。这不是错误，并且ioctl调用会成功。如果应用程序希望获取缺失的路由，可以使用足够大的```routes```数组发出新的```VIDIOC_SUBDEV_G_ROUTING```调用。
```VIDIOC_SUBDEV_S_ROUTING```可能会返回比用户在```num_routes```字段中提供的更多的路由，这可能是由于硬件属性等原因。

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.7cm}|

.. c:type:: v4l2_subdev_routing

.. flat-table:: struct v4l2_subdev_routing
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ```which```
      - 要访问的路由表，取自枚举
        :ref:`v4l2_subdev_format_whence <v4l2-subdev-format-whence>`
    * - __u32
      - ```len_routes```
      - 数组长度（即内存中为数组预留的空间）
    * - struct :c:type:`v4l2_subdev_route`
      - ```routes[]```
      - 结构体 :c:type:`v4l2_subdev_route` 的数组
    * - __u32
      - ```num_routes```
      - ```routes```数组中的条目数量
    * - __u32
      - ```reserved[11]```
      - 保留用于未来扩展。应用程序和驱动程序必须将数组设置为零

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.7cm}|

.. c:type:: v4l2_subdev_route

.. flat-table:: struct v4l2_subdev_route
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ```sink_pad```
      - 汇入端口编号
    * - __u32
      - ```sink_stream```
      - 汇入端口流编号
    * - __u32
      - ```source_pad```
      - 源端口编号
    * - __u32
      - ```source_stream```
      - 源端口流编号
    * - __u32
      - ```flags```
      - 路由启用/禁用标志
        :ref:`v4l2_subdev_routing_flags <v4l2-subdev-routing-flags>`
* - __u32
  - ``reserved`` [5]
  - 保留供将来扩展使用。应用程序和驱动程序必须将数组设置为零。
.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.7cm}|

.. _v4l2-subdev-routing-flags:

.. flat-table:: 枚举 v4l2_subdev_routing_flags
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - V4L2_SUBDEV_ROUTE_FL_ACTIVE
      - 0x0001
      - 路径已启用。由应用程序设置。

返回值
======

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。

EINVAL
   沉淀或源垫标识符引用了一个不存在的垫，或者引用了不同类型的垫（例如，沉淀垫标识符引用了一个源垫），或者 ``which`` 字段包含一个不支持的值。
E2BIG
   应用程序为 ``VIDIOC_SUBDEV_S_ROUTING`` 提供的 ``num_routes`` 大于驱动程序能够处理的路径数量。
