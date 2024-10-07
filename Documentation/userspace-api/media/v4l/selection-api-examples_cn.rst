SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

********
示例
********

（假设有一个视频采集设备；对于其他设备，请更改 `V4L2_BUF_TYPE_VIDEO_CAPTURE`；要配置合成区域，请将目标更改为 `V4L2_SEL_TGT_COMPOSE_*` 家族）

示例：重置裁剪参数
==========================

.. code-block:: c

    struct v4l2_selection sel = {
        .type = V4L2_BUF_TYPE_VIDEO_CAPTURE,
        .target = V4L2_SEL_TGT_CROP_DEFAULT,
    };
    ret = ioctl(fd, VIDIOC_G_SELECTION, &sel);
    if (ret)
        exit(-1);
    sel.target = V4L2_SEL_TGT_CROP;
    ret = ioctl(fd, VIDIOC_S_SELECTION, &sel);
    if (ret)
        exit(-1);

在输出处设置一个最大尺寸为限制尺寸一半的合成区域，位于显示中心
示例：简单的缩小
===========================

.. code-block:: c

    struct v4l2_selection sel = {
        .type = V4L2_BUF_TYPE_VIDEO_OUTPUT,
        .target = V4L2_SEL_TGT_COMPOSE_BOUNDS,
    };
    struct v4l2_rect r;

    ret = ioctl(fd, VIDIOC_G_SELECTION, &sel);
    if (ret)
        exit(-1);
    /* 设置较小的合成矩形 */
    r.width = sel.r.width / 2;
    r.height = sel.r.height / 2;
    r.left = sel.r.width / 4;
    r.top = sel.r.height / 4;
    sel.r = r;
    sel.target = V4L2_SEL_TGT_COMPOSE;
    sel.flags = V4L2_SEL_FLAG_LE;
    ret = ioctl(fd, VIDIOC_S_SELECTION, &sel);
    if (ret)
        exit(-1);

假设有一个视频输出设备；对于其他设备，请更改 `V4L2_BUF_TYPE_VIDEO_OUTPUT`

示例：查询缩放系数
=====================

.. code-block:: c

    struct v4l2_selection compose = {
        .type = V4L2_BUF_TYPE_VIDEO_OUTPUT,
        .target = V4L2_SEL_TGT_COMPOSE,
    };
    struct v4l2_selection crop = {
        .type = V4L2_BUF_TYPE_VIDEO_OUTPUT,
        .target = V4L2_SEL_TGT_CROP,
    };
    double hscale, vscale;

    ret = ioctl(fd, VIDIOC_G_SELECTION, &compose);
    if (ret)
        exit(-1);
    ret = ioctl(fd, VIDIOC_G_SELECTION, &crop);
    if (ret)
        exit(-1);

    /* 计算缩放系数 */
    hscale = (double)compose.r.width / crop.r.width;
    vscale = (double)compose.r.height / crop.r.height;
