```
SPDX-License-Identifier: GPL-2.0

==============================================
6LoWPAN 接口的 Netdev 私有数据区
==============================================

所有支持 6LoWPAN 的网络设备，即所有具有 ARPHRD_6LOWPAN 的接口，
必须将 `struct lowpan_priv` 放在 `netdev_priv` 的开头。
每个接口的私有大小应通过以下方式计算：

```c
dev->priv_size = LOWPAN_PRIV_SIZE(LL_6LOWPAN_PRIV_DATA);
```

其中 `LL_6LOWPAN_PRIV_DATA` 是链路层 6LoWPAN 私有数据结构的大小。

要访问 `LL_6LOWPAN_PRIV_DATA` 结构，可以进行类型转换：

```c
lowpan_priv(dev)->priv;
```

转换为你的 `LL_6LOWPAN_PRIV_DATA` 结构。

在注册 6LoWPAN 网络设备之前，必须运行以下代码：

```c
lowpan_netdev_setup(dev, LOWPAN_LLTYPE_FOOBAR);
```

其中 `LOWPAN_LLTYPE_FOOBAR` 是你定义的 6LoWPAN 链路层类型的枚举值 `enum lowpan_lltypes`。

通常评估私有数据时，你可以这样做：

```c
static inline struct lowpan_priv_foobar *
lowpan_foobar_priv(struct net_device *dev)
{
    return (struct lowpan_priv_foobar *)lowpan_priv(dev)->priv;
}
```

```c
switch (dev->type) {
case ARPHRD_6LOWPAN:
    lowpan_priv = lowpan_priv(dev);
    /* 进行与 ARPHRD_6LOWPAN 相关的操作 */
    switch (lowpan_priv->lltype) {
    case LOWPAN_LLTYPE_FOOBAR:
        /* 在这里处理 802.15.4 6LoWPAN */
        lowpan_foobar_priv(dev)->bar = foo;
        break;
    // 其他情况
    }
    break;
// 其他类型
}
```

对于通用 6LoWPAN 分支（"net/6lowpan"），你可以移除对 ARPHRD_6LOWPAN 的检查，
因为你可以确定这些函数是由 ARPHRD_6LOWPAN 接口调用的。
```
