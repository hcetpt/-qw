SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _standard:

***************
视频标准
***************

视频设备通常支持一个或多个不同的视频标准或标准的变体。每个视频输入和输出可能支持另一组标准。这些标准由 `VIDIOC_ENUMINPUT` 和 `VIDIOC_ENUMOUTPUT` ioctl 返回的 `struct v4l2_input` 和 `struct v4l2_output` 中的 `std` 字段报告。V4L2 定义了当前全球使用的每种模拟视频标准的一个位，并为驱动程序定义的标准保留了一些位，例如用于在 PAL 电视上观看 NTSC 录像带及其反向情况的混合标准。

应用程序可以使用预定义的位来选择特定的标准，尽管向用户显示支持的标准菜单更为理想。为了枚举和支持标准的属性查询，应用程序应使用 `VIDIOC_ENUMSTD` ioctl。许多定义的标准实际上只是少数主要标准的变体。硬件实际上可能不区分它们，或者内部自动切换。因此，枚举的标准也包含一个或多个标准位的集合。

假设有一个假想的调谐器，能够解调 B/PAL、G/PAL 和 I/PAL 信号。第一个枚举的标准是一组 B 和 G/PAL 的组合，根据选定的 UHF 或 VHF 频段中的无线电频率自动切换。枚举给出 “PAL-B/G” 或 “PAL-I” 的选择。类似地，复合输入可能会合并标准，枚举出 “PAL-B/G/H/I”、“NTSC-M” 和 “SECAM-D/K”。[#f1]_

为了查询和选择当前视频输入或输出所用的标准，应用程序应调用 `VIDIOC_G_STD` 和 `VIDIOC_S_STD` ioctl。接收的标准可以通过 `VIDIOC_QUERYSTD` ioctl 感知。
.. note::
   
   所有这些 ioctl 的参数是指向 `v4l2_std_id` 类型（即标准集）的指针，而不是指向标准枚举的索引。当设备有一个或多个视频输入或输出时，驱动程序必须实现所有视频标准 ioctl。

对于像 USB 摄像头这样的设备，视频标准的概念意义不大。更广泛地说，任何捕获或输出设备如果满足以下条件之一：

- 无法以视频标准的标称速率捕获场或帧，或
- 不支持视频标准格式

在这种情况下，驱动程序应将 `struct v4l2_input` 和 `struct v4l2_output` 中的 `std` 字段设置为零，并且 `VIDIOC_G_STD`、`VIDIOC_S_STD`、`VIDIOC_QUERYSTD` 和 `VIDIOC_ENUMSTD` ioctl 应返回 `ENOTTY` 或 `EINVAL` 错误代码。

应用程序可以利用 `input-capabilities` 和 `output-capabilities` 标志来确定是否可以在给定的输入或输出中使用视频标准 ioctl。
示例：获取当前视频标准的信息
=====================================

.. code-block:: c

    v4l2_std_id std_id;
    struct v4l2_standard standard;

    if (-1 == ioctl(fd, VIDIOC_G_STD, &std_id)) {
        /* 注意，当使用VIDIOC_ENUMSTD总是返回ENOTTY时，
           这不是一个视频设备或它属于USB例外情况，
           而且VIDIOC_G_STD返回ENOTTY不是错误。*/

        perror("VIDIOC_G_STD");
        exit(EXIT_FAILURE);
    }

    memset(&standard, 0, sizeof(standard));
    standard.index = 0;

    while (0 == ioctl(fd, VIDIOC_ENUMSTD, &standard)) {
        if (standard.id & std_id) {
            printf("当前视频标准: %s\n", standard.name);
            exit(EXIT_SUCCESS);
        }

        standard.index++;
    }

    /* EINVAL 表示枚举的结束，除非该设备属于USB例外情况，否则不能为空。*/

    if (errno == EINVAL || standard.index == 0) {
        perror("VIDIOC_ENUMSTD");
        exit(EXIT_FAILURE);
    }

示例：列出当前输入支持的视频标准
====================================

.. code-block:: c

    struct v4l2_input input;
    struct v4l2_standard standard;

    memset(&input, 0, sizeof(input));

    if (-1 == ioctl(fd, VIDIOC_G_INPUT, &input.index)) {
        perror("VIDIOC_G_INPUT");
        exit(EXIT_FAILURE);
    }

    if (-1 == ioctl(fd, VIDIOC_ENUMINPUT, &input)) {
        perror("VIDIOC_ENUM_INPUT");
        exit(EXIT_FAILURE);
    }

    printf("当前输入 %s 支持:\n", input.name);

    memset(&standard, 0, sizeof(standard));
    standard.index = 0;

    while (0 == ioctl(fd, VIDIOC_ENUMSTD, &standard)) {
        if (standard.id & input.std)
            printf("%s\n", standard.name);

        standard.index++;
    }

    /* EINVAL 表示枚举的结束，除非该设备属于USB例外情况，否则不能为空。*/

    if (errno != EINVAL || standard.index == 0) {
        perror("VIDIOC_ENUMSTD");
        exit(EXIT_FAILURE);
    }

示例：选择新的视频标准
=========================

.. code-block:: c

    struct v4l2_input input;
    v4l2_std_id std_id;

    memset(&input, 0, sizeof(input));

    if (-1 == ioctl(fd, VIDIOC_G_INPUT, &input.index)) {
        perror("VIDIOC_G_INPUT");
        exit(EXIT_FAILURE);
    }

    if (-1 == ioctl(fd, VIDIOC_ENUMINPUT, &input)) {
        perror("VIDIOC_ENUM_INPUT");
        exit(EXIT_FAILURE);
    }

    if (0 == (input.std & V4L2_STD_PAL_BG)) {
        fprintf(stderr, "Oops. B/G PAL 不受支持。\n");
        exit(EXIT_FAILURE);
    }

    /* 注意，这也适用于仅支持B或G/PAL的情况。*/

    std_id = V4L2_STD_PAL_BG;

    if (-1 == ioctl(fd, VIDIOC_S_STD, &std_id)) {
        perror("VIDIOC_S_STD");
        exit(EXIT_FAILURE);
    }

.. [#f1]
   一些用户已经被技术术语PAL、NTSC和SECAM搞糊涂了。没有必要让他们区分B、G、D或K，因为软件或硬件可以自动完成这些工作。
