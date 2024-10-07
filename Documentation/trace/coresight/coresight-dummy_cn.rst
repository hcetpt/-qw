.. SPDX-License-Identifier: GPL-2.0

=============================
Coresight 傻瓜追踪模块
=============================

    :作者:   张浩 <quic_hazha@quicinc.com>
    :日期:   2023年6月

简介
------------

Coresight 傻瓜追踪模块适用于内核没有权限访问或配置的特定设备，例如高通平台上的 CoreSight TPDM。对于这些设备，需要一个傻瓜驱动程序将它们注册为 Coresight 设备。该模块还可以用于定义那些没有任何编程接口的组件，以便在驱动程序中创建路径。它提供了对傻瓜设备进行操作（如启用和禁用）的 Coresight API，并且还提供了用于调试的 Coresight 傻瓜汇点/源点路径。

配置详情
--------------

有两种类型的节点：傻瓜汇点（dummy sink）和傻瓜源点（dummy source）。这些节点可以在 ``/sys/bus/coresight/devices`` 中找到。
示例输出如下：

    $ ls -l /sys/bus/coresight/devices | grep dummy
    dummy_sink0 -> ../../../devices/platform/soc@0/soc@0:sink/dummy_sink0
    dummy_source0 -> ../../../devices/platform/soc@0/soc@0:source/dummy_source0
