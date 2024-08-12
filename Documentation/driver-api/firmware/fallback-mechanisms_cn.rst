回退机制
========

支持一种回退机制，以克服直接在根文件系统上进行文件系统查找失败的问题，或者由于实际原因无法将固件安装到根文件系统上的情况。与支持固件回退机制相关的内核配置选项包括：

  * CONFIG_FW_LOADER_USER_HELPER：启用构建固件回退机制。大多数发行版今天都启用了此选项。如果启用但禁用了CONFIG_FW_LOADER_USER_HELPER_FALLBACK，则仅提供自定义回退机制，并且对于request_firmware_nowait()调用，
  * CONFIG_FW_LOADER_USER_HELPER_FALLBACK：强制启用每个请求以在所有固件API调用（除了request_firmware_direct()）上启用kobject uevent回退机制。大多数发行版今天禁用了此选项。request_firmware_nowait()调用允许一个替代的回退机制：如果启用了此kconfig选项，并且您传递给request_firmware_nowait()的第二个参数uevent设置为false，那么您告诉内核您有一个自定义的回退机制，并且它会手动加载固件。下面提供更多细节。
请注意，这意味着当具有以下配置时：

CONFIG_FW_LOADER_USER_HELPER=y
CONFIG_FW_LOADER_USER_HELPER_FALLBACK=n

即使对于request_firmware_nowait()调用时uevent设置为true，kobject uevent回退机制也不会生效。

证明固件回退机制的必要性
========================

直接文件系统查找可能会因各种原因失败。已知的原因值得列举和记录，以证明回退机制的需求：

* 启动时与根文件系统的访问竞争
* 恢复时的竞争。这个问题通过固件缓存解决，但固件缓存只有在使用uevents时才支持，并且不支持request_firmware_into_buf()

* 无法通过典型手段访问固件：

        * 它不能被安装到根文件系统中
        * 固件提供了针对单元高度定制的独特设备特定数据。例如，对于移动设备的WiFi芯片组的校准数据。这种校准数据不是所有单元共有的，而是针对每个单元定制的。此类信息可能安装在与提供根文件系统的闪存分区不同的其他闪存分区中。
回退机制类型
=============

实际上有两种回退机制可用，使用一个共享的sysfs接口作为加载设施：

* Kobject uevent回退机制
* 自定义回退机制

首先让我们记录共享的sysfs加载设施。
固件sysfs加载设施
==================

为了帮助设备驱动程序使用回退机制上传固件，固件基础设施创建了一个sysfs接口，使用户空间能够加载并指示固件何时准备好。该sysfs目录是通过fw_create_instance()创建的。此调用创建一个以所请求的固件命名的新结构设备，并通过将用于发出请求的设备作为父设备关联来在设备层次结构中建立它。

该sysfs目录的文件属性通过新设备的类（firmware_class）和组（fw_dev_attr_groups）定义和控制。

实际上，原始的firmware_class模块名就是从这里来的，因为最初唯一可用的固件加载机制就是我们现在作为回退机制使用的机制，该机制注册一个struct class firmware_class。因为暴露的属性是模块名的一部分，所以为了确保与旧用户空间的向后兼容性，将来不能重命名模块名firmware_class。
为了使用 sysfs 接口加载固件，我们暴露了一个加载指示器及一个文件上传固件的位置：

  * `/sys/$DEVPATH/loading`
  * `/sys/$DEVPATH/data`

要上传固件，您需要向加载文件写入 `1` 来表明正在加载固件。然后将固件写入数据文件中，并通过向加载文件写入 `0` 来通知内核固件已准备好。
用于帮助使用 sysfs 加载固件的固件设备仅在直接固件加载失败且您的固件请求启用了回退机制的情况下创建。这通过 `:c:func::firmware_fallback_sysfs` 设置。重要的是要强调，如果直接文件系统查找成功，则不会创建任何设备。
使用如下命令：

        `echo 1 > /sys/$DEVPATH/loading`

将会立即清除任何之前的部分加载，并使固件 API 返回错误。当加载固件时，`firmware_class` 会根据 `PAGE_SIZE` 增量增长一个缓冲区来保存传入的固件图像。`firmware_data_read()` 和 `firmware_loading_show()` 主要是为测试固件驱动程序提供的，以供测试使用，在正常情况下它们不会被调用或期望用户空间经常使用。
### firmware_fallback_sysfs
.. kernel-doc:: drivers/base/firmware_loader/fallback.c
   :functions: firmware_fallback_sysfs

