SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later 或 GPL-2.0

.. c:命名空间:: dtv.legacy.osd

.. _dvb_osd:

==============
DVB OSD 设备
==============

.. 注意:: 切勿在新驱动程序中使用！
          参见: :ref:`legacy_dvb_decoder_notes`

DVB OSD 设备控制基于 AV7110 的 DVB 卡的屏幕显示功能，这些卡带有硬件 MPEG2 解码器。它可以通过 `/dev/dvb/adapter?/osd0` 进行访问。
数据类型和 ioctl 定义可以通过在应用程序中包含 `linux/dvb/osd.h` 来获取。
OSD 不是一个像许多其他卡那样的帧缓冲区。
它更像是一个可以绘图的画布。
颜色深度取决于安装的内存大小。
需要设置适当的调色板。
可以通过 `OSD_GET_CAPABILITY`_ ioctl 获取已安装的内存大小。

OSD 数据类型
==============

OSD_Command
-----------

概述
~~~~~~~~

.. 代码块:: c

    typedef enum {
	/* 所有函数在“未打开”时返回 -2 */
	OSD_Close = 1,
	OSD_Open,
	OSD_Show,
	OSD_Hide,
	OSD_Clear,
	OSD_Fill,
	OSD_SetColor,
	OSD_SetPalette,
	OSD_SetTrans,
	OSD_SetPixel,
	OSD_GetPixel,
	OSD_SetRow,
	OSD_SetBlock,
	OSD_FillRow,
	OSD_FillBlock,
	OSD_Line,
	OSD_Query,
	OSD_Test,
	OSD_Text,
	OSD_SetWindow,
	OSD_MoveWindow,
	OSD_OpenRaw,
    } OSD_Command;

命令
~~~~~~~~

.. 注意:: 所有函数在“未打开”时返回 -2

.. 平坦表格::
    :表头行数:  1
    :存根列数: 0

    -  .
-  命令

       -  | `osd_cmd_t`_ 结构体中使用的变量
| 如果有替代用法，则使用 {变量}
```markdown
-  `cspan:2` 描述


    -  .
-  ``OSD_Close``

       -  -

       -  | 禁用 OSD 并释放缓冲区
| 成功时返回 0
-  .
-  ``OSD_Open``

       -  | x0, y0, x1, y1,
          | BitPerPixel[2/4/8]{color&0x0F},
          | mix[0..15]{color&0xF0}

       -  | 以指定大小和位深度打开 OSD
          | 成功时返回 0，
          | DRAM 分配错误时返回 -1，
          | 已经打开时返回 -2
-  .
-  ``OSD_Show``

       - -

       -  | 启用 OSD 模式
| 成功时返回 0
-  .
-  ``OSD_Hide``

       - -

       -  | 禁用 OSD 模式
```
| 成功时返回 0
-  .
-  ``OSD_Clear``

       - -

       -  | 将所有像素设置为颜色 0
| 成功时返回 0
-  .
-  ``OSD_Fill``

       -  color

       -  | 将所有像素设置为颜色 <color>
| 成功时返回 0
-  .
-  ``OSD_SetColor``

       -  | color,
          | R{x0},G{y0},B{x1},
          | opacity{y1}

       -  | 将调色板条目 <num> 设置为 <r,g,b>, <mix> 和 <trans> 应用
          | R,G,B: 0..255
          | R=红, G=绿, B=蓝
          | opacity=0: 像素透明度 0%（仅显示视频像素）
          | opacity=1..254: 像素透明度按头部指定
          | opacity=255: 像素透明度 100%（仅显示 OSD 像素）
          | 成功时返回 0，错误时返回 -1
          |
``OSD_SetPalette``
- `firstcolor{color}, lastcolor{x0}, data`
- 设置调色板中的若干项
  | 设置从数组`data`中获取的`firstcolor`到`lastcolor`之间的条目
  | 每种颜色的数据占用4个字节：R, G, B，以及一个透明度值：0 -> 透明，1..254 -> 混合，255 -> 像素

``OSD_SetTrans``
- `transparency{color}`
- 设置混合像素的透明度（0..15）
| 成功时返回0

``OSD_SetPixel``
- `x0, y0, color`
- 将坐标<x>,<y>处的像素设置为颜色号<color>
| 成功时返回0，错误时返回-1

``OSD_GetPixel``
- `x0, y0`
- 返回坐标<x>,<y>处像素的颜色号，或返回-1
| 当前命令不受AV7110支持！

-  .
-  ``OSD_SetRow``

       -  x0, y0, x1, data

       -  | 使用 data[] 的内容填充从 x0, y 到 x1, y 的像素
| 成功返回 0，所有像素被裁剪（未绘制任何像素）时返回 -1
-  .
-  ``OSD_SetBlock``

       -  | x0, y0, x1, y1，
          | increment{color}，
          | data

       -  | 使用 data[] 的内容填充从 x0, y0 到 x1, y1 的像素
| Inc 包含数据块中一行的宽度，inc <= 0 时使用块宽度作为行宽
| 成功返回 0，所有像素被裁剪时返回 -1
-  .
-  ``OSD_FillRow``

       -  x0, y0, x1, color

       -  | 使用颜色 <color> 填充从 x0, y 到 x1, y 的像素
| 成功返回 0，所有像素被裁剪时返回 -1
-  `OSD_FillBlock`
  -  x0, y0, x1, y1, color
  -  | 使用颜色 `<color>` 填充从 (x0, y0) 到 (x1, y1) 的像素
| 成功时返回 0，所有像素被裁剪时返回 -1

-  `OSD_Line`
  -  x0, y0, x1, y1, color
  -  | 用颜色 `<color>` 画一条从 (x0, y0) 到 (x1, y1) 的线
| 成功时返回 0

-  `OSD_Query`
  -  | x0, y0, x1, y1,
      | xasp{color}; yasp=11
  -  | 将参数填充为图像尺寸和像素宽高比
| 成功时返回 0
| 该命令目前不被 AV7110 支持！
``OSD_Test``

-  -

-  | 绘制测试图像
| 仅用于调试目的
| 成功时返回 0
-  .
-  ``OSD_Text``

       -  x0,y0,size,color,text

       -  在位置 (x0, y0) 绘制带有颜色 `<color>` 的文本
-  .
-  ``OSD_SetWindow``

       -  x0

       -  将编号为 0<x0<8 的窗口设置为当前窗口
-  .
-  ``OSD_MoveWindow``

       -  x0,y0

       -  将当前窗口移动到 (x0, y0)
-  .
``OSD_OpenRaw``

       -  | x0,y0,x1,y1,
          | `osd_raw_window_t`_ {color}

       -  打开其他类型的OSD窗口
描述
~~~~~~~~~~~

``OSD_Command`` 数据类型与 `OSD_SEND_CMD`_ ioctl 结合使用，告诉驱动程序要执行哪个 OSD_Command。

osd_cmd_t
---------

概述
~~~~~~~~

.. code-block:: c

    typedef struct osd_cmd_s {
	OSD_Command cmd;
	int x0;
	int y0;
	int x1;
	int y1;
	int color;
	void __user *data;
    } osd_cmd_t;

变量
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``OSD_Command cmd``

       -  要执行的 `OSD_Command`_
-  .
-  ``int x0``

       -  第一个水平位置
-  .
-  ``int y0``

       -  第一个垂直位置
-  .
-  ``int x1``

       -  第二个水平位置
``osd_cmd_t`` 数据类型用于 `OSD_SEND_CMD`_ ioctl。它包含了 OSD 命令的数据和 `OSD_Command`_ 本身。该结构需要传递给驱动程序，并且其成员可能被驱动程序修改。

---

``osd_raw_window_t``
--------------------

概述
~~~~~~~~

.. code-block:: c

    typedef enum {
	OSD_BITMAP1,
	OSD_BITMAP2,
	OSD_BITMAP4,
	OSD_BITMAP8,
	OSD_BITMAP1HR,
	OSD_BITMAP2HR,
	OSD_BITMAP4HR,
	OSD_BITMAP8HR,
	OSD_YCRCB422,
	OSD_YCRCB444,
	OSD_YCRCB444HR,
	OSD_VIDEOTSIZE,
	OSD_VIDEOHSIZE,
	OSD_VIDEOQSIZE,
	OSD_VIDEODSIZE,
	OSD_VIDEOTHSIZE,
	OSD_VIDEOTQSIZE,
	OSD_VIDEOTDSIZE,
	OSD_VIDEONSIZE,
	OSD_CURSOR
    } osd_raw_window_t;

常量
~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  . 

注释：表格部分的内容没有提供具体的常量值，因此这里保留了原始的表格格式。如果提供了具体的内容，请补充完整。
- ``OSD_BITMAP1``
  
       - 1位位图

    -  .
- ``OSD_BITMAP2``
  
       - 2位位图

    -  .
- ``OSD_BITMAP4``
  
       - 4位位图

    -  .
- ``OSD_BITMAP8``
  
       - 8位位图

    -  .
- ``OSD_BITMAP1HR``
  
       - 1位半分辨率位图

    -  .
- ``OSD_BITMAP2HR``
  
       - 2位半分辨率位图

    -  .
- ``OSD_BITMAP4HR``
  
       - 4位半分辨率位图

    -  .
- ``OSD_BITMAP8HR``
  
       - 8位半分辨率位图

    -  .
- ``OSD_YCRCB422``
  
       - 4:2:2 YCRCB 图形显示

    -  .
- ``OSD_YCRCB444``
  
       - 4:4:4 YCRCB 图形显示

    -  .
- ``OSD_YCRCB444HR``  
   - 4:4:4 YCRCB 图形半分辨率

- ``OSD_VIDEOTSIZE``  
   - 真实大小的正常MPEG视频显示

- ``OSD_VIDEOHSIZE``  
   - MPEG视频显示半分辨率

- ``OSD_VIDEOQSIZE``  
   - MPEG视频显示四分之一分辨率

- ``OSD_VIDEODSIZE``  
   - MPEG视频显示双倍分辨率

