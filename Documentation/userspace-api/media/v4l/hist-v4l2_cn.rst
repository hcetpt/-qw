.. 许可证标识符: GFDL-1.1-no-invariants-or-later
.. C 命名空间:: V4L

.. _hist-v4l2:

**************************
V4L2 API 的变更历史
**************************

V4L API 被加入内核后不久，就因其过于僵化而受到批评。1998年8月，Bill Dirks提出了一系列改进，并开始编写文档、示例驱动程序和应用程序。在其他志愿者的帮助下，这最终演变成了V4L2 API，不仅是对V4L API的扩展，而是直接替代了它。然而，新的API直到四年后并在两个稳定版内核发布之后才被正式接受并以当前形式纳入内核。

早期版本
=========

1998-08-20: 第一个版本
1998-08-27: 引入了 :c:func:`select()` 函数
1998-09-10: 新的视频标准接口
1998-09-18: 替换了 ``VIDIOC_NONCAP`` ioctl，用原本无意义的 ``O_TRUNC`` :c:func:`open()` 标志代替，并定义了别名 ``O_NONCAP`` 和 ``O_NOIO``。如果应用程序仅打算访问控制而不进行捕获，则可以设置此标志。``VIDEO_STD_XXX`` 标识符现在是序号而不是标志，并且 ``video_std_construct()`` 辅助函数接收 id 和传输参数
1998-09-28: 重新设计了视频标准，使视频控制可单独枚举
1998-10-02: 从结构体 ``video_standard`` 中移除了 ``id`` 字段，并重命名了颜色副载波字段。:ref:`VIDIOC_QUERYSTD` ioctl 被重命名为 :ref:`VIDIOC_ENUMSTD`，:ref:`VIDIOC_G_INPUT <VIDIOC_G_INPUT>` 被重命名为 :ref:`VIDIOC_ENUMINPUT`。发布了Codec API的第一个草案
1998-11-08: 许多小的更改。大多数符号已被重命名。结构体 v4l2_capability 进行了一些实质性修改
1998-11-12: 某些 ioctl 的读写方向定义错误
1998年11月14日: ``V4L2_PIX_FMT_RGB24`` 更改为 ``V4L2_PIX_FMT_BGR24``，并且 ``V4L2_PIX_FMT_RGB32`` 更改为 ``V4L2_PIX_FMT_BGR32``。音频控制现在可以通过带有 ``V4L2_CID_AUDIO`` 前缀的名称使用 :ref:`VIDIOC_G_CTRL <VIDIOC_G_CTRL>` 和 :ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` ioctl 访问。``V4L2_MAJOR`` 定义从 ``videodev.h`` 中移除，因为它仅在 ``videodev`` 内核模块中使用了一次。添加了 ``YUV422`` 和 ``YUV411`` 平面图像格式。

1998年11月28日: 一些 ioctl 符号发生了变化。增加了编解码器和视频输出设备的接口。

1999年1月14日: 添加了一个原始 VBI 捕获接口。

1999年1月19日: 移除了 ``VIDIOC_NEXTBUF`` ioctl。

V4L2 版本 0.16 1999年1月31日
============================

1999年1月27日: 现在只有一个 QBUF ioctl，VIDIOC_QWBUF 和 VIDIOC_QRBUF 已经被移除。VIDIOC_QBUF 接受一个 v4l2_buffer 作为参数。增加了数字缩放（裁剪）控制功能。

V4L2 版本 0.18 1999年3月16日
============================

在 videodev.c 中增加了一个 v4l 到 V4L2 ioctl 的兼容性层。驱动程序编写者，这会改变你实现 ioctl 处理器的方式。请参阅《驱动程序编写指南》。增加了一些新的控制 ID。

V4L2 版本 0.19 1999年6月5日
============================

1999年3月18日: 在将 v4l2_queryctrl 对象传递给驱动程序之前填充 category 和 catname 字段。需要对示例驱动程序中的 VIDIOC_QUERYCTRL 处理器进行微小更改。
1999年3月31日: 提高了对 v4l 内存捕获 ioctl 的兼容性。需要对驱动程序进行更改以完全支持新的兼容性特性，请参阅《驱动程序编写指南》和 v4l2cap.c。增加了新的控制 ID：V4L2_CID_HFLIP, _VFLIP。将 V4L2_PIX_FMT_YUV422P 改为 _YUV422P，并且 _YUV411P 改为 _YUV411P。
1999年4月4日: 增加了一些新的控制 ID。
1999年4月7日: 增加了按钮控制类型。
1999-05-02: 修复了 videodev.h 中的一个拼写错误，并添加了 V4L2_CTRL_FLAG_GRAYED（后来改为 V4L2_CTRL_FLAG_GRABBED）标志。
1999-05-20: VIDIOC_G_CTRL 的定义错误导致此 ioctl 功能异常。
1999-06-05: 更改了 V4L2_CID_WHITENESS 的值。
V4L2 版本 0.20（1999-09-10）
=================================

版本 0.20 引入了一些更改，这些更改与 0.19 及更早的版本**不兼容**。这些更改的目的是简化 API，使其更具可扩展性，并遵循常见的 Linux 驱动程序 API 规范。

1. 修复了 `V4L2_FMT_FLAG` 符号中的一些拼写错误。struct v4l2_clip 被修改以与 v4l 兼容。（1999-08-30）

2. 添加了 `V4L2_TUNER_SUB_LANG1`。（1999-09-05）

3. 所有使用整数参数的 ioctl 命令现在接受一个指向整数的指针。在适当的情况下，ioctl 将通过指针返回实际的新值，这是 V4L2 API 中的一个常见惯例。受影响的 ioctl 包括：VIDIOC_PREVIEW、VIDIOC_STREAMON、VIDIOC_STREAMOFF、VIDIOC_S_FREQ、VIDIOC_S_INPUT、VIDIOC_S_OUTPUT 和 VIDIOC_S_EFFECT。例如：

   ```c
   err = ioctl (fd, VIDIOC_XXX, V4L2_XXX);
   ```

   变为

   ```c
   int a = V4L2_XXX; err = ioctl(fd, VIDIOC_XXX, &a);
   ```

4. 所有的获取和设置格式的命令被合并为一个 ioctl：`VIDIOC_G_FMT` 和 `VIDIOC_S_FMT`，它们接受一个联合体和一个类型字段来选择联合体成员作为参数。目的是通过消除多个 ioctl 来简化 API，并允许在不增加新 ioctl 的情况下支持新的和驱动程序专用的数据流。
   
   这些更改使以下 ioctl 过时：`VIDIOC_S_INFMT`、`VIDIOC_G_INFMT`、`VIDIOC_S_OUTFMT`、`VIDIOC_G_OUTFMT`、`VIDIOC_S_VBIFMT` 和 `VIDIOC_G_VBIFMT`。图像格式结构体 `struct v4l2_format` 被重命名为 `struct v4l2_pix_format`，而 `struct v4l2_format` 现在是所有格式协商的外围结构。

5. 类似于上述更改，`VIDIOC_G_PARM` 和 `VIDIOC_S_PARM` ioctl 被合并到 `VIDIOC_G_OUTPARM` 和 `VIDIOC_S_OUTPARM` 中。新的结构体 `struct v4l2_streamparm` 中的一个 `type` 字段选择相应的联合体成员。
   
   这些更改使 `VIDIOC_G_OUTPARM` 和 `VIDIOC_S_OUTPARM` ioctl 过时。

6. 控制枚举被简化，并引入了两个新的控制标志，同时删除了一个。`catname` 字段被 `group` 字段取代。
   
   驱动程序现在可以使用 `V4L2_CTRL_FLAG_DISABLED` 和 `V4L2_CTRL_FLAG_GRABBED` 标志标记不受支持和暂时不可用的控制项。`group` 名称表示可能比 `category` 更窄的分类。换句话说，在一个类别内可能有多个组。同一组内的控制项通常会被放在一个组框内。不同类别的控制项可能会有更大的间隔，甚至出现在不同的窗口中。
7. 结构体 `v4l2_buffer` 中的 `timestamp` 字段被更改为一个 64 位整数，包含帧的采样或输出时间（以纳秒为单位）。此外，时间戳将使用绝对系统时间，而不是从流开始时的零开始计时。时间戳的数据类型名称是 `stamp_t`，定义为一个有符号的 64 位整数。输出设备不应在时间戳字段中的时间到达之前发送缓冲区。我希望效仿 SGI 的做法，并采用像他们那样的多媒体时间戳系统 UST（Unadjusted System Time）。详见 http://web.archive.org/web/*/http://reality.sgi.com/cpirazzi_engr/lg/time/intro.html。UST 使用的时间戳是 64 位有符号整数（不是 `struct timeval`），并以纳秒为单位。UST 时钟在系统启动时从零开始，并且连续均匀地运行。UST 溢出需要大约 292 年。无法设置 UST 时钟。常规的 Linux 当天时间时钟可以定期更改，如果用于标记多媒体流的时间戳，则会导致错误。真正的 UST 风格时钟需要内核中的一些支持，但目前还没有。不过为了提前准备，我将把时间戳字段更改为 64 位整数，并将 `v4l2_masterclock_gettime()` 函数（仅由驱动程序使用）的返回值更改为 64 位整数。

8. 在结构体 `v4l2_buffer` 中添加了一个 `sequence` 字段。`sequence` 字段用于计数捕获的帧，在输出设备中被忽略。当捕获驱动程序丢弃一帧时，该帧的序列号会被跳过。

V4L2 版本 0.20 的逐步变更
======================

1999-12-23：在结构体 `v4l2_vbi_format` 中，`reserved1` 字段变为 `offset`。此前，驱动程序要求清除 `reserved1` 字段。
2000-01-13：添加了 `V4L2_FMT_FLAG_NOT_INTERLACED` 标志。
2000-07-31：现在 `videodev.h` 包含了 `linux/poll.h` 头文件，以与原始 `videodev.h` 文件兼容。
2000-11-20：添加了 `V4L2_TYPE_VBI_OUTPUT` 和 `V4L2_PIX_FMT_Y41P`。
2000-11-25：添加了 `V4L2_TYPE_VBI_INPUT`。
2000-12-04：修正了一些符号名中的拼写错误。
2001-01-18：为了避免命名空间冲突，将 `videodev.h` 头文件中定义的 `fourcc` 宏重命名为 `v4l2_fourcc`。
2001-01-25：修复了 Linux 2.4.0 中的 `videodev.h` 文件与 `videodevX` 补丁中包含的 `videodev.h` 文件之间可能存在的驱动级兼容性问题。使用早期版本 `videodevX` 的用户应重新编译他们的 V4L 和 V4L2 驱动程序。
2001年1月26日：修复了``videodevX``补丁中的``videodev.h``文件与应用了devfs补丁的Linux 2.2.x中的``videodev.h``文件之间的可能内核级不兼容问题。

2001年3月2日：某些V4L ioctl在定义为只读参数的情况下，实际上双向传递数据，无法通过向后兼容层正确工作。[解决方案？]

2001年4月13日：添加了大端字节序的16位RGB格式。

2001年9月17日：添加了新的YUV格式以及:ref:`VIDIOC_G_FREQUENCY <VIDIOC_G_FREQUENCY>`和:ref:`VIDIOC_S_FREQUENCY <VIDIOC_G_FREQUENCY>` ioctl。旧的``VIDIOC_G_FREQ``和``VIDIOC_S_FREQ`` ioctl没有考虑多个调谐器的情况。

2000年9月18日：添加了``V4L2_BUF_TYPE_VBI``。这可能会*破坏兼容性*，因为:ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>`和:ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl现在如果结构体``v4l2_fmt``的``type``字段不包含``V4L2_BUF_TYPE_VBI``可能会失败。在结构体`v4l2_vbi_format`的文档中，“上升沿”这一模糊表述被改为“前沿”。

