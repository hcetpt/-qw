SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later 或 GPL-2.0

.. c:namespace:: dtv.legacy.audio

.. _dvb_audio:

================
DVB 音频设备
================

.. 注意:: 不要在新驱动程序中使用！
           参见：:ref:`legacy_dvb_decoder_notes`

DVB 音频设备控制 DVB 硬件中的 MPEG2 音频解码器。可以通过 ``/dev/dvb/adapter?/audio?`` 访问它。数据类型和 ioctl 定义可以通过在应用程序中包含 ``linux/dvb/audio.h`` 获取。
请注意，大多数 DVB 卡没有自己的 MPEG 解码器，这会导致音频和视频设备的缺失。
这些 ioctl 也被 V4L2 用来控制 V4L2 中实现的 MPEG 解码器。这种用途已被废弃，并创建了适当的 V4L2 ioctl 或控制来替代该功能。对于新驱动程序，请使用 :ref:`V4L2 ioctl<audio>`！

音频数据类型
================

本节描述了与音频设备交互时使用的结构、数据类型和定义。
-----

audio_stream_source_t
---------------------

概述
~~~~~~~~

.. c:enum:: audio_stream_source_t

.. code-block:: c

    typedef enum {
        AUDIO_SOURCE_DEMUX,
        AUDIO_SOURCE_MEMORY
    } audio_stream_source_t;

常量
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``AUDIO_SOURCE_DEMUX``

       -  :cspan:`1` 选择解复用器（由前端或 DVR 设备提供）作为音频流的来源
-  .
-  ``AUDIO_SOURCE_MEMORY``

       -  选择通过 `write()`_ 系统调用从应用程序传入的流
描述
~~~~~~~~~~~

音频流来源通过 `AUDIO_SELECT_SOURCE`_ 调用来设置，并可以根据是从内部（解复用器）还是外部（用户写入）来源重播而取以下值。
输入到解码器的数据也受 PID 过滤器控制。
输出选择: :c:type:`dmx_output` ``DMX_OUT_DECODER``
### audio_play_state_t

#### 概述

.. c:enum:: audio_play_state_t

.. code-block:: c

    typedef enum {
        AUDIO_STOPPED,
        AUDIO_PLAYING,
        AUDIO_PAUSED
    } audio_play_state_t;

#### 常量

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
    -  ``AUDIO_STOPPED``

           -  音频已停止
    -  .
    -  ``AUDIO_PLAYING``

           -  当前正在播放音频
    -  .
    -  ``AUDIO_PAUSED``

           -  音频已暂停
#### 描述

这些值可以通过 `AUDIO_GET_STATUS`_ 调用返回，表示音频播放的状态

### audio_channel_select_t

#### 概述

.. c:enum:: audio_channel_select_t

.. code-block:: c

    typedef enum {
        AUDIO_STEREO,
        AUDIO_MONO_LEFT,
        AUDIO_MONO_RIGHT,
        AUDIO_MONO,
        AUDIO_STEREO_SWAPPED
    } audio_channel_select_t;

#### 常量

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
    -  ``AUDIO_STEREO``

           -  立体声
    -  .
### 音频通道选择描述

- ``AUDIO_MONO_LEFT``
  - 单声道，选择左声道作为源
- 
- ``AUDIO_MONO_RIGHT``
  - 单声道，选择右声道作为源
- 
- ``AUDIO_MONO``
  - 仅单声道源
- 
- ``AUDIO_STEREO_SWAPPED``
  - 立体声，交换左右声道
描述
~~~~

通过 `AUDIO_CHANNEL_SELECT`_ 选定的音频通道由这些值确定。

---

### audio_mixer_t 结构体

概述
~~~~

```c
typedef struct audio_mixer {
    unsigned int volume_left;
    unsigned int volume_right;
} audio_mixer_t;
```

变量
~~~~

- ``unsigned int volume_left``
  - 左声道音量

--- 

