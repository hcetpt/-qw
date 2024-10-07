SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
c 命名空间:: V4L

.. _VIDIOC_SUBDEV_G_FMT:

**********************************************
ioctl VIDIOC_SUBDEV_G_FMT, VIDIOC_SUBDEV_S_FMT
**********************************************

名称
====

VIDIOC_SUBDEV_G_FMT - VIDIOC_SUBDEV_S_FMT - 获取或设置子设备端口上的数据格式

概要
====

.. c:macro:: VIDIOC_SUBDEV_G_FMT

``int ioctl(int fd, VIDIOC_SUBDEV_G_FMT, struct v4l2_subdev_format *argp)``

.. c:macro:: VIDIOC_SUBDEV_S_FMT

``int ioctl(int fd, VIDIOC_SUBDEV_S_FMT, struct v4l2_subdev_format *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 struct :c:type:`v4l2_subdev_format` 的指针
描述
====

这些 ioctl 用于协商图像管道中特定子设备端口的帧格式。
为了获取当前格式，应用程序将 struct :c:type:`v4l2_subdev_format` 的 ``pad`` 字段设置为媒体 API 报告的所需端口号，并将 ``which`` 字段设置为 ``V4L2_SUBDEV_FORMAT_ACTIVE``。当它们使用指向此结构的指针调用 ``VIDIOC_SUBDEV_G_FMT`` ioctl 时，驱动程序会填充 ``format`` 字段的成员。

为了更改当前格式，应用程序需要同时设置 ``pad`` 和 ``which`` 字段以及 ``format`` 字段的所有成员。当它们使用指向此结构的指针调用 ``VIDIOC_SUBDEV_S_FMT`` ioctl 时，驱动程序会验证请求的格式，根据硬件功能进行调整并配置设备。返回时，struct :c:type:`v4l2_subdev_format` 包含的内容与通过 ``VIDIOC_SUBDEV_G_FMT`` 调用返回的当前格式相同。

应用程序可以通过将 ``which`` 设置为 ``V4L2_SUBDEV_FORMAT_TRY`` 来查询设备的能力。当设置为 "尝试" 格式时，这些格式不会被驱动程序应用到设备上，而是像活动格式一样被精确更改，并存储在子设备文件句柄中。因此，两个查询同一子设备的应用程序不会相互影响。

例如，要在子设备的输出端口上尝试一种格式，应用程序首先会使用 ``VIDIOC_SUBDEV_S_FMT`` ioctl 在子设备输入端口设置尝试格式。然后，他们可以使用 ``VIDIOC_SUBDEV_G_FMT`` ioctl 获取输出端口的默认格式，或者使用 ``VIDIOC_SUBDEV_S_FMT`` ioctl 设置所需的输出端口格式并检查返回值。

尝试格式不依赖于活动格式，但可能依赖于当前链接配置或子设备控制值。例如，低通噪声滤波器可能会裁剪帧边界处的像素，从而改变其输出帧大小。

如果子设备节点是以只读模式注册的，则仅当 ``which`` 字段设置为 ``V4L2_SUBDEV_FORMAT_TRY`` 时，对 ``VIDIOC_SUBDEV_S_FMT`` 的调用才是有效的，否则会返回错误并将 errno 变量设置为 ``-EPERM``。

驱动程序不应仅仅因为请求的格式不符合设备的功能而返回错误。相反，它们必须修改格式以匹配硬件能够提供的内容。修改后的格式应尽可能接近原始请求。
```markdown
.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_subdev_format

.. flat-table:: 结构体 v4l2_subdev_format
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``pad``
      - 由媒体控制器 API 报告的 pad 编号
* - __u32
      - ``which``
      - 要修改的格式，取自枚举
	:ref:`v4l2_subdev_format_whence <v4l2-subdev-format-whence>`
* - struct :c:type:`v4l2_mbus_framefmt`
      - ``format``
      - 图像格式定义，详情参见 :c:type:`v4l2_mbus_framefmt`
* - __u32
      - ``stream``
      - 流标识符
* - __u32
      - ``reserved``\ [7]
      - 保留用于将来扩展。应用程序和驱动程序必须将数组设置为零

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _v4l2-subdev-format-whence:

.. flat-table:: 枚举 v4l2_subdev_format_whence
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - V4L2_SUBDEV_FORMAT_TRY
      - 0
      - 尝试格式，用于查询设备能力
* - V4L2_SUBDEV_FORMAT_ACTIVE
      - 1
      - 活动格式，应用于硬件

返回值
======
成功时返回 0，出错时返回 -1 并且设置 ``errno`` 变量为适当的值。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。

EBUSY
    由于 pad 当前处于忙碌状态，无法更改格式。这可能是由于 pad 上有活动的视频流等原因造成的。
    在没有首先执行其他操作来修复问题之前，不应重试此 ioctl。只有在 ``VIDIOC_SUBDEV_S_FMT`` 中返回。

EINVAL
    结构体 :c:type:`v4l2_subdev_format` 的 ``pad`` 引用了一个不存在的 pad，或者 ``which`` 字段具有不受支持的值。
```
EPERM
在只读子设备上调用了 ``VIDIOC_SUBDEV_S_FMT`` ioctl，并且 ``which`` 字段被设置为 ``V4L2_SUBDEV_FORMAT_ACTIVE``。

成功时返回 0，失败时返回 -1 并且设置 ``errno`` 变量。通用错误代码在《通用错误代码 <gen-errors>》章节中描述。
