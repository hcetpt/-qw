你从未想了解的关于 kobjects（内核对象）、ksets（内核集合）和 ktypes（内核类型）的一切

:作者: Greg Kroah-Hartman <gregkh@linuxfoundation.org>
:最后更新: 2007年12月19日

基于 Jon Corbet 为 lwn.net 在2003年10月1日撰写的原始文章，位于 https://lwn.net/Articles/51437/

理解驱动模型及其所基于的 kobject 抽象的一个难点在于，没有一个明显的起点。处理 kobjects 需要理解几种相互引用的不同类型。为了使事情变得简单些，我们将采取多阶段的方法，从模糊的概念开始，逐步添加细节。为此，这里有一些我们即将讨论的一些术语的快速定义：
- kobject 是 struct kobject 类型的对象。kobjects 有一个名字和一个引用计数。kobject 还包含一个父指针（允许对象组织成层次结构），特定的类型，并且通常在 sysfs 虚拟文件系统中有一个表示。
kobjects 通常本身并不引人注目；相反，它们通常嵌入在其他结构体中，这些结构体包含了代码真正关心的内容。
任何结构体都不应该**永远**包含超过一个嵌入的 kobject。
如果包含了一个以上的 kobject，那么对象的引用计数肯定会出错，你的代码将会有bug。因此，请不要这样做。
- ktype 是嵌入 kobject 的对象类型。每一个嵌入 kobject 的结构体都需要一个对应的 ktype。ktype 控制着 kobject 创建和销毁时的行为。
- kset 是一组 kobjects。这些 kobjects 可以是相同的 ktype 或属于不同的 ktypes。kset 是 kobjects 集合的基本容器类型。ksets 包含自己的 kobjects，但你可以安全地忽略这个实现细节，因为 kset 核心代码会自动处理这个 kobject。
当你看到一个 sysfs 目录充满了其他的目录时，通常每个这样的目录对应于同一个 kset 中的一个 kobject。

我们将探讨如何创建和操作所有这些类型。我们将采取自底向上的方法，所以我们先回到 kobjects 上来。
嵌入 kobjects
=============

内核代码很少创建独立的 kobject，除非下面解释的一个主要例外。相反，kobjects 用于控制对更大、特定领域的对象的访问。为此，kobjects 会被发现在其他结构体中嵌入。如果你习惯于用面向对象的方式来思考问题，kobjects 可以被看作是一个顶级的抽象类，其他类从它派生而来。kobject 实现了一组自身不是特别有用但对其他对象来说很不错的功能。C语言不允许直接表达继承，因此必须使用其他技术，如结构体嵌入等。
作为旁注，对于熟悉内核链表实现的人来说，
这类似于 "list_head" 结构体很少单独有用，
但总是嵌入在我们感兴趣的较大对象中。

因此，例如，`drivers/uio/uio.c` 中的 UIO 代码有一个结构体定义了与 UIO 设备相关的内存区域：

```markdown
    struct uio_map {
            struct kobject kobj;
            struct uio_mem *mem;
    };
```

如果你有一个 `struct uio_map` 结构体，要找到其中嵌入的 kobject 只需使用 kobj 成员即可。然而，处理 kobject 的代码经常会遇到相反的问题：给定一个 `struct kobject` 指针，指向包含该 kobject 的结构体的指针是什么？你必须避免一些技巧（如假设 kobject 在结构体的开头），而是使用 `container_of()` 宏，该宏可以在 `<linux/kernel.h>` 中找到：

```c
    container_of(ptr, type, member)
```

其中：

  * `ptr` 是指向嵌入式 kobject 的指针，
  * `type` 是包含结构体的类型，
  * `member` 是 `ptr` 所指向的结构体字段的名称。
`container_of()` 的返回值是指向相应容器类型的指针。因此，例如，指向 `struct kobject` 的指针 `kp`，如果它位于 `struct uio_map` 内，则可以转换为指向包含的 `uio_map` 结构体的指针：

```c
    struct uio_map *u_map = container_of(kp, struct uio_map, kobj);
```

为了方便起见，程序员通常会为从 kobject 指针“反向转换”到包含类型定义一个简单的宏。确切地，在前面提到的 `drivers/uio/uio.c` 中就发生了这种情况，如下所示：

```c
    struct uio_map {
            struct kobject kobj;
            struct uio_mem *mem;
    };

    #define to_map(map) container_of(map, struct uio_map, kobj)
```

