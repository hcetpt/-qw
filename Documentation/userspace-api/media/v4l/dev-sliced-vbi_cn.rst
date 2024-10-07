SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: V4L

.. _分片:

*************************
分片 VBI 数据接口
*************************

VBI 代表垂直消隐间隔，是模拟视频信号中行序列中的一个间隙。在 VBI 期间不传输图像信息，这使得阴极射线管电视的电子束有时间返回到屏幕顶部。
分片 VBI 设备使用硬件来解调在 VBI 中传输的数据。V4L2 驱动程序不应通过软件实现这一点，请参阅 :ref:`原始 VBI 接口 <raw-vbi>`。数据以固定大小的短数据包形式传递，每个扫描行覆盖一个数据包。每帧的数据包数量是可变的。
分片 VBI 捕获和输出设备通过与原始 VBI 设备相同的字符特殊文件访问。当驱动程序支持这两种接口时，默认功能是“/dev/vbi”设备的原始 VBI 捕获或输出，并且在调用下面定义的 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 后才提供分片 VBI 功能。同样，“/dev/video”设备可能支持分片 VBI API，但这里的默认功能是视频捕获或输出。
如果驱动程序支持同时传递原始和分片 VBI 数据，则必须使用不同的文件描述符。
查询能力
=====================

支持分片 VBI 捕获或输出 API 的设备在通过 :ref:`VIDIOC_QUERYCAP` ioctl 返回的 :c:type:`v4l2_capability` 结构体的 `capabilities` 字段中设置 `V4L2_CAP_SLICED_VBI_CAPTURE` 或 `V4L2_CAP_SLICED_VBI_OUTPUT` 标志。至少应支持一种读/写或流式传输 :ref:`I/O 方法 <io>`。分片 VBI 设备可能具有调谐器或调制器。
补充功能
======================

如果分片 VBI 设备具备这些功能，它们应支持 :ref:`视频输入或输出 <video>` 和 :ref:`调谐器或调制器 <tuner>` 的 ioctl，并且可以支持 :ref:`控制` ioctl。
:ref:`视频标准 <standard>` ioctl 提供了编程分片 VBI 设备所需的关键信息，因此必须支持这些 ioctl。
.. _分片-vbi-格式协商:

分片 VBI 格式协商
=============================

