================================
杂项AMDGPU驱动信息
================================

GPU产品信息
=======================

通过sysfs可以获取某些显卡的GPU相关信息：

产品名称
------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_fru_eeprom.c
   :doc: product_name

产品编号
--------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_fru_eeprom.c
   :doc: product_number

序列号
-------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_fru_eeprom.c
   :doc: serial_number

FRU ID
-------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_fru_eeprom.c
   :doc: fru_id

制造商
-------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_fru_eeprom.c
   :doc: manufacturer

唯一ID
---------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: unique_id

板卡信息
----------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_device.c
   :doc: board_info

加速处理单元（APU）信息
---------------------------------------

.. csv-table::
   :header-rows: 1
   :widths: 3, 2, 2, 1, 1, 1, 1
   :file: ./apu-asic-info-table.csv

独立GPU信息
-----------------

.. csv-table::
   :header-rows: 1
   :widths: 3, 2, 2, 1, 1, 1
   :file: ./dgpu-asic-info-table.csv


GPU内存使用信息
============================

可以通过sysfs访问各种内存统计信息：

VRAM总内存
-------------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_vram_mgr.c
   :doc: mem_info_vram_total

VRAM已用内存
------------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_vram_mgr.c
   :doc: mem_info_vram_used

可见VRAM总内存
-----------------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_vram_mgr.c
   :doc: mem_info_vis_vram_total

可见VRAM已用内存
----------------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_vram_mgr.c
   :doc: mem_info_vis_vram_used

GTT总内存
------------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_gtt_mgr.c
   :doc: mem_info_gtt_total

GTT已用内存
-----------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_gtt_mgr.c
   :doc: mem_info_gtt_used

PCIe统计信息
===========================

PCIe带宽
-------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: pcie_bw

PCIe重放计数
-----------------

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_device.c
   :doc: pcie_replay_count

GPU SmartShift信息
==========================

通过sysfs获取的GPU SmartShift信息：

SmartShift APU功率
--------------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: smartshift_apu_power

SmartShift 独立GPU功率
---------------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: smartshift_dgpu_power

SmartShift 偏置
---------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: smartshift_bias
