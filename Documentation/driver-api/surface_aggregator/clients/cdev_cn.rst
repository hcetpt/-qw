将以下内容翻译为中文：

SPDX 许可证标识符：GPL-2.0+

.. |ssam_cdev_request| replace:: :c:type:`struct ssam_cdev_request <ssam_cdev_request>`
.. |ssam_cdev_request_flags| replace:: :c:type:`enum ssam_cdev_request_flags <ssam_cdev_request_flags>`
.. |ssam_cdev_event| replace:: :c:type:`struct ssam_cdev_event <ssam_cdev_event>`

==============================
用户空间 EC 接口（cdev）
==============================

`surface_aggregator_cdev` 模块提供了一个杂项设备，用于 SSAM 控制器，允许用户空间与 SAM EC 建立（或多或少）直接连接。该模块主要用于开发和调试目的，因此不应用于或依赖于其他任何用途。请注意，此模块不会自动加载，而是需要手动加载。
所提供的接口可以通过 `/dev/surface/aggregator` 设备文件访问。此接口的所有功能均通过 IOCTL 实现。
这些 IOCTL 和其相应的输入/输出参数结构定义在 `include/uapi/linux/surface_aggregator/cdev.h` 中。
一个小型 Python 库及其脚本用于访问此接口，可在 https://github.com/linux-surface/surface-aggregator-module/tree/master/scripts/ssam 找到。

接收事件
=================

可通过从设备文件读取来接收事件。事件由 |ssam_cdev_event| 数据类型表示。
但在可以读取事件之前，必须通过 `SSAM_CDEV_NOTIF_REGISTER` IOCTL 注册所需的监听器。监听器本质上是回调函数，在 EC 发送事件时被调用。在此接口中，它们与特定的目标类别和设备文件实例相关联。
它们将此类别的任何事件转发到对应实例的缓冲区，然后可以从该缓冲区读取这些事件。
监听器本身并不会在 EC 上启用事件。因此，可能还需要通过 `SSAM_CDEV_EVENT_ENABLE` IOCTL 启用事件。监听器按客户端（即每个设备文件实例）工作，而事件则是全局启用的，适用于 EC 及其所有客户端（无论是在用户空间还是非用户空间）。`SSAM_CDEV_EVENT_ENABLE` 和 `SSAM_CDEV_EVENT_DISABLE` IOCTL 会处理事件引用计数，以确保只要有一个客户端请求了某个事件，该事件就会保持启用状态。
请注意，一旦客户端实例关闭，已启用的事件并不会自动禁用。因此，任何客户端进程（或进程组）都应平衡其启用事件的调用与相应的禁用事件调用。然而，在不同的客户端实例上启用和禁用事件是完全合理的。例如，可以在客户端实例 `A` 上设置监听器并读取事件，在实例 `B` 上启用这些事件（注意这些事件也会被 `A` 接收，因为事件是全局启用/禁用的），并且在不再需要事件时，通过实例 `C` 禁用之前启用的事件。

控制器 IOCTL
=================

提供了以下 IOCTL：

.. flat-table:: 控制器 IOCTL
   :widths: 1 1 1 1 4
   :header-rows: 1

   * - 类型
     - 编号
     - 方向
     - 名称
     - 描述

   * - ``0xA5``
     - ``1``
     - ``写入``
     - ``REQUEST``
     - 执行同步 SAM 请求
* - ``0xA5``
     - ``2``
     - ``W``
     - ``NOTIF_REGISTER``
     - 注册事件通知器
* - ``0xA5``
     - ``3``
     - ``W``
     - ``NOTIF_UNREGISTER``
     - 取消注册事件通知器
* - ``0xA5``
     - ``4``
     - ``W``
     - ``EVENT_ENABLE``
     - 启用事件源
* - ``0xA5``
     - ``5``
     - ``W``
     - ``EVENT_DISABLE``
     - 禁用事件源

``SSAM_CDEV_REQUEST``
---------------------

