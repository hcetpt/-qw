SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _audio:

************************
音频输入和输出
************************

音频输入和输出是设备的物理连接器。视频捕获设备有输入，输出设备有输出，每个设备可以有一个或多个。无线电设备没有音频输入或输出。它们只有一个调谐器，实际上这是一个音频源，但此API仅将调谐器与视频输入或输出关联，并且无线电设备没有任何这些接口。[#f1]_。电视卡上的一个将接收到的音频信号回环到声卡的连接器不被视为音频输出。

音频和视频输入及输出是相关的。选择视频源的同时也会选择音频源。当视频和音频源是一个调谐器时，这一点最为明显。进一步地，音频连接器可以与一个以上的视频输入或输出组合。假设存在两个复合视频输入和两个音频输入，则可能存在多达四种有效的组合。

视频和音频连接器之间的关系定义在相应的结构体的 ``audioset`` 字段中：:c:type:`v4l2_input` 或者 :c:type:`v4l2_output`，其中每个位代表一个音频输入或输出的索引号，从零开始计数。

为了了解可用输入和输出的数量和属性，应用程序可以通过 :ref:`VIDIOC_ENUMAUDIO` 和 :ref:`VIDIOC_ENUMAUDOUT <VIDIOC_ENUMAUDOUT>` ioctl 分别枚举它们。

由 :ref:`VIDIOC_ENUMAUDIO` ioctl 返回的结构体 :c:type:`v4l2_audio` 还包含适用于查询当前音频输入时的信号状态信息。

:ref:`VIDIOC_G_AUDIO <VIDIOC_G_AUDIO>` 和 :ref:`VIDIOC_G_AUDOUT <VIDIOC_G_AUDOUT>` ioctl 报告当前的音频输入和输出。

.. note::

   注意，与 :ref:`VIDIOC_G_INPUT <VIDIOC_G_INPUT>` 和 :ref:`VIDIOC_G_OUTPUT <VIDIOC_G_OUTPUT>` 不同，这些 ioctl 返回的是一个结构体，而不是仅仅一个索引。

要选择一个音频输入并更改其属性，应用程序应调用 :ref:`VIDIOC_S_AUDIO <VIDIOC_G_AUDIO>` ioctl。要选择一个音频输出（目前没有可更改的属性），应用程序应调用 :ref:`VIDIOC_S_AUDOUT <VIDIOC_G_AUDOUT>` ioctl。

当设备具有多个可选音频输入时，驱动程序必须实现所有音频输入 ioctl；当设备具有多个可选音频输出时，必须实现所有音频输出 ioctl。当设备有任何音频输入或输出时，驱动程序必须在通过 :ref:`VIDIOC_QUERYCAP` ioctl 返回的结构体 :c:type:`v4l2_capability` 中设置 ``V4L2_CAP_AUDIO`` 标志。

示例：关于当前音频输入的信息
==================================

.. code-block:: c

    struct v4l2_audio audio;

    memset(&audio, 0, sizeof(audio));

    if (-1 == ioctl(fd, VIDIOC_G_AUDIO, &audio)) {
	perror("VIDIOC_G_AUDIO");
	exit(EXIT_FAILURE);
    }

    printf("Current input: %s\\n", audio.name);

示例：切换到第一个音频输入
===========================================

.. code-block:: c

    struct v4l2_audio audio;

    memset(&audio, 0, sizeof(audio)); /* 清除 audio.mode, audio.reserved */

    audio.index = 0;

    if (-1 == ioctl(fd, VIDIOC_S_AUDIO, &audio)) {
	perror("VIDIOC_S_AUDIO");
	exit(EXIT_FAILURE);
    }

.. [#f1]
   实际上，结构体 :c:type:`v4l2_audio` 应该有一个 ``tuner`` 字段，就像结构体 :c:type:`v4l2_input` 一样，这不仅使API更加一致，还允许具有多个调谐器的无线电设备。
当然，请提供您需要翻译的文本。
