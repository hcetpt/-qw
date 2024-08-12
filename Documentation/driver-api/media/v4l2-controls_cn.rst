SPDX 许可证标识符: GPL-2.0

V4L2 控制
=========

简介
----

V4L2 控制 API 看起来足够简单，但在驱动程序中正确实现却很快变得非常困难。但实际上，处理控制所需的大部分代码并非特定于驱动程序，可以移动到 V4L 核心框架中。毕竟，驱动程序开发人员感兴趣的只有：

1) 如何添加一个控制？
2) 如何设置控制的值？（即 s_ctrl）

偶尔会用到：

3) 如何获取控制的值？（即 g_volatile_ctrl）
4) 如何验证用户提议的控制值是否有效？（即 try_ctrl）

其余的所有内容都可以集中处理。
创建控制框架是为了在一个中心位置实现与控制相关的所有 V4L2 规范规则，并尽可能简化驱动程序开发人员的工作。
请注意，控制框架依赖于 V4L2 驱动程序中的 `v4l2_device` 结构体以及子设备驱动程序中的 `v4l2_subdev` 结构体。

框架中的对象
--------------

有两个主要对象：

`v4l2_ctrl` 对象描述了控制属性并跟踪控制的值（当前值和提议的新值）。
`v4l2_ctrl_handler` 是用于跟踪控制的对象。它维护一个属于它的 `v4l2_ctrl` 对象列表以及对其他可能由其他处理器拥有的控制的引用列表。

V4L2 和子设备驱动程序的基本使用
-----------------------------------

1) 准备驱动程序：

.. code-block:: c

	#include <media/v4l2-ctrls.h>

1.1) 将处理器添加到您的驱动程序顶级结构体中：

对于 V4L2 驱动程序：

.. code-block:: c

    struct foo_dev {
        ...
    struct v4l2_device v4l2_dev;
        ...
    struct v4l2_ctrl_handler ctrl_handler;
        ...
    };

对于子设备驱动程序：

.. code-block:: c

    struct foo_dev {
        ...
### 结构体定义示例：

```c
struct v4l2_subdev sd;
// ...
struct v4l2_ctrl_handler ctrl_handler;
// ...
};
```

### 1.2) 初始化处理器：

```c
v4l2_ctrl_handler_init(&foo->ctrl_handler, nr_of_controls);
```

第二个参数是一个提示，告诉函数该处理器预计要处理多少个控制项。它会基于这些信息分配一个哈希表。这仅仅是一个提示。

### 1.3) 将控制处理器连接到驱动程序中：

对于V4L2驱动程序：

```c
foo->v4l2_dev.ctrl_handler = &foo->ctrl_handler;
```

对于子设备驱动程序：

```c
foo->sd.ctrl_handler = &foo->ctrl_handler;
```

### 1.4) 在最后清理处理器：

```c
v4l2_ctrl_handler_free(&foo->ctrl_handler);
```

### 2) 添加控制项：

通过调用 `v4l2_ctrl_new_std` 函数来添加非菜单控制项：

```c
struct v4l2_ctrl *v4l2_ctrl_new_std(struct v4l2_ctrl_handler *hdl,
            const struct v4l2_ctrl_ops *ops,
            u32 id, s32 min, s32 max, u32 step, s32 def);
```

菜单和整数菜单控制项通过调用 `v4l2_ctrl_new_std_menu` 函数添加：

```c
struct v4l2_ctrl *v4l2_ctrl_new_std_menu(struct v4l2_ctrl_handler *hdl,
            const struct v4l2_ctrl_ops *ops,
            u32 id, s32 max, s32 skip_mask, s32 def);
```

具有特定于驱动程序的菜单的菜单控制项通过调用 `v4l2_ctrl_new_std_menu_items` 函数添加：

```c
struct v4l2_ctrl *v4l2_ctrl_new_std_menu_items(
                struct v4l2_ctrl_handler *hdl,
                const struct v4l2_ctrl_ops *ops, u32 id, s32 max,
                s32 skip_mask, s32 def, const char * const *qmenu);
```

标准复合控制项可以通过调用 `v4l2_ctrl_new_std_compound` 函数添加：

```c
struct v4l2_ctrl *v4l2_ctrl_new_std_compound(struct v4l2_ctrl_handler *hdl,
                const struct v4l2_ctrl_ops *ops, u32 id,
                const union v4l2_ctrl_ptr p_def);
```

具有特定于驱动程序的菜单的整数菜单控制项可以通过调用 `v4l2_ctrl_new_int_menu` 函数添加：

```c
struct v4l2_ctrl *v4l2_ctrl_new_int_menu(struct v4l2_ctrl_handler *hdl,
            const struct v4l2_ctrl_ops *ops,
            u32 id, s32 max, s32 def, const s64 *qmenu_int);
```

这些函数通常在调用 `v4l2_ctrl_handler_init` 之后立即调用：

```c
static const s64 exp_bias_qmenu[] = {
       -2, -1, 0, 1, 2
};
static const char * const test_pattern[] = {
    "Disabled",
    "Vertical Bars",
    "Solid Black",
    "Solid White",
};

v4l2_ctrl_handler_init(&foo->ctrl_handler, nr_of_controls);
v4l2_ctrl_new_std(&foo->ctrl_handler, &foo_ctrl_ops,
        V4L2_CID_BRIGHTNESS, 0, 255, 1, 128);
v4l2_ctrl_new_std(&foo->ctrl_handler, &foo_ctrl_ops,
        V4L2_CID_CONTRAST, 0, 255, 1, 128);
v4l2_ctrl_new_std_menu(&foo->ctrl_handler, &foo_ctrl_ops,
        V4L2_CID_POWER_LINE_FREQUENCY,
        V4L2_CID_POWER_LINE_FREQUENCY_60HZ, 0,
        V4L2_CID_POWER_LINE_FREQUENCY_DISABLED);
v4l2_ctrl_new_int_menu(&foo->ctrl_handler, &foo_ctrl_ops,
        V4L2_CID_EXPOSURE_BIAS,
        ARRAY_SIZE(exp_bias_qmenu) - 1,
        ARRAY_SIZE(exp_bias_qmenu) / 2 - 1,
        exp_bias_qmenu);
v4l2_ctrl_new_std_menu_items(&foo->ctrl_handler, &foo_ctrl_ops,
        V4L2_CID_TEST_PATTERN, ARRAY_SIZE(test_pattern) - 1, 0,
        0, test_pattern);
// ...
if (foo->ctrl_handler.error) {
    int err = foo->ctrl_handler.error;

    v4l2_ctrl_handler_free(&foo->ctrl_handler);
    return err;
}
```

`v4l2_ctrl_new_std` 函数返回指向新控制项的 v4l2_ctrl 指针，但如果不需要在控制操作之外访问该指针，则无需存储它。
`v4l2_ctrl_new_std` 函数将根据控制ID填充大多数字段，除了最小值、最大值、步长和默认值。这些值通过最后四个参数传递。这些值是特定于驱动程序的，而像类型、名称、标志这样的控制属性都是全局的。控制项的当前值将被设置为默认值。
`v4l2_ctrl_new_std_menu` 函数非常类似，但用于菜单控制项。没有最小值参数，因为对于菜单控制项总是0，并且代替步长有一个 skip_mask 参数：如果第 X 位为 1，则跳过第 X 个菜单项。
`v4l2_ctrl_new_int_menu` 函数创建一个新的标准整数菜单控制项，其菜单中的项特定于驱动程序。它与 `v4l2_ctrl_new_std_menu` 的不同之处在于它没有 mask 参数，而是以最后一个参数的形式接受一个由 64 位有符号整数组成的数组，形成一个确切的菜单项列表。
`v4l2_ctrl_new_std_menu_items` 函数与 `v4l2_ctrl_new_std_menu` 非常类似，但多了一个参数 qmenu，它是特定于驱动程序的菜单，适用于其他方面标准的菜单控制项。这个控制项的一个好例子是捕获/显示/传感器设备的测试模式控制，这些设备具有生成测试模式的能力。这些测试模式是硬件特定的，因此菜单的内容会因设备而异。

注意，如果发生错误，函数将返回 NULL 或者错误并设置 ctrl_handler->error 为错误代码。如果 ctrl_handler->error 已经被设置，则它将只是返回不做任何事情。这对于 `v4l2_ctrl_handler_init` 如果无法分配内部数据结构时也同样适用。
这使得初始化控制器变得简单，并且可以添加所有控件，在最后仅检查错误代码。这样可以节省大量的重复性错误检查工作。
建议按照控制ID递增的顺序添加控件：这样做会稍微快一些。
3) 可选地强制进行初始控件设置：

