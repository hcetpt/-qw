==================
GPU 调试
==================

GPUVM 调试
==================

为了帮助调试与 GPU 虚拟内存相关的问题，驱动程序支持以下一些模块参数：

`vm_fault_stop` - 如果非0，则在发生 GPU 页面错误时停止 GPU 内存控制器
`vm_update_mode` - 如果非0，则使用 CPU 更新 GPU 页面表而不是 GPU

解码 GPUVM 页面错误
==================

如果你在内核日志中看到一个 GPU 页面错误，你可以对其进行解码以找出应用程序中的问题。你的内核日志中的页面错误可能看起来像这样：

::

 [gfxhub0] 无法重试的页面错误（src_id:0 ring:24 vmid:3 pasid:32777，进程 glxinfo pid 2424 线程 glxinfo:cs0 pid 2425）
   在地址 0x0000800102800000 开始的页面上，由 IH 客户端 0x1b (UTCL2) 引起
 VM_L2_PROTECTION_FAULT_STATUS:0x00301030
 	故障 UTCL2 客户端 ID: TCP (0x8)
 	更多故障: 0x0
 	WALKER_ERROR: 0x0
 	权限故障: 0x3
 	映射错误: 0x0
 	读写: 0x0

首先，你有内存中心 gfxhub 和 mmhub。gfxhub 是用于图形、计算和某些芯片上的 SDMA 的内存中心。mmhub 是用于多媒体和某些芯片上的 SDMA 的内存中心。
接下来是 vmid 和 pasid。如果 vmid 是0，此故障可能是由内核驱动或固件引起的。如果 vmid 非0，则通常是一个用户应用程序中的故障。pasid 用于将 vmid 与系统进程 ID 相关联。如果进程在发生故障时处于活动状态，则会打印进程信息。
接下来是引起故障的 GPU 虚拟地址。
客户端 ID 表示引起故障的 GPU 模块。
一些常见的客户端 ID：

- CB/DB：图形管道的颜色/深度后端
- CPF：命令处理器前端
- CPC：命令处理器计算
- CPG：命令处理器图形
- TCP/SQC/SQG：着色器
- SDMA：SDMA 引擎
- VCN：视频编码/解码引擎
- JPEG：JPEG 引擎

权限故障描述了遇到的故障情况：

- 位 0：PTE 不有效
- 位 1：PTE 读取位未设置
- 位 2：PTE 写入位未设置
- 位 3：PTE 执行位未设置

最后，RW 表示访问是读取 (0) 还是写入 (1)。
在上面的例子中，着色器（客户端 ID = TCP）生成了一个对无效页面（PERMISSION_FAULTS = 0x3）的读取（RW = 0x0），该页面位于 GPU 虚拟地址 0x0000800102800000。用户可以检查他们的着色器代码和资源描述符状态以确定导致 GPU 页面错误的原因。

UMR
===

`UMR <https://gitlab.freedesktop.org/tomstdenis/umr>`_ 是一个通用的 GPU 调试和诊断工具。请参阅 UMR 的 `文档 <https://umr.readthedocs.io/en/main/>`_ 了解其功能的更多信息。
