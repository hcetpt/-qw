SPDX 许可证标识符: GPL-2.0

高级 CI API
===========

.. note::

   本文档已过时

本文档描述了根据 Linux DVB API 的高级 CI API。通过高级 CI 方案，几乎任何架构的新卡都可以用这种方式实现，开关语句内的定义可以轻松适应任何卡，从而无需添加任何额外的 ioctl。

缺点是驱动程序/硬件需要管理其余部分。对于应用程序开发人员而言，这就像发送/接收 CI ioctl 定义的数组一样简单，这些定义在 Linux DVB API 中有详细说明。API 没有任何更改来适应此功能。

为什么需要另一个 CI 接口？
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

这是最常见的问题之一。一个不错的问题。

严格来说，这不是一个新的接口。

CI 接口在 DVB API 的 ca.h 文件中定义如下：

.. code-block:: c

    typedef struct ca_slot_info {
        int num;               /* 插槽编号 */

        int type;              /* 此插槽支持的 CI 接口类型 */
        #define CA_CI            1     /* 高级 CI 接口 */
        #define CA_CI_LINK       2     /* CI 链路层接口 */
        #define CA_CI_PHYS       4     /* CI 物理层接口 */
        #define CA_DESCR         8     /* 内置解扰器 */
        #define CA_SC          128     /* 简单智能卡接口 */

        unsigned int flags;
        #define CA_CI_MODULE_PRESENT 1 /* 模块（或卡片）插入 */
        #define CA_CI_MODULE_READY   2
    } ca_slot_info_t;

这个 CI 接口遵循的是高级 CI 接口，但大多数应用程序并未实现。因此重新审视这一领域。

该 CI 接口的不同之处在于它试图容纳所有其他基于 CI 的设备，这些设备属于其他类别。这意味着此 CI 接口仅在应用层处理 EN50221 样式的标签，并且应用程序不负责会话管理。驱动程序/硬件将负责这一切。

此接口纯粹是一个 EN50221 接口，用于交换 APDU。这意味着在此应用程序与驱动程序之间的通信中不存在会话管理、链路层或传输层。就是这么简单。驱动程序/硬件需要处理这些问题。
通过这个高级CI接口，接口可以通过常规的ioctl定义。所有这些ioctl也适用于高级CI接口。

```c
#define CA_RESET          _IO('o', 128)
#define CA_GET_CAP        _IOR('o', 129, ca_caps_t)
#define CA_GET_SLOT_INFO  _IOR('o', 130, ca_slot_info_t)
#define CA_GET_DESCR_INFO _IOR('o', 131, ca_descr_info_t)
#define CA_GET_MSG        _IOR('o', 132, ca_msg_t)
#define CA_SEND_MSG       _IOW('o', 133, ca_msg_t)
#define CA_SET_DESCR      _IOW('o', 134, ca_descr_t)
```

查询设备时，设备返回如下信息：

```plaintext
CA_GET_SLOT_INFO
----------------------------
Command = [info]
APP: Number=[1]
APP: Type=[1]
APP: flags=[1]
APP: CI High level interface
APP: CA/CI Module Present

CA_GET_CAP
----------------------------
Command = [caps]
APP: Slots=[1]
APP: Type=[1]
APP: Descrambler keys=[16]
APP: Type=[1]

CA_SEND_MSG
----------------------------
Descriptors(Program Level)=[ 09 06 06 04 05 50 ff f1]
Found CA descriptor @ program level

(20) ES type=[2] ES pid=[201]  ES length =[0 (0x0)]
(25) ES type=[4] ES pid=[301]  ES length =[0 (0x0)]
ca_message length is 25 (0x19) bytes
EN50221 CA MSG=[ 9f 80 32 19 03 01 2d d1 f0 08 01 09 06 06 04 05 50 ff f1 02 e0 c9 00 00 04 e1 2d 00 00]
```

并非所有的ioctl在驱动程序中都实现了API，硬件中无法通过API实现的其他功能则使用`CA_GET_MSG`和`CA_SEND_MSG` ioctl来实现。使用EN50221风格的包装器来交换数据，以保持与其他硬件的兼容性。

```c
/* 来自或发送给CI-CAM的消息 */
typedef struct ca_msg {
    unsigned int index;
    unsigned int type;
    unsigned int length;
    unsigned char msg[256];
} ca_msg_t;
```

数据流可以描述为：

```plaintext
App (User)
-----
parse
  |
  |
  v
en50221 APDU (package)
--------------------------------------
|    |                | 高级CI驱动程序
|    |                |
|    v                |
| en50221 APDU (unpackage) |
|    |                |
|    |                |
|    v                |
| sanity checks       |
|    |                |
|    |                |
|    v                |
| do (H/W dep)        |
--------------------------------------
  |    硬件
  |
  v
```

高级CI接口采用了EN50221 DVB标准，遵循标准确保了未来的兼容性和可扩展性。
