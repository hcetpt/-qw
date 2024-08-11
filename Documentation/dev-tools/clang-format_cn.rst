### Clang-Format

`clang-format` 是一个根据一组规则和启发式方法来格式化 C/C++ 代码的工具。

如同大多数工具一样，它并非完美，也无法覆盖所有情况，但已经足够好用。`clang-format` 可用于以下几种目的：

- 快速将一段代码重格式化为内核风格。特别适用于移动代码、对齐或排序时。详情参见 `clangformatreformat_`。
- 在你维护的文件中、审查的补丁、差异等地方发现风格错误、拼写错误以及可能的改进。详情参见 `clangformatreview_`。
- 帮助你遵循编码风格规则，特别是对于新接触内核开发的人或同时参与多个具有不同编码风格项目的开发者尤其有用。

其配置文件是位于内核树根目录下的 `.clang-format` 文件。

该文件中的规则试图接近最常见的内核编码风格。它们也尽可能地遵循 `Documentation/process/coding-style.rst <codingstyle>` 中的内容。由于内核的不同部分并不总是遵循相同的风格，因此你可能需要针对特定子系统或文件夹调整默认设置。要做到这一点，你可以在子文件夹中编写另一个 `.clang-format` 文件以覆盖默认值。

该工具本身已经被包括在流行 Linux 发行版的仓库中很长时间了。在你的仓库中搜索 `clang-format` 即可找到。否则，你可以从以下链接下载预构建的 LLVM/clang 二进制文件或编译源代码：

    https://releases.llvm.org/download.html

关于该工具的更多信息，请参阅：

    https://clang.llvm.org/docs/ClangFormat.html

    https://clang.llvm.org/docs/ClangFormatStyleOptions.html

### 审查文件和补丁的编码风格

通过运行工具的内联模式，可以审查整个子系统、文件夹或单个文件中的编码风格错误、拼写错误或改进。

要执行此操作，你可以运行类似下面的命令：

    # 确保你的工作目录是干净的！
    clang-format -i kernel/*.[ch]

然后查看 git diff。

计算此类 diff 的行数对于改进/微调配置文件中的样式选项也很有用；同时也可用于测试新的 `clang-format` 功能/版本。

`clang-format` 还支持读取统一差异（unified diffs），因此你可以轻松地审查补丁和 git 差异。具体文档请参阅：

    https://clang.llvm.org/docs/ClangFormat.html#script-for-patch-reformatting

为了避免 `clang-format` 格式化文件中的某些部分，你可以这样做：

    int formatted_code;
    // clang-format off
        void    unformatted_code  ;
    // clang-format on
    void formatted_code_again;

虽然使用这种方法保持文件始终与 `clang-format` 同步可能很诱人，尤其是在编写新文件或作为维护者时，请注意人们可能会运行不同的 `clang-format` 版本或根本没有可用的 `clang-format`。因此，在内核源码中使用这种方法之前，你应该谨慎行事，至少在我们确定 `clang-format` 是否变得普遍之前。
代码块的重新格式化
---------------------------

通过与文本编辑器集成，您可以使用单个按键操作来重新格式化任意选定的代码块。这对于移动代码、复杂的、深度缩进的代码、多行宏（及其反斜杠对齐）等情况下特别有用。

请记住，在工具未能完美完成任务的情况下，您始终可以随后调整更改。但作为一种初步处理方式，它非常有用。

对于许多流行的文本编辑器都存在集成支持。例如对于 Vim、Emacs、BBEdit 和 Visual Studio 等编辑器，您可以找到内置的支持。具体说明可以在以下链接中找到：

    https://clang.llvm.org/docs/ClangFormat.html

对于 Atom、Eclipse、Sublime Text、Visual Studio Code、XCode 及其他编辑器和集成开发环境 (IDE)，您应该能找到现成可用的插件。对于这种使用场景，考虑使用一个辅助的 `.clang-format` 文件，以便可以微调一些选项。参见 [额外功能/选项](#clangformatextra)。

.. _clangformatmissing:

缺失的支持
-------------

`clang-format` 缺少内核代码中一些常见的支持。这些情况很容易记住，因此如果您经常使用此工具，很快就会学会如何避免或忽略它们。

特别是，您会注意到的一些非常常见的情况包括：

  - 对齐的一行 `#define` 块，例如：

        #define TRACING_MAP_BITS_DEFAULT       11
        #define TRACING_MAP_BITS_MAX           17
        #define TRACING_MAP_BITS_MIN           7

    而不是：

        #define TRACING_MAP_BITS_DEFAULT 11
        #define TRACING_MAP_BITS_MAX 17
        #define TRACING_MAP_BITS_MIN 7

  - 对齐的指定初始化，例如：

        static const struct file_operations uprobe_events_ops = {
                .owner          = THIS_MODULE,
                .open           = probes_open,
                .read           = seq_read,
                .llseek         = seq_lseek,
                .release        = seq_release,
                .write          = probes_write,
        };

    而不是：

        static const struct file_operations uprobe_events_ops = {
                .owner = THIS_MODULE,
                .open = probes_open,
                .read = seq_read,
                .llseek = seq_lseek,
                .release = seq_release,
                .write = probes_write,
        };

.. _clangformatextra:

额外功能/选项
----------------------

配置文件中并未默认启用某些特性/样式选项，目的是最小化输出结果与现有代码之间的差异。换句话说，使差异尽可能小，以便于审查整个文件的风格，以及查看差异和补丁。

在其他情况下（例如特定子系统/文件夹/文件），内核风格可能有所不同，并且启用某些这些选项可能会更接近那里的风格。

例如：

  - 对齐赋值 (`AlignConsecutiveAssignments`)
  - 对齐声明 (`AlignConsecutiveDeclarations`)
- 在注释中重新排版文本（`ReflowComments`）
- 对 `#includes` 进行排序（`SortIncludes`）

这些选项通常更适合于块级的格式化调整，而不是整个文件的格式化。
你可能希望创建另一个 `.clang-format` 文件，并在你的编辑器或集成开发环境(IDE)中使用该文件。
