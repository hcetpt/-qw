使用 Sphinx 编写内核文档
=====================================

Linux 内核使用 `Sphinx`_ 来从 `reStructuredText`_ 文件中生成美观的文档，这些文件位于 ``Documentation`` 目录下。要构建 HTML 或 PDF 格式的文档，请使用 ``make htmldocs`` 或 ``make pdfdocs``。生成的文档将放置在 ``Documentation/output`` 中。
.. _Sphinx: http://www.sphinx-doc.org/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html

reStructuredText 文件可以包含指令来包含来自源文件中的结构化文档注释或内核文档注释。通常这些注释用于描述代码的功能、类型和设计。内核文档注释具有一些特殊的结构和格式，但除此之外，它们也被视为 reStructuredText。
最后，在 ``Documentation`` 目录下散布着数千个纯文本文档文件。随着时间的推移，其中一些可能会被转换为 reStructuredText，但大部分仍将保持纯文本形式。
.. _sphinx_install:

Sphinx 安装
==============

当前由 Documentation/ 文件使用的 ReST 标记旨在与版本 2.4.4 或更高版本的 ``Sphinx`` 一起使用。
有一个脚本用于检查 Sphinx 的要求。请参阅 :ref:`sphinx-pre-install` 以获取更多详细信息。
大多数发行版都自带 Sphinx，但其工具链较为脆弱，因此在你的机器上升级它或其他 Python 包导致文档构建失败的情况并不少见。
为了避免这种情况，建议使用不同于发行版自带的版本。为此，推荐在 ``virtualenv-3`` 或 ``virtualenv`` 中安装 Sphinx（这取决于你的发行版如何打包 Python 3）。
.. note:: 

   #) 推荐使用 RTD 主题进行 HTML 输出。根据 Sphinx 的版本，需要单独安装它，
      使用命令 ``pip install sphinx_rtd_theme``。
总之，如果你想安装最新版本的 Sphinx，则应执行以下操作：

```bash
$ virtualenv sphinx_latest
$ . sphinx_latest/bin/activate
(sphinx_latest) $ pip install -r Documentation/sphinx/requirements.txt
```

运行 ``. sphinx_latest/bin/activate`` 后，提示符将发生变化，以此表明你正在使用新的环境。如果你打开一个新的 shell，你需要重新运行此命令才能再次进入虚拟环境并在其中构建文档。
图像输出
------------

内核文档构建系统包含一个扩展，用于处理 GraphViz 和 SVG 格式的图像（参见 :ref:`sphinx_kfigure`）。
为了让其正常工作，您需要安装 GraphViz 和 ImageMagick 软件包。如果这些软件包没有安装，构建系统仍然会构建文档，但输出的 PDF 和 LaTeX 文件中将不包含任何图像。
PDF 和 LaTeX 构建
--------------------
目前仅在 Sphinx 2.4 及更高版本中支持此类构建。对于 PDF 和 LaTeX 输出，您还需要 ``XeLaTeX`` 3.14159265 版本。根据不同的发行版，您可能还需要安装一系列提供 ``XeLaTeX`` 正常工作所需的最小功能集的 ``texlive`` 软件包。
HTML 中的数学表达式
------------------------
一些 ReST 页面包含数学表达式。由于 Sphinx 的工作方式，这些表达式使用 LaTeX 符号编写。
Sphinx 有两种选项来在 HTML 输出中渲染数学表达式：
一种是名为 `imgmath`_ 的扩展，它将数学表达式转换为图像并嵌入到 HTML 页面中。
另一种是名为 `mathjax`_ 的扩展，它将数学渲染委托给具备 JavaScript 功能的 Web 浏览器。
前者是 6.1 版本之前内核文档的唯一选项，并且需要相当多的 ``texlive`` 软件包，包括 amsfonts 和 amsmath 等。
从 6.1 版本的内核开始，可以在不安装任何 ``texlive`` 软件包的情况下构建包含数学表达式的 HTML 页面。更多详细信息，请参阅 `Math Renderer 选择`_。
.. _imgmath: https://www.sphinx-doc.org/zh_CN/master/usage/extensions/math.html#module-sphinx.ext.imgmath
.. _mathjax: https://www.sphinx-doc.org/zh_CN/master/usage/extensions/math.html#module-sphinx.ext.mathjax

.. _sphinx-pre-install:

检查Sphinx依赖项
-------------------

有一个脚本可以自动检查Sphinx的依赖项。如果它可以识别您的发行版，它也会提供有关您的发行版安装命令行选项的提示：

	$ ./scripts/sphinx-pre-install
	正在检查Fedora release 26 (Twenty Six)所需的工具是否可用
	警告：最好也安装 "texlive-luatex85"
