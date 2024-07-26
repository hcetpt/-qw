### SPDX 许可证标识符：GPL-2.0

### _内核许可_

#### Linux 内核许可规则

Linux 内核依据 GNU 通用公共许可证第 2 版（仅限 GPL-2.0）的条款提供，详情参见 `LICENSES/preferred/GPL-2.0` 文件，并包含一个在 `LICENSES/exceptions/Linux-syscall-note` 中明确描述的系统调用例外。这些信息都在 COPYING 文件中进行了说明。本文档提供了如何为每个源文件添加注释以明确和无歧义地表明其许可证的方法。它不替代内核本身的许可证。COPYING 文件中描述的许可证适用于整个内核源代码，尽管单个源文件可以有与 GPL-2.0 兼容的不同许可证：

- `GPL-1.0+` ：GNU 通用公共许可证第 1.0 版或更高版本
- `GPL-2.0+` ：GNU 通用公共许可证第 2.0 版或更高版本
- `LGPL-2.0` ：GNU 库通用公共许可证第 2 版仅限
- `LGPL-2.0+` ：GNU 库通用公共许可证第 2 版或更高版本
- `LGPL-2.1` ：GNU 较弱通用公共许可证第 2.1 版仅限
- `LGPL-2.1+` ：GNU 较弱通用公共许可证第 2.1 版或更高版本

除此之外，单个文件还可以采用双重许可方式发布，例如其中一个与 GPL 兼容的许可，以及另一个如 BSD、MIT 等更为宽松的许可。
用户空间 API（UAPI）头文件是一个特殊情况，它们描述了用户空间程序与内核之间的接口。根据内核 COPYING 文件中的说明，系统调用接口是一个明确的界限，不会将 GPL 的要求扩展到使用此接口与内核通信的任何软件。因为 UAPI 头文件必须能够被创建在 Linux 内核上运行的可执行文件中的任何源文件包含，因此需要通过特殊许可声明来记录这一例外。

表示源文件许可证的一种常见方法是在文件顶部的注释中添加相应的模板文本。由于格式问题、拼写错误等，这些“模板”很难通过用于许可证合规性的工具进行验证。

