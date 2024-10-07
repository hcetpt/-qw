SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_ENC_INDEX:

************************
ioctl VIDIOC_G_ENC_INDEX
************************

名称
====

VIDIOC_G_ENC_INDEX - 获取压缩视频流的元数据

概要
========

.. c:macro:: VIDIOC_G_ENC_INDEX

``int ioctl(int fd, VIDIOC_G_ENC_INDEX, struct v4l2_enc_idx *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_enc_idx` 的指针
描述
===========

:ref:`VIDIOC_G_ENC_INDEX <VIDIOC_G_ENC_INDEX>` ioctl 提供当前从驱动程序读取的压缩视频流的元数据，这对于在不解码的情况下随机访问流非常有用。
为了读取这些数据，应用程序必须使用指向结构体 :c:type:`v4l2_enc_idx` 的指针调用 :ref:`VIDIOC_G_ENC_INDEX <VIDIOC_G_ENC_INDEX>`。成功时，驱动程序会填充 ``entry`` 数组，并将写入的元素数量存储在 ``entries`` 字段中，同时初始化 ``entries_cap`` 字段。
``entry`` 数组中的每个元素包含关于一帧图像的元数据。一次 :ref:`VIDIOC_G_ENC_INDEX <VIDIOC_G_ENC_INDEX>` 调用最多从驱动程序缓冲区中读取 ``V4L2_ENC_IDX_ENTRIES`` 个条目，该缓冲区最多可以容纳 ``entries_cap`` 个条目。这个数字可能比 ``V4L2_ENC_IDX_ENTRIES`` 更大或更小，但不能为零。如果应用程序未能及时读取元数据，则最旧的条目将会丢失。当缓冲区为空或没有正在进行的捕获/编码时，``entries`` 将为零。
目前此 ioctl 仅定义了适用于 MPEG-2 程序流和视频基本流。

.. tabularcolumns:: |p{4.2cm}|p{6.2cm}|p{6.9cm}|

.. c:type:: v4l2_enc_idx

.. flat-table:: 结构体 v4l2_enc_idx
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 3 8

    * - __u32
      - ``entries``
      - 驱动程序在 ``entry`` 数组中存储的条目数量
    * - __u32
      - ``entries_cap``
      - 驱动程序可以缓冲的条目数量。必须大于零
    * - __u32
      - ``reserved``\[4\]
      - 保留用于将来扩展。驱动程序必须将数组设置为零
    * - struct :c:type:`v4l2_enc_idx_entry`
      - ``entry``\[``V4L2_ENC_IDX_ENTRIES``\]
      - 压缩视频流的元数据。数组中的每个元素对应一个图片，按其 ``offset`` 升序排列
```markdown
.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_enc_idx_entry

.. flat-table:: 结构体 v4l2_enc_idx_entry
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u64
      - ``offset``
      - 从压缩视频流的开始到该图片开始处的字节偏移量，即根据 :ref:`mpeg2part1` 定义的 *PES 包头* 或根据 :ref:`mpeg2part2` 定义的 *图片头*。当编码器停止时，驱动程序将偏移量重置为零。
* - __u64
      - ``pts``
      - 根据 :ref:`mpeg2part1` 定义的该图片的 33 位 *Presentation Time Stamp*。
* - __u32
      - ``length``
      - 该图片的长度（以字节为单位）。
* - __u32
      - ``flags``
      - 包含该图片编码类型的标志，详见 :ref:`enc-idx-flags`。
* - __u32
      - ``reserved``\ [2]
      - 保留用于将来扩展。驱动程序必须将数组设置为零。

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _enc-idx-flags:

.. flat-table:: 索引条目标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_ENC_IDX_FRAME_I``
      - 0x00
      - 这是一个帧内编码的图片。
* - ``V4L2_ENC_IDX_FRAME_P``
      - 0x01
      - 这是一个前向预测编码的图片。
* - ``V4L2_ENC_IDX_FRAME_B``
      - 0x02
      - 这是一个双向预测编码的图片。
* - ``V4L2_ENC_IDX_FRAME_MASK``
      - 0x0F
      - 将标志字段与这个掩码进行 *AND* 操作，以获取图片的编码类型。

返回值
======

成功时返回 0，出错时返回 -1 并且设置 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
```
当然，请提供你需要翻译的文本。
