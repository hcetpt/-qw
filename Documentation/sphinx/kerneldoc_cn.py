```python
# coding=utf-8

# 版权声明 © 2016 Intel Corporation

# 在此授予任何人免费获取本软件及其相关文档文件（“软件”）的副本的权利，
# 并允许其不受限制地处理软件，包括但不限于使用、复制、修改、合并、发布、分发、转授权和/或出售软件副本，
# 并允许接收方这样做，前提是满足以下条件：

# 上述版权声明和此许可声明（包括下一段）必须包含在所有副本或实质部分中。

# 软件按“原样”提供，没有任何明示或暗示的保证，包括但不限于对适销性、特定用途适用性和非侵权性的保证。
# 在任何情况下，作者或版权持有人都不对任何索赔、损害或其他责任负责，无论是在合同行为、侵权行为还是其他行为中，
# 从软件或与软件使用或其他交易有关的任何事项引起的。

# 作者：
#    Jani Nikula <jani.nikula@intel.com>

# 请确保这段代码同时适用于Python 2和Python 3

import codecs
import os
import subprocess
import sys
import re
import glob

from docutils import nodes, statemachine
from docutils.statemachine import ViewList
from docutils.parsers.rst import directives, Directive
import sphinx
from sphinx.util.docutils import switch_source_input
import kernellog

__version__ = '1.0'

class KernelDocDirective(Directive):
    """从指定文件中提取内核文档注释"""
    required_argument = 1
    optional_arguments = 4
    option_spec = {
        'doc': directives.unchanged_required,
        'export': directives.unchanged,
        'internal': directives.unchanged,
        'identifiers': directives.unchanged,
        'no-identifiers': directives.unchanged,
        'functions': directives.unchanged,
    }
    has_content = False

    def run(self):
        env = self.state.document.settings.env
        cmd = [env.config.kerneldoc_bin, '-rst', '-enable-lineno']

        # 将版本字符串传递给内核文档，因为它需要根据Sphinx支持的C域的不同版本使用不同的方言
        cmd += ['-sphinx-version', sphinx.__version__]

        filename = env.config.kerneldoc_srctree + '/' + self.arguments[0]
        export_file_patterns = []

        # 告知Sphinx依赖关系
        env.note_dependency(os.path.abspath(filename))

        tab_width = self.options.get('tab-width', self.state.document.settings.tab_width)

        # 'function' 是 'identifiers' 的别名
        if 'functions' in self.options:
            self.options['identifiers'] = self.options.get('functions')

        # TODO: 使这部分更优雅，并且更健壮以应对错误
        if 'export' in self.options:
            cmd += ['-export']
            export_file_patterns = str(self.options.get('export')).split()
        elif 'internal' in self.options:
            cmd += ['-internal']
            export_file_patterns = str(self.options.get('internal')).split()
        elif 'doc' in self.options:
            cmd += ['-function', str(self.options.get('doc'))]
        elif 'identifiers' in self.options:
            identifiers = self.options.get('identifiers').split()
            if identifiers:
                for i in identifiers:
                    cmd += ['-function', i]
            else:
                cmd += ['-no-doc-sections']

        if 'no-identifiers' in self.options:
            no_identifiers = self.options.get('no-identifiers').split()
            if no_identifiers:
                for i in no_identifiers:
                    cmd += ['-nosymbol', i]

        for pattern in export_file_patterns:
            for f in glob.glob(env.config.kerneldoc_srctree + '/' + pattern):
                env.note_dependency(os.path.abspath(f))
                cmd += ['-export-file', f]

        cmd += [filename]

        try:
            kernellog.verbose(env.app, '调用 kernel-doc \'%s\'' % (" ".join(cmd)))

            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()

            out, err = codecs.decode(out, 'utf-8'), codecs.decode(err, 'utf-8')

            if p.returncode != 0:
                sys.stderr.write(err)

                kernellog.warn(env.app, 'kernel-doc \'%s\' 失败，返回码为 %d' % (" ".join(cmd), p.returncode))
                return [nodes.error(None, nodes.paragraph(text="kernel-doc 缺失"))]
            elif env.config.kerneldoc_verbosity > 0:
                sys.stderr.write(err)

            lines = statemachine.string2lines(out, tab_width, convert_whitespace=True)
            result = ViewList()

            lineoffset = 0
            line_regex = re.compile(r"^\.\. LINENO ([0-9]+)$")
            for line in lines:
                match = line_regex.search(line)
                if match:
                    # Sphinx 行号从 0 开始
                    lineoffset = int(match.group(1)) - 1
                    # 我们必须忽略我们的注释，因为它们会破坏标记
                else:
                    doc = str(env.srcdir) + "/" + env.docname + ":" + str(self.lineno)
                    result.append(line, doc + ": " + filename, lineoffset)
                    lineoffset += 1

            node = nodes.section()
            self.do_parse(result, node)

            return node.children

        except Exception as e:  # pylint: disable=W0703
            kernellog.warn(env.app, 'kernel-doc \'%s\' 处理失败： %s' % (" ".join(cmd), str(e)))
            return [nodes.error(None, nodes.paragraph(text="kernel-doc 缺失"))]

    def do_parse(self, result, node):
        with switch_source_input(self.state, result):
            self.state.nested_parse(result, 0, node, match_titles=1)

def setup(app):
    app.add_config_value('kerneldoc_bin', None, 'env')
    app.add_config_value('kerneldoc_srctree', None, 'env')
    app.add_config_value('kerneldoc_verbosity', 1, 'env')

    app.add_directive('kernel-doc', KernelDocDirective)

    return dict(
        version=__version__,
        parallel_read_safe=True,
        parallel_write_safe=True
    )
```

这段代码定义了一个Sphinx指令`KernelDocDirective`，用于从指定的文件中提取内核文档注释。同时，它还定义了如何设置该指令以及如何处理可能出现的异常情况。
