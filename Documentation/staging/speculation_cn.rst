### 推测
###

本文档解释了推测可能带来的影响，以及如何使用常见的API来便携地缓解不良影响。
-----------------------------------------------------------------------------------------------

为了提高性能并最小化平均延迟，许多现代CPU采用诸如分支预测的推测执行技术，在可能被后续阶段丢弃的情况下提前执行一些工作。通常情况下，从架构状态（如寄存器内容）中无法观察到推测执行。但在某些情况下，可以观察到其对微架构状态（如缓存中数据的存在或缺失）的影响。这种状态可能会形成侧信道，从而被利用来提取秘密信息。

例如，在存在分支预测的情况下，通过推测执行的代码可能会忽略边界检查。考虑以下代码：

```c
int load_array(int *array, unsigned int index)
{
    if (index >= MAX_ARRAY_ELEMS)
        return 0;
    else
        return array[index];
}
```

在arm64上，这可能编译为如下汇编序列：

```assembly
CMP     <index>, #MAX_ARRAY_ELEMS
B.LT    less
MOV     <returnval>, #0
RET
less:
LDR     <returnval>, [<array>, <index>]
RET
```

有可能CPU错误预测了条件分支，并且即使`index >= MAX_ARRAY_ELEMS`时也推测性地加载`array[index]`。这个值随后会被丢弃，但推测性的加载可能会影响后续可测量的微架构状态。

更复杂的涉及多个依赖内存访问的序列可能导致敏感信息泄露。考虑以下基于前例的代码：

```c
int load_dependent_arrays(int *arr1, int *arr2, int index)
{
    int val1, val2;

    val1 = load_array(arr1, index);
    val2 = load_array(arr2, val1);

    return val2;
}
```

在推测执行下，第一次调用`load_array()`可能返回越界地址的值，而第二次调用将根据该值影响微架构状态。这可能提供任意读取原语。

### 缓解推测侧信道
###

内核提供了一个通用API以确保即使在推测执行下也能遵守边界检查。受推测侧信道影响的架构应实现这些原语。

`<linux/nospec.h>`中的`array_index_nospec()`辅助函数可用于防止信息通过侧信道泄露。

调用`array_index_nospec(index, size)`返回一个在推测条件下限制在`[0, size)`范围内的安全索引值。

这可以用来保护之前的`load_array()`示例：

```c
int load_array(int *array, unsigned int index)
{
    if (index >= MAX_ARRAY_ELEMS)
        return 0;
    else {
        index = array_index_nospec(index, MAX_ARRAY_ELEMS);
        return array[index];
    }
}
```