### 固件 kobject uevent 回退机制

由于为帮助加载固件作为回退机制而创建了设备，用户空间可以通过依赖 kobject uevent 来获知该设备的添加。设备加入到设备层次结构中意味着固件加载的回退机制已经被启动。
对于实现细节，请参阅 `fw_load_sysfs_fallback()`，特别是关于 `dev_set_uevent_suppress()` 和 `kobject_uevent()` 的使用。内核的 kobject uevent 机制实现在 `lib/kobject_uevent.c` 中，它向用户空间发出 uevent。此外，Linux 发行版也可以启用 `CONFIG_UEVENT_HELPER_PATH`，这利用了内核用户模式助手（UMH）功能来为 kobject uevent 调用用户空间助手。但实际上没有标准发行版曾经使用过 `CONFIG_UEVENT_HELPER_PATH`。如果启用了 `CONFIG_UEVENT_HELPER_PATH`，则每当内核中调用 `kobject_uevent_env()` 触发每个 kobject uevent 时，都会调用此二进制文件。
用户空间支持了不同的实现来利用这种回退机制。当仅能通过 sysfs 机制加载固件时，用户空间组件 "hotplug" 提供了监控 kobject 事件的功能。历史上，这后来被 systemd 的 udev 所取代，但自 2014 年 8 月的 systemd commit `be2ea723b1d0`（"udev: remove userspace firmware loading support"）以来，固件加载支持从 udev 中移除。这意味着大多数现代 Linux 发行版今天不再使用或利用由 kobject uevents 提供的固件回退机制。这尤其突出，因为大多数今天的发行版禁用了 `CONFIG_FW_LOADER_USER_HELPER_FALLBACK`。
有关 kobject 事件变量设置的详细信息，请参阅 `do_firmware_uevent()`。当前通过 "kobject add" 事件传递给用户空间的变量包括：

* `FIRMWARE=` 固件名称
* `TIMEOUT=` 超时值
* `ASYNC=` API 请求是否异步

默认情况下，`DEVPATH` 由内核内部 kobject 基础设施设置。
以下是一个简单的 kobject uevent 脚本示例：

        # `$DEVPATH` 和 `$FIRMWARE` 已经在环境中提供
```bash
MY_FW_DIR=/lib/firmware/
echo 1 > /sys/$DEVPATH/loading
cat $MY_FW_DIR/$FIRMWARE > /sys/$DEVPATH/data
echo 0 > /sys/$DEVPATH/loading
```

自定义固件回退机制
==================

使用`request_firmware_nowait()`调用的用户还有另一个可用选项：依赖于sysfs回退机制，但要求不向用户空间发出任何kobject uevent。最初的逻辑是，除了udev之外，可能还需要其他工具在非传统路径中查找固件——这些路径位于“直接文件系统查找”部分所述路径之外。此选项对其他API调用不可用，因为它们总是强制启用uevent。由于uevent仅在内核启用了回退机制时才有意义，因此在未启用回退机制的内核上启用uevent似乎很奇怪。不幸的是，我们还依赖于可以被`request_firmware_nowait()`禁用的uevent标志来设置固件缓存。如上文所述，只有当为API调用启用uevent时，才会设置固件缓存。
虽然这可能会禁用`request_firmware_nowait()`调用的固件缓存，但使用此API的用户不应为此目的禁用缓存，因为这并非该标志的初衷。不设置uevent标志意味着您希望选择使用固件回退机制，但想要抑制kobject uevent，因为您有一个自定义解决方案，该方案会以某种方式监控设备层次结构中的设备添加，并通过自定义路径为您加载固件。

固件回退超时
=============

固件回退机制具有超时功能。如果在超时时间内没有将固件加载到sysfs接口，则会向驱动程序发送错误。默认情况下，如果需要uevent，则超时时间设置为60秒；否则，使用MAX_JIFFY_OFFSET（最大可能超时时间）。
对于不需要uevent的情况使用MAX_JIFFY_OFFSET的逻辑是，自定义解决方案将有足够的时间来加载固件。
您可以自定义固件超时时间，方法是在以下文件中echo您所需的超时时间：

* `/sys/class/firmware/timeout`

如果您echo 0，则表示使用MAX_JIFFY_OFFSET。超时的数据类型是一个整数。

EFI嵌入式固件回退机制
========================

