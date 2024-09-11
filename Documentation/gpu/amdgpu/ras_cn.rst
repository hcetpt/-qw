====================
AMDGPU RAS 支持
====================

AMDGPU RAS 接口通过 sysfs（用于信息查询）和 debugfs（用于错误注入）暴露。

RAS debugfs/sysfs 控制和错误注入接口
========================================================

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_ras.c
   :doc: AMDGPU RAS debugfs 控制接口

RAS 对于不可恢复错误的重启行为
============================================

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_ras.c
   :doc: AMDGPU RAS 对于不可恢复错误的重启行为

RAS 错误计数 sysfs 接口
===============================

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_ras.c
   :doc: AMDGPU RAS sysfs 错误计数接口

RAS EEPROM debugfs 接口
============================

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_ras.c
   :doc: AMDGPU RAS debugfs EEPROM 表重置接口

RAS VRAM 坏页面 sysfs 接口
==================================

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_ras.c
   :doc: AMDGPU RAS sysfs gpu_vram_bad_pages 接口

示例代码
===========

用于测试错误注入的示例代码可以在以下链接找到：
https://cgit.freedesktop.org/mesa/drm/tree/tests/amdgpu/ras_tests.c

这是 libdrm amdgpu 单元测试的一部分，覆盖了 GPU 的多个领域。有四组测试：

RAS 基本测试

该测试验证 RAS 功能是否已启用，并确保必要的 sysfs 和 debugfs 文件存在。
RAS 查询测试

此测试检查每个支持的 IP 块的 RAS 可用性和启用状态以及错误计数。
RAS 注入测试

此测试为每个 IP 注入错误。
RAS 禁用测试

此测试测试禁用每个 IP 块的 RAS 功能。
