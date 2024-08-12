SPDX 许可证标识符: GPL-2.0

CEC 内核支持
=============

CEC 框架为 HDMI CEC 硬件提供了一个统一的内核接口。它被设计来处理多种类型的硬件（接收器、发射器、USB 适配器等）。该框架还提供了选择在内核驱动程序中执行什么操作以及什么应该由用户空间应用程序处理的选项。此外，它还将遥控器透传功能集成到内核的遥控框架中。

CEC 协议
---------

CEC 协议使消费者电子设备能够通过 HDMI 连接相互通信。该协议使用逻辑地址进行通信。逻辑地址严格与设备提供的功能相关联。作为通信中心的电视总是分配地址 0。物理地址由设备之间的物理连接确定。
此处描述的 CEC 框架遵循 CEC 2.0 规范。它记录在 HDMI 1.4 规范中，新的 2.0 位则记录在 HDMI 2.0 规范中。但对于大多数功能来说，免费可用的 HDMI 1.3a 规范就足够了：

https://www.hdmi.org/spec/index

CEC 适配器接口
---------------

`struct cec_adapter` 表示 CEC 适配器硬件。它通过调用 `cec_allocate_adapter()` 创建，并通过调用 `cec_delete_adapter()` 删除：

```c
struct cec_adapter *cec_allocate_adapter(const struct cec_adap_ops *ops, void *priv, const char *name, u32 caps, u8 available_las);
void cec_delete_adapter(struct cec_adapter *adap);
```

为了创建一个适配器，你需要传递以下信息：

`ops`:
    适配器操作，这些操作将由 CEC 框架调用，且你必须实现它们。
`priv`:
    将存储在 `adap->priv` 中，可用于适配器操作。使用 `cec_get_drvdata(adap)` 获取 `priv` 指针。
`name`:
    CEC 适配器的名称。注意：这个名称将会被复制。
`caps`:
    CEC 适配器的能力。这些能力决定了硬件的能力以及哪些部分应由用户空间处理，哪些部分由内核空间处理。这些能力可以通过 `CEC_ADAP_G_CAPS` 获取。
`available_las`:
    此适配器可以同时处理的逻辑地址数量。必须满足 1 <= available_las <= CEC_MAX_LOG_ADDRS。

要获取 `priv` 指针，请使用此辅助函数：

```c
void *cec_get_drvdata(const struct cec_adapter *adap);
```

若要注册 `/dev/cecX` 设备节点和遥控设备（如果设置了 `CEC_CAP_RC`），请调用：

```c
int cec_register_adapter(struct cec_adapter *adap, struct device *parent);
```

其中 `parent` 是父设备。
要取消注册设备，请调用：

.. c:function::
    void cec_unregister_adapter(struct cec_adapter *adap);

注意：如果 `cec_register_adapter()` 失败，则应调用 `cec_delete_adapter()` 进行清理。但如果 `cec_register_adapter()` 成功，则只应调用 `cec_unregister_adapter()` 进行清理，绝不要调用 `cec_delete_adapter()`。`unregister` 函数会在最后一个 `/dev/cecX` 设备的使用者关闭其文件句柄后自动删除适配器。

实现低级 CEC 适配器
----------------------

以下低级适配器操作需要在您的驱动程序中实现：

.. c:struct:: cec_adap_ops

.. code-block:: none

    struct cec_adap_ops {
        /* 低级回调函数 */
        int (*adap_enable)(struct cec_adapter *adap, bool enable);
        int (*adap_monitor_all_enable)(struct cec_adapter *adap, bool enable);
        int (*adap_monitor_pin_enable)(struct cec_adapter *adap, bool enable);
        int (*adap_log_addr)(struct cec_adapter *adap, u8 logical_addr);
        void (*adap_unconfigured)(struct cec_adapter *adap);
        int (*adap_transmit)(struct cec_adapter *adap, u8 attempts,
                             u32 signal_free_time, struct cec_msg *msg);
        void (*adap_nb_transmit_canceled)(struct cec_adapter *adap,
                                          const struct cec_msg *msg);
        void (*adap_status)(struct cec_adapter *adap, struct seq_file *file);
        void (*adap_free)(struct cec_adapter *adap);

        /* 错误注入回调函数 */
        ..
        /* 高级回调函数 */
        ..
    };

这些低级操作处理控制 CEC 适配器硬件的各个方面。当持有互斥锁 `adap->lock` 时会调用它们。
为了启用或禁用硬件：

```c
int (*adap_enable)(struct cec_adapter *adap, bool enable);
```

