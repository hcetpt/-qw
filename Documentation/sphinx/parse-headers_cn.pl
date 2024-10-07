```perl
#!/usr/bin/env perl
use strict;
use Text::Tabs;
use Getopt::Long;
use Pod::Usage;

my $debug;
my $help;
my $man;

GetOptions(
    "debug" => \$debug,
    'usage|?' => \$help,
    'help' => \$man
) or pod2usage(2);

pod2usage(1) if $help;
pod2usage(-exitstatus => 0, -verbose => 2) if $man;
pod2usage(2) if (scalar @ARGV < 2 || scalar @ARGV > 3);

my ($file_in, $file_out, $file_exceptions) = @ARGV;

my $data;
my %ioctls;
my %defines;
my %typedefs;
my %enums;
my %enum_symbols;
my %structs;

require Data::Dumper if ($debug);

#
# 读取文件并获取标识符
#

my $is_enum = 0;
my $is_comment = 0;
open IN, $file_in or die "无法打开 $file_in";
while (<IN>) {
    $data .= $_;

    my $ln = $_;
    if (!$is_comment) {
        $ln =~ s,/\*.*(\*/),,g;

        $is_comment = 1 if ($ln =~ s,/\*.*,,);
    } else {
        if ($ln =~ s,^(.*\*/),,) {
            $is_comment = 0;
        } else {
            next;
        }
    }

    if ($is_enum && $ln =~ m/^\s*([_\w][\w\d_]+)\s*[\,=]?/) {
        my $s = $1;
        my $n = $1;
        $n =~ tr/A-Z/a-z/;
        $n =~ tr/_/-/;

        $enum_symbols{$s} = "\\ :ref:`$s <$n>`\\ ";

        $is_enum = 0 if ($is_enum && m/\}/);
        next;
    }
    $is_enum = 0 if ($is_enum && m/\}/);

    if ($ln =~ m/^\s*#\s*define\s+([_\w][\w\d_]+)\s+_IO/) {
        my $s = $1;
        my $n = $1;
        $n =~ tr/A-Z/a-z/;

        $ioctls{$s} = "\\ :ref:`$s <$n>`\\ ";
        next;
    }

    if ($ln =~ m/^\s*#\s*define\s+([_\w][\w\d_]+)\s+/) {
        my $s = $1;
        my $n = $1;
        $n =~ tr/A-Z/a-z/;
        $n =~ tr/_/-/;

        $defines{$s} = "\\ :ref:`$s <$n>`\\ ";
        next;
    }

    if ($ln =~ m/^\s*typedef\s+([_\w][\w\d_]+)\s+(.*)\s+([_\w][\w\d_]+);/) {
        my $s = $2;
        my $n = $3;

        $typedefs{$n} = "\\ :c:type:`$n <$s>`\\ ";
        next;
    }
    if ($ln =~ m/^\s*enum\s+([_\w][\w\d_]+)\s+\{/
        || $ln =~ m/^\s*enum\s+([_\w][\w\d_]+)$/
        || $ln =~ m/^\s*typedef\s*enum\s+([_\w][\w\d_]+)\s+\{/
        || $ln =~ m/^\s*typedef\s*enum\s+([_\w][\w\d_]+)$/) {
        my $s = $1;

        $enums{$s} = "enum :c:type:`$s`\\ ";

        $is_enum = $1;
        next;
    }
    if ($ln =~ m/^\s*struct\s+([_\w][\w\d_]+)\s+\{/
        || $ln =~ m/^\s*struct\s+([_\w][\w\d_]+)$/
        || $ln =~ m/^\s*typedef\s*struct\s+([_\w][\w\d_]+)\s+\{/
        || $ln =~ m/^\s*typedef\s*struct\s+([_\w][\w\d_]+)$/) {
        my $s = $1;

        $structs{$s} = "struct $s\\ ";
        next;
    }
}
close IN;

#
# 处理多行 typedef
#

my @matches = ($data =~ m/typedef\s+struct\s+\S+?\s*\{[^\}]+\}\s*(\S+)\s*\;/g,
              $data =~ m/typedef\s+enum\s+\S+?\s*\{[^\}]+\}\s*(\S+)\s*\;/g,);
foreach my $m (@matches) {
    my $s = $m;

    $typedefs{$s} = "\\ :c:type:`$s`\\ ";
    next;
}

#
# 处理异常，如果有的话
#

my %def_reftype = (
    "ioctl"   => ":ref",
    "define"  => ":ref",
    "symbol"  => ":ref",
    "typedef" => ":c:type",
    "enum"    => ":c:type",
    "struct"  => ":c:type",
);

if ($file_exceptions) {
    open IN, $file_exceptions or die "无法读取 $file_exceptions";
    while (<IN>) {
        next if (m/^\s*$/ || m/^\s*#/);

        # 解析忽略符号

        if (m/^ignore\s+ioctl\s+(\S+)/) {
            delete $ioctls{$1} if (exists($ioctls{$1}));
            next;
        }
        if (m/^ignore\s+define\s+(\S+)/) {
            delete $defines{$1} if (exists($defines{$1}));
            next;
        }
        if (m/^ignore\s+typedef\s+(\S+)/) {
            delete $typedefs{$1} if (exists($typedefs{$1}));
            next;
        }
        if (m/^ignore\s+enum\s+(\S+)/) {
            delete $enums{$1} if (exists($enums{$1}));
            next;
        }
        if (m/^ignore\s+struct\s+(\S+)/) {
            delete $structs{$1} if (exists($structs{$1}));
            next;
        }
        if (m/^ignore\s+symbol\s+(\S+)/) {
            delete $enum_symbols{$1} if (exists($enum_symbols{$1}));
            next;
        }

        # 解析替换符号
        my ($type, $old, $new, $reftype);

        if (m/^replace\s+(\S+)\s+(\S+)\s+(\S+)/) {
            $type = $1;
            $old = $2;
            $new = $3;
        } else {
            die "无法解析 $file_exceptions: $_";
        }

        if ($new =~ m/^\:c\:(data|func|macro|type)\:\`(.+)\`/) {
            $reftype = ":c:$1";
            $new = $2;
        } elsif ($new =~ m/\:ref\:\`(.+)\`/) {
            $reftype = ":ref";
            $new = $1;
        } else {
            $reftype = $def_reftype{$type};
        }
        $new = "$reftype:`$old <$new}`";

        if ($type eq "ioctl") {
            $ioctls{$old} = $new if (exists($ioctls{$old}));
            next;
        }
        if ($type eq "define") {
            $defines{$old} = $new if (exists($defines{$old}));
            next;
        }
        if ($type eq "symbol") {
            $enum_symbols{$old} = $new if (exists($enum_symbols{$old}));
            next;
        }
        if ($type eq "typedef") {
            $typedefs{$old} = $new if (exists($typedefs{$old}));
            next;
        }
        if ($type eq "enum") {
            $enums{$old} = $new if (exists($enums{$old}));
            next;
        }
        if ($type eq "struct") {
            $structs{$old} = $new if (exists($structs{$old}));
            next;
        }

        die "无法解析 $file_exceptions: $_";
    }
}

if ($debug) {
    print Data::Dumper->Dump([\%ioctls], [qw(*ioctls)]) if (%ioctls);
    print Data::Dumper->Dump([\%typedefs], [qw(*typedefs)]) if (%typedefs);
    print Data::Dumper->Dump([\%enums], [qw(*enums)]) if (%enums);
    print Data::Dumper->Dump([\%structs], [qw(*structs)]) if (%structs);
    print Data::Dumper->Dump([\%defines], [qw(*defines)]) if (%defines);
    print Data::Dumper->Dump([\%enum_symbols], [qw(*enum_symbols)]) if (%enum_symbols);
}

#
# 对齐块
#
$data = expand($data);
$data = "    " . $data;
$data =~ s/\n/\n    /g;
$data =~ s/\n\s+$/\n/g;
$data =~ s/\n\s+\n/\n\n/g;

#
# 添加特殊字符的转义码
#
$data =~ s,([\_\`\*\<\>\&\\\\:\/\|\%\$\#\{\}\~\^]),\\$1,g;

$data =~ s,DEPRECATED,**DEPRECATED**,g;

#
# 添加引用
#

my $start_delim = "[ \n\t\(\=\*\@]";
my $end_delim = "(\\s|,|\\\\=|\\\\:|\\;|\\\)|\\}|\\{)";

foreach my $r (keys %ioctls) {
    my $s = $ioctls{$r};

    $r =~ s,([\_\`\*\<\>\&\\\\:\/]),\\\\$1,g;

    print "$r -> $s\n" if ($debug);

    $data =~ s/($start_delim)($r)$end_delim/$1$s$3/g;
}

foreach my $r (keys %defines) {
    my $s = $defines{$r};

    $r =~ s,([\_\`\*\<\>\&\\\\:\/]),\\\\$1,g;

    print "$r -> $s\n" if ($debug);

    $data =~ s/($start_delim)($r)$end_delim/$1$s$3/g;
}

foreach my $r (keys %enum_symbols) {
    my $s = $enum_symbols{$r};

    $r =~ s,([\_\`\*\<\>\&\\\\:\/]),\\\\$1,g;

    print "$r -> $s\n" if ($debug);

    $data =~ s/($start_delim)($r)$end_delim/$1$s$3/g;
}

foreach my $r (keys %enums) {
    my $s = $enums{$r};

    $r =~ s,([\_\`\*\<\>\&\\\\:\/]),\\\\$1,g;

    print "$r -> $s\n" if ($debug);

    $data =~ s/enum\s+($r)$end_delim/$s$2/g;
}

foreach my $r (keys %structs) {
    my $s = $structs{$r};

    $r =~ s,([\_\`\*\<\>\&\\\\:\/]),\\\\$1,g;

    print "$r -> $s\n" if ($debug);

    $data =~ s/struct\s+($r)$end_delim/$s$2/g;
}

foreach my $r (keys %typedefs) {
    my $s = $typedefs{$r};

    $r =~ s,([\_\`\*\<\>\&\\\\:\/]),\\\\$1,g;

    print "$r -> $s\n" if ($debug);
    $data =~ s/($start_delim)($r)$end_delim/$1$s$3/g;
}

$data =~ s/\\ ([\n\s])/\1/g;

#
# 生成输出文件
#

my $title = $file_in;
$title =~ s,.*/,,;

open OUT, "> $file_out" or die "无法打开 $file_out";
print OUT ".. -*- coding: utf-8; mode: rst -*-\n\n";
print OUT "$title\n";
print OUT "=" x length($title);
print OUT "\n\n.. parsed-literal::\n\n";
print OUT $data;
close OUT;

__END__

=head1 NAME

parse_headers.pl - 解析 C 文件以识别函数、结构体、枚举和宏定义，并创建指向 Sphinx 文档的交叉引用
=head1 SYNOPSIS

B<parse_headers.pl> [<options>] <C_FILE> <OUT_FILE> [<EXCEPTIONS_FILE>]

其中 <options> 可以是：--debug, --help 或 --usage
=head1 OPTIONS

=over 8

=item B<--debug>

使脚本进入详细模式，便于调试
=item B<--usage>

打印简要的帮助信息并退出
=item B<--help>

打印更详细的帮助信息并退出
=back

=head1 DESCRIPTION

将 C 头文件或源文件（C_FILE）转换为包含交叉引用的 ReStructured Text，用于描述 API 的文档文件。可以接受一个可选的 EXCEPTIONS_FILE 来描述哪些元素将被忽略或指向非默认引用。
输出写入 (OUT_FILE)。
它可以识别宏定义、函数、结构体、类型定义、枚举和枚举符号，并为它们创建交叉引用。
它还能够区分用于指定 Linux ioctl 的 #define。
EXCEPTIONS_FILE 包含两条规则，允许忽略符号或将默认引用替换为自定义引用。
```
请在内核源码树中的 `Documentation/doc-guide/parse-headers.rst` 查阅更多详细信息。

=head1 问题报告

请将问题报告给 Mauro Carvalho Chehab <mchehab@kernel.org>

=head1 版权

版权所有 (c) 2016 Mauro Carvalho Chehab <mchehab+samsung@kernel.org>
许可证：GPLv2：GNU通用公共许可证第2版 <https://gnu.org/licenses/gpl.html>
这是自由软件，您可以自由修改和分发它
在法律允许的范围内，没有任何保修
=cut
