SPDX 许可证标识符: GPL-2.0

Linux USB 视频类（UVC）驱动程序
======================================

此文件记录了 UVC 驱动程序的一些特定内容，例如驱动程序特定的 ioctl 和实现说明。问题和意见可以发送到 Linux UVC 开发邮件列表：linux-media@vger.kernel.org

扩展单元（XU）支持
---------------------------

简介
~~~~~~~~~~~~

UVC 规范允许通过扩展单元（XUs）实现供应商特定的扩展。Linux UVC 驱动程序通过两种独立的机制支持扩展单元控制（XU 控制）：

  - 通过将 XU 控制映射到 V4L2 控制
  - 通过一个驱动程序特定的 ioctl 接口

第一种机制通过将某些 XU 控制映射到 V4L2 控制，使得通用的 V4L2 应用程序能够使用 XU 控制，这些控制会在常规控制枚举期间显示出来。
第二种机制要求应用程序具备 uvcvideo 特定的知识才能访问 XU 控制，但它将整个 UVC XU 概念暴露给用户空间以提供最大的灵活性。
这两种机制互为补充，并在下面详细描述。

控制映射
~~~~~~~~~~~~~~~~

UVC 驱动程序提供了一个 API，供用户空间应用程序在运行时定义所谓的控制映射。这些映射允许单独的 XU 控制或其字节范围映射到新的 V4L2 控制。这样的控制看起来和正常工作的 V4L2 控制完全一样（即标准控制，如亮度、对比度等）。然而，读取或写入此类 V4L2 控制会触发关联的 XU 控制的读取或写入。

用于创建这些控制映射的 ioctl 被称为 UVCIOC_CTRL_MAP。
早期版本的驱动程序（0.2.0 之前）需要使用另一个 ioctl（UVCIOC_CTRL_ADD）来传递 XU 控制信息给 UVC 驱动程序。
这在新版本的 uvcvideo 中已不再必要，因为新版本直接从设备查询信息。
关于 UVCIOC_CTRL_MAP ioctl 的详细信息，请参阅下面标题为 "ioctl 参考" 的部分。
3. 驱动特定的XU控制接口

对于需要直接访问XU控制的应用程序（例如用于测试目的、固件上传或访问二进制控制），提供了一种驱动特定的ioctl机制，即UVCIOC_CTRL_QUERY。
调用此ioctl允许应用程序向UVC驱动发送查询，这些查询直接映射到低级别的UVC控制请求。
为了发出此类请求，需要知道控制扩展单元的UVC单元ID和控制选择器。这些信息要么硬编码在应用程序中，要么通过其他方式获取，例如解析UVC描述符，或者如果可用的话，使用媒体控制器API来枚举设备的实体。
除非已经知道控制大小，否则首先需要发出UVC_GET_LEN请求以分配足够大的缓冲区，并将缓冲区大小设置为正确的值。同样地，要确定UVC_GET_CUR或UVC_SET_CUR是否是针对某个控制的有效请求，应该发出UVC_GET_INFO请求。结果字节的第0位（支持GET）和第1位（支持SET）表明哪些请求是有效的。
随着UVCIOC_CTRL_QUERY ioctl的添加，UVCIOC_CTRL_GET和UVCIOC_CTRL_SET ioctl已变得过时，因为它们的功能是前者的子集。目前它们仍然被支持，但建议应用程序开发者改用UVCIOC_CTRL_QUERY。
有关UVCIOC_CTRL_QUERY ioctl的详细信息，请参阅下面标题为“IOCTL参考”的部分。

安全性
~~~~~~~
当前API没有提供细粒度的访问控制设施。UVCIOC_CTRL_ADD和UVCIOC_CTRL_MAP ioctl需要超级用户权限。欢迎提出改进建议。

调试
~~~~~~~
为了调试与XU控制相关的问题或一般控制问题，建议启用模块参数'trace'中的UVC_TRACE_CONTROL位。这会导致额外的输出写入系统日志。
### UVCIOC_CTRL_MAP - 将 UVC 控制映射到 V4L2 控制
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

参数：struct uvc_xu_control_mapping

**描述**：

此 ioctl 创建一个 UVC 控制（或其部分）与 V4L2 控制之间的映射。一旦定义了这些映射，用户空间应用程序就可以通过 V4L2 控制 API 访问厂商定义的 UVC 控制。

为了创建一个映射，应用程序需要填充 `uvc_xu_control_mapping` 结构体，其中包含有关使用 UVCIOC_CTRL_ADD 定义的现有 UVC 控制和新的 V4L2 控制的信息。

