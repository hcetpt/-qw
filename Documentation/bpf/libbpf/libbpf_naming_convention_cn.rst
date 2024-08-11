SPDX 许可证标识符: (LGPL-2.1 或 BSD-2-Clause)

API 命名规范
============

libbpf API 提供了对几个逻辑上分离的函数和类型组的访问。每个组都有其自己的命名规范，这里进行了描述。建议在添加新函数或类型时遵循这些规范，以保持 libbpf API 的整洁和一致。
libbpf API 提供的所有类型和函数都应该有一个以下前缀之一：``bpf_``、``btf_``、``libbpf_``、``btf_dump_``、``ring_buffer_``、``perf_buffer_``。

系统调用封装
--------------

系统调用封装是对 sys_bpf 系统调用支持的命令的简单封装。这些封装应放入 ``bpf.h`` 头文件，并且与对应的命令一一对应。
例如，``bpf_map_lookup_elem`` 封装了 sys_bpf 中的 ``BPF_MAP_LOOKUP_ELEM`` 命令，``bpf_prog_attach`` 封装了 ``BPF_PROG_ATTACH`` 等等。

对象
----

libbpf API 提供的另一类类型和函数是“对象”及其相关操作函数。对象是高级抽象，如 BPF 程序或 BPF 映射。它们由相应的结构表示，如 ``struct bpf_object``、``struct bpf_program``、``struct bpf_map`` 等等。
这些结构被向前声明，并应通过相应的获取器和设置器来访问它们的字段，而不是直接访问。
这些对象与包含编译后的 BPF 程序的 ELF 对象的相关部分关联。
例如，``struct bpf_object`` 代表从 ELF 文件或缓冲区创建的 ELF 对象本身；``struct bpf_program`` 代表 ELF 对象中的程序；而 ``struct bpf_map`` 则是一个映射。
与对象相关的函数名称由对象名称、双下划线和描述函数目的的部分组成。
例如，``bpf_object__open`` 包含相应对象的名称 ``bpf_object``、双下划线以及 ``open``，该部分定义了函数的目的，即打开 ELF 文件并从中创建一个 ``bpf_object``。
所有非与BTF相关的对象及其对应函数应当放入`libbpf.h`中。而BTF类型和函数应放入`btf.h`。

辅助函数
--------

那些不适合归类于上述任何类别的辅助函数和类型，应该使用`libbpf_`前缀，例如`libbpf_get_error`或`libbpf_prog_type_by_name`。

ABI
---

libbpf既可以静态链接也可以作为动态共享对象（DSO）使用。为了避免与应用程序所链接的其他库可能产生的冲突，所有非静态的libbpf符号都应使用API文档中提到的一个前缀。请参阅API命名规范来为新的符号选择正确的名称。

符号可见性
----------

libbpf遵循这样的模型：所有全局符号默认可见性为“隐藏”，若要使一个符号可见，则必须明确地使用`LIBBPF_API`宏进行标注。例如：

```c
    LIBBPF_API int bpf_prog_get_fd_by_id(__u32 id);
```

这可以防止意外地导出不应该成为ABI一部分的符号，从而改善了libbpf开发者和用户的体验。

ABI版本管理
------------

为了支持未来的ABI扩展，libbpf的ABI是版本化的。
版本管理通过传递给链接器的`libbpf.map`版本脚本来实现。
版本名由`LIBBPF_`前缀加上三部分数字版本组成，从`0.0.1`开始。
每当ABI发生变化时，比如添加了一个新符号或者现有符号的语义发生改变，ABI版本号都应该升级。
ABI版本号最多在一个内核开发周期内升级一次。
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

并且一个新的符号`bpf_func_c`被引入，那么`libbpf.map`应该这样更改：

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

其中新版本`LIBBPF_0.0.2`依赖于先前的`LIBBPF_0.0.1`。

关于版本脚本的格式以及如何处理ABI变化（包括不兼容的变化）的详细描述，请参见[1]。

独立构建
--------------

在https://github.com/libbpf/libbpf下有一个（半）自动化的镜像，用于构建主分支版本的libbpf以供独立构建使用。
但是，对libbpf代码库的所有更改都必须通过主分支内核树向上游提交。

API文档约定
=================

libbpf API通过头文件中定义上方的注释进行文档化。这些注释可以由doxygen和sphinx生成为组织良好的HTML输出。本节描述了这些注释应遵循的格式约定。

以下是一个来自btf.h的例子：

```c
/**
 * @brief **btf__new()** 从ELF的BTF部分的原始字节创建一个新的BTF对象实例
 * @param data 原始字节
 * @param size 传递到`data`中的字节数
 * @return 新的BTF对象实例，最终需要通过**btf__free()**释放
 *
 * 出错时返回编码为指针的错误码，而不是NULL。要从这样的指针中提取错误码，应使用`libbpf_get_error()`。如果启用了`libbpf_set_strict_mode(LIBBPF_STRICT_CLEAN_PTRS)`，则出错时返回NULL。在这两种情况下，线程本地的`errno`变量始终设置为错误码
 */
```

注释必须以'/\*\*'形式的块注释开始。
文档总是以@brief指令开始。这一行是对这个API的简短描述。它以加粗的形式开始，如：**api_name**。如果是函数，请包含括号。接着是API的简短描述。可以在注释底部的最后一个指令下方添加更长形式的描述。

参数使用@param指令表示，每个参数应有一个。如果函数有非void类型的返回值，则使用@return指令来记录。

许可协议
--------------

libbpf采用LGPL 2.1和BSD 2-Clause双重许可。
链接
-------------------

[1] https://www.akkadia.org/drepper/dsohowto.pdf
    （第3章. 维护APIs和ABIs）
