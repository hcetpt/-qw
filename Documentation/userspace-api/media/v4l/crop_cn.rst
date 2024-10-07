SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

.. _crop:

*****************************************************
图像裁剪、插入和缩放——CROP API
*****************************************************

.. note::

   CROP API 大部分已被较新的 :ref:`SELECTION API <selection-api>` 取代。在大多数情况下应优先使用新 API，例外情况是像素宽高比检测功能，该功能由 :ref:`VIDIOC_CROPCAP <VIDIOC_CROPCAP>` 实现，并且在 SELECTION API 中没有等效功能。有关两个 API 的比较，请参见 :ref:`selection-vs-crop`。

一些视频捕获设备可以采样图像的一部分，并将其缩小或放大为任意大小的图像。我们将这些能力称为裁剪和缩放。一些视频输出设备可以将图像放大或缩小，并以任意扫描线和水平偏移插入到视频信号中。
应用程序可以使用以下 API 来选择视频信号中的区域，查询默认区域和硬件限制。
.. note::

   尽管名称如此，:ref:`VIDIOC_CROPCAP <VIDIOC_CROPCAP>`、:ref:`VIDIOC_G_CROP <VIDIOC_G_CROP>` 和 :ref:`VIDIOC_S_CROP <VIDIOC_G_CROP>` 这些 ioctl 同时适用于输入和输出设备。

缩放需要一个源和一个目标。在视频捕获或覆盖设备上，源是视频信号，裁剪 ioctl 确定实际采样的区域。目标是应用程序读取或覆盖到图形屏幕上的图像。其大小（对于覆盖还包括位置）通过 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` 和 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 这些 ioctl 协商确定。
在视频输出设备上，源是应用程序传递进来的图像，其大小同样通过 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` 和 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 这些 ioctl 协商确定，或者可能编码在一个压缩视频流中。目标是视频信号，裁剪 ioctl 确定图像插入的区域。
即使设备不支持缩放或 :ref:`VIDIOC_G_CROP <VIDIOC_G_CROP>` 和 :ref:`VIDIOC_S_CROP <VIDIOC_G_CROP>` 这些 ioctl，源和目标矩形也会被定义。在这种情况下，它们的大小（以及适用的位置）将是固定的。
.. note::

   所有支持 CROP 或 SELECTION API 的捕获和输出设备也将支持 :ref:`VIDIOC_CROPCAP <VIDIOC_CROPCAP>` 这个 ioctl。

裁剪结构
===================

.. _crop-scale:

.. kernel-figure:: crop.svg
    :alt:    crop.svg
    :align:  center

    图像裁剪、插入和缩放

    裁剪、插入和缩放过程

对于捕获设备，可采样区域的左上角坐标、宽度和高度由 :c:type:`v4l2_cropcap` 结构的 ``bounds`` 子结构给出，该结构由 :ref:`VIDIOC_CROPCAP <VIDIOC_CROPCAP>` ioctl 返回。为了支持广泛的硬件，本规范未定义原点或单位。
然而，按照惯例，驱动程序应该相对于 0H（即水平同步脉冲的前沿，参见 :ref:`vbi-hsync`）水平计数未缩放的样本。垂直方向上使用第一场的 ITU-R 行号（参见 ITU R-525 行编号，对于 :ref:`525 行 <vbi-525>` 和 :ref:`625 行 <vbi-625>`），如果驱动程序可以捕获两场，则乘以二。
左上角、宽度和高度的源矩形，即实际采样的区域，由结构体 `v4l2_crop` 使用与结构体 `v4l2_cropcap` 相同的坐标系统给出。应用程序可以使用 `VIDIOC_G_CROP` 和 `VIDIOC_S_CROP` 的 ioctl 命令来获取和设置这个矩形。该矩形必须完全位于捕获边界内，并且驱动程序可能会根据硬件限制进一步调整请求的大小和/或位置。

每个捕获设备都有一个默认的源矩形，由结构体 `v4l2_cropcap` 的 `defrect` 子结构给出。此矩形的中心应与视频信号的活动图像区域中心对齐，并覆盖驱动程序作者认为的完整图像。驱动程序在首次加载时应将源矩形重置为默认值，但之后不应再更改。

对于输出设备，这些结构体和 ioctl 命令也相应地定义了图像插入视频信号的目标矩形。

缩放调整
========

视频硬件可能有各种裁剪、插入和缩放限制。它可能仅支持放大或缩小，只支持离散的缩放因子，或者在水平和垂直方向有不同的缩放能力。同时，它也可能根本不支持缩放。此外，结构体 `v4l2_crop` 矩形可能需要对齐，并且源矩形和目标矩形都可能有任意的上限和下限。特别是，结构体 `v4l2_crop` 中的最大 `width` 和 `height` 可能小于结构体 `v4l2_cropcap` 的 `bounds` 区域。因此，通常情况下，驱动程序应调整请求的参数并返回实际选择的值。

应用程序可以先更改源矩形或目标矩形，因为它们可能更喜欢特定的图像尺寸或视频信号中的某个区域。如果驱动程序需要调整两者以满足硬件限制，则最后请求的矩形应优先考虑，而驱动程序应尽可能调整另一个矩形。然而，`VIDIOC_TRY_FMT` ioctl 不应改变驱动程序状态，因此只应调整请求的矩形。

假设视频捕获设备的缩放限制为任何方向上的 1:1 或 2:1 比例，并且目标图像尺寸必须是 16×16 像素的倍数。源裁剪矩形设置为默认值，在本例中也是上限值，为偏移量 0, 0 的 640×400 像素。应用程序请求图像尺寸为 300×225 像素，假定视频会从“全图”相应地缩小。