其中宏参数 "map" 是指向问题中的 `struct kobject` 的指针。然后通过以下方式调用该宏：

```c
    struct uio_map *map = to_map(kobj);
```

### kobject 的初始化

创建 kobject 的代码当然必须初始化该对象。某些内部字段通过（强制性的）调用 `kobject_init()` 来设置：

```c
    void kobject_init(struct kobject *kobj, const struct kobj_type *ktype);
```

为了正确创建 kobject，`ktype` 是必需的，因为每个 kobject 都必须关联一个 `kobj_type`。调用 `kobject_init()` 后，为了将 kobject 注册到 sysfs，必须调用 `kobject_add()` 函数：

```c
    int kobject_add(struct kobject *kobj, struct kobject *parent,
                    const char *fmt, ...);
```

这会正确设置 kobject 的父级和名称。如果 kobject 要与特定的 kset 关联，那么在调用 `kobject_add()` 之前必须设置 `kobj->kset`。如果 kset 与 kobject 相关联，那么在调用 `kobject_add()` 时可以将 kobject 的父级设置为 NULL，此时 kobject 的父级将是 kset 本身。

由于 kobject 的名称是在添加到内核时设置的，所以不应直接操纵 kobject 的名称。如果你必须更改 kobject 的名称，请调用 `kobject_rename()`：

```c
    int kobject_rename(struct kobject *kobj, const char *new_name);
```

`kobject_rename()` 不执行任何锁定操作，也没有明确的概念来确定哪些名称是有效的，因此调用者必须提供自己的合理性检查和序列化。

存在一个名为 `kobject_set_name()` 的函数，但它属于遗留代码，并正在被移除。如果你的代码需要调用此函数，它是不正确的并需要修正。

要正确访问 kobject 的名称，请使用 `kobject_name()` 函数：

```c
    const char *kobject_name(const struct kobject * kobj);
```

有一个辅助函数可以同时初始化和将 kobject 添加到内核中，不出所料，这个函数名为 `kobject_init_and_add()`：

```c
    int kobject_init_and_add(struct kobject *kobj, const struct kobj_type *ktype,
                             struct kobject *parent, const char *fmt, ...);
```

这些参数与上面描述的独立的 `kobject_init()` 和 `kobject_add()` 函数相同。

### Uevent

当 kobject 已经注册到 kobject 核心后，你需要向外界宣布它的创建。这可以通过调用 `kobject_uevent()` 来完成：

```c
    int kobject_uevent(struct kobject *kobj, enum kobject_action action);
```

当首次将 kobject 添加到内核时，请使用 `KOBJ_ADD` 动作。

这应该仅在 kobject 的任何属性或子项都已正确初始化之后进行，因为当这个调用发生时，用户空间会立即开始查找它们。

当 kobject 从内核中移除时（具体如何操作将在下面详细说明），kobject 核心会自动创建 `KOBJ_REMOVE` 的 uevent，因此调用者不必担心手动完成此事。

### 引用计数

kobject 的一个关键功能是作为其所在对象的引用计数器。只要存在对该对象的引用，该对象（及其支持代码）就必须继续存在。

用于操作 kobject 引用计数的低级别函数包括：

```c
    struct kobject *kobject_get(struct kobject *kobj);
    void kobject_put(struct kobject *kobj);
```

成功调用 `kobject_get()` 将会增加 kobject 的引用计数，并返回指向 kobject 的指针。
当一个引用被释放时，对 `kobject_put()` 的调用会递减引用计数，并可能释放该对象。请注意，`kobject_init()` 将引用计数设置为1，因此设置 kobject 的代码最终需要执行 `kobject_put()` 来释放这个引用。
因为 kobjects 是动态的，它们不能静态声明或在栈上声明，而应该始终动态分配。未来的内核版本将包含对静态创建的 kobjects 的运行时检查，并警告开发者这种不正确的使用方式。
如果你仅希望使用 kobject 作为你的结构体提供引用计数，请使用 `struct kref`；使用 kobject 可能是过度设计。关于如何使用 `struct kref` 的更多信息，请参阅 Linux 内核源代码中的文件 `Documentation/core-api/kref.rst`。
创建“简单”的 kobjects
==========================

有时，开发人员所需要的只是在 sysfs 层次结构中创建一个简单的目录，而不必处理 ksets、show 和 store 函数以及其他细节的全部复杂性。这是创建单个 kobject 的唯一例外。为了创建这样的条目，可以使用如下函数：

    ```c
    struct kobject *kobject_create_and_add(const char *name, struct kobject *parent);
    ```