```c
v4l2_ctrl_handler_setup(&foo->ctrl_handler);
```

这将无条件地为所有控件调用`s_ctrl`。实际上，这将硬件初始化为默认的控件值。建议你这样做，因为这能确保内部数据结构和硬件同步。
4) 最后：实现`:c:type:` `v4l2_ctrl_ops`

```c
static const struct v4l2_ctrl_ops foo_ctrl_ops = {
    .s_ctrl = foo_s_ctrl,
};
```

通常情况下，你只需要`s_ctrl`：

```c
static int foo_s_ctrl(struct v4l2_ctrl *ctrl)
{
    struct foo *state = container_of(ctrl->handler, struct foo, ctrl_handler);

    switch (ctrl->id) {
    case V4L2_CID_BRIGHTNESS:
        write_reg(0x123, ctrl->val);
        break;
    case V4L2_CID_CONTRAST:
        write_reg(0x456, ctrl->val);
        break;
    }
    return 0;
}
```

控件操作是使用`v4l2_ctrl`指针作为参数被调用的。
新的控件值已经被验证过，所以你需要做的只是更新硬件寄存器。
完成了！对于大多数驱动程序来说，这些就足够了。不需要对控件值进行任何验证，也不需要实现QUERYCTRL、QUERY_EXT_CTRL和QUERYMENU。G/S_CTRL以及G/TRY/S_EXT_CTRLS也会自动支持。
.. note::

   接下来的部分处理的是更高级的控件主题和场景。
实际上，如上所述的基本使用方法对于大多数驱动程序已经足够了。
继承子设备控件
------------------

当通过调用`v4l2_device_register_subdev()`将一个子设备注册到V4L2驱动程序中，并且`v4l2_subdev`和`v4l2_device`的`ctrl_handler`字段都被设置时，子设备的控件将会自动在V4L2驱动程序中可用。如果子设备驱动程序包含的控件已经在V4L2驱动程序中存在，则这些控件会被跳过（因此V4L2驱动程序始终可以覆盖子设备的控件）。
在这里发生的情况是`v4l2_device_register_subdev()`调用了`v4l2_ctrl_add_handler()`，将子设备的控件添加到`v4l2_device`的控件中。
### 访问控制值
------------------------

以下联合体在控制框架中用于访问控制值：

.. code-block:: c

    union v4l2_ctrl_ptr {
        s32 *p_s32;
        s64 *p_s64;
        char *p_char;
        void *p;
    };

`v4l2_ctrl` 结构体包含以下字段，可用于访问当前值和新值：

.. code-block:: c

    s32 val;
    struct {
        s32 val;
    } cur;

    union v4l2_ctrl_ptr p_new;
    union v4l2_ctrl_ptr p_cur;

如果控制类型为简单的 `s32` 类型，则有：

.. code-block:: c

    &ctrl->val == ctrl->p_new.p_s32
    &ctrl->cur.val == ctrl->p_cur.p_s32

