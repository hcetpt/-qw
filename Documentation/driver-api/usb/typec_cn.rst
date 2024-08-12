USB Type-C 连接器类别
==========================

简介
------------

Type-C 类别旨在以统一的方式向用户空间描述系统中的 USB Type-C 端口。该类别设计仅提供用户空间接口实现，希望它可以在尽可能多的平台上使用。
平台需要通过此类别注册其所有的 USB Type-C 端口。通常情况下，此注册由 USB Type-C 或 PD PHY 驱动程序完成，但也可能是用于 UCSI 等固件接口的驱动程序、USB PD 控制器驱动程序，甚至是 Thunderbolt3 控制器驱动程序。本文档将注册 USB Type-C 端口到类别的组件视为“端口驱动程序”。
除了显示端口的能力外，当端口驱动程序能够支持这些功能时，该类别还为用户空间提供了对端口角色和交替模式的控制权，以及合作伙伴和电缆插头的控制权。
该类别为本文档中描述的端口驱动程序提供了一个 API。属性在 `Documentation/ABI/testing/sysfs-class-typec` 中描述。

用户空间接口
--------------------

每个端口都将作为 `/sys/class/typec/` 下的独立设备呈现。第一个端口将被命名为 "port0"，第二个端口为 "port1"，以此类推。
连接后，合作伙伴也将作为 `/sys/class/typec/` 下的独立设备呈现。合作伙伴设备的父级始终是它所连接的端口。连接到 "port0" 的合作伙伴将被命名为 "port0-partner"。设备的完整路径将是 `/sys/class/typec/port0/port0-partner/`。
电缆及其两端的插头也可以作为 `/sys/class/typec/` 下的独立设备可选地呈现。连接到 "port0" 的电缆将被命名为 "port0-cable"，而 SOP Prime 端（参见 USB 电源传输规范第 2.4 章）的插头将被命名为 "port0-plug0"，SOP Double Prime 端的插头则被命名为 "port0-plug1"。电缆的父级始终是端口，而电缆插头的父级始终是电缆。
如果端口、合作伙伴或电缆插头支持交替模式，则每个支持的交替模式 SVID 都会有自己的设备来描述它们。需要注意的是，交替模式设备不会附加到 typec 类别中。交替模式的父级将是支持它的设备，例如 "port0-partner" 的交替模式将呈现为 `/sys/class/typec/port0-partner/`。
每种受支持的模式在其交替模式设备下都有一个名为 "mode<index>" 的组，例如 `/sys/class/typec/port0/<alternate mode>/mode1/`。进入或退出模式的请求可以通过该组中的 "active" 属性文件进行。

驱动 API
----------

注册端口
~~~~~~~~~~~~~~~~~~~~~

端口驱动程序将使用 `struct typec_capability` 数据结构描述其控制的所有 Type-C 端口，并使用以下 API 进行注册：

.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_register_port typec_unregister_port

在注册端口时，`struct typec_capability` 中的 `prefer_role` 成员特别值得注意。如果正在注册的端口没有初始角色偏好，即端口默认不执行 Try.SNK 或 Try.SRC，则 `prefer_role` 成员必须具有值 `TYPEC_NO_PREFERRED_ROLE`。
否则，如果端口默认执行Try.SNK操作，则成员必须具有值`TYPEC_DEVICE`；而当执行Try.SRC时，该值必须为`TYPEC_HOST`。

注册合作伙伴
~~~~~~~~~~~~~~

成功连接一个合作伙伴后，端口驱动程序需要将合作伙伴向类别注册。关于合作伙伴的详细信息需要在`struct typec_partner_desc`结构体中描述。类别会在注册期间复制这些详细信息。类别提供了以下API来注册和注销合作伙伴：
.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_register_partner typec_unregister_partner

如果注册成功，类别会提供指向`struct typec_partner`的句柄；否则返回NULL。
如果合作伙伴支持USB电力传输（Power Delivery），并且端口驱动程序能够展示“Discover Identity”命令的结果，那么合作伙伴描述符结构应包含指向`struct usb_pd_identity`实例的句柄。类别随后会在合作伙伴设备下为身份创建一个sysfs目录。“Discover Identity”命令的结果可以通过以下API报告：

.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_partner_set_identity

注册线缆
~~~~~~~~~~

