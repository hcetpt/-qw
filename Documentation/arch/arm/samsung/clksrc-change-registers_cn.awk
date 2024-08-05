```bash
#!/usr/bin/awk -f
#
# 版权所有 2010 Ben Dooks <ben-linux@fluff.org>
#
# 根据GPLv2发布

# 示例用法
# ./clksrc-change-registers.awk arch/arm/plat-s5pc1xx/include/plat/regs-clock.h < src > dst

function extract_value(s)
{
    eqat = index(s, "=")
    comat = index(s, ",")
    return substr(s, eqat+2, (comat-eqat)-2)
}

function remove_brackets(b)
{
    return substr(b, 2, length(b)-2)
}

function splitdefine(l, p)
{
    r = split(l, tp)

    p[0] = tp[2]
    p[1] = remove_brackets(tp[3])
}

function find_length(f)
{
    if (0)
	printf "find_length " f "\n" > "/dev/stderr"

    if (f ~ /0x1/)
	return 1
    else if (f ~ /0x3/)
	return 2
    else if (f ~ /0x7/)
	return 3
    else if (f ~ /0xf/)
	return 4

    printf "未知长度 " f "\n" > "/dev/stderr"
    exit
}

function find_shift(s)
{
    id = index(s, "<")
    if (id <= 0) {
	printf "无法找到移位 " s "\n" > "/dev/stderr"
	exit
    }

    return substr(s, id+2)
}

BEGIN {
    if (ARGC < 2) {
	print "参数太少" > "/dev/stderr"
	exit
    }

# 读取头文件并查找我们需要替换的掩码值
# 并创建一个关联数组来存储这些值

    while (getline line < ARGV[1] > 0) {
	if (line ~ /\#define.*_MASK/ &&
	    !(line ~ /USB_SIG_MASK/)) {
	    splitdefine(line, fields)
	    name = fields[0]
	    if (0)
		printf "MASK " line "\n" > "/dev/stderr"
	    dmask[name,0] = find_length(fields[1])
	    dmask[name,1] = find_shift(fields[1])
	    if (0)
		printf "=> '" name "' LENGTH=" dmask[name,0] " SHIFT=" dmask[name,1] "\n" > "/dev/stderr"
	} else {
	}
    }

    delete ARGV[1]
}

/clksrc_clk.*=.*{/ {
    shift=""
    mask=""
    divshift=""
    reg_div=""
    reg_src=""
    indent=1

    print $0

    for(; indent >= 1;) {
	if ((getline line) <= 0) {
	    printf "意外的文件结束" > "/dev/stderr"
	    exit 1;
	}

	if (line ~ /\.shift/) {
	    shift = extract_value(line)
	} else if (line ~ /\.mask/) {
	    mask = extract_value(line)
	} else if (line ~ /\.reg_divider/) {
	    reg_div = extract_value(line)
	} else if (line ~ /\.reg_source/) {
	    reg_src = extract_value(line)
	} else if (line ~ /\.divider_shift/) {
	    divshift = extract_value(line)
	} else if (line ~ /{/) {
		indent++
		print line
	    } else if (line ~ /}/) {
	    indent--

	    if (indent == 0) {
		if (0) {
		    printf "shift '" shift   "' ='" dmask[shift,0] "'\n" > "/dev/stderr"
		    printf "mask  '" mask    "'\n" > "/dev/stderr"
		    printf "dshft '" divshift "'\n" > "/dev/stderr"
		    printf "rdiv  '" reg_div "'\n" > "/dev/stderr"
		    printf "rsrc  '" reg_src "'\n" > "/dev/stderr"
		}

		generated = mask
		sub(reg_src, reg_div, generated)

		if (0) {
		    printf "/* rsrc " reg_src " */\n"
		    printf "/* rdiv " reg_div " */\n"
		    printf "/* shift " shift " */\n"
		    printf "/* mask " mask " */\n"
		    printf "/* generated " generated " */\n"
		}

		if (reg_div != "") {
		    printf "\t.reg_div = { "
		    printf ".reg = " reg_div ", "
		    printf ".shift = " dmask[generated,1] ", "
		    printf ".size = " dmask[generated,0] ", "
		    printf "},\n"
		}

		printf "\t.reg_src = { "
		printf ".reg = " reg_src ", "
		printf ".shift = " dmask[mask,1] ", "
		printf ".size = " dmask[mask,0] ", "

		printf "},\n"

	    }

	    print line
	} else {
	    print line
	}

	if (0)
	    printf indent ":" line "\n" > "/dev/stderr"
    }
}

// && ! /clksrc_clk.*=.*{/ { print $0 }
```
这是将原始脚本翻译成中文版本，保留了原始脚本的功能和逻辑。请注意，某些关键字（如函数名）没有翻译，因为它们在 AWK 脚本中需要保持英文。