对于所有其他类型，请使用 `ctrl->p_cur.p<something>`。基本上可以认为 `val` 和 `cur.val` 字段是等价的，因为它们被频繁地使用。在控制操作中你可以自由地使用这些字段。`val` 和 `cur.val` 的含义很明确。`p_char` 指针指向长度为 `ctrl->maximum + 1` 的字符缓冲区，并且总是以 0 结尾。
除非控制被标记为易变（volatile），否则 `p_cur` 字段指向当前缓存的控制值。当创建一个新的控制时，该值将与默认值相同。调用 `v4l2_ctrl_handler_setup()` 后，该值将传递给硬件。通常，调用此函数是一个好主意。
每当设置一个新值时，该新值会自动被缓存。这意味着大多数驱动程序不需要实现 `g_volatile_ctrl()` 操作。例外情况是那些返回易变寄存器的控制，例如连续变化的信号强度读取。在这种情况下，你需要像这样实现 `g_volatile_ctrl`：

.. code-block:: c

    static int foo_g_volatile_ctrl(struct v4l2_ctrl *ctrl)
    {
        switch (ctrl->id) {
        case V4L2_CID_BRIGHTNESS:
            ctrl->val = read_reg(0x123);
            break;
        }
    }

请注意，在 `g_volatile_ctrl` 中你也需要使用“新值”联合体。一般来说，需要实现 `g_volatile_ctrl` 的控制通常是只读控制。如果不是这样，在控制改变时不会生成 `V4L2_EVENT_CTRL_CH_VALUE` 事件。
要将控制标记为易变，需要设置 `V4L2_CTRL_FLAG_VOLATILE`：

.. code-block:: c

    ctrl = v4l2_ctrl_new_std(&sd->ctrl_handler, ...);
    if (ctrl)
        ctrl->flags |= V4L2_CTRL_FLAG_VOLATILE;

对于 `try/s_ctrl`，新的值（即用户传递的值）会被填充，你可以在 `try_ctrl` 中修改它们或在 `s_ctrl` 中设置它们。`cur` 联合体包含当前值，你可以使用它（但不能更改！）
如果 `s_ctrl` 返回 0（成功），那么控制框架会将新的最终值复制到 `cur` 联合体中。
在 `g_volatile/s/try_ctrl` 中，你可以访问同一控制器处理器拥有的所有控制的值，因为处理器的锁已经被持有。如果你需要访问其他处理器拥有的控制的值，那么必须非常小心，避免引入死锁。
在控制操作之外，你需要通过辅助函数安全地获取或设置单个控制值：

.. code-block:: c

    s32 v4l2_ctrl_g_ctrl(struct v4l2_ctrl *ctrl);
    int v4l2_ctrl_s_ctrl(struct v4l2_ctrl *ctrl, s32 val);

这些函数通过控制框架执行，就像 `VIDIOC_G/S_CTRL` ioctl 函数一样。不过不要在控制操作 `g_volatile/s/try_ctrl` 中使用这些函数，这会导致死锁，因为这些辅助函数也会锁定处理器。
你也可以自己锁定处理器：

.. code-block:: c

    mutex_lock(&state->ctrl_handler.lock);
    pr_info("字符串值是 '%s'\n", ctrl1->p_cur.p_char);
    pr_info("整数值是 '%s'\n", ctrl2->cur.val);
    mutex_unlock(&state->ctrl_handler.lock);

### 菜单控制
-------------

`v4l2_ctrl` 结构体包含以下联合体：

.. code-block:: c

    union {
        u32 step;
        u32 menu_skip_mask;
    };