定义为 ``_IOWR(0xA5, 1, struct ssam_cdev_request)``
执行一个同步的SAM请求。请求规范作为类型为 |ssam_cdev_request| 的参数传递，然后由IOCTL写入/修改以返回请求的状态和结果。
请求的有效载荷数据必须单独分配，并通过成员 ``payload.data`` 和 ``payload.length`` 传递。如果需要响应，则响应缓冲区必须由调用者分配并通过成员 ``response.data`` 传递。成员 ``response.length`` 必须设置为此缓冲区的容量，或者如果没有响应要求，则设置为零。在请求完成后，如果响应缓冲区的容量允许，该调用会将响应写入到响应缓冲区，并覆盖长度字段以实际的响应大小（以字节为单位）。

另外，如果请求有响应，则必须通过请求标志来指示这一点，就像内核中的请求一样处理。请求标志可以通过成员 ``flags`` 设置，其值对应于 |ssam_cdev_request_flags| 中的值。
最后，请求自身的状态会在成员 ``status`` 中返回（一个负的errno值表示失败）。需要注意的是，IOCTL的失败指示与请求的失败指示是分开的：如果在设置请求时发生任何失败（如 ``-EFAULT``），或者提供的参数或其任何字段无效（如 ``-EINVAL``），IOCTL将返回负状态码。在这种情况下，请求参数的状态值可能会被设置，提供更详细的出错信息（例如 ``-ENOMEM`` 表示内存不足），但此值也可能为零。如果请求已经成功地在IOCTL内部设置、提交并完成（即已返回给用户空间），则IOCTL将以零状态码返回，但如果实际执行请求后失败，请求的 ``status`` 成员仍然可能是负数。
下面是`argument struct`的完整定义：

``SSAM_CDEV_NOTIF_REGISTER``  
--------------------------------
定义为``_IOW(0xA5, 2, struct ssam_cdev_notifier_desc)``  
使用指定的优先级，根据给定的通知器描述中指定的目标类别注册一个通知器。注册通知器是接收事件所必需的，但本身并不启用事件。在为特定目标类别注册了一个通知器之后，该类别的所有事件都将被转发到用户空间客户端，并且可以从设备文件实例中读取这些事件。请注意，可能需要启用事件（例如通过``SSAM_CDEV_EVENT_ENABLE`` IOCTL），EC才会发送它们。
每个目标类别和客户端实例只能注册一个通知器。如果已经注册了通知器，则此IOCTL将因``-EEXIST``而失败。
当设备文件实例关闭时，通知器会自动移除。

``SSAM_CDEV_NOTIF_UNREGISTER``  
---------------------------------
定义为``_IOW(0xA5, 3, struct ssam_cdev_notifier_desc)``  
取消注册与指定目标类别相关联的通知器。此IOCTL将忽略优先级字段。如果没有为该客户端实例和给定类别注册通知器，则此IOCTL将以``-ENOENT``失败。

``SSAM_CDEV_EVENT_ENABLE``  
------------------------------
定义为``_IOW(0xA5, 4, struct ssam_cdev_event_desc)``  
启用与给定事件描述符相关的事件。
请注意，此调用本身不会注册通知器，它仅会在控制器上启用事件。如果你想通过从设备文件中读取来接收事件，则需要在该实例上注册相应的通知器。
事件在关闭设备文件时并不会自动禁用。这必须通过手动调用 `SSAM_CDEV_EVENT_DISABLE` IOCTL 来完成。

`SSAM_CDEV_EVENT_DISABLE`

定义为 `_IOW(0xA5, 5, struct ssam_cdev_event_desc)`  
禁用与给定事件描述符相关联的事件。
请注意，这不会取消注册任何通知器。调用此函数后，事件仍可能被接收并转发到用户空间。阻止接收事件的唯一安全方法是取消注册所有先前已注册的通知器。

结构体和枚举
=============

.. kernel-doc:: include/uapi/linux/surface_aggregator/cdev.h