V4L2 版本 0.20 2000年11月23日
=================================

对原始VBI接口进行了多项更改：
1. 在V4L2 API规范中增加了清晰说明行号计数方案的图示。“start”\[0\]和“start”\[1\]字段不再从零开始计数行号。理由：a) 原来的定义不清楚。b) “start”\[\]值是序数。c) 没有必要发明新的行号计数方案。我们现在使用ITU-R定义的行号。兼容性：将起始值加一。依赖于旧语义的应用程序可能无法正常工作。
2. 将限制“count\[0\] > 0 和 count\[1\] > 0”放宽到“(count\[0\] + count\[1\]) > 0”。理由：驱动程序可能以扫描线为单位分配资源，并且一些数据服务仅在第一场传输。之前关于两个“count”值通常相等的注释是误导性的且无意义，已被删除。此更改*破坏了与早期版本的兼容性*：驱动程序可能会返回``EINVAL``，应用程序可能无法正常工作。
3. 允许驱动程序再次返回负（未知）的起始值，正如早先提出的那样。为什么取消该功能尚不清楚。此更改可能会*破坏依赖于起始值为正数的应用程序的兼容性*。澄清了使用:ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl时的``EBUSY``和``EINVAL``错误代码。最终记录了``EBUSY``错误代码，并提到了之前仅在``videodev.h``头文件中提到的``reserved2``字段。
4. 添加了新的缓冲类型``V4L2_TYPE_VBI_INPUT``和``V4L2_TYPE_VBI_OUTPUT``。前者是旧的``V4L2_TYPE_VBI``的别名，后者之前在``videodev.h``文件中缺失。
V4L2 版本 0.20 2002-07-25
============================

添加了切片 VBI 接口提案
V4L2 在 Linux 2.5.46 中，2002-10
=============================

