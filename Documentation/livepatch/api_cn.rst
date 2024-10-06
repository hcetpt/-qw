SPDX 许可证标识符：GPL-2.0

=================
在线修补 API
=================

在线修补启用
====================

.. kernel-doc:: kernel/livepatch/core.c
   :export:


影子变量
================

.. kernel-doc:: kernel/livepatch/shadow.c
   :export:

系统状态变更
====================

.. kernel-doc:: kernel/livepatch/state.c
   :export:

对象类型
============

.. kernel-doc:: include/linux/livepatch.h
   :identifiers: klp_patch klp_object klp_func klp_callbacks klp_state
