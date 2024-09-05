```bash
# SPDX-License-Identifier: GPL-2.0
#
# 一个小脚本，用于可视化显示一个架构的内核特性支持状态
#
# （如果没有给出参数，则会打印主机架构的状态。）
#

ARCH=${1:-$(uname -m | sed 's/x86_64/x86/' | sed 's/i386/x86/')}

$(dirname $0)/../../scripts/get_feat.pl list --arch $ARCH
```
