===============================================
Linux WatchDog 定时器驱动核心内核API
===============================================

最后审核：2013年2月12日

Wim Van Sebroeck <wim@iguana.be>

简介
------------
本文档不描述什么是WatchDog 定时器（WDT）驱动或设备。
它也不描述用户空间用于与WatchDog 定时器通信的API。如果您想了解这些内容，请阅读以下文件：Documentation/watchdog/watchdog-api.rst
那么本文档描述了什么？它描述的是那些希望使用WatchDog 定时器驱动核心框架的WatchDog 定时器驱动可以使用的API。该框架提供了所有面向用户空间的接口，因此不必每次重复编写相同的代码。这也意味着一个watchdog定时器驱动只需要提供控制watchdog定时器（WDT）的不同例程（操作）即可。
API
-------
每个希望使用WatchDog 定时器驱动核心的watchdog定时器驱动都必须`#include <linux/watchdog.h>`（在编写watchdog设备驱动时无论如何都需要这样做）。此头文件包含以下注册/注销例程：

```c
	extern int watchdog_register_device(struct watchdog_device *);
	extern void watchdog_unregister_device(struct watchdog_device *);
```

`watchdog_register_device`例程用于注册一个watchdog定时器设备。此例程的参数是指向一个`watchdog_device`结构体的指针。该例程成功时返回0，在失败时返回一个负的errno代码。
`watchdog_unregister_device`例程用于注销已注册的watchdog定时器设备。此例程的参数是已注册的`watchdog_device`结构体的指针。
watchdog子系统包括一种注册延迟机制，允许您在启动过程中尽可能早地注册watchdog。

`watchdog_device`结构体如下所示：

```c
  struct watchdog_device {
	int id;
	struct device *parent;
	const struct attribute_group **groups;
	const struct watchdog_info *info;
	const struct watchdog_ops *ops;
	const struct watchdog_governor *gov;
	unsigned int bootstatus;
	unsigned int timeout;
	unsigned int pretimeout;
	unsigned int min_timeout;
	unsigned int max_timeout;
	unsigned int min_hw_heartbeat_ms;
	unsigned int max_hw_heartbeat_ms;
	struct notifier_block reboot_nb;
	struct notifier_block restart_nb;
	void *driver_data;
	struct watchdog_core_data *wd_data;
	unsigned long status;
	struct list_head deferred;
  };
```

它包含以下字段：

* `id`：由`watchdog_register_device`设置，id为0是特殊的。它既有`/dev/watchdog0` cdev（动态主设备号，次设备号为0），也有旧的`/dev/watchdog` miscdev。在调用`watchdog_register_device`时会自动设置id。
* `parent`：在调用`watchdog_register_device`之前将其设置为父设备（或NULL）。
* groups: 在创建看门狗设备时要创建的 sysfs 属性组列表
* info: 指向一个 watchdog_info 结构的指针。该结构提供了一些关于看门狗计时器本身的附加信息（例如其唯一名称）
* ops: 指向看门狗支持的操作列表的指针
* gov: 指向分配给看门狗设备的预超时管理器的指针，或者为 NULL
* timeout: 看门狗计时器的超时值（以秒为单位）。如果设置了 WDOG_ACTIVE，并且用户空间未发送心跳请求，则在此时间后系统将重启
* pretimeout: 看门狗计时器的预超时值（以秒为单位）
* min_timeout: 看门狗计时器的最小超时值（以秒为单位）。如果设置，则是 'timeout' 的最小可配置值
* max_timeout: 从用户空间视角来看的看门狗计时器的最大超时值（以秒为单位）。如果设置，则是 'timeout' 的最大可配置值。如果 max_hw_heartbeat_ms 非零，则不使用此值
* min_hw_heartbeat_ms: 硬件限制的两次心跳之间最小时间间隔，以毫秒为单位。这个值通常为 0；只有当硬件不能容忍更短的心跳间隔时才应提供该值
* max_hw_heartbeat_ms: 最大硬件心跳时间，以毫秒为单位。
如果设置，当 'timeout' 大于 max_hw_heartbeat_ms 时，基础设施会向看门狗驱动程序发送心跳信号，
除非设置了 WDOG_ACTIVE 并且用户空间至少在 'timeout' 秒内未能发送心跳信号。如果驱动程序没有实现停止功能，则必须设置 max_hw_heartbeat_ms。