对于菜单控制，使用 `menu_skip_mask`。它的作用是允许你轻松排除某些菜单项。这在 `VIDIOC_QUERYMENU` 实现中被使用，其中如果某个菜单项不存在，你可以返回 `-EINVAL`。请注意，对于菜单控制，`VIDIOC_QUERYCTRL` 总是返回步长值为 1。
一个很好的例子是 MPEG Audio Layer II 比特率菜单控制，其中菜单是一系列标准化的可能比特率列表。但实际上硬件实现只会支持其中的一部分。通过设置跳过掩码，你可以告诉框架应该跳过的菜单项。将其设置为 0 表示支持所有菜单项。
您可以使用 v4l2_ctrl_config 结构为自定义控制设置此掩码，或者通过调用 v4l2_ctrl_new_std_menu()。

### 自定义控制

------

可以使用 v4l2_ctrl_new_custom() 创建与驱动程序相关的控制：

```c
static const struct v4l2_ctrl_config ctrl_filter = {
	.ops = &ctrl_custom_ops,
	.id = V4L2_CID_MPEG_CX2341X_VIDEO_SPATIAL_FILTER,
	.name = "空间滤波器",
	.type = V4L2_CTRL_TYPE_INTEGER,
	.flags = V4L2_CTRL_FLAG_SLIDER,
	.max = 15,
	.step = 1,
};

ctrl = v4l2_ctrl_new_custom(&foo->ctrl_handler, &ctrl_filter, NULL);
```

最后一个参数是私有指针(priv)，它可以被设置为特定于驱动程序的私有数据。
结构体 v4l2_ctrl_config 还有一个字段用于设置 is_private 标志。
如果未设置 name 字段，则框架将假设这是一个标准控制，并相应地填充 name、type 和 flags 字段。

### 活动和已抓取的控制

--------------

如果您在控制间建立了更复杂的关系，那么您可能需要激活或停用某些控制。例如，如果“色度自动增益控制”开启，则“色度增益控制”处于非活动状态。也就是说，您可以设置其值，但在自动增益控制开启的情况下硬件不会使用该值。通常用户界面会禁用这样的输入字段。
您可以使用 v4l2_ctrl_activate() 设置“活动”状态。默认情况下所有控制都是活动的。请注意，框架不会检查这个标志，它纯粹是为了图形用户界面设计的。该函数通常在 s_ctrl 函数中被调用。
另一个标志是“已抓取”标志。一个已抓取的控制意味着您不能更改它，因为它正被某个资源使用。典型的例子是在进行捕获时无法更改的 MPEG 比特率控制。
如果使用 v4l2_ctrl_grab() 将一个控制设置为“已抓取”，则当尝试设置此控制时，框架会返回 -EBUSY。v4l2_ctrl_grab() 函数通常在驱动程序开始或停止流式传输时被调用。

### 控制集群

-------

默认情况下所有控制都是相互独立的。但在更复杂的场景中，可以从一个控制依赖于另一个控制。
在这种情况下，你需要对它们进行“聚类”：

.. code-block:: c

    struct foo {
        struct v4l2_ctrl_handler ctrl_handler;
        #define AUDIO_CL_VOLUME (0)
        #define AUDIO_CL_MUTE   (1)
        struct v42_ctrl *audio_cluster[2];
        ..
    };

    state->audio_cluster[AUDIO_CL_VOLUME] =
        v4l2_ctrl_new_std(&state->ctrl_handler, ...);
    state->audio_cluster[AUDIO_CL_MUTE] =
        v4l2_ctrl_new_std(&state->ctrl_handler, ...);
    v4l2_ctrl_cluster(ARRAY_SIZE(state->audio_cluster), state->audio_cluster);

从现在开始，每当设置（或获取，或尝试）属于同一聚类的控制时，只调用第一个控制（在这个例子中是“音量”）的控制操作。这样你就有效地创建了一个新的复合控制。这类似于C语言中的“结构体”的工作方式。
因此，当s_ctrl被调用并传入V4L2_CID_AUDIO_VOLUME作为参数时，你应该设置属于audio_cluster的所有两个控制：

