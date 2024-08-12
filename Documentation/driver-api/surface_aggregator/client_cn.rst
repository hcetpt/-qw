### SPDX 许可证标识符: GPL-2.0+

### 定义:
- `ssam_controller` |ssam_controller| : C 类型 `struct ssam_controller <ssam_controller>`
- `ssam_device` |ssam_device| : C 类型 `struct ssam_device <ssam_device>`
- `ssam_device_driver` |ssam_device_driver| : C 类型 `struct ssam_device_driver <ssam_device_driver>`
- `ssam_client_bind` |ssam_client_bind| : C 函数 `ssam_client_bind`
- `ssam_client_link` |ssam_client_link| : C 函数 `ssam_client_link`
- `ssam_get_controller` |ssam_get_controller| : C 函数 `ssam_get_controller`
- `ssam_controller_get` |ssam_controller_get| : C 函数 `ssam_controller_get`
- `ssam_controller_put` |ssam_controller_put| : C 函数 `ssam_controller_put`
- `ssam_device_alloc` |ssam_device_alloc| : C 函数 `ssam_device_alloc`
- `ssam_device_add` |ssam_device_add| : C 函数 `ssam_device_add`
- `ssam_device_remove` |ssam_device_remove| : C 函数 `ssam_device_remove`
- `ssam_device_driver_register` |ssam_device_driver_register| : C 函数 `ssam_device_driver_register`
- `ssam_device_driver_unregister` |ssam_device_driver_unregister| : C 函数 `ssam_device_driver_unregister`
- `module_ssam_device_driver` |module_ssam_device_driver| : C 函数 `module_ssam_device_driver`
- `SSAM_DEVICE` |SSAM_DEVICE| : C 函数 `SSAM_DEVICE`
- `ssam_notifier_register` |ssam_notifier_register| : C 函数 `ssam_notifier_register`
- `ssam_notifier_unregister` |ssam_notifier_unregister| : C 函数 `ssam_notifier_unregister`
- `ssam_device_notifier_register` |ssam_device_notifier_register| : C 函数 `ssam_device_notifier_register`
- `ssam_device_notifier_unregister` |ssam_device_notifier_unregister| : C 函数 `ssam_device_notifier_unregister`
- `ssam_request_do_sync` |ssam_request_do_sync| : C 函数 `ssam_request_do_sync`
- `ssam_event_mask` |ssam_event_mask| : C 类型 `enum ssam_event_mask <ssam_event_mask>`

### 编写客户端驱动程序

对于 API 文档，请参阅:

- [客户端 API](client-api)

#### 概览

客户端驱动程序可以通过两种主要方式设置，具体取决于相应的设备如何提供给系统。我们特别区分了通过传统方式呈现给系统的设备（例如通过 ACPI 作为平台设备），以及那些不可发现且需要通过其他机制明确提供的设备，如下文“非 SSAM 客户端驱动程序”中进一步讨论。

### 非 SSAM 客户端驱动程序

所有与 SAM EC 的通信都是通过 |ssam_controller| 进行的，该控制器代表 EC 向内核展示。针对非 SSAM 设备（因此不是 |ssam_device_driver|）的驱动程序需要显式地建立与该控制器的连接/关系。这可以通过 |ssam_client_bind| 函数完成。此函数返回对 SSAM 控制器的引用，但更重要的是，它还在客户端设备和控制器之间建立了设备链接（也可以通过 |ssam_client_link| 单独完成）。这样做很重要，首先保证返回的控制器在客户端驱动程序绑定到其设备期间有效使用，即在控制器失效之前，驱动程序会先解绑；其次确保正确的挂起/恢复顺序。此设置应在驱动程序的 probe 函数中完成，并且可以在 SSAM 子系统尚未准备好的情况下用于推迟探测，例如：

```c
static int client_driver_probe(struct platform_device *pdev)
{
        struct ssam_controller *ctrl;

        ctrl = ssam_client_bind(&pdev->dev);
        if (IS_ERR(ctrl))
                return PTR_ERR(ctrl) == -ENODEV ? -EPROBE_DEFER : PTR_ERR(ctrl);

        // ...
        return 0;
}
```

