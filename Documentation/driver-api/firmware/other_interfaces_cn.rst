其他固件接口
=========================

DMI 接口
--------------

.. kernel-doc:: drivers/firmware/dmi_scan.c
   :export:

EDD 接口
--------------

.. kernel-doc:: drivers/firmware/edd.c
   :internal:

通用系统帧缓冲接口
-------------------------------------

.. kernel-doc:: drivers/firmware/sysfb.c
   :export:

Intel Stratix10 SoC 服务层
---------------------------------
Intel Stratix10 SoC 的某些功能需要比内核更高的权限级别。此类安全特性包括 FPGA 编程。就 ARMv8 架构而言，内核运行在异常级别 1（EL1），而访问这些功能则需要异常级别 3（EL3）。
Intel Stratix10 SoC 服务层为驱动程序提供了一个内核内的 API，用于请求访问安全特性。这些请求被排队并逐一处理。ARM 的 SMCCC 用于将请求的执行传递给安全监视器（EL3）。

.. kernel-doc:: include/linux/firmware/intel/stratix10-svc-client.h
   :functions: stratix10_svc_command_code

.. kernel-doc:: include/linux/firmware/intel/stratix10-svc-client.h
   :functions: stratix10_svc_client_msg

.. kernel-doc:: include/linux/firmware/intel/stratix10-svc-client.h
   :functions: stratix10_svc_command_config_type

.. kernel-doc:: include/linux/firmware/intel/stratix10-svc-client.h
   :functions: stratix10_svc_cb_data

.. kernel-doc:: include/linux/firmware/intel/stratix10-svc-client.h
   :functions: stratix10_svc_client

.. kernel-doc:: drivers/firmware/stratix10-svc.c
   :export:
