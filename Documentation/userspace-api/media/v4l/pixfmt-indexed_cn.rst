.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _pixfmt-indexed:

**************
索引格式
**************

在该格式中，每个像素由一个指向包含 256 项的 ARGB 调色板的 8 位索引表示。它仅用于
:ref:`视频输出覆盖层 <osd>`。访问调色板没有专用的 ioctl，必须通过 Linux 帧缓冲 API 的 ioctl 来实现。

.. flat-table:: 索引图像格式
    :header-rows:  2
    :stub-columns: 0

    * - 标识符
      - 代码
      -
      - :cspan:`7` 字节 0
    * -
      -
      - 位
      - 7
      - 6
      - 5
      - 4
      - 3
      - 2
      - 1
      - 0
    * .. _V4L2-PIX-FMT-PAL8:

      - ``V4L2_PIX_FMT_PAL8``
      - 'PAL8'
      -
      - i\ :sub:`7`
      - i\ :sub:`6`
      - i\ :sub:`5`
      - i\ :sub:`4`
      - i\ :sub:`3`
      - i\ :sub:`2`
      - i\ :sub:`1`
      - i\ :sub:`0`
