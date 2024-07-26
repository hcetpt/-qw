BPF类型格式 (BTF)
=====================

1. 引言
===============

BTF（BPF类型格式）是一种元数据格式，用于编码与BPF程序/映射相关的调试信息。BTF这个名字最初是用来描述数据类型的。后来BTF扩展了功能以包含定义的子程序的信息以及源代码/行信息。这些调试信息用于映射美化打印、函数签名等。函数签名有助于更好地识别内核符号中的BPF程序/函数。而行信息则有助于生成带有源注释的转换字节码、JIT代码和验证器日志。

BTF规范包括两部分：
  * BTF内核API
  * BTF ELF文件格式

内核API是用户空间与内核之间的协议。内核在使用BTF信息之前会对其进行验证。ELF文件格式则是用户空间中ELF文件与libbpf加载器之间的协议。
类型和字符串部分属于BTF内核API的一部分，描述了由BPF程序引用的调试信息（主要是类型相关信息）。这两个部分将在 :ref:`BTF_Type_String` 中详细讨论。
.. _BTF_Type_String:

2. BTF类型和字符串编码
===============================

文件 ``include/uapi/linux/btf.h`` 提供了类型/字符串编码方式的高级定义。
数据块的开头必须如下所示：

    struct btf_header {
        __u16   magic;
        __u8    version;
        __u8    flags;
        __u32   hdr_len;

        /* 所有偏移量都是相对于此头结尾的字节数 */
        __u32   type_off;       /* 类型部分的偏移量       */
        __u32   type_len;       /* 类型部分的长度       */
        __u32   str_off;        /* 字符串部分的偏移量     */
        __u32   str_len;        /* 字符串部分的长度     */
    };

magic值为 ``0xeB9F``，对于大端和小端系统有不同的编码，并且可以用来测试BTF是否为大端或小端目标生成。当生成一个数据块时，`btf_header`的设计考虑到了可扩展性，其中`hdr_len`等于`sizeof(struct btf_header)`。
2.1 字符串编码
-------------------

字符串部分的第一个字符串必须是一个空字符串。剩下的字符串表是由其他以空字符终止的字符串拼接而成的。
2.2 类型编码
-----------------

类型ID `0` 预留给 `void` 类型。类型部分按顺序解析，并从ID `1` 开始给每个识别到的类型分配类型ID。目前支持以下类型：

    #define BTF_KIND_INT            1       /* 整数      */
    #define BTF_KIND_PTR            2       /* 指针      */
    #define BTF_KIND_ARRAY          3       /* 数组        */
    #define BTF_KIND_STRUCT         4       /* 结构       */
    #define BTF_KIND_UNION          5       /* 联合        */
    #define BTF_KIND_ENUM           6       /* 枚举（最多32位值） */
    #define BTF_KIND_FWD            7       /* 前向声明      */
    #define BTF_KIND_TYPEDEF        8       /* 类型别名      */
    #define BTF_KIND_VOLATILE       9       /* 易失性     */
    #define BTF_KIND_CONST          10      /* 常量        */
    #define BTF_KIND_RESTRICT       11      /* 限制     */
    #define BTF_KIND_FUNC           12      /* 函数     */
    #define BTF_KIND_FUNC_PROTO     13      /* 函数原型       */
    #define BTF_KIND_VAR            14      /* 变量     */
    #define BTF_KIND_DATASEC        15      /* 分区      */
    #define BTF_KIND_FLOAT          16      /* 浮点数       */
    #define BTF_KIND_DECL_TAG       17      /* 声明标签     */
    #define BTF_KIND_TYPE_TAG       18      /* 类型标签     */
    #define BTF_KIND_ENUM64         19      /* 枚举（最多64位值） */

