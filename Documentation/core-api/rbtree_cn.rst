# 红黑树 (rbtree) 在 Linux 中的应用

=================

:日期: 2007年1月18日
:作者: Rob Landley <rob@landley.net>

## 红黑树是什么以及它们的用途？

红黑树是一种自平衡二叉查找树，用于存储可排序的键值对数据。这与基数树不同（后者用于高效地存储稀疏数组，因此使用长整数索引来插入、访问和删除节点）和哈希表（后者不保持排序以便于按顺序遍历，并且必须针对特定大小和哈希函数进行调整，而红黑树则可以优雅地扩展以存储任意键）。红黑树与AVL树类似，但在实时最坏情况下的插入和删除性能方面提供了更快的界限（最多两次旋转和三次旋转来平衡树），虽然查找时间略慢（但仍然是O(log n))。

引用《Linux Weekly News》的话：

> 内核中有许多红黑树在使用。
>
> 截止期限调度器和CFQ I/O调度器使用红黑树来跟踪请求；CD/DVD包驱动程序也做同样的事情。
>
> 高分辨率定时器代码使用红黑树来组织未决的定时器请求。ext3文件系统使用红黑树来跟踪目录项。虚拟内存区域（VMAs）、epoll文件描述符、加密密钥和“层次化令牌桶”调度器中的网络包都使用红黑树进行跟踪。

本文档涵盖Linux红黑树实现的使用。有关红黑树特性和实现的更多信息，请参见：

