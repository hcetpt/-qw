.. SPDX 许可证标识符: GPL-2.0

.. _GPIO_GET_LINEHANDLE_IOCTL:

*************************
GPIO_GET_LINEHANDLE_IOCTL
*************************

.. warning::
    此 ioctl 是 chardev_v1.rst 的一部分，并已被 gpio-v2-get-line-ioctl.rst 废弃。
名称
====

GPIO_GET_LINEHANDLE_IOCTL - 从内核请求一个或多个线
概要
========

.. c:macro:: GPIO_GET_LINEHANDLE_IOCTL

``int ioctl(int chip_fd, GPIO_GET_LINEHANDLE_IOCTL, struct gpiohandle_request *request)``

参数
=========

``chip_fd``
    由 `open()` 返回的 GPIO 字符设备文件描述符
``request``
    :c:type:`handle_request<gpiohandle_request>`，用于指定要请求的线及其配置
描述
===========

从内核请求一个或多个线
虽然可以请求多个线，但同一配置适用于请求中的所有线
成功时，请求进程将获得对线值的独占访问权以及对线配置的写访问权
线的状态（包括输出线的值）保证在返回的文件描述符关闭前保持不变。一旦文件描述符被关闭，从用户空间的角度来看，线的状态将变得不受控制，并可能恢复到其默认状态
请求一个正在使用的线会导致错误（**EBUSY**）
关闭 ``chip_fd`` 对现有的线句柄没有影响
### 配置规则

以下配置规则适用：

- 方向标志 `GPIOHANDLE_REQUEST_INPUT` 和 `GPIOHANDLE_REQUEST_OUTPUT` 不能同时使用。如果两者都没有设置，则唯一可以设置的标志是 `GPIOHANDLE_REQUEST_ACTIVE_LOW`，线路将以“原样”请求，以便在不改变电气配置的情况下读取线路值。
- 驱动标志 `GPIOHANDLE_REQUEST_OPEN_xxx` 要求 `GPIOHANDLE_REQUEST_OUTPUT` 必须被设置。
- 只能设置一个驱动标志。
- 如果没有设置任何驱动标志，则假设为推挽（push-pull）模式。
- 只能设置一个偏置标志 `GPIOHANDLE_REQUEST_BIAS_xxx`，并且需要同时设置方向标志。
- 如果没有设置任何偏置标志，则偏置配置不会改变。
- 请求无效配置将导致错误（`EINVAL`）。

### 配置支持

当请求的配置无法直接由底层硬件和驱动程序支持时，内核会采取以下方法之一：

- 拒绝请求
- 在软件中模拟该功能
- 将该功能视为尽力而为（best effort）

所采取的方法取决于该功能是否可以在软件中合理地模拟，以及如果不支持该功能对硬件和用户空间的影响。对于每个功能的具体处理方法如下：

| 功能    | 方法         |
|---------|--------------|
| 偏置    | 尽力而为      |
| 方向    | 拒绝         |
| 驱动    | 模拟         |

偏置被视为尽力而为，以允许用户空间在支持内部偏置的平台上应用相同的配置，就像那些需要外部偏置的平台一样。最坏的情况是线路漂浮而不是按预期进行偏置。
驱动是通过在线路不应被驱动时将其切换为输入来模拟的。
在所有情况下，`gpio-get-lineinfo-ioctl.rst` 报告的配置是请求的配置，而不是实际的硬件配置。
用户空间无法确定某个功能是否在硬件中受支持、是否被模拟或是否尽力而为。

返回值
======
成功时返回 0，并且 `request.fd<gpiohandle_request>` 包含请求的文件描述符。
出错时返回 -1，并且 `errno` 变量会被适当设置。
常见的错误代码在 `error-codes.rst` 中有描述。
