=============================
设备驱动设计模式
=============================

本文档描述了在设备驱动中常见的几种设计模式。
很可能会有子系统维护者要求驱动开发者遵循这些设计模式。

1. 状态容器
2. `container_of()`


1. 状态容器
~~~~~~~~~~~~~~

尽管内核中存在一些假设仅会在特定系统上被`probe()`一次的设备驱动（即单例），但通常的做法是假设该驱动绑定的设备将会出现多次实例。这意味着`probe()`函数及其所有回调都需要能够重入。
实现这一点最常见的方法是使用状态容器设计模式。它通常具有以下形式：

```c
struct foo {
    spinlock_t lock; /* 示例成员 */
    (...其他成员...)
};

static int foo_probe(...)
{
    struct foo *foo;

    foo = devm_kzalloc(dev, sizeof(*foo), GFP_KERNEL);
    if (!foo)
        return -ENOMEM;
    spin_lock_init(&foo->lock);
    (...其他初始化代码...)
}
```

每当调用`probe()`时，都会在内存中创建一个`struct foo`实例。这就是我们为这个设备驱动实例的状态容器。
当然，之后必须将这个实例传递给所有需要访问状态及其成员的函数。
例如，如果驱动正在注册中断处理程序，则可以像这样传递`struct foo`的指针：

```c
static irqreturn_t foo_handler(int irq, void *arg)
{
    struct foo *foo = arg;
    (...处理中断...)
}

static int foo_probe(...)
{
    struct foo *foo;

    (...初始化代码...)
    ret = request_irq(irq, foo_handler, 0, "foo", foo);
}
```

这样，你总能在中断处理程序中获得指向正确`foo`实例的指针。

2. `container_of()`
~~~~~~~~~~~~~~~~~~~~

基于上述例子，我们添加了一个卸载的工作项：

```c
struct foo {
    spinlock_t lock;
    struct workqueue_struct *wq;
    struct work_struct offload;
    (...其他成员...)
};

static void foo_work(struct work_struct *work)
{
    struct foo *foo = container_of(work, struct foo, offload);

    (...执行工作...)
}

static irqreturn_t foo_handler(int irq, void *arg)
{
    struct foo *foo = arg;

    queue_work(foo->wq, &foo->offload);
    (...其他处理...)
}

static int foo_probe(...)
{
    struct foo *foo;

    foo->wq = create_singlethread_workqueue("foo-wq");
    INIT_WORK(&foo->offload, foo_work);
    (...其他初始化代码...)
}
```

对于hrtimer或其他类似机制，它们返回一个指向结构体成员的单一参数并在回调中使用的情况，设计模式相同。
`container_of()`是一个在`<linux/kernel.h>`中定义的宏。

`container_of()`的作用是从指向成员的指针获取指向包含该成员的结构体的指针。通过简单的减法操作使用标准C中的`offsetof()`宏来实现这一点，这允许类似面向对象的行为。
需要注意的是，包含的成员不能是指针，而必须是实际的成员，这样才能生效。
我们可以看到，这样我们就避免了对`struct foo *`实例的全局指针，同时仍然保持传递给工作函数的参数为一个指针。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
