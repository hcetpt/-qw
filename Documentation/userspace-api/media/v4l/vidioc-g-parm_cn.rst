SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间:: V4L

.. _VIDIOC_G_PARM:

**********************************
ioctl VIDIOC_G_PARM, VIDIOC_S_PARM
**********************************

名称
====

VIDIOC_G_PARM - VIDIOC_S_PARM - 获取或设置流参数

概要
====

.. c:macro:: VIDIOC_G_PARM

``int ioctl(int fd, VIDIOC_G_PARM, v4l2_streamparm *argp)``

.. c:macro:: VIDIOC_S_PARM

``int ioctl(int fd, VIDIOC_S_PARM, v4l2_streamparm *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_streamparm` 的指针

描述
====

应用程序可以请求不同的帧间隔。如果可能，捕获或输出设备将重新配置以支持请求的帧间隔。驱动程序可以选择跳过或重复帧以实现所需的帧间隔。对于有状态编码器（参见 :ref:`encoder`），这表示通常嵌入在编码视频流中的帧间隔。更改帧间隔不应改变格式。相反，更改格式可能会改变帧间隔。此外，这些 ioctl 可用于确定驱动程序在读/写模式下内部使用的缓冲区数量。具体影响请参见讨论 :c:func:`read()` 函数的部分。

为了获取和设置流参数，应用程序分别调用 :ref:`VIDIOC_G_PARM <VIDIOC_G_PARM>` 和 :ref:`VIDIOC_S_PARM <VIDIOC_G_PARM>` ioctl。它们需要一个指向结构体 :c:type:`v4l2_streamparm` 的指针，该结构体包含一个联合体，用于分别存储输入和输出设备的参数。
.. tabularcolumns:: |p{3.7cm}|p{3.5cm}|p{10.1cm}|

.. c:type:: v4l2_streamparm

.. flat-table:: 结构体 v4l2_streamparm
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``type``
      - 缓冲区（流）类型，与结构体 :c:type:`v4l2_format` 的 ``type`` 相同，由应用程序设置。参见 :c:type:`v4l2_buf_type`
    * - union {
      - ``parm``
    * - 结构体 :c:type:`v4l2_captureparm`
      - ``capture``
      - 用于捕获设备的参数，在 ``type`` 是 ``V4L2_BUF_TYPE_VIDEO_CAPTURE`` 或 ``V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE`` 时使用
    * - 结构体 :c:type:`v4l2_outputparm`
      - ``output``
      - 用于输出设备的参数，在 ``type`` 是 ``V4L2_BUF_TYPE_VIDEO_OUTPUT`` 或 ``V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE`` 时使用
* - __u8
  - ``raw_data``\ [200]
  - 为将来扩展保留的占位符
* - }

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_captureparm

.. flat-table:: 结构体 v4l2_captureparm
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``capability``
      - 参见 :ref:`parm-caps`
* - __u32
      - ``capturemode``
      - 由驱动程序和应用程序设置，参见 :ref:`parm-flags`
* - 结构体 :c:type:`v4l2_fract`
      - ``timeperframe``
      - 这是指定的由驱动程序捕获连续帧之间的周期（以秒为单位）
* - :cspan:`2`

	这将配置视频源（例如传感器）生成视频帧的速度。如果速度是固定的，则驱动程序可以选择跳过或重复帧以实现请求的帧率。
对于状态编码器（参见 :ref:`encoder`），这代表通常嵌入在编码视频流中的帧间隔。
应用程序在此存储所需的帧周期，驱动程序返回实际的帧周期。
更改视频标准（通过切换视频输入隐式进行）可能会将此参数重置为标称帧周期。要手动重置，应用程序只需将该字段设为零。
只有当驱动程序设置了 ``capability`` 字段中的 ``V4L2_CAP_TIMEPERFRAME`` 标志时，才支持此功能。
* - __u32
      - ``extendedmode``
      - 自定义（驱动程序特定的）流参数。未使用时，应用程序和驱动程序必须将此字段设为零。使用此字段的应用程序应检查驱动程序名称和版本，参见 :ref:`querycap`
* - `__u32`
  - `readbuffers`
  - 应用程序设置此字段为驱动程序在 `read()` 模式下内部使用的缓冲区数量
  驱动程序返回实际的缓冲区数量。当应用程序请求零个缓冲区时，驱动程序应返回当前设置，而不是最小值或错误代码。详情请参阅 :ref:`rw`
* - `__u32`
  - `reserved`[4]
  - 保留供将来扩展使用。驱动程序和应用程序必须将数组设置为零

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_outputparm

.. flat-table:: struct v4l2_outputparm
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `__u32`
      - `capability`
      - 详见 :ref:`parm-caps`
* - `__u32`
      - `outputmode`
      - 由驱动程序和应用程序设置，详见 :ref:`parm-flags`
* - 结构 :c:type:`v4l2_fract`
      - `timeperframe`
      - 这是驱动程序输出连续帧之间的期望周期（以秒为单位）

* - :cspan:`2`

  此字段旨在在 `write()` 模式下重复帧（在流模式中可以使用时间戳来控制输出），从而节省 I/O 带宽。
  对于有状态编码器（见 :ref:`encoder`），这代表了通常嵌入到编码视频流中的帧间隔，并为编码器提供了原始帧排队速度的提示。
  应用程序在此存储期望的帧周期，驱动程序返回实际的帧周期。
  更改视频标准（通过切换视频输出隐式进行）可能会将此参数重置为标称帧周期。要手动重置，应用程序只需将此字段设为零。
### 驱动程序仅在设置 `capability` 字段中的 `V4L2_CAP_TIMEPERFRAME` 标志时支持此功能。

* - `__u32`
  - `extendedmode`
  - 自定义（驱动程序特定）流参数。当未使用时，应用程序和驱动程序必须将此字段设置为零。使用此字段的应用程序应检查驱动程序名称和版本，详见 :ref:`querycap`
* - `__u32`
  - `writebuffers`
  - 应用程序在此字段中设置 :c:func:`write()` 模式下希望使用的缓冲区数量。驱动程序返回实际的缓冲区数量。当应用程序请求零个缓冲区时，驱动程序应返回当前设置而非最小值或错误代码。详细信息见 :ref:`rw`
* - `__u32`
  - `reserved`[4]
  - 保留用于将来扩展。驱动程序和应用程序必须将数组设置为零

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _parm-caps:

.. flat-table:: 流参数能力
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - `V4L2_CAP_TIMEPERFRAME`
      - 0x1000
      - 可以通过设置 `timeperframe` 字段来修改帧周期

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _parm-flags:

.. flat-table:: 捕获参数标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - `V4L2_MODE_HIGHQUALITY`
      - 0x0001
      - 高质量成像模式。高质量模式适用于静态成像应用。目的是获得硬件能够提供的最佳图像质量。驱动程序编写者如何实现这一点并未定义；这将取决于硬件和驱动程序编写者的创造力。高质量模式与常规运动视频捕获模式不同。在高质量模式下：

-   驱动程序可能能够捕获比运动捕获更高的分辨率
-   驱动程序可能支持比运动捕获更少的像素格式（例如：真彩色）
-   驱动程序可能捕获并算术组合多个连续场或帧，以消除色彩边缘伪影并减少视频数据中的噪声
-   驱动程序可能像扫描仪一样逐片捕获图像，以便处理更大格式的图像
-   图像捕获操作可能显著慢于运动捕获
### 移动的物体在图像中可能会有过多的运动模糊
### 只能通过 :c:func:`read()` 调用进行捕获

### 返回值
成功时返回 0，出错时返回 -1，并且设置 `errno` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中有描述。
