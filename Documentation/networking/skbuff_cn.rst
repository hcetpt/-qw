SPDX 许可证标识符: GPL-2.0

`struct sk_buff`
================

`:c:type:' `sk_buff` 是表示数据包的主要网络结构。

基本的 `sk_buff` 几何形状
----------------------

.. kernel-doc:: include/linux/skbuff.h
   :doc: 基本的 `sk_buff` 几何形状

共享的 `skbs` 和 `skb` 克隆
--------------------------

`:c:member:' `sk_buff.users` 是一个简单的引用计数，允许多个实体保持 `struct sk_buff` 的存活。如果 `sk_buff.users != 1`，则称这些 `skbs` 为共享 `skbs`（参见 `skb_shared()`）。`skb_clone()` 允许快速复制 `skbs`。数据缓冲区不会被复制，但调用者会得到一个新的元数据结构（`struct sk_buff`）。`&skb_shared_info.refcount` 表示指向相同数据包数据的 `skbs` 数量（即克隆）。

数据引用和无头 `skbs`
---------------------------

.. kernel-doc:: include/linux/skbuff.h
   :doc: 数据引用和无头 `skbs`

校验和信息
--------------------

.. kernel-doc:: include/linux/skbuff.h
   :doc: `skb` 校验和
