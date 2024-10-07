SPDX 许可声明标识符：GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.ca

.. _CA_RESET:

========
CA_RESET
========

名称
----

CA_RESET

概要
----

.. c:macro:: CA_RESET

``int ioctl(fd, CA_RESET)``

参数
---------

``fd``
  由先前调用 :c:func:`open()` 返回的文件描述符
描述
----

将条件访问（Conditional Access）硬件重置到初始状态。在开始使用 CA 硬件之前应调用此函数。
返回值
------------

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为相应的错误码
通用错误码在章节 :ref:`Generic Error Codes <gen-errors>` 中有描述