另一种方法是使用每份源文件中的软件包数据交换（SPDX）许可证标识符。SPDX 许可证标识符是可以被机器解析的精确许可证简写，用来表示文件内容的贡献许可。SPDX 许可证标识符由 Linux 基金会下的 SPDX 工作组管理，并得到了业界合作伙伴、工具供应商和法律团队的广泛认可。更多信息请参考 [https://spdx.org/](https://spdx.org/)。

Linux 内核要求所有源文件都必须使用精确的 SPDX 标识符。

#### 许可证标识符语法

1. **位置**：

   在内核文件中，SPDX 许可证标识符应添加在文件中第一条可能包含注释的行。对于大多数文件，这是第一行，除了需要在第一行包含 `#!PATH_TO_INTERPRETER` 的脚本文件。对于这类脚本，SPDX 标识符应放在第二行。

2. **样式**：

   SPDX 许可证标识符以注释的形式添加。注释样式取决于文件类型：

   - C 源文件：`// SPDX-License-Identifier: <SPDX License Expression>`
   - C 头文件：`/* SPDX-License-Identifier: <SPDX License Expression> */`
   - 汇编语言文件：`/* SPDX-License-Identifier: <SPDX License Expression> */`
   - 脚本文件：`# SPDX-License-Identifier: <SPDX License Expression>`
   - `.rst` 文件：`.. SPDX-License-Identifier: <SPDX License Expression>`
   - `.dts{i}` 文件：`// SPDX-License-Identifier: <SPDX License Expression>`

   如果特定工具无法处理标准注释样式，则应使用该工具可接受的适当注释机制。C 头文件使用 `/* */` 风格的注释是因为某些工具（如生成的 `.lds` 文件中使用的 `ld`）无法解析 C++ 风格的注释。虽然这个问题现在已经被修复，但仍然有一些较旧的汇编器工具无法处理 C++ 风格的注释。
3. 语法：

   一个<SPDX 许可表达式>要么是在SPDX许可列表上找到的SPDX简短形式的许可标识符，要么是两个SPDX简短形式的许可标识符通过“WITH”分隔而成（当适用许可例外时）。当有多个许可适用时，表达式由关键字“AND”、“OR”分隔子表达式并用“（”和“）”包围组成。
对于像[L]GPL这样带有‘或更高版本’选项的许可，其许可标识符通过使用“+”来表示‘或更高版本’选项。例如： 

      // SPDX-License-Identifier: GPL-2.0+
      // SPDX-License-Identifier: LGPL-2.1+

   “WITH”应当在需要对许可进行修改时使用。例如，Linux内核UAPI文件使用的表达式为：

      // SPDX-License-Identifier: GPL-2.0 WITH Linux-syscall-note
      // SPDX-License-Identifier: GPL-2.0+ WITH Linux-syscall-note

   内核中其他使用“WITH”例外的例子包括：

      // SPDX-License-Identifier: GPL-2.0 WITH mif-exception
      // SPDX-License-Identifier: GPL-2.0+ WITH GCC-exception-2.0

   例外只能与特定的许可标识符一起使用。有效的许可标识符列在例外文本文件的标签中。详情请参阅章节《许可标识符》_中的“例外”部分。
“OR”应当用于文件具有双重许可且仅需选择其中一个许可的情况。例如，一些dtsi文件可以在双重许可下使用：

      // SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause

   内核中关于双重许可文件中的许可表达式的例子包括：

      // SPDX-License-Identifier: GPL-2.0 OR MIT
      // SPDX-License-Identifier: GPL-2.0 OR BSD-2-Clause
      // SPDX-License-Identifier: GPL-2.0 OR Apache-2.0
      // SPDX-License-Identifier: GPL-2.0 OR MPL-1.1
      // SPDX-License-Identifier: (GPL-2.0 WITH Linux-syscall-note) OR MIT
      // SPDX-License-Identifier: GPL-1.0+ OR BSD-3-Clause OR OpenSSL

   “AND”应当用于文件具有多个许可且所有这些许可条款都适用于使用该文件的情况。例如，如果代码从另一个项目继承而来，并已获得将其放入内核的许可，但原始的许可条款需要保持有效：

      // SPDX-License-Identifier: (GPL-2.0 WITH Linux-syscall-note) AND MIT

   另一个例子是需要同时遵守两套许可条款的情况：

      // SPDX-License-Identifier: GPL-1.0+ AND LGPL-2.1+

### 许可标识符
-------------------

当前使用的许可以及添加到内核的代码所使用的许可可以分为：

1. _`首选许可`：

   尽可能地使用这些许可，因为它们被证明是完全兼容并且广泛使用的。这些许可可以从目录中获取：

      LICENSES/preferred/

   在内核源码树中
该目录中的文件包含完整的许可文本和`元标签`_。文件名与SPDX许可标识符相同，应在源文件中使用该标识符。
示例：

      LICENSES/preferred/GPL-2.0

   包含GPL版本2的许可文本和所需的元标签：

      LICENSES/preferred/MIT

   包含MIT许可文本和所需的元标签。

   _`元标签`：

   许可文件中必须包含以下元标签：

   - Valid-License-Identifier:

     一条或多条声明哪些许可标识符在项目中有效以引用此特定许可文本的行。通常这是一个单一的有效标识符，但对于具有‘或更高版本’选项的许可，有两个有效的标识符。
- SPDX-URL:

     关于该许可的SPDX页面的URL。
- Usage-Guidance:

     使用建议的自由格式文本。文本必须包含正确的示例，以说明如何根据《许可标识符语法》_指南将SPDX许可标识符放入源文件中。
- License-Text:

     此标签之后的所有文本被视为原始许可文本。

   文件格式示例：

      Valid-License-Identifier: GPL-2.0
      Valid-License-Identifier: GPL-2.0+
      SPDX-URL: https://spdx.org/licenses/GPL-2.0.html
      Usage-Guide:
        要在源代码中使用此许可，请按照许可规则文档中的放置指南将以下任一SPDX标签/值对放入注释中
对于‘GNU通用公共许可协议（GPL）版本2仅限于此版本’，使用：
	  SPDX-License-Identifier: GPL-2.0
对于‘GNU通用公共许可协议（GPL）版本2或任何更高版本’，使用：
	  SPDX-License-Identifier: GPL-2.0+
      License-Text:
        完整的许可文本

   ::

      SPDX-License-Identifier: MIT
      SPDX-URL: https://spdx.org/licenses/MIT.html
      Usage-Guide:
	要在源代码中使用此许可，请按照许可规则文档中的放置指南将以下SPDX标签/值对放入注释中
### 许可证标识符与文本：

- **SPDX-License-Identifier:** MIT
- **License-Text:**
  - 完整的许可证文本

---

### 2. 过时的许可证：

这些许可证仅应用于现有的代码或从其他项目导入的代码。这些许可证可以从内核源码树中的目录获取：
```
LICENSES/deprecated/
```

此目录下的文件包含完整的许可证文本和`元标签`_。文件名与SPDX许可证标识符相同，该标识符应用于源文件中的许可证。

**示例：**
- ```
  LICENSES/deprecated/ISC
  ```
  包含Internet Systems Consortium许可证文本及所需的元标签：
  
  - ```
    LICENSES/deprecated/GPL-1.0
    ```
  包含GPL版本1许可证文本及所需的元标签。

**元标签：**

对于“其他”许可证的元标签要求与`首选许可证`_的要求相同。

**文件格式示例：**

- **Valid-License-Identifier:** ISC
- **SPDX-URL:** https://spdx.org/licenses/ISC.html
- **Usage-Guide:**
  - 在内核中对新代码使用此许可证是不被鼓励的；它仅应用于从已有项目导入代码。
  
要在源代码中使用此许可证，请根据许可规则文档中的放置指南，在注释中放入以下SPDX标签/值对：
- **SPDX-License-Identifier:** ISC
- **License-Text:**
  - 完整的许可证文本

---

### 3. 只限双重许可

这些许可证仅应用于与其他许可证一起进行双重许可，此外还需加上首选许可证。这些许可证可以从内核源码树中的目录获取：
```
LICENSES/dual/
```

此目录下的文件包含完整的许可证文本和`元标签`_。文件名与SPDX许可证标识符相同，该标识符应用于源文件中的许可证。

**示例：**
- ```
  LICENSES/dual/MPL-1.1
  ```
  包含Mozilla Public License版本1.1许可证文本及所需的元标签：
  
  - ```
    LICENSES/dual/Apache-2.0
    ```
  包含Apache License版本2.0许可证文本及所需的元标签。

**元标签：**

对于“其他”许可证的元标签要求与`首选许可证`_的要求相同。
文件格式示例：

      有效许可标识符: MPL-1.1
      SPDX-URL: https://spdx.org/licenses/MPL-1.1.html
      使用指南:
        不要使用。MPL-1.1与GPL2不兼容。它仅可用于
        双许可的文件，其中另一个许可与GPL2兼容。
        如果最终使用了此许可，则必须与一个与GPL2兼容的
        许可一起使用 "或" 的形式。
        要使用Mozilla公共许可证版本1.1，请根据许可规则文档中的
        放置指南，在注释中添加以下SPDX标签/值对：
      SPDX-License-Identifier: MPL-1.1
      许可文本:
        完整许可文本

|

4. _`例外`:

   某些许可可以通过例外进行修改，这些例外授予原许可未提供的某些权利。
   这些例外可以从目录中获得：
   
      LICENSES/exceptions/
   
   在内核源码树中。该目录中的文件包含完整的例外文本和必需的 `例外元标签`_。
   示例：

      LICENSES/exceptions/Linux-syscall-note
   
   包含Linux内核COPYING文件中记录的Linux系统调用例外，用于UAPI头文件，
   例如 /* SPDX-License-Identifier: GPL-2.0 WITH Linux-syscall-note */ :
   
      LICENSES/exceptions/GCC-exception-2.0
   
   包含GCC的“链接例外”，允许将任何二进制文件（无论其许可如何）与带有此例外标记的文件编译版本链接。
   这对于从与GPL不兼容的源代码创建可执行程序是必需的。

_`例外元标签`:

   例外文件中必须包含以下元标签：

   - SPDX-Exception-Identifier:

     一个例外标识符，可以与SPDX许可标识符一起使用。
- SPDX-URL:

     与该例外相关的SPDX页面的URL。
- SPDX-Licenses:

     以逗号分隔的SPDX许可标识符列表，表示可以使用此例外的许可。
- 使用指导:

     自由格式的文本，提供使用建议。文本后应跟上正确的示例，说明如何根据 `许可标识符语法`_ 指南将SPDX许可标识符放入源文件中。
- Exception-Text:

     此标签之后的所有文本被视为原始例外文本。

   文件格式示例：

      SPDX-Exception-Identifier: Linux-syscall-note
      SPDX-URL: https://spdx.org/licenses/Linux-syscall-note.html
      SPDX-Licenses: GPL-2.0, GPL-2.0+, GPL-1.0+, LGPL-2.0, LGPL-2.0+, LGPL-2.1, LGPL-2.1+
      使用指导:
        此例外与上述SPDX-Licenses之一一起使用
        标记用户空间API（uapi）头文件，以便它们可以被纳入不符合GPL的用户空间应用程序代码。
要使用此例外，请使用关键字WITH将其添加到SPDX许可证标签中的一个标识符中：
``SPDX-License-Identifier: <SPDX-License> WITH Linux-syscall-note``  
**例外文本：**
```
全量例外文本

:: 

SPDX-Exception-Identifier: GCC-exception-2.0 
SPDX-URL: https://spdx.org/licenses/GCC-exception-2.0.html 
SPDX-Licenses: GPL-2.0, GPL-2.0+ 
Usage-Guidance: 
  “GCC 运行时库例外 2.0”与上述SPDX-Licenses之一一起用于从GCC运行时库导入的代码
```
要使用此例外，请使用关键字WITH将其添加到SPDX许可证标签中的一个标识符中：
``SPDX-License-Identifier: <SPDX-License> WITH GCC-exception-2.0``  
**例外文本：**
```
全量例外文本
```

所有SPDX许可证标识符和例外都必须在LICENSES子目录中有相应的文件。这是为了允许工具验证（例如checkpatch.pl）并使许可证可以直接从源码中读取和提取，这是多个FOSS组织推荐的做法，例如FSFE REUSE倡议（<https://reuse.software/>）。  
**MODULE_LICENSE**
-------------------

加载式内核模块也需要MODULE_LICENSE()标签。此标签既不是正确源码许可证信息（SPDX-License-Identifier）的替代品，也不以任何方式与表示或确定模块源码提供的确切许可证相关。
此标签的唯一目的是为内核模块加载器和用户空间工具提供足够的信息来判断该模块是自由软件还是专有软件。
对于MODULE_LICENSE()有效的许可字符串包括：

    ============================= =============================================
    "GPL"                          模块采用GPL版本2许可。这不区分
                                  GPL-2.0-only还是GPL-2.0-or-later。确切的
                                  许可信息只能通过相应源文件中的
                                  许可证信息来确定
"GPL v2"                          与"GPL"相同。出于历史原因存在
"GPL and additional rights"       表示模块源码同时遵循GPL v2变体和MIT许可的历史性表达方式。请勿在新代码中使用
"Dual MIT/GPL"                    正确地表示模块遵循GPL v2变体或MIT许可的选择
"Dual BSD/GPL"                    模块遵循GPL v2变体或BSD许可的选择。确切的BSD许可变体只能通过相应源文件中的
                                  许可证信息来确定
"Dual MPL/GPL"                    模块遵循GPL v2变体或Mozilla公共许可（MPL）的选择。确切的MPL许可变体只能通过相应源文件中的
                                  许可证信息来确定
"专有"         该模块受专有许可的约束。
此字符串仅用于专有的第三方模块，不能用于那些源代码在内核树中的模块。
标记为此类的模块在加载时会以内核标记添加 'P' 标志，并且内核模块加载器拒绝将此类模块与通过 EXPORT_SYMBOL_GPL() 导出的符号进行链接。
