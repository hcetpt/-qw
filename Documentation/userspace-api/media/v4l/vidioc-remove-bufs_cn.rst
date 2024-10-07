SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_REMOVE_BUFS:

************************
ioctl VIDIOC_REMOVE_BUFS
************************

名称
====

VIDIOC_REMOVE_BUFS - 从队列中移除缓冲区

概览
========

.. c:macro:: VIDIOC_REMOVE_BUFS

``int ioctl(int fd, VIDIOC_REMOVE_BUFS, struct v4l2_remove_buffers *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_remove_buffers` 的指针
描述
===========

应用程序可以选择性地调用 :ref:`VIDIOC_REMOVE_BUFS` ioctl 来从队列中移除缓冲区。
:ref:`VIDIOC_CREATE_BUFS` ioctl 支持是必需的，以启用 :ref:`VIDIOC_REMOVE_BUFS`。
如果在调用 :c:func:`VIDIOC_REQBUFS` 或 :c:func:`VIDIOC_CREATE_BUFS` 时设置了 ``V4L2_BUF_CAP_SUPPORTS_REMOVE_BUFS`` 能力，则此 ioctl 可用。

.. c:type:: v4l2_remove_buffers

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_remove_buffers
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``index``
      - 要移除的起始缓冲区索引。如果 count == 0，则忽略该字段
    * - __u32
      - ``count``
      - 要移除的缓冲区数量，索引范围为 'index' 到 'index + count - 1'
      所有这些范围内的缓冲区必须有效且处于 DEQUEUED 状态

:ref:`VIDIOC_REMOVE_BUFS` 总是会检查 ``type`` 的有效性，如果无效则返回 ``EINVAL`` 错误码。
如果 count 设置为 0，:ref:`VIDIOC_REMOVE_BUFS` 将什么都不做并返回 0。
* - __u32
      - ``type``
      - 流或缓冲区的类型，这与结构体 :c:type:`v4l2_format` 的 ``type`` 字段相同。有效的值请参见 :c:type:`v4l2_buf_type`
* - __u32
      - ``reserved``\ [13]
      - 为将来扩展保留的位置。驱动程序和应用程序必须将数组设置为零

返回值
======

成功时返回 0，失败时返回 -1 并且设置 ``errno`` 变量为适当的值。通用错误代码在“通用错误代码”章节中描述。如果发生错误，不会释放任何缓冲区，并会返回以下错误代码之一：

EBUSY
    文件 I/O 正在进行中
    范围 ``index`` 到 ``index + count - 1`` 中的一个或多个缓冲区不在 DEQUEUED 状态
EINVAL
    范围 ``index`` 到 ``index + count - 1`` 中的一个或多个缓冲区不存在于队列中
    缓冲区类型（``type`` 字段）无效