注：表格部分在Markdown中可能无法完全显示，因此使用了纯文本格式。
有效范围：0 ... 255

-  .
-  ``unsigned int volume_right``

       -  右声道音量
有效范围：0 ... 255

描述
~~~~~~~~~~~

此结构由 `AUDIO_SET_MIXER`_ 调用用于设置音频音量
-----

audio_status
------------

概要
~~~~~~~~

.. c:struct:: audio_status

.. code-block:: c

    typedef struct audio_status {
	int AV_sync_state;
	int mute_state;
	audio_play_state_t play_state;
	audio_stream_source_t stream_source;
	audio_channel_select_t channel_select;
	int bypass_mode;
	audio_mixer_t mixer_state;
    } audio_status_t;

变量
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  :rspan:`2` ``int AV_sync_state``

       -  :cspan:`1` 显示 A/V 同步是否开启或关闭
-  .
-  TRUE  ( != 0 )

       -  A/V 同步开启
-  .
-  FALSE ( == 0 )

       -  A/V 同步关闭
-  .
-  :rspan:`2` ``int mute_state``

       -  :cspan:`1` 表示音频是否被静音
-  .
-  TRUE  ( != 0 )

       -  静音音频

    -  .
-  FALSE ( == 0 )

       -  取消静音音频

    -  .
-  `audio_play_state_t`_ ``play_state``

       -  当前播放状态
-  .
-  `audio_stream_source_t`_ ``stream_source``

       -  当前数据源
-  .
-  :rspan:`2` ``int bypass_mode``

       -  :cspan:`1` 当前音频流在DVB子系统中的解码是否启用或禁用
-  .
-  `TRUE` （！= 0）

       -  旁路禁用
-  .
-  `FALSE` （== 0）

       -  旁路启用
-  .
-  `audio_mixer_t`_ `mixer_state`

       -  当前音量设置
描述
~~~~~~~~~~~

`AUDIO_GET_STATUS`_ 调用返回此结构，以提供关于播放操作各种状态的信息。

音频编码
---------------

概要
~~~~~~~~

.. code-block:: c

     #define AUDIO_CAP_DTS    1
     #define AUDIO_CAP_LPCM   2
     #define AUDIO_CAP_MP1    4
     #define AUDIO_CAP_MP2    8
     #define AUDIO_CAP_MP3   16
     #define AUDIO_CAP_AAC   32
     #define AUDIO_CAP_OGG   64
     #define AUDIO_CAP_SDDS 128
     #define AUDIO_CAP_AC3  256

常量
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  `AUDIO_CAP_DTS`

       -  :cspan:`1` 硬件支持 DTS 音轨
-  .
-  `AUDIO_CAP_LPCM`

       -  硬件支持带有线性脉冲编码调制（LPCM）的未压缩音频

    -  .
- ``AUDIO_CAP_MP1``  
  硬件支持 MPEG-1 音频层 1

- ``AUDIO_CAP_MP2``  
  硬件支持 MPEG-1 音频层 2，也称为 MUSICAM

- ``AUDIO_CAP_MP3``  
  硬件支持 MPEG-1 音频层 III，通常称为 .mp3

- ``AUDIO_CAP_AAC``  
  硬件支持 AAC（高级音频编码）
``AUDIO_CAP_OGG``
- 硬件支持 Vorbis 音轨
- 
``AUDIO_CAP_SDDS``
- 硬件支持索尼动态数字声音（Sony Dynamic Digital Sound，简称 SDDS）
- 
``AUDIO_CAP_AC3``
- 硬件支持杜比数字 ATSC A/52 音频，也称为 AC-3

描述
~~~~~~~~~~~
对 `AUDIO_GET_CAPABILITIES` 的调用会返回一个无符号整数，该整数根据硬件的能力设置了相应的位。

---

音频功能调用
====================

AUDIO_STOP
----------

概览
~~~~~~~~
.. c:macro:: AUDIO_STOP

