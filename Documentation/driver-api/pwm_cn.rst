脉冲宽度调制 (PWM) 接口
==========================

本节提供关于 Linux PWM 接口的概述。

PWM 常用于控制 LED、风扇或手机中的振动器。具有固定用途的 PWM 可能不需要实现 Linux PWM API（尽管它们也可以）。然而，作为 SoC 上的独立设备，PWM 经常没有固定的用途。由电路板设计者决定将其连接到 LED 还是风扇。为了提供这种灵活性，存在通用的 PWM API。
识别 PWM
---------

使用旧版 PWM API 的用户通过唯一 ID 来引用 PWM 设备。而不是通过其唯一 ID 引用 PWM 设备，电路板设置代码应注册一个静态映射，用于匹配 PWM 消费者和提供者，如下例所示：

```c
static struct pwm_lookup board_pwm_lookup[] = {
		PWM_LOOKUP("tegra-pwm", 0, "pwm-backlight", NULL,
		           50000, PWM_POLARITY_NORMAL),
	};

	static void __init board_init(void)
	{
		..
		pwm_add_table(board_pwm_lookup, ARRAY_SIZE(board_pwm_lookup));
		..
}
```

使用 PWM
--------

消费者使用 `pwm_get()` 函数，并向其传递消费设备或消费名称。`pwm_put()` 用于释放 PWM 设备。还存在管理版本的获取函数 `devm_pwm_get()` 和 `devm_fwnode_pwm_get()`。

请求后，必须使用以下函数配置 PWM：

```c
int pwm_apply_might_sleep(struct pwm_device *pwm, struct pwm_state *state);
```

此 API 同时控制 PWM 周期/占空比配置以及启用/禁用状态。

如果 PWM 不休眠，则可以从原子上下文使用 PWM。可以通过以下函数检查是否适用：

```c
bool pwm_might_sleep(struct pwm_device *pwm);
```

如果返回 false，则也可以从原子上下文中配置 PWM：

```c
int pwm_apply_atomic(struct pwm_device *pwm, struct pwm_state *state);
```

作为消费者，不要依赖于禁用的 PWM 输出的状态。如果可能，驱动程序应该输出非活动状态，但有些驱动程序不能。如果你依赖于获取非活动状态，请使用 `.duty_cycle=0, .enabled=true`。

还有一个 `usage_power` 设置：如果设置，PWM 驱动程序仅需维持功率输出，但在信号形式方面有更多自由度。

如果驱动程序支持，可以优化信号，例如通过相移芯片各个通道来改善 EMI。

`pwm_config()`、`pwm_enable()` 和 `pwm_disable()` 函数只是 `pwm_apply_might_sleep()` 的包装器，如果用户希望一次更改多个参数，则不应使用这些函数。例如，在同一函数中看到 `pwm_config()` 和 `pwm_{enable,disable}()` 调用可能意味着你应该改为使用 `pwm_apply_might_sleep()`。
PWM 用户 API 还允许查询通过 `pwm_apply_might_sleep()` 最后调用时传递的 PWM 状态，使用 `pwm_get_state()` 函数。请注意，这与驱动程序实际实现的状态不同，如果请求无法完全通过所使用的硬件满足的话。目前没有方法可以让使用者获取到实际实施的设置。

除了 PWM 状态之外，PWM API 还提供了 PWM 参数，这些参数是应该在这个 PWM 上使用的参考 PWM 配置。
PWM 参数通常是平台特定的，并允许 PWM 使用者只关心相对于整个周期的占空比（例如，占空比 = 周期的 50%）。`struct pwm_args` 包含两个字段（周期和极性），并应用于设置初始的 PWM 配置（通常在 PWM 使用者的探测函数中完成）。PWM 参数可以通过 `pwm_get_args()` 获取。

所有使用者在恢复时确实都应该根据需要重新配置 PWM。这是确保一切按正确顺序恢复的唯一方式。

### 使用 sysfs 接口的 PWM