大约在 2002 年 10 月到 11 月，在宣布对 Linux 2.5 进行功能冻结之前，API 进行了修订，吸取了 V4L2 0.20 的经验。这个未命名的版本最终合并到了 Linux 2.5.46 中。

1. 如 :ref:`related` 所规定，驱动程序必须为所有次要设备号提供相关设备功能。
2. :c:func:`open()` 函数要求访问模式为 ``O_RDWR``，无论设备类型如何。所有与应用程序交换数据的 V4L2 驱动程序都必须支持 ``O_NONBLOCK`` 标志。``O_NOIO`` 标志（一个与无意义的 ``O_TRUNC`` 别名相同的 V4L2 符号，用于指示没有数据交换的应用程序）被删除。驱动程序必须保持在“面板模式”，直到应用程序尝试发起数据交换，详见 :ref:`open`。
3. 结构体 v4l2_capability 发生了重大变化。请注意结构体的大小也发生了变化，这在 ioctl 请求代码中进行了编码，因此较旧的 V4L2 设备将对新的 :ref:`VIDIOC_QUERYCAP` ioctl 返回 ``EINVAL`` 错误码。

新增了用于标识驱动程序的字段、一个新的 RDS 设备功能 ``V4L2_CAP_RDS_CAPTURE``、标志 ``V4L2_CAP_AUDIO`` 表示设备是否有音频连接器、另一个 I/O 能力 V4L2_CAP_ASYNCIO 可以被标记。作为这些变化的响应，“type”字段变成了位集，并被合并到“flags”字段中。“V4L2_FLAG_TUNER”被重命名为“V4L2_CAP_TUNER”，“V4L2_CAP_VIDEO_OVERLAY”取代了“V4L2_FLAG_PREVIEW”，“V4L2_CAP_VBI_CAPTURE”和“V4L2_CAP_VBI_OUTPUT”取代了“V4L2_FLAG_DATA_SERVICE”。

``V4L2_FLAG_READ`` 和 ``V4L2_FLAG_WRITE`` 被合并为 ``V4L2_CAP_READWRITE``。

冗余字段 “inputs”、“outputs” 和 “audios” 被移除。这些属性可以按照 :ref:`video` 和 :ref:`audio` 中描述的方法确定。

稍微不稳定的且几乎没有用处的字段 “maxwidth”、“maxheight”、“minwidth”、“minheight”、“maxframerate” 被移除。这些信息可以通过 :ref:`format` 和 :ref:`standard` 中描述的方式获得。
``V4L2_FLAG_SELECT`` 已被移除。我们认为 `select()` 函数对于所有与应用程序交换数据的 V4L2 驱动程序来说非常重要，因此需要支持它。冗余的 ``V4L2_FLAG_MONOCHROME`` 标志已被移除，这些信息如 :ref:`format` 中所述。

4. 在 `struct v4l2_input` 中，`assoc_audio` 字段和 `capability` 字段及其唯一的标志 `V4L2_INPUT_CAP_AUDIO` 被新的 `audioset` 字段取代。此字段不再表示一个视频输入与一个音频输入之间的关联，而是报告该视频输入组合的所有音频输入。
新增的字段包括 `tuner`（反转了从前的调谐器到视频输入的链接），`std` 和 `status`。

相应地，`struct v4l2_output` 移除了其 `capability` 和 `assoc_audio` 字段，并新增了 `audioset`、`modulator` 和 `std` 字段。

5. `struct v4l2_audio` 的 `audio` 字段被重命名为 `index`，以与其他结构保持一致。新增了一个能力标志 `V4L2_AUDCAP_STEREO`，用于指示音频输入是否支持立体声。
移除了 `V4L2_AUDCAP_EFFECTS` 及其对应的 `V4L2_AUDMODE` 标志，这可以通过控制轻松实现（不过这也适用于仍然存在的 AVL）。

同样为了保持一致性，`struct v4l2_audioout` 的 `audio` 字段也被重命名为 `index`。

6. `struct v4l2_tuner` 的 `input` 字段被替换为 `index` 字段，允许设备具有多个调谐器。视频输入与调谐器之间的链接现在被反转，输入指向它们的调谐器。`std` 子结构变成了一个简单的集合（关于这一点下面有更多内容），并移到了 `struct v4l2_input` 中。
新增了一个 `type` 字段。
因此，在 `struct v4l2_modulator` 中，`output` 字段被替换为 `index` 字段。在 `struct v4l2_frequency` 中，`port` 字段被替换为包含相应调谐器或调制器索引号的 `tuner` 字段。添加了一个 `tuner type` 字段，并且 `reserved` 字段变大以供未来扩展（特别是卫星调谐器）。

7. 完全透明视频标准的想法被放弃了。经验表明，应用程序必须能够处理超出简单菜单展示的视频标准。应用程序现在可以使用 `:ref:v4l2_std_id<v4l2-std-id>` 和 `videodev2.h` 头文件中定义的符号来引用支持的标准。详细信息请参见 `:ref:standard`。`:ref:VIDIOC_G_STD<VIDIOC_G_STD>` 和 `:ref:VIDIOC_S_STD<VIDIOC_G_STD>` 现在接受指向该类型的指针作为参数。`:ref:VIDIOC_QUERYSTD` 被添加用于自动检测接收到的标准（如果硬件具备此功能）。在 `struct v4l2_standard` 中，添加了一个 `index` 字段用于 `:ref:VIDIOC_ENUMSTD`。添加了一个名为 `id` 的 `:ref:v4l2_std_id<v4l2-std-id>` 字段作为机器可读标识符，同时取代了 `transmission` 字段。误导性的 `framerate` 字段被重命名为 `frameperiod`。现在已经过时的 `colorstandard` 信息，最初是为了区分不同标准的变体，已被移除。
`struct v4l2_enumstd` 不再使用。`:ref:VIDIOC_ENUMSTD` 现在接受一个指向 `struct v4l2_standard` 的指针。视频输入或输出支持哪些标准的信息已移至 `struct v4l2_input` 和 `struct v4l2_output` 中名为 `std` 的字段。

8. `struct :ref:v4l2_queryctrl<v4l2-queryctrl>` 中的 `category` 和 `group` 字段并未流行起来，或者没有按预期实现，因此被移除。