.. code-block:: c

    static int foo_s_ctrl(struct v4l2_ctrl *ctrl)
    {
        struct foo *state = container_of(ctrl->handler, struct foo, ctrl_handler);

        switch (ctrl->id) {
        case V4L2_CID_AUDIO_VOLUME: {
            struct v4l2_ctrl *mute = ctrl->cluster[AUDIO_CL_MUTE];

            write_reg(0x123, mute->val ? 0 : ctrl->val);
            break;
        }
        case V4L2_CID_CONTRAST:
            write_reg(0x456, ctrl->val);
            break;
        }
        return 0;
    }

在上面的例子中，对于VOLUME的情况，以下内容是等价的：

.. code-block:: c

    ctrl == ctrl->cluster[AUDIO_CL_VOLUME] == state->audio_cluster[AUDIO_CL_VOLUME]
    ctrl->cluster[AUDIO_CL_MUTE] == state->audio_cluster[AUDIO_CL_MUTE]

实际上，像这样使用聚类数组会变得非常繁琐。因此，通常采用以下等效方法：

.. code-block:: c

    struct {
        /* 音频聚类 */
        struct v4l2_ctrl *volume;
        struct v4l2_ctrl *mute;
    };

使用匿名结构体明确地“聚类”这两个控制指针，但它没有其他用途。其效果与创建包含两个控制指针的数组相同。因此，你可以直接做：

.. code-block:: c

    state->volume = v4l2_ctrl_new_std(&state->ctrl_handler, ...);
    state->mute = v4l2_ctrl_new_std(&state->ctrl_handler, ...);
    v4l2_ctrl_cluster(2, &state->volume);

在foo_s_ctrl中可以直接使用这些指针：state->mute->val
需要注意的是，聚类中的控制可能为NULL。例如，如果出于某种原因，mute从未被添加（因为硬件不支持该特定功能），那么mute将是NULL。因此，在这种情况下，我们有一个包含2个控制的聚类，其中只有1个实际实例化。唯一的限制是聚类的第一个控制必须始终存在，因为它是聚类的“主控”。主控是标识聚类并提供用于该聚类的v4l2_ctrl_ops结构指针的控制。
显然，聚类数组中的所有控制都必须初始化为有效控制或NULL。
在极少数情况下，你可能想知道聚类中的哪些控制实际上是用户显式设置的。为此，可以检查每个控制的'is_new'标志。例如，在音量/静音聚类的情况下，如果用户仅调用了VIDIOC_S_CTRL来设置静音，则mute控制的'is_new'标志将被设置。如果用户调用VIDIOC_S_EXT_CTRLS同时设置mute和volume控制，则'is_new'标志对于这两个控制都将为1。
'is_new'标志在从v4l2_ctrl_handler_setup()调用时总是为1。
处理自动增益/增益类型控制的自动聚类
----------------------------------------------

一种常见的控制聚类类型是处理“自动-foo/foo”类型的控制。典型的例子有自动增益/增益、自动曝光/曝光、自动白平衡/红平衡/蓝平衡。在所有情况下，你都有一个控制来确定另一个控制是由硬件自动处理还是由用户手动控制。

如果聚类处于自动模式，则应将手动控制标记为非活动且易失性。当读取易失性控制时，g_volatile_ctrl操作应返回硬件的自动模式自动设置的值。

如果将聚类置于手动模式，则手动控制应再次变为活动状态，并清除易失性标志（因此在手动模式下不再调用g_volatile_ctrl）。此外，在切换到手动模式之前，应将当前值（由自动模式确定）复制为新的手动值。
最后，对于自动控制应设置V4L2_CTRL_FLAG_UPDATE标志，
因为更改该控制会影响手动控制的标志。
为了简化这一点，引入了一个特殊的v4l2_ctrl_cluster变体：

```c
void v4l2_ctrl_auto_cluster(unsigned ncontrols, struct v4l2_ctrl **controls,
				    u8 manual_val, bool set_volatile);
```