为了找出硬件支持哪些数据服务，应用程序可以调用 :ref:`VIDIOC_G_SLICED_VBI_CAP <VIDIOC_G_SLICED_VBI_CAP>` ioctl。
所有实现了分片 VBI 接口的驱动程序都必须支持此 ioctl。结果可能与 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 的结果不同，尤其是在硬件每帧能够捕获或输出的 VBI 行数或它能够在给定行上识别的服务数量有限的情况下。例如，在 PAL 线 16 上，硬件可能能够查找 VPS 或 Teletext 信号，但不能同时查找两者。
要确定当前选定的服务，应用程序将结构体 :c:type:`v4l2_format` 的 `type` 字段设置为 `V4L2_BUF_TYPE_SLICED_VBI_CAPTURE` 或 `V4L2_BUF_TYPE_SLICED_VBI_OUTPUT`，然后 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` ioctl 将填充 `fmt.sliced` 成员，即结构体 :c:type:`v4l2_sliced_vbi_format`。
应用程序可以通过初始化或修改 `fmt.sliced` 成员并调用指向 `v4l2_format` 结构体的 `VIDIOC_S_FMT` ioctl 来请求不同的参数。
分片 VBI API 比原始 VBI API 更复杂，因为硬件必须被告知在每一行上预期哪个 VBI 服务。并非所有服务在所有行上都受硬件支持（特别是在 VBI 输出时，Teletext 经常不受支持，并且其他服务只能插入到特定行中）。但在许多情况下，仅仅设置 `service_set` 字段为所需的服务，并让驱动程序根据硬件能力填充 `service_lines` 数组就足够了。只有当需要更精确的控制时，程序员才应显式设置 `service_lines` 数组。

`VIDIOC_S_FMT` ioctl 根据硬件能力修改参数。当驱动程序在此时分配资源时，如果所需的资源暂时不可用，则可能会返回 `EBUSY` 错误代码。其他可能返回 `EBUSY` 的资源分配点包括 `VIDIOC_STREAMON` ioctl 以及第一次 `read()`、`write()` 和 `select()` 调用。

.. c:type:: v4l2_sliced_vbi_format

`struct v4l2_sliced_vbi_format`
-------------------------------

.. raw:: latex

    \begingroup
    \scriptsize
    \setlength{\tabcolsep}{2pt}

.. tabularcolumns:: |p{.85cm}|p{3.3cm}|p{4.45cm}|p{4.45cm}|p{4.45cm}|

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 3 2 2 2

    * - __u16
      - `service_set`
      - :cspan:`2`

        如果 `service_set` 在传递给 `VIDIOC_S_FMT` 或 `VIDIOC_TRY_FMT` 时非零，则驱动程序将根据此字段指定的服务填充 `service_lines` 数组。例如，如果 `service_set` 初始化为 `V4L2_SLICED_TELETEXT_B | V4L2_SLICED_WSS_625`，则 cx25840 视频解码器驱动程序会将两个场的第 7-22 行设置为 `V4L2_SLICED_TELETEXT_B`，并将第一场的第 23 行设置为 `V4L2_SLICED_WSS_625`。如果 `service_set` 设置为零，则使用 `service_lines` 的值。
        返回时，驱动程序将此字段设置为返回的 `service_lines` 数组的所有元素的并集。它可能包含比请求的服务更少的服务，甚至只是一个服务，如果硬件无法同时处理更多服务。如果硬件不支持任何请求的服务，它可能是空的（零）。
    * - __u16
      - `service_lines`\ [2][24]
      - :cspan:`2`

        应用程序初始化此数组以指定驱动程序应在相应扫描线上查找或插入的数据服务集。
        驱动程序根据硬件能力返回请求的集合、子集（可能只有一个服务），或空集。
        当硬件无法在同一行上处理多个服务时，驱动程序应选择一个。无法假设驱动程序选择哪个服务。
        数据服务定义在 :ref:`vbi-services2` 中。数组索引映射到 ITU-R 行号\ [#f2]_ 如下：
    * -
      -
      - 元素
      - 525 行系统
      - 625 行系统
    * -
      -
      - `service_lines`\ [0][1]
      - 1
      - 1
    * -
      -
      - `service_lines`\ [0][23]
      - 23
      - 23
    * -
      -
      - `service_lines`\ [1][1]
      - 264
      - 314
    * -
      -
      - `service_lines`\ [1][23]
      - 286
      - 336
    * -
      -
      - :cspan:`2` 驱动程序必须将 `service_lines` [0][0] 和 `service_lines`\ [1][0] 设置为零。`V4L2_VBI_ITU_525_F1_START`、`V4L2_VBI_ITU_525_F2_START`、`V4L2_VBI_ITU_625_F1_START` 和 `V4L2_VBI_ITU_625_F2_START` 定义提供了每个场的起始行号，适用于每种 525 或 625 行格式。请记住 ITU 行号从 1 开始，而不是从 0 开始。
    * - __u32
      - `io_size`
      - :cspan:`2` 单次 `read()` 或 `write()` 调用传递的最大字节数，以及 `VIDIOC_QBUF` 和 `VIDIOC_DQBUF` ioctl 的缓冲区大小（以字节为单位）。驱动程序将此字段设置为 `v4l2_sliced_vbi_data` 结构体的大小乘以返回的 `service_lines` 数组中的非零元素数量（即可能携带数据的行数）。
* - `__u32`
  - `reserved`\ [2]
  - :cspan:`2` 该数组保留用于未来的扩展
  应用程序和驱动程序必须将其设置为零
.. raw:: latex

    \endgroup

.. _vbi-services2:

分片 VBI 服务
--------------

.. raw:: latex

    \footnotesize

.. tabularcolumns:: |p{4.2cm}|p{1.1cm}|p{2.1cm}|p{2.0cm}|p{6.5cm}|

.. flat-table::
    :header-rows:  1
    :stub-columns: 0
    :widths:       2 1 1 2 2

    * - 符号
      - 值
      - 参考
      - 行数，通常
      - 载荷
    * - `V4L2_SLICED_TELETEXT_B`（Teletext 系统 B）
      - 0x0001
      - :ref:`ets300706`，

	:ref:`itu653`
      - PAL/SECAM 行 7-22，320-335（第二场 7-22）
      - Teletext 数据包的最后 42 字节（共 45 字节），不包括时钟运行和帧码，按低位优先传输
* - `V4L2_SLICED_VPS`
      - 0x0400
      - :ref:`ets300231`
      - PAL 行 16
      - 根据 ETS 300 231 图 9 的第 3 到 15 字节，按低位优先传输
* - `V4L2_SLICED_CAPTION_525`
      - 0x1000
      - :ref:`cea608`
      - NTSC 行 21，284（第二场 21）
      - 包括奇偶校验位的两个字节，按低位优先传输
* - `V4L2_SLICED_WSS_625`
      - 0x4000
      - :ref:`itu1119`，

	:ref:`en300294`
      - PAL/SECAM 行 23
      - 见下面的 :ref:`v4l2-sliced-wss-625-payload`
* - `V4L2_SLICED_VBI_525`
      - 0x1000
      - :cspan:`2` 适用于 525 行系统的服务集
* - `V4L2_SLICED_VBI_625`
      - 0x4401
      - :cspan:`2` 适用于 625 行系统的服务集
.. raw:: latex

    \normalsize

当应用程序尝试在没有事先格式协商的情况下读取或写入数据、切换视频标准（这可能会使已协商的 VBI 参数失效）以及切换视频输入（这可能会作为副作用改变视频标准）时，驱动程序可以返回 `EINVAL` 错误代码。当应用程序尝试在 I/O 进行中（在 :ref:`VIDIOC_STREAMON` 和 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>` 调用之间，以及第一次 :c:func:`read()` 或 :c:func:`write()` 调用之后）更改格式时，:ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 可能会返回 `EBUSY` 错误代码。
.. _v4l2-sliced-wss-625-payload:

`V4L2_SLICED_WSS_625` 的载荷
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`V4L2_SLICED_WSS_625` 的载荷如下：

           +-----+------------------+-----------------------+
	   | 字节 |          0         |            1          |
           +-----+--------+---------+-----------+-----------+
	   |      | MSB    | LSB     | MSB       | LSB       |
           |      +-+-+-+--+--+-+-+--+--+-+--+---+---+--+-+--+
	   | 位   |7|6|5|4 | 3|2|1|0 | x|x|13|12 | 11|10|9|8 |
           +-----+-+-+-+--+--+-+-+--+--+-+--+---+---+--+-+--+

读取和写入分片 VBI 数据
=======================

单个 :c:func:`read()` 或 :c:func:`write()` 调用必须传递属于一个视频帧的所有数据。也就是说，一个结构体 :c:type:`v4l2_sliced_vbi_data` 的数组，包含一个或多个元素，并且总大小不超过 `io_size` 字节。同样，在流式 I/O 模式下，一个 `io_size` 字节的缓冲区必须包含一个视频帧的数据。未使用的结构体 :c:type:`v4l2_sliced_vbi_data` 元素的 `id` 必须为零
```markdown
### 类型：v4l2_sliced_vbi_data

#### 结构体 v4l2_sliced_vbi_data
---------------------------

| 字段         | 类型     | 描述                                                                                           |
|--------------|----------|-----------------------------------------------------------------------------------------------|
| `__u32`      | `id`     | 标识此数据包类型的一个标志，来自 :ref:`vbi-services`。仅设置一个比特位。如果捕获的数据包的 `id` 为零，则该数据包为空，其他字段的内容是未定义的，应用程序应忽略空数据包。如果输出数据包的 `id` 为零，则 `data` 字段的内容是未定义的，并且驱动程序不应在此请求的 `field` 和 `line` 上插入数据。|
| `__u32`      | `field`  | 此数据所捕获或应插入的视频场号。`0` 表示第一场，`1` 表示第二场。                             |
| `__u32`      | `line`   | 此数据所捕获或应插入的场（而非帧）行号。参见 :ref:`vbi-525` 和 :ref:`vbi-625` 以获取有效值。如果硬件无法可靠地识别扫描线，则切片 VBI 捕获设备可以将所有数据包的行号设为 `0`。场号必须始终有效。 |
| `__u32`      | `reserved` | 保留字段，用于将来扩展。应用程序和驱动程序必须将其设为零。                                     |
| `__u8`       | `data[48]` | 数据包的有效载荷。参见 :ref:`vbi-services` 以获取每种数据类型的内容和字节数。填充字节的内容是未定义的，驱动程序和应用程序应忽略它们。 |

数据包总是按递增的行号顺序传递，不包含重复的行号。当应用程序违反此规则时，:c:func:`write()` 函数和 :ref:`VIDIOC_QBUF` ioctl 必须返回 `EINVAL` 错误代码。当应用程序传递了错误的场号或行号，或者传递了一个未与 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` 或 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 协商过的 `field`, `line` 和 `id` 组合时，也必须返回 `EINVAL` 错误代码。如果行号未知，驱动程序必须按传输顺序传递数据包。驱动程序可以在数据包数组中的任何位置插入带有 `id` 设为零的空数据包。

