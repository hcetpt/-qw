```plaintext
# SPDX 许可证标识符: GPL-2.0

==============================================
6lowpan 接口的网络设备私有数据区
==============================================

所有支持 6lowpan 的网络设备，即所有具有 ARPHRD_6LOWPAN 类型的接口，
必须将 "struct lowpan_priv" 放置在网络设备私有数据区(netdev_priv)的开始位置。
每个接口的私有数据大小(priv_size)应该通过以下方式计算：

dev->priv_size = LOWPAN_PRIV_SIZE(LL_6LOWPAN_PRIV_DATA);

其中 LL_6LOWPAN_PRIV_DATA 是 6lowpan 链路层私有数据结构的大小。
要访问 LL_6LOWPAN_PRIV_DATA 结构，可以进行类型转换：

lowpan_priv(dev)->priv;

转换为你的 LL_6LOWPAN_PRIV_DATA 结构。
在注册低功耗 6lowpan 网络设备接口之前，必须运行：

lowpan_netdev_setup(dev, LOWPAN_LLTYPE_FOOBAR);

其中 LOWPAN_LLTYPE_FOOBAR 是你定义的 6LoWPAN 链路层类型的枚举值 (enum lowpan_lltypes)。
通常情况下，你可以这样访问私有数据：

static inline struct lowpan_priv_foobar *
lowpan_foobar_priv(struct net_device *dev)
{
	return (struct lowpan_priv_foobar *)lowpan_priv(dev)->priv;
}

switch (dev->type) {
case ARPHRD_6LOWPAN:
	lowpan_priv = lowpan_priv(dev);
	/* 进行与 ARPHRD_6LOWPAN 相关的操作 */
	switch (lowpan_priv->lltype) {
	case LOWPAN_LLTYPE_FOOBAR:
		/* 在这里处理 802.15.4 6LoWPAN */
		lowpan_foobar_priv(dev)->bar = foo;
		break;
	..
}
	break;
 ..
}

对于通用 6lowpan 分支（"net/6lowpan"），你可以移除对 ARPHRD_6LOWPAN 的检查，
因为这些函数肯定是由 ARPHRD_6LOWPAN 接口调用的。
```