前两个参数与v4l2_ctrl_cluster相同。第三个参数告诉框架哪个值将集群切换到手动模式。最后一个参数可选地为非自动控制设置V4L2_CTRL_FLAG_VOLATILE标志。
如果它为假，则手动控制从不具有易失性。如果你通常无法通过硬件读取由自动模式确定的值（例如，如果自动增益开启，硬件不允许你获取当前的增益值），那么你通常会使用这个选项。
假设集群中的第一个控制是“自动”控制。
使用此函数可以确保你无需处理所有复杂的标志和易失性处理。

### VIDIOC_LOG_STATUS 支持

此ioctl允许你将驱动程序的当前状态转储到内核日志中。
你可以使用v4l2_ctrl_handler_log_status(ctrl_handler, prefix)来将给定处理器拥有的控制值转储到日志中。你还可以提供一个前缀。如果前缀没有以空格结尾，那么将为你添加': '。

### 不同视频节点的不同处理器

通常V4L2驱动程序只有一个对所有视频节点全局的控制处理器。但是，你也可以为不同的视频节点指定不同的控制处理器。你可以通过手动设置video_device结构中的ctrl_handler字段来实现这一点。
如果没有子设备(subdevs)参与，这没有问题；但如果有子设备，你需要阻止子设备控制自动合并到全局控制处理器。你只需将v4l2_device结构中的ctrl_handler字段设置为NULL即可实现这一点。这样，v4l2_device_register_subdev()将不再合并子设备控制。
在添加每个子设备之后，你需要手动调用v4l2_ctrl_add_handler来将子设备的控制处理器（sd->ctrl_handler）添加到所需的控制处理器。这个控制处理器可能是针对特定video_device或一组video_device的。例如：无线电设备节点只有音频控制，而视频和vbi设备节点则共享相同的控制处理器用于音频和视频控制。
如果你希望一个控制器（例如用于一个无线电设备节点）包含另一个控制器（例如用于一个视频设备节点）的一个子集，那么你应该首先将控制添加到第一个控制器中，然后将其他控制添加到第二个控制器，并最后将第一个控制器添加到第二个控制器中。例如：

.. 代码块:: c

	v4l2_ctrl_new_std(&radio_ctrl_handler, &radio_ops, V4L2_CID_AUDIO_VOLUME, ...);
	v4l2_ctrl_new_std(&radio_ctrl_handler, &radio_ops, V4L2_CID_AUDIO_MUTE, ...);
	v4l2_ctrl_new_std(&video_ctrl_handler, &video_ops, V4L2_CID_BRIGHTNESS, ...);
	v4l2_ctrl_new_std(&video_ctrl_handler, &video_ops, V4L2_CID_CONTRAST, ...);
	v4l2_ctrl_add_handler(&video_ctrl_handler, &radio_ctrl_handler, NULL);

`v4l2_ctrl_add_handler()`的最后一个参数是一个过滤函数，允许你过滤哪些控制将被添加。如果要添加所有控制，则将其设置为NULL。
或者你可以向控制器中添加特定的控制：

.. 代码块:: c

	volume = v4l2_ctrl_new_std(&video_ctrl_handler, &ops, V4L2_CID_AUDIO_VOLUME, ...);
	v4l2_ctrl_new_std(&video_ctrl_handler, &ops, V4L2_CID_BRIGHTNESS, ...);
	v4l2_ctrl_new_std(&video_ctrl_handler, &ops, V4L2_CID_CONTRAST, ...);

你不应该为两个控制器创建两个完全相同的控制。例如：

.. 代码块:: c

	v4l2_ctrl_new_std(&radio_ctrl_handler, &radio_ops, V4L2_CID_AUDIO_MUTE, ...);
	v4l2_ctrl_new_std(&video_ctrl_handler, &video_ops, V4L2_CID_AUDIO_MUTE, ...);

这将是不好的，因为静音无线电不会改变视频静音控制。规则是对于每个硬件旋钮，你应该只有一个控制。

