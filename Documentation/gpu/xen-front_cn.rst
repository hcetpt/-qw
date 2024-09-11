===============================================
drm/xen-front Xen 半虚拟化前端驱动
===============================================

此前端驱动根据 include/xen/interface/io/displif.h 中描述的显示协议实现了 Xen 半虚拟化显示。

显示缓冲区使用的驱动操作模式
==========================================

.. kernel-doc:: drivers/gpu/drm/xen/xen_drm_front.h
   :doc: 显示缓冲区使用的驱动操作模式

由前端驱动分配的缓冲区
----------------------------------------

.. kernel-doc:: drivers/gpu/drm/xen/xen_drm_front.h
   :doc: 由前端驱动分配的缓冲区

由后端分配的缓冲区
--------------------------------

.. kernel-doc:: drivers/gpu/drm/xen/xen_drm_front.h
   :doc: 由后端分配的缓冲区

驱动限制
==================

.. kernel-doc:: drivers/gpu/drm/xen/xen_drm_front.h
   :doc: 驱动限制