一个 UVC 控制可以映射到多个 V4L2 控制。例如，一个 UVC 平移/倾斜控制可以分别映射到单独的平移和倾斜 V4L2 控制。UVC 控制通过使用 'size' 和 'offset' 字段划分为不重叠的部分，并独立地映射到 V4L2 控制。

对于有符号整数类型的 V4L2 控制，`data_type` 字段应设置为 `UVC_CTRL_DATA_TYPE_SIGNED`。其他值目前会被忽略。

**返回值**：

成功时返回 0，失败时返回 -1 并根据错误类型设置 errno。

- ENOMEM：操作所需内存不足。
- EPERM：权限不足（需要超级用户权限）。
- EINVAL：没有这样的 UVC 控制。
- EOVERFLOW：请求的偏移量和大小超过了 UVC 控制的范围。
- EEXIST：映射已存在。
**数据类型**：

.. code-block:: none

	* struct uvc_xu_control_mapping

	__u32	id		V4L2 控制标识符
	__u8	name[32]	V4L2 控制名称
	__u8	entity[16]	UVC 扩展单元 GUID
	__u8	selector	UVC 控制选择器
	__u8	size		V4L2 控制大小（位数）
	__u8	offset		V4L2 控制偏移量（位数）
	enum v4l2_ctrl_type
		v4l2_type	V4L2 控制类型
	enum uvc_control_data_type
		data_type	UVC 控制数据类型
	struct uvc_menu_info
		*menu_info	菜单项数组（仅用于菜单控制）
	__u32	menu_count	菜单项数量（仅用于菜单控制）

	* struct uvc_menu_info

	__u32	value		设备使用的菜单项值
	__u8	name[32]	菜单项名称

	* enum uvc_control_data_type

	UVC_CTRL_DATA_TYPE_RAW		原始控制（字节数组）
	UVC_CTRL_DATA_TYPE_SIGNED	带符号整数
	UVC_CTRL_DATA_TYPE_UNSIGNED	无符号整数
	UVC_CTRL_DATA_TYPE_BOOLEAN	布尔值
	UVC_CTRL_DATA_TYPE_ENUM		枚举
	UVC_CTRL_DATA_TYPE_BITMASK	位掩码

UVCIOC_CTRL_QUERY - 查询 UVC XU 控制
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
参数: struct uvc_xu_control_query

**描述**：

此 ioctl 操作查询由其扩展单元 ID 和控制选择器标识的 UVC XU 控制。
有许多不同的查询可用，这些查询与 UVC 规范中描述的低级控制请求紧密对应。这些请求包括：

UVC_GET_CUR
	获取当前控制值
UVC_GET_MIN
	获取最小控制值
UVC_GET_MAX
	获取最大控制值
UVC_GET_DEF
	获取默认控制值
UVC_GET_RES
	查询控制分辨率，即允许的控制值的步长
UVC_GET_LEN
	查询控制的字节大小
UVC_GET_INFO
	查询控制信息位图，指示是否支持 get/set 请求
UVC_SET_CUR
	更新控制值

应用程序必须将 'size' 字段设置为正确的控制长度。例外情况是 UVC_GET_LEN 和 UVC_GET_INFO 查询，对于这两种查询，大小必须分别设置为 2 和 1。'data' 字段必须指向一个有效的可写缓冲区，该缓冲区足够大以容纳指定数量的数据字节。
数据直接从设备复制，无需任何驱动程序端处理。应用程序负责数据缓冲区的格式化，包括小端字节序和大端字节序的转换。这一点对于 UVC_GET_LEN 请求的结果尤为重要，因为设备始终以小端字节序返回一个 16 位整数。

**返回值**：

- 成功时返回 0。
- 出错时返回 -1，并且设置适当的 errno。

- ENOENT：设备不支持给定的控制或无法找到指定的扩展单元。
- ENOBUFS：指定的缓冲区大小不正确（太大或太小）。
- EINVAL：传递了无效的请求代码。
- EBADRQC：给定的控制不支持给定的请求。
- EFAULT：数据指针引用了一个不可访问的内存区域。

**数据类型**：

.. code-block:: none

    * struct uvc_xu_control_query

    __u8	unit		扩展单元 ID
    __u8	selector	控制选择器
    __u8	query		发送到设备的请求代码
    __u16	size		控制数据大小（字节数）
    __u8	*data		控制值