可以通过 |ssam_get_controller| 单独获取控制器，并通过 |ssam_controller_get| 和 |ssam_controller_put| 保证其生命周期。需要注意的是，这些函数都不能保证控制器不会被关闭或挂起。这些函数基本上只操作引用，即仅保证最低限度的可访问性，而对实际可操作性没有任何保证。

### 添加 SSAM 设备

如果一个设备不存在或未通过传统方式提供，则应通过 SSAM 客户端设备中心将其作为 |ssam_device| 提供。可以将新设备添加到相应的注册表中。SSAM 设备也可以通过 |ssam_device_alloc| 手动分配，随后必须通过 |ssam_device_add| 添加，并最终通过 |ssam_device_remove| 移除。默认情况下，设备的父设备被设置为用于分配的控制器设备，但是可以在添加设备前更改父设备。更改父设备时，必须注意确保控制器生命周期和挂起/恢复顺序保证（默认设置通过父子关系提供）得到保留。如有必要，可以使用 |ssam_client_link|，就像为非 SSAM 客户端驱动程序所做的一样，如上文所述。

客户端设备必须始终由添加相应设备的一方在控制器关闭之前移除。这种移除可以通过将提供 SSAM 设备的驱动程序链接到控制器来保证，导致它在控制器驱动程序解绑之前解绑。以控制器作为父设备注册的客户端设备在控制器关闭时会被自动移除，但不应依赖于此，特别是这不适用于具有不同父设备的客户端设备。

### SSAM 客户端驱动程序

本质上，SSAM 客户端设备驱动程序与其他类型的设备驱动程序没有区别。它们通过 |ssam_device_driver| 表示，并通过其 UID (`struct ssam_device.uid <ssam_device>`) 成员和匹配表 (`struct ssam_device_driver.match_table <ssam_device_driver>`) 绑定到 |ssam_device|。在声明驱动结构实例时应设置匹配表。有关如何定义驱动程序匹配表成员的更多详细信息，请参阅 |SSAM_DEVICE| 宏文档。

SSAM 客户端设备的 UID 包括“域”、“类别”、“目标”、“实例”和“功能”。`domain` 用于区分物理 SAM 设备（`SSAM_DOMAIN_SERIALHUB <ssam_device_domain>`），即可以通过 Surface 串行集线器访问的设备，以及虚拟设备（`SSAM_DOMAIN_VIRTUAL <ssam_device_domain>`），例如客户端设备中心，这些设备在 SAM EC 上没有真实的表示，仅在内核/驱动程序侧使用。对于物理设备，“类别”表示目标类别，“目标”表示目标 ID，“实例”表示用于访问物理 SAM 设备的实例 ID。此外，“功能”引用特定设备功能，但对 SAM EC 没有意义。客户端设备的（默认）名称是基于其 UID 生成的。

驱动程序实例可以通过 |ssam_device_driver_register| 注册，并通过 |ssam_device_driver_unregister| 解注册。为了方便起见，可以使用 |module_ssam_device_driver| 宏定义模块初始化和退出函数来注册驱动程序。

与 SSAM 客户端设备关联的控制器可以在其 `struct ssam_device.ctrl <ssam_device>` 成员中找到。此引用至少在客户端驱动程序绑定期间有效，但在客户端设备存在期间也应该是有效的。然而，在绑定客户端驱动程序之外访问时，必须确保控制器设备在进行任何请求或（取消）注册事件通知器时未被挂起（因此通常应避免）。当从绑定的客户端驱动程序内部访问控制器时，这是有保证的。
### 发起同步请求

