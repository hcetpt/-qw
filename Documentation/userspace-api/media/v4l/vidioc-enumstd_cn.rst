SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间: V4L

.. _VIDIOC_ENUMSTD:

*******************************************
ioctl VIDIOC_ENUMSTD, VIDIOC_SUBDEV_ENUMSTD
*******************************************

名称
====

VIDIOC_ENUMSTD - VIDIOC_SUBDEV_ENUMSTD - 列出支持的视频标准

概要
========

.. c:macro:: VIDIOC_ENUMSTD

``int ioctl(int fd, VIDIOC_ENUMSTD, struct v4l2_standard *argp)``

.. c:macro:: VIDIOC_SUBDEV_ENUMSTD

``int ioctl(int fd, VIDIOC_SUBDEV_ENUMSTD, struct v4l2_standard *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_standard` 的指针
描述
===========

为了查询视频标准的属性，特别是自定义（驱动程序定义）的标准，应用程序需要初始化结构体 :c:type:`v4l2_standard` 的 ``index`` 字段，并通过指向该结构体的指针调用 :ref:`VIDIOC_ENUMSTD` ioctl。驱动程序将填充结构体的其余部分，或者在索引超出范围时返回一个 ``EINVAL`` 错误码。为了枚举所有标准，应用程序应当从索引零开始，每次递增一，直到驱动程序返回 ``EINVAL``。在切换视频输入或输出后，驱动程序可能会枚举不同的标准集。[#f1]_

.. c:type:: v4l2_standard

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_standard
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``index``
      - 视频标准的编号，由应用程序设置
* - :ref:`v4l2_std_id <v4l2-std-id>`
      - ``id``
      - 该字段中的位表示标准为 :ref:`v4l2-std-id` 中列出的常见标准之一，或者如果位 32 到 63 被设置则表示自定义标准。如果硬件不区分这些标准，则可以设置多个位；然而，不同的索引并不表示相反的情况。“id”必须是唯一的。对于任何输入或输出，没有其他枚举的结构体 :c:type:`v4l2_standard` 可以包含相同的位集
* - __u8
      - ``name``\ [24]
      - 标准名称，例如：“PAL-B/G”，“NTSC Japan”。这是一个以 NUL 结尾的 ASCII 字符串，用于提供给用户的信息
* - struct :c:type:`v4l2_fract`
      - ``frameperiod``
      - 帧周期（不是场周期），例如 M/NTSC 的帧周期为 1001 / 30000 秒
* - __u32
      - ``framelines``
      - 包括消隐在内的每帧总行数，例如 PAL/B 的行数为 625
* - __u32
      - ``reserved``\ [4]
      - 保留供将来扩展使用。驱动程序必须将数组设置为零
```markdown
类型：v4l2_fract

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: 结构体 v4l2_fract
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``numerator``
      -
    * - __u32
      - ``denominator``
      -

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. _v4l2-std-id:

.. flat-table:: 类型定义 v4l2_std_id
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u64
      - ``v4l2_std_id``
      - 此类型是一个集合，每个比特代表一种视频标准，如下表和 :ref:`video-standards` 所示。最显著的 32 位保留用于自定义（驱动程序定义）的视频标准。
.. code-block:: c

    #define V4L2_STD_PAL_B          ((v4l2_std_id)0x00000001)
    #define V4L2_STD_PAL_B1         ((v4l2_std_id)0x00000002)
    #define V4L2_STD_PAL_G          ((v4l2_std_id)0x00000004)
    #define V4L2_STD_PAL_H          ((v4l2_std_id)0x00000008)
    #define V4L2_STD_PAL_I          ((v4l2_std_id)0x00000010)
    #define V4L2_STD_PAL_D          ((v4l2_std_id)0x00000020)
    #define V4L2_STD_PAL_D1         ((v4l2_std_id)0x00000040)
    #define V4L2_STD_PAL_K          ((v4l2_std_id)0x00000080)

    #define V4L2_STD_PAL_M          ((v4l2_std_id)0x00000100)
    #define V4L2_STD_PAL_N          ((v4l2_std_id)0x00000200)
    #define V4L2_STD_PAL_Nc         ((v4l2_std_id)0x00000400)
    #define V4L2_STD_PAL_60         ((v4l2_std_id)0x00000800)

``V4L2_STD_PAL_60`` 是一种混合标准，具有 525 行、60 Hz 刷新率，并采用带有 4.43 MHz 色副载波的 PAL 彩色调制。一些 PAL 视频录像机可以在这种模式下播放 NTSC 录像带以在 50/60 Hz 不敏感的 PAL 电视上显示。
.. code-block:: c

    #define V4L2_STD_NTSC_M         ((v4l2_std_id)0x00001000)
    #define V4L2_STD_NTSC_M_JP      ((v4l2_std_id)0x00002000)
    #define V4L2_STD_NTSC_443       ((v4l2_std_id)0x00004000)

``V4L2_STD_NTSC_443`` 是一种混合标准，具有 525 行、60 Hz 刷新率，并采用带有 4.43 MHz 色副载波的 NTSC 彩色调制。
.. code-block:: c

    #define V4L2_STD_NTSC_M_KR      ((v4l2_std_id)0x00008000)

    #define V4L2_STD_SECAM_B        ((v4l2_std_id)0x00010000)
    #define V4L2_STD_SECAM_D        ((v4l2_std_id)0x00020000)
    #define V4L2_STD_SECAM_G        ((v4l2_std_id)0x00040000)
    #define V4L2_STD_SECAM_H        ((v4l2_std_id)0x00080000)
    #define V4L2_STD_SECAM_K        ((v4l2_std_id)0x00100000)
    #define V4L2_STD_SECAM_K1       ((v4l2_std_id)0x00200000)
    #define V4L2_STD_SECAM_L        ((v4l2_std_id)0x00400000)
    #define V4L2_STD_SECAM_LC       ((v4l2_std_id)0x00800000)

    /* ATSC/HDTV */
    #define V4L2_STD_ATSC_8_VSB     ((v4l2_std_id)0x01000000)
    #define V4L2_STD_ATSC_16_VSB    ((v4l2_std_id)0x02000000)

``V4L2_STD_ATSC_8_VSB`` 和 ``V4L2_STD_ATSC_16_VSB`` 是美国地面数字电视标准。目前 V4L2 API 不支持数字电视。请参阅 Linux DVB API：`https://linuxtv.org <https://linuxtv.org>`__。
.. code-block:: c

    #define V4L2_STD_PAL_BG         (V4L2_STD_PAL_B         | \
                                     V4L2_STD_PAL_B1        | \
                                     V4L2_STD_PAL_G)
    #define V4L2_STD_B              (V4L2_STD_PAL_B         | \
                                     V4L2_STD_PAL_B1        | \
                                     V4L2_STD_SECAM_B)
    #define V4L2_STD_GH             (V4L2_STD_PAL_G         | \
                                     V4L2_STD_PAL_H         | \
                                     V4L2_STD_SECAM_G       | \
                                     V4L2_STD_SECAM_H)
    #define V4L2_STD_PAL_DK         (V4L2_STD_PAL_D         | \
                                     V4L2_STD_PAL_D1        | \
                                     V4L2_STD_PAL_K)
    #define V4L2_STD_PAL            (V4L2_STD_PAL_BG        | \
                                     V4L2_STD_PAL_DK        | \
                                     V4L2_STD_PAL_H         | \
                                     V4L2_STD_PAL_I)
    #define V4L2_STD_NTSC           (V4L2_STD_NTSC_M        | \
                                     V4L2_STD_NTSC_M_JP     | \
                                     V4L2_STD_NTSC_M_KR)
    #define V4L2_STD_MN             (V4L2_STD_PAL_M         | \
                                     V4L2_STD_PAL_N         | \
                                     V4L2_STD_PAL_Nc        | \
                                     V4L2_STD_NTSC)
    #define V4L2_STD_SECAM_DK       (V4L2_STD_SECAM_D       | \
                                     V4L2_STD_SECAM_K       | \
                                     V4L2_STD_SECAM_K1)
    #define V4L2_STD_DK             (V4L2_STD_PAL_DK        | \
                                     V4L2_STD_SECAM_DK)

    #define V4L2_STD_SECAM          (V4L2_STD_SECAM_B       | \
                                     V4L2_STD_SECAM_G       | \
                                     V4L2_STD_SECAM_H       | \
                                     V4L2_STD_SECAM_DK      | \
                                     V4L2_STD_SECAM_L       | \
                                     V4L2_STD_SECAM_LC)

    #define V4L2_STD_525_60         (V4L2_STD_PAL_M         | \
                                     V4L2_STD_PAL_60        | \
                                     V4L2_STD_NTSC          | \
                                     V4L2_STD_NTSC_443)
    #define V4L2_STD_625_50         (V4L2_STD_PAL           | \
                                     V4L2_STD_PAL_N         | \
                                     V4L2_STD_PAL_Nc        | \
                                     V4L2_STD_SECAM)

    #define V4L2_STD_UNKNOWN        0
    #define V4L2_STD_ALL            (V4L2_STD_525_60        | \
                                     V4L2_STD_625_50)

