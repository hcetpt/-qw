```sh
#!/bin/sh

# 打印出所需的 KASAN_SHADOW_OFFSETS，以便将 KASAN SHADOW 的起始地址放置在线性区域的顶部

print_kasan_offset () {
	printf "%02d\t" $1
	printf "0x%08x00000000\n" $(( (0xffffffff & (-1 << ($1 - 1 - 32))) \
			- (1 << (64 - 32 - $2)) ))
}

echo KASAN_SHADOW_SCALE_SHIFT = 3
printf "VABITS\tKASAN_SHADOW_OFFSET\n"
print_kasan_offset 48 3
print_kasan_offset 47 3
print_kasan_offset 42 3
print_kasan_offset 39 3
print_kasan_offset 36 3
echo
echo KASAN_SHADOW_SCALE_SHIFT = 4
printf "VABITS\tKASAN_SHADOW_OFFSET\n"
print_kasan_offset 48 4
print_kasan_offset 47 4
print_kasan_offset 42 4
print_kasan_offset 39 4
print_kasan_offset 36 4
```

这段脚本打印出不同的 `KASAN_SHADOW_OFFSET` 值，这些值用于将 KASAN SHADOW 的起始地址放置在内存线性区域的顶部。它通过定义一个函数 `print_kasan_offset` 来计算和打印这些值，并为两种不同的 `KASAN_SHADOW_SCALE_SHIFT`（3 和 4）调用该函数。
