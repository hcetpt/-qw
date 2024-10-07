.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: V4L

.. _rw:

**********
读取/写入
**********

输入和输出设备分别支持 :c:func:`read()` 和 :c:func:`write()` 函数，当结构体 :c:type:`v4l2_capability` 的 `capabilities` 字段中设置了 `V4L2_CAP_READWRITE` 标志时。该结构体由 :ref:`VIDIOC_QUERYCAP` ioctl 返回。

驱动程序可能需要 CPU 复制数据，但它们也可能支持直接内存访问（DMA），从或到用户内存，因此这种方法不一定比仅仅交换缓冲区指针的其他方法效率低。然而，由于没有传递像帧计数器或时间戳这样的元信息，这种方法被认为是较差的。这些信息对于识别丢帧和与其他数据流同步是必要的。不过这也是最简单的 I/O 方法，几乎不需要任何设置就可以交换数据。它允许在命令行上执行类似以下操作（vidctrl 工具是虚构的）：

.. code-block:: none

    $ vidctrl /dev/video --input=0 --format=YUYV --size=352x288
    $ dd if=/dev/video of=myimage.422 bs=202752 count=1

应用程序使用 :c:func:`read()` 函数来从设备读取数据，使用 :c:func:`write()` 函数来写入数据。如果驱动程序与应用程序交换数据，则必须实现一种 I/O 方法，但不必是这种方法。[#f1]_ 当支持读取或写入时，驱动程序还必须支持 :c:func:`select()` 和 :c:func:`poll()` 函数。[#f2]_

.. [#f1]
   如果应用程序能够依赖于驱动程序支持所有 I/O 接口当然是理想的，但鉴于复杂的内存映射 I/O 对某些设备来说并不总是适用，我们没有理由要求这种接口，而这种接口主要对捕获静态图像的简单应用最有用。
.. [#f2]
   在驱动程序级别，:c:func:`select()` 和 :c:func:`poll()` 是相同的，并且 :c:func:`select()` 太重要了，不能作为可选功能。