此回调函数用于启用或禁用 CEC 硬件。启用 CEC 硬件意味着将其启动到一个没有任何逻辑地址被声明的状态。如果设置了 `CEC_CAP_NEEDS_HPD` 标志，则物理地址始终有效。如果没有设置该标志，则物理地址可能在 CEC 硬件启用期间发生变化。除非硬件设计要求这样做，否则 CEC 驱动程序不应设置 `CEC_CAP_NEEDS_HPD` 标志，因为这将使得无法唤醒在待机模式下将 HPD 拉低的显示器。在调用 `cec_allocate_adapter()` 之后，CEC 适配器的初始状态为禁用。
请注意，当 `enable` 为假时，`adap_enable` 必须返回 0。
为了启用或禁用“监控所有”模式：

```c
int (*adap_monitor_all_enable)(struct cec_adapter *adap, bool enable);
```

如果启用了该模式，则适配器应置于可以监控并非发给我们的消息的模式。不是所有的硬件都支持这种模式，并且仅在设置了 `CEC_CAP_MONITOR_ALL` 能力时才会调用这个函数。此回调是可选的（某些硬件可能总是处于“监控所有”模式）。
请注意，当 `enable` 为假时，`adap_monitor_all_enable` 必须返回 0。
为了启用或禁用“监控引脚”模式：

```c
int (*adap_monitor_pin_enable)(struct cec_adapter *adap, bool enable);
```

如果启用了该模式，则适配器应置于可以监控 CEC 引脚变化的模式。不是所有的硬件都支持这种模式，并且仅在设置了 `CEC_CAP_MONITOR_PIN` 能力时才会调用这个函数。此回调是可选的（某些硬件可能总是处于“监控引脚”模式）。
请注意，当 `enable` 为假时，`adap_monitor_pin_enable` 必须返回 0。
为了设置一个新的逻辑地址：

    ```c
    int (*adap_log_addr)(struct cec_adapter *adap, u8 logical_addr);
    ```

如果 `logical_addr` 的值为 `CEC_LOG_ADDR_INVALID`，则所有已设置的逻辑地址应被清除。否则，应设置给定的逻辑地址。如果超过可用的最大逻辑地址数量，则应当返回 `-ENXIO`。一旦一个逻辑地址被设置，CEC硬件就可以接收指向该地址的定向消息。
注意：当 `logical_addr` 是 `CEC_LOG_ADDR_INVALID` 时，`adap_log_addr` 必须返回 `0`。
在适配器未配置时调用：

    ```c
    void (*adap_unconfigured)(struct cec_adapter *adap);
    ```

适配器处于未配置状态。如果驱动程序需要在未配置后执行特定的操作，则可以通过这个可选回调来完成。
为了传输一条新消息：

    ```c
    int (*adap_transmit)(struct cec_adapter *adap, u8 attempts,
			 u32 signal_free_time, struct cec_msg *msg);
    ```

这用于传输一条新消息。`attempts` 参数是建议的传输尝试次数。
`signal_free_time` 是适配器在检测到线路空闲后等待的时间（以数据位周期计），然后再尝试发送消息。这个值取决于本次传输是否为重试、新的发起者的消息还是同一发起者的另一条新消息。大多数硬件会自动处理这种情况，但在某些情况下，需要这些信息。
可以使用 `CEC_FREE_TIME_TO_USEC` 宏将 `signal_free_time` 转换为微秒（一个数据位周期为 2.4 毫秒）。
为了传递取消的非阻塞传输的结果：

    ```c
    void (*adap_nb_transmit_canceled)(struct cec_adapter *adap,
					const struct cec_msg *msg);
    ```

这个可选回调可以用来获取序列号为 `msg->sequence` 的取消的非阻塞传输的结果。如果传输被中止、传输超时（即硬件从未指示传输完成）、或者传输成功但等待预期回复的过程被中止或超时，则会调用此函数。
为了记录当前 CEC 硬件的状态：

    ```c
    void (*adap_status)(struct cec_adapter *adap, struct seq_file *file);
    ```

这个可选回调可以用来展示 CEC 硬件的状态。状态信息可以通过 debugfs 获取：`cat /sys/kernel/debug/cec/cecX/status`
在删除适配器时释放任何资源：

    ```c
    void (*adap_free)(struct cec_adapter *adap);
    ```

这个可选回调可以用来释放驱动程序可能分配的任何资源。它在 `cec_delete_adapter` 函数中被调用。
您的适配器驱动程序还需要对事件（通常是由中断触发的）作出反应，通过在以下情况下调用框架：

当传输完成（无论成功与否）时： 

```c
void cec_transmit_done(struct cec_adapter *adap, u8 status,
			       u8 arb_lost_cnt,  u8 nack_cnt, u8 low_drive_cnt,
			       u8 error_cnt);
```

或者：