此函数将创建一个 kobject 并将其放置在 sysfs 中指定父 kobject 下的位置。为了创建与该 kobject 关联的简单属性，可以使用：

    ```c
    int sysfs_create_file(struct kobject *kobj, const struct attribute *attr);
    ```

或者：

    ```c
    int sysfs_create_group(struct kobject *kobj, const struct attribute_group *grp);
    ```

在此处使用的两种类型的属性（使用 `kobject_create_and_add()` 创建的 kobject），可以是 `kobj_attribute` 类型，因此不需要创建任何特殊的自定义属性。
请参阅示例模块 `samples/kobject/kobject-example.c`，以获取简单 kobject 和属性实现的实例。
ktypes 和释放方法
==========================

讨论中仍然缺少的一个重要点是当 kobject 的引用计数达到零时会发生什么。创建 kobject 的代码通常不知道这何时会发生；如果它知道的话，那么使用 kobject 本身就没有多少意义了。即使可预测的对象生命周期，在引入 sysfs 后也会变得更加复杂，因为内核的其他部分可以获得系统中任何注册的 kobject 的引用。
最终结果是：受 kobject 保护的结构体不能在其引用计数变为零之前被释放。引用计数不由创建 kobject 的代码直接控制。因此，该代码必须在最后一个对其 kobject 的引用消失时异步地被通知。
一旦通过 `kobject_add()` 注册了你的 kobject，你绝不能直接使用 `kfree()` 来释放它。唯一安全的方式是使用 `kobject_put()`。在 `kobject_init()` 后总是使用 `kobject_put()` 是一种好的实践，这样可以避免出现错误。
这种通知是通过 kobject 的 `release()` 方法完成的。通常此类方法的形式如下：

    ```c
    void my_object_release(struct kobject *kobj)
    {
            struct my_object *mine = container_of(kobj, struct my_object, kobj);

            /* 对该对象进行任何额外清理，然后... */
            kfree(mine);
    }
    ```

有一个非常重要的点不容忽视：每个 kobject 必须有一个 `release()` 方法，并且该 kobject 必须一直存在（处于一致状态）直到该方法被调用。如果不满足这些约束，则代码存在问题。请注意，如果忘记提供 `release()` 方法，内核将会发出警告。不要试图通过提供一个“空”的释放函数来消除这个警告。
如果你的清理函数只需要调用 `kfree()`，则你必须创建一个包装函数，该函数使用 `container_of()` 上转型到正确的类型（如上面的例子所示），然后对整个结构体调用 `kfree()`。
请注意，kobject的名字在释放函数中是可用的，但在这个回调中**不得**修改这个名字。否则，kobject核心中会产生内存泄漏，这会让人们不高兴。
有趣的是，`release()`方法并不是存储在kobject本身中；相反，它与ktype关联。因此，让我们来介绍`struct kobj_type`：

    struct kobj_type {
            void (*release)(struct kobject *kobj);
            const struct sysfs_ops *sysfs_ops;
            const struct attribute_group **default_groups;
            const struct kobj_ns_type_operations *(*child_ns_type)(struct kobject *kobj);
            const void *(*namespace)(struct kobject *kobj);
            void (*get_ownership)(struct kobject *kobj, kuid_t *uid, kgid_t *gid);
    };

这个结构体用于描述特定类型的kobject（或者更准确地说，是包含对象的类型）。每个kobject都需要有一个关联的`kobj_type`结构体；当调用`kobject_init()`或`kobject_init_and_add()`时必须指定指向该结构体的指针。
`struct kobj_type`中的`release`字段当然是指向这种类型的kobject的`release()`方法的指针。其他两个字段（`sysfs_ops`和`default_groups`）控制这种类型的对象如何在sysfs中表示；它们超出了本文档的范围。
`default_groups`指针是一个默认属性列表，这些属性将为使用此ktype注册的任何kobject自动生成。
### ksets
####

kset仅仅是想要相互关联的一组kobjects。虽然没有规定它们必须具有相同的ktype，但如果它们不同，请务必小心。
kset的功能包括：

- 它充当一组对象的容器。内核可以使用kset来跟踪“所有块设备”或“所有PCI设备驱动程序”。

