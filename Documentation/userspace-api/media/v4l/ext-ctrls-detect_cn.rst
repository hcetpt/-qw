.. SPDX-License-Identifier: GFDL-1.1-no-invariants-or-later

.. _detect-controls:

************************
检测控制参考
************************

检测类包括各种运动或物体检测设备的常用功能控制。

.. _detect-control-id:

检测控制ID
==================

``V4L2_CID_DETECT_CLASS (class)``
    检测类描述符。对该控制调用 :ref:`VIDIOC_QUERYCTRL` 将返回此控制类的描述。
``V4L2_CID_DETECT_MD_MODE (menu)``
    设置运动检测模式。
.. tabularcolumns:: |p{7.7cm}|p{9.8cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_DETECT_MD_MODE_DISABLED``
      - 禁用运动检测
    * - ``V4L2_DETECT_MD_MODE_GLOBAL``
      - 使用单一的运动检测阈值
    * - ``V4L2_DETECT_MD_MODE_THRESHOLD_GRID``
      - 图像被划分为网格，每个单元格有自己的运动检测阈值。这些阈值通过 ``V4L2_CID_DETECT_MD_THRESHOLD_GRID`` 矩阵控制设置
    * - ``V4L2_DETECT_MD_MODE_REGION_GRID``
      - 图像被划分为网格，每个单元格有自己的区域值，指定应使用哪些区域特定的运动检测阈值。每个区域有自己的阈值。这些区域特定阈值的设置方式由驱动程序决定。网格中各单元格的区域值通过 ``V4L2_CID_DETECT_MD_REGION_GRID`` 矩阵控制设置
``V4L2_CID_DETECT_MD_GLOBAL_THRESHOLD (integer)``
    设置与 ``V4L2_DETECT_MD_MODE_GLOBAL`` 运动检测模式一起使用的全局运动检测阈值。
``V4L2_CID_DETECT_MD_THRESHOLD_GRID (__u16 matrix)``
    设置网格中每个单元格的运动检测阈值。与 ``V4L2_DETECT_MD_MODE_THRESHOLD_GRID`` 运动检测模式一起使用。矩阵元素 (0, 0) 表示网格左上角的单元格。
``V4L2_CID_DETECT_MD_REGION_GRID (__u8 matrix)``
    设置网格中每个单元格的运动检测区域值。与 ``V4L2_DETECT_MD_MODE_REGION_GRID`` 运动检测模式一起使用。矩阵元素 (0, 0) 表示网格左上角的单元格。
当然，请提供您需要翻译的文本。
