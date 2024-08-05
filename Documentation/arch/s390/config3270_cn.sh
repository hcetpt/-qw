```bash
#!/bin/sh
#
# config3270 -- 自动配置 /dev/3270/* 和 /etc/inittab
#
#       使用方法:
#               config3270
#
#       输出文件:
#               /tmp/mkdev3270
#
#       操作步骤:
#               1. 运行此脚本
#               2. 运行它生成的脚本: /tmp/mkdev3270
#               3. 发出 "telinit q" 或者重启系统，根据需要
#

P=/proc/tty/driver/tty3270
ROOT=
D=$ROOT/dev
SUBD=3270
TTY=$SUBD/tty
TUB=$SUBD/tub
SCR=$ROOT/tmp/mkdev3270
SCRTMP=$SCR.a
GETTYLINE=:2345:respawn:/sbin/mingetty
INITTAB=$ROOT/etc/inittab
NINITTAB=$ROOT/etc/NEWinittab
OINITTAB=$ROOT/etc/OLDinittab
ADDNOTE="\# 为 3270/tty* 驱动程序添加的额外 mingetty 行, tub3270 ---"

if ! ls $P > /dev/null 2>&1; then
	modprobe tub3270 > /dev/null 2>&1
fi
ls $P > /dev/null 2>&1 || exit 1

# 初始化两个文件，一个用于 /dev/3270 命令，另一个用于替换 /etc/inittab 文件（旧文件保存在 OLDinittab 中）
echo "#!/bin/sh" > $SCR || exit 1
echo " " >> $SCR
echo "# 由 /sbin/config3270 构建的脚本" >> $SCR
if [ ! -d /dev/dasd ]; then
	echo rm -rf "$D/$SUBD/*" >> $SCR
fi
echo "grep -v $TTY $INITTAB > $NINITTAB" > $SCRTMP || exit 1
echo "echo $ADDNOTE >> $NINITTAB" >> $SCRTMP
if [ ! -d /dev/dasd ]; then
	echo mkdir -p $D/$SUBD >> $SCR
fi

# 现在查询 tub3270 驱动程序以获取 3270 设备信息
# 并向我们的文件中添加适当的 mknod 和 mingetty 行
echo what=config > $P
while read devno maj min;do
	if [ $min = 0 ]; then
		fsmaj=$maj
		if [ ! -d /dev/dasd ]; then
			echo mknod $D/$TUB c $fsmaj 0 >> $SCR
			echo chmod 666 $D/$TUB >> $SCR
		fi
	elif [ $maj = CONSOLE ]; then
		if [ ! -d /dev/dasd ]; then
			echo mknod $D/$TUB$devno c $fsmaj $min >> $SCR
		fi
	else
		if [ ! -d /dev/dasd ]; then
			echo mknod $D/$TTY$devno c $maj $min >>$SCR
			echo mknod $D/$TUB$devno c $fsmaj $min >> $SCR
		fi
		echo "echo t$min$GETTYLINE $TTY$devno >> $NINITTAB" >> $SCRTMP
	fi
done < $P

echo mv $INITTAB $OINITTAB >> $SCRTMP || exit 1
echo mv $NINITTAB $INITTAB >> $SCRTMP
cat $SCRTMP >> $SCR
rm $SCRTMP
exit 0
```
```
