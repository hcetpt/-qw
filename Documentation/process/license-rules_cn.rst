SPDX许可证标识符: GPL-2.0

.. _kernel_licensing:

Linux 内核许可规则
============================

Linux 内核依据 GNU 通用公共许可证版本 2（GPL-2.0）的条款提供，具体内容见 `LICENSES/preferred/GPL-2.0` 文件，并在 `LICENSES/exceptions/Linux-syscall-note` 文件中明确描述了系统调用例外。这些信息在 `COPYING` 文件中有详细说明。此文档文件提供了如何注释每个源文件以使其许可证清晰且明确的说明。它并不取代内核的许可证。`COPYING` 文件中描述的许可证适用于整个内核源代码，尽管单个源文件可以具有不同的许可证，但必须与 GPL-2.0 兼容：

```
GPL-1.0+  :  GNU 通用公共许可证 v1.0 或更高版本
GPL-2.0+  :  GNU 通用公共许可证 v2.0 或更高版本
LGPL-2.0  :  GNU 库通用公共许可证 v2 仅限
LGPL-2.0+ :  GNU 库通用公共许可证 v2 或更高版本
LGPL-2.1  :  GNU 较小通用公共许可证 v2.1 仅限
LGPL-2.1+ :  GNU 较小通用公共许可证 v2.1 或更高版本
```

除此之外，单个文件可以在双重许可下提供，例如，其中一个兼容的 GPL 变体以及另一个许可，如 BSD、MIT 等。用户空间 API（UAPI）头文件，它们描述了用户空间程序与内核之间的接口，是一个特殊情况。根据内核 `COPYING` 文件中的说明，系统调用接口是一个明确的界限，不会将 GPL 要求扩展到使用该接口与内核通信的任何软件。因为 UAPI 头文件必须包含在创建运行在 Linux 内核上的可执行文件的所有源文件中，因此需要通过特殊许可表达来记录这一例外。

表示源文件许可的常见方式是在文件顶部注释中添加相应的模板文本。由于格式化、拼写错误等原因，这些“模板”对于用于许可合规性检查的工具来说难以验证。

替代模板文本的一种方法是使用每个源文件中的软件包数据交换（SPDX）许可标识符。SPDX 许可标识符是机器可解析的、精确的许可简写，表示文件内容的贡献许可。SPDX 许可标识符由 Linux 基金会下的 SPDX 工作组管理，并得到了行业合作伙伴、工具供应商和法律团队的一致同意。更多信息请参见 https://spdx.org/

Linux 内核要求所有源文件都使用精确的 SPDX 标识符。内核中使用的有效标识符在 `License identifiers`_ 部分中解释，并从官方 SPDX 许可列表 https://spdx.org/licenses/ 中获取，包括许可证文本。

许可标识符语法
-------------------------

1. 放置位置：

   内核文件中的 SPDX 许可标识符应添加在文件中可以包含注释的第一行。对于大多数文件，这是第一行，除非脚本需要在第一行放置 `#!PATH_TO_INTERPRETER`。对于这些脚本，SPDX 标识符应放在第二行。

2. 样式：

   SPDX 许可标识符以注释的形式添加。注释样式取决于文件类型：
   
   ```
   C 源码： // SPDX-License-Identifier: <SPDX License Expression>
   C 头文件： /* SPDX-License-Identifier: <SPDX License Expression> */
   汇编：   /* SPDX-License-Identifier: <SPDX License Expression> */
   脚本：   # SPDX-License-Identifier: <SPDX License Expression>
   .rst：   .. SPDX-License-Identifier: <SPDX License Expression>
   .dts{i}： // SPDX-License-Identifier: <SPDX License Expression>
   ```

   如果某个特定工具无法处理标准注释样式，则应使用该工具接受的适当注释机制。这就是为什么在 C 头文件中使用 `/* */` 样式的注释。在生成的 `.lds` 文件中曾观察到构建中断问题，其中 `ld` 无法解析 C++ 注释。现在这个问题已经修复，但仍有一些较旧的汇编工具无法处理 C++ 风格的注释。
