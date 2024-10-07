.. 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.fe

.. _FE_ENABLE_HIGH_LNB_VOLTAGE:

********************************
ioctl FE_ENABLE_HIGH_LNB_VOLTAGE
********************************

名称
====

FE_ENABLE_HIGH_LNB_VOLTAGE - 选择输出直流电平，可在正常LNB电压和较高LNB电压之间切换

概述
========

.. c:宏:: FE_ENABLE_HIGH_LNB_VOLTAGE

``int ioctl(int fd, FE_ENABLE_HIGH_LNB_VOLTAGE, unsigned int high)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``high``
    有效标志：

    -  0 - 正常13V和18V
-  >0 - 启用略高于13/18V的电压，以补偿较长的天线电缆

描述
===========

选择输出直流电平，可在正常LNB电压（0）或一个大于0的值（较高电压）之间切换

返回值
============

成功时返回0
出错时返回-1，并且设置 ``errno`` 变量为适当的错误码
通用错误码在《通用错误码 <gen-errors>`_ 章节中有描述