9. 添加了 `:ref:VIDIOC_TRY_FMT<VIDIOC_G_FMT>` ioctl 来协商数据格式，类似于 `:ref:VIDIOC_S_FMT<VIDIOC_G_FMT>`，但没有编程硬件的开销，并且不受正在进行的 I/O 影响。在 `struct v4l2_format` 中，`fmt` 联合体被扩展以包含 `struct v4l2_window`。所有图像格式的协商现在都可以通过 `VIDIOC_G_FMT`、`VIDIOC_S_FMT` 和 `VIDIOC_TRY_FMT` ioctl 来完成。`VIDIOC_G_WIN` 和 `VIDIOC_S_WIN` ioctl 用于准备视频覆盖，已被移除。`type` 字段更改为枚举类型 `enum v4l2_buf_type`，缓冲区类型名称如下更改：
```
Old defines    | enum v4l2_buf_type
---------------------------------
V4L2_BUF_TYPE_CAPTURE | V4L2_BUF_TYPE_VIDEO_CAPTURE
V4L2_BUF_TYPE_CODECIN | Omitted for now
V4L2_BUF_TYPE_CODECOUT| Omitted for now
V4L2_BUF_TYPE_EFFECTSIN| Omitted for now
V4L2_BUF_TYPE_EFFECTSIN2| Omitted for now
V4L2_BUF_TYPE_EFFECTSOUT| Omitted for now
V4L2_BUF_TYPE_VIDEOOUT | V4L2_BUF_TYPE_VIDEO_OUTPUT
-                      | V4L2_BUF_TYPE_VIDEO_OVERLAY
-                      | V4L2_BUF_TYPE_VBI_CAPTURE
-                      | V4L2_BUF_TYPE_VBI_OUTPUT
-                      | V4L2_BUF_TYPE_SLICED_VBI_CAPTURE
-                      | V4L2_BUF_TYPE_SLICED_VBI_OUTPUT
V4L2_BUF_TYPE_PRIVATE_BASE | V4L2_BUF_TYPE_PRIVATE (但这是弃用的)
```

10. 在 `struct v4l2_fmtdesc` 中，添加了一个与 `struct v4l2_format` 类似的 `enum v4l2_buf_type` 类型的 `type` 字段。`:ref:VIDIOC_ENUM_FBUFFMT` ioctl 已不再需要并被移除。这些调用可以用 `:ref:VIDIOC_ENUM_FMT` 替代，类型为 `V4L2_BUF_TYPE_VIDEO_OVERLAY`。
11. 在结构体 `v4l2_pix_format` 中，移除了 `depth` 字段，假设应用程序通过其四字符代码识别格式时已经知道颜色深度，而其他应用程序并不关心这个字段。同样的理由导致移除了 `V4L2_FMT_FLAG_COMPRESSED` 标志。由于驱动程序不应该在内核空间中转换图像，因此移除了 `V4L2_FMT_FLAG_SWCONVECOMPRESSED` 标志。应该提供一个用户库来代替转换函数。`V4L2_FMT_FLAG_BYTESPERLINE` 标志是冗余的。应用程序可以通过将 `bytesperline` 字段设置为零来获得一个合理的默认值。由于剩下的标志也被替换，因此移除了 `flags` 字段本身。
   
   交错标志被一个新的 `field` 字段中的枚举类型 `v4l2_field` 替代。
   
   .. flat-table::
       :header-rows:  1
       :stub-columns: 0

       * - 旧标志
         - 枚举 v4l2_field
       * - `V4L2_FMT_FLAG_NOT_INTERLACED`
         - ?
       * - `V4L2_FMT_FLAG_INTERLACED` = `V4L2_FMT_FLAG_COMBINED`
         - `V4L2_FIELD_INTERLACED`
       * - `V4L2_FMT_FLAG_TOPFIELD` = `V4L2_FMT_FLAG_ODDFIELD`
         - `V4L2_FIELD_TOP`
       * - `V4L2_FMT_FLAG_BOTFIELD` = `V4L2_FMT_FLAG_EVENFIELD`
         - `V4L2_FIELD_BOTTOM`
       * - `-`
         - `V4L2_FIELD_SEQ_TB`
       * - `-`
         - `V4L2_FIELD_SEQ_BT`
       * - `-`
         - `V4L2_FIELD_ALTERNATE`

   颜色空间标志被一个新的 `colorspace` 字段中的枚举类型 `v4l2_colorspace` 替代，其中 `V4L2_COLORSPACE_SMPTE170M`、`V4L2_COLORSPACE_BT878`、`V4L2_COLORSPACE_470_SYSTEM_M` 或 `V4L2_COLORSPACE_470_SYSTEM_BG` 取代了 `V4L2_FMT_CS_601YUV`。

12. 在结构体 `v4l2_requestbuffers` 中，`type` 字段被正确定义为枚举类型 `v4l2_buf_type`。缓冲区类型如上所述进行了更改。新增了一个 `memory` 字段，类型为枚举类型 `v4l2_memory`，用于区分由驱动程序或应用程序分配的缓冲区。详见 :ref:`io`。

13. 在结构体 `v4l2_buffer` 中，`type` 字段被正确定义为枚举类型 `v4l2_buf_type`。缓冲区类型如上所述进行了更改。新增了一个 `field` 字段，类型为枚举类型 `v4l2_field`，用于指示缓冲区包含的是顶部场还是底部场。旧的字段标志被移除。由于没有按计划在内核中添加未调整的系统时间时钟，`timestamp` 字段从类型 `stamp_t`（一个表示样本时间的64位无符号整数）变回 `struct timeval`。随着第二种内存映射方法的增加，`offset` 字段移到了联合体 `m` 中，并新增了一个 `memory` 字段，类型为枚举类型 `v4l2_memory`，用于区分 I/O 方法。详见 :ref:`io`。

   `V4L2_BUF_REQ_CONTIG` 标志曾被 V4L 兼容性层使用，在对该代码进行更改后，它不再需要。`V4L2_BUF_ATTR_DEVICEMEM` 标志会指示缓冲区是否确实分配在设备内存而不是可DMA的系统内存中。该标志几乎没用，因此被移除。

14. 在结构体 `v4l2_framebuffer` 中，`base[3]` 数组预见到双缓冲和三缓冲在离屏视频内存中的使用，但并未定义同步机制，因此被替换为一个单一指针。`V4L2_FBUF_CAP_SCALEUP` 和 `V4L2_FBUF_CAP_SCALEDOWN` 标志被移除。应用程序可以使用新的裁剪和缩放接口更准确地确定这些功能。`V4L2_FBUF_CAP_CLIPPING` 标志被 `V4L2_FBUF_CAP_LIST_CLIPPING` 和 `V4L2_FBUF_CAP_BITMAP_CLIPPING` 替换。

15. 在结构体 `v4l2_clip` 中，`x`、`y`、`width` 和 `height` 字段被移到一个名为 `c` 的子结构体中，类型为 `v4l2_rect`。`x` 和 `y` 字段被重命名为 `left` 和 `top`，即相对于上下文相关的原点的偏移量。
16. 在结构体 `v4l2_window` 中，字段 `x`、`y`、`width` 和 `height` 被移到了一个名为 `w` 的子结构体中。新增了一个类型为 `enum v4l2_field` 的字段 `field`，用于区分场（interlaced）和帧覆盖。

17. 数码变焦接口，包括 `struct v4l2_zoomcap`、`struct v4l2_zoom`、`V4L2_ZOOM_NONCAP` 和 `V4L2_ZOOM_WHILESTREAMING` 被一个新的裁剪和缩放接口取代。此前未使用的 `struct v4l2_cropcap` 和 `struct v4l2_crop` 被重新定义用于此目的。详细信息见 :ref:`crop`。

18. 在结构体 `v4l2_vbi_format` 中，字段 `SAMPLE_FORMAT` 现在包含一个四字符代码，用于标识视频图像格式，并且 `V4L2_PIX_FMT_GREY` 取代了 `V4L2_VBI_SF_UBYTE` 定义。字段 `reserved` 被扩展了。

19. 在结构体 `v4l2_captureparm` 中，字段 `timeperframe` 的类型从无符号长整型改为 `struct v4l2_fract`。这允许准确表达 NTSC-M 帧率的倍数（30000 / 1001）。新增了一个字段 `readbuffers` 用于控制读取 I/O 模式下的驱动行为。
类似的改动也应用到了 `struct v4l2_outputparm`。

20. 结构体 `v4l2_performance` 和 `VIDIOC_G_PERF` ioctl 被移除。除了使用 :ref:`读写 I/O 方法 <rw>`（该方法本身是有限制的），这些信息已经对应用程序可用。

21. 旧版 V4L2 文档中的 RGB 到 YCbCr 色彩空间转换示例不准确，这个问题已经在 :ref:`pixfmt` 中得到了修正。

V4L2 2003-06-19
===============

1. 新增了一个能力标志 `V4L2_CAP_RADIO` 用于无线电设备。在此更改之前，无线电设备仅通过具有一个类型字段为 `V4L2_TUNER_RADIO` 的调谐器来识别。

2. 添加了一个可选的驱动访问优先级机制，详细信息见 :ref:`app-pri`。
3. 发现音频输入和输出接口不完整
此前，:ref:`VIDIOC_G_AUDIO <VIDIOC_G_AUDIO>` ioctl 用于枚举可用的音频输入。然而，没有一个 ioctl 可以确定当前的音频输入（如果存在多个音频输入与当前视频输入组合使用）。因此，`VIDIOC_G_AUDIO` 被重命名为 `VIDIOC_G_AUDIO_OLD`，此 ioctl 在内核 2.6.39 中被移除。新增了 :ref:`VIDIOC_ENUMAUDIO` ioctl 用于枚举音频输入，而 :ref:`VIDIOC_G_AUDIO <VIDIOC_G_AUDIO>` 现在报告当前的音频输入。
对 :ref:`VIDIOC_G_AUDOUT <VIDIOC_G_AUDOUT>` 和 :ref:`VIDIOC_ENUMAUDOUT <VIDIOC_ENUMAUDOUT>` 也进行了同样的更改。
在此之后，“videodev”模块将自动在旧版和新版 ioctl 之间进行转换，但驱动程序和应用程序必须更新才能成功重新编译。

4. :ref:`VIDIOC_OVERLAY` ioctl 被错误地定义为写读参数。它已被更改为只写参数，同时写读版本被重命名为 `VIDIOC_OVERLAY_OLD`。
旧的 ioctl 在内核 2.6.39 中被移除。“videodev”内核模块将继续自动转换到新版本，因此驱动程序需要重新编译，但应用程序不需要。

5. :ref:`overlay` 错误地说明剪裁矩形定义了视频可见的区域。正确的说法是剪裁矩形定义了不应显示视频的区域，从而可以看到图形表面。