- 《Linux Weekly News》关于红黑树的文章：[https://lwn.net/Articles/184495/](https://lwn.net/Articles/184495/)
- 维基百科关于红黑树的条目：[https://en.wikipedia.org/wiki/Red-black_tree](https://en.wikipedia.org/wiki/Red-black_tree)

## Linux中的红黑树实现

Linux的红黑树实现在文件“lib/rbtree.c”中。要使用它，请`#include <linux/rbtree.h>`。

Linux的红黑树实现经过了速度优化，因此比传统的树实现少了一层间接性（并具有更好的缓存局部性）。没有使用指向单独的`rb_node`和数据结构的指针，而是每个`struct rb_node`实例嵌入到它所组织的数据结构中。此外，没有使用比较回调函数指针，而是用户需要编写自己的树搜索和插入函数，这些函数调用提供的红黑树函数。锁定也是由红黑树代码的使用者自己处理的。

### 创建新的红黑树

红黑树中的数据节点是包含`struct rb_node`成员的结构体：

```c
struct mytype {
   struct rb_node node;
   char *keystring;
};
```

当处理嵌入的`struct rb_node`指针时，可以使用标准的`container_of()`宏访问包含的数据结构。此外，还可以直接通过`rb_entry(node, type, member)`访问单个成员。

在每个红黑树的根部是一个`rb_root`结构，可以通过以下方式初始化为空：

```c
struct rb_root mytree = RB_ROOT;
```

### 在红黑树中搜索值

为您的树编写搜索函数相当直接：从根开始，比较每个值，并根据需要跟随左或右分支。

示例：

```c
struct mytype *my_search(struct rb_root *root, char *string)
{
   struct rb_node *node = root->rb_node;

   while (node) {
      struct mytype *data = container_of(node, struct mytype, node);
      int result;

      result = strcmp(string, data->keystring);

      if (result < 0)
         node = node->rb_left;
      else if (result > 0)
         node = node->rb_right;
      else
         return data;
   }
   return NULL;
}
```

### 将数据插入红黑树

将数据插入树中首先涉及搜索新节点的插入位置，然后插入该节点并对树进行重新平衡（“重新着色”）。
插入操作与之前的搜索操作的不同之处在于需要找到新节点应嫁接的指针位置。新节点还需要链接到其父节点，以便进行再平衡操作。
例如：

```c
int my_insert(struct rb_root *root, struct mytype *data)
{
    struct rb_node **new = &(root->rb_node), *parent = NULL;

    /* 确定新节点的位置 */
    while (*new) {
        struct mytype *this = container_of(*new, struct mytype, node);
        int result = strcmp(data->keystring, this->keystring);

        parent = *new;
        if (result < 0)
            new = &((*new)->rb_left);
        else if (result > 0)
            new = &((*new)->rb_right);
        else
            return FALSE;
    }

    /* 添加新节点并重新平衡树 */
    rb_link_node(&data->node, parent, new);
    rb_insert_color(&data->node, root);

    return TRUE;
}
```

从红黑树中移除或替换现有数据
-----------------------------------

要从树中移除现有的节点，可以调用：

```c
void rb_erase(struct rb_node *victim, struct rb_root *tree);
```

例如：

```c
struct mytype *data = mysearch(&mytree, "walrus");

if (data) {
    rb_erase(&data->node, &mytree);
    myfree(data);
}
```

要使用具有相同键的新节点替换树中的现有节点，请调用：

```c
void rb_replace_node(struct rb_node *old, struct rb_node *new, struct rb_root *tree);
```

以这种方式替换节点不会重新排序树：如果新节点的键与旧节点不同，则红黑树可能会变得损坏。

遍历红黑树中存储的元素（按排序顺序）
-------------------------------------------

提供了四个函数来按排序顺序遍历红黑树的内容。这些函数适用于任意树，并且通常不需要被修改或包装（除了锁定目的）：

```c
struct rb_node *rb_first(struct rb_root *tree);
struct rb_node *rb_last(struct rb_root *tree);
struct rb_node *rb_next(struct rb_node *node);
struct rb_node *rb_prev(struct rb_node *node);
```

要开始遍历，请使用指向树根的指针调用`rb_first()`或`rb_last()`，这将返回一个指向树中第一个或最后一个元素所包含的节点结构的指针。要继续，可以通过在当前节点上调用`rb_next()`或`rb_prev()`来获取下一个或前一个节点。当没有更多的节点时，这将返回NULL。

迭代函数返回一个指向嵌入式`struct rb_node`的指针，可以从该指针通过`container_of()`宏访问包含的数据结构，也可以直接通过`rb_entry(node, type, member)`访问单个成员。
例如：

```c
struct rb_node *node;
for (node = rb_first(&mytree); node; node = rb_next(node))
    printk("key=%s\n", rb_entry(node, struct mytype, node)->keystring);
```

缓存的红黑树
--------------

计算最左侧（最小的）节点是二叉搜索树中常见的任务，如用于遍历或用户依赖于特定顺序来处理自己的逻辑。为此，用户可以使用`struct rb_root_cached`来优化O(logN)的`rb_first()`调用为简单的指针获取，避免可能昂贵的树迭代。这在维护上几乎没有任何运行时开销；尽管内存占用较大。
类似于`rb_root`结构，缓存的红黑树通过以下方式初始化为空：

```c
struct rb_root_cached mytree = RB_ROOT_CACHED;
```

缓存的红黑树只是常规的`rb_root`，但多了一个指针来缓存最左侧的节点。这允许`rb_root_cached`存在于任何`rb_root`可以存在的地方，这意味着也支持增强树以及几个额外的接口：

```c
struct rb_node *rb_first_cached(struct rb_root_cached *tree);
void rb_insert_color_cached(struct rb_node *, struct rb_root_cached *, bool);
void rb_erase_cached(struct rb_node *node, struct rb_root_cached *);
```

插入和删除调用都有它们对应增强树的版本：

```c
void rb_insert_augmented_cached(struct rb_node *node, struct rb_root_cached *, bool, struct rb_augment_callbacks *);
void rb_erase_augmented_cached(struct rb_node *, struct rb_root_cached *, struct rb_augment_callbacks *);
```

支持增强的红黑树
------------------

增强的红黑树是在每个节点中存储一些额外数据的红黑树，其中节点N的额外数据必须是N子树中所有节点内容的函数。这种数据可用于为红黑树增加新的功能。增强的红黑树是基于基本红黑树基础设施之上的可选特性。
希望使用此特性的红黑树用户在插入和删除节点时必须调用增强函数，并提供用户定义的增强回调。
实现增强红黑树操纵的C文件必须包含`<linux/rbtree_augmented.h>`而不是`<linux/rbtree.h>`。请注意，`linux/rbtree_augmented.h`暴露了一些红黑树实现细节，你不应该依赖这些细节；请坚持使用文档中的API，并不要从头文件中包含`<linux/rbtree_augmented.h>`，以尽量减少你的用户意外依赖这些实现细节的可能性。
在插入时，用户必须更新路径上插入节点的增强信息，然后像往常一样调用`rb_link_node()`，并代替通常的`rb_insert_color()`调用`rb_augment_inserted()`。
如果`rb_augment_inserted()`重新平衡了红黑树，它会回调到用户提供的函数来更新受影响子树的增强信息。
在删除一个节点时，用户必须调用`rb_erase_augmented()`而不是`rb_erase()`。`rb_erase_augmented()`会回调到用户提供的函数以更新受影响子树的增强信息。
在这两种情况下，回调是通过`struct rb_augment_callbacks`提供的。
需要定义三个回调：

- 传播回调，用于更新给定节点及其祖先的增强值，直到某个停止点（或NULL以更新到根节点）
- 复制回调，用于复制给定子树的增强值到新分配的子树根节点
- 树旋转回调，用于复制给定子树的增强值到新分配的子树根节点，并重新计算原子树根节点的增强信息
`rb_erase_augmented()`编译后的代码可能会内联传播和复制回调，这会导致一个较大的函数，因此每个增强的红黑树用户应该只有一个`rb_erase_augmented()`调用点以限制编译后的代码大小。

示例使用
^^^^^^^^^^^^

区间树是一个增强红黑树的例子。参考 - "算法导论"由Cormen, Leiserson, Rivest 和 Stein撰写
关于区间树的更多细节：

经典的红黑树有一个单一的键，它不能直接用来存储区间范围如[lo:hi]并快速查找是否有与新的lo:hi重叠或者找到是否有一个新的lo:hi的确切匹配。
然而，红黑树可以被增强以结构化的方式存储这样的区间范围，使其能够进行高效的查找和精确匹配。
存储在每个节点中的“额外信息”是在所有该节点后代中最大的hi (max_hi) 值。这个信息可以通过查看节点及其直接子节点来维护。并且这将用于O(log n)查找最低匹配（所有可能匹配中最低的起始地址）, 类似于如下所示：

```c
struct interval_tree_node *
interval_tree_first_match(struct rb_root *root,
			  unsigned long start, unsigned long last)
{
  struct interval_tree_node *node;

  if (!root->rb_node)
    return NULL;
  node = rb_entry(root->rb_node, struct interval_tree_node, rb);

  while (true) {
    if (node->rb.rb_left) {
      struct interval_tree_node *left =
	rb_entry(node->rb.rb_left,
		 struct interval_tree_node, rb);
      if (left->__subtree_last >= start) {
        /*
         * 左子树中的一些节点满足Cond2
         */ 
```
请注意，示例中的注释部分没有完整给出，需要根据具体上下文来确定。
Iterate to find the leftmost node `N` that meets the criteria:
* If it also satisfies `Cond1`, then this is the match we are looking for. Otherwise, there is no matching interval because nodes to the right of `N` cannot satisfy `Cond1` either.

```c
node = left;
continue;
```

```c
if (node->start <= last) {       /* Cond1 */
    if (node->last >= start)     /* Cond2 */
        return node;             /* node is the leftmost match */
    if (node->rb.rb_right) {
        node = rb_entry(node->rb.rb_right,
                        struct interval_tree_node, rb);
        if (node->__subtree_last >= start)
            continue;
    }
}
return NULL;                     /* No match */
```

The insertion and removal operations are defined using the following enhanced callback functions:

```c
static inline unsigned long
compute_subtree_last(struct interval_tree_node *node)
{
    unsigned long max = node->last, subtree_last;
    if (node->rb.rb_left) {
        subtree_last = rb_entry(node->rb.rb_left,
                                struct interval_tree_node, rb)->__subtree_last;
        if (max < subtree_last)
            max = subtree_last;
    }
    if (node->rb.rb_right) {
        subtree_last = rb_entry(node->rb.rb_right,
                                struct interval_tree_node, rb)->__subtree_last;
        if (max < subtree_last)
            max = subtree_last;
    }
    return max;
}

static void augment_propagate(struct rb_node *rb, struct rb_node *stop)
{
    while (rb != stop) {
        struct interval_tree_node *node =
            rb_entry(rb, struct interval_tree_node, rb);
        unsigned long subtree_last = compute_subtree_last(node);
        if (node->__subtree_last == subtree_last)
            break;
        node->__subtree_last = subtree_last;
        rb = rb_parent(&node->rb);
    }
}

static void augment_copy(struct rb_node *rb_old, struct rb_node *rb_new)
{
    struct interval_tree_node *old =
        rb_entry(rb_old, struct interval_tree_node, rb);
    struct interval_tree_node *new =
        rb_entry(rb_new, struct interval_tree_node, rb);

    new->__subtree_last = old->__subtree_last;
}

static void augment_rotate(struct rb_node *rb_old, struct rb_node *rb_new)
{
    struct interval_tree_node *old =
        rb_entry(rb_old, struct interval_tree_node, rb);
    struct interval_tree_node *new =
        rb_entry(rb_new, struct interval_tree_node, rb);

    new->__subtree_last = old->__subtree_last;
    old->__subtree_last = compute_subtree_last(old);
}

static const struct rb_augment_callbacks augment_callbacks = {
    .propagate = augment_propagate,
    .copy = augment_copy,
    .rotate = augment_rotate
};

void interval_tree_insert(struct interval_tree_node *node,
                          struct rb_root *root)
{
    struct rb_node **link = &root->rb_node, *rb_parent = NULL;
    unsigned long start = node->start, last = node->last;
    struct interval_tree_node *parent;

    while (*link) {
        rb_parent = *link;
        parent = rb_entry(rb_parent, struct interval_tree_node, rb);
        if (parent->__subtree_last < last)
            parent->__subtree_last = last;
        if (start < parent->start)
            link = &parent->rb.rb_left;
        else
            link = &parent->rb.rb_right;
    }

    node->__subtree_last = last;
    rb_link_node(&node->rb, rb_parent, link);
    rb_insert_augmented(&node->rb, root, &augment_callbacks);
}

void interval_tree_remove(struct interval_tree_node *node,
                          struct rb_root *root)
{
    rb_erase_augmented(&node->rb, root, &augment_callbacks);
}
```
These functions handle the insertion and removal of nodes in an interval tree, updating the `__subtree_last` field as necessary to maintain the structure's properties.