* reboot_nb: 注册用于重启通知的通知块，仅供内部使用。
如果驱动程序调用 watchdog_stop_on_reboot，看门狗核心将在此类通知时停止看门狗。

* restart_nb: 注册用于机器重启的通知块，仅供内部使用。
如果看门狗能够重启机器，它应定义 ops->restart。可以通过 watchdog_set_restart_priority 改变优先级。

* bootstatus: 设备启动后的状态（通过看门狗 WDIOF_* 状态位报告）。

* driver_data: 指向看门狗设备私有数据的指针。
此数据仅应通过 watchdog_set_drvdata 和 watchdog_get_drvdata 函数访问。

* wd_data: 指向看门狗核心内部数据的指针。

* status: 此字段包含一些状态位，提供了关于设备状态的额外信息（例如：看门狗计时器是否正在运行/激活，或者 nowayout 位是否已设置）。

* deferred: 在 wtd_deferred_reg_list 中的条目，用于注册早期初始化的看门狗。
这段代码定义了一个结构体 `watchdog_ops`，用于描述看门狗操作的列表。具体内容如下：

```markdown
结构体 watchdog_ops 定义为：

  struct watchdog_ops {
    struct module *owner; // 模块所有者
    /* 必须的操作 */
    int (*start)(struct watchdog_device *); // 启动看门狗定时器设备
    /* 可选的操作 */
    int (*stop)(struct watchdog_device *); // 停止看门狗定时器设备
    int (*ping)(struct watchdog_device *); // 发送心跳信号到看门狗硬件
    unsigned int (*status)(struct watchdog_device *); // 获取看门狗状态
    int (*set_timeout)(struct watchdog_device *, unsigned int); // 设置超时时间
    int (*set_pretimeout)(struct watchdog_device *, unsigned int); // 设置预超时时间
    unsigned int (*get_timeleft)(struct watchdog_device *); // 获取剩余时间
    int (*restart)(struct watchdog_device *); // 重启看门狗
    long (*ioctl)(struct watchdog_device *, unsigned int, unsigned long); // 输入输出控制
  };

在定义看门狗定时器驱动的操作之前，非常重要的一点是首先定义模块所有者。这个模块所有者将在看门狗激活时锁定模块。（这是为了避免在卸载模块时 `/dev/watchdog` 仍然打开导致系统崩溃）

一些操作是必须的，而另一些则是可选的。必须的操作包括：

- start: 这是指向启动看门狗定时器设备例程的指针
  此例程需要一个指向看门狗定时器设备结构的指针作为参数。成功时返回0，失败时返回负的errno代码

并非所有的看门狗硬件都支持相同的功能。因此，其他例程/操作都是可选的，只需要提供它们被支持时的情况。这些可选的例程/操作包括：

- stop: 使用此例程停止看门狗定时器设备
  此例程需要一个指向看门狗定时器设备结构的指针作为参数。成功时返回0，失败时返回负的errno代码
  有些看门狗硬件只能启动而不能停止。支持此类硬件的驱动程序不必实现 stop 例程
  如果驱动程序没有 stop 函数，则看门狗核心将设置 WDOG_HW_RUNNING，并在关闭看门狗设备后开始调用驱动程序的 keepalive 心跳函数
  如果看门狗驱动程序不实现 stop 函数，它必须设置 max_hw_heartbeat_ms
- ping: 这是指向发送心跳信号到看门狗硬件例程的指针
  此例程需要一个指向看门狗定时器设备结构的指针作为参数。成功时返回0，失败时返回负的errno代码
```

以上是对给定的英文描述进行了翻译。
大部分不支持此功能作为独立操作的硬件会使用启动函数来重启看门狗定时器硬件。这也是看门狗定时器驱动核心所做的：为了向看门狗定时器硬件发送保持活动的心跳信号，它将使用心跳操作（如果可用）或启动操作（当心跳操作不可用时）。
（注：`WDIOC_KEEPALIVE` ioctl 调用仅在看门狗信息结构的选项字段中设置了`WDIOF_KEEPALIVEPING`位时才有效）
* 状态：此例程检查看门狗定时器设备的状态。设备状态通过看门狗`WDIOF_*`状态标志/位报告。`WDIOF_MAGICCLOSE`和`WDIOF_KEEPALIVEPING`由看门狗核心报告；无需从驱动程序报告这些位。此外，如果驱动程序没有提供状态函数，则看门狗核心会报告在`struct watchdog_device`中的`bootstatus`变量中提供的状态位
* 设置超时：此例程检查并更改看门狗定时器设备的超时时间。成功时返回0，"参数超出范围"时返回-EINVAL，"无法向看门狗写入值"时返回-EIO。成功时，此例程应将`watchdog_device`的超时值设置为实际的超时值（这可能与请求的不同，因为看门狗不一定具有1秒的分辨率）
实现`max_hw_heartbeat_ms`的驱动程序将硬件看门狗心跳设置为超时时间和`max_hw_heartbeat_ms`之间的较小值。这些驱动程序将`watchdog_device`的超时值设置为请求的超时值（如果大于`max_hw_heartbeat_ms`），或者设置为实际的超时值
（注：必须在看门狗信息结构的选项字段中设置`WDIOF_SETTIMEOUT`）
如果看门狗驱动程序除了设置`watchdog_device.timeout`外无需执行任何操作，则可以省略此回调
如果没有提供`set_timeout`但设置了`WDIOF_SETTIMEOUT`，则看门狗基础设施会将`watchdog_device`的超时值内部更新为请求的值
如果使用了预超时特性（`WDIOF_PRETIMEOUT`），那么`set_timeout`还必须负责检查预超时是否仍然有效，并相应地设置定时器。这不能在核心中无竞争地完成，因此这是驱动程序的责任。
* `set_pretimeout`: 此例程用于检查并更改看门狗的预超时值。它是可选的，因为并非所有看门狗都支持预超时通知。超时值并不是绝对时间，而是实际超时发生前的秒数。成功时返回0，参数超出范围时返回`-EINVAL`，无法向看门狗写入值时返回`-EIO`。预超时通知值为0表示禁用。
（注：`WDIOF_PRETIMEOUT` 需要在看门狗信息结构的选项字段中设置）
如果看门狗驱动程序除了设置 `watchdog_device.pretimeout` 之外无需执行任何其他操作，则可以省略此回调。这意味着如果未提供 `set_pretimeout` 但设置了 `WDIOF_PRETIMEOUT`，则看门狗基础设施会内部更新 `watchdog_device` 的预超时值至请求的值。

* `get_timeleft`: 此例程返回重置前剩余的时间。

* `restart`: 此例程重启机器。成功时返回0，失败时返回负的errno代码。

* `ioctl`: 如果存在此例程，则在进行我们自己的内部 `ioctl` 调用处理之前首先调用它。对于不支持的命令，此例程应返回 `-ENOIOCTLCMD`。传递给 `ioctl` 调用的参数包括：`watchdog_device`、`cmd` 和 `arg`。

状态位应当（最好）使用类似 `set_bit` 和 `clear_bit` 的位操作来设置。定义的状态位包括：

* `WDOG_ACTIVE`: 此状态位指示从用户角度来看看门狗计时器设备是否处于活动状态。当此标志被设置时，用户空间预计会向驱动程序发送心跳请求。

* `WDOG_NO_WAY_OUT`: 此位存储看门狗的 `nowayout` 设置。如果设置了此位，则看门狗计时器将无法停止。

* `WDOG_HW_RUNNING`: 由看门狗驱动程序设置，表示硬件看门狗正在运行。如果无法停止看门狗计时器硬件，则必须设置该位。在系统启动后、打开看门狗设备之前，如果看门狗计时器正在运行，也可以设置该位。如果设置，当 `WDOG_ACTIVE` 未设置时，看门狗基础设施将继续向看门狗硬件发送保持活跃信号。
注释：当你设置该位并注册看门狗定时器设备时，
  打开 /dev/watchdog 将会跳过启动操作，而是发送一个保持活动请求。
