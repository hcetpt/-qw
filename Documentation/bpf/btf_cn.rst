BPF类型格式（BTF）
=====================

1. 引言
===============

BTF（BPF类型格式）是编码与BPF程序/映射相关的调试信息的元数据格式。最初，BTF这个名字被用来描述数据类型。后来，BTF被扩展以包含已定义子例程的函数信息以及源代码/行信息的行信息。调试信息用于映射的美化打印、函数签名等。函数签名使BPF程序/函数内核符号更加完善。行信息有助于生成带有源注释的转换字节码、即时编译代码和验证器日志。

BTF规范包含两部分：
  * BTF内核API
  * BTF ELF文件格式

内核API是用户空间与内核之间的契约。在使用BTF信息之前，内核会对其进行验证。ELF文件格式是用户空间中ELF文件与libbpf加载器之间的契约。
类型和字符串段是BTF内核API的一部分，描述了由BPF程序引用的调试信息（主要是类型相关）。这两个部分在 :ref:`BTF_Type_String` 中详细讨论。
.. _BTF_Type_String:

2. BTF类型和字符串编码
===============================

文件 ``include/uapi/linux/btf.h`` 提供了类型/字符串如何编码的高级定义。
数据块的开头必须是这样的结构体：

    struct btf_header {
        __u16   magic;
        __u8    version;
        __u8    flags;
        __u32   hdr_len;

        /* 所有偏移量都是相对于此头末尾的字节数 */
        __u32   type_off;       /* 类型段的偏移量       */
        __u32   type_len;       /* 类型段的长度       */
        __u32   str_off;        /* 字符串段的偏移量     */
        __u32   str_len;        /* 字符串段的长度     */
    };

魔数是 ``0xeB9F`` ，对于大端和小端系统有不同的编码，并且可以用来测试BTF是否为大端或小端目标生成。当生成数据块时，“btf_header”设计为可扩展的，其中“hdr_len”等于 “sizeof(struct btf_header)”。
2.1 字符串编码
-------------------

字符串段中的第一个字符串必须是一个空字符串。其余的字符串表是由其他以空字符结尾的字符串拼接而成的。
2.2 类型编码
-----------------

类型ID ``0`` 被保留为 ``void`` 类型。类型段按顺序解析，并从ID ``1`` 开始为每个识别的类型分配类型ID。目前，支持以下类型：

    #define BTF_KIND_INT            1       /* 整型      */
    #define BTF_KIND_PTR            2       /* 指针      */
    #define BTF_KIND_ARRAY          3       /* 数组        */
    #define BTF_KIND_STRUCT         4       /* 结构体       */
    #define BTF_KIND_UNION          5       /* 联合        */
    #define BTF_KIND_ENUM           6       /* 枚举至32位值 */
    #define BTF_KIND_FWD            7       /* 前向声明      */
    #define BTF_KIND_TYPEDEF        8       /* 类型别名      */
    #define BTF_KIND_VOLATILE       9       /* 易失性     */
    #define BTF_KIND_CONST          10      /* 常量        */
    #define BTF_KIND_RESTRICT       11      /* 限制性     */
    #define BTF_KIND_FUNC           12      /* 函数     */
    #define BTF_KIND_FUNC_PROTO     13      /* 函数原型       */
    #define BTF_KIND_VAR            14      /* 变量     */
    #define BTF_KIND_DATASEC        15      /* 段      */
    #define BTF_KIND_FLOAT          16      /* 浮点数       */
    #define BTF_KIND_DECL_TAG       17      /* 声明标签     */
    #define BTF_KIND_TYPE_TAG       18      /* 类型标签     */
    #define BTF_KIND_ENUM64         19      /* 枚举至64位值 */