3. 语法：

   一个<SPDX 许可表达式>要么是SPDX许可列表上的SPDX简短形式许可标识符，要么是在许可例外适用时由“WITH”分隔的两个SPDX简短形式许可标识符。当有多个许可适用时，表达式由关键字“AND”、“OR”分隔的子表达式组成，并被“（）”包围。
   具有“或更高版本”选项的[L]GPL等许可的标识符通过使用“+”来表示该选项。

      // SPDX-License-Identifier: GPL-2.0+
      // SPDX-License-Identifier: LGPL-2.1+

   当需要对许可进行修改时应使用WITH。
   例如，Linux内核UAPI文件使用的表达式为：

      // SPDX-License-Identifier: GPL-2.0 WITH Linux-syscall-note
      // SPDX-License-Identifier: GPL-2.0+ WITH Linux-syscall-note

   内核中使用WITH例外的其他示例：

      // SPDX-License-Identifier: GPL-2.0 WITH mif-exception
      // SPDX-License-Identifier: GPL-2.0+ WITH GCC-exception-2.0

   例外只能与特定的许可标识符一起使用。有效的许可标识符列在例外文本文件的标签中。详细信息请参见“许可标识符”章中的“例外”部分。
   如果文件具有双重许可并且仅选择一个许可，则应使用OR。
   例如，某些dtsi文件具有双重许可：

      // SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause

   内核中双许可文件的许可表达式示例：

      // SPDX-License-Identifier: GPL-2.0 OR MIT
      // SPDX-License-Identifier: GPL-2.0 OR BSD-2-Clause
      // SPDX-License-Identifier: GPL-2.0 OR Apache-2.0
      // SPDX-License-Identifier: GPL-2.0 OR MPL-1.1
      // SPDX-License-Identifier: (GPL-2.0 WITH Linux-syscall-note) OR MIT
      // SPDX-License-Identifier: GPL-1.0+ OR BSD-3-Clause OR OpenSSL

   如果文件具有多个其所有条款均适用于使用该文件的许可，则应使用AND。
   例如，如果代码是从另一个项目继承来的，并且已获得将其放入内核的许可，但原始许可条款需要保持有效：

      // SPDX-License-Identifier: (GPL-2.0 WITH Linux-syscall-note) AND MIT

   另一个需要遵守两组许可条款的示例为：

      // SPDX-License-Identifier: GPL-1.0+ AND LGPL-2.1+

许可标识符
--------------

目前使用的以及添加到内核的代码所用的许可可以分为：

1. _`首选许可`：

   尽可能使用这些许可，因为它们是完全兼容且广泛使用的。这些许可可以从目录获取：

      LICENSES/preferred/

   在内核源码树中
   该目录中的文件包含完整的许可文本和`元标签`_。文件名与应在源文件中使用的SPDX许可标识符相同。
   示例：

      LICENSES/preferred/GPL-2.0

   包含GPL版本2的许可文本和所需的元标签：

      LICENSES/preferred/MIT

   包含MIT许可文本和所需的元标签

   _`元标签`：

   许可文件中必须包含以下元标签：

   - Valid-License-Identifier:

     声明哪些许可标识符在项目中有效以引用此特定许可文本的一行或多行。通常这是一个有效的标识符，但对于具有“或更高版本”选项的许可，有两个有效的标识符。
- SPDX-URL:

     包含与许可相关附加信息的SPDX页面的URL
- Usage-Guidance:

     自由格式的使用建议。文本必须包括根据`许可标识符语法`_指南放置到源文件中的SPDX许可标识符的正确示例
- License-Text:

     此标签之后的所有文本被视为原始许可文本

   文件格式示例：

      Valid-License-Identifier: GPL-2.0
      Valid-License-Identifier: GPL-2.0+
      SPDX-URL: https://spdx.org/licenses/GPL-2.0.html
      Usage-Guide:
        要在源代码中使用此许可，请根据许可规则文档中的放置指南将以下SPDX标签/值对之一放在注释中
对于“GNU通用公共许可（GPL）版本2”使用：
	  SPDX-License-Identifier: GPL-2.0
