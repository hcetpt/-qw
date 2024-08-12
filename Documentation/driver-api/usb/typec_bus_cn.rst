USB Type-C 替代模式驱动程序的 API
=========================================

简介
------------

替代模式需要使用 USB Type-C 和 USB 电源传输规范中定义的供应商自定义消息 (VDM) 与合作伙伴进行通信。通信是 SVID（标准或供应商 ID）特定的，即针对每种替代模式都是特定的，因此每种替代模式都需要一个定制的驱动程序。USB Type-C 总线允许通过使用 SVID 和模式编号将驱动程序绑定到已发现的合作伙伴替代模式。
:ref:`USB Type-C 连接器类 <typec>` 为端口支持的每个替代模式提供一个设备，并为合作伙伴支持的每个替代模式提供单独的设备。替代模式的驱动程序绑定到合作伙伴的替代模式设备上，而端口的替代模式设备必须由端口驱动程序处理。
当注册一个新的合作伙伴替代模式设备时，它会链接到该合作伙伴所连接的端口的替代模式设备，该设备具有匹配的 SVID 和模式。端口驱动程序和替代模式驱动程序之间的通信将使用相同的 API。
端口的替代模式设备作为合作伙伴和替代模式驱动程序之间的代理，因此端口驱动程序仅需将来自替代模式驱动程序的 SVID 特定命令传递给合作伙伴，以及从合作伙伴传递给替代模式驱动程序。端口驱动程序不需要直接进行 SVID 特定通信，但它们需要为端口的替代模式设备提供操作回调，就像替代模式驱动程序需要为合作伙伴的替代模式设备提供这些回调一样。

使用方法：
------

通用
~~~~~~~

默认情况下，替代模式驱动程序负责进入该模式。
也可以将是否进入模式的决策留给用户空间（参见 Documentation/ABI/testing/sysfs-class-typec）。端口驱动程序不应自行进入任何模式。
`->vdm` 是操作回调向量中最重要的一项回调。它将用于在合作伙伴与替代模式驱动程序之间传送所有 SVID 特定命令，对于端口驱动程序来说也是双向的。驱动程序使用 :c:func:`typec_altmode_vdm()` 向彼此发送 SVID 特定命令。
如果使用 SVID 特定命令与合作伙伴通信导致需要重新配置连接器上的引脚，则替代模式驱动程序需要使用 :c:func:`typec_altmode_notify()` 通知总线。驱动程序将协商得出的 SVID 特定引脚配置值作为参数传递给该函数。然后，总线驱动程序将使用该值作为复用器的状态值来配置连接器后面的复用器。
注释：SVID 特定的引脚配置值必须始终从 `TYPEC_STATE_MODAL` 开始。
USB Type-C 规范为连接器定义了两种默认状态：`TYPEC_STATE_USB` 和 `TYPEC_STATE_SAFE`。这些值被总线保留为状态的第一个可能值。当进入替代模式时，根据 USB Type-C 规范定义，总线会将连接器置于 `TYPEC_STATE_SAFE` 状态，然后发送 Enter 或 Exit 模式命令，并且在退出模式后将连接器重新置于 `TYPEC_STATE_USB` 状态。

SVID 特定引脚配置的工作定义示例如下：

    枚举 {
        ALTMODEX_CONF_A = TYPEC_STATE_MODAL,
        ALTMODEX_CONF_B,
        ..
    };

辅助宏 `TYPEC_MODAL_STATE()` 也可以使用：

    #define ALTMODEX_CONF_A = TYPEC_MODAL_STATE(0);
    #define ALTMODEX_CONF_B = TYPEC_MODAL_STATE(1);

电缆插头替代模式
~~~~~~~~~~~~~~~~~~~~~~~~~~

替代模式驱动程序不绑定到电缆插头替代模式设备，而是绑定到合作伙伴替代模式设备。如果替代模式支持或需要响应 SOP Prime 的电缆（可选地响应 SOP Double Prime 消息），那么该替代模式的驱动程序必须使用 `typec_altmode_get_plug()` 请求电缆插头替代模式的句柄，并接管其控制。

驱动程序 API
--------------

替代模式结构体
~~~~~~~~~~~~~~~~~~~~~~

.. kernel-doc:: include/linux/usb/typec_altmode.h
   :functions: typec_altmode_driver typec_altmode_ops

注册/注销替代模式驱动程序
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. kernel-doc:: include/linux/usb/typec_altmode.h
   :functions: typec_altmode_register_driver typec_altmode_unregister_driver

替代模式驱动程序操作
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. kernel-doc:: drivers/usb/typec/bus.c
   :functions: typec_altmode_enter typec_altmode_exit typec_altmode_attention typec_altmode_vdm typec_altmode_notify

端口驱动程序的 API
~~~~~~~~~~~~~~~~~~~~~~~~

.. kernel-doc:: drivers/usb/typec/bus.c
   :functions: typec_match_altmode

电缆插头操作
~~~~~~~~~~~~~~~~~~~~~

.. kernel-doc:: drivers/usb/typec/bus.c
   :functions: typec_altmode_get_plug typec_altmode_put_plug