驱动程序将图像尺寸设置为最接近的可能值 304×224 像素，然后选择最接近请求尺寸的裁剪矩形，即 608×224 像素（224×2:1 超过上限 400）。偏移量 0, 0 仍然有效，因此未修改。根据 `VIDIOC_CROPCAP` 报告的默认裁剪矩形，应用程序可以轻松提议另一个偏移量以使裁剪矩形居中。

现在，应用程序可能坚持要覆盖一个更接近原始请求的图片宽高比的区域，因此它请求一个 608×456 像素的裁剪矩形。当前的缩放因子限制裁剪为 640×384，因此驱动程序返回裁剪尺寸 608×384 并将图像尺寸调整为最接近的可能值 304×192。

示例
====

在关闭和重新打开设备时，源矩形和目标矩形应保持不变，以便将数据输入或输出到设备时无需特殊准备即可工作。更高级的应用程序应在开始 I/O 之前确保参数适合。
.. 注意::

   在下面两个示例中，假设使用的是视频采集设备；
   对于其他类型的设备，请更改 ``V4L2_BUF_TYPE_VIDEO_CAPTURE``

示例：重置裁剪参数
==========================

.. code-block:: c

    struct v4l2_cropcap cropcap;
    struct v4l2_crop crop;

    memset (&cropcap, 0, sizeof (cropcap));
    cropcap.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    if (-1 == ioctl (fd, VIDIOC_CROPCAP, &cropcap)) {
	perror ("VIDIOC_CROPCAP");
	exit (EXIT_FAILURE);
    }

    memset (&crop, 0, sizeof (crop));
    crop.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    crop.c = cropcap.defrect;

    /* 如果不支持裁剪（EINVAL），则忽略。 */

    if (-1 == ioctl (fd, VIDIOC_S_CROP, &crop)
	&& errno != EINVAL) {
	perror ("VIDIOC_S_CROP");
	exit (EXIT_FAILURE);
    }


示例：简单的缩小
===========================

.. code-block:: c

    struct v4l2_cropcap cropcap;
    struct v4l2_format format;

    reset_cropping_parameters ();

    /* 缩小到全图大小的1/4。 */

    memset (&format, 0, sizeof (format)); /* 默认值 */

    format.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    format.fmt.pix.width = cropcap.defrect.width >> 1;
    format.fmt.pix.height = cropcap.defrect.height >> 1;
    format.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;

    if (-1 == ioctl (fd, VIDIOC_S_FMT, &format)) {
	perror ("VIDIOC_S_FORMAT");
	exit (EXIT_FAILURE);
    }

    /* 我们现在可以检查实际的图像大小、实际的缩放因子或驱动程序是否能进行缩放。 */

示例：选择输出区域
=====================

.. 注意:: 此示例假设是一个输出设备
.. code-block:: c

    struct v4l2_cropcap cropcap;
    struct v4l2_crop crop;

    memset (&cropcap, 0, sizeof (cropcap));
    cropcap.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;

    if (-1 == ioctl (fd, VIDIOC_CROPCAP, &cropcap)) {
	perror ("VIDIOC_CROPCAP");
	exit (EXIT_FAILURE);
    }

    memset (&crop, 0, sizeof (crop));

    crop.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
    crop.c = cropcap.defrect;

    /* 将宽度和高度缩小到原始大小的一半，并居中输出。 */

    crop.c.width /= 2;
    crop.c.height /= 2;
    crop.c.left += crop.c.width / 2;
    crop.c.top += crop.c.height / 2;

    /* 如果不支持裁剪（EINVAL），则忽略。 */

    if (-1 == ioctl (fd, VIDIOC_S_CROP, &crop)
	&& errno != EINVAL) {
	perror ("VIDIOC_S_CROP");
	exit (EXIT_FAILURE);
    }

示例：当前的缩放比例和像素宽高比
=================================

.. 注意:: 此示例假设是一个视频采集设备
.. code-block:: c

    struct v4l2_cropcap cropcap;
    struct v4l2_crop crop;
    struct v4l2_format format;
    double hscale, vscale;
    double aspect;
    int dwidth, dheight;

    memset (&cropcap, 0, sizeof (cropcap));
    cropcap.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    if (-1 == ioctl (fd, VIDIOC_CROPCAP, &cropcap)) {
	perror ("VIDIOC_CROPCAP");
	exit (EXIT_FAILURE);
    }

    memset (&crop, 0, sizeof (crop));
    crop.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    if (-1 == ioctl (fd, VIDIOC_G_CROP, &crop)) {
	if (errno != EINVAL) {
	    perror ("VIDIOC_G_CROP");
	    exit (EXIT_FAILURE);
	}

	/* 不支持裁剪。 */
	crop.c = cropcap.defrect;
    }

    memset (&format, 0, sizeof (format));
    format.fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    if (-1 == ioctl (fd, VIDIOC_G_FMT, &format)) {
	perror ("VIDIOC_G_FMT");
	exit (EXIT_FAILURE);
    }

    /* 驱动程序应用的缩放比例。 */

    hscale = format.fmt.pix.width / (double) crop.c.width;
    vscale = format.fmt.pix.height / (double) crop.c.height;

    aspect = cropcap.pixelaspect.numerator /
	 (double) cropcap.pixelaspect.denominator;
    aspect = aspect * hscale / vscale;

    /* 遵循ITU-R BT.601标准的设备不会捕获方形像素。
       为了在计算机显示器上播放，我们应该将图像缩放到这个大小。 */

    dwidth = format.fmt.pix.width / aspect;
    dheight = format.fmt.pix.height;