对于“GNU通用公共许可（GPL）版本2或任何更高版本”使用：
	  SPDX-License-Identifier: GPL-2.0+
      License-Text:
        完整的许可文本

   ::

      SPDX-License-Identifier: MIT
      SPDX-URL: https://spdx.org/licenses/MIT.html
      Usage-Guide:
	要在源代码中使用此许可，请根据许可规则文档中的放置指南将以下SPDX标签/值对放在注释中
### 许可证标识符和许可证文本：

```
SPDX-License-Identifier: MIT
License-Text:
    完整的许可证文本
```

---

### 已弃用的许可证：

这些许可证仅应用于现有代码或从其他项目导入代码。这些许可证可以从内核源码树中的目录获取：

```
LICENSES/deprecated/
```

此目录中的文件包含完整的许可证文本和`元标签`。文件名与SPDX许可证标识符相同，该标识符应在源文件中使用。

示例：

```
LICENSES/deprecated/ISC
```

包含Internet Systems Consortium许可证文本和所需的元标签：

```
LICENSES/deprecated/GPL-1.0
```

包含GPL版本1许可证文本和所需的元标签。

#### 元标签：

“其他”许可证的元标签要求与“首选许可证”的要求相同。

#### 文件格式示例：

```
Valid-License-Identifier: ISC
SPDX-URL: https://spdx.org/licenses/ISC.html
Usage-Guide:
    在内核中新代码中不鼓励使用此许可证，而应仅用于从已有项目导入代码
```

要在源代码中使用此许可证，请根据许可规则文档中的放置指南，在注释中添加以下SPDX标签/值对：

```
SPDX-License-Identifier: ISC
License-Text:
    完整的许可证文本
```

---

### 双重许可仅适用：

这些许可证仅用于在首选许可证之外与其他许可证一起双重授权代码。这些许可证可以从内核源码树中的目录获取：

```
LICENSES/dual/
```

此目录中的文件包含完整的许可证文本和`元标签`。文件名与SPDX许可证标识符相同，该标识符应在源文件中使用。

示例：

```
LICENSES/dual/MPL-1.1
```

包含Mozilla Public License版本1.1许可证文本和所需的元标签：

```
LICENSES/dual/Apache-2.0
```

包含Apache License版本2.0许可证文本和所需的元标签。

#### 元标签：

“其他”许可证的元标签要求与“首选许可证”的要求相同。
文件格式示例：

```
有效许可标识符: MPL-1.1
SPDX-URL: https://spdx.org/licenses/MPL-1.1.html
使用指南:
    不要使用。MPL-1.1 不与 GPL2 兼容。它只能用于双许可证文件，其中另一个许可证与 GPL2 兼容。
如果您最终使用了此许可证，则必须与一个与 GPL2 兼容的许可证一起使用 "OR"。
要使用 Mozilla Public License 版本 1.1，请根据许可证规则文档中的放置指南，在注释中添加以下 SPDX 标签/值对：
SPDX-License-Identifier: MPL-1.1
许可证文本:
    完整的许可证文本

|

4. _`例外`:

   某些许可证可以通过例外来增加某些权利，而这些权利是原始许可证所不具备的。这些例外可以从目录获取：
   
   LICENSES/exceptions/
   
   在内核源码树中。该目录中的文件包含完整的例外文本和所需的 `异常元标签`_ 示例：
   
   示例:
   
   LICENSES/exceptions/Linux-syscall-note
   
   包含 Linux 内核 COPYING 文件中记录的 Linux syscall 例外，用于 UAPI 头文件，例如 /* SPDX-License-Identifier: GPL-2.0 WITH Linux-syscall-note */：
   
   LICENSES/exceptions/GCC-exception-2.0
   
   包含 GCC 的 '链接例外'，允许任何二进制文件无论其许可证如何都可以链接到标记有此例外的编译后的文件。这对于从不兼容 GPL 的源代码创建可运行的可执行文件是必需的。

_`异常元标签`:

   异常文件中必须包含以下元标签：

   - SPDX-Exception-Identifier:
     
     可以与 SPDX 许可证标识符一起使用的单个例外标识符
   - SPDX-URL:
     
     包含与该例外相关附加信息的 SPDX 页面的 URL
   - SPDX-Licenses:
     
     逗号分隔的 SPDX 许可证标识符列表，这些许可证可以与该例外一起使用
   - Usage-Guidance:
     
     自由形式的使用建议文本。文本后应跟上正确的示例，这些示例应根据 `许可证标识符语法`_ 指南放入源文件中
   - Exception-Text:
     
     此标签之后的所有文本被视为原始例外文本

   文件格式示例：

   SPDX-Exception-Identifier: Linux-syscall-note
   SPDX-URL: https://spdx.org/licenses/Linux-syscall-note.html
   SPDX-Licenses: GPL-2.0, GPL-2.0+, GPL-1.0+, LGPL-2.0, LGPL-2.0+, LGPL-2.1, LGPL-2.1+
   Usage-Guidance:
     此例外与上述任何一个 SPDX-Licenses 一起使用，用于标记用户空间 API（uapi）头文件，以便它们可以被非 GPL 兼容的用户空间应用程序代码包含
```
要使用此例外情况，请使用关键字WITH将其添加到SPDX-Licenses标签中的一个标识符：
```
SPDX-License-Identifier: <SPDX-License> WITH Linux-syscall-note
```
异常文本：
```
Full exception text
```