要设置 WDOG_NO_WAY_OUT 状态位（在注册你的看门狗定时器设备之前），你可以：

  * 在你的看门狗设备结构中静态地设置它：

		.status = WATCHDOG_NOWAYOUT_INIT_STATUS,

    （这将设置的值与 CONFIG_WATCHDOG_NOWAYOUT 相同）或者
  * 使用下面的帮助函数：

	static inline void watchdog_set_nowayout(struct watchdog_device *wdd,
						 int nowayout)

注释：
   看门狗定时器驱动核心支持魔术关闭功能和 no way out 特性。要使用魔术关闭功能，你必须在看门狗的信息结构的选项字段中设置 WDIOF_MAGICCLOSE 位。
no way out 特性将会覆盖魔术关闭特性。
为了获取或设置特定于驱动的数据，应该使用以下两个帮助函数：

  static inline void watchdog_set_drvdata(struct watchdog_device *wdd,
					  void *data)
  static inline void *watchdog_get_drvdata(struct watchdog_device *wdd)

watchdog_set_drvdata 函数允许你添加特定于驱动的数据。这个函数的参数是你想要添加特定于驱动数据的看门狗设备以及指向数据本身的指针。
watchdog_get_drvdata 函数允许你检索特定于驱动的数据。这个函数的参数是你想要从中检索数据的看门狗设备。函数返回指向特定于驱动数据的指针。
为了初始化超时字段，可以使用以下函数：

  extern int watchdog_init_timeout(struct watchdog_device *wdd,
                                   unsigned int timeout_parm,
                                   struct device *dev);

watchdog_init_timeout 函数允许你使用模块超时参数或从设备树中获取 timeout-sec 属性来初始化超时字段（如果模块超时参数无效）。最佳做法是在看门狗设备中设置默认超时值作为超时值，并使用此函数设置用户“偏好的”超时值。
此例程成功时返回零，失败时返回一个负的 errno 代码。
为了在重启时禁用看门狗，用户必须调用以下帮助函数：

  static inline void watchdog_stop_on_reboot(struct watchdog_device *wdd);

为了在注销看门狗时禁用看门狗，用户必须调用以下帮助函数。注意，这仅当 no way out 标志未设置时才会停止看门狗。

  static inline void watchdog_stop_on_unregister(struct watchdog_device *wdd);

为了改变重启处理器的优先级，应该使用以下帮助函数：

  void watchdog_set_restart_priority(struct watchdog_device *wdd, int priority);

用户在设置优先级时应遵循以下指南：

* 0: 应该在最后手段下被调用，重启能力有限
* 128: 默认重启处理器，如果预计没有其他处理器可用，或者重启足以重启整个系统，则使用它
* 255: 最高优先级，将抢占所有其他重启处理器

为了发出预超时通知，应该使用以下函数：

  void watchdog_notify_pretimeout(struct watchdog_device *wdd)

可以在中断上下文中调用此函数。如果启用了看门狗预超时管理框架（kbuild CONFIG_WATCHDOG_PRETIMEOUT_GOV 符号），则由预先配置并分配给看门狗设备的预超时管理器采取行动。如果没有启用看门狗预超时管理框架，watchdog_notify_pretimeout() 向内核日志缓冲区打印一条通知消息。
为了设置已知的最后一个硬件心跳时间给监视定时器（watchdog），应使用以下函数：

```c
int watchdog_set_last_hw_keepalive(struct watchdog_device *wdd,
                                     unsigned int last_ping_ms)
```

此函数必须在监视定时器注册后立即调用。它将已知的最后一次硬件心跳时间设置为当前时间之前的`last_ping_ms`毫秒。只有在满足以下条件时才需要调用此函数：当`probe`被调用时，监视定时器已经在运行，并且从上一次心跳之后至少已经过去了`min_hw_heartbeat_ms`的时间，此时才能对监视定时器进行心跳操作。
