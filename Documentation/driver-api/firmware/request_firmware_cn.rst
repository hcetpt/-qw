====================
请求固件 API
====================

通常，您会加载固件然后以某种方式将其加载到设备中。
典型的固件工作流程如下所示：

	如果 (request_firmware(&fw_entry, "$FIRMWARE", device) == 0)
                将固件复制到设备(fw_entry->data, fw_entry->size);
	释放固件(fw_entry);

同步固件请求
=============================

同步固件请求将等待直到找到固件或返回错误。
request_firmware
----------------
.. kernel-doc:: drivers/base/firmware_loader/main.c
   :functions: request_firmware

firmware_request_nowarn
-----------------------
.. kernel-doc:: drivers/base/firmware_loader/main.c
   :functions: firmware_request_nowarn

firmware_request_platform
-------------------------
.. kernel-doc:: drivers/base/firmware_loader/main.c
   :functions: firmware_request_platform

request_firmware_direct
-----------------------
.. kernel-doc:: drivers/base/firmware_loader/main.c
   :functions: request_firmware_direct

request_firmware_into_buf
-------------------------
.. kernel-doc:: drivers/base/firmware_loader/main.c
   :functions: request_firmware_into_buf

异步固件请求
==============================

异步固件请求允许驱动程序代码不必等待直到返回固件或错误。提供了函数回调，以便在找到固件或错误时通过回调通知驱动程序。request_firmware_nowait()不能在原子上下文中调用。
request_firmware_nowait
-----------------------
.. kernel-doc:: drivers/base/firmware_loader/main.c
   :functions: request_firmware_nowait

重启时的特殊优化
===============================

某些设备具有优化措施，可以在系统重启期间保留固件。当使用此类优化时，驱动程序作者必须确保从挂起状态恢复后固件仍然可用，这可以通过使用firmware_request_cache()来完成，而不是请求加载固件。
firmware_request_cache()
------------------------
.. kernel-doc:: drivers/base/firmware_loader/main.c
   :functions: firmware_request_cache

预期的驱动程序使用request firmware API
========================================

一旦API调用返回，您处理固件然后释放固件。例如，如果您使用了request_firmware()且它返回成功，则驱动程序可以通过fw_entry->{data,size}访问固件映像。如果出现问题，request_firmware()返回非零值，并将fw_entry设置为NULL。一旦您的驱动程序处理完固件，它可以调用release_firmware(fw_entry)来释放固件映像及相关资源。