需要注意的是，类型部分编码的是调试信息，不仅仅是纯粹的类型。
`BTF_KIND_FUNC` 不是一种类型，而是表示一个定义好的子程序。
每种类型都包含以下共同的数据：

    struct btf_type {
        __u32 name_off;
        /* "info"位布局
         * 位  0-15: vlen（例如结构体成员的数量）
         * 位 16-23: 未使用
         * 位 24-28: 类型（例如整数、指针、数组……等等）
         * 位 29-30: 未使用
         * 位     31: kind_flag，当前被
         *             结构体、联合体、前向声明、枚举和枚举64使用 */
对于某些类型，通用数据后跟特定于该类型的额外数据。`struct btf_type` 中的 `name_off` 指定了在字符串表中的偏移量。以下各节详细介绍了每种类型的编码方式。

### 2.2.1 BTF_KIND_INT

`struct btf_type` 的编码要求如下：
- `name_off`: 任何有效的偏移量
- `info.kind_flag`: 0
- `info.kind`: BTF_KIND_INT
- `info.vlen`: 0
- `size`: 整型大小（以字节为单位）

`btf_type` 后跟一个 `__u32` 类型的数据，其位布局如下所示：

```c
#define BTF_INT_ENCODING(VAL)   (((VAL) & 0x0f000000) >> 24)
#define BTF_INT_OFFSET(VAL)     (((VAL) & 0x00ff0000) >> 16)
#define BTF_INT_BITS(VAL)       ((VAL)  & 0x000000ff)
```

`BTF_INT_ENCODING` 定义了以下属性：

```c
#define BTF_INT_SIGNED  (1 << 0)
#define BTF_INT_CHAR    (1 << 1)
#define BTF_INT_BOOL    (1 << 2)
```

`BTF_INT_ENCODING()` 提供了整型的额外信息：有符号性、字符类型或布尔类型。字符和布尔类型的编码主要用于美化输出。对于整型，最多只能指定一种编码。
`BTF_INT_BITS()` 指定此整型实际持有的位数。例如，4位位字段的 `BTF_INT_BITS()` 等于 4。
对于该类型，`btf_type.size * 8` 必须等于或大于 `BTF_INT_BITS()`。`BTF_INT_BITS()` 的最大值为 128。
`BTF_INT_OFFSET()` 指定了用于计算此整型值的起始位偏移。例如，位字段结构成员有：

* 从结构开始处的 btf 成员位偏移为 100，
* btf 成员指向一个整型类型，
* 整型具有 `BTF_INT_OFFSET() = 2` 和 `BTF_INT_BITS() = 4`

那么在结构内存布局中，该成员将占据从位 `100 + 2 = 102` 开始的 `4` 位。
或者，位字段结构成员可以如下设置以访问与上述相同的位：

* btf 成员位偏移为 102，
* btf 成员指向一个整型类型，
* 整型具有 `BTF_INT_OFFSET() = 0` 和 `BTF_INT_BITS() = 4`

`BTF_INT_OFFSET()` 的原始意图是为了提供位字段编码的灵活性。目前，llvm 和 pahole 对所有整型都生成 `BTF_INT_OFFSET() = 0`
2.2.2 BTF_KIND_PTR
~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`: 0
  * `info.kind_flag`: 0
  * `info.kind`: BTF_KIND_PTR
  * `info.vlen`: 0
  * `type`: 指针所指的对象类型

没有额外的类型数据跟随 `btf_type`
2.2.3 BTF_KIND_ARRAY
~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`: 0
  * `info.kind_flag`: 0
  * `info.kind`: BTF_KIND_ARRAY
  * `info.vlen`: 0
  * `size/type`: 0，不使用

`btf_type` 后跟一个 `struct btf_array`：

    ```c
    struct btf_array {
        __u32   type;
        __u32   index_type;
        __u32   nelems;
    };
    ```

`struct btf_array` 编码：
  * `type`: 元素类型
  * `index_type`: 索引类型
  * `nelems`: 此数组中的元素数量（`0` 也是允许的）
索引类型可以是任何常规整型 (`u8`, `u16`, `u32`, `u64`, `unsigned __int128`)。包含 `index_type` 的原始设计遵循 DWARF，其数组类型具有一个 `index_type`
目前，在 BTF 中除了类型验证外，`index_type` 不被使用
`struct btf_array` 允许通过元素类型链接来表示多维数组。例如，对于 `int a[5][6]`，以下类型信息说明了链接：

  * [1]: int
  * [2]: 数组, `btf_array.type = [1]`, `btf_array.nelems = 6`
  * [3]: 数组, `btf_array.type = [2]`, `btf_array.nelems = 5`

目前，pahole 和 llvm 都将多维数组简化为一维数组，例如，对于 `a[5][6]`，`btf_array.nelems` 等于 `30`。这是因为最初的用例是在地图美观打印中整个数组被输出，因此一维数组就足够了。随着更多 BTF 使用场景的探索，pahole 和 llvm 可以被修改以生成适当的多维数组链接表示
2.2.4 BTF_KIND_STRUCT
~~~~~~~~~~~~~~~~~~~~~
2.2.5 BTF_KIND_UNION
~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`: 0 或指向有效 C 标识符的偏移量
  * `info.kind_flag`: 0 或 1
  * `info.kind`: BTF_KIND_STRUCT 或 BTF_KIND_UNION
  * `info.vlen`: 结构体/联合体成员的数量
  * `info.size`: 结构体/联合体的字节大小

`btf_type` 后跟 `info.vlen` 个 `struct btf_member`：

    ```c
    struct btf_member {
        __u32   name_off;
        __u32   type;
        __u32   offset;
    };
    ```

`struct btf_member` 编码：
  * `name_off`: 指向有效 C 标识符的偏移量
  * `type`: 成员类型
  * `offset`: 见下文

如果类型信息 `kind_flag` 未设置，则偏移量仅包含成员的位偏移。需要注意的是位字段的基本类型只能是整型或枚举类型。如果位字段大小为 32，则基本类型可以是整型或枚举类型。如果位字段大小不是 32，则基本类型必须是整型，并且整型 `BTF_INT_BITS()` 编码位字段大小
如果设置了 `kind_flag`，则 `btf_member.offset` 包含成员位字段大小和位偏移。位字段大小和位偏移按以下方式计算：

  ```c
  #define BTF_MEMBER_BITFIELD_SIZE(val)   ((val) >> 24)
  #define BTF_MEMBER_BIT_OFFSET(val)      ((val) & 0xffffff)
  ```

在这种情况下，如果基本类型是整型，则它必须是一个常规整型：

  * `BTF_INT_OFFSET()` 必须为 0
  * `BTF_INT_BITS()` 必须等于 `{1,2,4,8,16} * 8`
提交 9d5f9f701b18 引入了 `kind_flag` 并解释了为何存在两种模式。

2.2.6 BTF_KIND_ENUM
~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`：0 或指向有效 C 标识符的偏移量
  * `info.kind_flag`：对于无符号类型为 0，对于有符号类型为 1
  * `info.kind`：BTF_KIND_ENUM
  * `info.vlen`：枚举值的数量
  * `size`：1/2/4/8

`btf_type` 后面跟着 `info.vlen` 数量的 `struct btf_enum`。::

    struct btf_enum {
        __u32   name_off;
        __s32   val;
    };

`btf_enum` 的编码：
  * `name_off`：指向有效 C 标识符的偏移量
  * `val`：任意值

如果原始枚举值是有符号的且大小小于 4 字节，则该值会被扩展到 4 字节。如果大小是 8 字节，则值会被截断为 4 字节。

2.2.7 BTF_KIND_FWD
~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`：指向有效 C 标识符的偏移量
  * `info.kind_flag`：对于结构体为 0，对于联合体为 1
  * `info.kind`：BTF_KIND_FWD
  * `info.vlen`：0
  * `type`：0

没有额外的类型数据跟在 `btf_type` 后面。

2.2.8 BTF_KIND_TYPEDEF
~~~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`：指向有效 C 标识符的偏移量
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_TYPEDEF
  * `info.vlen`：0
  * `type`：可以通过 `name_off` 指定的名字引用的类型

没有额外的类型数据跟在 `btf_type` 后面。

2.2.9 BTF_KIND_VOLATILE
~~~~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`：0
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_VOLATILE
  * `info.vlen`：0
  * `type`：具有 `volatile` 限定符的类型

没有额外的类型数据跟在 `btf_type` 后面。

2.2.10 BTF_KIND_CONST
~~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`：0
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_CONST
  * `info.vlen`：0
  * `type`：具有 `const` 限定符的类型

没有额外的类型数据跟在 `btf_type` 后面。

2.2.11 BTF_KIND_RESTRICT
~~~~~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`：0
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_RESTRICT
  * `info.vlen`：0
  * `type`：具有 `restrict` 限定符的类型

没有额外的类型数据跟在 `btf_type` 后面。

2.2.12 BTF_KIND_FUNC
~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`：指向有效 C 标识符的偏移量
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_FUNC
  * `info.vlen`：链接信息（BTF_FUNC_STATIC、BTF_FUNC_GLOBAL 或 BTF_FUNC_EXTERN）
  * `type`：一个 BTF_KIND_FUNC_PROTO 类型

没有额外的类型数据跟在 `btf_type` 后面。
BTF_KIND_FUNC 定义的不是类型，而是一个子程序（函数），其签名由 `type` 定义。因此，该子程序是该类型的实例。BTF_KIND_FUNC 可能会被 `BTF_Ext_Section` （ELF）中的 func_info 或 `BPF_Prog_Load` （ABI）的参数所引用。
目前内核只支持 BTF_FUNC_STATIC 和 BTF_FUNC_GLOBAL 的链接值。
### 2.2.13 BTF_KIND_FUNC_PROTO

`struct btf_type` 编码要求：
  * `name_off`: 0
  * `info.kind_flag`: 0
  * `info.kind`: BTF_KIND_FUNC_PROTO
  * `info.vlen`: 参数的数量
  * `type`: 返回类型

`btf_type` 后面跟着 `info.vlen` 数量的 `struct btf_param` 结构体。:: 

    struct btf_param {
        __u32   name_off;
        __u32   type;
    };

如果一个 BTF_KIND_FUNC_PROTO 类型被 BTF_KIND_FUNC 类型引用，那么
`btf_param.name_off` 必须指向一个有效的 C 标识符，除了可能代表变长参数的最后一个参数。`btf_param.type` 指向参数类型。
如果函数有变长参数，最后一个参数编码为
`name_off = 0` 和 `type = 0`

### 2.2.14 BTF_KIND_VAR

`struct btf_type` 编码要求：
  * `name_off`: 指向有效 C 标识符的偏移量
  * `info.kind_flag`: 0
  * `info.kind`: BTF_KIND_VAR
  * `info.vlen`: 0
  * `type`: 变量的类型

`btf_type` 后面跟着单个 `struct btf_variable` 结构体，内容如下：:: 

    struct btf_var {
        __u32   linkage;
    };

`struct btf_var` 编码：
  * `linkage`: 目前仅支持静态变量 0 或者在 ELF 分区中的全局分配变量 1

并非所有类型的全局变量都被 LLVM 支持。目前可用的是：

  * 带或不带分区属性的静态变量
  * 带分区属性的全局变量

后者是为了将来从映射定义中提取键/值类型 ID。

### 2.2.15 BTF_KIND_DATASEC

`struct btf_type` 编码要求：
  * `name_off`: 与变量关联的有效名称偏移量或其中之一 .data/.bss/.rodata
  * `info.kind_flag`: 0
  * `info.kind`: BTF_KIND_DATASEC
  * `info.vlen`: 变量数量
  * `size`: 部分大小（字节）：编译时为 0，在加载时（如通过 libbpf）更新为实际大小

`btf_type` 后面跟着 `info.vlen` 数量的 `struct btf_var_secinfo` 结构体。:: 

    struct btf_var_secinfo {
        __u32   type;
        __u32   offset;
        __u32   size;
    };

`struct btf_var_secinfo` 编码：
  * `type`: BTF_KIND_VAR 变量的类型
  * `offset`: 变量在分区内的偏移量
  * `size`: 变量的大小（字节）

### 2.2.16 BTF_KIND_FLOAT

`struct btf_type` 编码要求：
 * `name_off`: 任何有效偏移量
 * `info.kind_flag`: 0
 * `info.kind`: BTF_KIND_FLOAT
 * `info.vlen`: 0
 * `size`: 浮点类型大小（字节）：2、4、8、12 或 16

没有额外的数据跟在 `btf_type` 后面。

### 2.2.17 BTF_KIND_DECL_TAG

`struct btf_type` 编码要求：
 * `name_off`: 指向非空字符串的偏移量
 * `info.kind_flag`: 0
 * `info.kind`: BTF_KIND_DECL_TAG
 * `info.vlen`: 0
 * `type`: `struct`、`union`、`func`、`var` 或 `typedef`

`btf_type` 后面跟着 `struct btf_decl_tag` 结构体。:: 

    struct btf_decl_tag {
        __u32   component_idx;
    };

`name_off` 编码了 btf_decl_tag 属性字符串。
`type` 应该是 `struct`、`union`、`func`、`var` 或 `typedef`。
对于 `var` 或 `typedef` 类型，`btf_decl_tag.component_idx` 必须为 `-1`。
对于其他三种类型，如果 btf_decl_tag 属性应用于 `struct`、`union` 或 `func` 本身，
`btf_decl_tag.component_idx` 必须为 `-1`。否则，
该属性应用于 `struct`/`union` 成员或 `func` 参数，
并且 `btf_decl_tag.component_idx` 应该是一个有效的索引（从 0 开始），指向成员或参数。
### 2.2.18 BTF_KIND_TYPE_TAG

`struct btf_type` 编码要求：
* `name_off`：指向非空字符串的偏移量
* `info.kind_flag`：0
* `info.kind`：BTF_KIND_TYPE_TAG
* `info.vlen`：0
* `type`：具有 `btf_type_tag` 属性的类型

目前，`BTF_KIND_TYPE_TAG` 仅用于指针类型。
它有以下的 BTF 类型链：
```
ptr -> [type_tag]*
    -> [const | volatile | restrict | typedef]*
    -> base_type
```

基本上，一个指针类型指向零个或多个
`type_tag`，然后是零个或多个 `const`/`volatile`/`restrict`/`typedef`
最后是基础类型。基础类型可以是
`int`、`ptr`、`array`、`struct`、`union`、`enum`、`func_proto` 和 `float` 类型。

### 2.2.19 BTF_KIND_ENUM64

`struct btf_type` 编码要求：
* `name_off`：0 或指向有效的 C 标识符的偏移量
* `info.kind_flag`：对于无符号数为 0，对于带符号数为 1
* `info.kind`：BTF_KIND_ENUM64
* `info.vlen`：枚举值的数量
* `size`：1/2/4/8

`btf_type` 后跟 `info.vlen` 数量的 `struct btf_enum64` 结构体：
```
struct btf_enum64 {
    __u32   name_off;
    __u32   val_lo32;
    __u32   val_hi32;
};
```

`btf_enum64` 的编码：
* `name_off`：指向有效 C 标识符的偏移量
* `val_lo32`：64位值的低32位值
* `val_hi32`：64位值的高32位值

如果原始枚举值是有符号的且大小小于 8 字节，
则该值将被扩展到 8 字节。

### 3. BTF 内核 API

涉及 BTF 的 bpf 系统调用命令包括：
* BPF_BTF_LOAD：将 BTF 数据块加载到内核中
* BPF_MAP_CREATE：使用 btf 键和值类型信息创建映射
* BPF_PROG_LOAD：加载带有 btf 函数和行信息的程序
* BPF_BTF_GET_FD_BY_ID：根据 ID 获取 btf 文件描述符
* BPF_OBJ_GET_INFO_BY_FD：返回 btf、函数信息、行信息等与 btf 相关的信息

通常的工作流程如下所示：

```
Application:
    BPF_BTF_LOAD
        |
        v
    BPF_MAP_CREATE 和 BPF_PROG_LOAD
        |
        V
    .....
Introspection tool:
    .....
BPF_{PROG,MAP}_GET_NEXT_ID（获取程序/映射 ID）
        |
        V
BPF_{PROG,MAP}_GET_FD_BY_ID（根据 ID 获取程序/映射文件描述符）
        |
        V
BPF_OBJ_GET_INFO_BY_FD（根据文件描述符获取 bpf_prog_info/bpf_map_info 和 btf_id）
        |                                     |
        V                                     |
BPF_BTF_GET_FD_BY_ID（根据 ID 获取 btf 文件描述符）         |
        |                                     |
        V                                     |
BPF_OBJ_GET_INFO_BY_FD（获取 btf）          |
        |                                     |
        V                                     V
pretty print 类型、转储函数签名和行信息等
```

### 3.1 BPF_BTF_LOAD

将 BTF 数据块加载到内核中。如 :ref:`BTF_Type_String` 中所述的数据块可以直接加载到内核中。返回给用户空间一个 `btf_fd`。
### 3.2 BPF_MAP_CREATE
----------------------

可以使用`btf_fd`和指定的键/值类型ID来创建一个映射。:: 

    __u32   btf_fd;         /* 指向BTF类型数据的文件描述符 */
    __u32   btf_key_type_id;        /* 键的BTF类型ID */
    __u32   btf_value_type_id;      /* 值的BTF类型ID */

在libbpf中，可以通过额外的注解来定义映射，如下所示：:: 

    struct {
        __uint(type, BPF_MAP_TYPE_ARRAY);
        __type(key, int);
        __type(value, struct ipv_counts);
        __uint(max_entries, 4);
    } btf_map SEC(".maps");

在解析ELF文件时，libbpf能够自动提取键/值类型ID，并将它们分配给`BPF_MAP_CREATE`属性。

### 3.3 BPF_PROG_LOAD
----------------------

在加载程序时，可以为以下属性传递适当的值来将函数信息（`func_info`）和行信息（`line_info`）传递给内核：:: 

    __u32           insn_cnt;
    __aligned_u64   insns;
    .....
    __u32           prog_btf_fd;    /* 指向BTF类型数据的文件描述符 */
    __u32           func_info_rec_size;     /* 用户空间bpf_func_info大小 */
    __aligned_u64   func_info;      /* 函数信息 */
    __u32           func_info_cnt;  /* bpf_func_info记录的数量 */
    __u32           line_info_rec_size;     /* 用户空间bpf_line_info大小 */
    __aligned_u64   line_info;      /* 行信息 */
    __u32           line_info_cnt;  /* bpf_line_info记录的数量 */

`func_info`和`line_info`分别是以下结构的数组：:: 

    struct bpf_func_info {
        __u32   insn_off; /* [0, insn_cnt - 1] */
        __u32   type_id;  /* 指向BTF_KIND_FUNC类型 */
    };
    struct bpf_line_info {
        __u32   insn_off; /* [0, insn_cnt - 1] */
        __u32   file_name_off; /* 文件名到字符串表的偏移量 */
        __u32   line_off; /* 源代码行到字符串表的偏移量 */
        __u32   line_col; /* 行号和列号 */
    };

`func_info_rec_size`是每个`func_info`记录的大小，而`line_info_rec_size`是每个`line_info`记录的大小。将记录大小传递给内核使得将来扩展记录成为可能。

下面是`func_info`的要求：
  * `func_info[0].insn_off` 必须为0
* `func_info insn_off` 必须严格递增，并匹配BPF函数边界

下面是`line_info`的要求：
  * 每个函数的第一条指令必须有一个指向它的`line_info`记录
* `line_info insn_off` 必须严格递增

对于`line_info`，行号和列号定义如下：:: 

    #define BPF_LINE_INFO_LINE_NUM(line_col)        ((line_col) >> 10)
    #define BPF_LINE_INFO_LINE_COL(line_col)        ((line_col) & 0x3ff)

### 3.4 BPF_{PROG,MAP}_GET_NEXT_ID
------------------------------

在内核中，每一个加载的程序、映射或BTF都有一个唯一的ID。在整个程序、映射或BTF的生命周期中，该ID不会改变。
`BPF_{PROG,MAP}_GET_NEXT_ID`命令会返回所有ID，每个命令返回一个ID，分别针对BPF程序或映射，以便检查工具可以检查所有程序和映射。

### 3.5 BPF_{PROG,MAP}_GET_FD_BY_ID
-------------------------------

检查工具无法直接使用ID获取有关程序或映射的详细信息。
首先需要获取文件描述符以用于引用计数的目的。
3.6 BPF_OBJ_GET_INFO_BY_FD
--------------------------

一旦获取了程序/映射的文件描述符(fd)，内省工具可以从内核中获取关于该fd的详细信息，其中一些与BTF相关。例如，“bpf_map_info”返回“btf_id”和键/值类型id；“bpf_prog_info”返回“btf_id”，函数信息(func_info)以及转换后的BPF字节码的行信息(line info)，还有编译后的行信息(jited_line_info)。
3.7 BPF_BTF_GET_FD_BY_ID
------------------------

通过在“bpf_map_info”和“bpf_prog_info”中获得的“btf_id”，可以使用BPF系统调用命令BPF_BTF_GET_FD_BY_ID来检索一个btf文件描述符。然后，使用BPF_OBJ_GET_INFO_BY_FD命令，可以检索最初使用BPF_BTF_LOAD加载到内核中的btf blob。
有了btf blob、“bpf_map_info”和“bpf_prog_info”，内省工具就可以完全理解btf，并能够以友好的格式打印映射的键/值、转储函数签名和行信息，同时伴随着字节码(byte code)和编译后的代码(jit code)。
4. ELF 文件格式接口
============================

4.1 .BTF段
-----------------

.BTF段包含类型和字符串数据。此段的格式与:ref:`BTF_Type_String`中描述的一致。
.. _BTF_Ext_Section:

4.2 .BTF.ext段
--------------------

.BTF.ext段编码函数信息(func_info)、行信息(line_info)以及CO-RE重定位(relocation)，这些需要在加载到内核之前进行加载器处理。
.BTF.ext段的规范定义在``tools/lib/bpf/btf.h``和``tools/lib/bpf/btf.c``中。
.BTF.ext段当前的头部格式如下所示：

    struct btf_ext_header {
        __u16   magic;
        __u8    version;
        __u8    flags;
        __u32   hdr_len;

        /* 所有偏移量都是相对于此头部结束位置的字节数 */
        __u32   func_info_off;
        __u32   func_info_len;
        __u32   line_info_off;
        __u32   line_info_len;

        /* .BTF.ext头部的可选部分 */
        __u32   core_relo_off;
        __u32   core_relo_len;
    };

它与.BTF段非常相似。不同之处在于，它不包含类型/字符串段，而是包含函数信息(func_info)、行信息(line_info)以及核心重定位(core_relo)子段。
有关函数信息(func_info)和行信息(line_info)记录格式的详细信息，请参见:ref:`BPF_Prog_Load`。
`func_info` 的组织结构如下：

     func_info_rec_size              /* __u32 值 */
     btf_ext_info_sec 对于 section #1 /* section #1 的 func_info */
     btf_ext_info_sec 对于 section #2 /* section #2 的 func_info */
     ..
`func_info_rec_size` 指定了生成 `.BTF.ext` 时 `bpf_func_info` 结构的大小。下面定义的 `btf_ext_info_sec` 是针对每个特定 ELF 部分的 `func_info` 集合。::

     struct btf_ext_info_sec {
        __u32   sec_name_off; /* 部分名称的偏移量 */
        __u32   num_info;
        /* 接下来是 num_info * 记录大小的字节数 */
        __u8    data[0];
     };

这里，num_info 必须大于 0。
`line_info` 的组织结构如下：

     line_info_rec_size              /* __u32 值 */
     btf_ext_info_sec 对于 section #1 /* section #1 的 line_info */
     btf_ext_info_sec 对于 section #2 /* section #2 的 line_info */
     ..
`line_info_rec_size` 指定了生成 `.BTF.ext` 时 `bpf_line_info` 结构的大小。
`bpf_func_info->insn_off` 和 `bpf_line_info->insn_off` 在内核 API 和 ELF API 中的解释不同。对于内核 API，`insn_off` 是以 `struct bpf_insn` 为单位的指令偏移量。对于 ELF API，`insn_off` 是从部分（`btf_ext_info_sec->sec_name_off`）开始的字节偏移量。
`core_relo` 的组织结构如下：::

     core_relo_rec_size              /* __u32 值 */
     btf_ext_info_sec 对于 section #1 /* section #1 的 core_relo */
     btf_ext_info_sec 对于 section #2 /* section #2 的 core_relo */

`core_relo_rec_size` 指定了生成 `.BTF.ext` 时 `bpf_core_relo` 结构的大小。单个 `btf_ext_info_sec` 内的所有 `bpf_core_relo` 结构描述了应用于由 `btf_ext_info_sec->sec_name_off` 命名的部分中的重定位。
有关 CO-RE 重定位的更多信息，请参阅 :ref:`Documentation/bpf/llvm_reloc.rst <btf-co-re-relocations>`。
4.2 .BTF_ids 部分
-------------------

.BTF_ids 部分编码了在内核中使用的 BTF ID 值
此部分是在内核编译期间借助 `include/linux/btf_ids.h` 头文件中定义的宏创建的。内核代码可以使用它们来创建 BTF ID 值的列表和集合（排序列表）
`BTF_ID_LIST` 和 `BTF_ID` 宏定义了未排序的 BTF ID 值列表，语法如下：

  BTF_ID_LIST(list)
  BTF_ID(type1, name1)
  BTF_ID(type2, name2)

这会在 .BTF_ids 部分中产生以下布局：

  __BTF_ID__type1__name1__1:
  .zero 4
  __BTF_ID__type2__name2__2:
  .zero 4

定义了变量 `u32 list[];` 来访问该列表。
```plaintext
"BTF_ID_UNUSED" 宏定义了4个零字节。当我们在 BTF_ID_LIST 中定义未使用的条目时会用到它，例如：

      BTF_ID_LIST(bpf_skb_output_btf_ids)
      BTF_ID(struct, sk_buff)
      BTF_ID_UNUSED
      BTF_ID(struct, task_struct)

"BTF_SET_START/END" 宏对定义了一个排序的 BTF ID 值列表及其数量，其语法如下：

  BTF_SET_START(set)
  BTF_ID(type1, name1)
  BTF_ID(type2, name2)
  BTF_SET_END(set)

这会在 .BTF_ids 段中生成如下布局：

  __BTF_ID__set__set:
  .zero 4
  __BTF_ID__type1__name1__3:
  .zero 4
  __BTF_ID__type2__name2__4:
  .zero 4

定义变量 "struct btf_id_set set;" 来访问该列表。
"typeX" 名称可以是以下之一：

   struct, union, typedef, func

在解析 BTF ID 值时将其作为过滤器使用。
所有的 BTF ID 列表和集合都会编译到 .BTF_ids 段中，并且在内核构建的链接阶段由 "resolve_btfids" 工具解析。

5. 使用 BTF
============

5.1 bpftool 地图美化打印
----------------------------

借助 BTF，可以根据字段而不是简单的原始字节来打印地图键/值。对于大型结构或数据结构包含位域的情况尤其有价值。例如，对于以下地图：

      enum A { A1, A2, A3, A4, A5 };
      typedef enum A ___A;
      struct tmp_t {
           char a1:4;
           int  a2:4;
           int  :4;
           __u32 a3:4;
           int b;
           ___A b1:4;
           enum A b2:4;
      };
      struct {
           __uint(type, BPF_MAP_TYPE_ARRAY);
           __type(key, int);
           __type(value, struct tmp_t);
           __uint(max_entries, 1);
      } tmpmap SEC(".maps");

bpftool 能够美化打印如下：
::

      [{
            "key": 0,
            "value": {
                "a1": 0x2,
                "a2": 0x4,
                "a3": 0x6,
                "b": 7,
                "b1": 0x8,
                "b2": 0xa
            }
        }
      ]

5.2 bpftool 程序转储
---------------------

下面是一个示例，展示了 func_info 和 line_info 如何帮助程序转储获得更好的内核符号名称、函数原型和行信息。例如：

    $ bpftool prog dump jited pinned /sys/fs/bpf/test_btf_haskv
    [...]
    int test_long_fname_2(struct dummy_tracepoint_args * arg):
    bpf_prog_44a040bf25481309_test_long_fname_2:
    ; static int test_long_fname_2(struct dummy_tracepoint_args *arg)
       0:   push   %rbp
       1:   mov    %rsp,%rbp
       4:   sub    $0x30,%rsp
       b:   sub    $0x28,%rbp
       f:   mov    %rbx,0x0(%rbp)
      13:   mov    %r13,0x8(%rbp)
      17:   mov    %r14,0x10(%rbp)
      1b:   mov    %r15,0x18(%rbp)
      1f:   xor    %eax,%eax
      21:   mov    %rax,0x20(%rbp)
      25:   xor    %esi,%esi
    ; int key = 0;
      27:   mov    %esi,-0x4(%rbp)
    ; if (!arg->sock)
      2a:   mov    0x8(%rdi),%rdi
    ; if (!arg->sock)
      2e:   cmp    $0x0,%rdi
      32:   je     0x0000000000000070
      34:   mov    %rbp,%rsi
    ; counts = bpf_map_lookup_elem(&btf_map, &key);
    [...]

5.3 验证器日志
----------------

下面是一个示例，展示了 line_info 如何有助于调试验证失败。例如：

       /* 在 tools/testing/selftests/bpf/test_xdp_noinline.c 中修改代码为
        * 下面的形式
*/
       data = (void *)(long)xdp->data;
       data_end = (void *)(long)xdp->data_end;
       /*
       if (data + 4 > data_end)
               return XDP_DROP;
       */
       *(u32 *)data = dst->dst;

    $ bpftool prog load ./test_xdp_noinline.o /sys/fs/bpf/test_xdp_noinline type xdp
        ; data = (void *)(long)xdp->data;
        224: (79) r2 = *(u64 *)(r10 -112)
        225: (61) r2 = *(u32 *)(r2 +0)
        ; *(u32 *)data = dst->dst;
        226: (63) *(u32 *)(r2 +0) = r1
        对包的无效访问，偏移量=0 大小=4, R2(id=0,off=0,r=0)
        R2 的偏移量位于包之外

6. BTF 生成
=================

您需要最新的 pahole

  https://git.kernel.org/pub/scm/devel/pahole/pahole.git/

或者 LLVM (8.0 或更高版本)。pahole 充当 dwarf2btf 转换器。它目前还不支持 .BTF.ext 和 btf BTF_KIND_FUNC 类型。例如，

      -bash-4.4$ cat t.c
      struct t {
        int a:2;
        int b:3;
        int c:2;
      } g;
      -bash-4.4$ gcc -c -O2 -g t.c
      -bash-4.4$ pahole -JV t.o
      文件 t.o:
      [1] STRUCT t kind_flag=1 size=4 vlen=3
              a type_id=2 bitfield_size=2 bits_offset=0
              b type_id=2 bitfield_size=3 bits_offset=2
              c type_id=2 bitfield_size=2 bits_offset=5
      [2] INT int size=4 bit_offset=0 nr_bits=32 encoding=SIGNED

LLVM 能够直接为 bpf 目标生成 .BTF 和 .BTF.ext，并且通过 -g 参数实现。汇编代码 (-S) 可以以汇编格式显示 BTF 编码。例如，

    -bash-4.4$ cat t2.c
    typedef int __int32;
    struct t2 {
      int a2;
      int (*f2)(char q1, __int32 q2, ...);
      int (*f3)();
    } g2;
    int main() { return 0; }
    int test() { return 0; }
    -bash-4.4$ clang -c -g -O2 --target=bpf t2.c
    -bash-4.4$ readelf -S t2.o
      .....
[ 8] .BTF              PROGBITS         0000000000000000  00000247
           000000000000016e  0000000000000000           0     0     1
      [ 9] .BTF.ext          PROGBITS         0000000000000000  000003b5
           0000000000000060  0000000000000000           0     0     1
      [10] .rel.BTF.ext      REL              0000000000000000  000007e0
           0000000000000040  0000000000000010          16     9     8
      .....
-bash-4.4$ clang -S -g -O2 --target=bpf t2.c
    -bash-4.4$ cat t2.s
      .....
.section        .BTF,"",@progbits
            .short  60319                   # 0xeb9f
            .byte   1
            .byte   0
            .long   24
            .long   0
            .long   220
            .long   220
            .long   122
            .long   0                       # BTF_KIND_FUNC_PROTO(id = 1)
            .long   218103808               # 0xd000000
            .long   2
            .long   83                      # BTF_KIND_INT(id = 2)
            .long   16777216                # 0x1000000
            .long   4
            .long   16777248                # 0x1000020
      .....
.byte   0                       # 字符串偏移量=0
            .ascii  ".text"                 # 字符串偏移量=1
            .byte   0
            .ascii  "/home/yhs/tmp-pahole/t2.c" # 字符串偏移量=7
            .byte   0
            .ascii  "int main() { return 0; }" # 字符串偏移量=33
            .byte   0
            .ascii  "int test() { return 0; }" # 字符串偏移量=58
            .byte   0
            .ascii  "int"                   # 字符串偏移量=83
      .....
.section        .BTF.ext,"",@progbits
            .short  60319                   # 0xeb9f
            .byte   1
            .byte   0
            .long   24
            .long   0
            .long   28
            .long   28
            .long   44
            .long   8                       # FuncInfo
            .long   1                       # FuncInfo section 字符串偏移量=1
            .long   2
            .long   .Lfunc_begin0
            .long   3
            .long   .Lfunc_begin1
            .long   5
            .long   16                      # LineInfo
            .long   1                       # LineInfo section 字符串偏移量=1
            .long   2
            .long   .Ltmp0
            .long   7
            .long   33
            .long   7182                    # 行 7 列 14
            .long   .Ltmp3
            .long   7
            .long   58
            .long   8206                    # 行 8 列 14

7. 测试
==========

内核 BPF 自测 `tools/testing/selftests/bpf/prog_tests/btf.c`_
提供了一组广泛的与 BTF 相关的测试。
```
链接:
.. _tools/testing/selftests/bpf/prog_tests/btf.c:
   https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/tools/testing/selftests/bpf/prog_tests/btf.c

翻译为中文可表示为:
链接:
.. _工具/测试/selftests/bpf/程序测试/btf.c:
   https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/工具/测试/selftests/bpf/程序测试/btf.c

请注意，这种文档链接标记（如 ".. _tools/testing/selftests/bpf/prog_tests/btf.c:"）通常是特定文档系统（例如 Sphinx 文档生成系统）使用的，用于创建内部链接。在实际中文文档中，你可能需要根据所用的文档系统调整格式。而URL通常无需翻译。
