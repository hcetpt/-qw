SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

.. _extended-controls:

******************
扩展控制 API
******************

简介
============

最初设计的控制机制是用于用户设置（如亮度、饱和度等）。然而，它被证明是一个实现更复杂驱动程序 API 的非常有用的模型，每个驱动程序只实现一个更大的 API 的一部分。MPEG 编码 API 是设计和实现这个扩展控制机制的主要推动力：MPEG 标准相当庞大，目前支持的硬件 MPEG 编码器各自只实现了该标准的一部分。此外，许多与视频如何编码成 MPEG 流相关的参数是特定于 MPEG 编码芯片的，因为 MPEG 标准仅定义了生成的 MPEG 流的格式，而不是视频如何实际编码成该格式。

不幸的是，原始控制 API 缺乏一些新用途所需的功能，因此它被扩展成了扩展控制 API。尽管 MPEG 编码 API 是第一个使用扩展控制 API 的尝试，但现在也有其他类别的扩展控制，例如相机控制和 FM 发射机控制。以下文字将描述扩展控制 API 及其所有扩展控制类别。

扩展控制 API
========================

提供了三个新的 ioctl：

:ref:`VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>`，
:ref:`VIDIOC_S_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 和
:ref:`VIDIOC_TRY_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>`。

这些 ioctl 作用于控制数组（而 :ref:`VIDIOC_G_CTRL <VIDIOC_G_CTRL>` 和
:ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` ioctl 作用于单个控制）。这是必要的，因为通常需要原子地更改多个控制项。

每个新的 ioctl 都期望一个指向 struct :c:type:`v4l2_ext_controls` 的指针。此结构包含对控制数组的指针、该数组中的控制项数以及一个控制类别。控制类别用于将类似的控制项分组到一个类别中。例如，控制类别 ``V4L2_CTRL_CLASS_USER`` 包含所有用户控制（即所有也可以使用旧的 :ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` ioctl 设置的控制）。控制类别 ``V4L2_CTRL_CLASS_CODEC`` 包含与编解码器相关的控制项。

控制数组中的所有控制项必须属于指定的控制类别。如果不符合此条件，则返回错误。

还可以使用空的控制数组（``count`` == 0）来检查是否支持指定的控制类别。

控制数组是一个 struct :c:type:`v4l2_ext_control` 数组。struct :c:type:`v4l2_ext_control` 与 struct :c:type:`v4l2_control` 非常相似，只是它还允许传递 64 位值和指针。

由于 struct :c:type:`v4l2_ext_control` 支持指针，现在可以有复合类型的控制项，例如多维数组和/或结构体。在枚举控制项时，您需要指定 ``V4L2_CTRL_FLAG_NEXT_COMPOUND`` 才能看到这样的复合控制项。换句话说，这些具有复合类型的控制项应仅用于编程中。
由于这类复合控件需要暴露比 `:ref: VIDIOC_QUERYCTRL <VIDIOC_QUERYCTRL>` 更多的信息，因此添加了 `:ref: VIDIOC_QUERY_EXT_CTRL <VIDIOC_QUERYCTRL>` ioctl。特别是，这个 ioctl 可以提供 N 维数组的维度信息，如果这个控件包含多个元素。

.. note::

   1. 需要注意的是，由于控件的灵活性，必须检查你想要设置的控件是否在驱动程序中支持以及有效值范围是什么。因此，请使用 `:ref: VIDIOC_QUERYCTRL` 来检查这一点。
   2. 对于类型为 `V4L2_CTRL_TYPE_MENU` 的控件，某些菜单索引可能不被支持（`VIDIOC_QUERYMENU` 将返回错误）。一个很好的例子是支持的 MPEG 音频比特率列表。一些驱动程序只支持一种或两种比特率，而其他驱动程序则支持更广泛的范围。

所有控件都使用机器字节序。

枚举扩展控件
=============================

推荐的枚举扩展控件的方法是结合使用 `:ref: VIDIOC_QUERYCTRL` 和 `V4L2_CTRL_FLAG_NEXT_CTRL` 标志：

.. code-block:: c

    struct v4l2_queryctrl qctrl;

    qctrl.id = V4L2_CTRL_FLAG_NEXT_CTRL;
    while (0 == ioctl (fd, VIDIOC_QUERYCTRL, &qctrl)) {
        /* ... */
        qctrl.id |= V4L2_CTRL_FLAG_NEXT_CTRL;
    }

初始控件 ID 设置为 0 并与 `V4L2_CTRL_FLAG_NEXT_CTRL` 标志进行 OR 操作。`VIDIOC_QUERYCTRL` ioctl 将返回具有比指定 ID 更高 ID 的第一个控件。如果没有找到这样的控件，则会返回错误。

如果你想获取特定控件类中的所有控件，可以将初始 `qctrl.id` 值设置为该控件类，并添加一个额外的检查，在遇到不同控件类时跳出循环：

.. code-block:: c

    qctrl.id = V4L2_CTRL_CLASS_CODEC | V4L2_CTRL_FLAG_NEXT_CTRL;
    while (0 == ioctl(fd, VIDIOC_QUERYCTRL, &qctrl)) {
        if (V4L2_CTRL_ID2CLASS(qctrl.id) != V4L2_CTRL_CLASS_CODEC)
            break;
        /* ... */
        qctrl.id |= V4L2_CTRL_FLAG_NEXT_CTRL;
    }

32 位的 `qctrl.id` 值分为三个位范围：最上面的 4 位保留用于标志（例如 `V4L2_CTRL_FLAG_NEXT_CTRL`），实际上并不是 ID 的一部分。剩下的 28 位形成控件 ID，其中最高 12 位定义控件类，最低 16 位标识控件类中的控件。保证这最后 16 位对于控件始终是非零的。从 0x1000 开始的范围保留用于驱动程序特定的控件。宏 `V4L2_CTRL_ID2CLASS(id)` 根据控件 ID 返回控件类 ID。

如果驱动程序不支持扩展控件，则在 `VIDIOC_QUERYCTRL` 与 `V4L2_CTRL_FLAG_NEXT_CTRL` 结合使用时会失败。在这种情况下，应使用旧方法枚举控件（参见 :ref: `enum_all_controls`）。但如果支持扩展控件，则保证枚举所有控件，包括驱动程序私有的控件。

创建控件面板
=======================

可以为图形用户界面创建控件面板，让用户选择各种控件。基本上，你需要按照上述方法遍历所有控件。每个控件类都以类型为 `V4L2_CTRL_TYPE_CTRL_CLASS` 的控件开始。`VIDIOC_QUERYCTRL` 将返回此控件类的名称，可以用作控件面板中选项卡的标题。

结构体 `:ref: v4l2_queryctrl <v4l2-queryctrl>` 的 `flags` 字段还包含了有关控件行为的提示。请参阅 `:ref: VIDIOC_QUERYCTRL` 文档以获取更多详细信息。