- ``OSD_VIDEOTHSIZE``  
   - 真实大小的MPEG视频显示半分辨率

- ``OSD_VIDEOTQSIZE``  
   - 真实大小的MPEG视频显示四分之一分辨率

- ``OSD_VIDEOTDSIZE``  
   - 真实大小的MPEG视频显示双倍分辨率

- ``OSD_VIDEONSIZE``  
   - 全尺寸MPEG视频显示

- ``OSD_CURSOR``  
   - 光标

描述
~~~~~~~~~~~

``osd_raw_window_t`` 数据类型用于配合 `OSD_Command`_ 中的 OSD_OpenRaw 命令，告诉驱动程序要打开哪种类型的OSD。
### osd_cap_t

#### 简介
~~~~~~~~

```c
typedef struct osd_cap_s {
    int  cmd;
    #define OSD_CAP_MEMSIZE         1
    long val;
} osd_cap_t;
```

#### 变量
~~~~~~~~

-  ``int  cmd``

   -  要查询的能力
-  ``long val``

   -  用于存储数据

#### 支持的能力
~~~~~~~~~~~~~~~~~~~~~~

-  ``OSD_CAP_MEMSIZE``

   -  卡上安装的内存大小

#### 描述
~~~~~~~~~~~

此数据结构与 `OSD_GET_CAPABILITY`_ 调用一起使用

---

### OSD 函数调用

#### OSD_SEND_CMD
------------

#### 简介
~~~~~~~~

.. c:macro:: OSD_SEND_CMD

```c
int ioctl(int fd, int request = OSD_SEND_CMD, enum osd_cmd_t *cmd)
```

#### 参数
~~~~~~~~~

-  ``int fd``

   -  :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符
-  ``enum osd_cmd_t *cmd``

   -  命令枚举值指针
### `int request`

- 指向此命令的 `osd_cmd_t`_ 结构位置

描述
~~~~

.. 注意:: **不要**在新驱动程序中使用！
         参见：:ref:`legacy_dvb_decoder_notes`

此 ioctl 向卡片发送 `OSD_Command`_。
返回值
~~~~~

成功时返回 0，失败时返回 -1 并且设置 `errno` 变量。通用错误代码在
:ref:`Generic Error Codes <gen-errors>` 章节中描述。

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``EINVAL``

       -  命令超出范围
-----

### OSD_GET_CAPABILITY
----------------------

概述
~~~~

.. c:macro:: OSD_GET_CAPABILITY

.. code-block:: c

    int ioctl(int fd, int request = OSD_GET_CAPABILITY,
    struct osd_cap_t *cap)

参数
~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``int fd``

       -  :cspan:`1` 由先前调用 `open()`_ 返回的文件描述符
-  .
-  ``int request``

       -  对于此命令等于 ``OSD_GET_CAPABILITY``
-  .
``unsigned int *cap``

- 指向此命令的 `osd_cap_t`_ 结构体位置

描述
~~~~~~~~~~~

.. 注意:: 不要在新的驱动程序中使用！
             参见：:ref:`legacy_dvb_decoder_notes`

此ioctl用于获取基于AV7110的DVB解码卡的OSD功能。
.. 提示::
    用户需要设置osd_cap_t结构体并将其传递给驱动程序
返回值
~~~~~~~~~~~~

成功时返回0，失败时返回-1，并且设置适当的`errno`变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述
.. flat-table::
    :header-rows:  0
    :stub-columns: 0


    -  .
-  ``EINVAL``

       -  不支持的功能
-----

open()
------

概要
~~~~~~~~

.. code-block:: c

    #include <fcntl.h>

.. c:function:: int open(const char *deviceName, int flags)

参数
~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .
-  ``const char *deviceName``

       -  具体OSD设备的名称
-  .
-  :rspan:`3` ``int flags``

       -  :cspan:`1` 以下标志的按位或：

    -  .
- ``O_RDONLY``
    - 只读访问

- ``O_RDWR``
    - 读写访问

- ``O_NONBLOCK``
    - 以非阻塞模式打开
      （默认模式为阻塞模式）

描述
~~~~~~~~~~~

此系统调用为后续使用打开一个命名的OSD设备（例如 `/dev/dvb/adapter?/osd0`）

返回值
~~~~~~~~~~~~

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

- ``ENODEV``
    - 设备驱动程序未加载/不可用

- ``EINTERNAL``
    - 内部错误

- ``EBUSY``
    - 设备或资源忙
### close()
#### 概述
~~~ c:function
int close(int fd)
~~~

#### 参数
~~~ flat-table
    :header-rows:  0
    :stub-columns: 0

    -  .
    -  ``int fd``
        -  :cspan:`1` 由先前的 `open()`_ 调用返回的文件描述符
~~~

#### 描述
此系统调用关闭一个先前打开的 OSD 设备。

#### 返回值
~~~ flat-table
    :header-rows:  0
    :stub-columns: 0

    -  .
    -  ``EBADF``
        -  fd 不是一个有效的已打开文件描述符
~~~

#### 错误码
-  ``EINVAL``
    -  无效参数
