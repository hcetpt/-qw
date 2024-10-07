.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _net:

####################################
数字电视网络 API
####################################

数字电视网络设备控制将传输流中的数据包映射到虚拟网络接口，通过标准的 Linux 网络协议栈可见。目前支持两种封装方式：

-  `多协议封装 (MPE) <http://en.wikipedia.org/wiki/Multiprotocol_Encapsulation>`__

-  `超轻量级封装 (ULE) <http://en.wikipedia.org/wiki/Unidirectional_Lightweight_Encapsulation>`__

为了创建 Linux 虚拟网络接口，应用程序需要告诉内核传输流中存在的 PID 和封装类型。这通过 `/dev/dvb/adapter?/net?` 设备节点完成。数据将通过虚拟 `dvb?_?` 网络接口可用，并且可以通过标准的 IP 工具（如 ip、route、netstat、ifconfig 等）进行控制和路由。数据类型和 ioctl 定义在 `linux/dvb/net.h` 头文件中定义。
.. _net_fcalls:

数字电视网络函数调用
#############################

.. toctree::
    :maxdepth: 1

    net-types
    net-add-if
    net-remove-if
    net-get-if
