====  
UAPI  
====

与本节相关的源代码可以在 ``pvr_drm.h`` 中找到
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: PowerVR UAPI

对象数组  
=============

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_obj_array

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: DRM_PVR_OBJ_ARRAY

IOCTLS  
======

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: PowerVR IOCTL 接口

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: PVR_IOCTL

设备查询  
---------
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: PowerVR IOCTL 设备查询接口

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_dev_query

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_dev_query_args

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_dev_query_gpu_info
                 drm_pvr_dev_query_runtime_info
                 drm_pvr_dev_query_hwrt_info
                 drm_pvr_dev_query_quirks
                 drm_pvr_dev_query_enhancements

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_heap_id
                 drm_pvr_heap
                 drm_pvr_dev_query_heap_info

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_static_data_area_usage
                 drm_pvr_static_data_area
                 drm_pvr_dev_query_static_data_areas

创建 BO  
---------
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: PowerVR IOCTL 创建 BO 接口

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_create_bo_args

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: 用于创建 BO 的标志

获取 BO MMAP 偏移量  
------------------
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: PowerVR IOCTL 获取 BO MMAP 偏移量接口

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_get_bo_mmap_offset_args

创建和销毁 VM 上下文  
----------------------------------------
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: PowerVR IOCTL 创建和销毁 VM 上下文接口

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_create_vm_context_args
                 drm_pvr_ioctl_destroy_vm_context_args

VM 映射和 VM 反映射  
-------------------
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: PowerVR IOCTL VM 映射和 VM 反映射接口

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_vm_map_args
                 drm_pvr_ioctl_vm_unmap_args

创建和销毁上下文  
----------------------------------
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: PowerVR IOCTL 创建和销毁上下文接口

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_create_context_args

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ctx_priority
                 drm_pvr_ctx_type
                 drm_pvr_static_render_context_state
                 drm_pvr_static_render_context_state_format
                 drm_pvr_reset_framework
                 drm_pvr_reset_framework_format

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_destroy_context_args

创建和销毁空闲列表  
--------------------------------------
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: PowerVR IOCTL 创建和销毁空闲列表接口

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_create_free_list_args

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_destroy_free_list_args

创建和销毁硬件运行数据集  
--------------------------------------------
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: PowerVR IOCTL 创建和销毁硬件运行数据集接口

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_create_hwrt_dataset_args

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_create_hwrt_geom_data_args
                 drm_pvr_create_hwrt_rt_data_args

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_destroy_hwrt_dataset_args

提交任务  
-----------
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: PowerVR IOCTL 提交任务接口

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: drm_pvr_sync_op 对象的标志
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_ioctl_submit_jobs_args

.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: 提交任务 ioctl 几何命令的标志
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: 提交任务 ioctl 片元命令的标志
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: 提交任务 ioctl 计算命令的标志
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :doc: 提交任务 ioctl 传输命令的标志
.. kernel-doc:: include/uapi/drm/pvr_drm.h
   :identifiers: drm_pvr_sync_op
                 drm_pvr_job_type
                 drm_pvr_hwrt_data_ref
                 drm_pvr_job

内部注释  
==============
.. kernel-doc:: drivers/gpu/drm/imagination/pvr_device.h
   :doc: IOCTL 验证助手

.. kernel-doc:: drivers/gpu/drm/imagination/pvr_device.h
   :identifiers: PVR_STATIC_ASSERT_64BIT_ALIGNED PVR_IOCTL_UNION_PADDING_CHECK
                 pvr_ioctl_union_padding_check
