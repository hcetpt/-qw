SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later 或 GPL-2.0

.. c:命名空间:: dtv.legacy.video

.. _dvb_video:

================
DVB 视频设备
================

.. 注意:: 在新驱动程序中**不要**使用！
         参见: :ref:`legacy_dvb_decoder_notes`

DVB 视频设备控制 DVB 硬件中的 MPEG2 视频解码器。可以通过 `/dev/dvb/adapter0/video0` 进行访问。数据类型和 ioctl 定义可以通过在应用程序中包含 `linux/dvb/video.h` 来访问。
请注意，DVB 视频设备仅控制 MPEG 视频流的解码，而不负责其在电视或计算机屏幕上的显示。在 PC 上，这通常由一个关联的视频4Linux设备（如 `/dev/video`）处理，该设备允许缩放并定义输出窗口。
大多数 DVB 卡没有自己的 MPEG 解码器，这会导致音频和视频设备以及视频4Linux设备的缺失。
这些 ioctl 也曾被 V4L2 用于控制 V4L2 中实现的 MPEG 解码器。这些 ioctl 用于此目的已经过时，并且已经创建了适当的 V4L2 ioctl 或控制来取代该功能。对于新驱动程序，请使用 :ref:`V4L2 ioctl<video>`！

视频数据类型
================

video_format_t
--------------

概览
~~~~~~~~

.. 代码块:: c

    typedef enum {
	VIDEO_FORMAT_4_3,
	VIDEO_FORMAT_16_9,
	VIDEO_FORMAT_221_1
    } video_format_t;

常量
~~~~~~~~~

.. 平坦表格::
    :表头行:  0
    :存根列: 0

    -  .
-  ``VIDEO_FORMAT_4_3``

       -  选择 4:3 格式
-  .
-  ``VIDEO_FORMAT_16_9``

       -  选择 16:9 格式
-  .
-  ``VIDEO_FORMAT_221_1``

       -  选择 2.21:1 格式
描述
~~~~~~~~~~~

`video_format_t` 数据类型
用于 `VIDEO_SET_FORMAT`_ 函数，告诉驱动程序输出硬件（例如电视）的宽高比。它也用于 `video_status`_ 数据结构中，该数据结构由 `VIDEO_GET_STATUS`_ 返回，并且还用于 `video_event`_ 数据结构中，该数据结构由 `VIDEO_GET_EVENT`_ 返回，报告当前视频流的显示格式。

`video_displayformat_t`
---------------------

概览
~~~~~~~~

.. code-block:: c

    typedef enum {
	VIDEO_PAN_SCAN,
	VIDEO_LETTER_BOX,
	VIDEO_CENTER_CUT_OUT
    } video_displayformat_t;

常量
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``VIDEO_PAN_SCAN``

       -  使用平移和扫描格式
-  .
-  ``VIDEO_LETTER_BOX``

       -  使用信箱格式
-  .
-  ``VIDEO_CENTER_CUT_OUT``

       -  使用中心裁剪格式

描述
~~~~~~~~~~~

当视频流的显示格式与显示硬件的格式不一致时，应用程序需要指定如何处理图像的裁剪。这可以通过使用接受此枚举作为参数的 `VIDEO_SET_DISPLAY_FORMAT`_ 调用来完成。

`video_size_t`
------------

概览
~~~~~~~~

.. code-block:: c

    typedef struct {
	int w;
	int h;
	video_format_t aspect_ratio;
    } video_size_t;

变量
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int w``

       -  视频宽度（以像素为单位）
```markdown
### h
- 视频的高度（像素）

### `int h`

- 视频的高度（像素）

### `video_format_t aspect_ratio`

- 宽高比

描述
~~~~

在结构体 `video_event` 中使用。它存储视频的分辨率和宽高比。

---

### video_stream_source_t
#### 概览
~~~~~c
typedef enum {
    VIDEO_SOURCE_DEMUX,
    VIDEO_SOURCE_MEMORY
} video_stream_source_t;
#### 常量
~~~~
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
    -  `VIDEO_SOURCE_DEMUX`

        -  选择解复用器作为主要来源
    -  .
    -  `VIDEO_SOURCE_MEMORY`

        -  如果选择了此来源，则流通过用户写系统调用来提供
描述
~~~~

视频流来源通过 `VIDEO_SELECT_SOURCE` 调用设置，并根据是从内部（解复用器）还是外部（用户写入）来源回放，可以取以下值。
```
### VIDEO_SOURCE_DEMUX
`VIDEO_SOURCE_DEMUX` 选择解复用器（由前端或 DVR 设备提供输入）作为视频流的来源。如果选择了 `VIDEO_SOURCE_MEMORY`，则视频流通过 `write()` 系统调用从应用程序中获取。

---

### video_play_state_t

#### 概览

```c
typedef enum {
    VIDEO_STOPPED,
    VIDEO_PLAYING,
    VIDEO_FREEZED
} video_play_state_t;
```

#### 常量

