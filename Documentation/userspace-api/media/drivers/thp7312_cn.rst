SPDX 许可证标识符: 仅限 GPL-2.0

THine THP7312 ISP 驱动程序
========================

THP7312 驱动程序实现了以下特定于驱动程序的控制功能：

``V4L2_CID_THP7312_LOW_LIGHT_COMPENSATION``
    在启用自动曝光时，根据光照条件自动调整帧率的启用/禁用功能。

``V4L2_CID_THP7312_AUTO_FOCUS_METHOD``
    设置自动对焦的方法。只有在启用自动对焦时才生效。
.. flat-table::
        :header-rows:  0
        :stub-columns: 0
        :widths:       1 4

        * - ``0``
          - 基于对比度的自动对焦
        * - ``1``
          - 相位检测自动对焦 (PDAF)
        * - ``2``
          - 基于对比度和相位检测的混合自动对焦

    该控制支持的值取决于连接到 THP7312 的相机传感器模块。如果模块没有可调焦距的镜头驱动器，则 THP7312 驱动程序不会暴露此控制。如果模块有可调焦距的镜头但传感器不支持 PDAF，则只有基于对比度的自动对焦值有效。否则，所有控制值都将被支持。
``V4L2_CID_THP7312_NOISE_REDUCTION_AUTO``
    启用/禁用自动降噪。
``V4L2_CID_THP7312_NOISE_REDUCTION_ABSOLUTE``
    设置降噪强度，其中 0 表示最弱，10 表示最强。