.. raw:: latex

    \begingroup
    \tiny
    \setlength{\tabcolsep}{2pt}

..                            NTSC/M   PAL/M    /N       /B       /D       /H       /I        SECAM/B    /D       /K1     /L
.. tabularcolumns:: |p{1.43cm}|p{1.38cm}|p{1.59cm}|p{1.7cm}|p{1.7cm}|p{1.17cm}|p{0.64cm}|p{1.71cm}|p{1.6cm}|p{1.07cm}|p{1.07cm}|p{1.07cm}|

.. _video-standards:

.. flat-table:: 视频标准（基于 :ref:`itu470`）
    :header-rows:  1
    :stub-columns: 0

    * - 特性
      - M/NTSC [#f2]_
      - M/PAL
      - N/PAL [#f3]_
      - B, B1, G/PAL
      - D, D1, K/PAL
      - H/PAL
      - I/PAL
      - B, G/SECAM
      - D, K/SECAM
      - K1/SECAM
      - L/SECAM
    * - 帧行数
      - :cspan:`1` 525
      - :cspan:`8` 625
    * - 帧周期 (秒)
      - :cspan:`1` 1001/30000
      - :cspan:`8` 1/25
    * - 色度副载波频率 (赫兹)
      - 3579545 ± 10
      - 3579611.49 ± 10
      - 4433618.75 ± 5

	(3582056.25 ± 5)
      - :cspan:`3` 4433618.75 ± 5
      - 4433618.75 ± 1
      - :cspan:`2` f\ :sub:`OR` = 4406250 ± 2000,

	f\ :sub:`OB` = 4250000 ± 2000
    * - 名义射频信道带宽 (兆赫)
      - 6
      - 6
      - 6
      - B: 7; B1, G: 8
      - 8
      - 8
      - 8
      - 8
      - 8
      - 8
      - 8
    * - 音频载波相对于图像载波 (兆赫)
      - 4.5
      - 4.5
      - 4.5
      - 5.5 ± 0.001  [#f4]_  [#f5]_  [#f6]_  [#f7]_
      - 6.5 ± 0.001
      - 5.5
      - 5.9996 ± 0.0005
      - 5.5 ± 0.001
      - 6.5 ± 0.001
      - 6.5
      - 6.5 [#f8]_

.. raw:: latex

    \endgroup

返回值
======
成功时返回 0，错误时返回 -1 并设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
EINVAL
    结构体 :c:type:`v4l2_standard` 的 ``index`` 超出了范围
ENODATA
    当前输入或输出不支持标准视频定时
.. [#f1]
   支持的标准可能重叠，我们需要一个明确的集合来查找由 :ref:`VIDIOC_G_STD <VIDIOC_G_STD>` 返回的当前标准。
.. [#f2]
   日本使用类似于 M/NTSC 的标准（V4L2_STD_NTSC_M_JP）
```
.. [#f3]
   括号中的值适用于在阿根廷使用的 N/PAL（也称为 N\ :sub:`C`）系统（V4L2_STD_PAL_Nc）
   
.. [#f4]
   在德意志联邦共和国、奥地利、意大利、荷兰、斯洛伐克和瑞士，使用了一种双音频载波系统，第二个载波的频率比第一个载波高 242.1875 kHz。澳大利亚在立体声传输中也使用了类似的系统。
   
.. [#f5]
   新西兰使用的音频载波频率比视频载波高出 5.4996 ± 0.0005 MHz。
   
.. [#f6]
   在丹麦、芬兰、新西兰、瑞典和西班牙使用了一种双音频载波系统。冰岛、挪威和波兰也在引入相同的系统。第二个载波比视频载波高 5.85 MHz，并采用 DQPSK 调制，数据速率为 728 kbit/s 的声音和数据复用。（NICAM 系统）
   
.. [#f7]
   在英国使用了一种双音频载波系统。第二个音频载波比视频载波高 6.552 MHz，并采用 DQPSK 调制，数据速率为 728 kbit/s 的声音和数据复用，能够承载两个音频通道。（NICAM 系统）
   
.. [#f8]
   在法国，除了主音频载波外，还可以使用一个距离视频载波 5.85 MHz 的数字载波。该载波采用差分编码 QPSK 调制，数据速率为 728 kbit/s 的声音和数据复用器，能够承载两个音频通道。（NICAM 系统）