| 常量           | 描述                         |
|----------------|----------------------------|
| `VIDEO_STOPPED` | 视频已停止                   |
| `VIDEO_PLAYING` | 视频正在播放                 |
| `VIDEO_FREEZED` | 视频已冻结                   |

#### 描述
这些值可以由 `VIDEO_GET_STATUS` 调用返回，表示视频播放的状态。

---

### struct video_command

#### 概览

```c
struct video_command {
    __u32 cmd;
    __u32 flags;
    union {
        struct {
            __u64 pts;
        } stop;

        struct {
            __s32 speed;
            __u32 format;
        } play;

        struct {
            __u32 data[16];
        } raw;
    };
};
```

#### 变量

| 变量          | 描述                             |
|---------------|--------------------------------|
| `__u32 cmd`   | 解码器命令                       |
| `__u32 flags` | 标志字段                         |
| `union`       | 包含不同命令的具体参数           |
| `- stop`      | `pts`：停止时间戳                |
| `- play`      | `speed`：播放速度；`format`：播放格式 |
| `- raw`       | `data`：原始数据数组             |
- ``__u32 flags``  
  - 解码器命令的标志

- 
- ``struct stop``  
  - ``__u64 pts``  
  - MPEG PTS

- 
- :rspan:`5` ``struct play``  
  - :rspan:`4` ``__s32 speed``  
    - 0 或 1000 表示正常速度，
  -  
  - 1: 表示向前逐帧，
  - 
  - -1: 表示向后逐帧，
  - 
  - >1: 以正常速度的 speed / 1000 播放
  - 
  - <-1: 以正常速度的 (-speed / 1000) 倒播

- 
- ``__u32 format``  
  - `播放输入格式`  

-
``__u32 data[16]``

- 保留

描述
~~~~~~~~~~~

在应用程序使用该结构之前，必须将其清零。这确保了将来可以安全地扩展它。

预定义的解码器命令和标志
------------------------------

概述
~~~~~~~~

.. code-block:: c

    #define VIDEO_CMD_PLAY                      (0)
    #define VIDEO_CMD_STOP                      (1)
    #define VIDEO_CMD_FREEZE                    (2)
    #define VIDEO_CMD_CONTINUE                  (3)

    #define VIDEO_CMD_FREEZE_TO_BLACK      (1 << 0)

    #define VIDEO_CMD_STOP_TO_BLACK        (1 << 0)
    #define VIDEO_CMD_STOP_IMMEDIATELY     (1 << 1)

    #define VIDEO_PLAY_FMT_NONE                 (0)
    #define VIDEO_PLAY_FMT_GOP                  (1)

    #define VIDEO_VSYNC_FIELD_UNKNOWN           (0)
    #define VIDEO_VSYNC_FIELD_ODD               (1)
    #define VIDEO_VSYNC_FIELD_EVEN              (2)
    #define VIDEO_VSYNC_FIELD_PROGRESSIVE       (3)

常量
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  :rspan:`3` _`解码器命令`

       -  ``VIDEO_CMD_PLAY``

       -  开始播放
-  .
-  ``VIDEO_CMD_STOP``

       -  停止播放
-  .
-  ``VIDEO_CMD_FREEZE``

       -  暂停播放
-  .
-  ``VIDEO_CMD_CONTINUE``

       -  暂停后继续播放
-  .
-  `VIDEO_CMD_FREEZE` 标志

       -  `VIDEO_CMD_FREEZE_TO_BLACK`

       -  冻结时显示黑色画面
-  .
-  `VIDEO_CMD_STOP` 标志

       -  `VIDEO_CMD_STOP_TO_BLACK`

       -  停止时显示黑色画面
-  .
-  `VIDEO_CMD_STOP_IMMEDIATELY`

       -  立即停止，不清空缓冲区
-  .
-  _`播放输入格式`

       -  `VIDEO_PLAY_FMT_NONE`

       -  解码器没有特殊格式要求
-  .
-  `VIDEO_PLAY_FMT_GOP`

       -  解码器需要完整的GOP
-  .
-  `场顺序`

       -  `VIDEO_VSYNC_FIELD_UNKNOWN`

       -  如果硬件不知道Vsync是针对奇数场、偶数场还是逐行（即非交错）场，则可以使用FIELD_UNKNOWN
-  .
### VIDEO_VSYNC_FIELD_ODD
- Vsync 是针对奇数场的。

### VIDEO_VSYNC_FIELD_EVEN
- Vsync 是针对偶数场的。

### VIDEO_VSYNC_FIELD_PROGRESSIVE
- 逐行扫描（即非交错）。

---

### video_event

#### 概述
```c
struct video_event {
    __s32 type;
    #define VIDEO_EVENT_SIZE_CHANGED        1
    #define VIDEO_EVENT_FRAME_RATE_CHANGED  2
    #define VIDEO_EVENT_DECODER_STOPPED     3
    #define VIDEO_EVENT_VSYNC               4
    long timestamp;
    union {
        video_size_t size;
        unsigned int frame_rate;
        unsigned char vsync_field;
    } u;
};
```