同步请求（目前）是主机与EC进行通信的主要形式。有几种方式可以定义和执行此类请求，但大多数最终都会简化为类似下面示例中的内容。此示例定义了一个写-读请求，即调用者向SAM EC提供一个参数并接收响应。调用者需要知道响应负载（最大）长度，并为此提供缓冲区。
必须注意的是，传递给SAM EC的任何命令负载数据都应采用小端格式，并且类似地，从它接收到的任何响应负载数据都需要从小端格式转换为主机字节序。
```c
int perform_request(struct ssam_controller *ctrl, u32 arg, u32 *ret)
{
    struct ssam_request rqst;
    struct ssam_response resp;
    int status;

    /* 将请求参数转换为小端格式。 */
    __le32 arg_le = cpu_to_le32(arg);
    __le32 ret_le = cpu_to_le32(0);

    /*
     * 初始化请求规范。请用您的值替换这里的内容
     * 如果rqst.length为零，则rqst.payload字段可以为NULL，
     * 表示请求没有参数
     *
     * 注意：这里使用的请求参数无效，即它们不代表实际的SAM/EC请求
     */
    rqst.target_category = SSAM_SSH_TC_SAM;
    rqst.target_id = SSAM_SSH_TID_SAM;
    rqst.command_id = 0x02;
    rqst.instance_id = 0x03;
    rqst.flags = SSAM_REQUEST_HAS_RESPONSE;
    rqst.length = sizeof(arg_le);
    rqst.payload = (u8 *)&arg_le;

    /* 初始化请求响应。 */
    resp.capacity = sizeof(ret_le);
    resp.length = 0;
    resp.pointer = (u8 *)&ret_le;

    /*
     * 执行实际请求。如果请求没有响应，则响应指针可以为null。
     * 这必须与上面规范中设置的SSAM_REQUEST_HAS_RESPONSE标志一致
     */
    status = ssam_request_do_sync(ctrl, &rqst, &resp);

    /*
     * 或者使用
     *
     *   ssam_request_do_sync_onstack(ctrl, &rqst, &resp, sizeof(arg_le));
     *
     * 来执行请求，直接在栈上分配消息缓冲区，而不是通过kzalloc()分配
     */

    /*
     * 将请求响应转换回本机格式。请注意，在错误情况下，
     * 此值不会被SSAM核心所修改，即
     */ 
```
* `ret_le` 将会按照初始化时的规定被置零
*/
           *ret = le32_to_cpu(ret_le);

           return status;
   }

请注意，本质上 `ssam_request_do_sync` 是对更低层级请求原语的封装，这些原语也可以用来执行请求。请参阅其实现和文档以获取更多细节。
一种可能更为用户友好的定义此类函数的方法是使用生成宏，例如：

.. code-block:: c

   SSAM_DEFINE_SYNC_REQUEST_W(__ssam_tmp_perf_mode_set, __le32, {
           .target_category = SSAM_SSH_TC_TMP,
           .target_id       = SSAM_SSH_TID_SAM,
           .command_id      = 0x03,
           .instance_id     = 0x00,
   });

这个例子定义了一个函数

.. code-block:: c

   static int __ssam_tmp_perf_mode_set(struct ssam_controller *ctrl, const __le32 *arg);

该函数执行指定的请求，并在调用时传递控制器。在这个例子中，参数通过 `arg` 指针提供。需要注意的是，生成的函数在栈上分配消息缓冲区。因此，如果通过请求提供的参数很大，则应避免使用这类宏。此外，与之前非宏示例中的函数不同，此函数不进行字节序转换，这需要由调用者处理。除此之外，由宏生成的函数与上面非宏示例中的函数相似。
此类函数生成宏的完整列表如下：

- :c:func:`SSAM_DEFINE_SYNC_REQUEST_N` 用于没有返回值且无参数的请求
- :c:func:`SSAM_DEFINE_SYNC_REQUEST_R` 用于有返回值但无参数的请求
- :c:func:`SSAM_DEFINE_SYNC_REQUEST_W` 用于没有返回值但有参数的请求
请参阅各自的文档以获取更多详细信息。对于每个宏，都提供了一个特殊变体，用于处理适用于同一设备类型多个实例的请求类型：

- :c:func:`SSAM_DEFINE_SYNC_REQUEST_MD_N`
- :c:func:`SSAM_DEFINE_SYNC_REQUEST_MD_R`
- :c:func:`SSAM_DEFINE_SYNC_REQUEST_MD_W`

这些宏与之前提到的版本的不同之处在于，生成的函数的目标设备和实例ID不是固定的，而是需要由调用者提供。
此外，还提供了直接与客户端设备（如 `ssam_device`）一起使用的变体。例如：