```
SPDX-Exception-Identifier: GCC-exception-2.0
SPDX-URL: https://spdx.org/licenses/GCC-exception-2.0.html
SPDX-Licenses: GPL-2.0, GPL-2.0+
Usage-Guidance:
  “GCC 运行时库例外 2.0”与上述SPDX-Licenses之一一起用于从GCC运行时库导入的代码
```
要使用此例外情况，请使用关键字WITH将其添加到SPDX-Licenses标签中的一个标识符：
```
SPDX-License-Identifier: <SPDX-License> WITH GCC-exception-2.0
```
异常文本：
```
Full exception text
```

所有SPDX许可证标识符和例外都必须在LICENSES子目录中有一个对应的文件。这是为了允许工具验证（例如checkpatch.pl）并使许可证可以立即从源码中读取和提取，这被多个FOSS组织推荐，例如FSFE REUSE倡议。

`MODULE_LICENSE`
-----------------
可加载内核模块也需要一个MODULE_LICENSE()标签。此标签既不是正确源码许可信息（SPDX-License-Identifier）的替代品，也不是以任何形式表达或确定模块源码提供的确切许可方式。
此标签的唯一目的是为内核模块加载器和用户空间工具提供足够的信息来判断该模块是否为自由软件或专有软件。
MODULE_LICENSE()的有效许可字符串如下：

| 许可字符串 | 解释 |
| :--: | :-- |
| "GPL" | 模块按照GPL版本2许可。这并不表示GPL-2.0-only还是GPL-2.0-or-later的区别。确切的许可信息只能通过相应的源文件中的许可信息确定 |
| "GPL v2" | 与"GPL"相同。其存在是出于历史原因 |
| "GPL and additional rights" | 表示模块源码采用GPL v2变体和MIT许可双重许可的历史变种。请勿在新代码中使用 |
| "Dual MIT/GPL" | 正确地表示模块采用GPL v2变体或MIT许可选择双重许可的方式 |
| "Dual BSD/GPL" | 模块采用GPL v2变体或BSD许可选择双重许可的方式。确切的BSD许可变体只能通过相应源文件中的许可信息确定 |
| "Dual MPL/GPL" | 模块采用GPL v2变体或Mozilla公共许可（MPL）选择双重许可的方式。确切的MPL许可变体只能通过相应源文件中的许可信息确定 |
“专有” 该模块采用专有许可
此字符串仅用于专有的第三方模块，不能用于源代码在内核树中的模块。
标记为此类的模块在加载时会以内核标记‘P’污染内核，并且内核模块加载器拒绝将此类模块与使用EXPORT_SYMBOL_GPL()导出的符号进行链接。