#### 变量
- **`__s32 type`**
    - 事件类型
- `VIDEO_EVENT_SIZE_CHANGED`
    - 尺寸变化
- `VIDEO_EVENT_FRAME_RATE_CHANGED`
    - 帧率变化
-  .
-  ``VIDEO_EVENT_DECODER_STOPPED``

       -  解码器停止
-  .
-  ``VIDEO_EVENT_VSYNC``

       -  发生垂直同步（Vsync）
-  .
-  ``long timestamp``

       -  MPEG PTS 在发生时的值
-  .
-  :rspan:`2` ``union u``

       -  `video_size_t`_ size

       -  视频的分辨率和宽高比
-  .
-  ``unsigned int frame_rate``

       -  每1000秒的帧数

    -  .
### `unsigned char vsync_field`

- | 未知 / 奇数场 / 偶数场 / 逐行扫描
  | 参见: `预定义的解码器命令和标志`_

描述
~~~~~~~~~~~

这是视频事件的结构，由 `VIDEO_GET_EVENT`_ 调用返回。更多细节请参见该调用。

---

### video_status

#### 概述
`VIDEO_GET_STATUS`_ 调用返回以下结构，提供关于播放操作各种状态的信息。

```c
struct video_status {
    int                    video_blank;
    video_play_state_t     play_state;
    video_stream_source_t  stream_source;
    video_format_t         video_format;
    video_displayformat_t  display_format;
};
```

#### 变量
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  :rspan:`2` `int video_blank`

       -  :cspan:`1` 在冻结时显示空白视频？

    -  .
-  TRUE  ( != 0 )

       -  冻结时显示空白屏幕
-  .
-  FALSE ( == 0 )

       -  显示最后解码的帧
-  .
-  `video_play_state_t`_ `play_state`

       -  当前播放状态
-  .
### `video_stream_source_t`_ `stream_source`

- 当前源（解复用/内存）

### `video_format_t`_ `video_format`

- 当前流的宽高比

### `video_displayformat_t`_ `display_format`

- 应用的裁剪模式

描述
~~~~

如果将 `video_blank` 设置为 `TRUE`，则在切换频道或停止播放时会屏蔽视频。否则，会显示最后一帧图片。`play_state` 表示当前视频是否被冻结、停止或正在播放。`stream_source` 对应于选定的视频流源，它可以来自解复用器或内存。`video_format` 指示当前播放视频流的宽高比（4:3 或 16:9）。最后，`display_format` 对应于当源视频格式与输出设备格式不同时应用的裁剪模式。

---

### video_still_picture

#### 简介
~~~~

```c
struct video_still_picture {
    char *iFrame;
    int32_t size;
};
```

#### 变量
~~~~

- `char *iFrame`

   - 内存中单个 I 帧的指针

- `int32_t size`

   - I 帧的大小（以字节为单位）
```int32_t size```
- I帧的大小

描述
~~~~~~~~~~~
通过 `VIDEO_STILLPICTURE`_ 调用显示的I帧会在这个结构体中传递。

视频能力
------------------

概要
~~~~~~~~
.. code-block:: c

    #define VIDEO_CAP_MPEG1   1
    #define VIDEO_CAP_MPEG2   2
    #define VIDEO_CAP_SYS     4
    #define VIDEO_CAP_PROG    8

常量
~~~~~~~~
能力的位定义：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``VIDEO_CAP_MPEG1``

       -  :cspan:`1` 硬件可以解码MPEG1
-  .
-  ``VIDEO_CAP_MPEG2``

       -  硬件可以解码MPEG2
-  .
-  ``VIDEO_CAP_SYS``

       -  视频设备接受系统流
尽管如此，你仍然需要打开视频和音频设备，
但只需将流发送到视频设备。
-  .
```
``VIDEO_CAP_PROG``

- 视频设备接受节目流
您仍然需要打开视频和音频设备，
但只需将流发送到视频设备

描述
~~~~~~

对 `VIDEO_GET_CAPABILITIES`_ 的调用会返回一个无符号整数，根据硬件功能设置以下位。

---

视频功能调用
====================

VIDEO_STOP
----------

概要
~~~~~~~~

.. c:macro:: VIDEO_STOP

.. code-block:: c

   int ioctl(fd, VIDEO_STOP, int mode)

参数
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符
-  .
-  ``int request``

       -  :cspan:`1` 对于此命令等于 ``VIDEO_STOP``
-  .
-  :rspan:`2` ``int mode``

       -  :cspan:`1` 指示如何处理屏幕
-  .
### 翻译成中文

- `TRUE` （!= 0）

       - 停止时屏幕变黑
-  .
- `FALSE` （== 0）

       - 显示最后解码的帧
描述
~~~~~~

.. 注意:: 不要在新的驱动程序中使用！
           参见：:ref:`legacy_dvb_decoder_notes`

此ioctl仅适用于数字电视设备。要控制V4L2解码器，请使用V4L2 :ref:`VIDIOC_DECODER_CMD`。
此ioctl调用要求视频设备停止播放当前流。根据输入参数，屏幕可以变黑或显示最后解码的帧。
返回值
~~~~~~

成功时返回0，出错时返回-1，并且设置`errno`变量为相应的错误代码。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中有描述。

---

### VIDEO_PLAY
---

概述
~~~~

.. c:宏:: VIDEO_PLAY

.. 代码块:: c

	int ioctl(fd, VIDEO_PLAY)

参数
~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由之前调用`open()`_返回的文件描述符
-  .
-  ``int request``

       - 对于此命令等于`VIDEO_PLAY`
描述
~~~~~~~~~~~

.. 注意:: **不要** 在新的驱动程序中使用！
             参见: :ref:`legacy_dvb_decoder_notes`

此ioctl（输入/输出控制）仅适用于数字电视设备。要控制V4L2解码器，请使用V4L2的:ref:`VIDIOC_DECODER_CMD`
此ioctl调用请求视频设备从选定的源开始播放视频流
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置`errno`变量为适当的错误代码。通用错误代码在:ref:`Generic Error Codes <gen-errors>`章节中有描述

---

VIDEO_FREEZE
------------

概览
~~~~~~~~

.. c:宏:: VIDEO_FREEZE

.. 代码块:: c

	int ioctl(fd, VIDEO_FREEZE)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前的`open()`_调用返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于``VIDEO_FREEZE``
描述
~~~~~~~~~~~

.. 注意:: **不要** 在新的驱动程序中使用！
             参见: :ref:`legacy_dvb_decoder_notes`

此ioctl仅适用于数字电视设备。要控制V4L2解码器，请使用V4L2的:ref:`VIDIOC_DECODER_CMD`
此ioctl调用会暂停正在播放的实时视频流（如果选择了VIDEO_SOURCE_DEMUX）。解码和播放被冻结
然后可以使用`VIDEO_CONTINUE`_命令重新启动视频流的解码和播放过程
### 如果在 ioctl 调用 `VIDEO_SELECT_SOURCE` 中选择了 `VIDEO_SOURCE_MEMORY`
数字电视子系统将不再解码任何数据，直到执行 ioctl 调用 `VIDEO_CONTINUE` 或 `VIDEO_PLAY`

#### 返回值
成功时返回 0，错误时返回 -1，并且设置 `errno` 变量。通用错误代码在“通用错误代码”章节中描述。

---

### VIDEO_CONTINUE

#### 简介
```c
int ioctl(fd, VIDEO_CONTINUE)
```

#### 参数

- `int fd`
  - 文件描述符，由之前的 `open()` 调用返回。
- `int request`
  - 对于此命令等于 `VIDEO_CONTINUE`。

#### 描述

**注意：不要在新驱动程序中使用！**
参见：:ref:`legacy_dvb_decoder_notes`

此 ioctl 仅适用于数字电视设备。要控制 V4L2 解码器，请使用 V4L2 的 :ref:`VIDIOC_DECODER_CMD`。

此 ioctl 调用重新启动之前调用 `VIDEO_FREEZE` 时播放的视频流的解码和播放过程。

#### 返回值
成功时返回 0，错误时返回 -1，并且设置 `errno` 变量。通用错误代码在“通用错误代码”章节中描述。

---

### VIDEO_SELECT_SOURCE

#### 简介
```c
int ioctl(fd, VIDEO_SELECT_SOURCE, video_stream_source_t source)
```

#### 参数

- `int fd`
  - 文件描述符，由之前的 `open()` 调用返回。
- `video_stream_source_t source`
  - 视频流源类型。
### 描述

- `int fd`
  - :cspan:`1` 由先前调用 `open()`_ 返回的文件描述符。
- .
- `int request`
  - 等于 `VIDEO_SELECT_SOURCE` 用于此命令。
- .
- `video_stream_source_t`_ `source`
  - 指示视频流应使用的源。

### 描述

**注意：** 不要在新的驱动程序中使用！请参阅：:ref:`legacy_dvb_decoder_notes`

此 ioctl 仅适用于数字电视设备。此 ioctl 也曾被 V4L2 ivtv 驱动支持，但已被 ivtv 特定的 `IVTV_IOC_PASSTHROUGH_MODE` ioctl 替代。

此 ioctl 调用通知视频设备应使用哪个输入数据源。可能的数据源是解复用器（demux）或内存。如果选择内存，则通过写入命令使用 `video_stream_source_t`_ 结构体将数据馈送给视频设备。如果选择解复用器，则数据直接从板载解复用设备传输到解码器。馈送给解码器的数据也受 PID 过滤器控制。

输出选择：:c:type:`dmx_output` `DMX_OUT_DECODER`

### 返回值

成功时返回 0，出错时返回 -1，并且 `errno` 变量会被相应设置。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。
### VIDEO_SET_BLANK

#### 概述
~~~
.. c:macro:: VIDEO_SET_BLANK

.. code-block:: c

    int ioctl(fd, VIDEO_SET_BLANK, int mode)
~~~

#### 参数
~~~
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
    -  ``int fd``

           -  :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符
    -  .
    -  ``int request``

           -  :cspan:`1` 对于此命令等于 ``VIDEO_SET_BLANK``
    -  .
    -  :rspan:`2` ``int mode``

           -  :cspan:`1` 指示是否应使屏幕变为空白
    -  .
    -  TRUE  ( != 0 )

           -  停止时使屏幕变为空白
    -  .
    -  FALSE ( == 0 )

           -  显示最后解码的帧
~~~
描述
~~~~~~~~~~~

.. 注意:: 在新驱动中**不要**使用！
             参见：:ref:`legacy_dvb_decoder_notes`

此ioctl调用请求视频设备将画面变黑
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中有描述

VIDEO_GET_STATUS
----------------

概览
~~~~~~~~

.. c:宏:: VIDEO_GET_STATUS

.. 代码块:: c

	int ioctl(fd, int request = VIDEO_GET_STATUS,
	          struct video_status *status)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由之前的 `open()`_ 调用返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_GET_STATUS``
-  .
-  ``struct`` `video_status`_ ``*status``

       -  返回视频设备当前的状态
描述
~~~~~~~~~~~

.. 注意:: 在新驱动中**不要**使用！
             参见：:ref:`legacy_dvb_decoder_notes`

此ioctl调用请求视频设备返回设备当前的状态
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中有描述
### VIDEO_GET_EVENT

#### 概述
~~~~~~~~

.. c:macro:: VIDEO_GET_EVENT

.. code-block:: c

   int ioctl(fd, int request = VIDEO_GET_EVENT, struct video_event *ev)

#### 参数
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由前一个 `open()`_ 调用返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_GET_EVENT``
-  .
-  ``struct`` `video_event`_ ``*ev``

       -  指向事件（如果有）将被存储的位置
#### 描述
~~~~~~~~~~~

.. attention:: 不要在新的驱动程序中使用！
             参见: :ref:`legacy_dvb_decoder_notes`

此 ioctl 仅适用于 DVB 设备。要从 V4L2 解码器获取事件，请使用 V4L2 的 :ref:`VIDIOC_DQEVENT` ioctl。
此 ioctl 调用在有可用事件时返回一个类型为 `video_event`_ 的事件。最新的一组事件将按发生顺序排队并返回。如果未及时获取，则较旧的事件可能会被丢弃。如果没有事件可用，行为取决于设备是处于阻塞模式还是非阻塞模式。在后一种情况下，调用会立即失败，并将 errno 设置为 ``EWOULDBLOCK``。在前一种情况下，调用会一直阻塞直到有事件可用。可以使用标准的 Linux poll() 和/或 select() 系统调用来监视设备文件描述符上的新事件。对于 select()，应将文件描述符包含在 exceptfds 参数中；对于 poll()，应指定 POLLPRI 作为唤醒条件。此 ioctl 调用只需要读取权限。
#### 返回值
~~~~~~~~~~~~

成功时返回 0，出错时返回 -1 并设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
``EWOULDBLOCK``
- :cspan:`1` 没有待处理的事件，并且设备处于非阻塞模式

``EOVERFLOW``
- 事件队列溢出 —— 一个或多个事件丢失

-----

VIDEO_SET_DISPLAY_FORMAT
------------------------

简介
~~~~~~~~

.. c:macro:: VIDEO_SET_DISPLAY_FORMAT

.. code-block:: c

   int ioctl(fd, int request = VIDEO_SET_DISPLAY_FORMAT,
             video_display_format_t format)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

-  .
-  ``int fd``

       -  :cspan:`1` 由先前 `open()`_ 调用返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_SET_DISPLAY_FORMAT``
-  .
-  `video_displayformat_t`_ ``format``

       -  选择要使用的视频格式
描述
~~~~~~~~~~~

.. 注意:: 不要在新的驱动程序中使用！
         参见：:ref:`legacy_dvb_decoder_notes`

此 ioctl 调用请求视频设备选择 MPEG 芯片应用于视频的视频格式。
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量为适当的值。通用错误代码在《通用错误代码》章节中有描述。

VIDEO_STILLPICTURE
------------------

概要
~~~~~~~~

.. c:macro:: VIDEO_STILLPICTURE

.. code-block:: c

   int ioctl(fd, int request = VIDEO_STILLPICTURE, struct video_still_picture *sp)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前调用 `open()`_ 返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_STILLPICTURE``
-  .
-  ``struct`` `video_still_picture`_ ``*sp``

       -  指向存储包含I帧及其大小的结构的位置
描述
~~~~~~~~~~~

.. 注意:: 新驱动程序不要使用！
           参见：:ref:`legacy_dvb_decoder_notes`

这个 ioctl 调用要求视频设备显示一幅静止图片（I帧）。输入数据应当是一个包含I帧的元素视频流的部分。通常这部分是从TS或PES录制中提取出来的。分辨率和编解码器（参见 `video capabilities`_）必须被设备支持。如果指针为NULL，则当前显示的静止图片将被清空。
例如，AV7110 支持带有常见PAL-SD分辨率的MPEG1和MPEG2。
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量为适当的值。通用错误代码在《通用错误代码》章节中有描述。
### VIDEO_FAST_FORWARD

#### 概述
~~~~~~~~

.. c:macro:: VIDEO_FAST_FORWARD

.. code-block:: c

   int ioctl(fd, int request = VIDEO_FAST_FORWARD, int nFrames)

#### 参数
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前调用 `open()`_ 返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_FAST_FORWARD``
-  .
-  ``int nFrames``

       -  要跳过的帧数
#### 描述
~~~~~~~~~~~

.. attention:: 不要在新的驱动程序中使用！
             参见: :ref:`legacy_dvb_decoder_notes`

此 ioctl 调用请求视频设备跳过解码 N 个 I 帧。只有在选择了 ``VIDEO_SOURCE_MEMORY`` 时才能使用此调用。
#### 返回值
~~~~~~~~~~~~

成功时返回 0，错误时返回 -1，并且设置 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``EPERM``

       -  未选择模式 ``VIDEO_SOURCE_MEMORY``
### VIDEO_SLOWMOTION

#### 概述
~~~~~~~~

.. c:macro:: VIDEO_SLOWMOTION

.. code-block:: c

    int ioctl(fd, int request = VIDEO_SLOWMOTION, int nFrames)

#### 参数
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前调用 `open()`_ 返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_SLOWMOTION``
-  .
-  ``int nFrames``

       -  每帧重复的次数
#### 描述
~~~~~~~~~~~

.. attention:: **不要**在新的驱动程序中使用！
             参见：:ref:`legacy_dvb_decoder_notes`

此 ioctl 调用要求视频设备将解码的帧重复 N 次。只有在选择了 ``VIDEO_SOURCE_MEMORY`` 的情况下才能使用此调用。
#### 返回值
~~~~~~~~~~~~

成功时返回 0，错误时返回 -1 并设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``EPERM``

       -  未选择模式 ``VIDEO_SOURCE_MEMORY``
### VIDEO_GET_CAPABILITIES

#### 概述
~~~~~~~~

.. c:macro:: VIDEO_GET_CAPABILITIES

.. code-block:: c

   int ioctl(fd, int request = VIDEO_GET_CAPABILITIES, unsigned int *cap)

#### 参数
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由前一个 `open()`_ 调用返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_GET_CAPABILITIES``
-  .
-  ``unsigned int *cap``

       -  指向存储能力信息的位置
#### 描述
~~~~~~~~

.. attention:: 不要在新驱动程序中使用！
             参见：:ref:`legacy_dvb_decoder_notes`

此 ioctl 调用询问视频设备关于其解码能力的信息。如果成功，它会返回一个整数，该整数根据 `video capabilities`_ 中的定义设置了某些位。
#### 返回值
~~~~~~~~

如果成功返回 0，如果失败则返回 -1，并且设置 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。

---

### VIDEO_CLEAR_BUFFER

#### 概述
~~~~~~~~

.. c:macro:: VIDEO_CLEAR_BUFFER

.. code-block:: c

   int ioctl(fd, int request = VIDEO_CLEAR_BUFFER)

#### 参数
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由前一个 `open()`_ 调用返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_CLEAR_BUFFER``
```markdown
### `int fd`