查找控制
---------

通常情况下，你自己已经创建了这些控制，并可以将`struct v4l2_ctrl`指针存储在自己的结构体中。
但有时你需要从不属于你的另一个控制器中找到一个控制。例如，如果你需要从一个子设备中找到音量控制，你可以通过调用`v4l2_ctrl_find`来实现：

.. 代码块:: c

	struct v4l2_ctrl *volume;

	volume = v4l2_ctrl_find(sd->ctrl_handler, V4L2_CID_AUDIO_VOLUME);

由于`v4l2_ctrl_find`会锁定控制器，因此你需要小心在哪里使用它。例如，这不是一个好主意：

.. 代码块:: c

	struct v4l2_ctrl_handler ctrl_handler;

	v4l2_ctrl_new_std(&ctrl_handler, &video_ops, V4L2_CID_BRIGHTNESS, ...);
	v4l2_ctrl_new_std(&ctrl_handler, &video_ops, V4L2_CID_CONTRAST, ...);

...并在`video_ops.s_ctrl`中：

.. 代码块:: c

	case V4L2_CID_BRIGHTNESS:
		contrast = v4l2_find_ctrl(&ctrl_handler, V4L2_CID_CONTRAST);
		..

当`s_ctrl`由框架调用时，`ctrl_handler.lock`已经被占用，因此尝试从同一个控制器中查找另一个控制会导致死锁。
建议不要在控制操作中使用此函数。

防止控制继承
--------------

当你使用`v4l2_ctrl_add_handler`将一个控制器添加到另一个控制器时，默认情况下来自一个控制器的所有控制都会合并到另一个控制器中。但是子设备可能有一些低级别的控制，这些控制对于某些高级嵌入式系统有意义，但对于消费者级别的硬件则没有意义。在这种情况下，你希望将这些低级别的控制保持在子设备本地。你可以通过简单地将控制的`is_private`标志设置为1来实现这一点：

.. 代码块:: c

	static const struct v4l2_ctrl_config ctrl_private = {
		.ops = &ctrl_custom_ops,
		.id = V4L2_CID_...,
		.name = "Some Private Control",
		.type = V4L2_CTRL_TYPE_INTEGER,
		.max = 15,
		.step = 1,
		.is_private = 1,
	};

	ctrl = v4l2_ctrl_new_custom(&foo->ctrl_handler, &ctrl_private, NULL);

当调用`v4l2_ctrl_add_handler`时，这些控制现在将被跳过。

V4L2_CTRL_TYPE_CTRL_CLASS 控制
------------------------------

这种类型的控制可用于GUI获取控制类的名称。
一个功能完整的图形用户界面（GUI）可以通过多个标签页与之进行对话，每个标签页包含属于特定控制类别的控件。通过查询ID为 `<控制类别 | 1>` 的特殊控件可以找到每个标签的名字。驱动程序不需要关心这些细节。框架会在添加属于新控制类别的第一个控件时自动添加这种类型的控件。

### 添加通知回调

有时，平台或桥接驱动程序需要在子设备驱动程序中的某个控件发生变化时得到通知。您可以通过调用以下函数来设置通知回调：

```c
void v4l2_ctrl_notify(struct v4l2_ctrl *ctrl,
    void (*notify)(struct v4l2_ctrl *ctrl, void *priv), void *priv);
```

每当给定的控件值发生变化时，将会调用通知回调函数，并传入指向该控件的指针和通过 `v4l2_ctrl_notify` 函数传递的私有数据指针。请注意，在调用通知函数时，会持有控件的处理锁。

每个控件处理器只能有一个通知函数。尝试设置另一个通知函数将会导致 `WARN_ON` 警告。

### v4l2_ctrl 函数和数据结构

```markdown
.. kernel-doc:: include/media/v4l2-ctrls.h
```
此部分文档描述了内核中用于视频4 Linux 2 (V4L2) 控件处理的函数和数据结构。
