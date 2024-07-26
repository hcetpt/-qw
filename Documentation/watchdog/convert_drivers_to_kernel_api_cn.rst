将旧的看门狗驱动程序转换为看门狗框架
=========================================================

作者：Wolfram Sang <wsa@kernel.org>

在看门狗框架被加入内核之前，每个驱动程序都必须自己实现API。现在，随着框架提取了通用组件，这些驱动程序可以简化并成为框架的用户。本文件旨在指导您完成这项任务。描述了必要的步骤以及需要注意的事项。

移除`file_operations`结构体
---------------------------------

旧驱动程序会为其自身定义`file_operations`结构体以处理如`open()`、`write()`等操作。这些现在由框架处理，并在需要时调用驱动程序。因此，通常情况下，`file_operations`结构体及其相关函数都可以删除。只有少数与驱动程序特定的细节需要转移到其他函数中。以下是各函数及其可能需要的操作概述：

- `open`: 所有涉及资源管理（文件打开检查、关闭前的准备等）的部分可以直接删除。设备特定的代码需要移到特定于驱动程序的启动函数中。请注意，对于某些驱动程序，启动函数同时也作为ping函数使用。如果确实如此并且你需要确保启动/停止是平衡的（例如时钟！），那么最好重构一个单独的启动函数。
- `close`: 与`open`相同提示适用。
- `write`: 可以直接删除，所有定义的行为都由框架处理，例如写入时的ping操作和特殊字符（'V'）的处理。
- `ioctl`: 虽然允许驱动程序扩展IOCTL接口，但最常用的操作由框架处理，需要一些来自驱动程序的帮助：
  
  - `WDIOC_GETSUPPORT`: 从驱动程序返回必需的`watchdog_info`结构体。
  - `WDIOC_GETSTATUS`: 需要定义状态回调函数，否则返回0。
  - `WDIOC_GETBOOTSTATUS`: 需要正确设置`bootstatus`成员。如果你没有进一步的支持，请确保它是0！
  - `WDIOC_SETOPTIONS`: 不需要任何准备工作。
  - `WDIOC_KEEPALIVE`: 如果需要，`watchdog_info`中的选项需要设置`WDIOF_KEEPALIVEPING`。
  - `WDIOC_SETTIMEOUT`: `watchdog_info`中的选项需要设置`WDIOF_SETTIMEOUT`，并且需要定义`set_timeout`回调函数。核心也会做限制检查，如果设置了`watchdog`设备中的`min_timeout`和`max_timeout`。所有这些都是可选的。
  - `WDIOC_GETTIMEOUT`: 不需要任何准备工作。
  - `WDIOC_GETTIMELEFT`: 需要定义`get_timeleft()`回调函数。否则它将返回`EOPNOTSUPP`。

  其他IOCTL可以通过`ioctl`回调函数来处理。请注意，这主要是为了移植旧驱动程序；新驱动程序不应该发明私有的IOCTL。
  
  私有的IOCTL首先被处理。当回调函数返回`-ENOIOCTLCMD`时，框架的IOCTL也将被尝试。任何其他错误将直接提供给用户。

示例转换：

```c
-static const struct file_operations s3c2410wdt_fops = {
-       .owner          = THIS_MODULE,
-       .llseek         = no_llseek,
-       .write          = s3c2410wdt_write,
-       .unlocked_ioctl = s3c2410wdt_ioctl,
-       .open           = s3c2410wdt_open,
-       .release        = s3c2410wdt_release,
-};
```

检查函数中是否有设备特定的内容，并保留下来以便后续重构。其余部分可以删除。
移除杂项设备
--------------

由于文件操作结构体已经不再使用，因此你也可以移除 `struct miscdevice`。框架将在由 `watchdog_register_device()` 调用的 `watchdog_dev_register()` 中创建它：

  -static struct miscdevice s3c2410wdt_miscdev = {
  -       .minor          = WATCHDOG_MINOR,
  -       .name           = "watchdog",
  -       .fops           = &s3c2410wdt_fops,
  -};