成功连接一条支持USB电力传输“Discover Identity”的线缆后，端口驱动程序需要注册该线缆及其一到两个插头，具体取决于线缆中是否存在CC Double Prime控制器。因此，仅支持SOP Prime通信但不支持SOP Double Prime通信的线缆应该只注册一个插头。更多关于SOP通信的信息，请参阅最新的USB电力传输规范。
插头作为独立设备表示。首先注册线缆，然后注册线缆插头。线缆将是插头的父设备。线缆的详细信息需要在`struct typec_cable_desc`结构体中描述，而插头的详细信息则需要在`struct typec_plug_desc`结构体中描述。类别会在注册期间复制这些详细信息。类别提供了以下API来注册和注销线缆及其插头：

.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_register_cable typec_unregister_cable typec_register_plug typec_unregister_plug

如果注册成功，类别会提供指向`struct typec_cable`和`struct typec_plug`的句柄；否则返回NULL。
如果线缆支持USB电力传输，并且端口驱动程序能够展示“Discover Identity”命令的结果，那么线缆描述符结构应包含指向`struct usb_pd_identity`实例的句柄。类别随后会在线缆设备下为身份创建一个sysfs目录。“Discover Identity”命令的结果可以通过以下API报告：

.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_cable_set_identity

通知
~~~~~

当合作伙伴执行了角色更改或在连接合作伙伴或线缆时默认角色发生更改时，端口驱动程序必须使用以下API向类别报告：
.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_set_data_role typec_set_pwr_role typec_set_vconn_role typec_set_pwr_opmode

备用模式
~~~~~~~~~

USB Type-C端口、合作伙伴以及线缆插头可能支持备用模式。每个备用模式都有一个标识符称为SVID，它可能是由USB-IF分配的标准ID或厂商ID，并且每个支持的SVID可以有1到6个模式。类别提供了`struct typec_mode_desc`用于描述SVID的单个模式，以及`struct typec_altmode_desc`用作所有支持模式的容器。
支持备用模式的端口需要使用以下API注册它们支持的每个SVID：

.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_port_register_altmode

如果合作伙伴或线缆插头作为对USB电力传输结构化VDM“Discover SVIDs”消息的响应提供了一系列SVID列表，那么每个SVID都需要被注册。
合作伙伴的API：

.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_partner_register_altmode

线缆插头的API：

.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_plug_register_altmode

因此，端口、合作伙伴和线缆插头都会使用它们自己的函数来注册备用模式，但是注册总是会在成功时返回指向`struct typec_altmode`的句柄，失败时返回NULL。注销也将通过同一个函数进行：

.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_unregister_altmode

如果合作伙伴或线缆插头进入或退出模式，端口驱动程序需要使用以下API通知类别：

.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_altmode_update_active

多路复用器/解多路复用器开关
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

USB Type-C连接器后面可能有一个或多个多路复用器/解多路复用器开关。由于插头可以正反面插入，因此需要一个开关来将正确的数据对从连接器路由到USB控制器。如果支持备用或配件模式，则需要另一个开关来将连接器上的引脚路由到除USB之外的其他组件。USB Type-C连接器类别为此提供了API。
.. kernel-doc:: drivers/usb/typec/mux.c
   :functions: typec_switch_register typec_switch_unregister typec_mux_register typec_mux_unregister

在大多数情况下，同一个物理多路复用器将同时处理方向和模式。
然而，因为端口驱动程序负责方向，而备用模式驱动程序负责模式，所以两者总是被分离成它们各自的逻辑组件：“mux”用于模式，“switch”用于方向。
当一个端口被注册时，USB Type-C 连接器类别会请求该端口的多路复用器(mux)和开关。驱动程序随后可以使用以下API来控制它们：

.. kernel-doc:: drivers/usb/typec/class.c
   :functions: typec_set_orientation typec_set_mode

如果连接器支持双角色功能，则也可能存在数据角色的开关。USB Type-C 连接器类别并未为此提供单独的API。端口驱动程序可以使用USB角色类别API与这些开关配合工作。
下面是一个示意图，展示了支持交替模式的连接器后面的多路复用器：

                     ------------------------
                     |       Connector      |
                     ------------------------
                            |         |
                     ------------------------
                      \     Orientation    /
                       --------------------
                                |
                       --------------------
                      /        Mode        \
                     ------------------------
                         /              \
      ------------------------        --------------------
      |       Alt Mode       |       /      USB Role      \
      ------------------------      ------------------------
                                         /            \
                     ------------------------      ------------------------
                     |       USB Host       |      |       USB Device     |
                     ------------------------      ------------------------