- :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符

### `int request`

- 等于 `VIDEO_CLEAR_BUFFER` 对于此命令

描述
~~~~~~~~~~~

.. 注意:: 不要在新的驱动程序中使用！
         参见：:ref:`legacy_dvb_decoder_notes`

此 ioctl 调用会清除驱动程序和解码器硬件中的所有视频缓冲区。

返回值
~~~~~~~~~~~~

成功时返回 0，失败时返回 -1 并设置 `errno` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

-----

### VIDEO_SET_STREAMTYPE
#### 概述
~~~~~~~~

.. c:macro:: VIDEO_SET_STREAMTYPE

.. code-block:: c

    int ioctl(fd, int request = VIDEO_SET_STREAMTYPE, int type)

#### 参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

- ．
- `int fd`

   - :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符
- ．
- `int request`

   - 等于 `VIDEO_SET_STREAMTYPE` 对于此命令
- ．
```
``int type``

- 流类型
描述
~~~~~~~~~~~

.. 注意:: 不要在新的驱动程序中使用！
           参见: :ref:`legacy_dvb_decoder_notes`

这个 ioctl 告诉驱动程序预期将被写入的流类型。
智能解码器可能不支持或忽略（如 AV7110）此调用，并自行确定流类型。
当前使用的流类型如下：

.. 平坦表格::
    :header-rows:  1
    :stub-columns: 0

    -  .
- 编码器

       -  流类型

    -  .
- MPEG2

       -  0

    -  .
- MPEG4 h.264

       -  1

    -  .
- VC1

       -  3

    -  .
- MPEG4 第2部分

       -  4

    -  .
- VC1 简单模式

       -  5

    -  .
### MPEG1
- 6
- .

### HEVC h.265
- | 7
| DREAMBOX: 22
- .

### AVS
- 16
- .

### AVS2
- 40

并非每个解码器都支持所有流类型。

#### 返回值
~~~~~~~~~~~~

成功时返回 0，失败时返回 -1，并设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。

-----

### VIDEO_SET_FORMAT
----------------

#### 概述
~~~~~~~~

.. c:macro:: VIDEO_SET_FORMAT

.. code-block:: c

   int ioctl(fd, int request = VIDEO_SET_FORMAT, video_format_t format)

#### 参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

- .
- ``int fd``
   - :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符
- .
- ``int request``
   - 对于此命令等于 ``VIDEO_SET_FORMAT``
- .
```video_format_t`` `format`

