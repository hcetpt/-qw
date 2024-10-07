SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _osd:

*******************************
视频输出叠加接口
*******************************

**也称为屏幕显示（OSD）**

一些视频输出设备可以在输出视频信号上叠加一个帧缓冲图像。应用程序可以使用此接口设置此类叠加，该接口借鉴了 :ref:`Video Overlay <overlay>` 接口中的结构和 ioctl。OSD 功能通过与 :ref:`Video Output <capture>` 功能相同的字符特殊文件访问。
.. note::

   此类 ``/dev/video`` 设备的默认功能是视频捕获或输出。在调用 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 后，OSD 功能才可用。

查询能力
=====================

支持 *Video Output Overlay* 接口的设备会在由 :ref:`VIDIOC_QUERYCAP` ioctl 返回的 struct :c:type:`v4l2_capability` 结构体的 ``capabilities`` 字段中设置 ``V4L2_CAP_VIDEO_OUTPUT_OVERLAY`` 标志。
帧缓冲
===========

与 *Video Overlay* 接口不同，帧缓冲通常实现在电视卡而不是显卡上。在 Linux 上，它作为一个帧缓冲设备（``/dev/fbN``）访问。给定一个 V4L2 设备，应用程序可以通过调用 :ref:`VIDIOC_G_FBUF <VIDIOC_G_FBUF>` ioctl 找到相应的帧缓冲设备。它返回的信息中包括 struct :c:type:`v4l2_framebuffer` 的 ``base`` 字段中的帧缓冲物理地址。
ioctl ``FBIOGET_FSCREENINFO`` 在 struct :c:type:`fb_fix_screeninfo` 的 ``smem_start`` 字段中返回相同的地址。ioctl ``FBIOGET_FSCREENINFO`` 和 struct :c:type:`fb_fix_screeninfo` 定义在头文件 ``linux/fb.h`` 中。
帧缓冲的宽度和高度取决于当前视频标准。V4L2 驱动程序可能会拒绝尝试更改视频标准（或其他可能导致帧缓冲大小变化的 ioctl），直到所有应用程序关闭帧缓冲设备，并返回 ``EBUSY`` 错误码。
示例：为 OSD 寻找帧缓冲设备
---------------------------------------------

.. code-block:: c

    #include <linux/fb.h>

    struct v4l2_framebuffer fbuf;
    unsigned int i;
    int fb_fd;

    if (-1 == ioctl(fd, VIDIOC_G_FBUF, &fbuf)) {
	perror("VIDIOC_G_FBUF");
	exit(EXIT_FAILURE);
    }

    for (i = 0; i < 30; i++) {
	char dev_name[16];
	struct fb_fix_screeninfo si;

	snprintf(dev_name, sizeof(dev_name), "/dev/fb%u", i);

	fb_fd = open(dev_name, O_RDWR);
	if (-1 == fb_fd) {
	    switch (errno) {
	    case ENOENT: /* 没有此类文件 */
	    case ENXIO:  /* 没有驱动程序 */
		continue;

	    default:
		perror("open");
		exit(EXIT_FAILURE);
	    }
	}

	if (0 == ioctl(fb_fd, FBIOGET_FSCREENINFO, &si)) {
	    if (si.smem_start == (unsigned long)fbuf.base)
		break;
	} else {
	    /* 显然不是一个帧缓冲设备。 */
	}

	close(fb_fd);
	fb_fd = -1;
    }

    /* fb_fd 是视频输出叠加帧缓冲设备的文件描述符，
       或者如果没有找到设备，则为 -1。*/

叠加窗口与缩放
==========================

叠加由源矩形和目标矩形控制。源矩形选择帧缓冲图像的一个子部分进行叠加，目标矩形指定图像在输出视频信号中的显示区域。驱动程序可能支持或不支持缩放以及这些矩形的任意大小和位置。此外，驱动程序可能支持（或不支持）为 :ref:`Video Overlay <overlay>` 接口定义的任何剪辑/混合方法。
struct :c:type:`v4l2_window` 定义了源矩形的大小、其在帧缓冲中的位置以及用于叠加的剪辑/混合方法。要获取当前参数，应用程序将 struct :c:type:`v4l2_format` 的 ``type`` 字段设置为 ``V4L2_BUF_TYPE_VIDEO_OUTPUT_OVERLAY`` 并调用 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` ioctl。驱动程序填充名为 ``win`` 的 struct :c:type:`v4l2_window` 子结构。无法检索先前编程的剪辑列表或位图。
要编程源矩形，应用程序将 struct :c:type:`v4l2_format` 的 ``type`` 字段设置为 ``V4L2_BUF_TYPE_VIDEO_OUTPUT_OVERLAY``，初始化 ``win`` 子结构并调用 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl。
驾驶员根据硬件限制调整参数，并像 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` 一样返回实际参数。与 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 类似，:ref:`VIDIOC_TRY_FMT <VIDIOC_G_FMT>` ioctl 可以用来了解驱动程序的功能，而不会实际改变驱动程序的状态。与 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 不同的是，在覆盖层启用后，这个 ioctl 仍然有效。

一个 :c:type:`v4l2_crop` 结构体定义了目标矩形的大小和位置。覆盖层的缩放因子由结构体 :c:type:`v4l2_window` 和 :c:type:`v4l2_crop` 中给出的宽度和高度隐含。裁剪 API 对 *视频输出* 和 *视频输出覆盖层* 设备的应用方式与对 *视频捕获* 和 *视频覆盖层* 设备相同，只是数据流的方向相反。更多信息请参见 :ref:`crop`

启用覆盖层
===========

没有专门的 V4L2 ioctl 来启用或禁用覆盖层，但是驱动程序的帧缓冲接口可能支持 ``FBIOBLANK`` ioctl。
