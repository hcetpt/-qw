### SPDX 许可证标识符: GPL-2.0

===================
固件上传 API
===================

注册到固件加载器的设备驱动程序将暴露持久化的 sysfs 节点，以便用户能够发起对该设备的固件更新。接收的数据验证工作由设备驱动程序和/或设备本身负责。固件上传使用了与固件回退文档中描述相同的 *loading* 和 *data* sysfs 文件。此外，还添加了额外的 sysfs 文件来提供关于固件图像传输到设备的状态信息。

注册用于固件上传
============================

设备驱动程序通过调用 `firmware_upload_register()` 注册用于固件上传。参数列表中包含一个名称，用于在 `/sys/class/firmware` 下识别该设备。用户可以通过向目标设备的 *loading* sysfs 文件写入数字 1 来启动固件上传。接下来，用户将固件图像写入 *data* sysfs 文件。写入固件数据后，用户向 *loading* sysfs 文件写入数字 0 以表示完成。向 *loading* 写入 0 还会触发固件向较低级别的设备驱动程序的传输（在内核工作者线程的上下文中）。

为了使用固件上传 API，需要编写实现一组操作的驱动程序。探测函数调用 `firmware_upload_register()` 并且移除函数调用 `firmware_upload_unregister()`，例如：

```c
static const struct fw_upload_ops m10bmc_ops = {
    .prepare = m10bmc_sec_prepare,
    .write = m10bmc_sec_write,
    .poll_complete = m10bmc_sec_poll_complete,
    .cancel = m10bmc_sec_cancel,
    .cleanup = m10bmc_sec_cleanup,
};

static int m10bmc_sec_probe(struct platform_device *pdev)
{
    const char *fw_name, *truncate;
    struct m10bmc_sec *sec;
    struct fw_upload *fwl;
    unsigned int len;

    sec = devm_kzalloc(&pdev->dev, sizeof(*sec), GFP_KERNEL);
    if (!sec)
        return -ENOMEM;

    sec->dev = &pdev->dev;
    sec->m10bmc = dev_get_drvdata(pdev->dev.parent);
    dev_set_drvdata(&pdev->dev, sec);

    fw_name = dev_name(sec->dev);
    truncate = strstr(fw_name, ".auto");
    len = (truncate) ? truncate - fw_name : strlen(fw_name);
    sec->fw_name = kmemdup_nul(fw_name, len, GFP_KERNEL);

    fwl = firmware_upload_register(THIS_MODULE, sec->dev, sec->fw_name,
                                   &m10bmc_ops, sec);
    if (IS_ERR(fwl)) {
        dev_err(sec->dev, "固件上传驱动未能启动\n");
        kfree(sec->fw_name);
        return PTR_ERR(fwl);
    }

    sec->fwl = fwl;
    return 0;
}

static int m10bmc_sec_remove(struct platform_device *pdev)
{
    struct m10bmc_sec *sec = dev_get_drvdata(&pdev->dev);

    firmware_upload_unregister(sec->fwl);
    kfree(sec->fw_name);
    return 0;
}
```

firmware_upload_register
------------------------
.. kernel-doc:: drivers/base/firmware_loader/sysfs_upload.c
   :identifiers: firmware_upload_register

firmware_upload_unregister
--------------------------
.. kernel-doc:: drivers/base/firmware_loader/sysfs_upload.c
   :identifiers: firmware_upload_unregister

固件上传操作
-------------------
.. kernel-doc:: include/linux/firmware.h
   :identifiers: fw_upload_ops

固件上传进度代码
------------------------------
以下进度代码被固件加载器内部使用。
对应的字符串通过下面描述的状态 sysfs 节点报告，并在 ABI 文档中记录。
.. kernel-doc:: drivers/base/firmware_loader/sysfs_upload.h
   :identifiers: fw_upload_prog

固件上传错误代码
---------------------------
在失败的情况下，驱动程序操作可能返回以下错误代码：

.. kernel-doc:: include/linux/firmware.h
   :identifiers: fw_upload_err

sysfs 属性
================

除了 *loading* 和 *data* sysfs 文件外，还有其他 sysfs 文件用于监控数据传输到目标设备的状态以及确定传输的最终成功或失败状态。
根据设备和固件图像的大小，固件更新可能需要毫秒到几分钟的时间。

额外的 sysfs 文件包括：

* status - 提供固件更新进度的指示
* error - 提供失败的固件更新的错误信息
* remaining_size - 跟踪更新中的数据传输部分
* cancel - 向此文件写入数字 1 以取消更新