移除过时的包含和定义
--------------------

由于简化，一些定义可能现在不再使用。移除它们。包含文件也可以被移除。例如：

  - #include <linux/fs.h>
  - #include <linux/miscdevice.h> （如果未使用MODULE_ALIAS_MISCDEV）
  - #include <linux/uaccess.h> （如果没有自定义IOCTL）

添加看门狗操作
---------------

所有可能的回调函数都在 `struct watchdog_ops` 中定义。你可以在本目录下的 `watchdog-kernel-api.txt` 文件中找到其解释。`start()` 和 `owner` 必须设置，其余的是可选的。在旧驱动程序中很容易找到对应的函数。请注意，你现在将获得一个指向看门狗设备的指针作为这些函数的参数，因此你可能需要更改函数的头部。其他更改很可能不需要，因为这里直接进行硬件访问。如果你在上述步骤中有遗留的特定于设备的代码，应该重构为这些回调。这里有一个简单的例子：

  +static struct watchdog_ops s3c2410wdt_ops = {
  +       .owner = THIS_MODULE,
  +       .start = s3c2410wdt_start,
  +       .stop = s3c2410wdt_stop,
  +       .ping = s3c2410wdt_keepalive,
  +       .set_timeout = s3c2410wdt_set_heartbeat,
  +};

典型的函数头部更改如下所示：

  -static void s3c2410wdt_keepalive(void)
  +static int s3c2410wdt_keepalive(struct watchdog_device *wdd)
   {
  ..
+
  +       return 0;
   }

  ..
-       s3c2410wdt_keepalive();
  +       s3c2410wdt_keepalive(&s3c2410_wdd);

添加看门狗设备
---------------

现在我们需要创建一个 `struct watchdog_device` 并填充必要的信息以供框架使用。该结构体也在本目录下的 `watchdog-kernel-api.txt` 文件中详细解释。我们将强制性的 `watchdog_info` 结构体以及新创建的 `watchdog_ops` 传递给它。通常，旧驱动程序使用静态变量来记录诸如启动状态和超时时间等信息。这些必须转换为使用 `watchdog_device` 中的成员。请注意，超时值是无符号整数。有些驱动程序使用有符号整数，因此这也需要转换。这里是一个简单的看门狗设备的例子：

  +static struct watchdog_device s3c2410_wdd = {
  +       .info = &s3c2410_wdt_ident,
  +       .ops = &s3c2410wdt_ops,
  +};

处理 'nowayout' 特性
---------------------

一些驱动程序静态地使用 nowayout，即没有为此特性提供模块参数，并且仅通过 CONFIG_WATCHDOG_NOWAYOUT 来确定是否使用此功能。这需要通过以下方式初始化看门狗设备的状态变量：

        .status = WATCHDOG_NOWAYOUT_INIT_STATUS,

然而，大多数驱动程序也允许运行时配置 nowayout，通常通过添加模块参数实现。这种转换可能是这样的：

	watchdog_set_nowayout(&s3c2410_wdd, nowayout);

模块参数本身需要保留，与 nowayout 相关的其他内容都可以删除。这很可能是 `open()`、`close()` 或 `write()` 中的一些代码。

注册看门狗设备
----------------

将 `misc_register(&miscdev)` 替换为 `watchdog_register_device(&watchdog_dev)` 。确保检查返回值，并且如果存在错误消息，它仍然适用。同样也要转换卸载的情况：

  -       ret = misc_register(&s3c2410wdt_miscdev);
  +       ret = watchdog_register_device(&s3c2410_wdd);

  ..
-       misc_deregister(&s3c2410wdt_miscdev);
  +       watchdog_unregister_device(&s3c2410_wdd);

更新 Kconfig 项
----------------

驱动程序的条目现在需要选择 WATCHDOG_CORE：

  +       select WATCHDOG_CORE

创建补丁并发送到上游
----------------------

确保你理解了 `Documentation/process/submitting-patches.rst`，并将你的补丁发送到 linux-watchdog@vger.kernel.org。我们期待着你的贡献 :)
