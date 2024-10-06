### 阴影变量
阴影变量是一种简单的方法，用于让实时补丁模块将额外的“阴影”数据与现有的数据结构关联起来。阴影数据独立于父数据结构分配，而父数据结构保持不变。本文档中描述的阴影变量API用于分配/添加和移除/释放阴影变量到其父数据结构。实现引入了一个全局内核哈希表，该哈希表将父对象指针与其阴影数据的数字标识符关联起来。数字标识符是一个简单的枚举，可以用来描述阴影变量的版本、类别或类型等。更具体地说，父指针作为哈希表键，而数字ID随后过滤哈希表查询。多个阴影变量可以附加到同一个父对象上，但它们的数字标识符将它们区分开来。

1. 简要API总结
===============
（请参阅livepatch/shadow.c中的完整API使用文档。）

一个哈希表引用了所有阴影变量。这些引用通过<obj, id>对存储和检索。
- `klp_shadow` 变量数据结构封装了跟踪元数据和阴影数据：
  - 元数据
    - `obj` - 指向父对象的指针
    - `id` - 数据标识符
  - `data[]` - 存储阴影数据

需要注意的是，默认情况下 `klp_shadow_alloc()` 和 `klp_shadow_get_or_alloc()` 将变量清零。当需要非零值时，它们还允许调用自定义构造函数。调用者应提供所需的互斥操作。
请注意，构造函数是在 `klp_shadow_lock` 自旋锁下被调用的，这允许在新变量分配时执行只能执行一次的操作。
- `klp_shadow_get()` - 获取阴影变量数据指针
  - 在哈希表中搜索 <obj, id> 对

- `klp_shadow_alloc()` - 分配并添加一个新的阴影变量
  - 在哈希表中搜索 <obj, id> 对
  - 如果已存在
    - 发出警告并返回 NULL
  - 如果 <obj, id> 不存在
    - 分配一个新的阴影变量
    - 使用提供的自定义构造函数和数据初始化变量
    - 将 <obj, id> 添加到全局哈希表

- `klp_shadow_get_or_alloc()` - 获取现有或分配新的阴影变量
  - 在哈希表中搜索 <obj, id> 对
  - 如果已存在
    - 返回现有的阴影变量
  - 如果 <obj, id> 不存在
    - 分配一个新的阴影变量
    - 使用提供的自定义构造函数和数据初始化变量
    - 将 <obj, id> 对添加到全局哈希表

- `klp_shadow_free()` - 解除并释放 <obj, id> 阴影变量
  - 从全局哈希表中查找并移除 <obj, id> 引用
    - 如果找到
      - 调用定义的析构函数
      - 释放阴影变量

- `klp_shadow_free_all()` - 解除并释放所有 <_, id> 阴影变量
  - 从全局哈希表中查找并移除任何 <_, id> 引用
    - 如果找到
      - 调用定义的析构函数
      - 释放阴影变量

2. 使用案例
============
（请参阅samples/livepatch/中的示例阴影变量实时补丁模块以获取完整的演示。）

对于以下使用案例示例，请考虑提交 1d147bfa6429（"mac80211: fix AP powersave TX vs. wakeup race"），该提交在net/mac80211/sta_info.h :: struct sta_info 中添加了一个自旋锁。每个使用案例示例都可以视为该修复的一个独立实时补丁实现。
匹配父对象生命周期
---------------------
如果父数据结构频繁创建和销毁，可能最简单的方法是将其阴影变量的生命周期与相同的分配和释放函数对齐。在这种情况下，父数据结构通常会被分配、初始化，然后以某种方式注册。阴影变量的分配和设置可以被视为父对象初始化的一部分，并应在父对象“上线”之前完成（即，在为这个 <obj, id> 对进行任何阴影变量get-API请求之前）。

对于提交 1d147bfa6429，当分配一个父 `sta_info` 结构时，分配一个 `ps_lock` 指针的阴影副本，然后初始化它：

```c
#define PS_LOCK 1
struct sta_info *sta_info_alloc(struct ieee80211_sub_if_data *sdata,
				const u8 *addr, gfp_t gfp)
{
	struct sta_info *sta;
	spinlock_t *ps_lock;

	/* 创建父结构 */
	sta = kzalloc(sizeof(*sta) + hw->sta_data_size, gfp);

	/* 附加相应的阴影变量，然后初始化它 */
	ps_lock = klp_shadow_alloc(sta, PS_LOCK, sizeof(*ps_lock), gfp,
				   NULL, NULL);
	if (!ps_lock)
		goto shadow_fail;
	spin_lock_init(ps_lock);
	..
```

当需要 `ps_lock` 时，通过阴影变量API查询以获取特定 `struct sta_info` 的一个实例：

```c
void ieee80211_sta_ps_deliver_wakeup(struct sta_info *sta)
{
	spinlock_t *ps_lock;

	/* 同步于 ieee80211_tx_h_unicast_ps_buf */
	ps_lock = klp_shadow_get(sta, PS_LOCK);
	if (ps_lock)
		spin_lock(ps_lock);
	..
```

当父 `sta_info` 结构被释放时，首先释放阴影变量：

```c
void sta_info_free(struct ieee80211_local *local, struct sta_info *sta)
{
	klp_shadow_free(sta, PS_LOCK, NULL);
	kfree(sta);
	..
```
飞行中的父对象
------------------------

有时可能不方便或无法在父对象旁边分配影子变量。或者，实时补丁修复可能只需要为父对象实例的子集分配影子变量。在这种情况下，可以使用 `klp_shadow_get_or_alloc()` 调用来将影子变量附加到已经处于运行状态的父对象上。对于提交 1d147bfa6429，在 `ieee80211_sta_ps_deliver_wakeup()` 函数中分配一个影子自旋锁是一个不错的选择：

```c
int ps_lock_shadow_ctor(void *obj, void *shadow_data, void *ctor_data)
{
    spinlock_t *lock = shadow_data;

    spin_lock_init(lock);
    return 0;
}

#define PS_LOCK 1
void ieee80211_sta_ps_deliver_wakeup(struct sta_info *sta)
{
    spinlock_t *ps_lock;

    /* 同步 ieee80211_tx_h_unicast_ps_buf */
    ps_lock = klp_shadow_get_or_alloc(sta, PS_LOCK,
            sizeof(*ps_lock), GFP_ATOMIC,
            ps_lock_shadow_ctor, NULL);

    if (ps_lock)
        spin_lock(ps_lock);
    ...
}
```

这种用法仅在需要时创建影子变量，否则会使用已经为这个 `<obj, id>` 对创建的影子变量。
与之前的用例类似，影子自旋锁也需要被清理。影子变量可以在其父对象释放之前释放，甚至在其本身不再需要时释放。

其他用例
---------------

影子变量还可以用作标志，表示数据结构是由新的实时补丁代码分配的。在这种情况下，影子变量持有的数据值并不重要，其存在表明如何处理父对象。

3. 参考资料
=============

* [https://github.com/dynup/kpatch](https://github.com/dynup/kpatch)

  实时补丁实现基于 kpatch 版本的影子变量。
* [http://files.mkgnu.net/files/dynamos/doc/papers/dynamos_eurosys_07.pdf](http://files.mkgnu.net/files/dynamos/doc/papers/dynamos_eurosys_07.pdf)

  Dynamic and Adaptive Updates of Non-Quiescent Subsystems in Commodity Operating System Kernels (Kritis Makris, Kyung Dong Ryu 2007) 提出了称为“影子数据结构”的数据类型更新技术。
