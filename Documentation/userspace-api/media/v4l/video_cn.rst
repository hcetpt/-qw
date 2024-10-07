SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _video:

************************
视频输入和输出
************************

视频输入和输出是设备的物理连接器。例如，这些可以包括：射频（RF）连接器（天线/电缆）、复合视频（CVBS）、S-视频和RGB连接器。摄像头传感器也被认为是视频输入。视频和垂直消隐间隔（VBI）捕获设备具有输入。视频和VBI输出设备至少各有一个输出。无线电设备没有视频输入或输出。

要了解可用输入和输出的数量及其属性，应用程序可以通过 :ref:`VIDIOC_ENUMINPUT` 和 :ref:`VIDIOC_ENUMOUTPUT` ioctl 分别枚举它们。由 :ref:`VIDIOC_ENUMINPUT` ioctl 返回的结构体 :c:type:`v4l2_input` 还包含在查询当前视频输入时适用的信号状态信息。:ref:`VIDIOC_G_INPUT <VIDIOC_G_INPUT>` 和 :ref:`VIDIOC_G_OUTPUT <VIDIOC_G_OUTPUT>` ioctl 返回当前视频输入或输出的索引。为了选择不同的输入或输出，应用程序应调用 :ref:`VIDIOC_S_INPUT <VIDIOC_G_INPUT>` 和 :ref:`VIDIOC_S_OUTPUT <VIDIOC_G_OUTPUT>` ioctl。当设备有一个或多个输入时，驱动程序必须实现所有输入 ioctl；当设备有一个或多个输出时，必须实现所有输出 ioctl。

示例：获取当前视频输入的信息
==================================================

.. code-block:: c

    struct v4l2_input input;
    int index;

    if (-1 == ioctl(fd, VIDIOC_G_INPUT, &index)) {
	perror("VIDIOC_G_INPUT");
	exit(EXIT_FAILURE);
    }

    memset(&input, 0, sizeof(input));
    input.index = index;

    if (-1 == ioctl(fd, VIDIOC_ENUMINPUT, &input)) {
	perror("VIDIOC_ENUMINPUT");
	exit(EXIT_FAILURE);
    }

    printf("Current input: %s\n", input.name);

示例：切换到第一个视频输入
===========================================

.. code-block:: c

    int index;

    index = 0;

    if (-1 == ioctl(fd, VIDIOC_S_INPUT, &index)) {
	perror("VIDIOC_S_INPUT");
	exit(EXIT_FAILURE);
    }
