监管器驱动接口
==========================

监管器驱动接口相对简单，并设计用于允许
监管器驱动向核心框架注册它们的服务。
注册
============

驱动可以通过调用以下函数来注册一个监管器：

  struct regulator_dev *regulator_register(struct regulator_desc *regulator_desc,
                                           const struct regulator_config *config);

这将把监管器的能力和操作注册到监管器核心中。
可以通过调用以下函数来取消注册监管器：

  void regulator_unregister(struct regulator_dev *rdev);


监管器事件
================

监管器可以通过调用以下函数向消费者驱动发送事件（例如过温、欠压等）：

  int regulator_notifier_call_chain(struct regulator_dev *rdev,
                                    unsigned long event, void *data);