- kset也是sysfs中的一个子目录，在这里与kset相关联的kobjects可以显示出来。每个kset都包含一个kobject，它可以被设置为其他kobjects的父级；sysfs层次结构的顶级目录就是以这种方式构建的。

- kset可以支持kobjects的“热插拔”，并影响如何向用户空间报告uevent事件。
从面向对象的角度来看，“kset”是顶层容器类；ksets包含它们自己的kobject，但该kobject由kset代码管理，不应由其他用户操纵。
kset将其子项保存在一个标准的内核链表中。Kobjects通过它们的`kset`字段指向其包含的kset。在几乎所有情况下，属于kset的kobjects都有该kset（严格来说，是它的嵌入式kobject）作为它们的父级。
由于kset内部包含了一个kobject，因此应该总是动态创建kset，而不要静态声明或在栈上声明。要创建一个新的kset，请使用：

  struct kset *kset_create_and_add(const char *name,
                                   const struct kset_uevent_ops *uevent_ops,
                                   struct kobject *parent_kobj);

当你完成对kset的操作后，请调用：

  void kset_unregister(struct kset *k);

来销毁它。这会将kset从sysfs中移除，并减少其引用计数。当引用计数降为零时，kset将被释放。
因为可能仍然存在对 `kset` 的其他引用，所以在 `kset_unregister()` 返回后，释放操作可能会发生。
使用 `kset` 的一个例子可以在内核树中的 `samples/kobject/kset-example.c` 文件中看到。
如果一个 `kset` 希望控制与其关联的 `kobject` 的 uevent 操作，它可以使用 `struct kset_uevent_ops` 来处理它：

```c
struct kset_uevent_ops {
        int (* const filter)(struct kobject *kobj);
        const char *(* const name)(struct kobject *kobj);
        int (* const uevent)(struct kobject *kobj, struct kobj_uevent_env *env);
};
```

`filter` 函数允许 `kset` 阻止特定 `kobject` 向用户空间发送 uevent。如果函数返回 0，则不会发送 uevent。
`name` 函数将被调用来覆盖默认情况下发送给用户空间的 `kset` 名称。默认情况下，名称与 `kset` 相同，但如果存在这个函数，它可以覆盖这个名称。
当 uevent 即将发送到用户空间时，`uevent` 函数将被调用以允许向 uevent 添加更多的环境变量。

有人可能会问，具体来说，一个 `kobject` 是如何添加到 `kset` 中的，鉴于目前还没有介绍执行该功能的函数。答案是这项任务由 `kobject_add()` 处理。当一个 `kobject` 被传递给 `kobject_add()` 时，它的 `kset` 成员应指向该 `kobject` 将属于的 `kset`。`kobject_add()` 将处理剩余的工作。
如果属于 `kset` 的 `kobject` 没有设置父 `kobject`，它将被添加到 `kset` 的目录中。并非所有 `kset` 的成员都必然位于 `kset` 目录中。如果在添加 `kobject` 之前指定了显式的父 `kobject`，则 `kobject` 将注册到 `kset`，但会在父 `kobject` 下方添加。

### Kobject 清除

成功地将 `kobject` 注册到 `kobject` 核心之后，在代码不再需要它时必须进行清理。为此，请调用 `kobject_put()`。通过这样做，`kobject` 核心会自动清理此 `kobject` 分配的所有内存。如果为对象发送了 `KOBJ_ADD` uevent，则会发送相应的 `KOBJ_REMOVE` uevent，并且会适当地处理任何其他 sysfs 清理工作。
如果你需要分两阶段删除 `kobject`（例如，当你不允许睡眠时需要销毁对象），可以调用 `kobject_del()`，这将从 sysfs 注销 `kobject`。这使得 `kobject` “不可见”，但它不会被清理，且对象的引用计数仍然相同。稍后调用 `kobject_put()` 以完成与 `kobject` 相关的内存清理。
如果构建了循环引用，可以使用 `kobject_del()` 来解除对父对象的引用。在某些情况下，父对象引用子对象是合理的。循环引用必须通过明确调用 `kobject_del()` 来打破，以便调用释放函数，并使前循环中的对象互相释放。
可以正确使用 ksets 和 kobjects 的示例代码，请参阅：
=========================

为了更完整地展示如何正确使用 ksets 和 kobjects，可参考示例程序 ``samples/kobject/{kobject-example.c,kset-example.c}``，
如果你选择了 ``CONFIG_SAMPLE_KOBJECT``，这些示例程序将会被构建为可加载模块。
