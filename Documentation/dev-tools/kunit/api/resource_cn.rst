SPDX许可标识符: GPL-2.0

============
资源API
============

本文件记录了KUnit资源API的使用方法。
大多数用户无需直接使用此API，但高级用户可以利用它来在每个测试用例的基础上存储状态信息、注册自定义清理操作等。
.. kernel-doc:: include/kunit/resource.h
   :internal:

管理的设备
---------------

用于操作KUnit管理的`struct device`和`struct device_driver`结构体的函数。
如果要使用这些功能，请包含`kunit/device.h`。
.. kernel-doc:: include/kunit/device.h
   :internal:
