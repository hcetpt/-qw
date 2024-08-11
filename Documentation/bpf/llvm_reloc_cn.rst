此文档描述了LLVM BPF后端的重定位类型。
重定位记录
=============

LLVM BPF后端使用以下16字节的ELF结构来记录每个重定位::

  typedef struct
  {
    Elf64_Addr    r_offset;  // 从节开始的偏移量
    Elf64_Xword   r_info;    // 重定位类型和符号索引
  } Elf64_Rel;

例如，对于以下代码::

  int g1 __attribute__((section("sec")));
  int g2 __attribute__((section("sec")));
  static volatile int l1 __attribute__((section("sec")));
  static volatile int l2 __attribute__((section("sec")));
  int test() {
    return g1 + g2 + l1 + l2;
  }

使用``clang --target=bpf -O2 -c test.c``编译后，以下是通过``llvm-objdump -dr test.o``得到的代码::

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

上述内容中有四个重定位，对应四个`LD_imm64`指令。
下面的``llvm-readelf -r test.o``显示了这四个重定位的二进制值::

  Relocation section '.rel.text' at offset 0x190 contains 4 entries:
      Offset             Info             Type               Symbol's Value  Symbol's Name
  0000000000000000  0000000600000001 R_BPF_64_64            0000000000000000 g1
  0000000000000018  0000000700000001 R_BPF_64_64            0000000000000004 g2
  0000000000000038  0000000400000001 R_BPF_64_64            0000000000000000 sec
  0000000000000058  0000000400000001 R_BPF_64_64            0000000000000000 sec

每个重定位由“Offset”（8字节）和“Info”（8字节）表示。
例如，第一个重定位对应第一条指令（Offset 0x0），相应的“Info”指示“R_BPF_64_64”的重定位类型（类型1）以及符号表中的条目（条目6）。
下面是通过``llvm-readelf -s test.o``得到的符号表::

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

第6个条目是全局变量`g1`，其值为0。
同样地，第二个重定位位于``.text``偏移量``0x18``处，即指令3，类型为``R_BPF_64_64``，并指向符号表中的第7个条目。
第二个重定位解析为全局变量`g2`，该变量具有符号值4。符号值表示全局变量`g2`初始值在`.data`节开始处的偏移量。
第三个和第四个重定位引用静态变量`l1`和`l2`。从上面的``.rel.text``节中无法清楚地看出它们真正引用的是哪些符号，因为它们都引用符号表中的第4个条目，即符号`sec`，它具有`STT_SECTION`类型，代表一个节。因此，对于静态变量或函数，节的偏移量被写入原始指令缓冲区，称为“A”（加数）。查看上面的指令``7``和``11``，它们有节偏移量``8``和``12``。
从符号表中，我们可以找到它们分别对应于条目“2”和“3”，即`l1`和`l2`。
通常情况下，“A”对于全局变量和函数是0，而对于静态变量/函数则是段偏移或基于段偏移的一些计算结果。非段偏移的情况指的是函数调用。下面将提供更多细节。

不同的重定位类型
==================

支持六种重定位类型。以下是概述，并且`S`代表符号表中的符号值：

  * 枚举  ELF 重定位类型     描述      位大小  偏移量        计算方法
  * 0     R_BPF_NONE         无
  * 1     R_BPF_64_64        ld_imm64 指令   32       r_offset + 4  S + A
  * 2     R_BPF_64_ABS64     正常数据      64       r_offset      S + A
  * 3     R_BPF_64_ABS32     正常数据      32       r_offset      S + A
  * 4     R_BPF_64_NODYLD32  .BTF[.ext] 数据  32       r_offset      S + A
  * 10    R_BPF_64_32        调用指令      32       r_offset + 4  (S + A) / 8 - 1

