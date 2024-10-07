SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _app-pri:

********************
应用程序优先级
********************

当多个应用程序共享一个设备时，可能需要为它们分配不同的优先级。与传统的“rm -rf /”思维模式相反，例如，视频录制应用程序可以阻止其他应用程序更改视频控制或切换当前的电视频道。另一个目标是允许后台运行的低优先级应用程序，这些应用程序可以被用户控制的应用程序抢占，并在稍后自动重新获得设备控制权。由于这些功能无法完全在用户空间实现，V4L2 定义了 :ref:`VIDIOC_G_PRIORITY <VIDIOC_G_PRIORITY>` 和 :ref:`VIDIOC_S_PRIORITY <VIDIOC_G_PRIORITY>` ioctl 来请求和查询与文件描述符相关的访问优先级。打开设备会分配一个中等优先级，这与早期版本的 V4L2 和不支持这些 ioctl 的驱动程序兼容。需要不同优先级的应用程序通常会在使用 :ref:`VIDIOC_QUERYCAP` ioctl 验证设备之后调用 :ref:`VIDIOC_S_PRIORITY <VIDIOC_G_PRIORITY>`。

更改驱动程序属性的 ioctl（如 :ref:`VIDIOC_S_INPUT <VIDIOC_G_INPUT>`）在另一个应用程序获得更高优先级后会返回一个 “EBUSY” 错误代码。