如果内核配置中启用了 `CONFIG_SYSFS`，将提供一个简单的 sysfs 接口来从用户空间使用 PWM。它暴露在 `/sys/class/pwm/` 下。每个探测到的 PWM 控制器/芯片将被导出为 `pwmchipN`，其中 N 是 PWM 芯片的基础。在目录内部，你将找到：

  - `npwm`
    此芯片支持的 PWM 通道数（只读）
  - `export`
    导出用于 sysfs 的 PWM 通道（写入）
  - `unexport`
    从 sysfs 取消导出 PWM 通道（写入）

PWM 通道使用从 0 到 npwm-1 的每芯片索引进行编号。

当一个 PWM 通道被导出时，在其关联的 `pwmchipN` 目录中会创建一个名为 `pwmX` 的目录，其中 X 是已导出通道的编号。接下来可以访问以下属性：

  - `period`
    PWM 信号的总周期（可读/写）
值以纳秒表示，是 PWM 激活时间和非激活时间之和。
### 脉冲宽度调制 (PWM) 驱动器相关术语的中文翻译：

- **duty_cycle**  
  **占空比**  
  PWM 信号的有效时间（可读/可写）  
  值以纳秒为单位，必须小于或等于周期。

- **polarity**  
  **极性**  
  改变 PWM 信号的极性（可读/可写）  
  只有在 PWM 芯片支持改变极性的情况下，对该属性的写入才有效。  
  值为字符串 "normal" 或 "inversed"。

- **enable**  
  **启用/禁用**  
  启用/禁用 PWM 信号（可读/可写）  
  - 0 - 禁用  
  - 1 - 启用  

### 实现 PWM 驱动器

目前有两种方法来实现 PWM 驱动器。传统上，只有基础 API 的存在意味着每个驱动器都必须自己实现 pwm_*() 函数。这意味着系统中不可能同时拥有多个 PWM 驱动器。因此，对于新的驱动器来说，使用通用 PWM 框架是强制性的。

一个新的 PWM 控制器/芯片可以通过 `pwmchip_alloc()` 分配，然后通过 `pwmchip_add()` 注册，并且可以使用 `pwmchip_remove()` 移除。如果要撤销 `pwmchip_alloc()` 的操作，则使用 `pwmchip_put()`。`pwmchip_add()` 需要一个填充好的 `struct pwm_chip` 结构体作为参数，它提供了关于 PWM 芯片的描述、芯片提供的 PWM 设备数量以及芯片特定的 PWM 操作实现。

当在 PWM 驱动器中实现极性支持时，请确保遵守 PWM 框架中的信号约定。根据定义，正常极性指的是信号在占空比期间处于高电平，在剩余周期内处于低电平。相反，具有反向极性的信号在占空比期间处于低电平，在剩余周期内处于高电平。

鼓励驱动器实现 `->apply()` 方法而不是传统的 `->enable()`, `->disable()` 和 `->config()` 方法。这样做应该能够提供 PWM 配置工作流中的原子性，这对于控制关键设备（如电源调节器）的 PWM 是必需的。
实现`->get_state()`（一个用于检索初始PWM状态的方法）也是被鼓励的，原因相同：让PWM用户了解当前PWM的状态可以让他们避免出现故障。

驱动程序不应实现任何电源管理功能。换句话说，消费者应按照“使用PWM”部分所述来实现电源管理。

锁定
----

PWM核心列表操作受到互斥锁保护，因此`pwm_get()`和`pwm_put()`不能从原子上下文中调用。目前PWM核心不对`pwm_enable()`、`pwm_disable()`和`pwm_config()`进行任何锁定强制，因此调用上下文目前是驱动程序特定的。这是一个源自于先前基本API的问题，并且应该很快得到解决。

辅助函数
----

目前，PWM只能通过`period_ns`和`duty_ns`配置。对于许多应用场景而言，使用`freq_hz`和`duty_percent`可能更加合适。而不是在你的驱动程序中进行这些计算，请考虑为框架添加合适的辅助函数。