例如，`R_BPF_64_64` 重定位类型用于`ld_imm64`指令。实际要重定位的数据（0 或段偏移）存储在`r_offset + 4`处，读写数据的位大小为32（4字节）。可以通过符号值加上隐式加数来解析重定位。需要注意的是，“位大小”为32意味着段偏移必须小于等于`UINT32_MAX`，这由LLVM BPF后端强制执行。
另一种情况是，`R_BPF_64_ABS64` 重定位类型用于正常的64位数据。实际要重定位的数据存储在`r_offset`处，读写数据的位大小为64（8字节）。同样可以通过符号值加上隐式加数来解析重定位。
`R_BPF_64_ABS32` 和 `R_BPF_64_NODYLD32` 类型都是用于32位数据，但`R_BPF_64_NODYLD32`特别指在`.BTF`和`.BTF.ext`段中的重定位。对于像bcc这样的情况，如果使用了LLVM的`ExecutionEngine RuntimeDyld`，那么`R_BPF_64_NODYLD32`类型的重定位不应该解析为实际的函数/变量地址。否则，`.BTF`和`.BTF.ext`将无法被bcc和内核使用。
类型`R_BPF_64_32`用于调用指令。调用目标的段偏移存储在`r_offset + 4`（32位），计算公式为`(S + A) / 8 - 1`。

示例
=====

`R_BPF_64_64` 和 `R_BPF_64_32` 两种类型用于解析`ld_imm64`和`call`指令。例如：

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

使用`clang --target=bpf -O2 -c test.c`编译后，使用`llvm-objdump -dr test.o`将得到以下代码：