为了保证同步并区分丢帧情况，当捕获的帧不携带任何请求的数据服务时，驱动程序必须传递一个或多个空数据包。当应用程序未能及时传递 VBI 数据以供输出时，驱动程序必须再次输出最后一个 VPS 和 WSS 数据包，并禁用闭合字幕和图文电视数据的输出，或者输出被闭合字幕和图文电视解码器忽略的数据。

切片 VBI 设备可能支持读写 (:ref:`rw`) 和/或流式（:ref:`memory mapping <mmap>` 和/或 :ref:`user pointer <userp>`）I/O。后者可以通过使用缓冲区时间戳来同步视频和 VBI 数据。

### 切片 VBI 数据在 MPEG 流中
-------------------

如果设备能够生成 MPEG 输出流，则它可能能够在 MPEG 流中嵌入协商好的切片 VBI 服务数据。用户或应用程序通过 :ref:`V4L2_CID_MPEG_STREAM_VBI_FMT <v4l2-mpeg-stream-vbi-fmt>` 控制来控制这种切片 VBI 数据的插入。

如果驱动程序不提供 :ref:`V4L2_CID_MPEG_STREAM_VBI_FMT <v4l2-mpeg-stream-vbi-fmt>` 控制，或者只允许将该控制设为 :ref:`V4L2_MPEG_STREAM_VBI_FMT_NONE <v4l2-mpeg-stream-vbi-fmt>`，则设备无法在 MPEG 流中嵌入切片 VBI 数据。
```
V4L2_CID_MPEG_STREAM_VBI_FMT 控制不会隐式地设置设备驱动程序进行捕捉或停止捕捉切片 VBI 数据。该控制仅指示将切片 VBI 数据嵌入 MPEG 流中，前提是应用程序已协商捕获切片 VBI 服务。
在某些情况下，设备可能只能在特定类型的 MPEG 流中嵌入切片 VBI 数据：例如，在 MPEG-2 PS 中而不是 MPEG-2 TS 中。在这种情况下，如果请求插入切片 VBI 数据，则当支持时，切片 VBI 数据将被嵌入到相应的 MPEG 流类型中，并且在设备不支持插入切片 VBI 数据的 MPEG 流类型中将被静默忽略。
以下小节指定了嵌入的切片 VBI 数据格式。

### MPEG 流嵌入的切片 VBI 数据格式：无
----------------------

V4L2_MPEG_STREAM_VBI_FMT_NONE 嵌入的切片 VBI 格式应由驱动程序解释为停止在 MPEG 流中嵌入切片 VBI 数据。当设置此格式时，设备和驱动程序都不应在 MPEG 流中插入“空”的嵌入切片 VBI 数据包。此格式没有指定任何 MPEG 流数据结构。

### MPEG 流嵌入的切片 VBI 数据格式：IVTV
----------------------

V4L2_MPEG_STREAM_VBI_FMT_IVTV 嵌入的切片 VBI 格式（如果支持），指示驱动程序在 MPEG 流中的 MPEG-2 *Private Stream 1 PES* 包装在 MPEG-2 *Program Pack* 中每帧嵌入最多 36 行切片 VBI 数据。
*历史背景*：此格式规范起源于 `ivtv` 驱动程序使用的自定义嵌入切片 VBI 数据格式。
此格式已在内核源文件 `Documentation/userspace-api/media/drivers/cx2341x-uapi.rst` 中非正式地规定。此格式的有效载荷大小和其他方面由 CX23415 MPEG 解码器的能力和限制驱动，特别是从 MPEG 流中提取、解码和显示嵌入的切片 VBI 数据。
此格式的使用不仅限于 `ivtv` 驱动程序，也不限于 CX2341x 设备，因为将切片 VBI 数据包插入 MPEG 流是由驱动程序软件实现的。至少 `cx18` 驱动程序也提供在此格式下将切片 VBI 数据插入 MPEG-2 PS 中。

当 V4L2_MPEG_STREAM_VBI_FMT_IVTV 设置时，包含切片 VBI 数据的 MPEG-2 *Private Stream 1 PES* 包的有效载荷由结构 `v4l2_mpeg_vbi_fmt_ivtv` 指定。（MPEG-2 *Private Stream 1 PES* 包头和封装的 MPEG-2 *Program Pack* 包头未在此详细说明，请参阅 MPEG-2 规范以获取这些包头的详细信息。）

包含切片 VBI 数据的 MPEG-2 *Private Stream 1 PES* 包的有效载荷是可变长度的，取决于视频帧中存在的实际切片 VBI 数据行数。有效载荷的末尾可能用未指定的填充字节进行填充，以使有效载荷的结尾对齐到 4 字节边界。有效载荷永远不会超过 1552 字节（2 场，每场 18 行，每行 43 字节的数据，加上一个 4 字节的魔术数字）。

.. c:type:: v4l2_mpeg_vbi_fmt_ivtv

```c
struct v4l2_mpeg_vbi_fmt_ivtv {
```

.. tabularcolumns:: |p{4.2cm}|p{2.0cm}|p{11.1cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``magic``[4]
      - 一个来自 :ref:`v4l2-mpeg-vbi-fmt-ivtv-magic` 的“魔术”常量，指示这是一个有效的切片 VBI 数据有效载荷，并且还指示匿名联合体 ``itv0`` 或 ``ITV0`` 中哪个成员用于有效载荷数据。
```markdown
* - union {
      - (匿名)
    * - struct :c:type:`v4l2_mpeg_vbi_itv0`
      - ``itv0``
      - 这是切片VBI数据的有效负载的主要形式，包含从1到35行的切片VBI数据。这种有效负载形式提供了行掩码，指示哪些VBI行是有效的。
* - struct :ref:`v4l2_mpeg_vbi_ITV0 <v4l2-mpeg-vbi-itv0-1>`
      - ``ITV0``
      - 当存在36行切片VBI数据时使用的切片VBI数据的有效负载的替代形式。在这种有效负载形式中不提供行掩码；所有有效的行掩码位都是隐式设置的。
* - }
      -

.. _v4l2-mpeg-vbi-fmt-ivtv-magic:

结构体v4l2_mpeg_vbi_fmt_ivtv的magic字段的魔法常量
-------------------------------------------------------------

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. flat-table::
    :header-rows:  1
    :stub-columns: 0
    :widths:       3 1 4