您应该运行：

		sudo dnf install -y texlive-luatex85
		/usr/bin/virtualenv sphinx_2.4.4
		. sphinx_2..4.4/bin/activate
		pip install -r Documentation/sphinx/requirements.txt

	在./scripts/sphinx-pre-install第468行处缺少1个必需的依赖项，无法构建
默认情况下，它会检查html和PDF格式所需的所有要求，包括图像、数学表达式和LaTeX构建的要求，并假设将使用Python虚拟环境。对于html构建所必需的那些被认为是强制性的；其他的则被视为可选的。
它支持两个可选参数：

``--no-pdf``
	禁用PDF的检查；

``--no-virtualenv``
	使用OS包装而不是Python虚拟环境来安装Sphinx
Sphinx构建
============

通常生成文档的方式是运行 ``make htmldocs`` 或 ``make pdfdocs``。还有其他可用的格式：请参阅 ``make help`` 中的文档部分。生成的文档会被放置在 ``Documentation/output`` 下的特定格式子目录中。
为了生成文档，显然需要安装Sphinx（``sphinx-build``）。对于PDF输出，您还需要 ``XeLaTeX`` 和来自ImageMagick的 ``convert(1)``\ [#ink]_ 。所有这些都非常广泛地可用并且被包含在各种发行版中。
要向Sphinx传递额外的选项，您可以使用 ``SPHINXOPTS`` make 变量。例如，使用 ``make SPHINXOPTS=-v htmldocs`` 来获取更详细的输出。
还可以通过使用 ``DOCS_CSS`` make 变量传递一个额外的DOCS_CSS覆盖文件，以自定义html布局。
默认情况下，“Alabaster”主题用于构建HTML文档；这个主题已经包含在Sphinx中，无需单独安装。
可以通过使用 ``DOCS_THEME`` make 变量来覆盖Sphinx主题。
存在另一个构建变量 `SPHINXDIRS`，在测试构建文档子集时非常有用。例如，你可以通过运行 `make SPHINXDIRS=doc-guide htmldocs` 来构建位于 `Documentation/doc-guide` 下的文档。
要查看可以指定的子目录列表，请参阅 `make help` 的文档部分。
要移除生成的文档，请运行 `make cleandocs`。

.. [#ink] 如果同时安装了 Inkscape（<https://inkscape.org>）中的 `inkscape(1)`，则可以提高嵌入到 PDF 文档中的图像质量，特别是对于内核版本 5.18 及以上。

数学渲染器的选择
----------------------

自内核版本 6.1 起，MathJax 作为 HTML 输出的备选数学渲染器使用。[\#sph1_8]_

根据可用命令的不同，选择不同的数学渲染器，具体如下表所示：

.. 表格:: HTML 输出的数学渲染器选择

    ============= ================= ============
    数学渲染器   所需命令           图像格式
    ============= ================= ============
    imgmath       latex, dvipng      PNG（位图）
    mathjax
    ============= ================= ============

可以通过设置环境变量 `SPHINX_IMGMATH` 来覆盖默认选择，如下面表格所示：

.. 表格:: 设置 `SPHINX_IMGMATH` 的效果

    ====================== ========
    设置                   渲染器
    ====================== ========
    `SPHINX_IMGMATH=yes`   imgmath
    `SPHINX_IMGMATH=no`    mathjax
    ====================== ========

.. [#sph1_8] 数学渲染器的备选项要求 Sphinx 版本大于等于 1.8

编写文档
=====================

添加新文档可以很简单，步骤如下：

1. 在 `Documentation` 目录下新建一个 `.rst` 文件。
2. 在 `Documentation/index.rst` 中的 Sphinx 主 `TOC tree`_ 中引用它。
.. _TOC tree: http://www.sphinx-doc.org/en/stable/markup/toctree.html

这通常对于简单的文档（如你现在阅读的文档）来说已经足够好，但对于较大的文档，创建一个子目录（或使用现有的子目录）可能更为合适。例如，图形子系统的文档位于 `Documentation/gpu` 下，被拆分为多个 `.rst` 文件，并且有一个单独的 `index.rst`（包含自己的 `toctree`），这个文件从主索引中被引用。
请参阅 `Sphinx`_ 和 `reStructuredText`_ 的文档以了解它们能做些什么。特别是，Sphinx 的 `reStructuredText 入门指南`_ 是开始学习 reStructuredText 的好地方。还有一些 `Sphinx 特定的标记构造`_。
.. _reStructuredText 入门指南: http://www.sphinx-doc.org/en/stable/rest.html
.. _Sphinx 特定的标记构造: http://www.sphinx-doc.org/en/stable/markup/index.html

针对内核文档的具体指导方针
-----------------------------------

以下是针对内核文档的一些具体指导方针：

* 请不要过度使用 reStructuredText 标记。保持简洁。大多数情况下，文档应为纯文本，只需具备足够的格式一致性以便能够转换为其他格式。
* 在将现有文档转换为reStructuredText时，请尽量减少格式更改。
* 在转换文档时，不仅要更新格式，还要更新内容。
* 请遵循以下标题装饰的顺序：

  1. 对于文档标题使用上方和下方的 ``=`` ：

         ==============
         文档标题
         ==============

  2. 对于章节使用 ``=`` ：

         章节
         ========

  3. 对于节使用 ``-`` ：

         节
         -------

  4. 对于子节使用 ``~`` ：

         子节
         ~~~~~~~~~~

  尽管reStructuredText没有规定特定的顺序（"而不是强加固定的段落标题装饰样式数量和顺序，执行的顺序将是遇到的顺序"），但总体上保持较高级别的统一使得文档更易于跟踪。

* 对于插入固定宽度的文本块（例如代码示例、用例示例等），对于不需要语法高亮的短片段使用 ``::`` 。对于较长的代码块，使用 ``.. code-block:: <language>`` ，特别是当它们可以从语法高亮中受益时。对于嵌入在文本中的短代码片段，使用 ```` 。

C 域
------------

**Sphinx 的 C 域**（名称 c）适用于 C API 的文档编写。例如一个函数原型：

.. code-block:: rst

    .. c:function:: int ioctl( int fd, int request )

内核文档的 C 域有一些额外的功能。例如，您可以对像 `open` 或 `ioctl` 这样常见的函数名进行**重命名**：

.. code-block:: rst

     .. c:function:: int ioctl( int fd, int request )
        :name: VIDIOC_LOG_STATUS

函数名（例如 ioctl）在输出中保留不变，但是参考名从 `ioctl` 更改为 `VIDIOC_LOG_STATUS`。该函数的索引条目也更改为 `VIDIOC_LOG_STATUS`。

请注意，没有必要使用 `c:func:` 来生成指向函数文档的交叉引用。由于一些 Sphinx 扩展的魔法，文档构建系统会自动将对 `function()` 的引用转换为交叉引用，如果存在给定函数名的索引条目。如果您在内核文档中看到 `c:func:` 的用法，请随意删除它。

表格
------

reStructuredText 提供了几种表格语法选项。内核风格是优先使用 *简单表格* 语法或 *网格表格* 语法。有关更多详细信息，请参阅 `reStructuredText 用户参考中的表格语法`_。
.. _reStructuredText 用户参考中的表格语法:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#tables

列表表格
~~~~~~~~~~~

列表表格格式对于那些不容易用通常的 Sphinx ASCII 艺术格式布局的表格很有用。然而，这些格式对于纯文本文档的读者来说几乎是无法理解的，除非有充分的理由，否则应避免使用。

`扁平表格` 是类似于 `列表表格` 的两阶段列表，并具有一些附加功能：

* 列合并：通过角色 `cspan` 可以使单元格扩展到其他列

* 行合并：通过角色 `rspan` 可以使单元格扩展到其他行

* 自动将表格行的最右侧单元格跨过该表格行右侧缺失的单元格。使用选项 `:fill-cells:` 可以将此行为从 *自动跨列* 改变为 *自动填充*，即自动插入（空）单元格代替跨列。
  
选项：

* ``:header-rows:``   [整数] 头部行的数量
* ``:stub-columns:``  [整数] 慢性列的数量
* ``:widths:``        [[整数] [整数] ... ] 各列的宽度
* ``:fill-cells:``    替代自动跨列缺失单元格，插入缺失单元格

角色：

* ``:cspan:`` [整数] 额外的列（*morecols*）
* ``:rspan:`` [整数] 额外的行（*morerows*）

下面的例子展示了如何使用这种标记。第一级的分阶段列表是 *表格行* 。在 *表格行* 中只允许一种标记，即该 *表格行* 中的单元格列表。例外是 *注释*（ ``..`` ）和 *目标*（例如指向 ``:ref:`最后一行 <last row>`` / :ref:`最后一行 <last row>` 的引用）。
下面是提供的文档的中文翻译：

```rest
.. code-block:: rst

   .. flat-table:: 表格标题
      :widths: 2 1 1 3

      * - 标题列1
        - 标题列2
        - 标题列3
        - 标题列4

      * - 第一行
        - 字段1.1
        - 自动合并的字段1.2

      * - 第二行
        - 字段2.1
        - :rspan:`1` :cspan:`1` 字段2.2 - 3.3

      * .. _`最后一行`:

        - 第三行

渲染结果如下：

   .. flat-table:: 表格标题
      :widths: 2 1 1 3

      * - 标题列1
        - 标题列2
        - 标题列3
        - 标题列4

      * - 第一行
        - 字段1.1
        - 自动合并的字段1.2

      * - 第二行
        - 字段2.1
        - :rspan:`1` :cspan:`1` 字段2.2 - 3.3

      * .. _`最后一行`:

        - 第三行

跨文档引用
----------

从一个文档页面到另一个文档页面的跨文档引用可以通过简单地写入目标文档文件的路径来完成，不需要任何特殊的语法。路径可以是绝对的也可以是相对的。对于绝对路径，以 "Documentation/" 开头即可。例如，要引用这个页面，以下都是有效的选项，具体取决于当前文档所在的目录（注意需要包含 ``.rst`` 扩展名）：

    查看 Documentation/doc-guide/sphinx.rst。这总是有效。
查看 sphinx.rst，它位于同一目录中。
阅读 ../sphinx.rst，它位于上一级目录中。

如果希望链接显示的文本不同于文档的标题，你需要使用 Sphinx 的 ``doc`` 角色。例如：

    参见 :doc:`我为文档 sphinx 定制的链接文本<sphinx>`。

对于大多数用途来说，前一种方式更可取，因为它更简洁，更适合阅读源文件的人。如果你遇到没有增加任何价值的 ``:doc:`` 使用，请随时将其转换为仅文档路径。

关于如何跨文档引用内核函数或类型的信息，请参阅 Documentation/doc-guide/kernel-doc.rst。

引用提交
~~~~~~~~~

如果以以下格式之一书写，对 Git 提交的引用将自动被超链接：

    提交 72bf4f1767f0
    提交 72bf4f1767f0 ("net: 不要在写队列中留下空skb")

.. _sphinx_kfigure:

图形和图像
==========

如果你想添加一个图像，你应该使用 ``kernel-figure`` 和 ``kernel-image`` 指令。例如，为了插入一个可缩放的图像格式，可以使用 SVG （:ref:`svg_image_example`）：

    .. kernel-figure::  svg_image.svg
       :alt: 简单的 SVG 图像

       SVG 图像示例

.. _svg_image_example:

.. kernel-figure::  svg_image.svg
   :alt: 简单的 SVG 图像

   SVG 图像示例

内核图形（和图像）指令支持 **DOT** 格式的文件，详情请参考：

* DOT: http://graphviz.org/pdf/dotguide.pdf
* Graphviz: http://www.graphviz.org/content/dot-language

一个简单的例子（:ref:`hello_dot_file`）：

  .. kernel-figure::  hello.dot
     :alt: 你好世界

     DOT 的你好世界示例

.. _hello_dot_file:

.. kernel-figure::  hello.dot
   :alt: 你好世界

   DOT 的你好世界示例

嵌入式 *渲染* 标记语言，如 Graphviz 的 **DOT** 语言，由 ``kernel-render`` 指令提供支持：

  .. kernel-render:: DOT
     :alt: foobar 有向图
     :caption: 嵌入式 **DOT** (Graphviz) 代码

     digraph foo {
      "bar" -> "baz";
     }

其渲染效果取决于安装的工具。如果安装了 Graphviz，你将看到一个矢量图像。如果没有安装，原始标记将作为 *literal-block* 插入（:ref:`hello_dot_render`）

.. _hello_dot_render:

.. kernel-render:: DOT
   :alt: foobar 有向图
   :caption: 嵌入式 **DOT** (Graphviz) 代码

   digraph foo {
      "bar" -> "baz";
   }

*render* 指令具有 *figure* 指令的所有选项，并且还支持 ``caption`` 选项。如果 ``caption`` 有一个值，则插入 *figure* 节点。如果没有，则插入 *image* 节点。如果你想引用它，也需要有 ``caption``（:ref:`hello_svg_render`）
嵌入式 **SVG**：

  .. kernel-render:: SVG
     :caption: 嵌入式 **SVG** 标记
     :alt: so-nw-arrow

     <?xml version="1.0" encoding="UTF-8"?>
     <svg xmlns="http://www.w3.org/2000/svg"
     version="1.1" baseProfile="full" width="70px" height="40px" viewBox="0 0 700 400">
     <line x1="180" y1="370" x2="500" y2="50" stroke="black" stroke-width="15px"/>
     <polygon points="585 0 525 25 585 50" transform="rotate(135 525 25)"/>
     </svg>

.. _hello_svg_render:

.. kernel-render:: SVG
   :caption: 嵌入式 **SVG** 标记
   :alt: so-nw-arrow

   <?xml version="1.0" encoding="UTF-8"?>
   <svg xmlns="http://www.w3.org/2000/svg"
     version="1.1" baseProfile="full" width="70px" height="40px" viewBox="0 0 700 400">
   <line x1="180" y1="370" x2="500" y2="50" stroke="black" stroke-width="15px"/>
   <polygon points="585 0 525 25 585 50" transform="rotate(135 525 25)"/>
   </svg>
```

请注意，以上翻译尽可能保留了原始的 ReStructuredText 格式，但某些元素可能无法直接在中文环境中正确显示，例如表格、图片标签等。
