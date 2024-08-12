下面是来自Rene Herman最初提交的ISA总线驱动程序提交信息的部分内容：

在最近关于“使用平台设备的ISA驱动程序”的讨论中，有人指出（ALSA）ISA驱动程序遇到了一个问题：由于未能将`probe()`错误向上传递到驱动模型，因此无法在未找到其硬件时选择性地失败加载驱动程序（实际上是设备注册）。在这个过程中，我建议最好有一个单独的ISA总线；Russell King表示同意，并建议这个总线可以使用`.match()`方法来进行实际的设备发现。

所附的补丁实现了这一点。对于这种老旧且非通用发现机制的ISA硬件来说，只有驱动程序本身能够进行发现，因此与`platform_bus`不同的是，这个`isa_bus`也向上分发了`match()`方法给驱动程序。

另一个不同之处在于：这些设备仅存在于驱动模型中是因为驱动程序创建了它们，因为它可能需要驱动这些设备，这意味着所有设备创建都被内部化了。

这种方式提供的使用模型很好，已经被ALSA方面的Takashi Iwai和Jaroslav Kysela认可。对于只支持旧ISA设备的ALSA驱动模块的初始化现在变为：

```c
static int __init alsa_card_foo_init(void)
{
    return isa_register_driver(&snd_foo_isa_driver, SNDRV_CARDS);
}

static void __exit alsa_card_foo_exit(void)
{
    isa_unregister_driver(&snd_foo_isa_driver);
}
```

这很像其他总线模型的做法。这从ALSA ISA驱动程序中移除了大量的重复初始化代码。

传递给`isa_driver`结构体的是一个常规的`driver`结构体，其中嵌入了一个`struct device_driver`，以及正常的`probe`、`remove`、`shutdown`、`suspend`、`resume`回调函数，还有如前所述的`match`回调函数。

你看到的被传入的`SNDRV_CARDS`是一个`unsigned int ndev`参数，表示要创建并调用我们方法的设备数量。

`platform_driver`回调函数使用`platform_device`参数；而`isa_driver`回调函数则直接使用`struct device *dev, unsigned int id`对——因为设备创建完全由总线内部处理，所以这样更干净，不需要通过传递`isa_dev`来泄露它们。我们除了`struct device`之外唯一需要的就是`id`，并且这也使得回调函数中的代码更加简洁。

有了额外的`match`回调函数，ISA驱动程序拥有了所有选项。如果ALSA希望保留旧的行为，即在确认所有必需的硬件都存在后才保持驱动程序注册状态，它可以在`match`中保留所有旧的`probe`逻辑。如果它想要像之前切换到平台设备之后那样总是加载驱动程序的行为，它可以不提供`match`回调，而是像以前一样在`probe`中完成所有工作。

如果按照Takashi Iwai早些时候建议的方式，更接近于其他更为合理的总线模型，即当后续绑定有可能成功时就加载驱动程序，那么它可以在`match`中检查先决条件（例如，检查用户是否希望启用该卡，以及端口、中断、DMA值是否已传递），而在`probe`中处理其他所有事情。这是最优雅的模型。
这段代码主要描述了ISA总线驱动程序的注册与注销机制，以及设备匹配的过程。以下是翻译：

这段代码只公开了两个函数：`isa_{,un}register_driver()`。

`isa_register_driver()`函数负责注册`struct device_driver`结构体，并遍历传入的`ndev`来创建设备并注册它们。这会触发设备的总线匹配方法，该方法如下所示：

```c
int isa_bus_match(struct device *dev, struct device_driver *driver)
{
    struct isa_driver *isa_driver = to_isa_driver(driver);

    if (dev->platform_data == isa_driver) {
        if (!isa_driver->match ||
            isa_driver->match(dev, to_isa_dev(dev)->id))
            return 1;
        dev->platform_data = NULL;
    }
    return 0;
}
```

这个方法首先检查设备是否属于该驱动程序管理的设备之一，通过比较设备的`platform_data`指针是否指向该驱动程序实现。平台设备通常需要字符串比较，但在这个内部实现中不需要，因此`isa_register_driver()`函数滥用`dev->platform_data`作为`isa_driver`指针，以便在这里进行检查。
接着，如果驱动程序没有提供`.match`方法，则默认匹配成功；如果提供了`.match`方法，则调用该方法以确定是否匹配。
如果未匹配成功，将`dev->platform_data`重置为`NULL`，以指示给`isa_register_driver()`函数，后者可以再次注销该设备。
在上述过程中，如果出现任何错误，或者没有任何设备匹配，所有操作都将回滚，并返回相应的错误码或`-ENODEV`。
`isa_unregister_driver()`函数则负责注销已匹配的设备和驱动程序本身。

`module_isa_driver`是一个辅助宏，用于简化那些在模块初始化和退出时不做特殊处理的ISA驱动程序，这样可以减少大量模板代码。每个模块只能使用此宏一次，并且使用它会替代`module_init`和`module_exit`的调用。
`max_num_isa_dev` 是一个用于确定在给定 ISA 设备的地址范围内，I/O 端口地址空间中可以注册的最大可能 ISA 设备数量的宏。
