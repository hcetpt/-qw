===================
ALSA 驱动程序 API
===================

卡片和设备的管理
===============================

卡片管理
---------------
.. kernel-doc:: sound/core/init.c

设备组件
-----------------
.. kernel-doc:: sound/core/device.c

模块请求和设备文件条目
---------------------------------------
.. kernel-doc:: sound/core/sound.c

内存管理辅助函数
-------------------------
.. kernel-doc:: sound/core/memory.c
.. kernel-doc:: sound/core/memalloc.c


PCM API
=======

PCM 核心
--------
.. kernel-doc:: sound/core/pcm.c
.. kernel-doc:: sound/core/pcm_lib.c
.. kernel-doc:: sound/core/pcm_native.c
.. kernel-doc:: include/sound/pcm.h

PCM 格式辅助函数
------------------
.. kernel-doc:: sound/core/pcm_misc.c

PCM 内存管理
---------------------
.. kernel-doc:: sound/core/pcm_memory.c

PCM DMA 引擎 API
------------------
.. kernel-doc:: sound/core/pcm_dmaengine.c
.. kernel-doc:: include/sound/dmaengine_pcm.h

控制/混音器 API
=================

通用控制接口
-------------------------
.. kernel-doc:: sound/core/control.c

AC97 编解码器 API
--------------
.. kernel-doc:: sound/pci/ac97/ac97_codec.c
.. kernel-doc:: sound/pci/ac97/ac97_pcm.c

虚拟主控 API
--------------------------
.. kernel-doc:: sound/core/vmaster.c
.. kernel-doc:: include/sound/control.h

MIDI API
========

原始 MIDI API
------------
.. kernel-doc:: sound/core/rawmidi.c

MPU401-UART API
---------------
.. kernel-doc:: sound/drivers/mpu401/mpu401_uart.c

进程信息 API
=============

进程信息接口
-------------------
.. kernel-doc:: sound/core/info.c

压缩卸载
================

压缩卸载 API
--------------------
.. kernel-doc:: sound/core/compress_offload.c
.. kernel-doc:: include/uapi/sound/compress_offload.h
.. kernel-doc:: include/uapi/sound/compress_params.h
.. kernel-doc:: include/sound/compress_driver.h

ASoC
====

ASoC 核心 API
-------------
.. kernel-doc:: include/sound/soc.h
.. kernel-doc:: sound/soc/soc-core.c
.. kernel-doc:: sound/soc/soc-devres.c
.. kernel-doc:: sound/soc/soc-component.c
.. kernel-doc:: sound/soc/soc-pcm.c
.. kernel-doc:: sound/soc/soc-ops.c
.. kernel-doc:: sound/soc/soc-compress.c

ASoC DAPM API
-------------
.. kernel-doc:: sound/soc/soc-dapm.c

ASoC DMA 引擎 API
-------------------
.. kernel-doc:: sound/soc/soc-generic-dmaengine-pcm.c

其他函数
=======================

硬件相关设备 API
------------------------------
.. kernel-doc:: sound/core/hwdep.c

耳机抽象层 API
--------------------------
.. kernel-doc:: include/sound/jack.h
.. kernel-doc:: sound/core/jack.c
.. kernel-doc:: sound/soc/soc-jack.c

ISA DMA 辅助函数
---------------
.. kernel-doc:: sound/core/isadma.c

其他辅助宏
-------------------
.. kernel-doc:: include/sound/core.h
.. kernel-doc:: sound/sound_core.c
