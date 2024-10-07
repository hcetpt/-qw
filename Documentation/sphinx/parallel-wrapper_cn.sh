```sh
#!/bin/sh
# SPDX-License-Identifier: GPL-2.0+
#
# 确定是否应根据 make 环境（由 scripts/jobserver-exec 导出）遵循特定的并行度，
# 或者在顶层 "make" 调用中未指定 "-jN" 时回退到 "auto" 并行模式
sphinx="$1"
shift || true

parallel="$PARALLELISM"
if [ -z "$parallel" ] ; then
	# 如果顶层 make 没有指定并行度，则回退到 "htmldocs" 目标所期望的 "-jauto" 模式
	auto=$(perl -e 'open IN,"'"$sphinx"' --version 2>&1 |";
			while (<IN>) {
				if (m/([\d\.]+)/) {
					print "auto" if ($1 >= "1.7")
				}
			}
			close IN')
	if [ -n "$auto" ] ; then
		parallel="$auto"
	fi
fi
# 只有在确定了某种并行度的情况下，我们才添加 -jN 选项
if [ -n "$parallel" ] ; then
	parallel="-j$parallel"
fi

exec "$sphinx" $parallel "$@"
```
