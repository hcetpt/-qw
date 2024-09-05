理解 fbdev 的 cmap
==========================

这些笔记解释了 X 的 dix 层如何使用 fbdev 的 cmap 结构。

- 以下是 fbdev 中用于 3 位灰度 cmap 的相关结构示例：

```c
struct fb_var_screeninfo {
	.bits_per_pixel = 8,
	.grayscale = 1,
	.red = { 4, 3, 0 },
	.green = { 0, 0, 0 },
	.blue = { 0, 0, 0 },
}
struct fb_fix_screeninfo {
	.visual = FB_VISUAL_STATIC_PSEUDOCOLOR,
}
for (i = 0; i < 8; i++) {
	info->cmap.red[i] = (((2 * i) + 1) * (0xFFFF)) / 16;
}
memcpy(info->cmap.green, info->cmap.red, sizeof(u16) * 8);
memcpy(info->cmap.blue, info->cmap.red, sizeof(u16) * 8);
```

- 当 X11 应用程序尝试使用灰度时，通常会执行以下类似的操作：

```c
for (i = 0; i < 8; i++) {
	char colorspec[64];
	memset(colorspec, 0, 64);
	sprintf(colorspec, "rgb:%x/%x/%x", i * 36, i * 36, i * 36);
	if (!XParseColor(outputDisplay, testColormap, colorspec, &wantedColor))
		printf("Can't get color %s\n", colorspec);
	XAllocColor(outputDisplay, testColormap, &wantedColor);
	grays[i] = wantedColor;
}
```

此外，还可以使用诸如 gray1..x 这样的命名等价项，只要你有 rgb.txt 文件。在 X 的调用链的某个地方，这将导致调用处理颜色映射的 X 代码。例如，Xfbdev 会触发以下代码：

`xc-011010/programs/Xserver/dix/colormap.c`：

```c
FindBestPixel(pentFirst, size, prgb, channel)

dr = (long) pent->co.local.red - prgb->red;
dg = (long) pent->co.local.green - prgb->green;
db = (long) pent->co.local.blue - prgb->blue;
sq = dr * dr;
UnsignedToBigNum (sq, &sum);
BigNumAdd (&sum, &temp, &sum);
```

`co.local.red` 是通过 `FBIOGETCMAP` 获取的条目，直接来自上面列出的 `info->cmap.red`。`prgb` 是应用程序希望匹配的颜色值。上述代码看起来像是最小二乘匹配函数。这就是为什么 cmap 条目不能设置为颜色范围的左侧边界的原因。
