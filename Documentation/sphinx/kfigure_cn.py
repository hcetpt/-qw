```python
# -*- coding: utf-8; mode: python -*-
# pylint: disable=C0103, R0903, R0912, R0915
"""
    可扩展的图像和图形处理
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    实现可扩展图像处理的Sphinx扩展。
:copyright:  版权所有 © 2016 Markus Heiser
:license:    GPL 第2版，1991年6月发布，请参阅 Linux/COPYING 的详细信息
图像格式的构建取决于图像的源格式和输出的目标格式。此扩展实现了简化图像处理的方法，从作者的角度来看。像 ``kernel-figure`` 这样的指令实现了始终获得最佳输出格式的方法，即使某些工具未安装。更多细节请查看 ``convert_image(...)`` ，这是所有转换的核心。
* ``.. kernel-image``: 图像处理 / 替代 ``.. image::``

    * ``.. kernel-figure``: 图形处理 / 替代 ``.. figure::``

    * ``.. kernel-render``: 渲染标记 / 嵌入渲染标记（或语言）的概念。支持的标记（参见 ``RENDER_MARKUP_EXT``）

      - ``DOT``: 渲染嵌入的Graphviz的 **DOC**
      - ``SVG``: 渲染嵌入的可缩放矢量图形（**SVG**）
      - ... 可开发的

使用的工具：

    * ``dot(1)``: Graphviz（https://www.graphviz.org）。如果Graphviz不可用，则将DOT语言作为字面块插入
对于PDF转换，当可用时，使用librsvg的 ``rsvg-convert(1)`` （https://gitlab.gnome.org/GNOME/librsvg）
* SVG到PDF：生成PDF需要以下至少一个工具：

      - ``convert(1)``: ImageMagick（https://www.imagemagick.org）
      - ``inkscape(1)``: Inkscape（https://inkscape.org/）

自定义列表：

    * 从SVG生成PDF / 由PDF（LaTeX）生成器使用

    * 从DOT文件生成SVG（HTML生成器）和PDF（LaTeX生成器）
DOT: 参见 https://www.graphviz.org/content/dot-language

"""

import os
from os import path
import subprocess
from hashlib import sha1
import re
from docutils import nodes
from docutils.statemachine import ViewList
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import images
import sphinx
from sphinx.util.nodes import clean_astext
import kernellog

Figure = images.Figure

__version__ = '1.0.0'

# 简单的帮助函数
# ---------------

def which(cmd):
    """在环境变量 `PATH` 中搜索 `cmd`
此 `which` 在PATH中搜索可执行文件 `cmd` 。找到的第一个匹配项返回，如果没有找到，则返回 `None`
"""
    envpath = os.environ.get('PATH', None) or os.defpath
    for folder in envpath.split(os.pathsep):
        fname = folder + os.sep + cmd
        if path.isfile(fname):
            return fname

def mkdir(folder, mode=0o775):
    if not path.isdir(folder):
        os.makedirs(folder, mode)

def file2literal(fname):
    with open(fname, "r") as src:
        data = src.read()
        node = nodes.literal_block(data, data)
    return node

def isNewer(path1, path2):
    """如果 `path1` 比 `path2` 新则返回 `True`

如果 `path1` 存在且比 `path2` 新，则返回 `True`，否则返回 `False`
"""
    return (path.exists(path1)
            and os.stat(path1).st_ctime > os.stat(path2).st_ctime)

def pass_handle(self, node):           # pylint: disable=W0613
    pass

# 设置转换工具和Sphinx扩展
# -------------------------------------------

# Graphviz的dot(1)支持
dot_cmd = None
# 使用dot(1) -Tpdf
dot_Tpdf = False

# ImageMagick的convert(1)支持
convert_cmd = None

# librsvg的rsvg-convert(1)支持
rsvg_convert_cmd = None

# Inkscape的inkscape(1)支持
inkscape_cmd = None
# Inkscape 1.0之前的版本使用不同的命令选项
inkscape_ver_one = False


def setup(app):
    # 首先检查工具链
    app.connect('builder-inited', setupTools)

    # 图像处理
    app.add_directive("kernel-image",  KernelImage)
    app.add_node(kernel_image,
                 html    = (visit_kernel_image, pass_handle),
                 latex   = (visit_kernel_image, pass_handle),
                 texinfo = (visit_kernel_image, pass_handle),
                 text    = (visit_kernel_image, pass_handle),
                 man     = (visit_kernel_image, pass_handle), )

    # 图形处理
    app.add_directive("kernel-figure", KernelFigure)
    app.add_node(kernel_figure,
                 html    = (visit_kernel_figure, pass_handle),
                 latex   = (visit_kernel_figure, pass_handle),
                 texinfo = (visit_kernel_figure, pass_handle),
                 text    = (visit_kernel_figure, pass_handle),
                 man     = (visit_kernel_figure, pass_handle), )

    # 渲染处理
    app.add_directive('kernel-render', KernelRender)
    app.add_node(kernel_render,
                 html    = (visit_kernel_render, pass_handle),
                 latex   = (visit_kernel_render, pass_handle),
                 texinfo = (visit_kernel_render, pass_handle),
                 text    = (visit_kernel_render, pass_handle),
                 man     = (visit_kernel_render, pass_handle), )

    app.connect('doctree-read', add_kernel_figure_to_std_domain)

    return dict(
        version = __version__,
        parallel_read_safe = True,
        parallel_write_safe = True
    )


def setupTools(app):
    """
    检查可用的构建工具并记录一些详细的日志消息
此函数在构建器初始化时调用一次
```
```python
# 全局变量定义
global dot_cmd, dot_Tpdf, convert_cmd, rsvg_convert_cmd   # pylint: disable=W0603
global inkscape_cmd, inkscape_ver_one  # pylint: disable=W0603
kernellog.verbose(app, "kfigure: 检查已安装的工具...")

# 查找命令路径
dot_cmd = which('dot')
convert_cmd = which('convert')
rsvg_convert_cmd = which('rsvg-convert')
inkscape_cmd = which('inkscape')

# 处理 dot 命令
if dot_cmd:
    kernellog.verbose(app, "使用 dot(1) 从: " + dot_cmd)

    try:
        dot_Thelp_list = subprocess.check_output([dot_cmd, '-Thelp'],
                                    stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        dot_Thelp_list = err.output
        pass

    dot_Tpdf_ptn = b'pdf'
    dot_Tpdf = re.search(dot_Tpdf_ptn, dot_Thelp_list)
else:
    kernellog.warn(app, "未找到 dot(1)，为了更好的输出质量，请从 https://www.graphviz.org 安装 graphviz")

# 处理 inkscape 命令
if inkscape_cmd:
    kernellog.verbose(app, "使用 inkscape(1) 从: " + inkscape_cmd)
    inkscape_ver = subprocess.check_output([inkscape_cmd, '--version'],
                                           stderr=subprocess.DEVNULL)
    ver_one_ptn = b'Inkscape 1'
    inkscape_ver_one = re.search(ver_one_ptn, inkscape_ver)
    convert_cmd = None
    rsvg_convert_cmd = None
    dot_Tpdf = False

else:
    if convert_cmd:
        kernellog.verbose(app, "使用 convert(1) 从: " + convert_cmd)
    else:
        kernellog.verbose(app,
                          "既没有找到 inkscape(1) 也没有找到 convert(1)\n"
                          "为了将 SVG 转换为 PDF，\n"
                          "请安装 Inkscape (https://inkscape.org/)（首选）或\n"
                          "ImageMagick (https://www.imagemagick.org)")

    if rsvg_convert_cmd:
        kernellog.verbose(app, "使用 rsvg-convert(1) 从: " + rsvg_convert_cmd)
        kernellog.verbose(app, "使用 'dot -Tsvg' 和 rsvg-convert(1) 进行 DOT -> PDF 转换")
        dot_Tpdf = False
    else:
        kernellog.verbose(app,
                          "未找到 rsvg-convert(1)\n"
                          "  使用 convert(1) 的 SVG 渲染由 ImageMagick 本机渲染器完成。")
        if dot_Tpdf:
            kernellog.verbose(app, "使用 'dot -Tpdf' 进行 DOT -> PDF 转换")
        else:
            kernellog.verbose(app, "使用 'dot -Tsvg' 和 convert(1) 进行 DOT -> PDF 转换")


# 集成转换工具
# ---------------------------------

RENDER_MARKUP_EXT = {
    # '.ext' 必须由 convert_image(..) 函数的 *in_ext* 输入处理
    'DOT': '.dot',
    'SVG': '.svg'
}

def convert_image(img_node, translator, src_fname=None):
    """转换图像节点以供构建器使用
不同的构建器偏好不同的图像格式，例如 *latex* 构建器
偏好 PDF 格式，而 *html* 构建器偏好 SVG 格式。
此函数根据源格式和转换器的输出格式处理输出图像格式。
"""
    app = translator.builder.app

    fname, in_ext = path.splitext(path.basename(img_node['uri']))
    if src_fname is None:
        src_fname = path.join(translator.builder.srcdir, img_node['uri'])
        if not path.exists(src_fname):
            src_fname = path.join(translator.builder.outdir, img_node['uri'])

    dst_fname = None

    # 在内核构建中，使用 'make SPHINXOPTS=-v' 查看详细信息

    kernellog.verbose(app, '确定最佳格式: ' + img_node['uri'])

    if in_ext == '.dot':
        if not dot_cmd:
            kernellog.verbose(app,
                              "未找到 graphviz 的 dot / 包含原始 DOT 文件。")
            img_node.replace_self(file2literal(src_fname))
        elif translator.builder.format == 'latex':
            dst_fname = path.join(translator.builder.outdir, fname + '.pdf')
            img_node['uri'] = fname + '.pdf'
            img_node['candidates'] = {'*': fname + '.pdf'}
        elif translator.builder.format == 'html':
            dst_fname = path.join(
                translator.builder.outdir,
                translator.builder.imagedir,
                fname + '.svg')
            img_node['uri'] = path.join(
                translator.builder.imgpath, fname + '.svg')
            img_node['candidates'] = {
                '*': path.join(translator.builder.imgpath, fname + '.svg')}
        else:
            # 所有其他构建器格式都将包含原始 DOT 文件
            img_node.replace_self(file2literal(src_fname))

    elif in_ext == '.svg':
        if translator.builder.format == 'latex':
            if not inkscape_cmd and convert_cmd is None:
                kernellog.warn(app,
                               "没有可用的 SVG 到 PDF 转换 / 包含原始 SVG 文件。\n"
                               "包含大型原始 SVG 可能会导致 xelatex 错误。\n"
                               "安装 Inkscape（首选）或 ImageMagick。")
                img_node.replace_self(file2literal(src_fname))
            else:
                dst_fname = path.join(translator.builder.outdir, fname + '.pdf')
                img_node['uri'] = fname + '.pdf'
                img_node['candidates'] = {'*': fname + '.pdf'}

    if dst_fname:
        # 构建器不需要再复制一次，所以如果存在则删除它
        translator.builder.images.pop(img_node['uri'], None)
        _name = dst_fname[len(str(translator.builder.outdir)) + 1:]

        if isNewer(dst_fname, src_fname):
            kernellog.verbose(app,
                              "转换: {out}/%s 已经存在且较新" % _name)
        else:
            ok = False
            mkdir(path.dirname(dst_fname))

            if in_ext == '.dot':
                kernellog.verbose(app, '转换 DOT 到: {out}/' + _name)
                if translator.builder.format == 'latex' and not dot_Tpdf:
                    svg_fname = path.join(translator.builder.outdir, fname + '.svg')
                    ok1 = dot2format(app, src_fname, svg_fname)
                    ok2 = svg2pdf_by_rsvg(app, svg_fname, dst_fname)
                    ok = ok1 and ok2
                else:
                    ok = dot2format(app, src_fname, dst_fname)

            elif in_ext == '.svg':
                kernellog.verbose(app, '转换 SVG 到: {out}/' + _name)
                ok = svg2pdf(app, src_fname, dst_fname)

            if not ok:
                img_node.replace_self(file2literal(src_fname))


def dot2format(app, dot_fname, out_fname):
    """使用 `dot(1)` 将 DOT 文件转换为 `out_fname`
* `dot_fname` 输入 DOT 文件的路径名，包括扩展名 `.dot`
* `out_fname` 输出文件的路径名，包括格式扩展名

格式扩展名取决于 `dot` 命令（参见 `man dot` 选项 `-Txxx`）。通常你会使用以下扩展名之一：

- `.ps` 用于 PostScript，
- `.svg` 或 `svgz` 用于结构化矢量图形，
- `.fig` 用于 XFIG 图形，
- `.png` 或 `gif` 用于常见位图图形
"""
    out_format = path.splitext(out_fname)[1][1:]
    cmd = [dot_cmd, '-T%s' % out_format, dot_fname]
    exit_code = 42

    with open(out_fname, "w") as out:
        exit_code = subprocess.call(cmd, stdout=out)
        if exit_code != 0:
            kernellog.warn(app,
                           "调用时发生错误 #%d: %s" % (exit_code, " ".join(cmd)))
    return bool(exit_code == 0)

def svg2pdf(app, svg_fname, pdf_fname):
    """使用 `inkscape(1)` 或 `convert(1)` 命令将 SVG 转换为 PDF
使用来自 Inkscape (https://inkscape.org/) 的 `inkscape(1)` 或
来自 ImageMagick (https://www.imagemagick.org) 的 `convert(1)` 进行转换
成功返回 `True`，发生错误返回 `False`
"""
    # 实现 svg2pdf 函数
    pass
```

