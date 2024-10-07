SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _streaming-par:

********************
流参数
********************

流参数旨在优化视频捕获过程以及输入/输出（I/O）。目前，应用程序可以通过 :ref:`VIDIOC_S_PARM <VIDIOC_G_PARM>` ioctl 请求高质量的捕获模式。当前的视频标准确定了每秒的标准帧数。如果需要捕获或输出的帧数少于这个标准帧数，应用程序可以在驱动程序端请求跳帧或重复帧。这在使用 :c:func:`read()` 或 :c:func:`write()` 时特别有用，因为这些函数没有时间戳或序列计数器的增强功能，并且可以避免不必要的数据复制。最后，这些 ioctl 可用于确定驱动程序在读写模式下内部使用的缓冲区数量。关于其影响，请参阅讨论 :c:func:`read()` 函数的部分。

为了获取和设置流参数，应用程序分别调用 :ref:`VIDIOC_G_PARM <VIDIOC_G_PARM>` 和 :ref:`VIDIOC_S_PARM <VIDIOC_G_PARM>` ioctl。它们需要一个指向 struct :c:type:`v4l2_streamparm` 的指针，该结构包含一个联合体，分别存储输入设备和输出设备的参数。

这些 ioctl 是可选的，驱动程序不必实现它们。如果不支持，则返回 ``EINVAL`` 错误代码。
