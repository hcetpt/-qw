SPDX 许可证标识符：(LGPL-2.1 或 BSD-2-Clause)

API 命名规范
============

libbpf API 提供了对几个逻辑上分离的函数和类型组的访问。每个组都有其自己的命名规范，如下所述。每当添加新函数或类型时，建议遵循这些规范以保持 libbpf API 的整洁和一致性。
由 libbpf API 提供的所有类型和函数应具有以下前缀之一：“bpf_”、“btf_”、“libbpf_”、“btf_dump_”、“ring_buffer_”、“perf_buffer_”。

系统调用包装器
------------------

系统调用包装器是为 sys_bpf 系统调用支持的命令提供的简单包装器。这些包装器应该放在“bpf.h”头文件中，并与相应的命令一一对应。
例如，“bpf_map_lookup_elem”包装了 sys_bpf 的“BPF_MAP_LOOKUP_ELEM”命令，“bpf_prog_attach”包装了“BPF_PROG_ATTACH”，等等。

对象
-------

libbpf API 提供的另一类类型和函数是“对象”及其操作函数。对象是高级抽象，如 BPF 程序或 BPF 地图。它们由相应的结构表示，如“struct bpf_object”、“struct bpf_program”、“struct bpf_map”等。
结构被提前声明，应通过相应的获取器和设置器而非直接访问来提供对其字段的访问。
这些对象与包含编译后的 BPF 程序的 ELF 对象的相关部分相关联。
例如，“struct bpf_object”代表从 ELF 文件或缓冲区创建的 ELF 对象本身，“struct bpf_program”代表 ELF 对象中的程序，“struct bpf_map”则是一个地图。
与对象交互的函数名称由对象名称、双下划线和描述函数目的的部分组成。
例如，“bpf_object__open”由相应的对象名称“bpf_object”、双下划线和“open”组成，定义了该函数的目的，即打开 ELF 文件并从中创建“bpf_object”。
除了与BTF相关的所有对象和对应函数都应该放入`libbpf.h`。BTF类型和函数应该放入`btf.h`。

辅助函数
--------

那些不太适合归类于上述任何类别的辅助函数和类型，应该使用`libbpf_`前缀，例如`libbpf_get_error`或`libbpf_prog_type_by_name`。

ABI
---

libbpf既可以静态链接，也可以作为DSO使用。为了避免可能与应用程序链接的其他库发生冲突，所有非静态的libbpf符号都应该使用上面API文档中提到的一个前缀。请参阅API命名约定以选择新符号的正确名称。

符号可见性
----------

libbpf遵循一种模型，即默认情况下所有全局符号的可见性为“隐藏”，要使一个符号可见，必须明确地用`LIBBPF_API`宏进行属性标记。例如：

```c
        LIBBPF_API int bpf_prog_get_fd_by_id(__u32 id);
```

这可以防止意外导出不应该是ABI一部分的符号，从而改善了libbpf开发人员和用户的体验。

ABI版本控制
------------

为了使未来的ABI扩展成为可能，libbpf的ABI进行了版本控制。
版本控制由传递给链接器的`libbpf.map`版本脚本实现。
版本名是`LIBBPF_`前缀加上三部分数字版本，从`0.0.1`开始。
每当ABI发生变化时，例如因为添加了新符号或现有符号的语义发生了变化，ABI版本应该升级。
这种ABI版本的升级在每个内核开发周期中最多一次。
例如，如果`libbpf.map`的当前状态是：

```plaintext
LIBBPF_0.0.1 {
        global:
                bpf_func_a;
                bpf_func_b;
        local:
                *;
};
```

并且正在引入一个新的符号`bpf_func_c`，那么`libbpf.map`应该这样更改：

```plaintext
LIBBPF_0.0.1 {
        global:
                bpf_func_a;
                bpf_func_b;
        local:
                *;
};
LIBBPF_0.0.2 {
        global:
                bpf_func_c;
} LIBBPF_0.0.1;
```

其中新版本`LIBBPF_0.0.2`依赖于先前的`LIBBPF_0.0.1`。关于版本脚本的格式以及如何处理ABI变化（包括不兼容的变化）的详细描述，请参见[1]。

独立构建
--------------

在https://github.com/libbpf/libbpf下有一个（半）自动化的镜像，用于构建主线版本的libbpf以进行独立构建。
然而，对libbpf代码库的所有更改都必须通过主线内核树向上游提交。

API文档约定
==================

libbpf的API通过头文件中定义上方的注释来记录。这些注释可以通过doxygen和sphinx渲染，以生成组织良好的HTML输出。本节描述了这些注释应遵循的格式约定。

以下是btf.h中的一个例子：

```c
/**
 * @brief **btf__new()** 从ELF的BTF段的原始字节创建一个新的BTF对象实例
 * @param data 原始字节
 * @param size 在`data`中传递的字节数
 * @return 新的BTF对象实例，最终需要使用**btf__free()**释放
 *
 * 如果出错，返回编码为指针的错误码，而不是NULL。要从这样的指针中提取错误码，应使用`libbpf_get_error()`。如果启用了`libbpf_set_strict_mode(LIBBPF_STRICT_CLEAN_PTRS)`，则在出错时返回NULL。在这两种情况下，线程本地的`errno`变量始终设置为错误码。
*/
```

注释必须以'/\*\*'形式的块注释开始。
文档总是以@brief指令开始。这一行是对这个API的简短描述。它以加粗的API名称开始，如下所示：**api_name**。如果是函数，请包含一对括号。跟随的是API的简短描述。更长形式的描述可以添加在最后一个指令下方，位于注释底部。

参数用@param指令表示，每个参数都应该有一个。如果这是一个非void返回值的函数，使用@return指令来记录它。

许可
--------------

libbpf采用LGPL 2.1和BSD 2-Clause双重许可。
链接
-------------------

[1] https://www.akkadia.org/drepper/dsohowto.pdf
    （第3章. 维护API和ABI）