6. :ref:`VIDIOC_S_PARM <VIDIOC_G_PARM>` 和 :ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` ioctl 被定义为只写参数，这与其他修改参数的 ioctl 不一致。它们被更改为写读参数，同时在只写版本中添加了 `_OLD` 后缀。旧的 ioctl 在内核 2.6.39 中被移除。假设参数不变的驱动程序和应用程序需要更新。

V4L2 2003-11-05
===============

1. 在 :ref:`pixfmt-rgb` 中，以下像素格式从 Bill Dirks 的 V4L2 规范中被错误地转移。下面的描述指内存中的字节顺序，按地址递增顺序排列。
.. flat-table::
       :header-rows:  1
       :stub-columns: 0

       * - 符号
	 - 修订 0.5 之前的文档
	 - 纠正后
       * - ``V4L2_PIX_FMT_RGB24``
	 - B, G, R
	 - R, G, B
       * - ``V4L2_PIX_FMT_BGR24``
	 - R, G, B
	 - B, G, R
       * - ``V4L2_PIX_FMT_RGB32``
	 - B, G, R, X
	 - R, G, B, X
       * - ``V4L2_PIX_FMT_BGR32``
	 - R, G, B, X
	 - B, G, R, X

   `V4L2_PIX_FMT_BGR24` 示例始终正确。
在 :ref:`v4l-image-properties` 中，对 V4L 的 ``VIDEO_PALETTE_RGB24`` 和 ``VIDEO_PALETTE_RGB32`` 格式到 V4L2 像素格式的映射进行了相应的修正。

2. 与上述修复无关的是，驱动程序仍可能以不同的方式解释某些 V4L2 RGB 像素格式。这些问题尚未解决，详细信息请参见 :ref:`pixfmt-rgb`

Linux 2.6.6 中的 V4L2，2004-05-09
==================================

1. :ref:`VIDIOC_CROPCAP` ioctl 被错误地定义为只读参数。现在它被定义为写-读 ioctl，而只读版本被重命名为 ``VIDIOC_CROPCAP_OLD``。旧的 ioctl 在内核 2.6.39 中被移除。

Linux 2.6.8 中的 V4L2
=====================

1. 在 struct v4l2_buffer 中新增了一个字段 ``input``（之前的 ``reserved[0]``）。此字段的目的在于在视频捕获过程中交替使用视频输入（例如摄像头）。此功能必须通过新的 ``V4L2_BUF_FLAG_INPUT`` 标志启用。字段 ``flags`` 不再是只读的。

V4L2 规范勘误，2004-08-01
===========================

1. :ref:`func-open` 函数的返回值被错误地记录。
2. 音频输出 ioctl 结尾应为 -AUDOUT，而不是 -AUDIOOUT。
3. 在当前音频输入示例中，ioctl ``VIDIOC_G_AUDIO`` 使用了错误的参数。
4. :ref:`VIDIOC_QBUF` 和 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl 的文档没有提到 struct v4l2_buffer 的 ``memory`` 字段。这一字段在示例中也缺失。此外，在 ``VIDIOC_DQBUF`` 页面上，未记录 ``EIO`` 错误码。

Linux 2.6.14 中的 V4L2
======================

1. 新增了一个分片 VBI 接口。该接口在 :ref:`sliced` 中有详细描述，并取代了 V4L2 规格 0.8 版本中最初提出的接口。

Linux 2.6.15 中的 V4L2
======================

1. 新增了 :ref:`VIDIOC_LOG_STATUS` ioctl。
2. 定义了新的视频标准 ``V4L2_STD_NTSC_443``、``V4L2_STD_SECAM_LC``、``V4L2_STD_SECAM_DK``（一组 SECAM D、K 和 K1）和 ``V4L2_STD_ATSC``（一组 ``V4L2_STD_ATSC_8_VSB`` 和 ``V4L2_STD_ATSC_16_VSB``）。请注意，现在 ``V4L2_STD_525_60`` 集合中包含了 ``V4L2_STD_NTSC_443``。详情请参见 :ref:`v4l2-std-id`

3. ``VIDIOC_G_COMP`` 和 ``VIDIOC_S_COMP`` ioctl 分别重命名为 ``VIDIOC_G_MPEGCOMP`` 和 ``VIDIOC_S_MPEGCOMP``。它们的参数被替换为一个指向 ``v4l2_mpeg_compression`` 结构体的指针。（``VIDIOC_G_MPEGCOMP`` 和 ``VIDIOC_S_MPEGCOMP`` ioctl 在 Linux 2.6.25 中被移除。）

V4L2 规格勘误表 2005-11-27
============================

在 :ref:`capture-example` 中的捕获示例调用了 :ref:`VIDIOC_S_CROP <VIDIOC_G_CROP>` ioctl 而没有检查是否支持裁剪功能。在 :ref:`standard` 中的视频标准选择示例中，:ref:`VIDIOC_S_STD <VIDIOC_G_STD>` 调用使用了错误的参数类型。

V4L2 规格勘误表 2006-01-10
============================

1. 结构体 v4l2_input 中的 ``V4L2_IN_ST_COLOR_KILL`` 标志不仅表示颜色杀手是否启用，还表示其是否活跃（颜色杀手在检测到视频信号中无颜色时禁用颜色解码以提高图像质量。）

2. :ref:`VIDIOC_S_PARM <VIDIOC_G_PARM>` 是一个写读 ioctl，而不是仅写 ioctl，如其参考页所述。该 ioctl 在 2003 年进行了更改。

V4L2 规格勘误表 2006-02-03
============================

1. 在结构体 v4l2_captureparm 和 v4l2_outputparm 中的 ``timeperframe`` 字段给出的时间单位是秒，而不是微秒。

V4L2 规格勘误表 2006-02-04
============================

1. 结构体 v4l2_window 中的 ``clips`` 字段必须指向一个 v4l2_clip 结构体数组，而不是链表，因为驱动程序忽略结构体 v4l2_clip 的 ``next`` 指针。

Linux 2.6.17 中的 V4L2
====================

1. 新增了视频标准宏：``V4L2_STD_NTSC_M_KR``（南韩 NTSC M），以及集合 ``V4L2_STD_MN``、``V4L2_STD_B``、``V4L2_STD_GH`` 和 ``V4L2_STD_DK``。现在 ``V4L2_STD_NTSC`` 和 ``V4L2_STD_SECAM`` 集合分别包含了 ``V4L2_STD_NTSC_M_KR`` 和 ``V4L2_STD_SECAM_LC``。

2. 定义了一个新的 ``V4L2_TUNER_MODE_LANG1_LANG2`` 来记录双语节目的两种语言。现在使用 ``V4L2_TUNER_MODE_STEREO`` 的目的已过时。详情请参见 :ref:`VIDIOC_G_TUNER <VIDIOC_G_TUNER>` 部分。

V4L2 规格勘误表 2006-09-23（草案 0.15）
=========================================

1. 在多个地方未提及切片 VBI 接口中的 ``V4L2_BUF_TYPE_SLICED_VBI_CAPTURE`` 和 ``V4L2_BUF_TYPE_SLICED_VBI_OUTPUT`` 缓冲区类型。

2. 在 :ref:`VIDIOC_G_AUDIO <VIDIOC_G_AUDIO>` 中澄清了结构体 v4l2_audio 的 ``mode`` 字段是一个标志字段。
3. :ref:`VIDIOC_QUERYCAP` 没有提及切片 VBI 和无线电功能标志。
4. 在 :ref:`VIDIOC_G_FREQUENCY <VIDIOC_G_FREQUENCY>` 中明确指出，应用程序必须在调用 :ref:`VIDIOC_S_FREQUENCY <VIDIOC_G_FREQUENCY>` 之前初始化结构体 v4l2_frequency 中的调谐器 `type` 字段。
5. 结构体 v4l2_requestbuffers 中的 `reserved` 数组有 2 个元素，而不是 32 个。
6. 在 :ref:`output` 和 :ref:`raw-vbi` 中，从未被广泛采用的设备文件名 `/dev/vout` 被替换为 `/dev/video`。
7. 在 Linux 2.6.15 中，VBI 设备次设备号的可能范围从 224-239 扩展到了 224-255。因此，现在可以使用设备文件名 `/dev/vbi0` 到 `/dev/vbi31`。

V4L2 在 Linux 2.6.18 中的变化
============================

1. 新增了 ioctl 命令 :ref:`VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>`、:ref:`VIDIOC_S_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 和 :ref:`VIDIOC_TRY_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>`，新增了一个标志来跳过不支持的控制项 :ref:`VIDIOC_QUERYCTRL`，新的控制类型 `V4L2_CTRL_TYPE_INTEGER64` 和 `V4L2_CTRL_TYPE_CTRL_CLASS`（枚举类型 v4l2_ctrl_type），以及新的控制标志 `V4L2_CTRL_FLAG_READ_ONLY`、`V4L2_CTRL_FLAG_UPDATE`、`V4L2_CTRL_FLAG_INACTIVE` 和 `V4L2_CTRL_FLAG_SLIDER`（:ref:`control-flags`）。详细信息请参见 :ref:`extended-controls`。

V4L2 在 Linux 2.6.19 中的变化
============================

1. 在结构体 v4l2_sliced_vbi_cap 中添加了一个缓冲区类型字段，替换了保留字段。请注意，在枚举类型的大小与整型大小不同的架构上，结构体的大小发生了变化。ioctl 命令 :ref:`VIDIOC_G_SLICED_VBI_CAP <VIDIOC_G_SLICED_VBI_CAP>` 从只读重新定义为读写。应用程序现在必须初始化类型字段并清除保留字段。这些更改可能会导致与旧驱动程序和应用程序的**兼容性问题**。
2. 新增了 ioctl 命令 :ref:`VIDIOC_ENUM_FRAMESIZES` 和 :ref:`VIDIOC_ENUM_FRAMEINTERVALS`。
3. 新增了一个像素格式 `V4L2_PIX_FMT_RGB444`（:ref:`pixfmt-rgb`）。

V4L2 规范勘误表 2006-10-12（草稿 0.17）
=========================================

1. `V4L2_PIX_FMT_HM12`（:ref:`reserved-formats`）是一个 YUV 4:2:0 格式，而非 4:2:2 格式。
V4L2在Linux 2.6.21中的更新
====================

1. 现在`videodev2.h`头文件采用GNU通用公共许可证（版本二或更高）和3条款BSD风格的许可证双重授权。

V4L2在Linux 2.6.22中的更新
====================

