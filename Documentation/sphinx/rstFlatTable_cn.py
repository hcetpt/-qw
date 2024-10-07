```python
#！/usr/bin/env python3
# -*- coding: utf-8; mode: python -*-
# pylint: disable=C0330, R0903, R0912

"""
    flat-table
    ~~~~~~~~~~

    实现 ``flat-table`` reST 指令
:copyright:  版权所有 (C) 2016 Markus Heiser
:license:    GPL 第 2 版，1991 年 6 月发布，请参阅 linux/COPYING 以获取详细信息。
``flat-table``（:py:class:`FlatTable`）是一个类似于 ``list-table`` 的双阶段列表，并且具有一些附加功能：

    * *column-span*：使用角色 ``cspan`` 可以将单元格扩展到额外的列中。

    * *row-span*：使用角色 ``rspan`` 可以将单元格扩展到额外的行中。

    * *自动填充* 表格行最右侧的单元格可以跨越该表格行右侧缺失的单元格。通过选项 ``:fill-cells:`` 可以将此行为从 *自动跨越* 更改为 *自动填充*，自动插入（空）单元格而不是跨越最后一个单元格。
选项：

    * header-rows: [int] 标题行的数量
    * stub-columns: [int] 辅助列的数量
    * widths: [[int] [int] ...] 列宽
    * fill-cells: 代替自动跨越缺失的单元格，插入缺失的单元格

    角色：

    * cspan: [int] 额外的列（*morecols*）
    * rspan: [int] 额外的行（*morerows*）
"""

# ==============================================================================
# 导入模块
# ==============================================================================

from docutils import nodes
from docutils.parsers.rst import directives, roles
from docutils.parsers.rst.directives.tables import Table
from docutils.utils import SystemMessagePropagation

# ==============================================================================
# 公共全局变量
# ==============================================================================

__version__ = '1.0'

# ==============================================================================
def setup(app):
# ==============================================================================

    app.add_directive("flat-table", FlatTable)
    roles.register_local_role('cspan', c_span)
    roles.register_local_role('rspan', r_span)

    return dict(
        version=__version__,
        parallel_read_safe=True,
        parallel_write_safe=True
    )

# ==============================================================================
def c_span(name, rawtext, text, lineno, inliner, options=None, content=None):
# ==============================================================================
    # pylint: disable=W0613

    options = options if options is not None else {}
    content = content if content is not None else []
    nodelist = [colSpan(span=int(text))]
    msglist = []
    return nodelist, msglist

# ==============================================================================
def r_span(name, rawtext, text, lineno, inliner, options=None, content=None):
# ==============================================================================
    # pylint: disable=W0613

    options = options if options is not None else {}
    content = content if content is not None else []
    nodelist = [rowSpan(span=int(text))]
    msglist = []
    return nodelist, msglist


# ==============================================================================
class rowSpan(nodes.General, nodes.Element): pass  # pylint: disable=C0103,C0321
class colSpan(nodes.General, nodes.Element): pass  # pylint: disable=C0103,C0321
# ==============================================================================

# ==============================================================================
class FlatTable(Table):
# ==============================================================================

    """FlatTable （``flat-table``）指令"""

    option_spec = {
        'name': directives.unchanged,
        'class': directives.class_option,
        'header-rows': directives.nonnegative_int,
        'stub-columns': directives.nonnegative_int,
        'widths': directives.positive_int_list,
        'fill-cells': directives.flag
    }

    def run(self):

        if not self.content:
            error = self.state_machine.reporter.error(
                '“%s”指令为空；需要内容。' % self.name,
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno
            )
            return [error]

        title, messages = self.make_title()
        node = nodes.Element()  # 匿名容器用于解析
        self.state.nested_parse(self.content, self.content_offset, node)

        tableBuilder = ListTableBuilder(self)
        tableBuilder.parseFlatTableNode(node)
        tableNode = tableBuilder.buildTableNode()
        if title:
            tableNode.insert(0, title)
        return [tableNode] + messages


# ==============================================================================
class ListTableBuilder(object):
# ==============================================================================

    """从双阶段列表构建表格"""

    def __init__(self, directive):
        self.directive = directive
        self.rows = []
        self.max_cols = 0

    def buildTableNode(self):

        colwidths = self.directive.get_column_widths(self.max_cols)
        if isinstance(colwidths, tuple):
            # 自 docutils 0.13 起，get_column_widths 返回一个 (widths, colwidths) 元组，
            # 其中 widths 是一个字符串（即 'auto'）
# 参见 https://sourceforge.net/p/docutils/patches/120/
            colwidths = colwidths[1]
        stub_columns = self.directive.options.get('stub-columns', 0)
        header_rows = self.directive.options.get('header-rows', 0)

        table = nodes.table()
        tgroup = nodes.tgroup(cols=len(colwidths))
        table += tgroup

        for colwidth in colwidths:
            colspec = nodes.colspec(colwidth=colwidth)
            if stub_columns:
                colspec.attributes['stub'] = 1
                stub_columns -= 1
            tgroup += colspec
        stub_columns = self.directive.options.get('stub-columns', 0)

        if header_rows:
            thead = nodes.thead()
            tgroup += thead
            for row in self.rows[:header_rows]:
                thead += self.buildTableRowNode(row)

        tbody = nodes.tbody()
        tgroup += tbody

        for row in self.rows[header_rows:]:
            tbody += self.buildTableRowNode(row)
        return table

    def buildTableRowNode(self, row_data, classes=None):
        classes = [] if classes is None else classes
        row = nodes.row()
        for cell in row_data:
            if cell is None:
                continue
            cspan, rspan, cellElements = cell

            attributes = {"classes": classes}
            if rspan:
                attributes['morerows'] = rspan
            if cspan:
                attributes['morecols'] = cspan
            entry = nodes.entry(**attributes)
            entry.extend(cellElements)
            row += entry
        return row

    def raiseError(self, msg):
        error = self.directive.state_machine.reporter.error(
            msg,
            nodes.literal_block(self.directive.block_text, self.directive.block_text),
            line=self.directive.lineno
        )
        raise SystemMessagePropagation(error)

    def parseFlatTableNode(self, node):
        """解析来自 :py:class:`FlatTable` 指令主体的节点"""

        if len(node) != 1 or not isinstance(node[0], nodes.bullet_list):
            self.raiseError(
                '解析 “%s” 指令的内容块时出错：期望恰好有一个项目列表。' % self.directive.name
            )

        for rowNum, rowItem in enumerate(node[0]):
            row = self.parseRowItem(rowItem, rowNum)
            self.rows.append(row)
        self.roundOffTableDefinition()

    def roundOffTableDefinition(self):
        """完成表格定义
此方法完成 :py:member:`rows` 中的表格定义：
* 此方法插入因跨越单元格而缺失的 ``None`` 值
* 重新计算 :py:member:`max_cols`

* 自动跨越或填充（选项 ``fill-cells``）表格行右侧的缺失单元格
"""

        y = 0
        while y < len(self.rows):
            x = 0

            while x < len(self.rows[y]):
                cell = self.rows[y][x]
                if cell is None:
                    x += 1
                    continue
                cspan, rspan = cell[:2]
                # 处理当前行中的 colspan
                for c in range(cspan):
                    try:
                        self.rows[y].insert(x + c + 1, None)
                    except:  # pylint: disable=W0702
                        # 用户设置了有歧义的 rowspan
                        pass  # SDK.CONSOLE()
                # 处理跨越的行中的 colspan
                for r in range(rspan):
                    for c in range(cspan + 1):
                        try:
                            self.rows[y + r + 1].insert(x + c, None)
                        except:  # pylint: disable=W0702
                            # 用户设置了有歧义的 rowspan
                            pass  # SDK.CONSOLE()
                x += 1
            y += 1

        # 在右侧插入缺失的单元格。为此，首先重新计算最大列数
```
```python
for row in self.rows:
    if self.max_cols < len(row):
        self.max_cols = len(row)

# 填充空单元格还是单元格合并？

fill_cells = False
if 'fill-cells' in self.directive.options:
    fill_cells = True

for row in self.rows:
    x = self.max_cols - len(row)
    if x and not fill_cells:
        if row[-1] is None:
            row.append((x - 1, 0, []))
        else:
            cspan, rspan, content = row[-1]
            row[-1] = (cspan + x, rspan, content)
    elif x and fill_cells:
        for i in range(x):
            row.append((0, 0, nodes.comment()))

def pprint(self):
    # 用于调试
    retVal = "[   "
    for row in self.rows:
        retVal += "[ "
        for col in row:
            if col is None:
                retVal += '%r\n    , ' % col
            else:
                content = col[2][0].astext()
                if len(content) > 30:
                    content = content[:30] + "..."
                retVal += '(cspan=%s, rspan=%s, %r)' % (col[0], col[1], content)
                retVal += "]\n    , "
        retVal = retVal[:-2]
        retVal += "]\n  , "
    retVal = retVal[:-2]
    return retVal + "]"

def parseRowItem(self, rowItem, rowNum):
    row = []
    childNo = 0
    error = False
    cell = None
    target = None

    for child in rowItem:
        if isinstance(child, nodes.comment) or isinstance(child, nodes.system_message):
            pass
        elif isinstance(child, nodes.target):
            target = child
        elif isinstance(child, nodes.bullet_list):
            childNo += 1
            cell = child
        else:
            error = True
            break

    if childNo != 1 or error:
        self.raiseError(
            '解析 "%s" 指令的内容块时出错：期望的是两级项目符号列表，但第 %s 行不包含第二级项目符号列表。'
            % (self.directive.name, rowNum + 1))

    for cellItem in cell:
        cspan, rspan, cellElements = self.parseCellItem(cellItem)
        if target is not None:
            cellElements.insert(0, target)
        row.append((cspan, rspan, cellElements))
    return row

def parseCellItem(self, cellItem):
    # 在此列表项（字段）的第一个元素中搜索并移除 cspan, rspan colspec
    cspan = rspan = 0
    if not len(cellItem):
        return cspan, rspan, []
    for elem in cellItem[0]:
        if isinstance(elem, colSpan):
            cspan = elem.get("span")
            elem.parent.remove(elem)
            continue
        if isinstance(elem, rowSpan):
            rspan = elem.get("span")
            elem.parent.remove(elem)
            continue
    return cspan, rspan, cellItem[:]
```

这段代码主要实现了以下几个功能：
1. 计算最大列数 `max_cols`。
2. 根据配置决定是否填充空单元格或进行单元格合并。
3. 打印表格内容用于调试。
4. 解析表格行中的各个元素，并处理单元格合并和列宽信息。