需要注意的是，类型段不仅编码纯类型，还编码调试信息。
``BTF_KIND_FUNC`` 并不是一个类型，它代表一个定义过的子程序。
每种类型都包含以下通用数据：

    struct btf_type {
        __u32 name_off;
        /* "info"位排列
         * 位  0-15: vlen （例如，结构体成员的数量）
         * 位 16-23: 未使用
         * 位 24-28: 种类（例如，整型，指针，数组...等等）
         * 位 29-30: 未使用
         * 位     31: kind_flag，当前由
         *             结构体，联合，前向声明，枚举和enum64使用 */
对于某些类型，通用数据后跟特定于该类型的详细数据。`struct btf_type`中的`name_off`指定了在字符串表中的偏移量。以下各节详细说明了每种类型的编码。

2.2.1 BTF_KIND_INT
~~~~~~~~~~~~~~~~~~

`struct btf_type`编码要求：
 * `name_off`：任何有效偏移量
 * `info.kind_flag`：0
 * `info.kind`：BTF_KIND_INT
 * `info.vlen`：0
 * `size`：int类型的字节大小

`btf_type`后面跟着一个`u32`，其位布局如下所示：

```c
#define BTF_INT_ENCODING(VAL)   (((VAL) & 0x0f000000) >> 24)
#define BTF_INT_OFFSET(VAL)     (((VAL) & 0x00ff0000) >> 16)
#define BTF_INT_BITS(VAL)       ((VAL)  & 0x000000ff)
```

`BTF_INT_ENCODING`具有以下属性：

```c
#define BTF_INT_SIGNED  (1 << 0)
#define BTF_INT_CHAR    (1 << 1)
#define BTF_INT_BOOL    (1 << 2)
```

`BTF_INT_ENCODING()`提供了有关int类型的附加信息：有符号性、字符型或布尔型。字符和布尔编码主要用于美化打印。int类型最多可以指定一种编码。

`BTF_INT_BITS()`指定了此int类型实际持有的位数。例如，4位位字段的`BTF_INT_BITS()`等于4。

`btf_type.size * 8`必须等于或大于`BTF_INT_BITS()`对于该类型。`BTF_INT_BITS()`的最大值为128。
`BTF_INT_OFFSET()` 指定了用于计算此整型值的起始位偏移。例如，一个位字段结构成员有：

* 从结构开始处的 btf 成员位偏移为 100，
* btf 成员指向一个整型类型，
* 整型类型具有 `BTF_INT_OFFSET() = 2` 和 `BTF_INT_BITS() = 4`

那么在结构内存布局中，该成员将占用从位 `100 + 2 = 102` 开始的 `4` 位。
或者，位字段结构成员可以是以下方式以访问与上述相同位：

* btf 成员位偏移 102，
* btf 成员指向一个整型类型，
* 整型类型具有 `BTF_INT_OFFSET() = 0` 和 `BTF_INT_BITS() = 4`

`BTF_INT_OFFSET()` 的最初意图是为了提供位字段编码的灵活性。目前，对于所有整型类型，llvm 和 pahole 都生成 `BTF_INT_OFFSET() = 0`
2.2.2 BTF_KIND_PTR
~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`：0
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_PTR
  * `info.vlen`：0
  * `type`：指针的目标类型

没有额外的类型数据跟在 `btf_type` 后面。
2.2.3 BTF_KIND_ARRAY
~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`：0
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_ARRAY
  * `info.vlen`：0
  * `size/type`：0，未使用

`btf_type` 被一个 `struct btf_array` 跟随：

    struct btf_array {
        __u32   type;
        __u32   index_type;
        __u32   nelems;
    };

`struct btf_array` 编码：
  * `type`：元素类型
  * `index_type`：索引类型
  * `nelems`：此数组的元素数量（允许 `0`）

`index_type` 可以是任何常规整型类型（`u8`，`u16`，`u32`，`u64`，`unsigned __int128`）。包含 `index_type` 的原始设计遵循 DWARF，其数组类型有一个 `index_type`。
目前，在 BTF 中，除了类型验证外，`index_type` 并未使用。
`struct btf_array` 允许通过元素类型链接来表示多维数组。例如，对于 `int a[5][6]`，下面的类型信息说明了链接：

  * [1]：int
  * [2]：数组，`btf_array.type = [1]`，`btf_array.nelems = 6`
  * [3]：数组，`btf_array.type = [2]`，`btf_array.nelems = 5`

目前，pahole 和 llvm 将多维数组缩减为一维数组，例如，对于 `a[5][6]`，`btf_array.nelems` 等于 `30`。这是因为最初的使用案例是映射漂亮打印，其中整个数组被输出，因此一维数组就足够了。随着更多 BTF 使用场景的探索，pahole 和 llvm 可以改变生成正确的多维数组链接表示。
2.2.4 BTF_KIND_STRUCT
~~~~~~~~~~~~~~~~~~~~~
2.2.5 BTF_KIND_UNION
~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码要求：
  * `name_off`：0 或指向有效 C 标识符的偏移
  * `info.kind_flag`：0 或 1
  * `info.kind`：BTF_KIND_STRUCT 或 BTF_KIND_UNION
  * `info.vlen`：结构或联合体成员的数量
  * `info.size`：结构或联合体的字节大小

`btf_type` 被 `info.vlen` 数量的 `struct btf_member` 跟随。

    struct btf_member {
        __u32   name_off;
        __u32   type;
        __u32   offset;
    };

`struct btf_member` 编码：
  * `name_off`：指向有效 C 标识符的偏移
  * `type`：成员类型
  * `offset`：<见下文>

如果类型信息 `kind_flag` 未设置，则偏移量仅包含成员的位偏移。需要注意的是，位字段的基本类型只能是整型或枚举类型。如果位字段大小为 32，则基本类型可以是整型或枚举类型。如果位字段大小不是 32，则基本类型必须是整型，并且整型类型 `BTF_INT_BITS()` 编码位字段大小。
如果 `kind_flag` 被设置，则 `btf_member.offset` 包含成员位字段大小和位偏移。位字段大小和位偏移按如下方式计算：

  #define BTF_MEMBER_BITFIELD_SIZE(val)   ((val) >> 24)
  #define BTF_MEMBER_BIT_OFFSET(val)      ((val) & 0xffffff)

在这种情况下，如果基本类型是一个整型类型，它必须是一个常规整型类型：

  * `BTF_INT_OFFSET()` 必须为 0
* `BTF_INT_BITS()` 必须等于 `{1,2,4,8,16} * 8`
提交 9d5f9f701b18 引入了 `kind_flag` 并解释了为何存在两种模式。

2.2.6 BTF_KIND_ENUM
~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码需求：
  * `name_off`：0 或指向有效 C 标识符的偏移量
  * `info.kind_flag`：对于无符号类型为 0，对于有符号类型为 1
  * `info.kind`：BTF_KIND_ENUM
  * `info.vlen`：枚举值的数量
  * `size`：1/2/4/8

`btf_type` 后面跟随着 `info.vlen` 数量的 `struct btf_enum`。::

    struct btf_enum {
        __u32   name_off;
        __s32   val;
    };

`btf_enum` 的编码：
  * `name_off`：指向有效 C 标识符的偏移量
  * `val`：任意值

如果原始枚举值是有符号的且大小小于 4 字节，该值将被扩展为 4 字节的符号数。如果大小是 8 字节，则值将被截断为 4 字节。

2.2.7 BTF_KIND_FWD
~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码需求：
  * `name_off`：指向有效 C 标识符的偏移量
  * `info.kind_flag`：对于结构体为 0，对于联合体为 1
  * `info.kind`：BTF_KIND_FWD
  * `info.vlen`：0
  * `type`：0

`btf_type` 之后没有额外的类型数据。

2.2.8 BTF_KIND_TYPEDEF
~~~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码需求：
  * `name_off`：指向有效 C 标识符的偏移量
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_TYPEDEF
  * `info.vlen`：0
  * `type`：在 `name_off` 处可以引用的类型

`btf_type` 之后没有额外的类型数据。

2.2.9 BTF_KIND_VOLATILE
~~~~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码需求：
  * `name_off`：0
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_VOLATILE
  * `info.vlen`：0
  * `type`：带有 `volatile` 限定符的类型

`btf_type` 之后没有额外的类型数据。

2.2.10 BTF_KIND_CONST
~~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码需求：
  * `name_off`：0
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_CONST
  * `info.vlen`：0
  * `type`：带有 `const` 限定符的类型

`btf_type` 之后没有额外的类型数据。

2.2.11 BTF_KIND_RESTRICT
~~~~~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码需求：
  * `name_off`：0
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_RESTRICT
  * `info.vlen`：0
  * `type`：带有 `restrict` 限定符的类型

`btf_type` 之后没有额外的类型数据。

2.2.12 BTF_KIND_FUNC
~~~~~~~~~~~~~~~~~~~~

`struct btf_type` 编码需求：
  * `name_off`：指向有效 C 标识符的偏移量
  * `info.kind_flag`：0
  * `info.kind`：BTF_KIND_FUNC
  * `info.vlen`：链接信息（BTF_FUNC_STATIC、BTF_FUNC_GLOBAL 或 BTF_FUNC_EXTERN）
  * `type`：一个 BTF_KIND_FUNC_PROTO 类型

`btf_type` 之后没有额外的类型数据。
BTF_KIND_FUNC 定义的不是一个类型，而是一个子程序（函数），其签名由 `type` 定义。因此，该子程序是该类型的实例。BTF_KIND_FUNC 可能会被 `BTF_Ext_Section` （ELF）中的 func_info 或 `BPF_Prog_Load` （ABI）的参数所引用。

目前内核只支持 BTF_FUNC_STATIC 和 BTF_FUNC_GLOBAL 的链接值。
### 2.2.13 BTF_KIND_FUNC_PROTO

`struct btf_type` 编码要求：
  * `name_off`: 0
  * `info.kind_flag`: 0
  * `info.kind`: BTF_KIND_FUNC_PROTO
  * `info.vlen`: 参数的数量
  * `type`: 返回类型

`btf_type` 后面跟着 `info.vlen` 数量的 `struct btf_param`。::

    struct btf_param {
        __u32   name_off;
        __u32   type;
    };

如果一个 BTF_KIND_FUNC_PROTO 类型被 BTF_KIND_FUNC 类型引用，则 `btf_param.name_off` 必须指向一个有效的 C 标识符，除了可能代表可变参数的最后一个参数。`btf_param.type` 指向参数类型。
如果函数有可变参数，最后一个参数被编码为 `name_off = 0` 和 `type = 0`。

### 2.2.14 BTF_KIND_VAR

`struct btf_type` 编码要求：
  * `name_off`: 指向有效 C 标识符的偏移量
  * `info.kind_flag`: 0
  * `info.kind`: BTF_KIND_VAR
  * `info.vlen`: 0
  * `type`: 变量的类型

`btf_type` 后面跟着一个 `struct btf_variable` 的数据结构，如下所示：::

    struct btf_var {
        __u32   linkage;
    };

`struct btf_var` 编码：
  * `linkage`: 目前只支持静态变量（值为 0），或 ELF 部分中的全局分配变量（值为 1）

并非所有类型的全局变量都被 LLVM 支持。目前可用的是：

  * 带或不带段属性的静态变量
  * 带段属性的全局变量

后者是为了将来从映射定义中提取键/值类型 ID。

### 2.2.15 BTF_KIND_DATASEC

`struct btf_type` 编码要求：
  * `name_off`: 与变量关联的有效名称的偏移量或其中之一：.data/.bss/.rodata
  * `info.kind_flag`: 0
  * `info.kind`: BTF_KIND_DATASEC
  * `info.vlen`: 变量数量
  * `size`: 段的总大小（字节）（编译时为 0，在加载时如 libbpf 中补丁为实际大小）

`btf_type` 后面跟着 `info.vlen` 数量的 `struct btf_var_secinfo`。::

    struct btf_var_secinfo {
        __u32   type;
        __u32   offset;
        __u32   size;
    };

`struct btf_var_secinfo` 编码：
  * `type`: BTF_KIND_VAR 变量的类型
  * `offset`: 变量在段中的偏移量
  * `size`: 变量的字节大小

### 2.2.16 BTF_KIND_FLOAT

`struct btf_type` 编码要求：
 * `name_off`: 任何有效偏移量
 * `info.kind_flag`: 0
 * `info.kind`: BTF_KIND_FLOAT
 * `info.vlen`: 0
 * `size`: 浮点类型大小（字节）：2、4、8、12 或 16

`btf_type` 后无额外类型数据。

### 2.2.17 BTF_KIND_DECL_TAG

`struct btf_type` 编码要求：
 * `name_off`: 非空字符串的偏移量
 * `info.kind_flag`: 0
 * `info.kind`: BTF_KIND_DECL_TAG
 * `info.vlen`: 0
 * `type`: `struct`、`union`、`func`、`var` 或 `typedef`

`btf_type` 后面跟着 `struct btf_decl_tag`。::

    struct btf_decl_tag {
        __u32   component_idx;
    };

`name_off` 编码了 btf_decl_tag 属性字符串。
`type` 应该是 `struct`、`union`、`func`、`var` 或 `typedef`。
对于 `var` 或 `typedef` 类型，`btf_decl_tag.component_idx` 必须为 `-1`。
对于其他三种类型，如果 btf_decl_tag 属性应用于 `struct`、`union` 或 `func` 本身，
`btf_decl_tag.component_idx` 必须为 `-1`。否则，
属性应用于 `struct`/`union` 成员或 `func` 参数，
且 `btf_decl_tag.component_idx` 应该是一个有效索引（从 0 开始），指向成员或参数。
### 2.2.18 类型标签 (BTF_KIND_TYPE_TAG)

``struct btf_type`` 编码要求：
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

基本上，指针类型指向零个或多个 `type_tag`，然后是零个或多个 `const`、`volatile`、`restrict` 或 `typedef`，最后是基础类型。基础类型可以是 `int`、`ptr`、`array`、`struct`、`union`、`enum`、`func_proto` 和 `float` 中的一种。

### 2.2.19 枚举64位 (BTF_KIND_ENUM64)

``struct btf_type`` 编码要求：
* `name_off`：0 或指向有效 C 标识符的偏移量
* `info.kind_flag`：对于无符号为0，对于有符号为1
* `info.kind`：BTF_KIND_ENUM64
* `info.vlen`：枚举值的数量
* `size`：1/2/4/8

`btf_type` 后跟 `info.vlen` 数量的 `struct btf_enum64`。
```
struct btf_enum64 {
    __u32   name_off;
    __u32   val_lo32;
    __u32   val_hi32;
};
```

`btf_enum64` 的编码：
* `name_off`：指向有效 C 标识符的偏移量
* `val_lo32`：64位值的低32位
* `val_hi32`：64位值的高32位

如果原始枚举值是有符号的且大小小于8字节，则该值将扩展为8字节。

### 3. BTF 内核 API

涉及 BTF 的 bpf 系统调用命令包括：
* BPF_BTF_LOAD：将 BTF 数据块加载到内核中
* BPF_MAP_CREATE：使用 btf 键和值类型信息创建映射
* BPF_PROG_LOAD：使用 btf 函数和行信息加载程序
* BPF_BTF_GET_FD_BY_ID：获取 btf 文件描述符
* BPF_OBJ_GET_INFO_BY_FD：返回 btf、函数信息、行信息和其他与 btf 相关的信息

工作流程通常如下所示：
```
应用程序:
    BPF_BTF_LOAD
        |
        v
    BPF_MAP_CREATE 和 BPF_PROG_LOAD
        |
        V
    .....

自省工具:
    .....
BPF_{PROG,MAP}_GET_NEXT_ID（获取程序/映射ID）
        |
        V
BPF_{PROG,MAP}_GET_FD_BY_ID（获取程序/映射文件描述符）
        |
        V
BPF_OBJ_GET_INFO_BY_FD（获取带有 btf_id 的 bpf_prog_info/bpf_map_info）
        |                                     |
        V                                     |
BPF_BTF_GET_FD_BY_ID（获取 btf_fd）         |
        |                                     |
        V                                     |
BPF_OBJ_GET_INFO_BY_FD（获取 btf）          |
        |                                     |
        V                                     V
漂亮打印类型、转储函数签名和行信息等
```

#### 3.1 BPF_BTF_LOAD

将 BTF 数据块加载到内核中。根据 :ref:`BTF_Type_String` 描述的数据块可以直接加载到内核中。一个 `btf_fd` 将被返回给用户空间。
### 3.2 创建BPF_MAP

可以使用`btf_fd`和指定的键/值类型ID来创建映射。如下所示：

```plaintext
__u32   btf_fd;         /* 指向BTF类型数据的文件描述符 */
__u32   btf_key_type_id;        /* 键的BTF类型ID */
__u32   btf_value_type_id;      /* 值的BTF类型ID */
```

在libbpf中，可以通过额外的注解来定义映射，例如：
```plaintext
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __type(key, int);
    __type(value, struct ipv_counts);
    __uint(max_entries, 4);
} btf_map SEC(".maps");
```

在解析ELF时，libbpf能够自动提取键/值类型ID，并将它们分配给BPF_MAP_CREATE属性。

### 3.3 BPF_PROG_LOAD

在加载程序时，可以将func_info和line_info与以下属性的适当值传递给内核：
```plaintext
__u32           insn_cnt;
__aligned_u64   insns;
...
__u32           prog_btf_fd;    /* 指向BTF类型数据的文件描述符 */
__u32           func_info_rec_size;     /* 用户空间bpf_func_info大小 */
__aligned_u64   func_info;      /* 函数信息 */
__u32           func_info_cnt;  /* bpf_func_info记录数量 */
__u32           line_info_rec_size;     /* 用户空间bpf_line_info大小 */
__aligned_u64   line_info;      /* 行信息 */
__u32           line_info_cnt;  /* bpf_line_info记录数量 */
```

func_info和line_info分别是以下结构数组的一部分：
```plaintext
struct bpf_func_info {
    __u32   insn_off; /* [0, insn_cnt - 1] */
    __u32   type_id;  /* 指向BTF_KIND_FUNC类型 */
};
struct bpf_line_info {
    __u32   insn_off; /* [0, insn_cnt - 1] */
    __u32   file_name_off; /* 文件名字符串表偏移量 */
    __u32   line_off; /* 源代码行字符串表偏移量 */
    __u32   line_col; /* 行号和列号 */
};
```

func_info_rec_size是每个func_info记录的大小，line_info_rec_size是每个line_info记录的大小。将记录大小传递给内核使将来扩展记录成为可能。

对于func_info有以下要求：
- func_info[0].insn_off必须为0
- func_info中的insn_off严格递增，并匹配BPF函数边界

对于line_info有以下要求：
- 每个函数的第一条指令必须有一个指向它的line_info记录
- line_info中的insn_off严格递增

对于line_info，行号和列号的定义如下：
```plaintext
#define BPF_LINE_INFO_LINE_NUM(line_col)        ((line_col) >> 10)
#define BPF_LINE_INFO_LINE_COL(line_col)        ((line_col) & 0x3ff)
```

### 3.4 BPF_{PROG,MAP}_GET_NEXT_ID

在内核中，每个加载的程序、映射或BTF都有一个唯一的ID。这个ID在程序、映射或BTF的生命周期内不会改变。

BPF_{PROG,MAP}_GET_NEXT_ID系统调用命令将所有ID（每个命令一个）返回到用户空间，分别针对BPF程序或映射，因此检查工具可以检查所有程序和映射。

### 3.5 BPF_{PROG,MAP}_GET_FD_BY_ID

检查工具不能使用ID获取有关程序或映射的详细信息。但是，可以使用此命令通过ID获取与程序或映射关联的文件描述符。这使得即使不知道具体名称，也能访问和操作这些资源。
为了进行引用计数，首先需要获取文件描述符。
3.6 BPF_OBJ_GET_INFO_BY_FD
--------------------------

一旦获得了程序/映射的文件描述符（fd），内省工具可以从内核获取关于该fd的详细信息，其中一些与BTF相关。例如，“bpf_map_info”返回“btf_id”和键/值类型id；“bpf_prog_info”返回“btf_id”，函数信息以及转换后的BPF字节码的行信息。
3.7 BPF_BTF_GET_FD_BY_ID
------------------------

通过在“bpf_map_info”和“bpf_prog_info”中获得的“btf_id”，BPF系统调用命令BPF_BTF_GET_FD_BY_ID可以检索一个btf fd。然后，使用BPF_OBJ_GET_INFO_BY_FD命令，最初使用BPF_BTF_LOAD加载到内核中的btf blob可以被检索出来。
有了btf blob，“bpf_map_info”和“bpf_prog_info”，内省工具便完全掌握了btf知识，能够漂亮地打印出映射键/值，转储函数签名和行信息，连同字节码/jit代码。
4. ELF文件格式接口
============================

4.1 .BTF段
----------------

.BTF段包含类型和字符串数据。此段的格式与在:ref:`BTF_Type_String`中描述的一致。
.. _BTF_Ext_Section:

4.2 .BTF.ext段
--------------------

.BTF.ext段编码了函数信息、行信息和CO-RE重定位，这些在加载到内核之前需要加载器处理。
.BTF.ext段的规范定义在“tools/lib/bpf/btf.h”和“tools/lib/bpf/btf.c”中。
.BTF.ext段当前的头部结构如下：

    struct btf_ext_header {
        __u16   magic;       // 魔术数字
        __u8    version;     // 版本号
        __u8    flags;       // 标志
        __u32   hdr_len;     // 头部长度

        // 所有偏移量都是相对于此头部末尾的字节数
        __u32   func_info_off;  // 函数信息偏移
        __u32   func_info_len;  // 函数信息长度
        __u32   line_info_off;  // 行信息偏移
        __u32   line_info_len;  // 行信息长度

        // .BTF.ext头部的可选部分
        __u32   core_relo_off;  // CO-RE重定位偏移
        __u32   core_relo_len;  // CO-RE重定位长度
    };

它与.BTF段非常相似。但代替类型/字符串段，它包含了函数信息、行信息和核心重定位子段。
有关函数信息和行信息记录格式的详细信息，请参阅:ref:`BPF_Prog_Load`。
`func_info` 的组织结构如下：

     func_info_rec_size              /* __u32 值 */
     btf_ext_info_sec 对于 section #1 /* section #1 的 func_info */
     btf_ext_info_sec 对于 section #2 /* section #2 的 func_info */
     ..
`func_info_rec_size` 指定了在生成 `.BTF.ext` 时 `bpf_func_info` 结构的大小。下面定义的 `btf_ext_info_sec` 是针对每个特定 ELF section 的 `func_info` 集合。::

     struct btf_ext_info_sec {
        __u32   sec_name_off; /* section 名称的偏移量 */
        __u32   num_info;
        /* 后跟 num_info * 记录大小的字节数 */
        __u8    data[0];
     };

此处，num_info 必须大于 0
`line_info` 的组织结构如下：

     line_info_rec_size              /* __u32 值 */
     btf_ext_info_sec 对于 section #1 /* section #1 的 line_info */
     btf_ext_info_sec 对于 section #2 /* section #2 的 line_info */
     ..
`line_info_rec_size` 指定了在生成 `.BTF.ext` 时 `bpf_line_info` 结构的大小
`bpf_func_info->insn_off` 和 `bpf_line_info->insn_off` 在内核 API 和 ELF API 中的解释不同。对于内核 API，`insn_off` 是以 `struct bpf_insn` 为单位的指令偏移量。对于 ELF API，`insn_off` 是从 section 开始（`btf_ext_info_sec->sec_name_off`）的字节偏移量。
`core_relo` 的组织结构如下：::

     core_relo_rec_size              /* __u32 值 */
     btf_ext_info_sec 对于 section #1 /* section #1 的 core_relo */
     btf_ext_info_sec 对于 section #2 /* section #2 的 core_relo */

`core_relo_rec_size` 指定了在生成 `.BTF.ext` 时 `bpf_core_relo` 结构的大小。单个 `btf_ext_info_sec` 内的所有 `bpf_core_relo` 结构描述了应用于由 `btf_ext_info_sec->sec_name_off` 命名的 section 的重定位。
更多关于 CO-RE 重定位的信息，请参阅 :ref:`Documentation/bpf/llvm_reloc.rst <btf-co-re-relocations>`。

4.2 `.BTF_ids` section
----------------------

`.BTF_ids` section 编码了在内核中使用的 BTF ID 值
此 section 在内核编译期间创建，借助于 `include/linux/btf_ids.h` 头文件中定义的宏。内核代码可以使用它们来创建 BTF ID 值的列表和集合（排序列表）
`BTF_ID_LIST` 和 `BTF_ID` 宏定义了未排序的 BTF ID 值列表，其语法如下：

  BTF_ID_LIST(list)
  BTF_ID(type1, name1)
  BTF_ID(type2, name2)

这将导致在 `.BTF_ids` section 中形成以下布局：

  __BTF_ID__type1__name1__1:
  .zero 4
  __BTF_ID__type2__name2__2:
  .zero 4

定义了变量 `u32 list[];` 来访问该列表。
"BTF_ID_UNUSED"宏定义了4个零字节。当我们在BTF_ID_LIST中定义未使用的条目时会用到它，例如：

      BTF_ID_LIST(bpf_skb_output_btf_ids)
      BTF_ID(struct, sk_buff)
      BTF_ID_UNUSED
      BTF_ID(struct, task_struct)

"BTF_SET_START/END"宏对定义了排序的BTF ID值列表及其数量，语法如下：

  BTF_SET_START(set)
  BTF_ID(type1, name1)
  BTF_ID(type2, name2)
  BTF_SET_END(set)

这将在.BTF_ids段中生成以下布局：

  __BTF_ID__set__set:
  .zero 4
  __BTF_ID__type1__name1__3:
  .zero 4
  __BTF_ID__type2__name2__4:
  .zero 4

定义了"struct btf_id_set set;"变量以访问该列表。
"typeX"名称可以是以下之一：

   struct, union, typedef, func

在解析BTF ID值时用作过滤器。
所有BTF ID列表和集都在.BTF_ids段中编译，并在内核构建的链接阶段由"resolve_btfids"工具解析。

5. 使用BTF

5.1 bpftool地图美化打印

借助BTF，可以根据字段而非仅根据原始字节来打印地图键/值。对于大型结构或数据结构具有位字段的情况，这一点尤其有价值。例如，对于以下地图：

      枚举 A { A1, A2, A3, A4, A5 };
      典型枚举 A ___A;
      结构 tmp_t {
           字符 a1:4;
           整数  a2:4;
           整数  :4;
           __u32 a3:4;
           整数 b;
           ___A b1:4;
           枚举 A b2:4;
      };
      结构 {
           __uint(类型, BPF_MAP_TYPE_ARRAY);
           __type(键, 整数);
           __type(值, 结构 tmp_t);
           __uint(最大条目, 1);
      } tmpmap SEC(".maps");

bpftool能够美化打印如下：

      [{
            "键": 0,
            "值": {
                "a1": 0x2,
                "a2": 0x4,
                "a3": 0x6,
                "b": 7,
                "b1": 0x8,
                "b2": 0xa
            }
        }
      ]

5.2 bpftool程序转储

以下是示例，展示了func_info和line_info如何帮助程序转储，提供更好的内核符号名称、函数原型和行信息。例如：

    $ bpftool 程序 转储 JITed 针定 /sys/fs/bpf/test_btf_haskv
    [...]
    整数 test_long_fname_2(结构 dummy_tracepoint_args * arg):
    bpf_prog_44a040bf25481309_test_long_fname_2:
    ; 静态整数 test_long_fname_2(结构 dummy_tracepoint_args *arg)
       0:   推入   %rbp
       1:   移动    %rsp,%rbp
       4:   减少    $0x30,%rsp
       b:   减少    $0x28,%rbp
       f:   移动    %rbx,0x0(%rbp)
      13:   移动    %r13,0x8(%rbp)
      17:   移动    %r14,0x10(%rbp)
      1b:   移动    %r15,0x18(%rbp)
      1f:   异或    %eax,%eax
      21:   移动    %rax,0x20(%rbp)
      25:   异或    %esi,%esi
    ; 整数 键 = 0;
      27:   移动    %esi,-0x4(%rbp)
    ; 如果(!arg->sock)
      2a:   移动    0x8(%rdi),%rdi
    ; 如果(!arg->sock)
      2e:   比较    $0x0,%rdi
      32:   跳等于 0x0000000000000070
      34:   移动    %rbp,%rsi
    ; 计数 = bpf_map_lookup_elem(&btf_map, &键);
    [...]

5.3 验证器日志

以下是示例，展示了line_info如何帮助调试验证失败。例如：

       /* 位于 tools/testing/selftests/bpf/test_xdp_noinline.c 的代码
        * 修改为以下
*/
       数据 = (void *)(长整数)xdp->数据;
       数据结束 = (void *)(长整数)xdp->数据结束;
       /*
       如果 (数据 + 4 > 数据结束)
               返回 XDP_DROP;
       */
       *(u32 *)数据 = 目的地->目的地;

    $ bpftool 程序 加载 ./test_xdp_noinline.o /sys/fs/bpf/test_xdp_noinline 类型 xdp
        ; 数据 = (void *)(长整数)xdp->数据;
        224: (79) r2 = *(u64 *)(r10 -112)
        225: (61) r2 = *(u32 *)(r2 +0)
        ; *(u32 *)数据 = 目的地->目的地;
        226: (63) *(u32 *)(r2 +0) = r1
        对包的无效访问，偏移量=0 大小=4，R2(id=0,偏移量=0,r=0)
        R2偏移量超出包范围

6. BTF生成

您需要最新的pahole

  https://git.kernel.org/pub/scm/devel/pahole/pahole.git/

或者llvm（8.0或更高版本）。pahole充当dwarf2btf转换器。它尚不支持.BTF.ext和btf BTF_KIND_FUNC类型。例如，

      -bash-4.4$ cat t.c
      结构 t {
        整数 a:2;
        整数 b:3;
        整数 c:2;
      } g;
      -bash-4.4$ gcc -c -O2 -g t.c
      -bash-4.4$ pahole -JV t.o
      文件 t.o：
      [1] 结构 t kind_flag=1 大小=4 vlen=3
              a 类型_id=2 位字段大小=2 位偏移量=0
              b 类型_id=2 位字段大小=3 位偏移量=2
              c 类型_id=2 位字段大小=2 位偏移量=5
      [2] 整数 int 大小=4 位偏移量=0 位数=32 编码=SIGNED

llvm能够直接通过-g为bpf目标生成.BTF和.BTF.ext。汇编代码(-S)能够在汇编格式中显示BTF编码。例如，

    -bash-4.4$ cat t2.c
    典型整数 __int32;
    结构 t2 {
      整数 a2;
      整数 (*f2)(字符 q1, __int32 q2, ...);
      整数 (*f3)();
    } g2;
    整数 main() { 返回 0; }
    整数 test() { 返回 0; }
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
            .long   7182                    # 行7 列14
            .long   .Ltmp3
            .long   7
            .long   58
            .long   8206                    # 行8 列14

7. 测试

内核BPF自测`tools/testing/selftests/bpf/prog_tests/btf.c`_
提供了广泛的BTF相关测试。
链接:
.. _tools/testing/selftests/bpf/prog_tests/btf.c:
   https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/tools/testing/selftests/bpf/prog_tests/btf.c

翻译为:

链接:
.. _工具/测试/selftests/bpf/程序测试/btf.c:
   https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/工具/测试/selftests/bpf/程序测试/btf.c

但是，这种翻译方式并不常用。在技术文档中，通常会保持原始的英文路径或术语不变，以避免混淆和保持一致性。因此，更常见的做法是：

链接:
.. _tools/testing/selftests/bpf/prog_tests/btf.c:
   https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/tools/testing/selftests/bpf/prog_tests/btf.c

并在文本中解释这个链接所指向的内容，例如：“这是一个指向Linux内核稳定分支中BPF自测代码btf.c的链接。”