.. code-block:: c

     int ioctl(int fd, int request = AUDIO_STOP)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    - .
- ``int fd``

   - 由先前的 `open()` 调用返回的文件描述符
- .
```markdown
### AUDIO_STOP

#### 描述
``int request``

- :cspan:`1` 对于此命令等于 ``AUDIO_STOP``

描述
~~~~~~~~~~~

.. 注意:: **不要** 在新的驱动程序中使用！
          参见：:ref:`legacy_dvb_decoder_notes`

这个 ioctl 调用请求音频设备停止播放当前的流。

返回值
~~~~~~~~~~~~

成功时返回 0，失败时返回 -1 并且设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。

---

### AUDIO_PLAY

#### 概览
.. c:macro:: AUDIO_PLAY

.. code-block:: c

    int ioctl(int fd, int request = AUDIO_PLAY)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
    -  ``int fd``
        -  由先前调用 `open()`_ 返回的文件描述符。
    -  .
    -  ``int request``
        -  :cspan:`1` 对于此命令等于 ``AUDIO_PLAY``

描述
~~~~~~~~~~~

.. 注意:: **不要** 在新的驱动程序中使用！
          参见：:ref:`legacy_dvb_decoder_notes`

这个 ioctl 调用请求音频设备从选定的源开始播放音频流。

返回值
~~~~~~~~~~~~

成功时返回 0，失败时返回 -1 并且设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。

---

### AUDIO_PAUSE

#### 概览
.. c:macro:: AUDIO_PAUSE

.. code-block:: c

    int ioctl(int fd, int request = AUDIO_PAUSE)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
    -  ``int fd``
        -  由先前调用 `open()`_ 返回的文件描述符。
    -  .
    -  ``int request``
        -  :cspan:`1` 对于此命令等于 ``AUDIO_PAUSE``
```
### AUDIO_PAUSE

#### 概述
```c
int ioctl(int fd, int request = AUDIO_PAUSE)
```

##### 参数

- ``int fd``
    - 文件描述符，由前一次的 `open()` 调用返回。
- 
- ``int request``
    - 对于此命令等于 `AUDIO_PAUSE`。

#### 描述

**注意：** 不要在新的驱动程序中使用！  
请参阅：:ref:`legacy_dvb_decoder_notes`

这个 ioctl 调用会暂停正在播放的音频流。解码和播放被暂停。然后可以使用 `AUDIO_CONTINUE`_ 命令重新开始音频流的解码和播放过程。

#### 返回值

成功时返回 0，错误时返回 -1，并且 `errno` 变量会被设置为适当的值。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。

---

### AUDIO_CONTINUE

#### 概述
```c
int ioctl(int fd, int request = AUDIO_CONTINUE)
```

##### 参数

- ``int fd``
    - 文件描述符，由前一次的 `open()` 调用返回。
- 
- ``int request``
    - 对于此命令等于 `AUDIO_CONTINUE`。

#### 描述

**注意：** 不要在新的驱动程序中使用！  
请参阅：:ref:`legacy_dvb_decoder_notes`

这个 ioctl 调用会重新开始之前使用 `AUDIO_PAUSE`_ 命令暂停的解码和播放过程。
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量。通用错误代码在“通用错误代码”章节中有描述。

AUDIO_SELECT_SOURCE
-------------------

概要
~~~~~~~~

.. c:macro:: AUDIO_SELECT_SOURCE

.. code-block:: c

    int ioctl(int fd, int request = AUDIO_SELECT_SOURCE,
    audio_stream_source_t source)

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

       -  对于此命令等于 ``AUDIO_SELECT_SOURCE``
-  .
-  `audio_stream_source_t`_ ``source``

       -  指示将用于音频流的源
描述
~~~~~~~~~~~

.. 注意:: 不要在新的驱动程序中使用！
          详见：:ref:`legacy_dvb_decoder_notes`

此ioctl调用通知音频设备将使用哪个源作为输入数据。可能的源是解复用器或内存。如果选择了 ``AUDIO_SOURCE_MEMORY``，则通过写命令将数据馈送到音频设备。如果选择了 ``AUDIO_SOURCE_DEMUX``，则数据直接从板载解复用设备传输到解码器。注意：这目前仅支持具有一个解复用器和一个解码器的DVB设备。
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量。通用错误代码在“通用错误代码”章节中有描述。
### AUDIO_SET_MUTE

#### 概述
~~~~~~~~

.. c:macro:: AUDIO_SET_MUTE

.. code-block:: c

    int ioctl(int fd, int request = AUDIO_SET_MUTE, int state)

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

       -  :cspan:`1` 对于此命令，等于 ``AUDIO_SET_MUTE``
-  .
-  :rspan:`2` ``int state``

       -  :cspan:`1` 表示音频设备是否静音
-  .
-  TRUE  ( != 0 )

       -  静音音频

    -  .
-  FALSE ( == 0 )

       -  取消静音音频

#### 描述
~~~~~~~~~~~

.. attention:: 不要在新的驱动程序中使用！
             请参阅：:ref:`legacy_dvb_decoder_notes`

此 ioctl 仅适用于 DVB 设备。要控制 V4L2 解码器，请使用 V4L2 :ref:`VIDIOC_DECODER_CMD` 并设置 ``V4L2_DEC_CMD_START_MUTE_AUDIO`` 标志。
此 ioctl 调用要求音频设备静音当前正在播放的流。
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量为适当的值。通用错误代码在《通用错误代码》一章中描述。

AUDIO_SET_AV_SYNC
-----------------

简介
~~~~~~~~

.. c:macro:: AUDIO_SET_AV_SYNC

.. code-block:: c

    int ioctl(int fd, int request = AUDIO_SET_AV_SYNC, int state)

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

       -  :cspan:`1` 对于此命令等于 ``AUDIO_SET_AV_SYNC``
-  .
-  :rspan:`2` ``int state``

       -  :cspan:`1` 告诉 DVB 子系统是否开启或关闭 A/V 同步
-  .
-  TRUE  ( != 0 )

       -  开启 AV 同步
-  .
### FALSE ( == 0 )

- AV-sync OFF
描述
~~~~~~~~~~~

.. 注意:: 不要在新的驱动程序中使用！
           参见：:ref:`legacy_dvb_decoder_notes`

此ioctl调用请求音频设备打开或关闭A/V同步。
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并设置`errno`变量。通用错误代码在
:ref:`通用错误代码<gen-errors>`章节中有描述。

---

### AUDIO_SET_BYPASS_MODE
#### 简介
~~~~~~~~

.. C:宏:: AUDIO_SET_BYPASS_MODE

.. 代码块:: c

    int ioctl(int fd, int request = AUDIO_SET_BYPASS_MODE, int mode)

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

       -  :cspan:`1` 对于此命令等于``AUDIO_SET_BYPASS_MODE``
-  .
-  :rspan:`2` ``int mode``

       -  :cspan:`1` 启用或禁用DVB子系统中当前音频流的解码
-  .
### 翻译

#### 常量定义
- `TRUE`（不等于 0）
  - 禁用旁路
- `.`  
- `FALSE`（等于 0）
  - 启用旁路

#### 描述
~~~~~~~~~~~
.. 注意:: 不要在新的驱动程序中使用！请参阅：:ref:`legacy_dvb_decoder_notes`

此 ioctl 调用请求音频设备绕过音频解码器并直接转发流而不进行解码。当需要解码 DVB 系统无法处理的流时，应使用此模式。如果硬件支持的话，Dolby DigitalTM 流将自动由 DVB 子系统转发。
#### 返回值
~~~~~~~~~~~~
成功时返回 0，失败时返回 -1 并且设置 `errno` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。

---

### AUDIO_CHANNEL_SELECT
--------------------
#### 概述
~~~~~~~~
.. C 宏:: AUDIO_CHANNEL_SELECT