- 电视视频格式，如 `video_format_t`_ 中定义
描述
~~~~~~~~~~~

.. 注意:: 切勿在新驱动程序中使用！
         参见：:ref:`legacy_dvb_decoder_notes`

此ioctl设置连接的输出设备（电视）的屏幕格式（宽高比），以便可以根据需要调整解码器的输出。
返回值
~~~~~~~~~~~~

成功时返回0，失败时返回-1，并且根据情况设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中有描述。

-----

VIDEO_GET_SIZE
--------------

概览
~~~~~~~~

.. c:macro:: VIDEO_GET_SIZE

.. code-block:: c

	int ioctl(int fd, int request = VIDEO_GET_SIZE, video_size_t *size)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  由先前调用 `open()`_ 返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_GET_SIZE``
-  .
-  `video_size_t`_ ``*size``

       -  返回大小和宽高比
描述
~~~~~~~~~~~

.. 注意:: 切勿在新驱动程序中使用！
         参见：:ref:`legacy_dvb_decoder_notes`

此ioctl返回大小和宽高比。
```
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量为适当的值。通用错误代码在《通用错误代码》一章中有描述。

VIDEO_GET_PTS
-------------

简介
~~~~~~~~

.. c:macro:: VIDEO_GET_PTS

.. code-block:: c

   int ioctl(int fd, int request = VIDEO_GET_PTS, __u64 *pts)

参数
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前调用 `open()`_ 返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_GET_PTS``
-  .
-  ``__u64 *pts``

       -  返回按照 ITU T-REC-H.222.0 / ISO/IEC 13818-1 定义的33位时间戳
          如果可能的话，PTS 应属于当前播放的帧，但也可能是接近该值的一个值，例如上一个解码帧的 PTS 或 PES 解析器提取的最后一个 PTS。
描述
~~~~~~~~~~~

.. 注意:: 不要在新的驱动程序中使用！
           参见：:ref:`legacy_dvb_decoder_notes`

对于 V4L2 解码器，此 ioctl 已被 ``V4L2_CID_MPEG_VIDEO_DEC_PTS`` 控制所取代。
此 ioctl 调用请求视频设备返回当前的 PTS 时间戳。
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量。通用错误代码在“<gen-errors>”章节中描述。

VIDEO_GET_FRAME_COUNT
---------------------

简介
~~~~~~~~

.. c:macro:: VIDEO_GET_FRAME_COUNT

.. code-block:: c

   int ioctl(int fd, VIDEO_GET_FRAME_COUNT, __u64 *pts)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_GET_FRAME_COUNT``
-  .
-  ``__u64 *pts``

       -  返回自解码器启动以来显示的帧数
描述
~~~~~~~~~~~

.. 注意:: 不要在新的驱动程序中使用！
         参见：:ref:`legacy_dvb_decoder_notes`

对于V4L2解码器，此ioctl已被 ``V4L2_CID_MPEG_VIDEO_DEC_FRAME`` 控制取代。
此ioctl调用请求视频设备返回自解码器启动以来显示的帧数。
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量。通用错误代码在“<gen-errors>”章节中描述。
### VIDEO_COMMAND

#### 概述
~~~~~~~~

.. c:macro:: VIDEO_COMMAND

.. code-block:: c

   int ioctl(int fd, int request = VIDEO_COMMAND, struct video_command *cmd)

#### 参数
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``VIDEO_COMMAND``
-  .
-  `struct video_command`_ ``*cmd``

       -  控制解码器
#### 描述
~~~~~~~~~~~

.. attention:: 不要在新的驱动程序中使用！
             参见: :ref:`legacy_dvb_decoder_notes`

对于V4L2解码器，此ioctl已被 :ref:`VIDIOC_DECODER_CMD` ioctl 替换。
此ioctl用于控制解码器。`struct video_command`_ 是 ``v4l2_decoder_cmd`` 结构体的一个子集，因此请参阅 :ref:`VIDIOC_DECODER_CMD` 文档以获取更多信息。
#### 返回值
~~~~~~~~~~~~

成功时返回0，出错时返回-1，并且设置 ``errno`` 变量为适当的错误代码。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。

---

### VIDEO_TRY_COMMAND

#### 概述
~~~~~~~~

.. c:macro:: VIDEO_TRY_COMMAND

.. code-block:: c

   int ioctl(int fd, int request = VIDEO_TRY_COMMAND, struct video_command *cmd)

#### 参数
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
### `int fd`
- **描述**：由前一次调用 `open()` 返回的文件描述符

### .
### `int request`
- **描述**：对于此命令等于 `VIDEO_TRY_COMMAND`

### .
### `struct video_command`_ `*cmd`
- **描述**：尝试一个解码器命令

### 描述
~~~~~~~~~~~
**注意**：不要在新的驱动程序中使用！
参见：:ref:`legacy_dvb_decoder_notes`

对于V4L2解码器，此ioctl已被
:ref:`VIDIOC_TRY_DECODER_CMD <VIDIOC_DECODER_CMD>` ioctl所取代。
此ioctl尝试一个解码器命令。`struct video_command`_ 是 `v4l2_decoder_cmd` 结构体的一个子集，
因此请参考 :ref:`VIDIOC_TRY_DECODER_CMD <VIDIOC_DECODER_CMD>` 文档获取更多信息。

### 返回值
~~~~~~~~~~~~
成功时返回0，失败时返回-1，并且设置 `errno` 变量为适当的错误代码。
通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。

---

### `open()`
#### 概述
~~~~~~~~
```c
#include <fcntl.h>
int open(const char *deviceName, int flags);
```

#### 参数
~~~~~~~~~
- **`const char *deviceName`**
  - 描述：特定视频设备的名称
### 翻译

-  .
-  :rspan:`3` ``int flags``

       -  :cspan:`1` 下列标志的按位或：

    -  .
-  ``O_RDONLY``

       -  只读访问

    -  .
-  ``O_RDWR``

       -  读写访问

    -  .
-  ``O_NONBLOCK``
       -  | 以非阻塞模式打开
          | （默认为阻塞模式）

描述
~~~~

这个系统调用用于打开一个命名的视频设备（例如 `/dev/dvb/adapter?/video?`），以便后续使用。
当 `open()` 调用成功后，设备将准备好使用。阻塞模式和非阻塞模式的意义在相关函数文档中有描述。它不会影响 `open()` 调用本身的语义。使用 `fcntl` 系统调用中的 `F_SETFL` 命令可以在阻塞模式和非阻塞模式之间切换（反之亦然）。这是标准系统调用，在 Linux 手册页中有关于 `fcntl` 的文档。只有单个用户可以以 `O_RDWR` 模式打开视频设备。其他尝试以该模式打开设备的操作都会失败，并返回错误代码。如果视频设备以 `O_RDONLY` 模式打开，则唯一可用的 `ioctl` 调用是 `VIDEO_GET_STATUS`。所有其他调用都会返回错误代码。

返回值
~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``ENODEV``

       -  :cspan:`1` 设备驱动程序未加载/不可用
-  .
``EINTERNAL``
- 内部错误
- ．
``EBUSY``
- 设备或资源忙
- ．
``EINVAL``
- 无效参数
-----

close()
-------

概要
~~~~~~~~

.. c:function:: int close(int fd)

参数
~~~~~~~~~

.. flat-table::
    :header-rows: 0
    :stub-columns: 0

    - ．
- ``int fd``
  
       -  :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符
描述
~~~~~~~~~~~

此系统调用关闭先前打开的视频设备
返回值
~~~~~~~~~~~~

.. flat-table::
    :header-rows: 0
    :stub-columns: 0

    - ．
- ``EBADF``

       - fd 不是一个有效的打开文件描述符
### write()

#### 概述
~~~~~~~~

.. c:function:: size_t write(int fd, const void *buf, size_t count)

#### 参数
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前调用 `open()`_ 返回的文件描述符
-  .
-  ``void *buf``

       -  指向包含 PES 数据的缓冲区的指针
-  .
-  ``size_t count``

       -  buf 的大小
#### 描述
~~~~~~~~~~~

此系统调用仅在 ioctl 调用 `VIDEO_SELECT_SOURCE`_ 中选择了 VIDEO_SOURCE_MEMORY 时才能使用。提供的数据应为 PES 格式，除非能力允许其他格式。TS 是存储 DVB 数据最常用的格式，通常也支持。如果未指定 O_NONBLOCK，则函数将阻塞直到有可用的缓冲空间。要传输的数据量由 count 指定。
.. note:: 参见：:ref:`DVB 数据格式 <legacy_dvb_decoder_formats>`

#### 返回值
~~~~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``EPERM``

       -  :cspan:`1` 未选择模式 ``VIDEO_SOURCE_MEMORY``
-  `ENOMEM`

       - 尝试写入的数据量超过内部缓冲区的容量
-  `EBADF`

       - 文件描述符 fd 无效或不是有效的已打开文件描述符