在某些设备上，系统的EFI代码/ROM可能包含一些集成外围设备的嵌入式固件副本，而外围设备的Linux设备驱动程序需要访问这些固件。
需要此类固件的设备驱动程序可以使用`firmware_request_platform()`函数，注意这是与其它回退机制分开的独立机制，并且不使用sysfs接口。
需要此固件的设备驱动程序可以使用`efi_embedded_fw_desc`结构来描述其所需的固件：

.. kernel-doc:: include/linux/efi_embedded_fw.h
   :functions: efi_embedded_fw_desc

EFI嵌入式固件代码的工作原理是扫描所有EFI_BOOT_SERVICES_CODE内存段，寻找匹配前缀的八字节序列；如果找到前缀，则对长度字节执行sha256运算，如果匹配，则复制长度字节并将其添加到已找到的固件列表中。
为了避免在所有系统上进行这种较为昂贵的扫描，使用了DMI匹配。驱动程序预计会导出一个dmi_system_id数组，其中每个条目的driver_data指向一个`efi_embedded_fw_desc`。
为了将此数组注册到 efi-embedded-fw 代码中，驱动程序需要执行以下操作：

1. 必须始终内置到内核中，或者将 dmi_system_id 数组存储在一个单独的对象文件中，并确保该文件始终被内置。
2. 在 `include/linux/efi_embedded_fw.h` 中为 dmi_system_id 数组添加一个 extern 声明。
3. 将 dmi_system_id 数组添加到 `drivers/firmware/efi/embedded-firmware.c` 文件中的 embedded_fw_table 中，并使用 `#ifdef` 进行测试以确认驱动程序正在被内置。
4. 在其 Kconfig 入口中添加 `"select EFI_EMBEDDED_FIRMWARE if EFI_STUB"`。
`firmware_request_platform()` 函数会始终首先尝试直接从磁盘加载具有指定名称的固件，因此可以通过在 `/lib/firmware` 目录下放置一个文件来覆盖 EFI 内置固件。

请注意以下几点：

1. 扫描 EFI 内置固件的代码在 `start_kernel()` 的末尾运行，在调用 `rest_init()` 之前。对于使用 `subsys_initcall()` 注册自身的常规驱动程序和子系统来说这无关紧要。这意味着在此之前的代码无法使用 EFI 内置固件。
2. 当前，EFI 内置固件代码假设固件始终从 8 字节的倍数偏移开始，如果您的情况不符合这一条件，请提交补丁进行修正。
3. 当前，EFI 内置固件代码仅在 x86 架构上工作，因为其他架构在 EFI 内置固件代码有机会扫描之前就释放了 EFI_BOOT_SERVICES。
4. 当前对 EFI_BOOT_SERVICES 的暴力扫描是一种临时性的暴力解决方案。曾有讨论使用 UEFI 平台初始化 (PI) 规范中的固件卷协议，但被拒绝，原因是：
   1. PI 规范没有定义外围设备固件。
   2. PI 规范的内部接口不保证任何向后兼容性。FV 协议中的任何实现细节都可能发生变化，并且可能因系统而异。支持 FV 协议会很困难，因为它故意含糊不清。

检查并提取内置固件的方法示例
-----------------------------------

要检查并提取例如 Silead 触摸屏控制器的内置固件，请执行以下步骤：

1. 使用 `efi=debug` 参数启动系统。

2. 将 `/sys/kernel/debug/efi/boot_services_code?` 复制到您的主目录。

3. 在十六进制编辑器中打开 boot_services_code? 文件，搜索 Silead 固件的魔法前缀：`F0 00 00 00 02 00 00 00`，这将给出固件在 boot_services_code? 文件内的起始地址。
4. 固件具有特定的模式，它以一个8字节的页地址开始，通常是 F0 00 00 00 02 00 00 00 对于第一页，随后是32位单词地址+32位值对。随着每一对的出现，单词地址会增加4个字节（1个单词），直到一页完成。一页完成后紧接着是一个新的页地址，然后是更多的单词+值对。这导致了一个非常独特的模式。向下滚动直到这个模式停止，这就给出了固件在 boot_services_code? 文件内的结束位置。

5. `"dd if=boot_services_code? of=firmware bs=1 skip=<begin-addr> count=<len>"` 将为你提取固件。在十六进制编辑器中检查固件文件，确保你使用的 dd 参数正确。

6. 将其复制到 /lib/firmware 目录下，并使用预期的名称进行测试。

7. 如果提取出的固件可以正常工作，你可以使用找到的信息来填充一个 efi_embedded_fw_desc 结构体来描述它，运行 "sha256sum firmware" 来获取 sha256 值并将其放入 sha256 字段中。