.. 代码块:: c
     int ioctl(int fd, int request = AUDIO_CHANNEL_SELECT, audio_channel_select_t)

#### 参数
~~~~~~~~~
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

- `int fd`
  - :cspan:`1` 由之前的 `open()`_ 调用返回的文件描述符
- `int request`
  - 此命令等于 `AUDIO_CHANNEL_SELECT`
- `audio_channel_select_t` `ch`
  - 选择音频输出格式（单声道左/右、立体声）

#### 描述
~~~~~~~~~~~
.. 注意:: 不要在新的驱动程序中使用！请参阅：:ref:`legacy_dvb_decoder_notes`

此 ioctl 仅用于 DVB 设备。要控制 V4L2 解码器，请使用 V4L2 的 `V4L2_CID_MPEG_AUDIO_DEC_PLAYBACK` 控制。
这段ioctl调用请求音频设备在可能的情况下选择所请求的通道。

返回值
~~~~~~~~~~~~
成功时返回0，失败时返回-1，并且设置`errno`变量为适当的错误码。通用错误码在《通用错误码》章节中有描述。

AUDIO_GET_STATUS
----------------

简介
~~~~~~~~

.. c:macro:: AUDIO_GET_STATUS

.. code-block:: c

	 int ioctl(int fd, int request = AUDIO_GET_STATUS,
	 struct audio_status *status)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由之前`open()`_调用返回的文件描述符
-  .
-  ``int request``

       -  对于此命令应等于AUDIO_GET_STATUS
-  .
-  ``struct`` `audio_status`_ ``*status``

       -  返回音频设备的当前状态
描述
~~~~~~~~~~~

.. 注意:: 新驱动程序不要使用！
         参见：:ref:`legacy_dvb_decoder_notes`

这段ioctl调用请求音频设备返回其当前状态。

返回值
~~~~~~~~~~~~
成功时返回0，失败时返回-1，并且设置`errno`变量为适当的错误码。通用错误码在《通用错误码》章节中有描述。
### AUDIO_GET_CAPABILITIES

#### 概述
~~~~~~~~

.. c:macro:: AUDIO_GET_CAPABILITIES

.. code-block:: c

    int ioctl(int fd, int request = AUDIO_GET_CAPABILITIES,
              unsigned int *cap)

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
         -  对于此命令等于 ``AUDIO_GET_CAPABILITIES``
    -  .
      -  ``unsigned int *cap``
         -  返回支持的声音格式的位数组。位定义在 `audio encodings`_ 中

#### 描述
~~~~~~~~

.. attention:: **不要** 在新驱动程序中使用！
             参见： :ref:`legacy_dvb_decoder_notes`

此 ioctl 调用请求音频设备告诉我们有关音频硬件解码能力的信息。

#### 返回值
~~~~~~~~

成功时返回 0，错误时返回 -1 并设置适当的 ``errno`` 变量。通用错误代码在
:ref:`Generic Error Codes <gen-errors>` 章节中描述。

---

### AUDIO_CLEAR_BUFFER

#### 概述
~~~~~~~~

.. c:macro:: AUDIO_CLEAR_BUFFER

.. code-block:: c

    int ioctl(int fd, int request = AUDIO_CLEAR_BUFFER)

#### 参数
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
      -  ``int fd``
         -  由先前的 `open()`_ 调用返回的文件描述符
    -  .
      -  ``int request``
         -  对于此命令等于 ``AUDIO_CLEAR_BUFFER``
### `int fd`

- :cspan:`1` 由前一次调用 `open()`_ 返回的文件描述符

### .

### `int request`

- 等于 `AUDIO_CLEAR_BUFFER` 对于此命令

### 描述

**注意：** 不要在新的驱动程序中使用！
参见: :ref:`legacy_dvb_decoder_notes`

这个 ioctl 调用请求音频设备清除音频解码器设备的所有软件和硬件缓冲区。

### 返回值

成功时返回 0，失败时返回 -1 并且设置 `errno` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

---

### AUDIO_SET_ID

### 概述

.. c:macro:: AUDIO_SET_ID

.. code-block:: c

    int ioctl(int fd, int request = AUDIO_SET_ID, int id)

### 参数

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    - .
    - `int fd`

        - :cspan:`1` 由前一次调用 `open()`_ 返回的文件描述符
    - .
    - `int request`

        - 等于 `AUDIO_SET_ID` 对于此命令
    - .
### `int id`

- 音频子流ID
描述
~~~~~~~~~~~

.. 注意:: **不要**在新驱动程序中使用！
          参见: :ref:`legacy_dvb_decoder_notes`

此ioctl用于选择在将节目流或系统流发送到视频设备时要解码的子流。
如果未设置音频流类型，则ID必须在以下范围内：
- 对于MPEG声音，在[0xC0,0xDF]范围内；
- 对于AC3，在[0x80,0x87]范围内；
- 对于LPCM，在[0xA0,0xA7]范围内。

参见ITU-T H.222.0 | ISO/IEC 13818-1以获取更多描述。
如果通过`AUDIO_SET_STREAMTYPE`_设置了流类型，则指定的ID仅表示音频子流的子流ID，并且仅识别前5位 (& 0x1F)。
返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置`errno`变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中有描述。

-----

### AUDIO_SET_MIXER
--------------

概述
~~~~~~~~

.. c:macro:: AUDIO_SET_MIXER

.. code-block:: c

    int ioctl(int fd, int request = AUDIO_SET_MIXER, audio_mixer_t *mix)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

-  .
-  ``int fd``

       -  :cspan:`1` 由先前调用`open()`_返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于``AUDIO_SET_MIXER``
### `audio_mixer_t *mix`

- 混音器设置
描述
~~~~~~~~~~~

.. 注意:: 在新的驱动程序中**不要**使用！
         参见：:ref:`legacy_dvb_decoder_notes`

此ioctl（输入/输出控制）操作允许您调整音频解码器的混音器设置。
返回值
~~~~~~~~~~~~

成功时返回0，失败时返回-1，并且设置`errno`变量。通用错误代码在
:ref:`通用错误代码<gen-errors>`章节中有描述。

---

### AUDIO_SET_STREAMTYPE
概要
~~~~~~~~

.. C:宏:: AUDIO_SET_STREAMTYPE

.. 代码块:: c

    int ioctl(fd, int request = AUDIO_SET_STREAMTYPE, int type)

参数
~~~~~~~~~

.. 平坦表格::
    :header-rows:  0
    :stub-columns: 0

    -  .
    -  ``int fd``

       -  :cspan:`1` 由前一个`open()`_调用返回的文件描述符
    -  .
    -  ``int request``

       -  对于此命令等于`AUDIO_SET_STREAMTYPE`
    -  .
    -  ``int type``

       -  流类型
描述
~~~~~~~~~~~

.. 注意:: 不要在新的驱动程序中使用！
             参见：:ref:`legacy_dvb_decoder_notes`

这个ioctl（输入/输出控制）命令告诉驱动程序预期的音频流类型。这在流提供多个音频子流（如LPCM和AC3）时非常有用。
定义在ITU-T H.222.0 | ISO/IEC 13818-1中的流类型被使用。

返回值
~~~~~~~~~~~~

成功时返回0，错误时返回-1，并且设置`errno`变量。通用错误代码在:ref:`Generic Error Codes <gen-errors>`章节中有描述。
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``EINVAL``

       -  类型不是有效的或支持的流类型
-----

AUDIO_BILINGUAL_CHANNEL_SELECT
------------------------------

概述
~~~~~~~~

.. c:macro:: AUDIO_BILINGUAL_CHANNEL_SELECT

.. code-block:: c

	 int ioctl(int fd, int request = AUDIO_BILINGUAL_CHANNEL_SELECT,
	 audio_channel_select_t)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前调用`open()`_返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于``AUDIO_BILINGUAL_CHANNEL_SELECT`` 
