SPDX 许可证标识符: BSD-3-Clause

=================================================================
对传统 Generic Netlink 家族的 Netlink 规格支持
=================================================================

本文档描述了描述较旧的 Generic Netlink 家族所需的许多额外特性和属性，这些家族构成了 "genetlink-legacy" 协议级别的规范。

规范
=============

全局
-------

在规范文件根级别直接列出的属性
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

版本
~~~~~~~

Generic Netlink 家族版本，默认为 1。
`version` 历史上用于引入可能导致向后兼容性中断的家族更改。由于通常不允许破坏兼容性的更改，因此 `version` 很少使用。

属性类型嵌套
--------------------

新的 Netlink 家族应使用 `multi-attr` 来定义数组。
较旧的家族（如 `genetlink` 控制家族）尝试通过重用属性类型来携带信息以定义数组类型。
作为参考，`multi-attr` 数组可能如下所示：

```
[ARRAY-ATTR]
  [INDEX （可选地）]
  [MEMBER1]
  [MEMBER2]
[SOME-OTHER-ATTR]
[ARRAY-ATTR]
  [INDEX （可选地）]
  [MEMBER1]
  [MEMBER2]
```

其中 `ARRAY-ATTR` 是数组条目的类型。

索引数组
~~~~~~~~~~~~~

`indexed-array` 将整个数组包装在一个额外的属性中（从而限制其大小为 64kB）。`ENTRY` 的嵌套是特殊的，其类型是条目的索引而不是常规的属性类型。
需要一个 `sub-type` 来描述 `ENTRY` 中的类型。如果 `sub-type` 是 `nest`，则意味着 `ENTRY` 中有嵌套数组，结构如下：

```
[SOME-OTHER-ATTR]
[ARRAY-ATTR]
  [ENTRY]
    [MEMBER1]
    [MEMBER2]
  [ENTRY]
    [MEMBER1]
    [MEMBER2]
```

其他类型的 `sub-type` 如 `u32` 表示 `ENTRY` 中只有一个成员，并且该成员由 `sub-type` 描述。结构如下：

```
[SOME-OTHER-ATTR]
[ARRAY-ATTR]
  [ENTRY u32]
  [ENTRY u32]
```

类型值
~~~~~~~~~~

`type-value` 是一种构造，使用属性类型来携带有关单个对象的信息（通常在数组逐项转储时使用）。
`type-value` 可以有多层嵌套，例如 genetlink 的策略转储会创建以下结构：

```
[POLICY-IDX]
  [ATTR-IDX]
    [POLICY-INFO-ATTR1]
    [POLICY-INFO-ATTR2]
```

其中第一级嵌套的属性类型是策略索引，它包含一个具有属性索引类型的单个嵌套。在 attr-index 嵌套内部是策略属性。现代 Netlink 家族应该定义为一个扁平结构，这里的嵌套没有任何实际用途。
操作
==========

枚举（消息ID）模型
-----------------------

统一模型
~~~~~~~

现代家庭使用“统一”消息ID模型，该模型为家族内的所有消息使用单一的枚举。请求和响应共享同一个消息ID。通知则从同一空间中分配独立的ID。例如，给定以下操作列表：

```yaml
-
  name: a
  value: 1
  do: ..
-
  name: b
  do: ..
-
  name: c
  value: 4
  notify: a
-
  name: d
  do: ..
```

操作`a`的请求和响应将具有ID 1，操作`b`的请求和响应将是ID 2（由于没有显式指定`value`，因此它是前一个操作`+ 1`）。通知`c`将使用ID 4，操作`d`将使用ID 5等。

方向模型
~~~~~~~~~~~

“方向”模型根据消息的方向来划分ID的分配。内核发出和接收的消息不会混淆，因此这节省了ID空间（代价是编程变得更加繁琐）。在这种情况下，应在操作的`request`和`reply`部分中指定`value`属性（如果操作同时包含`do`和`dump`，则ID共享，`value`应设置在`do`中）。对于通知，在操作级别提供`value`，但它仅分配一个“来自内核”的ID。让我们来看一个例子：

```yaml
-
  name: a
  do:
    request:
      value: 2
      attributes: ..
  reply:
      value: 1
      attributes: ..
-
  name: b
  notify: a
-
  name: c
  notify: a
  value: 7
-
  name: d
  do: ..
```

在这种情况下，`a`在向内核发送消息时将使用2，并期望接收到ID为1的消息作为响应。通知`b`分配了一个“来自内核”的ID，即2。`c`分配了一个“来自内核”的ID为7。
如果操作 ``d`` 在规范中没有显式设置 ``values``，则请求部分将被分配为 3（``a`` 是带有请求部分且值为 2 的前一个操作），响应部分将被分配为 8（``c`` 是“from-kernel”方向上的前一个操作）。

其他注意事项
=============

结构体
-------

遗留家族可以定义 C 结构体，既可以用作属性的内容，也可以用作固定的消息头。结构体在 ``definitions`` 中定义，并在操作或属性成员中引用。

成员
~~~~~~~

- ``name`` - 结构体成员的属性名称
- ``type`` - 标量类型之一：``u8``、``u16``、``u32``、``u64``、``s8``、``s16``、``s32``、``s64``、``string``、``binary`` 或 ``bitfield32``
- ``byte-order`` - ``big-endian`` 或 ``little-endian``
- ``doc``、``enum``、``enum-as-flags``、``display-hint`` - 与 :ref:`属性定义 <attribute_properties>` 相同

请注意，YAML 中定义的结构体根据 C 规范隐式地进行打包。例如，以下结构体是 4 字节，而不是 6 字节：

.. code-block:: c

  struct {
          u8 a;
          u16 b;
          u8 c;
  }

任何填充必须显式添加，并且 C 类语言应从成员是否自然对齐来推断显式填充的需求。以下是上面的结构体定义，在 YAML 中声明：

.. code-block:: yaml

  definitions:
    -
      name: message-header
      type: struct
      members:
        -
          name: a
          type: u8
        -
          name: b
          type: u16
        -
          name: c
          type: u8

固定头
~~~~~~~~~~~~~

可以使用 ``fixed-header`` 向操作添加固定消息头。默认的 ``fixed-header`` 可以在 ``operations`` 中设置，并且可以为每个操作设置或覆盖。
.. code-block:: yaml

  operations:
    fixed-header: message-header
    list:
      -
        name: get
        fixed-header: custom-header
        attribute-set: message-attrs

属性
~~~~~~~~~~

可以通过使用具有结构体定义名称的 ``struct`` 属性将 ``binary`` 属性解释为 C 结构体。``struct`` 属性隐含了 ``sub-type: struct``，因此不需要指定子类型。
.. code-block:: yaml

  attribute-sets:
    -
      name: stats-attrs
      attributes:
        -
          name: stats
          type: binary
          struct: vport-stats

C 数组
--------

遗留家族还使用 ``binary`` 属性来封装 C 数组。使用 ``sub-type`` 来标识要提取的标量类型。
.. code-block:: yaml

  attributes:
    -
      name: ports
      type: binary
      sub-type: u32

多消息 DO
------------

新的 Netlink 家族不应使用带有 ``NLM_F_MULTI`` 标志的多个回复响应 DO 操作。请改用过滤后的转储。
在规范级别，我们可以在 ``do`` 中定义一个 ``dumps`` 属性，其值可能为 ``combine`` 和 ``multi-object``，具体取决于解析方式（解析为单个回复 vs 对象列表，即基本上是一个转储）。
当然，请提供你需要翻译的文本。
