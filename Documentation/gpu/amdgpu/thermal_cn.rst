===========================================
GPU 功率/热控制与监控
===========================================

HWMON 接口
================

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: hwmon

GPU sysfs 功率状态接口
================================

GPU 功率控制通过 sysfs 文件暴露
power_dpm_state
---------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: power_dpm_state

power_dpm_force_performance_level
---------------------------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: power_dpm_force_performance_level

pp_table
--------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: pp_table

pp_od_clk_voltage
-----------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: pp_od_clk_voltage

pp_dpm_*
--------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: pp_dpm_sclk pp_dpm_mclk pp_dpm_socclk pp_dpm_fclk pp_dpm_dcefclk pp_dpm_pcie

pp_power_profile_mode
---------------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: pp_power_profile_mode

pm_policy
---------------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: pm_policy

*_busy_percent
---------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: gpu_busy_percent

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: mem_busy_percent

gpu_metrics
-----------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: gpu_metrics

fan_curve
---------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: fan_curve

acoustic_limit_rpm_threshold
----------------------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: acoustic_limit_rpm_threshold

acoustic_target_rpm_threshold
-----------------------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: acoustic_target_rpm_threshold

fan_target_temperature
----------------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: fan_target_temperature

fan_minimum_pwm
---------------

.. kernel-doc:: drivers/gpu/drm/amd/pm/amdgpu_pm.c
   :doc: fan_minimum_pwm

GFXOFF
======

GFXOFF 是在大多数现代 GPU 中发现的一项功能，可在运行时节省电力。当 GFX 或计算管道上没有工作负载时，显卡的 RLC（运行列表控制器）固件会动态关闭图形引擎。在支持的 GPU 上，默认情况下 GFXOFF 是开启的。
用户空间可以通过 debugfs 接口与 GFXOFF 进行交互（所有值为 `uint32_t` 类型，除非另有说明）：

``amdgpu_gfxoff``
-----------------

用于启用/禁用 GFXOFF，并检查当前是否已启用/禁用：

  $ xxd -l1 -p /sys/kernel/debug/dri/0/amdgpu_gfxoff
  01

- 写入 0 禁用它，写入 1 启用它
- 读取 0 表示已禁用，1 表示已启用
如果已启用，则表示 GPU 可以根据需要进入 GFXOFF 模式。禁用表示永远不会进入 GFXOFF 模式
``amdgpu_gfxoff_status``
------------------------

用于检查当前 GPU 的 GFXOFF 状态：

  $ xxd -l1 -p /sys/kernel/debug/dri/0/amdgpu_gfxoff_status
  02

- 0：GPU 处于 GFXOFF 状态，图形引擎已关闭
- 1：从 GFXOFF 状态退出
- 2：未处于 GFXOFF 状态
- 3：进入 GFXOFF 状态

如果 GFXOFF 已启用，则值将在 [0, 3] 之间变化，尽可能进入 0 状态。当禁用时，它始终为 2。如果不支持则返回 ``-EINVAL``
``amdgpu_gfxoff_count``
-----------------------

用于获取自系统启动以来的总 GFXOFF 入口计数。该值为 `uint64_t` 类型，但由于固件限制，目前可能会作为 `uint32_t` 溢出。*仅在 vangogh 中支持*

``amdgpu_gfxoff_residency``
---------------------------

向 amdgpu_gfxoff_residency 写入 1 开始记录，写入 0 停止。读取它以获取上次记录间隔期间平均 GFXOFF 居留百分比乘以 100。例如，值为 7854 表示在上次记录间隔期间 GPU 有 78.54% 的时间处于 GFXOFF 模式。*仅在 vangogh 中支持*