```c
void cec_transmit_attempt_done(struct cec_adapter *adap, u8 status);
```

状态可以是以下之一：

`CEC_TX_STATUS_OK`:  
传输成功

`CEC_TX_STATUS_ARB_LOST`:  
仲裁失败：另一个CEC发起者控制了CEC线路，并且您在仲裁中失败

`CEC_TX_STATUS_NACK`:  
消息被否定确认（对于定向消息）或被确认（对于广播消息）。需要重新传输

`CEC_TX_STATUS_LOW_DRIVE`:  
CEC总线上检测到低驱动。这表明跟随者在总线上检测到了错误并请求重新传输

`CEC_TX_STATUS_ERROR`:  
发生了某种未指定的错误：这可能是ARB_LOST或LOW_DRIVE其中之一，如果硬件无法区分，或者是其他某种情况。有些硬件仅支持OK和FAIL作为传输的结果，即无法区分各种可能的错误。在这种情况下，将FAIL映射为`CEC_TX_STATUS_NACK`而不是`CEC_TX_STATUS_ERROR`

`CEC_TX_STATUS_MAX_RETRIES`:  
尝试多次后仍无法传输该消息  
仅当驱动程序具有硬件重试支持时才应设置此状态。如果设置了，则框架会假设它不需要再次尝试传输消息，因为硬件已经完成了这一操作

