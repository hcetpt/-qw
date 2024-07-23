SPDX 许可证标识符：（LGPL-2.1 或 BSD-2-Clause）

====================
BPF LLVM 定位类型
====================

本文件描述了 LLVM BPF 后端的定位类型。
定位记录
==================

LLVM BPF 后端通过以下 16 字节的 ELF 结构记录每个定位：

```cpp
typedef struct
{
    Elf64_Addr    r_offset;  // 从节起始的偏移量
    Elf64_Xword   r_info;    // 定位类型和符号索引
} Elf64_Rel;
```

例如，对于以下代码：

```c
int g1 __attribute__((section("sec")));
int g2 __attribute__((section("sec")));
static volatile int l1 __attribute__((section("sec")));
static volatile int l2 __attribute__((section("sec")));
int test() {
    return g1 + g2 + l1 + l2;
}
```

使用 `clang --target=bpf -O2 -c test.c` 编译后，使用 `llvm-objdump -dr test.o` 得到的代码如下：

```
       0:       18 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 r1 = 0 ll
                0000000000000000:  R_BPF_64_64  g1
       2:       61 11 00 00 00 00 00 00 r1 = *(u32 *)(r1 + 0)
       3:       18 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 r2 = 0 ll
                0000000000000018:  R_BPF_64_64  g2
       5:       61 20 00 00 00 00 00 00 r0 = *(u32 *)(r2 + 0)
       6:       0f 10 00 00 00 00 00 00 r0 += r1
       7:       18 01 00 00 08 00 00 00 00 00 00 00 00 00 00 00 r1 = 8 ll
                0000000000000038:  R_BPF_64_64  sec
       9:       61 11 00 00 00 00 00 00 r1 = *(u32 *)(r1 + 0)
      10:       0f 10 00 00 00 00 00 00 r0 += r1
      11:       18 01 00 00 0c 00 00 00 00 00 00 00 00 00 00 00 r1 = 12 ll
                0000000000000058:  R_BPF_64_64  sec
      13:       61 11 00 00 00 00 00 00 r1 = *(u32 *)(r1 + 0)
      14:       0f 10 00 00 00 00 00 00 r0 += r1
      15:       95 00 00 00 00 00 00 00 exit
```

在上面的示例中，有四个定位用于四个 `LD_imm64` 指令。下面的 `llvm-readelf -r test.o` 显示了这四个定位的二进制值：

```
Relocation section '.rel.text' at offset 0x190 contains 4 entries:
      Offset             Info             Type               Symbol's Value  Symbol's Name
  0000000000000000  0000000600000001 R_BPF_64_64            0000000000000000 g1
  0000000000000018  0000000700000001 R_BPF_64_64            0000000000000004 g2
  0000000000000038  0000000400000001 R_BPF_64_64            0000000000000000 sec
  0000000000000058  0000000400000001 R_BPF_64_64            0000000000000000 sec
```

每个定位由 `Offset`（8 字节）和 `Info`（8 字节）表示。例如，第一个定位对应于第一条指令（偏移量 0x0），相应的 `Info` 指示定位类型为 `R_BPF_64_64`（类型 1）和符号表中的条目（条目 6）。下面是使用 `llvm-readelf -s test.o` 的符号表：

```
Symbol table '.symtab' contains 8 entries:
     Num:    Value          Size Type    Bind   Vis       Ndx Name
       0: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT   UND
       1: 0000000000000000     0 FILE    LOCAL  DEFAULT   ABS test.c
       2: 0000000000000008     4 OBJECT  LOCAL  DEFAULT     4 l1
       3: 000000000000000c     4 OBJECT  LOCAL  DEFAULT     4 l2
       4: 0000000000000000     0 SECTION LOCAL  DEFAULT     4 sec
       5: 0000000000000000   128 FUNC    GLOBAL DEFAULT     2 test
       6: 0000000000000000     4 OBJECT  GLOBAL DEFAULT     4 g1
       7: 0000000000000004     4 OBJECT  GLOBAL DEFAULT     4 g2
```

