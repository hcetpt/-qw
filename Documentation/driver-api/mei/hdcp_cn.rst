SPDX 许可证标识符: GPL-2.0

HDCP:
=====

管理引擎固件（ME FW）作为安全引擎提供了设置 Intel 图形设备与 HDCP 2.2 接收器之间 HDCP 2.2 协议协商的能力。
ME FW 准备 HDCP 2.2 协商参数，并根据 HDCP 2.2 规范对这些参数进行签名和加密。Intel 图形设备将创建的数据包发送给 HDCP 2.2 接收器。
同样，HDCP 2.2 接收器的响应被传递给 ME FW 进行解密和验证。
一旦 HDCP 2.2 协商的所有步骤完成，在请求时，ME FW 将配置端口为已认证，并向 Intel 图形硬件提供 HDCP 加密密钥。

mei_hdcp 驱动
---------------
.. kernel-doc:: drivers/misc/mei/hdcp/mei_hdcp.c
    :doc: MEI_HDCP 客户端驱动

mei_hdcp API
------------

.. kernel-doc:: drivers/misc/mei/hdcp/mei_hdcp.c
    :functions:
