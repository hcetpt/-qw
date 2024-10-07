==========================
调节器驱动接口
==========================

调节器驱动接口相对简单，设计目的是允许调节器驱动向核心框架注册其服务。
注册
============

驱动可以通过调用以下函数来注册一个调节器：

```c
struct regulator_dev *regulator_register(struct regulator_desc *regulator_desc,
					 const struct regulator_config *config);
```

这将向调节器核心注册调节器的能力和操作。
可以通过调用以下函数来取消注册调节器：

```c
void regulator_unregister(struct regulator_dev *rdev);
```

调节器事件
================

调节器可以通过调用以下函数发送事件（例如过温、欠压等）给消费者驱动：

```c
int regulator_notifier_call_chain(struct regulator_dev *rdev,
					unsigned long event, void *data);
```