```plaintext
.text段的反汇编结果：

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

sec1段的反汇编结果：

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
第二个重定位对应于 ``lfunc(a, b)``，其中 ``lfunc`` 的段偏移为 ``0x18``，因此 “call” 指令的偏移量为 ``(0 + 0x18)/8 - 1 = 2``。
第三个重定位对应于 ``global`` 的 ld_imm64，其具有一个段偏移 ``0``。
下面是一个示例，说明如何生成 R_BPF_64_ABS64 ：

  int global() { return 0; }
  struct t { void *g; } gbl = { global };

使用 ``clang --target=bpf -O2 -g -c test.c`` 编译后，我们可以通过命令 ``llvm-readelf -r test.o`` 在 ``.data`` 段中看到以下重定位：

  重定位段 '.rel.data' 在偏移量 0x458 处包含 1 个条目：
      偏移量             Info             类型               符号值    符号名
  0000000000000000  0000000700000002 R_BPF_64_ABS64         0000000000000000 global

该重定位表示 ``.data`` 段的前 8 字节应该被填充以 ``global`` 变量的地址。
通过 ``llvm-readelf`` 输出，我们可以看到 dwarf 段中有一系列的 ``R_BPF_64_ABS32`` 和 ``R_BPF_64_ABS64`` 重定位：

  重定位段 '.rel.debug_info' 在偏移量 0x468 处包含 13 个条目：
      偏移量             Info             类型               符号值    符号名
  0000000000000006  0000000300000003 R_BPF_64_ABS32         0000000000000000 .debug_abbrev
  000000000000000c  0000000400000003 R_BPF_64_ABS32         0000000000000000 .debug_str
  0000000000000012  0000000400000003 R_BPF_64_ABS32         0000000000000000 .debug_str
  0000000000000016  0000000600000003 R_BPF_64_ABS32         0000000000000000 .debug_line
  000000000000001a  0000000400000003 R_BPF_64_ABS32         0000000000000000 .debug_str
  000000000000001e  0000000200000002 R_BPF_64_ABS64         0000000000000000 .text
  000000000000002b  0000000400000003 R_BPF_64_ABS32         0000000000000000 .debug_str
  0000000000000037  0000000800000002 R_BPF_64_ABS64         0000000000000000 gbl
  0000000000000040  0000000400000003 R_BPF_64_ABS32         0000000000000000 .debug_str
  .....
`.BTF/.BTF.ext` 段中有 `R_BPF_64_NODYLD32` 重定位：

  重定位段 '.rel.BTF' 在偏移量 0x538 处包含 1 个条目：
      偏移量             Info             类型               符号值    符号名
  0000000000000084  0000000800000004 R_BPF_64_NODYLD32      0000000000000000 gbl

  重定位段 '.rel.BTF.ext' 在偏移量 0x548 处包含 2 个条目：
      偏移量             Info             类型               符号值    符号名
  000000000000002c  0000000200000004 R_BPF_64_NODYLD32      0000000000000000 .text
  0000000000000040  0000000200000004 R_BPF_64_NODYLD32      0000000000000000 .text

.. _btf-co-re-relocations:

=================
CO-RE 重定位
=================

从对象文件的角度来看，CO-RE 机制是通过一组特定于 CO-RE 的重定位记录实现的。这些重定位记录与 ELF 重定位无关，并且在 `.BTF.ext` 段中编码。有关 `.BTF.ext` 结构的更多信息，请参阅 :ref:`Documentation/bpf/btf.rst <BTF_Ext_Section>`。
CO-RE 重定位应用于 BPF 指令，以便在加载时用与目标内核相关的信息更新指令中的立即数或偏移字段。
要修补的字段根据指令类别选择：

* 对于 BPF_ALU、BPF_ALU64、BPF_LD，修补 `immediate` 字段；
* 对于 BPF_LDX、BPF_STX、BPF_ST，修补 `offset` 字段；
* BPF_JMP、BPF_JMP32 指令 **不应** 被修补
重定位类型
=================

有几种类型的 CO-RE 重定位可以分为三组：

* 基于字段的 - 使用与字段相关的数据来修补指令，例如更改 BPF_LDX 指令的偏移字段以反映目标内核中特定结构字段的偏移量
* 基于类型的 - 与类型相关信息一起的补丁指令，例如：
  将 BPF_ALU 移动指令的立即数字段更改为 0 或 1 以反映目标内核中是否存在特定类型。
* 基于枚举的 - 与枚举相关信息一起的补丁指令，例如：
  更改 BPF_LD_IMM64 指令的立即数字段以反映目标内核中特定枚举字面值的值。

所有重定位种类由以下枚举表示：

.. code-block:: c

  enum bpf_core_relo_kind {
      BPF_CORE_FIELD_BYTE_OFFSET = 0,  /* 字段的字节偏移量 */
      BPF_CORE_FIELD_BYTE_SIZE   = 1,  /* 字段的字节数 */
      BPF_CORE_FIELD_EXISTS      = 2,  /* 目标内核中的字段存在性 */
      BPF_CORE_FIELD_SIGNED      = 3,  /* 字段的符号性（0 - 无符号，1 - 有符号） */
      BPF_CORE_FIELD_LSHIFT_U64  = 4,  /* 位字段特性的左移位 */
      BPF_CORE_FIELD_RSHIFT_U64  = 5,  /* 位字段特性的右移位 */
      BPF_CORE_TYPE_ID_LOCAL     = 6,  /* 本地 BPF 对象中的类型ID */
      BPF_CORE_TYPE_ID_TARGET    = 7,  /* 目标内核中的类型ID */
      BPF_CORE_TYPE_EXISTS       = 8,  /* 目标内核中的类型存在性 */
      BPF_CORE_TYPE_SIZE         = 9,  /* 类型的字节数 */
      BPF_CORE_ENUMVAL_EXISTS    = 10, /* 枚举值在目标内核中的存在性 */
      BPF_CORE_ENUMVAL_VALUE     = 11, /* 枚举值的整数值 */
      BPF_CORE_TYPE_MATCHES      = 12, /* 目标内核中的类型匹配 */
  };

注释：

* ``BPF_CORE_FIELD_LSHIFT_U64`` 和 ``BPF_CORE_FIELD_RSHIFT_U64`` 的用途是用于读取位字段值，使用如下算法：

  .. code-block:: c

     // 从结构体 ``s`` 中读取位字段 ``f``
     is_signed = relo(s->f, BPF_CORE_FIELD_SIGNED)
     off = relo(s->f, BPF_CORE_FIELD_BYTE_OFFSET)
     sz  = relo(s->f, BPF_CORE_FIELD_BYTE_SIZE)
     l   = relo(s->f, BPF_CORE_FIELD_LSHIFT_U64)
     r   = relo(s->f, BPF_CORE_FIELD_RSHIFT_U64)
     // 定义 ``v`` 为大小为 ``sz`` 的有符号或无符号整数
     v = *({s|u}<sz> *)((void *)s + off)
     v <<= l
     v >>= r

* ``BPF_CORE_TYPE_MATCHES`` 查询的是匹配关系，定义如下：

  * 对于整数：如果大小和符号性匹配，则类型匹配；
  * 对于数组和指针：目标类型递归地匹配；
  * 对于结构体和联合体：

    * 本地成员需要在目标中存在，并且具有相同的名称；

    * 对于每个成员，我们递归检查匹配情况，除非它已经位于指针之后，在这种情况下，我们只检查匹配的名称和兼容的类型；

  * 对于枚举：

    * 本地变体必须通过符号名称在目标中找到匹配（但不是数字值）；

    * 大小必须匹配（但枚举可以匹配 enum64 反之亦然）；

  * 对于函数指针：

    * 本地类型中的参数数量和位置必须与目标匹配；
    * 对于每个参数和返回值，我们递归检查匹配情况。

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

* ``insn_off`` - 该重定位所在代码段内的指令偏移量（以字节计）；
* ``type_id`` - 可重定位类型或字段的“根”（包含）实体的 BTF 类型ID；
* ``access_str_off`` - 对应的 .BTF 字符串段中的偏移量；

字符串解释取决于具体的重定位类型：

  * 对于基于字段的重定位，字符串用一系列字段和数组索引（以冒号 : 分隔）来编码访问的字段。这在概念上非常接近 LLVM 的 `getelementptr <GEP_>`_ 指令的参数，用于标识到字段的偏移。考虑以下 C 代码为例：

    .. code-block:: c

       struct sample {
           int a;
           int b;
           struct { int c[10]; };
       } __attribute__((preserve_access_index));
       struct sample *s;

    * 访问 ``s[0].a`` 将被编码为 ``0:0``：

      * ``0``: ``s`` 的第一个元素（如同 ``s`` 是一个数组）；
      * ``0``: 在 ``struct sample`` 中字段 ``a`` 的索引；
* 访问 ``s->a`` 也将被编码为 ``0:0``；
* 访问 ``s->b`` 将被编码为 ``0:1``：

      * ``0``: ``s`` 的第一个元素；
      * ``1``: 在 ``struct sample`` 中字段 ``b`` 的索引；
* 访问 ``s[1].c[5]`` 将被编码为 ``1:2:0:5``：

      * ``1``: ``s`` 的第二个元素；
      * ``2``: 在 ``struct sample`` 中匿名结构字段的索引；
      * ``0``: 匿名结构中字段 ``c`` 的索引；
      * ``5``: 访问数组元素 #5。
对于基于类型的重定位，`string` 预期仅是 "0"；

对于基于枚举值的重定位，`string` 包含该枚举值在其枚举类型中的索引；

* `kind` - `enum bpf_core_relo_kind` 中的一种
.. _GEP: https://llvm.org/docs/LangRef.html#getelementptr-instruction

.. _btf_co_re_relocation_examples:

CO-RE 重定位示例
=========================

对于以下 C 代码：

.. code-block:: c

 struct foo {
   int a;
   int b;
   unsigned c:15;
 } __attribute__((preserve_access_index));

 enum bar { U, V };

以及以下 BTF 定义：

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

当使用 `__attribute__((preserve_access_index))` 时，字段偏移量重定位会自动生成，例如：

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

所有类型的重定位都可通过内置函数请求。
例如基于字段的重定位：

.. code-block:: c

  void bravo(struct foo *s, volatile unsigned long *g) {
    *g = __builtin_preserve_field_info(s->b, 0 /* 字段字节偏移 */);
    *g = __builtin_preserve_field_info(s->b, 1 /* 字段字节大小 */);
    *g = __builtin_preserve_field_info(s->b, 2 /* 字段存在性 */);
    *g = __builtin_preserve_field_info(s->b, 3 /* 字段符号性 */);
    *g = __builtin_preserve_field_info(s->c, 4 /* 位域左移 */);
    *g = __builtin_preserve_field_info(s->c, 5 /* 位域右移 */);
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
    *g = __builtin_preserve_type_info(*s, 0 /* 类型存在性 */);
    *g = __builtin_preserve_type_info(*s, 1 /* 类型大小 */);
    *g = __builtin_preserve_type_info(*s, 2 /* 类型匹配 */);
    *g = __builtin_btf_type_id(*s, 0 /* 在此目标文件中的类型ID */);
    *g = __builtin_btf_type_id(*s, 1 /* 在目标内核中的类型ID */);
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
    *g = __builtin_preserve_enum_value(*(enum bar *)U, 0 /* 枚举字面量存在性 */);
    *g = __builtin_preserve_enum_value(*(enum bar *)V, 1 /* 枚举字面量值 */);
  }

  f0 <delta>:
    30:     r1 = 0x1 ll
            f0:  CO-RE <enumval_exists> [16] enum bar::U = 0
    32:     *(u64 *)(r2 + 0x0) = r1
    33:     r1 = 0x1 ll
            108:  CO-RE <enumval_value> [16] enum bar::V = 1
    35:     *(u64 *)(r2 + 0x0) = r1
    36:     exit
