SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间: V4L

.. _VIDIOC_SUBSCRIBE_EVENT:
.. _VIDIOC_UNSUBSCRIBE_EVENT:

*******************************************************
ioctl VIDIOC_SUBSCRIBE_EVENT, VIDIOC_UNSUBSCRIBE_EVENT
*******************************************************

名称
====

VIDIOC_SUBSCRIBE_EVENT - VIDIOC_UNSUBSCRIBE_EVENT - 订阅或取消订阅事件

概要
========

.. c:macro:: VIDIOC_SUBSCRIBE_EVENT

``int ioctl(int fd, VIDIOC_SUBSCRIBE_EVENT, struct v4l2_event_subscription *argp)``

.. c:macro:: VIDIOC_UNSUBSCRIBE_EVENT

``int ioctl(int fd, VIDIOC_UNSUBSCRIBE_EVENT, struct v4l2_event_subscription *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_event_subscription` 结构体的指针

描述
===========

订阅或取消订阅 V4L2 事件。已订阅的事件可以通过 :ref:`VIDIOC_DQEVENT` ioctl 来出队。
.. tabularcolumns:: |p{2.6cm}|p{4.4cm}|p{10.3cm}|

.. c:type:: v4l2_event_subscription

.. flat-table:: struct v4l2_event_subscription
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``type``
      - 事件类型，参见 :ref:`event-type`

.. note::

    可以使用 ``V4L2_EVENT_ALL`` 与 :ref:`VIDIOC_UNSUBSCRIBE_EVENT <VIDIOC_SUBSCRIBE_EVENT>` 一起取消订阅所有事件。

* - __u32
      - ``id``
      - 事件源的 ID。如果没有与事件源关联的 ID，则将其设置为 0。是否需要 ID 取决于事件类型。
* - __u32
      - ``flags``
      - 事件标志，参见 :ref:`event-flags`
* - __u32
      - ``reserved``\ [5]
      - 保留用于将来扩展。驱动程序和应用程序必须将数组设置为零。

.. tabularcolumns:: |p{7.5cm}|p{2.0cm}|p{7.8cm}|

.. _event-flags:

.. flat-table:: 事件标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_EVENT_SUB_FL_SEND_INITIAL``
      - 0x0001
      - 当订阅此事件时，会发送一个初始事件，包含当前状态。这仅对由状态更改触发的事件（如 ``V4L2_EVENT_CTRL``）有意义。其他事件将忽略此标志。
* - ``V4L2_EVENT_SUB_FL_ALLOW_FEEDBACK``
  - 0x0002
  - 如果设置了此标志，则由 ioctl 直接引发的事件也会发送到调用该 ioctl 的文件句柄。例如，使用 :ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` 改变一个控制项时，会向同一个文件句柄发送一个 V4L2_EVENT_CTRL 事件。
通常这类事件会被抑制，以防止反馈循环，即应用程序将一个控制项改变为一个值后再改变为另一个值，然后收到一个事件告知该控制项已变为第一个值。
由于无法判断该事件是由另一个应用程序引起的还是由 :ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` 调用引起的，因此很难决定是将控制项设置为事件中的值还是忽略它。
在设置此标志时，请仔细考虑，以免陷入此类情况。

返回值
======
成功时返回 0，失败时返回 -1 并且 ``errno`` 变量会被相应设置。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中有描述。