1. 添加了两种新的场顺序`V4L2_FIELD_INTERLACED_TB`和`V4L2_FIELD_INTERLACED_BT`。详情请参见枚举v4l2_field。
2. 视频覆盖接口中添加了三种新的裁剪/混合方法，支持全局、直接或反向局部alpha值。详细信息请参考`VIDIOC_G_FBUF`和`VIDIOC_S_FBUF`的ioctl描述。
   `struct v4l2_window`中新增了一个`global_alpha`字段，扩展了该结构。这可能会**破坏与直接使用`struct v4l2_window`的应用程序的兼容性**。然而，使用指向带有填充字节的`struct v4l2_format`父结构的`VIDIOC_G/S/TRY_FMT` ioctl 不受影响。
3. `struct v4l2_window`中的`chromakey`字段格式从“主机顺序RGB32”更改为与帧缓冲区相同的像素值。这可能会**破坏现有应用程序的兼容性**。目前未知有支持“主机顺序RGB32”格式的驱动程序。

V4L2在Linux 2.6.24中的更新
====================

1. 添加了像素格式`V4L2_PIX_FMT_PAL8`、`V4L2_PIX_FMT_YUV444`、`V4L2_PIX_FMT_YUV555`、`V4L2_PIX_FMT_YUV565`和`V4L2_PIX_FMT_YUV32`。

V4L2在Linux 2.6.25中的更新
====================

1. 添加了像素格式`V4L2_PIX_FMT_Y16`和`V4L2_PIX_FMT_SBGGR16`。
2. 新增了控制项`V4L2_CID_POWER_LINE_FREQUENCY`、`V4L2_CID_HUE_AUTO`、`V4L2_CID_WHITE_BALANCE_TEMPERATURE`、`V4L2_CID_SHARPNESS`和`V4L2_CID_BACKLIGHT_COMPENSATION`。同时，`V4L2_CID_BLACK_LEVEL`、`V4L2_CID_WHITENESS`、`V4L2_CID_HCENTER`和`V4L2_CID_VCENTER`被标记为已弃用。
3. 添加了 :ref:`Camera controls class <camera-controls>`，其中包括新的控制项 ``V4L2_CID_EXPOSURE_AUTO``、``V4L2_CID_EXPOSURE_ABSOLUTE``、``V4L2_CID_EXPOSURE_AUTO_PRIORITY``、``V4L2_CID_PAN_RELATIVE``、``V4L2_CID_TILT_RELATIVE``、``V4L2_CID_PAN_RESET``、``V4L2_CID_TILT_RESET``、``V4L2_CID_PAN_ABSOLUTE``、``V4L2_CID_TILT_ABSOLUTE``、``V4L2_CID_FOCUS_ABSOLUTE``、``V4L2_CID_FOCUS_RELATIVE`` 和 ``V4L2_CID_FOCUS_AUTO``。
4. 已经被 Linux 2.6.18 中的 :ref:`extended controls <extended-controls>` 接口取代的 ``VIDIOC_G_MPEGCOMP`` 和 ``VIDIOC_S_MPEGCOMP`` ioctls 最终从 ``videodev2.h`` 头文件中移除。

V4L2 在 Linux 2.6.26 中的变化
====================

1. 添加了像素格式 ``V4L2_PIX_FMT_Y16`` 和 ``V4L2_PIX_FMT_SBGGR16``。
2. 添加了用户控制项 ``V4L2_CID_CHROMA_AGC`` 和 ``V4L2_CID_COLOR_KILLER``。

V4L2 在 Linux 2.6.27 中的变化
====================

1. 添加了 :ref:`VIDIOC_S_HW_FREQ_SEEK` ioctl 和 ``V4L2_CAP_HW_FREQ_SEEK`` 能力。
2. 添加了像素格式 ``V4L2_PIX_FMT_YVYU``、``V4L2_PIX_FMT_PCA501``、``V4L2_PIX_FMT_PCA505``、``V4L2_PIX_FMT_PCA508``、``V4L2_PIX_FMT_PCA561``、``V4L2_PIX_FMT_SGBRG8``、``V4L2_PIX_FMT_PAC207`` 和 ``V4L2_PIX_FMT_PJPG``。

V4L2 在 Linux 2.6.28 中的变化
====================

1. 添加了 ``V4L2_MPEG_AUDIO_ENCODING_AAC`` 和 ``V4L2_MPEG_AUDIO_ENCODING_AC3`` MPEG 音频编码。
2. 添加了 ``V4L2_MPEG_VIDEO_ENCODING_MPEG_4_AVC`` MPEG 视频编码。
3. 添加了像素格式 ``V4L2_PIX_FMT_SGRBG10`` 和 ``V4L2_PIX_FMT_SGRBG10DPCM8``。

V4L2 在 Linux 2.6.29 中的变化
====================

1. 将 ``VIDIOC_G_CHIP_IDENT`` ioctl 重命名为 ``VIDIOC_G_CHIP_IDENT_OLD`` 并引入了 ``VIDIOC_DBG_G_CHIP_IDENT``。旧的结构体 ``v4l2_chip_ident`` 也被重命名为 ``v4l2_chip_ident_old``。
V4L2在Linux 2.6.30中的更新
====================

1. 新增了像素格式 ``V4L2_PIX_FMT_VYUY``、``V4L2_PIX_FMT_NV16`` 和 ``V4L2_PIX_FMT_NV61``
2. 新增了相机控制功能 ``V4L2_CID_ZOOM_ABSOLUTE``、``V4L2_CID_ZOOM_RELATIVE``、``V4L2_CID_ZOOM_CONTINUOUS`` 和 ``V4L2_CID_PRIVACY``

V4L2在Linux 2.6.32中的更新
====================

1. 新增了控制标志 ``V4L2_CTRL_FLAG_WRITE_ONLY``
2. 新增了控制功能 ``V4L2_CID_COLORFX``

为了便于比较V4L2 API和内核版本，现在V4L2 API使用Linux内核版本编号进行编号。
- 完成了RDS捕获API。更多信息请参见 :ref:`rds`
- 新增了调制器和RDS编码器的新功能
- 添加了libv4l API的描述
- 通过新增类型 ``V4L2_CTRL_TYPE_STRING`` 支持字符串控制
- 添加了 ``V4L2_CID_BAND_STOP_FILTER`` 的文档说明
7. 增加了 FM 调制器（FM TX）扩展控制类：
   ``V4L2_CTRL_CLASS_FM_TX`` 及其控制 ID
8. 增加了 FM 接收器（FM RX）扩展控制类：
   ``V4L2_CTRL_CLASS_FM_RX`` 及其控制 ID
9. 增加了遥控器章节，描述了媒体设备的默认遥控器映射

V4L2 在 Linux 2.6.33 中的变化
====================
1. 增加了对数字视频时序的支持，以支持 HDTV 接收器和发射器

V4L2 在 Linux 2.6.34 中的变化
====================
1. 在 :ref:`相机控制类 <camera-controls>` 中增加了 ``V4L2_CID_IRIS_ABSOLUTE`` 和 ``V4L2_CID_IRIS_RELATIVE`` 控制

