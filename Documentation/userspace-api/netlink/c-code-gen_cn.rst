SPDX 许可证标识符: BSD-3-Clause

==============================
Netlink 规格生成 C 代码
==============================

本文档描述了如何使用 Netlink 规格来生成 C 代码（例如 uAPI、策略等）。同时，它还定义了在旧版本族中由 `genetlink-c` 协议级别允许的附加属性，以控制命名。为了简洁起见，本文档通过对象类型来引用各种对象的 `name` 属性。例如，`$attr` 表示属性中的 `name` 的值，而 `$family` 是族的名称（全局 `name` 属性）。
大写字母用于表示字面量值，例如 `$family-CMD` 意味着 `$family`、一个连字符字符以及字面量 `CMD` 的连接。
`#define` 和枚举值的名称总是转换为大写，并将连字符（`-`）替换为下划线（`_`）。
如果构造的名称是一个 C 关键字，则会追加一个额外的下划线（`do` -> `do_`）。

全局变量
=======

`c-family-name` 控制家族名称的 `#define` 名称，默认是 `$family-FAMILY-NAME`。
`c-version-name` 控制家族版本的 `#define` 名称，默认是 `$family-FAMILY-VERSION`。
`max-by-define` 选择是否将枚举的最大值定义为 `#define` 而不是在枚举内部定义。

定义
===

常量
----

每个常量都会被渲染为一个 `#define`。
常量的名称是 `$family-$constant`，其值根据规格中的类型被渲染为字符串或整数。
枚举与标志
------------

枚举命名为 ``$family-$enum``。可以通过直接设置或通过指定 ``enum-name`` 属性来省略完整名称。
默认的条目名称为 ``$family-$enum-$entry``。
如果指定了 ``name-prefix``，则会替换条目名称中的 ``$family-$enum`` 部分。
布尔值 ``render-max`` 控制最大值的创建（这些值默认对于属性枚举是启用的）。

属性
=====

每个属性集（不包括分数集）都会被渲染为一个枚举。
在 netlink 头文件中，属性枚举传统上是无名的。
如果需要命名，可以使用 ``enum-name`` 来指定名称。
如果集合名称与家族名称相同，默认的属性名称前缀为 ``$family-A``；如果不同，则为 ``$family-A-$set``。可以通过集合的 ``name-prefix`` 属性覆盖这个前缀。
以下部分将前缀称为 ``$pfx``。
属性命名为 ``$pfx-$attribute``。
属性枚举以两个特殊值 `__$pfx-MAX` 和 `$pfx-MAX` 结尾，这些值用于属性表的大小设置。
这两个名称可以直接通过 `attr-cnt-name` 和 `attr-max-name` 属性指定。
如果在全局级别将 `max-by-define` 设置为 `true`，则 `attr-max-name` 将被指定为 `#define` 而不是一个枚举值。

操作
====

操作命名为 `$family-CMD-$operation`。
如果指定了 `name-prefix`，它将替换名称中的 `$family-CMD` 部分。
与属性枚举类似，操作枚举也以特殊的计数和最大属性结尾。对于操作，可以通过 `cmd-cnt-name` 和 `cmd-max-name` 重命名这些属性。如果 `max-by-define` 为 `true`，最大值将是一个 `#define`。

多播组
======

每个多播组都会生成一个定义，并被渲染到内核 uAPI 头文件中。
该定义的名称为 `$family-MCGRP-$group`，可以通过 `c-define-name` 属性覆盖。

代码生成
=======

默认情况下，假设 uAPI 头文件来自默认头文件搜索路径中的 `<linux/$family.h>`。
可以使用全局属性 `uapi-header` 来更改这一点。