    * - 定义符号
      - 值
      - 描述
    * - ``V4L2_MPEG_VBI_IVTV_MAGIC0``
      - "itv0"
      - 指示结构体 :c:type:`v4l2_mpeg_vbi_fmt_ivtv` 中的 ``itv0`` 成员有效
* - ``V4L2_MPEG_VBI_IVTV_MAGIC1``
      - "ITV0"
      - 指示结构体 :c:type:`v4l2_mpeg_vbi_fmt_ivtv` 中的 ``ITV0`` 成员有效，并且存在36行切片VBI数据

.. c:type:: v4l2_mpeg_vbi_itv0

.. c:type:: v4l2_mpeg_vbi_ITV0

结构体v4l2_mpeg_vbi_itv0和v4l2_mpeg_vbi_ITV0
-------------------------------------------------

.. raw:: latex

   \footnotesize

.. tabularcolumns:: |p{4.6cm}|p{2.0cm}|p{10.7cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __le32
      - ``linemask``\ [2]
      - 表示存在的VBI服务行的位掩码。这些 ``linemask`` 值以小端字节序存储在MPEG流中。以下是一些参考 ``linemask`` 位位置及其对应的VBI行号和视频场的例子：
b\ :sub:`0` 表示一个 ``linemask`` 值的最低有效位：

	::

	    linemask[0] b0:     第一场第 6 行
	    linemask[0] b17:    第一场第 23 行
	    linemask[0] b18:    第二场第 6 行
	    linemask[0] b31:    第二场第 19 行
	    linemask[1] b0:     第二场第 20 行
	    linemask[1] b3:     第二场第 23 行
	    linemask[1] b4-b31: 未使用并设置为0
    * - struct
	:c:type:`v4l2_mpeg_vbi_itv0_line`
      - ``line``\ [35]
      - 这是一个变长数组，包含从1到35行的切片VBI数据。存在的切片VBI数据行对应于 ``linemask`` 数组中设置的位，从 ``linemask``\ [0] 的 b\ :sub:`0` 开始直到 ``linemask``\ [0] 的 b\ :sub:`31`，以及从 ``linemask``\ [1] 的 b\ :sub:`0` 到 ``linemask``\ [1] 的 b\ :sub:`3`。 ``line``\ [0] 对应于在 ``linemask`` 数组中找到的第一个设置的位， ``line``\ [1] 对应于在 ``linemask`` 数组中找到的第二个设置的位，依此类推。如果没有任何 ``linemask`` 数组位被设置，则 ``line``\ [0] 可能包含一条未指定的数据，应用程序应该忽略这条数据。

.. raw:: latex

   \normalsize

.. _v4l2-mpeg-vbi-itv0-1:

结构体v4l2_mpeg_vbi_ITV0
-------------------------

.. tabularcolumns:: |p{5.2cm}|p{2.4cm}|p{9.7cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - struct
	:c:type:`v4l2_mpeg_vbi_itv0_line`
      - ``line``\ [36]
      - 一个固定长度的36行切片VBI数据数组。 ``line``\ [0] 到 ``line``\ [17] 对应于第一场的第6到第23行。 ``line``\ [18] 到 ``line``\ [35] 对应于第二场的第6到第23行。

.. c:type:: v4l2_mpeg_vbi_itv0_line

结构体v4l2_mpeg_vbi_itv0_line
------------------------------

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``id``
      - 一个行标识值，来自 :ref:`ITV0-Line-Identifier-Constants`，指示该行上存储的切片VBI数据类型。
* - __u8
      - ``data``\ [42]
      - 该行的切片VBI数据

.. _ITV0-Line-Identifier-Constants:

结构体v4l2_mpeg_vbi_itv0_line的id字段的行标识符
-------------------------------------------------------------

.. tabularcolumns:: |p{7.0cm}|p{1.8cm}|p{8.5cm}|

.. flat-table::
    :header-rows:  1
    :stub-columns: 0
    :widths:       3 1 4

    * - 定义符号
      - 值
      - 描述
    * - ``V4L2_MPEG_VBI_IVTV_TELETEXT_B``
      - 1
      - 有关该行有效负载的描述，请参见 :ref:`Sliced VBI services <vbi-services2>`
```
* - ``V4L2_MPEG_VBI_IVTV_CAPTION_525``
      - 4
      - 有关行有效负载的描述，请参阅 :ref:`Sliced VBI 服务 <vbi-services2>`
* - ``V4L2_MPEG_VBI_IVTV_WSS_625``
      - 5
      - 有关行有效负载的描述，请参阅 :ref:`Sliced VBI 服务 <vbi-services2>`
* - ``V4L2_MPEG_VBI_IVTV_VPS``
      - 7
      - 有关行有效负载的描述，请参阅 :ref:`Sliced VBI 服务 <vbi-services2>`

.. [#f1]
   根据 :ref:`ETS 300 706 <ets300706>`，第一场的第6至22行和第二场的第5至22行可能携带电传文字数据

.. [#f2]
   请参见 :ref:`vbi-525` 和 :ref:`vbi-625`
