```makefile
# SPDX 许可证标识符: GPL-2.0-only

# 定义默认的安装、删除和删除目录命令
INSTALL          ?= install
RM               ?= rm -f
RMDIR            ?= rmdir --ignore-fail-on-non-empty

# 定义前缀和手册页的目录路径
PREFIX           ?= /usr/share
MANDIR           ?= $(PREFIX)/man
MAN1DIR          = $(MANDIR)/man1

# 搜索所有以rv开头的rst格式文档
MAN1_RST         = $(wildcard rv*.rst)

# 将找到的rst文件转换为对应的手册页名称
_DOC_MAN1        = $(patsubst %.rst,%.1,$(MAN1_RST))
DOC_MAN1         = $(addprefix $(OUTPUT),$(_DOC_MAN1))

# 查找rst2man工具的位置
RST2MAN_DEP      := $(shell command -v rst2man 2>/dev/null)
# 设置rst2man的选项
RST2MAN_OPTS     += --verbose

# 测试rst2man是否可用
TEST_RST2MAN     = $(shell sh -c "rst2man --version > /dev/null 2>&1 || echo n")

# 规则: 从rst文件生成手册页
$(OUTPUT)%.1: %.rst
ifndef RST2MAN_DEP
    # 如果未找到rst2man，显示提示信息并退出
    $(info ********************************************)
    $(info ** 注意: 未找到rst2man)
    $(info **)
    $(info ** 考虑从你的发行版中安装最新的rst2man，例如，在Fedora上使用'dnf install python3-docutils')
    $(info ** 或者从源代码安装：)
    $(info **)
    $(info **  https://docutils.sourceforge.io/docs/dev/repository.html )
    $(info **)
    $(info ********************************************)
    $(error 注意: 需要rst2man来生成手册页)
endif
    # 使用rst2man将rst文件转换为手册页
    rst2man $(RST2MAN_OPTS) $< > $@

# 目标: 生成man1目录下的手册页
man1: $(DOC_MAN1)
# 默认目标: 生成所有手册页
man: man1

# 清理规则: 删除生成的手册页
clean:
    $(RM) $(DOC_MAN1)

# 安装规则: 安装手册页到指定目录
install: man
    $(INSTALL) -d -m 755 $(DESTDIR)$(MAN1DIR)
    $(INSTALL) -m 644 $(DOC_MAN1) $(DESTDIR)$(MAN1DIR)

# 卸载规则: 删除已安装的手册页和目录
uninstall:
    $(RM) $(addprefix $(DESTDIR)$(MAN1DIR)/,$(_DOC_MAN1))
    $(RMDIR) $(DESTDIR)$(MAN1DIR)

# 声明伪目标
.PHONY: man man1 clean install uninstall
# 设置默认目标
.DEFAULT_GOAL := man
```
这段Makefile脚本定义了用于构建、安装和卸载手册页的规则。它使用`rst2man`工具将`.rst`格式的文档转换为Unix/Linux系统中的手册页（`.1`）。此外，它还包含了安装和卸载手册页到系统中的规则，以及清理生成的手册页文件的功能。