第 6 个条目是全局变量 `g1`，其值为 0。同样，第二个定位位于 `.text` 偏移量 `0x18`，指令 3，具有 `R_BPF_64_64` 类型，并引用符号表中的第 7 个条目。第二个定位解析为全局变量 `g2`，该变量具有符号值 4。符号值代表从 `.data` 节开始存储全局变量 `g2` 初始值的偏移量。

第三和第四个定位引用静态变量 `l1` 和 `l2`。从上面的 `.rel.text` 节来看，不清楚它们实际上引用的是哪个符号，因为它们都引用了符号表中的条目 4，即符号 `sec`，它具有 `STT_SECTION` 类型并表示一个节。因此，对于静态变量或函数，节偏移量被写入原始指令缓冲区，称为 `A`（加数）。查看上述指令 `7` 和 `11`，它们具有节偏移量 `8` 和 `12`。
从符号表中，我们可以找到它们分别对应于`l1`和`l2`的条目“2”和“3”。通常，“A”对于全局变量和函数是0，而对于静态变量/函数，则是节偏移量或基于节偏移量的一些计算结果。非节偏移量的情况指的是函数调用。下面将提供更详细的说明。

不同的重定位类型
=================

支持六种重定位类型。以下是一个概述，其中“S”代表符号表中符号的值：

  枚举   ELF重定位类型       描述           位大小  偏移量        计算方式
  0     R_BPF_NONE         无
  1     R_BPF_64_64        ld_imm64指令   32       r_offset + 4  S + A
  2     R_BPF_64_ABS64     正常数据       64       r_offset      S + A
  3     R_BPF_64_ABS32     正常数据       32       r_offset      S + A
  4     R_BPF_64_NODYLD32  .BTF[.ext]数据 32       r_offset      S + A
  10    R_BPF_64_32        调用指令       32       r_offset + 4  (S + A) / 8 - 1

例如，`R_BPF_64_64`重定位类型用于`ld_imm64`指令。实际待重定位的数据（0或节偏移量）存储在`r_offset + 4`处，读写数据位大小为32（4字节）。可以通过符号值加上隐式加数来解析重定位。请注意，“位大小”为32意味着节偏移量必须小于等于`UINT32_MAX`，这是由LLVM BPF后端强制执行的。
在另一种情况下，`R_BPF_64_ABS64`重定位类型用于正常64位数据。实际待重定位的数据存储在`r_offset`处，读写数据位大小为64（8字节）。可以通过符号值加上隐式加数来解析重定位。
`R_BPF_64_ABS32`和`R_BPF_64_NODYLD32`类型都是针对32位数据的，但是`R_BPF_64_NODYLD32`特别指代`.BTF`和`.BTF.ext`节中的重定位。对于涉及LLVM `ExecutionEngine RuntimeDyld`的情况，如bcc，`R_BPF_64_NODYLD32`类型的重定位不应该解析为实际的函数/变量地址。否则，`.BTF`和`.BTF.ext`将无法被bcc和内核使用。
`R_BPF_64_32`类型用于调用指令。调用目标节偏移量存储在`r_offset + 4`（32位），并计算为`(S + A) / 8 - 1`。

示例
====

`R_BPF_64_64`和`R_BPF_64_32`类型用于解析`ld_imm64`和`call`指令。例如：

```c
__attribute__((noinline)) __attribute__((section("sec1")))
int gfunc(int a, int b) {
    return a * b;
}
static __attribute__((noinline)) __attribute__((section("sec1")))
int lfunc(int a, int b) {
    return a + b;
}
int global __attribute__((section("sec2")));
int test(int a, int b) {
    return gfunc(a, b) +  lfunc(a, b) + global;
}
```

使用`clang --target=bpf -O2 -c test.c`编译后，我们将有以下代码与`llvm-objdump -dr test.o`一起使用：

```
.text节的反汇编：

0000000000000000 <test>:
         0:       bf 26 00 00 00 00 00 00 r6 = r2
         1:       bf 17 00 00 00 00 00 00 r7 = r1
         2:       85 10 00 00 ff ff ff ff call -1
                  0000000000000010:  R_BPF_64_32  gfunc
         3:       bf 08 00 00 00 00 00 00 r8 = r0
         4:       bf 71 00 00 00 00 00 00 r1 = r7
         5:       bf 62 00 00 00 00 00 00 r2 = r6
         6:       85 10 00 00 02 00 00 00 call 2
                  0000000000000030:  R_BPF_64_32  sec1
         7:       0f 80 00 00 00 00 00 00 r0 += r8
         8:       18 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 r1 = 0 ll
                  0000000000000040:  R_BPF_64_64  global
        10:       61 11 00 00 00 00 00 00 r1 = *(u32 *)(r1 + 0)
        11:       0f 10 00 00 00 00 00 00 r0 += r1
        12:       95 00 00 00 00 00 00 00 exit

sec1节的反汇编：

0000000000000000 <gfunc>:
         0:       bf 20 00 00 00 00 00 00 r0 = r2
         1:       2f 10 00 00 00 00 00 00 r0 *= r1
         2:       95 00 00 00 00 00 00 00 exit

0000000000000018 <lfunc>:
         3:       bf 20 00 00 00 00 00 00 r0 = r2
         4:       0f 10 00 00 00 00 00 00 r0 += r1
         5:       95 00 00 00 00 00 00 00 exit
```

第一个重定位对应于`gfunc(a, b)`，其中`gfunc`的值为0，因此`call`指令的偏移量为`(0 + 0)/8 - 1 = -1`。
第二个重定位对应于 ``lfunc(a, b)``，其中 ``lfunc`` 有一个节偏移量 ``0x18``，因此 "call" 指令的偏移量为 ``(0 + 0x18)/8 - 1 = 2``
第三个重定位对应于 ``global`` 的 ld_imm64，它具有一个节偏移量 ``0``
以下是一个示例，展示如何生成 R_BPF_64_ABS64 ::

  定义一个函数 global() { 返回 0; }
  定义一个结构体 t { void *g; } 并初始化 gbl = { global };

使用 ``clang --target=bpf -O2 -g -c test.c`` 编译后，在 ``.data`` 节中使用命令 ``llvm-readelf -r test.o`` 可以看到如下重定位 ::

  在偏移量 0x458 处的重定位节 '.rel.data' 包含 1 条记录：
      偏移量             Info             类型               符号值        符号名称
  0000000000000000  0000000700000002 R_BPF_64_ABS64         0000000000000000 global

重定位表明 ``.data`` 节的前 8 字节应该被填充为 ``global`` 变量的地址
通过 ``llvm-readelf`` 输出，我们可以看到 dwarf 节包含大量 ``R_BPF_64_ABS32`` 和 ``R_BPF_64_ABS64`` 重定位 ::

  在偏移量 0x468 处的重定位节 '.rel.debug_info' 包含 13 条记录：
      偏移量             Info             类型               符号值        符号名称
  0000000000000006  0000000300000003 R_BPF_64_ABS32         0000000000000000 .debug_abbrev
  000000000000000c  0000000400000003 R_BPF_64_ABS32         0000000000000000 .debug_str
  ...
  000000000000001e  0000000200000002 R_BPF_64_ABS64         0000000000000000 .text
  ...
  0000000000000037  0000000800000002 R_BPF_64_ABS64         0000000000000000 gbl
  ...

.BTF/.BTF.ext 节有 R_BPF_64_NODYLD32 重定位 ::

  在偏移量 0x538 处的重定位节 '.rel.BTF' 包含 1 条记录：
      偏移量             Info             类型               符号值        符号名称
  0000000000000084  0000000800000004 R_BPF_64_NODYLD32      0000000000000000 gbl

在偏移量 0x548 处的重定位节 '.rel.BTF.ext' 包含 2 条记录：
      偏移量             Info             类型               符号值        符号名称
  000000000000002c  0000000200000004 R_BPF_64_NODYLD32      0000000000000000 .text
  0000000000000040  0000000200000004 R_BPF_64_NODYLD32      0000000000000000 .text

.. _btf-co-re-relocations:

=================
CO-RE 重定位
=================

从目标文件的角度来看，CO-RE 机制是通过一组特定于 CO-RE 的重定位记录实现的。这些重定位记录与 ELF 重定位无关，并且编码在 .BTF.ext 节中。
有关 .BTF.ext 结构的更多信息，请参阅 :ref:`Documentation/bpf/btf.rst <BTF_Ext_Section>`
CO-RE 重定位应用于 BPF 指令，以便在加载时使用与目标内核相关的信息更新指令的立即数或偏移字段
要修补的字段根据指令类别选择：

* 对于 BPF_ALU, BPF_ALU64, BPF_LD，将修补 'immediate' 字段；
* 对于 BPF_LDX, BPF_STX, BPF_ST，将修补 'offset' 字段；
* BPF_JMP, BPF_JMP32 指令 **不应** 被修补
重定位种类
================

有几种类型的 CO-RE 重定位，可以分为三组：

* 基于字段的 - 使用与字段相关的信息修补指令，例如，更改 BPF_LDX 指令的偏移字段以反映目标内核中特定结构字段的偏移量
* 基于类型的 - 与类型相关的补丁指令，例如
将BPF_ALU移动指令的立即数字段更改为0或1以
反映特定类型是否存在于目标内核中
* 基于枚举的 - 与枚举相关的补丁指令，例如
将BPF_LD_IMM64指令的立即数字段更改以反映
目标内核中特定枚举字面值的值
所有重定位种类的完整列表由以下枚举表示：

.. code-block:: c

 enum bpf_core_relo_kind {
	BPF_CORE_FIELD_BYTE_OFFSET = 0,  /* 字段字节偏移量 */
	BPF_CORE_FIELD_BYTE_SIZE   = 1,  /* 字段大小（字节） */
	BPF_CORE_FIELD_EXISTS      = 2,  /* 目标内核中的字段存在性 */
	BPF_CORE_FIELD_SIGNED      = 3,  /* 字段符号性（0 - 无符号，1 - 有符号） */
	BPF_CORE_FIELD_LSHIFT_U64  = 4,  /* 位字段特异性左移位 */
	BPF_CORE_FIELD_RSHIFT_U64  = 5,  /* 位字段特异性右移位 */
	BPF_CORE_TYPE_ID_LOCAL     = 6,  /* 本地BPF对象中的类型ID */
	BPF_CORE_TYPE_ID_TARGET    = 7,  /* 目标内核中的类型ID */
	BPF_CORE_TYPE_EXISTS       = 8,  /* 目标内核中的类型存在性 */
	BPF_CORE_TYPE_SIZE         = 9,  /* 类型大小（字节） */
	BPF_CORE_ENUMVAL_EXISTS    = 10, /* 目标内核中的枚举值存在性 */
	BPF_CORE_ENUMVAL_VALUE     = 11, /* 枚举值整数值 */
	BPF_CORE_TYPE_MATCHES      = 12, /* 目标内核中的类型匹配 */
 };

注释：

* ``BPF_CORE_FIELD_LSHIFT_U64`` 和 ``BPF_CORE_FIELD_RSHIFT_U64`` 应用于使用以下算法读取位字段值：

  .. code-block:: c

     // 从“struct s”读取位字段“f”
     is_signed = relo(s->f, BPF_CORE_FIELD_SIGNED)
     off = relo(s->f, BPF_CORE_FIELD_BYTE_OFFSET)
     sz  = relo(s->f, BPF_CORE_FIELD_BYTE_SIZE)
     l   = relo(s->f, BPF_CORE_FIELD_LSHIFT_U64)
     r   = relo(s->f, BPF_CORE_FIELD_RSHIFT_U64)
     // 定义“v”为大小为“sz”的有符号或无符号整数
     v = *({s|u}<sz> *)((void *)s + off)
     v <<= l
     v >>= r