-  .
### `audio_channel_select_t ch`

- 选择音频输出格式（单声道左/右，立体声）
描述
~~~~

.. 注意:: 不要在新驱动中使用！
          参见：:ref:`legacy_dvb_decoder_notes`

此ioctl已被替换为V4L2的`V4L2_CID_MPEG_AUDIO_DEC_MULTILINGUAL_PLAYBACK`控制，
用于通过V4L2控制的MPEG解码器。
此ioctl调用请求音频设备在可能的情况下选择双语流中的请求通道。
返回值
~~~~~~

成功时返回0，失败时返回-1，并设置`errno`变量。
通用错误代码在:ref:`Generic Error Codes <gen-errors>`章节中描述。

---

### open()
### 简介
~~~~

.. code-block:: c

    #include <fcntl.h>

.. c:function:: int open(const char *deviceName, int flags)

参数
~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``const char *deviceName``

       -  具体音频设备的名称
-  .
-  :rspan:`3` ``int flags``

       -  :cspan:`1` 下列标志位的按位或操作：

    -  .
-  ``O_RDONLY``

       -  只读访问

    -  .
-  ``O_RDWR``

       -  读写访问

    -  .
``O_NONBLOCK``
- | 以非阻塞模式打开
  | （默认模式为阻塞模式）

描述
~~~~~~~~~~~

此系统调用用于打开一个命名的音频设备（例如 `/dev/dvb/adapter0/audio0`），以便后续使用。当 `open()` 调用成功后，设备将准备好使用。阻塞模式或非阻塞模式的意义在相关函数的文档中有描述。它不会影响 `open()` 调用本身的语义。一个以阻塞模式打开的设备可以稍后通过 `fcntl` 系统调用中的 `F_SETFL` 命令转换为非阻塞模式（反之亦然）。这是一个标准系统调用，在 Linux 手册页中有关于 `fcntl` 的文档。只有一个用户可以在 `O_RDWR` 模式下打开音频设备。所有其他尝试以该模式打开设备的操作都将失败，并返回错误代码。如果音频设备以 `O_RDONLY` 模式打开，则唯一可以使用的 `ioctl` 调用是 `AUDIO_GET_STATUS`。所有其他调用将返回错误代码。

返回值
~~~~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``ENODEV``

       -  设备驱动程序未加载/不可用
-  .
-  ``EBUSY``

       -  设备或资源忙
-  .
-  ``EINVAL``

       -  无效参数

---

close()
-------

概要
~~~~~~~~

.. c:function:: int close(int fd)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符
描述
~~~~~~~~~~~

此系统调用用于关闭先前已打开的音频设备。

返回值
~~~~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``EBADF``

       -  文件描述符（Fd）不是一个有效的已打开文件描述符

---

write()
-------

概述
~~~~~~~~

.. code-block:: c

	 size_t write(int fd, const void *buf, size_t count)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符
-  .
-  ``void *buf``

       -  指向包含 PES 数据的缓冲区的指针
-  .
-  ``size_t count``

       -  缓冲区（buf）的大小

描述
~~~~~~~~~~~

此系统调用仅在 ioctl 调用 `AUDIO_SELECT_SOURCE`_ 中选择了 ``AUDIO_SOURCE_MEMORY`` 时可用。提供的数据应为 PES 格式。如果未指定 ``O_NONBLOCK``，则该函数将阻塞直到有缓冲区空间可用。要传输的数据量由 count 参数隐含决定。
返回值
~~~~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
    -  ``EPERM``

           -  :cspan:`1` 未选择模式 ``AUDIO_SOURCE_MEMORY``
    -  .
    -  ``ENOMEM``

           -  尝试写入的数据超过内部缓冲区的容量
    -  .
    -  ``EBADF``

           -  文件描述符 Fd 无效或不是打开的文件描述符