.. code-block:: c

   SSAM_DEFINE_SYNC_REQUEST_CL_R(ssam_bat_get_sta, __le32, {
           .target_category = SSAM_SSH_TC_BAT,
           .command_id      = 0x01,
   });

这个宏调用定义了一个函数

.. code-block:: c

   static int ssam_bat_get_sta(struct ssam_device *sdev, __le32 *ret);

该函数使用客户端设备中的设备ID和控制器来执行指定的请求。此类客户端设备宏的完整列表为：

- :c:func:`SSAM_DEFINE_SYNC_REQUEST_CL_N`
- :c:func:`SSAM_DEFINE_SYNC_REQUEST_CL_R`
- :c:func:`SSAM_DEFINE_SYNC_REQUEST_CL_W`

处理事件
==========

要从 SAM EC 接收事件，必须为所需的事件通过 `ssam_notifier_register` 注册一个事件通知器。不再需要时，必须通过 `ssam_notifier_unregister` 取消注册。对于 `ssam_device` 类型的客户端，建议使用 `ssam_device_notifier_register` 和 `ssam_device_notifier_unregister` 包装器，因为它们可以正确处理客户端设备的热插拔问题。
注册事件通知器至少需要提供一个回调函数，当接收到事件时将被调用；一个注册表，用于指定如何启用事件；一个事件ID，用于指定目标类别以及，根据所使用的注册表，可选地指定实例ID，以便启用哪些事件；最后，一些标志描述EC如何发送这些事件。如果特定的注册表不支持按实例ID启用事件，则实例ID必须设置为零。此外，还可以为相应的通知器指定优先级，以确定它相对于同一目标类别下的其他任何通知器的顺序。
默认情况下，事件通知器将接收到特定目标类别的所有事件，无论在注册通知器时指定了哪个实例ID。可以通过提供事件掩码（参见 `ssam_event_mask`）来指示核心仅在事件的目标ID或实例ID（或者两者）与通知器ID所暗示的相匹配时调用通知器（在目标ID的情况下，指的是注册表的目标ID）。
通常，注册表的目标ID也是已启用事件的目标ID（值得注意的是，在Surface Laptop 1和2上的键盘输入事件是一个例外，这些事件通过目标ID为1的注册表启用，但提供的事件具有目标ID 2）。
下面提供了一个注册事件通知器和处理接收到的事件的完整示例：

```c
u32 notifier_callback(struct ssam_event_notifier *nf,
                      const struct ssam_event *event)
{
    int status = .. /* 处理事件... */

    /* 转换返回值并指示我们已经处理了该事件。 */
    return ssam_notifier_from_errno(status) | SSAM_NOTIF_HANDLED;
}

int setup_notifier(struct ssam_device *sdev,
                   struct ssam_event_notifier *nf)
{
    /* 设置相对于同一目标类别的其他处理器的优先级。 */
    nf->base.priority = 1;

    /* 设置事件/通知器回调函数。 */
    nf->base.fn = notifier_callback;

    /* 指定事件注册表，即如何启用/禁用事件。 */
    nf->event.reg = SSAM_EVENT_REGISTRY_KIP;

    /* 指定要启用/禁用的事件。 */
    nf->event.id.target_category = sdev->uid.category;
    nf->event.id.instance = sdev->uid.instance;

    /*
     * 指定哪些事件将执行通知器回调。
     * 这实质上告诉核心是否可以跳过那些目标或实例ID与事件不匹配的通知器。
     */
    nf->event.mask = SSAM_EVENT_MASK_STRICT;

    /* 指定事件标志。 */
    nf->event.flags = SSAM_EVENT_SEQUENCED;

    return ssam_notifier_register(sdev->ctrl, nf);
}
```

对于同一个事件可以注册多个事件通知器。当通知器被注册和注销时，事件处理核心会负责启用和禁用事件，方法是跟踪当前有多少个特定事件（注册表、事件目标类别以及事件实例ID的组合）的通知器已注册。这意味着，当第一个通知器被注册时，特定事件将被启用；而当最后一个通知器被注销时，该事件将被禁用。需要注意的是，事件标志仅对第一个注册的通知器使用，但是应当确保特定事件的所有通知器始终以相同的标志进行注册，否则会被视为错误。