硬件必须能够区分OK、NACK以及“其他”
\*_cnt参数是指观察到的错误条件的数量  
如果没有可用的信息，这些值可以为0。不支持硬件重试的驱动程序可以将与传输错误相对应的计数器设置为1，如果硬件支持重试，则如果硬件没有提供发生哪些错误以及发生次数的反馈，则可以将这些计数器设置为0，或者根据硬件报告的正确值填写。
```
请注意，调用这些函数可能会立即开始一个新的传输操作，
如果队列中有一个待处理的传输任务。因此，在调用这些函数之前，
请确保硬件处于可以开始新传输的状态。
`cec_transmit_attempt_done()` 函数适用于硬件从不重试的情况，
即传输总是只尝试一次。它会反过来调用 `cec_transmit_done()`，
并将计数参数设置为 1 来表示状态。如果状态正常，则全部设为 0。

当接收到一个 CEC 消息时：

.. c:function::
    void cec_received_msg(struct cec_adapter *adap, struct cec_msg *msg);

这个函数自解释。

实现中断处理程序
-------------------

通常，CEC 硬件提供中断来指示传输完成及其是否成功，
并且在接收到 CEC 消息时也提供中断。
CEC 驱动应始终先处理传输中断，然后再处理接收中断。
框架期望看到 `cec_transmit_done` 的调用出现在 `cec_received_msg` 调用之前，
否则如果接收到的消息是作为已发送消息的响应，框架可能会混淆。

可选：实现错误注入支持
------------------------------

如果 CEC 适配器支持错误注入功能，则可以通过以下错误注入回调接口将其暴露出来：

.. code-block:: none

    struct cec_adap_ops {
        /* 低级回调函数 */
        ..
        /* 错误注入回调函数 */
        int (*error_inj_show)(struct cec_adapter *adap, struct seq_file *sf);
        bool (*error_inj_parse_line)(struct cec_adapter *adap, char *line);

        /* 高级 CEC 消息回调函数 */
        ..
    };

如果设置了这两个回调函数，那么在调试文件系统(debugfs)中将出现一个名为“error-inj”的文件。
基本语法如下：

前导空格或制表符会被忽略。如果下一个字符是“#”或者到达行尾，则忽略整行。否则，预期是一个命令。
这种基础解析由 CEC 框架完成。驱动程序需要决定要实现哪些命令。唯一的要求是必须实现不带任何参数的命令 `clear`，
并且该命令会清除所有当前的错误注入命令。
这确保了您可以始终执行 `echo clear >error-inj` 来清除任何错误注入，而无需了解特定于驱动程序命令的详细信息。请注意 `error-inj` 的输出应当作为 `error-inj` 的输入是有效的。因此，以下操作必须可行：

```plaintext
$ cat error-inj >einj.txt
$ cat einj.txt >error-inj
```

当读取此文件时会调用第一个回调函数，并且应该显示当前的错误注入状态：
```c
int (*error_inj_show)(struct cec_adapter *adap, struct seq_file *sf);
```

建议该回调以包含基本使用信息的注释块开始。成功返回0，否则返回错误。
第二个回调将解析写入 `error-inj` 文件的命令：
```c
bool (*error_inj_parse_line)(struct cec_adapter *adap, char *line);
```

`line` 参数指向命令的起始位置。任何前导空格或制表符已经被跳过。它只是一行（因此没有嵌入的新行），并且以0结尾。回调可以自由修改缓冲区的内容。仅对包含命令的行调用此回调，因此此回调不会为空白行或注释行调用。
如果命令有效则返回true，如果存在语法错误则返回false。

实现高级CEC适配器
------------------------

低级操作驱动硬件，而高级操作由CEC协议驱动。在不持有 adap->lock 互斥锁的情况下调用高级回调。可用的高级回调如下：

```plaintext
struct cec_adap_ops {
    /* 低级回调 */
    ..
    /* 错误注入回调 */
    ..
    /* 高级CEC消息回调 */
    void (*configured)(struct cec_adapter *adap);
    int (*received)(struct cec_adapter *adap, struct cec_msg *msg);
};
```

当适配器配置完成时调用：
```c
void (*configured)(struct cec_adapter *adap);
```

适配器已完全配置，即所有逻辑地址均已被成功声明。如果驱动程序需要在配置后执行特定的操作，则可以通过此可选回调进行。

`received()` 回调允许驱动程序选择性地处理新接收的CEC消息：
```c
int (*received)(struct cec_adapter *adap, struct cec_msg *msg);
```

如果驱动程序想要处理一个CEC消息，它可以实现这个回调。如果不希望处理此消息，则应返回 `-ENOMSG`，否则CEC框架认为已处理此消息，并不再对其进行任何操作。

CEC框架函数
------------------------

CEC适配器驱动程序可以调用以下CEC框架函数：

```c
int cec_transmit_msg(struct cec_adapter *adap, struct cec_msg *msg, bool block);
```

传输一个CEC消息。如果 `block` 为真，则等待消息被发送完毕，否则只是将其排队并返回。
### c:function:: 
```c
void cec_s_phys_addr(struct cec_adapter *adap, u16 phys_addr, bool block);
```

更改物理地址。此函数将设置 `adap->phys_addr` 并在地址发生变化时发送事件。如果已调用 `cec_s_log_addrs()` 并且物理地址已变为有效，则 CEC 框架将开始声明逻辑地址。如果 `block` 为真，则此函数不会返回，直到这一过程完成。

当物理地址设置为有效值时，CEC 适配器将被启用（参见 `adap_enable` 操作）。当它被设置为 `CEC_PHYS_ADDR_INVALID` 时，CEC 适配器将被禁用。如果你将一个有效的物理地址更改为另一个有效的物理地址，此函数将首先将地址设置为 `CEC_PHYS_ADDR_INVALID`，然后启用新的物理地址。

### c:function:: 
```c
void cec_s_phys_addr_from_edid(struct cec_adapter *adap, const struct edid *edid);
```

这是一个辅助函数，用于从 `edid` 结构中提取物理地址，并使用该地址或 `CEC_PHYS_ADDR_INVALID`（如果 EDID 不包含物理地址或 `edid` 是空指针）调用 `cec_s_phys_addr()`。

### c:function:: 
```c
int cec_s_log_addrs(struct cec_adapter *adap, struct cec_log_addrs *log_addrs, bool block);
```

声明 CEC 逻辑地址。如果设置了 `CEC_CAP_LOG_ADDRS`，则不应调用此函数。如果 `block` 为真，则等待逻辑地址已被声明，否则仅将其排队并返回。要取消配置所有逻辑地址，请通过将 `log_addrs` 设置为 NULL 或将 `log_addrs->num_log_addrs` 设置为 0 来调用此函数。在取消配置时会忽略 `block` 参数。如果物理地址无效，此函数将直接返回。一旦物理地址变得有效，框架将尝试声明这些逻辑地址。

### CEC Pin 框架

大多数 CEC 硬件处理完整的 CEC 消息，其中软件提供消息而硬件处理低级别的 CEC 协议。但有些硬件只驱动 CEC 引脚，需要软件来处理低级别的 CEC 协议。CEC 引脚框架就是为了处理这类设备而创建的。

请注意，由于接近实时的要求，无法保证其100%的工作效果。此框架内部使用高分辨率计时器，但如果计时器延迟超过 300 微秒可能会导致错误的结果。实际上，它的可靠性似乎相当不错。

这种低级别实现的一个优点是它可以作为廉价的 CEC 分析仪使用，特别是在可以使用中断检测 CEC 引脚从低到高或反之的转换时。

### CEC Notifier 框架

大多数 DRM HDMI 实现都有集成的 CEC 实现，不需要通知器支持。但有些拥有独立的 CEC 实现，它们有自己的驱动程序。这可能是一个 SoC 的 IP 块或一个完全独立的芯片来处理 CEC 引脚。对于这些情况，DRM 驱动程序可以安装一个通知器，并使用通知器向 CEC 驱动程序通知物理地址的变化。