V4L2 在 Linux 2.6.37 中的变化
====================
1. 移除了 vtx（视频文本/电传视讯）API。该 API 已不再使用，并且没有硬件可以验证此 API。也没有发现任何用户空间应用程序使用它。原本计划在 2.6.35 版本中移除

V4L2 在 Linux 2.6.39 中的变化
====================
1. 移除了旧的 VIDIOC_*_OLD 符号和 V4L1 支持
2. 增加了多平面 API。不会影响当前驱动程序和应用程序的兼容性。详情请参阅 :ref:`多平面 API <planar-apis>`

V4L2 在 Linux 3.1 中的变化
=================
1. VIDIOC_QUERYCAP 现在返回的是每个子系统的版本而不是每个驱动程序的版本
标准化一个无效 ioctl 的错误代码
添加了 V4L2_CTRL_TYPE_BITMASK

Linux 3.2 中的 V4L2
==================

1. 添加了 V4L2_CTRL_FLAG_VOLATILE 以向用户空间指示易失性控制。
2. 添加选择 API 以增强对裁剪和组合的控制。
   不影响当前驱动程序和应用程序的兼容性。详情请参阅 :ref:`选择 API <selection-api>`。

Linux 3.3 中的 V4L2
==================

1. 在 :ref:`用户控制类 <control>` 中添加了 ``V4L2_CID_ALPHA_COMPONENT`` 控制项。
2. 在 `struct v4l2_capabilities` 中添加了 `device_caps` 字段，并添加了新的 `V4L2_CAP_DEVICE_CAPS` 功能。

Linux 3.4 中的 V4L2
==================

1. 添加了 :ref:`JPEG 压缩控制类 <jpeg-controls>`。
2. 扩展了 DV 时序 API：
   :ref:`VIDIOC_ENUM_DV_TIMINGS`、
   :ref:`VIDIOC_QUERY_DV_TIMINGS` 和
   :ref:`VIDIOC_DV_TIMINGS_CAP`。

Linux 3.5 中的 V4L2
==================

1. 添加了整数菜单，新类型将是 V4L2_CTRL_TYPE_INTEGER_MENU。
2. 为 V4L2 子设备接口添加了选择 API：
   :ref:`VIDIOC_SUBDEV_G_SELECTION` 和
   :ref:`VIDIOC_SUBDEV_S_SELECTION <VIDIOC_SUBDEV_G_SELECTION>`。
3. 向 `V4L2_CID_COLORFX` 控制中添加了 `V4L2_COLORFX_ANTIQUE`、`V4L2_COLORFX_ART_FREEZE`、`V4L2_COLORFX_AQUA`、`V4L2_COLORFX_SILHOUETTE`、`V4L2_COLORFX_SOLARIZATION`、`V4L2_COLORFX_VIVID` 和 `V4L2_COLORFX_ARBITRARY_CBCR` 菜单项。
4. 添加了 `V4L2_CID_COLORFX_CBCR` 控制。
5. 添加了相机控制项：`V4L2_CID_AUTO_EXPOSURE_BIAS`、`V4L2_CID_AUTO_N_PRESET_WHITE_BALANCE`、`V4L2_CID_IMAGE_STABILIZATION`、`V4L2_CID_ISO_SENSITIVITY`、`V4L2_CID_ISO_SENSITIVITY_AUTO`、`V4L2_CID_EXPOSURE_METERING`、`V4L2_CID_SCENE_MODE`、`V4L2_CID_3A_LOCK`、`V4L2_CID_AUTO_FOCUS_START`、`V4L2_CID_AUTO_FOCUS_STOP`、`V4L2_CID_AUTO_FOCUS_STATUS` 和 `V4L2_CID_AUTO_FOCUS_RANGE`。

Linux 3.6 中的 V4L2
==================

1. 将 struct v4l2_buffer 中的 `input` 替换为 `reserved2` 并移除了 `V4L2_BUF_FLAG_INPUT` 标志。
2. 添加了 `V4L2_CAP_VIDEO_M2M` 和 `V4L2_CAP_VIDEO_M2M_MPLANE` 能力。
3. 添加了频率带枚举的支持：参见 :ref:`VIDIOC_ENUM_FREQ_BANDS`。

Linux 3.9 中的 V4L2
==================

1. 在 struct v4l2_buffer 的 `flags` 字段中添加了时间戳类型。参见 :ref:`buffer-flags`。
2. 添加了 `V4L2_EVENT_CTRL_CH_RANGE` 控制事件变化标志。参见 :ref:`ctrl-changes-flags`。

Linux 3.10 中的 V4L2
==================

1. 移除了过时且未使用的 DV_PRESET ioctl：VIDIOC_G_DV_PRESET、VIDIOC_S_DV_PRESET、VIDIOC_QUERY_DV_PRESET 和 VIDIOC_ENUM_DV_PRESET。移除了相关的 v4l2_input/output 能力标志 V4L2_IN_CAP_PRESETS 和 V4L2_OUT_CAP_PRESETS。
2. 添加了新的调试 ioctl：:ref:`VIDIOC_DBG_G_CHIP_INFO`。
V4L2 在 Linux 3.11 中的更新
==================

1. 移除了过时的 ``VIDIOC_DBG_G_CHIP_IDENT`` ioctl

V4L2 在 Linux 3.14 中的更新
==================

1. 在结构体 `v4l2_rect` 中，`width` 和 `height` 字段的类型从 `_s32` 更改为 `_u32`

V4L2 在 Linux 3.15 中的更新
==================

1. 添加了软件定义无线电（SDR）接口

V4L2 在 Linux 3.16 中的更新
==================

1. 添加了事件 `V4L2_EVENT_SOURCE_CHANGE`

V4L2 在 Linux 3.17 中的更新
==================

1. 扩展了 `struct v4l2_pix_format`。添加了格式标志
2. 添加了复合控制类型和 :ref:`VIDIOC_QUERY_EXT_CTRL <VIDIOC_QUERYCTRL>`

V4L2 在 Linux 3.18 中的更新
==================

1. 添加了相机控制 `V4L2_CID_PAN_SPEED` 和 `V4L2_CID_TILT_SPEED`

V4L2 在 Linux 3.19 中的更新
==================

1. 重写了色彩空间章节，添加了新的枚举 `v4l2_ycbcr_encoding` 和 `v4l2_quantization` 字段到 `struct v4l2_pix_format`、`struct v4l2_pix_format_mplane` 和 `struct v4l2_mbus_framefmt`

V4L2 在 Linux 4.4 中的更新
==================

1. 将 `V4L2_TUNER_ADC` 重命名为 `V4L2_TUNER_SDR`。现在使用 `V4L2_TUNER_ADC` 已被弃用
2. 添加了 RF 调谐器控制 `V4L2_CID_RF_TUNER_RF_GAIN`