* ``BPF_CORE_TYPE_MATCHES`` 查询匹配关系，定义如下：

  * 对于整数：如果大小和符号性匹配，则类型匹配；
  * 对于数组&指针：目标类型递归匹配；
  * 对于结构体&联合体：

    * 本地成员需要在目标中以相同名称存在；

    * 对于每个成员，我们递归检查匹配，除非它已经在指针后面，在这种情况下，我们只检查匹配的名称和兼容的类型；

  * 对于枚举：

    * 本地变体必须通过符号名称（但不是数值）在目标中有匹配；

    * 大小必须匹配（但枚举可以匹配enum64反之亦然）；

  * 对于函数指针：

    * 本地类型中的参数数量和位置必须与目标匹配；
    * 对于每个参数和返回值，我们递归检查匹配

CO-RE 重定位记录
==================

重定位记录被编码为以下结构：

.. code-block:: c

 struct bpf_core_relo {
	__u32 insn_off;
	__u32 type_id;
	__u32 access_str_off;
	enum bpf_core_relo_kind kind;
 };

* ``insn_off`` - 在与此重定位关联的代码段中的指令偏移量（字节）
* ``type_id`` - 可重定位类型或字段的“根”（包含）实体的BTF类型ID；
* ``access_str_off`` - 对应.BTF字符串段中的偏移量
字符串解释依赖于特定的重定位类型：

  * 对于基于字段的重定位，字符串使用一系列字段和数组索引（用冒号(:)分隔）来编码访问的字段。其概念上非常接近LLVM的`getelementptr <GEP_>`_指令的参数，用于标识到字段的偏移。考虑以下C代码：

    .. code-block:: c

       struct sample {
           int a;
           int b;
           struct { int c[10]; };
       } __attribute__((preserve_access_index));
       struct sample *s;

    * 访问``s[0].a``将被编码为``0:0``：

      * ``0``: “s”的第一个元素（就像“s”是一个数组）；
      * ``0``: “struct sample”中字段“a”的索引
* 访问``s->a``也将被编码为``0:0``
* 访问``s->b``将被编码为``0:1``：

      * ``0``: “s”的第一个元素；
      * ``1``: “struct sample”中字段“b”的索引
* 访问``s[1].c[5]``将被编码为``1:2:0:5``：

      * ``1``: “s”的第二个元素；
      * ``2``: “struct sample”中匿名结构字段的索引；
      * ``0``: 匿名结构中字段“c”的索引；
      * ``5``: 访问数组元素#5
对于基于类型的重定位，字符串预期仅为"0"；

对于基于枚举值的重定位，字符串包含其在枚举类型内的枚举值索引；

`kind` - `enum bpf_core_relo_kind`之一

.. _GEP: https://llvm.org/docs/LangRef.html#getelementptr-instruction

.. _btf_co_re_relocation_examples:

CO-RE 重定位示例
=========================

对于以下C代码：

.. code-block:: c

 struct foo {
   int a;
   int b;
   unsigned c:15;
 } __attribute__((preserve_access_index));

 enum bar { U, V };

带有以下BTF定义：

.. code-block::

 ..
[2] STRUCT 'foo' size=8 vlen=2
        'a' type_id=3 bits_offset=0
        'b' type_id=3 bits_offset=32
        'c' type_id=4 bits_offset=64 bitfield_size=15
 [3] INT 'int' size=4 bits_offset=0 nr_bits=32 encoding=SIGNED
 [4] INT 'unsigned int' size=4 bits_offset=0 nr_bits=32 encoding=(none)
 ..
[16] ENUM 'bar' encoding=UNSIGNED size=4 vlen=2
        'U' val=0
        'V' val=1

当使用``__attribute__((preserve_access_index))``时，会自动生成字段偏移重定位，例如：

.. code-block:: c

  void alpha(struct foo *s, volatile unsigned long *g) {
    *g = s->a;
    s->a = 1;
  }

  00 <alpha>:
    0:  r3 = *(s32 *)(r1 + 0x0)
           00:  CO-RE <byte_off> [2] struct foo::a (0:0)
    1:  *(u64 *)(r2 + 0x0) = r3
    2:  *(u32 *)(r1 + 0x0) = 0x1
           10:  CO-RE <byte_off> [2] struct foo::a (0:0)
    3:  exit


所有类型的重定位都可以通过内置函数请求。
例如基于字段的重定位：

.. code-block:: c

  void bravo(struct foo *s, volatile unsigned long *g) {
    *g = __builtin_preserve_field_info(s->b, 0 /* field byte offset */);
    *g = __builtin_preserve_field_info(s->b, 1 /* field byte size */);
    *g = __builtin_preserve_field_info(s->b, 2 /* field existence */);
    *g = __builtin_preserve_field_info(s->b, 3 /* field signedness */);
    *g = __builtin_preserve_field_info(s->c, 4 /* bitfield left shift */);
    *g = __builtin_preserve_field_info(s->c, 5 /* bitfield right shift */);
  }

  20 <bravo>:
     4:     r1 = 0x4
            20:  CO-RE <byte_off> [2] struct foo::b (0:1)
     5:     *(u64 *)(r2 + 0x0) = r1
     6:     r1 = 0x4
            30:  CO-RE <byte_sz> [2] struct foo::b (0:1)
     7:     *(u64 *)(r2 + 0x0) = r1
     8:     r1 = 0x1
            40:  CO-RE <field_exists> [2] struct foo::b (0:1)
     9:     *(u64 *)(r2 + 0x0) = r1
    10:     r1 = 0x1
            50:  CO-RE <signed> [2] struct foo::b (0:1)
    11:     *(u64 *)(r2 + 0x0) = r1
    12:     r1 = 0x31
            60:  CO-RE <lshift_u64> [2] struct foo::c (0:2)
    13:     *(u64 *)(r2 + 0x0) = r1
    14:     r1 = 0x31
            70:  CO-RE <rshift_u64> [2] struct foo::c (0:2)
    15:     *(u64 *)(r2 + 0x0) = r1
    16:     exit


基于类型的重定位：

.. code-block:: c

  void charlie(struct foo *s, volatile unsigned long *g) {
    *g = __builtin_preserve_type_info(*s, 0 /* type existence */);
    *g = __builtin_preserve_type_info(*s, 1 /* type size */);
    *g = __builtin_preserve_type_info(*s, 2 /* type matches */);
    *g = __builtin_btf_type_id(*s, 0 /* type id in this object file */);
    *g = __builtin_btf_type_id(*s, 1 /* type id in target kernel */);
  }

  88 <charlie>:
    17:     r1 = 0x1
            88:  CO-RE <type_exists> [2] struct foo
    18:     *(u64 *)(r2 + 0x0) = r1
    19:     r1 = 0xc
            98:  CO-RE <type_size> [2] struct foo
    20:     *(u64 *)(r2 + 0x0) = r1
    21:     r1 = 0x1
            a8:  CO-RE <type_matches> [2] struct foo
    22:     *(u64 *)(r2 + 0x0) = r1
    23:     r1 = 0x2 ll
            b8:  CO-RE <local_type_id> [2] struct foo
    25:     *(u64 *)(r2 + 0x0) = r1
    26:     r1 = 0x2 ll
            d0:  CO-RE <target_type_id> [2] struct foo
    28:     *(u64 *)(r2 + 0x0) = r1
    29:     exit

基于枚举的重定位：

.. code-block:: c

  void delta(struct foo *s, volatile unsigned long *g) {
    *g = __builtin_preserve_enum_value(*(enum bar *)U, 0 /* enum literal existence */);
    *g = __builtin_preserve_enum_value(*(enum bar *)V, 1 /* enum literal value */);
  }

  f0 <delta>:
    30:     r1 = 0x1 ll
            f0:  CO-RE <enumval_exists> [16] enum bar::U = 0
    32:     *(u64 *)(r2 + 0x0) = r1
    33:     r1 = 0x1 ll
            108:  CO-RE <enumval_value> [16] enum bar::V = 1
    35:     *(u64 *)(r2 + 0x0) = r1
    36:     exit