请注意，`svg2pdf` 函数需要实现具体的转换逻辑。
```python
# 翻译为中文:

* ``svg_fname`` 输入SVG文件的路径名，包括扩展名（``.svg``）
* ``pdf_name`` 输出PDF文件的路径名，包括扩展名（``.pdf``）

"""
cmd = [convert_cmd, svg_fname, pdf_fname]
cmd_name = 'convert(1)'

if inkscape_cmd:
    cmd_name = 'inkscape(1)'
    if inkscape_ver_one:
        cmd = [inkscape_cmd, '-o', pdf_fname, svg_fname]
    else:
        cmd = [inkscape_cmd, '-z', '--export-pdf=%s' % pdf_fname, svg_fname]

try:
    warning_msg = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    exit_code = 0
except subprocess.CalledProcessError as err:
    warning_msg = err.output
    exit_code = err.returncode
    pass

if exit_code != 0:
    kernellog.warn(app, "调用时发生错误 #%d: %s" % (exit_code, " ".join(cmd)))
    if warning_msg:
        kernellog.warn(app, "%s 的警告信息: %s"
                       % (cmd_name, str(warning_msg, 'utf-8')))
elif warning_msg:
    kernellog.verbose(app, "%s 的警告信息（可能无害）:\n%s"
                      % (cmd_name, str(warning_msg, 'utf-8')))

return exit_code == 0

def svg2pdf_by_rsvg(app, svg_fname, pdf_fname):
    """使用 ``rsvg-convert(1)`` 命令将SVG转换为PDF
* ``svg_fname`` 输入SVG文件的路径名，包括扩展名 ``.svg``
* ``pdf_fname`` 输出PDF文件的路径名，包括扩展名 ``.pdf``

输入的SVG文件应由 ``dot2format()`` 生成。
SVG到PDF的转换由 ``rsvg-convert(1)`` 完成。
如果 ``rsvg-convert(1)`` 不可用，则回退到 ``svg2pdf()``。

"""
    if rsvg_convert_cmd is None:
        ok = svg2pdf(app, svg_fname, pdf_fname)
    else:
        cmd = [rsvg_convert_cmd, '--format=pdf', '-o', pdf_fname, svg_fname]
        # 使用父进程的标准输出和标准错误
        exit_code = subprocess.call(cmd)
        if exit_code != 0:
            kernellog.warn(app, "调用时发生错误 #%d: %s" % (exit_code, " ".join(cmd)))
        ok = exit_code == 0

    return ok

# 图像处理
# ---------------------

def visit_kernel_image(self, node):    # pylint: disable=W0613
    """访问 ``kernel_image`` 节点
通过 ``convert_image(...)`` 处理 ``image`` 子节点
"""
    img_node = node[0]
    convert_image(img_node, self)

class kernel_image(nodes.image):
    """用于 ``kernel-image`` 指令的节点。"""
    pass

class KernelImage(images.Image):
    u"""KernelImage 指令

继承自 ``.. image::`` 指令的所有功能，除了 *远程URI* 和 *glob* 模式。
KernelImage 将图像节点包装在一个 kernel_image 节点中。参见 ``visit_kernel_image``。
    
    def run(self):
        uri = self.arguments[0]
        if uri.endswith('.*') or uri.find('://') != -1:
            raise self.severe(
                '在 "%s: %s" 中出现错误：不允许使用 glob 模式和远程图像'
                % (self.name, uri))
        result = images.Image.run(self)
        if len(result) == 2 or isinstance(result[0], nodes.system_message):
            return result
        (image_node,) = result
        # 将图像节点包装在一个 kernel_image 节点中 / 参见访问器
        node = kernel_image('', image_node)
        return [node]

# 图形处理
# ---------------------

def visit_kernel_figure(self, node):   # pylint: disable=W0613
    """访问 ``kernel_figure`` 节点
通过 ``convert_image(...)`` 处理 ``image`` 子节点
"""
    img_node = node[0][0]
    convert_image(img_node, self)

class kernel_figure(nodes.figure):
    """用于 ``kernel-figure`` 指令的节点。"""

class KernelFigure(Figure):
    u"""KernelFigure 指令

继承自 ``.. figure::`` 指令的所有功能，除了 *远程URI* 和 *glob* 模式。
KernelFigure 将图形节点包装在一个 kernel_figure 节点中。参见 ``visit_kernel_figure``。
```
```python
def 运行(self):
    uri = self.arguments[0]
    if uri.endswith('.*') or uri.find('://') != -1:
        raise self.severe(
            '在 "%s: %s" 中出现错误：'
            '不支持通配符模式和远程图片'
            % (self.name, uri))
    结果 = Figure.运行(self)
    if len(结果) == 2 or isinstance(结果[0], nodes.system_message):
        return 结果
    (figure_node,) = 结果
    # 将 figure 节点包裹在一个 kernel_figure 节点中 / 参见访问者方法
    节点 = kernel_figure('', figure_node)
    return [节点]


# 渲染处理
# ---------------------

def 访问_kernel_渲染(self, 节点):
    """访问 ``kernel_render`` 节点的方法
如果渲染工具可用，将 ``literal_block`` 子节点的标记保存到一个文件中，并用指向该文件的新创建的 ``image`` 节点替换 ``literal_block`` 节点。之后，使用 ``convert_image(...)`` 处理 image 子节点
"""
    应用 = self.builder.app
    源语言 = 节点.get('srclang')

    kernellog.verbose(应用, '访问 kernel-渲染 节点 语言: "%s"' % (源语言))

    临时扩展名 = RENDER_MARKUP_EXT.get(源语言, None)
    if 临时扩展名 is None:
        kernellog.warn(应用, 'kernel-渲染: "%s" 未知 / 包含原始内容.' % (源语言))
        return

    if not dot_cmd and 临时扩展名 == '.dot':
        kernellog.verbose(应用, "graphviz 的 dot 不可用 / 包含原始内容.")
        return

    文本块 = 节点[0]

    代码 = 文本块.astext()
    哈希对象 = 代码.encode('utf-8')  # str(节点属性)
    文件名 = path.join('%s-%s' % (源语言, sha1(哈希对象).hexdigest()))

    临时文件名 = path.join(
        self.builder.outdir, self.builder.imagedir, 文件名 + 临时扩展名)

    if not path.isfile(临时文件名):
        mkdir(path.dirname(临时文件名))
        with open(临时文件名, "w") as 输出:
            输出.write(代码)

    图像节点 = nodes.image(节点.rawsource, **节点属性)
    图像节点['uri'] = path.join(self.builder.imgpath, 文件名 + 临时扩展名)
    图像节点['candidates'] = {
        '*': path.join(self.builder.imgpath, 文件名 + 临时扩展名)}

    文本块.replace_self(图像节点)
    convert_image(图像节点, self, 临时文件名)


class kernel_渲染(nodes.General, nodes.Inline, nodes.Element):
    """用于 ``kernel-渲染`` 指令的节点。"""
    pass

class Kernel_渲染(Figure):
    """Kernel_渲染 指令

    使用外部工具渲染内容。具有来自 *figure* 指令的所有选项，加上 *caption* 选项。如果 *caption* 有值，则插入一个带有 *caption* 的 figure 节点；如果没有值，则插入一个 image 节点。
    Kernel_渲染 指令将指令的文本包裹在一个 literal_block 节点中，并将其包裹在一个 kernel_渲染 节点中。参见 ``访问_kernel_渲染`` 方法。
    """
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False

    # 从 'figure' 继承选项
    option_spec = Figure.option_spec.copy()
    option_spec['caption'] = directives.unchanged

    def 运行(self):
        return [self.构建节点()]

    def 构建节点(self):

        源语言 = self.arguments[0].strip()
        if 源语言 not in RENDER_MARKUP_EXT.keys():
            return [self.state_machine.reporter.warning(
                '未知的源语言 "%s"，请选择以下之一: %s.' % (
                    源语言, ",".join(RENDER_MARKUP_EXT.keys())),
                line=self.lineno)]

        代码 = '\n'.join(self.content)
        if not 代码.strip():
            return [self.state_machine.reporter.warning(
                '忽略没有内容的 "%s" 指令.' % (
                    self.name),
                line=self.lineno)]

        节点 = kernel_渲染()
        节点['alt'] = self.options.get('alt', '')
        节点['srclang'] = 源语言
        文本节点 = nodes.literal_block(代码, 代码)
        节点 += 文本节点

        标题 = self.options.get('caption')
        if 标题:
            # 解析标题的内容
            解析后 = nodes.Element()
            self.state.nested_parse(
                ViewList([标题], source=''), self.content_offset, 解析后)
            标题节点 = nodes.caption(
                解析后[0].rawsource, '', *解析后[0].children)
            标题节点.source = 解析后[0].source
            标题节点.line = 解析后[0].line

            figure_节点 = nodes.figure('', 节点)
            for k, v in self.options.items():
                figure_节点[k] = v
            figure_节点 += 标题节点

            节点 = figure_节点

        return 节点

def 添加_kernel_图示到_std_域(app, 文档树):
    """向 'std' 域添加 kernel_图示 锚点
``StandardDomain.process_doc(..)`` 方法不知道如何解析 ``kernel_图示`` 指令的标题（标签）（它只知道标准节点，如表格、图等）。没有额外的处理会导致 kernel_图示 的“未定义标签”问题。
此处理程序将 kernel_图示 的标签添加到 'std' 域的标签中。
"""

    std = app.env.domains["std"]
    文档名 = app.env.docname
    标签 = std.data["labels"]

    for 名称, 显式 in 文档树.nametypes.items():
        if not 显式:
            continue
        标签ID = 文档树.nameids[名称]
        if 标签ID is None:
            continue
        节点 = 文档树.ids[标签ID]

        if 节点.tagname == 'kernel_图示':
            for n in 节点.next_node():
                if n.tagname == 'caption':
                    节名称 = clean_astext(n)
                    # 将标签添加到 std 域
                    标签[名称] = 文档名, 标签ID, 节名称
                    break
```

请注意，上述代码已经尽可能地进行了翻译，但是某些特定的功能名称和上下文可能需要根据实际应用场景进行适当的调整。
