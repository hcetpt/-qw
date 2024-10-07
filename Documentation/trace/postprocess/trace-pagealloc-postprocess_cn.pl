```perl
#!/usr/bin/env perl
# 这是一个POC（概念验证或垃圾代码，任选其一）用于读取与页面分配相关的跟踪输出的文本表示。它尝试提取一些高层次的信息以了解正在发生的情况。解析器的准确性可能会有所不同。
#
# 示例用法: trace-pagealloc-postprocess.pl < /sys/kernel/tracing/trace_pipe
# 其他选项
#   --prepend-parent	报告父进程及其PID
#   --read-procstat	如果跟踪记录缺少进程信息，则从 /proc 获取
#   --ignore-pid	将相同名称的进程汇总在一起
#
# 版权所有 © 2009 IBM公司
# 作者: Mel Gorman <mel@csn.ul.ie>
use strict;
use Getopt::Long;

# 跟踪点事件
use constant MM_PAGE_ALLOC		=> 1;
use constant MM_PAGE_FREE		=> 2;
use constant MM_PAGE_FREE_BATCHED	=> 3;
use constant MM_PAGE_PCPU_DRAIN		=> 4;
use constant MM_PAGE_ALLOC_ZONE_LOCKED	=> 5;
use constant MM_PAGE_ALLOC_EXTFRAG	=> 6;
use constant EVENT_UNKNOWN		=> 7;

# 用于跟踪状态的常量
use constant STATE_PCPU_PAGES_DRAINED	=> 8;
use constant STATE_PCPU_PAGES_REFILLED	=> 9;

# 从跟踪点推断出的高层次事件
use constant HIGH_PCPU_DRAINS		=> 10;
use constant HIGH_PCPU_REFILLS		=> 11;
use constant HIGH_EXT_FRAGMENT		=> 12;
use constant HIGH_EXT_FRAGMENT_SEVERE	=> 13;
use constant HIGH_EXT_FRAGMENT_MODERATE	=> 14;
use constant HIGH_EXT_FRAGMENT_CHANGED	=> 15;

my %perprocesspid;
my %perprocess;
my $opt_ignorepid;
my $opt_read_procstat;
my $opt_prepend_parent;

# 捕获SIGINT并根据请求退出
my $sigint_report = 0;
my $sigint_exit = 0;
my $sigint_pending = 0;
my $sigint_received = 0;
sub sigint_handler {
	my $current_time = time;
	if ($current_time - 2 > $sigint_received) {
		print "SIGINT 收到，报告待处理。再次按 Ctrl-C 退出\n";
		$sigint_report = 1;
	} else {
		if (!$sigint_exit) {
			print "短时间内收到第二次 SIGINT，退出\n";
		}
		$sigint_exit++;
	}

	if ($sigint_exit > 3) {
		print "收到多次 SIGINT，现在不生成报告直接退出\n";
		exit;
	}

	$sigint_received = $current_time;
	$sigint_pending = 1;
}
$SIG{INT} = "sigint_handler";

# 解析命令行选项
GetOptions(
	'ignore-pid'	 => \$opt_ignorepid,
	'read-procstat'	 => \$opt_read_procstat,
	'prepend-parent' => \$opt_prepend_parent,
);

# 动态发现的正则表达式默认值
my $regex_fragdetails_default = 'page=([0-9a-f]*) pfn=([0-9]*) alloc_order=([-0-9]*) fallback_order=([-0-9]*) pageblock_order=([-0-9]*) alloc_migratetype=([-0-9]*) fallback_migratetype=([-0-9]*) fragmenting=([-0-9]) change_ownership=([-0-9])';

# 动态发现的正则表达式
my $regex_fragdetails;

# 静态使用的正则表达式。这样指定是为了可读性和使用 /o
#                       (process_pid)     (cpus      )   (时间  )   (跟踪点    ) (详细信息)
my $regex_traceevent = '\s*([a-zA-Z0-9-]*)\s*(\[[0-9]*\])\s*([0-9.]*):\s*([a-zA-Z_]*):\s*(.*)';
my $regex_statname = '[-0-9]*\s\((.*)\).*';
my $regex_statppid = '[-0-9]*\s\(.*\)\s[A-Za-z]\s([0-9]*).*';

sub generate_traceevent_regex {
	my $event = shift;
	my $default = shift;
	my $regex;

	# 读取事件格式或使用默认值
	if (!open (FORMAT, "/sys/kernel/tracing/events/$event/format")) {
		$regex = $default;
	} else {
		my $line;
		while (!eof(FORMAT)) {
			$line = <FORMAT>;
			if ($line =~ /^print fmt:\s"(.*)",.*/) {
				$regex = $1;
				$regex =~ s/%p/\([0-9a-f]*\)/g;
				$regex =~ s/%d/\([-0-9]*\)/g;
				$regex =~ s/%lu/\([0-9]*\)/g;
			}
		}
	}

	# 验证字段是否按正确顺序排列
	my $tuple;
	foreach $tuple (split /\s/, $regex) {
		my ($key, $value) = split(/=/, $tuple);
		my $expected = shift;
		if ($key ne $expected) {
			print("警告: 格式不符合预期 '$key' != '$expected'");
			$regex =~ s/$key=\((.*)\)/$key=$1/;
		}
	}

	if (defined shift) {
		die("格式中的字段少于预期");
	}

	return $regex;
}
$regex_fragdetails = generate_traceevent_regex("kmem/mm_page_alloc_extfrag",
			$regex_fragdetails_default,
			"page", "pfn",
			"alloc_order", "fallback_order", "pageblock_order",
			"alloc_migratetype", "fallback_migratetype",
			"fragmenting", "change_ownership");

sub read_statline($) {
	my $pid = $_[0];
	my $statline;

	if (open(STAT, "/proc/$pid/stat")) {
		$statline = <STAT>;
		close(STAT);
	}

	if ($statline eq '') {
		$statline = "-1 (UNKNOWN_PROCESS_NAME) R 0";
	}

	return $statline;
}

sub guess_process_pid($$) {
	my $pid = $_[0];
	my $statline = $_[1];

	if ($pid == 0) {
		return "swapper-0";
	}

	if ($statline !~ /$regex_statname/o) {
		die("未能匹配进程名称的 stat 行 :: $statline");
	}
	return "$1-$pid";
}

sub parent_info($$) {
	my $pid = $_[0];
	my $statline = $_[1];
	my $ppid;

	if ($pid == 0) {
		return "NOPARENT-0";
	}

	if ($statline !~ /$regex_statppid/o) {
		die("未能匹配进程 ppid 的 stat 行 :: $statline");
	}

	# 读取ppid的stat行
	$ppid = $1;
	return guess_process_pid($ppid, read_statline($ppid));
}

sub process_events {
	my $traceevent;
	my $process_pid;
	my $cpus;
	my $timestamp;
	my $tracepoint;
	my $details;
	my $statline;

	# 逐行读取事件日志
	EVENT_PROCESS:
	while ($traceevent = <STDIN>) {
		if ($traceevent =~ /$regex_traceevent/o) {
			$process_pid = $1;
			$tracepoint = $4;

			if ($opt_read_procstat || $opt_prepend_parent) {
				$process_pid =~ /(.*)-([0-9]*)$/;
				my $process = $1;
				my $pid = $2;

				$statline = read_statline($pid);

				if ($opt_read_procstat && $process eq '') {
					$process_pid = guess_process_pid($pid, $statline);
				}

				if ($opt_prepend_parent) {
					$process_pid = parent_info($pid, $statline) . " :: $process_pid";
				}
			}

			# 在此脚本中是不必要的。如需使用请取消注释
			# $cpus = $2;
			# $timestamp = $3;
		} else {
			next;
		}

		# Perl的Switch()非常糟糕
		if ($tracepoint eq "mm_page_alloc") {
			$perprocesspid{$process_pid}->{MM_PAGE_ALLOC}++;
		} elsif ($tracepoint eq "mm_page_free") {
			$perprocesspid{$process_pid}->{MM_PAGE_FREE}++
		} elsif ($tracepoint eq "mm_page_free_batched") {
			$perprocesspid{$process_pid}->{MM_PAGE_FREE_BATCHED}++;
		} elsif ($tracepoint eq "mm_page_pcpu_drain") {
			$perprocesspid{$process_pid}->{MM_PAGE_PCPU_DRAIN}++;
			$perprocesspid{$process_pid}->{STATE_PCPU_PAGES_DRAINED}++;
		} elsif ($tracepoint eq "mm_page_alloc_zone_locked") {
			$perprocesspid{$process_pid}->{MM_PAGE_ALLOC_ZONE_LOCKED}++;
			$perprocesspid{$process_pid}->{STATE_PCPU_PAGES_REFILLED}++;
		} elsif ($tracepoint eq "mm_page_alloc_extfrag") {

			# 提取事件的详细信息
			$details = $5;

			my ($page, $pfn);
			my ($alloc_order, $fallback_order, $pageblock_order);
			my ($alloc_migratetype, $fallback_migratetype);
			my ($fragmenting, $change_ownership);

			if ($details !~ /$regex_fragdetails/o) {
				print "警告: 未能按预期解析 mm_page_alloc_extfrag\n";
				next;
			}

			$perprocesspid{$process_pid}->{MM_PAGE_ALLOC_EXTFRAG}++;
			$page = $1;
			$pfn = $2;
			$alloc_order = $3;
			$fallback_order = $4;
			$pageblock_order = $5;
			$alloc_migratetype = $6;
			$fallback_migratetype = $7;
			$fragmenting = $8;
			$change_ownership = $9;

			if ($fragmenting) {
				$perprocesspid{$process_pid}->{HIGH_EXT_FRAG}++;
				if ($fallback_order <= 3) {
					$perprocesspid{$process_pid}->{HIGH_EXT_FRAGMENT_SEVERE}++;
				} else {
					$perprocesspid{$process_pid}->{HIGH_EXT_FRAGMENT_MODERATE}++;
				}
			}
			if ($change_ownership) {
				$perprocesspid{$process_pid}->{HIGH_EXT_FRAGMENT_CHANGED}++;
			}
		} else {
			$perprocesspid{$process_pid}->{EVENT_UNKNOWN}++;
		}

		# 捕获完整的pcpu排空事件
		if ($perprocesspid{$process_pid}->{STATE_PCPU_PAGES_DRAINED} &&
				$tracepoint ne "mm_page_pcpu_drain") {

			$perprocesspid{$process_pid}->{HIGH_PCPU_DRAINS}++;
			$perprocesspid{$process_pid}->{STATE_PCPU_PAGES_DRAINED} = 0;
		}

		# 捕获完整的pcpu填充事件
		if ($perprocesspid{$process_pid}->{STATE_PCPU_PAGES_REFILLED} &&
				$tracepoint ne "mm_page_alloc_zone_locked") {
			$perprocesspid{$process_pid}->{HIGH_PCPU_REFILLS}++;
			$perprocesspid{$process_pid}->{STATE_PCPU_PAGES_REFILLED} = 0;
		}

		if ($sigint_pending) {
			last EVENT_PROCESS;
		}
	}
}

sub dump_stats {
	my $hashref = shift;
	my %stats = %$hashref;

	# 输出每个进程的统计信息
	my $process_pid;
	my $max_strlen = 0;

	# 获取最长的进程名称
	foreach $process_pid (keys %perprocesspid) {
		my $len = length($process_pid);
		if ($len > $max_strlen) {
			$max_strlen = $len;
		}
	}
	$max_strlen += 2;

	printf("\n");
	printf("%-" . $max_strlen . "s %8s %10s   %8s %8s   %8s %8s %8s   %8s %8s %8s %8s %8s %8s\n",
		"进程", "页面",  "页面",      "页面", "页面", "PCPU",  "PCPU",   "PCPU",    "碎片",  "碎片", "迁移类型", "严重碎片", "中等碎片", "未知");
	printf("%-" . $max_strlen . "s %8s %10s   %8s %8s   %8s %8s %8s   %8s %8s %8s %8s %8s %8s\n",
		"详细信息", "分配", "锁定下分配",     "释放", "页向量释放", "排空", "排空次数", "填充次数", "回退", "导致",   "更改", "严重", "中等", "");

	printf("%-" . $max_strlen . "s %8s %10s   %8s %8s   %8s %8s %8s   %8s %8s %8s %8s %8s %8s\n",
		"",        "",       "分配", "直接", "批量", "排空", "", "", "", "", "", "", "");

	foreach $process_pid (keys %stats) {
		# 输出最终汇总
		if ($stats{$process_pid}->{STATE_PCPU_PAGES_DRAINED}) {
			$stats{$process_pid}->{HIGH_PCPU_DRAINS}++;
			$stats{$process_pid}->{STATE_PCPU_PAGES_DRAINED} = 0;
		}
		if ($stats{$process_pid}->{STATE_PCPU_PAGES_REFILLED}) {
			$stats{$process_pid}->{HIGH_PCPU_REFILLS}++;
			$stats{$process_pid}->{STATE_PCPU_PAGES_REFILLED} = 0;
		}

		printf("%-" . $max_strlen . "s %8d %10d   %8d %8d   %8d %8d %8d   %8d %8d %8d %8d %8d %8d\n",
			$process_pid,
			$stats{$process_pid}->{MM_PAGE_ALLOC},
			$stats{$process_pid}->{MM_PAGE_ALLOC_ZONE_LOCKED},
			$stats{$process_pid}->{MM_PAGE_FREE},
			$stats{$process_pid}->{MM_PAGE_FREE_BATCHED},
			$stats{$process_pid}->{MM_PAGE_PCPU_DRAIN},
			$stats{$process_pid}->{HIGH_PCPU_DRAINS},
			$stats{$process_pid}->{HIGH_PCPU_REFILLS},
			$stats{$process_pid}->{MM_PAGE_ALLOC_EXTFRAG},
			$stats{$process_pid}->{HIGH_EXT_FRAG},
			$stats{$process_pid}->{HIGH_EXT_FRAGMENT_CHANGED},
			$stats{$process_pid}->{HIGH_EXT_FRAGMENT_SEVERE},
			$stats{$process_pid}->{HIGH_EXT_FRAGMENT_MODERATE},
			$stats{$process_pid}->{EVENT_UNKNOWN});
	}
}

sub aggregate_perprocesspid() {
	my $process_pid;
	my $process;
	undef %perprocess;

	foreach $process_pid (keys %perprocesspid) {
		$process = $process_pid;
		$process =~ s/-([0-9])*$//;
		if ($process eq '') {
			$process = "NO_PROCESS_NAME";
		}

		$perprocess{$process}->{MM_PAGE_ALLOC} += $perprocesspid{$process_pid}->{MM_PAGE_ALLOC};
		$perprocess{$process}->{MM_PAGE_ALLOC_ZONE_LOCKED} += $perprocesspid{$process_pid}->{MM_PAGE_ALLOC_ZONE_LOCKED};
		$perprocess{$process}->{MM_PAGE_FREE} += $perprocesspid{$process_pid}->{MM_PAGE_FREE};
		$perprocess{$process}->{MM_PAGE_FREE_BATCHED} += $perprocesspid{$process_pid}->{MM_PAGE_FREE_BATCHED};
		$perprocess{$process}->{MM_PAGE_PCPU_DRAIN} += $perprocesspid{$process_pid}->{MM_PAGE_PCPU_DRAIN};
		$perprocess{$process}->{HIGH_PCPU_DRAINS} += $perprocesspid{$process_pid}->{HIGH_PCPU_DRAINS};
		$perprocess{$process}->{HIGH_PCPU_REFILLS} += $perprocesspid{$process_pid}->{HIGH_PCPU_REFILLS};
		$perprocess{$process}->{MM_PAGE_ALLOC_EXTFRAG} += $perprocesspid{$process_pid}->{MM_PAGE_ALLOC_EXTFRAG};
		$perprocess{$process}->{HIGH_EXT_FRAG} += $perprocesspid{$process_pid}->{HIGH_EXT_FRAG};
		$perprocess{$process}->{HIGH_EXT_FRAGMENT_CHANGED} += $perprocesspid{$process_pid}->{HIGH_EXT_FRAGMENT_CHANGED};
		$perprocess{$process}->{HIGH_EXT_FRAGMENT_SEVERE} += $perprocesspid{$process_pid}->{HIGH_EXT_FRAGMENT_SEVERE};
		$perprocess{$process}->{HIGH_EXT_FRAGMENT_MODERATE} += $perprocesspid{$process_pid}->{HIGH_EXT_FRAGMENT_MODERATE};
		$perprocess{$process}->{EVENT_UNKNOWN} += $perprocesspid{$process_pid}->{EVENT_UNKNOWN};
	}
}

sub report() {
	if (!$opt_ignorepid) {
		dump_stats(\%perprocesspid);
	} else {
		aggregate_perprocesspid();
		dump_stats(\%perprocess);
	}
}

# 处理事件或信号直到两者都不可用
sub signal_loop() {
	my $sigint_processed;
	do {
		$sigint_processed = 0;
		process_events();

		# 如果有未处理的信号则处理
		if ($sigint_pending) {
			my $current_time = time;

			if ($sigint_exit) {
				print "收到退出信号\n";
				$sigint_pending = 0;
			}
			if ($sigint_report) {
				if ($current_time >= $sigint_received + 2) {
					report();
					$sigint_report = 0;
					$sigint_pending = 0;
					$sigint_processed = 1;
				}
			}
		}
	} while ($sigint_pending || $sigint_processed);
}

signal_loop();
report();
```
