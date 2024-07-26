SPDX 许可证标识符: GPL-2.0

`struct sk_buff` 结构体
========================

`:c:type:'`sk_buff`是代表数据包的主要网络结构。
基本的 `sk_buff` 几何形状
------------------------------

.. kernel-doc:: include/linux/skbuff.h
   :doc: 基本的 `sk_buff` 几何形状

共享的 `sk_buff` 和 `sk_buff` 的克隆
---------------------------------------

`:c:member:` `sk_buff.users` 是一个简单的引用计数，允许多个实体保持 `struct sk_buff` 的活性。当 `sk_buff.users != 1` 时，这些 `sk_buff` 被称为共享的 `sk_buff`（参见 `skb_shared()`）。`skb_clone()` 允许快速复制 `sk_buff`。数据缓冲区本身不会被复制，但调用者会得到一个新的元数据结构 (`struct sk_buff`)。`&skb_shared_info.refcount` 表示指向相同的数据包数据的 `sk_buff` 数量（即克隆的数量）。

数据引用和无头部的 `sk_buff`
---------------------------------

.. kernel-doc:: include/linux/skbuff.h
   :doc: 数据引用和无头部的 `sk_buff`

校验和信息
--------------

.. kernel-doc:: include/linux/skbuff.h
   :doc: `sk_buff` 校验和
