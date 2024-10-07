```python
#!/usr/bin/env python3
# -*- coding: utf-8; mode: python -*-
# pylint: disable=R0903, C0330, R0914, R0912, E0401

"""
    kernel-include
    ~~~~~~~~~~~~~~

    实现了 ``kernel-include`` reST 指令。
    :copyright:  版权所有 (C) 2016 Markus Heiser
    :license:    GPL 第 2 版，1991 年 6 月发布，请参阅 linux/COPYING 获取详细信息
    ``kernel-include`` reST 指令是 ``include`` 指令的替代方案。``kernel-include`` 指令在路径名中扩展环境变量，并允许从任意位置包含文件。
    .. hint::
          从任意位置（例如从 ``/etc``）包含文件对构建者来说是一个安全风险。这就是为什么 docutils 的 ``include`` 指令禁止指向放置包含指令的 reST 文档所在文件系统树之外的位置的路径名。
    形如 $name 或 ${name} 的子字符串将被替换为环境变量 name 的值。格式错误的变量名称和对不存在变量的引用将保持不变。
"""

# ==============================================================================
# 导入模块
# ==============================================================================

import os.path
from docutils import io, nodes, statemachine
from docutils.utils.error_reporting import SafeString, ErrorString
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.body import CodeBlock, NumberLines
from docutils.parsers.rst.directives.misc import Include

__version__ = '1.0'

# ==============================================================================
def setup(app):
# ==============================================================================
    app.add_directive("kernel-include", KernelInclude)
    return dict(
        version=__version__,
        parallel_read_safe=True,
        parallel_write_safe=True
    )

# ==============================================================================
class KernelInclude(Include):
# ==============================================================================
    """KernelInclude (``kernel-include``) 指令"""

    def run(self):
        env = self.state.document.settings.env
        path = os.path.realpath(
            os.path.expandvars(self.arguments[0]))

        # 为了增加安全性，禁止使用 /etc:
        if path.startswith(os.sep + "etc"):
            raise self.severe(
                '在 "%s" 指令中出现问题，禁止的路径: %s'
                % (self.name, path))

        self.arguments[0] = path

        env.note_dependency(os.path.abspath(path))

        # return super(KernelInclude, self).run()  # 不会工作，见 _run() 中的提示
        return self._run()

    def _run(self):
        """将一个文件作为此 reST 文件内容的一部分包含进来。"""

        # 提示：我不得不复制并粘贴整个 Include.run 方法。我对这个做法并不满意，
        # 但由于安全原因，Include.run 方法不允许绝对或相对路径指向放置 reST 文档的文件系统树之外的位置。
        if not self.state.document.settings.file_insertion_enabled:
            raise self.warning('"%s" 指令已禁用。' % self.name)
        source = self.state_machine.input_lines.source(
            self.lineno - self.state_machine.input_offset - 1)
        source_dir = os.path.dirname(os.path.abspath(source))
        path = directives.path(self.arguments[0])
        if path.startswith('<') and path.endswith('>'):
            path = os.path.join(self.standard_include_path, path[1:-1])
        path = os.path.normpath(os.path.join(source_dir, path))

        # 提示：这是我唯一需要修改/注释掉的一行：
        # path = utils.relative_path(None, path)

        encoding = self.options.get(
            'encoding', self.state.document.settings.input_encoding)
        e_handler = self.state.document.settings.input_encoding_error_handler
        tab_width = self.options.get(
            'tab-width', self.state.document.settings.tab_width)
        try:
            self.state.document.settings.record_dependencies.add(path)
            include_file = io.FileInput(source_path=path,
                                        encoding=encoding,
                                        error_handler=e_handler)
        except UnicodeEncodeError as error:
            raise self.severe('在 "%s" 指令路径中出现问题：\n'
                              '无法编码输入文件路径 "%s" '
                              '(错误的本地设置？).' %
                              (self.name, SafeString(path)))
        except IOError as error:
            raise self.severe('在 "%s" 指令路径中出现问题：\n%s.' %
                              (self.name, ErrorString(error)))
        startline = self.options.get('start-line', None)
        endline = self.options.get('end-line', None)
        try:
            if startline or (endline is not None):
                lines = include_file.readlines()
                rawtext = ''.join(lines[startline:endline])
            else:
                rawtext = include_file.read()
        except UnicodeError as error:
            raise self.severe('在 "%s" 指令中出现问题：\n%s' %
                              (self.name, ErrorString(error)))
        # start-after/end-before: 匹配文本中没有换行符限制，
        # 并且在行内匹配与行边界匹配之间没有限制
        after_text = self.options.get('start-after', None)
        if after_text:
            # 跳过 rawtext 中匹配文本之前的内容（包括匹配文本）
            after_index = rawtext.find(after_text)
            if after_index < 0:
                raise self.severe('在 "%s" 指令的 "start-after" 选项中出现问题：\n未找到文本。' % self.name)
            rawtext = rawtext[after_index + len(after_text):]
        before_text = self.options.get('end-before', None)
        if before_text:
            # 跳过 rawtext 中匹配文本之后的内容（包括匹配文本）
            before_index = rawtext.find(before_text)
            if before_index < 0:
                raise self.severe('在 "%s" 指令的 "end-before" 选项中出现问题：\n未找到文本。' % self.name)
            rawtext = rawtext[:before_index]

        include_lines = statemachine.string2lines(rawtext, tab_width,
                                                  convert_whitespace=True)
        if 'literal' in self.options:
            # 如果 `tab_width` 是正数，则将制表符转换为空格
            if tab_width >= 0:
                text = rawtext.expandtabs(tab_width)
            else:
                text = rawtext
            literal_block = nodes.literal_block(rawtext, source=path,
                                                classes=self.options.get('class', []))
            literal_block.line = 1
            self.add_name(literal_block)
            if 'number-lines' in self.options:
                try:
                    startline = int(self.options['number-lines'] or 1)
                except ValueError:
                    raise self.error(':number-lines: 非整数开始值')
                endline = startline + len(include_lines)
                if text.endswith('\n'):
                    text = text[:-1]
                tokens = NumberLines([([], text)], startline, endline)
                for classes, value in tokens:
                    if classes:
                        literal_block += nodes.inline(value, value,
                                                      classes=classes)
                    else:
                        literal_block += nodes.Text(value, value)
            else:
                literal_block += nodes.Text(text, text)
            return [literal_block]
        if 'code' in self.options:
            self.options['source'] = path
            codeblock = CodeBlock(self.name,
                                  [self.options.pop('code')],  # 参数
                                  self.options,
                                  include_lines,  # 内容
                                  self.lineno,
                                  self.content_offset,
                                  self.block_text,
                                  self.state,
                                  self.state_machine)
            return codeblock.run()
        self.state_machine.insert_input(include_lines, path)
        return []
```
