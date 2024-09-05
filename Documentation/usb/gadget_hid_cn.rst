Linux USB HID 设备驱动程序
===========================

简介
============

HID 设备驱动程序提供了 USB 人机接口设备（HID）的仿真功能。基本的 HID 处理在内核中完成，通过 `/dev/hidgX` 字符设备进行 I/O 操作可以发送和接收 HID 报告。关于 HID 的更多详细信息，请参阅 https://www.usb.org/developers/hidpage/ 上的开发者页面。

配置
=============

`g_hid` 是一个平台驱动程序，因此要使用它，需要在您的平台代码中添加 `struct platform_device` 定义您想要使用的 HID 功能描述符。例如：

```c
#include <linux/platform_device.h>
#include <linux/usb/g_hid.h>

/* 用于键盘的 HID 描述符 */
static struct hidg_func_descriptor my_hid_data = {
	.subclass		= 0, /* 无子类 */
	.protocol		= 1, /* 键盘 */
	.report_length		= 8,
	.report_desc_length	= 63,
	.report_desc		= {
		0x05, 0x01,	/* USAGE_PAGE (通用桌面) */
		0x09, 0x06,	/* USAGE (键盘) */
		0xa1, 0x01,	/* COLLECTION (应用) */
		0x05, 0x07,	/*   USAGE_PAGE (键盘) */
		0x19, 0xe0,	/*   USAGE_MINIMUM (键盘左Ctrl) */
		0x29, 0xe7,	/*   USAGE_MAXIMUM (键盘右GUI) */
		0x15, 0x00,	/*   LOGICAL_MINIMUM (0) */
		0x25, 0x01,	/*   LOGICAL_MAXIMUM (1) */
		0x75, 0x01,	/*   REPORT_SIZE (1) */
		0x95, 0x08,	/*   REPORT_COUNT (8) */
		0x81, 0x02,	/*   INPUT (数据,变,绝对) */
		0x95, 0x01,	/*   REPORT_COUNT (1) */
		0x75, 0x08,	/*   REPORT_SIZE (8) */
		0x81, 0x03,	/*   INPUT (常量,变,绝对) */
		0x95, 0x05,	/*   REPORT_COUNT (5) */
		0x75, 0x01,	/*   REPORT_SIZE (1) */
		0x05, 0x08,	/*   USAGE_PAGE (LEDs) */
		0x19, 0x01,	/*   USAGE_MINIMUM (数字锁定) */
		0x29, 0x05,	/*   USAGE_MAXIMUM (Kana) */
		0x91, 0x02,	/*   OUTPUT (数据,变,绝对) */
		0x95, 0x01,	/*   REPORT_COUNT (1) */
		0x75, 0x03,	/*   REPORT_SIZE (3) */
		0x91, 0x03,	/*   OUTPUT (常量,变,绝对) */
		0x95, 0x06,	/*   REPORT_COUNT (6) */
		0x75, 0x08,	/*   REPORT_SIZE (8) */
		0x15, 0x00,	/*   LOGICAL_MINIMUM (0) */
		0x25, 0x65,	/*   LOGICAL_MAXIMUM (101) */
		0x05, 0x07,	/*   USAGE_PAGE (键盘) */
		0x19, 0x00,	/*   USAGE_MINIMUM (保留) */
		0x29, 0x65,	/*   USAGE_MAXIMUM (键盘应用) */
		0x81, 0x00,	/*   INPUT (数据,数组,绝对) */
		0xc0		/* END_COLLECTION */
	}
};

static struct platform_device my_hid = {
	.name			= "hidg",
	.id			= 0,
	.num_resources		= 0,
	.resource		= 0,
	.dev.platform_data	= &my_hid_data,
};
```

您可以添加尽可能多的 HID 功能，仅受限于您的设备驱动程序支持的中断端点数量。

使用 configfs 进行配置
===========================

除了通过添加假的平台设备和驱动程序来向内核传递一些数据外，如果 HID 是使用 configfs 组合的设备的一部分，则可以通过将相应的字节流写入 configfs 属性来将 `hidg_func_descriptor.report_desc` 传递给内核。

发送和接收 HID 报告
============================

HID 报告可以通过对 `/dev/hidgX` 字符设备执行读/写操作来发送和接收。下面是一个示例程序：

`hid_gadget_test` 是一个小的交互式程序，用于测试 HID 设备驱动程序。使用时，指向一个 `hidg` 设备并设置设备类型（键盘/鼠标/游戏杆）。例如：

```
# hid_gadget_test /dev/hidg0 keyboard
```

现在您处于 `hid_gadget_test` 的提示符下。您可以输入任意组合的选项和值。可用的选项和值会在程序启动时列出。在键盘模式下，您可以发送最多六个值。
例如，输入：`g i s t r --left-shift`

按回车键后，相应的报告将由 HID 设备发送出去。
另一个有趣的例子是大写锁定测试。输入 `--caps-lock` 并按回车键。然后会发送一个报告，并且您应该接收到主机的响应，该响应对应于大写锁定 LED 状态：

```
--caps-lock
recv report:2
```

使用此命令：

```
# hid_gadget_test /dev/hidg1 mouse
```

您可以测试鼠标仿真。值是两个有符号数。

示例代码：
```c
/* hid_gadget_test */

#include <pthread.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define BUF_LEN 512

struct options {
	const char    *opt;
	unsigned char val;
};

static struct options kmod[] = {
	{.opt = "--left-ctrl",		.val = 0x01},
	{.opt = "--right-ctrl",		.val = 0x10},
	{.opt = "--left-shift",		.val = 0x02},
	{.opt = "--right-shift",	.val = 0x20},
	{.opt = "--left-alt",		.val = 0x04},
	{.opt = "--right-alt",		.val = 0x40},
	{.opt = "--left-meta",		.val = 0x08},
	{.opt = "--right-meta",		.val = 0x80},
	{.opt = NULL}
};

static struct options kval[] = {
	{.opt = "--return",	.val = 0x28},
	{.opt = "--esc",	.val = 0x29},
	{.opt = "--bckspc",	.val = 0x2a},
	{.opt = "--tab",	.val = 0x2b},
	{.opt = "--spacebar",	.val = 0x2c},
	{.opt = "--caps-lock",	.val = 0x39},
	{.opt = "--f1",		.val = 0x3a},
	{.opt = "--f2",		.val = 0x3b},
	{.opt = "--f3",		.val = 0x3c},
	{.opt = "--f4",		.val = 0x3d},
	{.opt = "--f5",		.val = 0x3e},
	{.opt = "--f6",		.val = 0x3f},
	{.opt = "--f7",		.val = 0x40},
	{.opt = "--f8",		.val = 0x41},
	{.opt = "--f9",		.val = 0x42},
	{.opt = "--f10",	.val = 0x43},
	{.opt = "--f11",	.val = 0x44},
	{.opt = "--f12",	.val = 0x45},
	{.opt = "--insert",	.val = 0x49},
	{.opt = "--home",	.val = 0x4a},
	{.opt = "--pageup",	.val = 0x4b},
	{.opt = "--del",	.val = 0x4c},
	{.opt = "--end",	.val = 0x4d},
	{.opt = "--pagedown",	.val = 0x4e},
	{.opt = "--right",	.val = 0x4f},
	{.opt = "--left",	.val = 0x50},
	{.opt = "--down",	.val = 0x51},
	{.opt = "--kp-enter",	.val = 0x58},
	{.opt = "--up",		.val = 0x52},
	{.opt = "--num-lock",	.val = 0x53},
	{.opt = NULL}
};

int keyboard_fill_report(char report[8], char buf[BUF_LEN], int *hold)
{
	char *tok = strtok(buf, " ");
	int key = 0;
	int i = 0;

	for (; tok != NULL; tok = strtok(NULL, " ")) {

		if (strcmp(tok, "--quit") == 0)
			return -1;

		if (strcmp(tok, "--hold") == 0) {
			*hold = 1;
			continue;
		}

		if (key < 6) {
			for (i = 0; kval[i].opt != NULL; i++)
				if (strcmp(tok, kval[i].opt) == 0) {
					report[2 + key++] = kval[i].val;
					break;
				}
			if (kval[i].opt != NULL)
				continue;
		}

		if (key < 6)
			if (islower(tok[0])) {
				report[2 + key++] = (tok[0] - ('a' - 0x04));
				continue;
			}

		for (i = 0; kmod[i].opt != NULL; i++)
			if (strcmp(tok, kmod[i].opt) == 0) {
				report[0] = report[0] | kmod[i].val;
				break;
			}
		if (kmod[i].opt != NULL)
			continue;

		if (key < 6)
			fprintf(stderr, "unknown option: %s\n", tok);
	}
	return 8;
}

static struct options mmod[] = {
	{.opt = "--b1", .val = 0x01},
	{.opt = "--b2", .val = 0x02},
	{.opt = "--b3", .val = 0x04},
	{.opt = NULL}
};

int mouse_fill_report(char report[8], char buf[BUF_LEN], int *hold)
{
	char *tok = strtok(buf, " ");
	int mvt = 0;
	int i = 0;
	for (; tok != NULL; tok = strtok(NULL, " ")) {

		if (strcmp(tok, "--quit") == 0)
			return -1;

		if (strcmp(tok, "--hold") == 0) {
			*hold = 1;
			continue;
		}

		for (i = 0; mmod[i].opt != NULL; i++)
			if (strcmp(tok, mmod[i].opt) == 0) {
				report[0] = report[0] | mmod[i].val;
				break;
			}
		if (mmod[i].opt != NULL)
			continue;

		if (!(tok[0] == '-' && tok[1] == '-') && mvt < 2) {
			errno = 0;
			report[1 + mvt++] = (char)strtol(tok, NULL, 0);
			if (errno != 0) {
				fprintf(stderr, "Bad value:'%s'\n", tok);
				report[1 + mvt--] = 0;
			}
			continue;
		}

		fprintf(stderr, "unknown option: %s\n", tok);
	}
	return 3;
}

static struct options jmod[] = {
	{.opt = "--b1",		.val = 0x10},
	{.opt = "--b2",		.val = 0x20},
	{.opt = "--b3",		.val = 0x40},
	{.opt = "--b4",		.val = 0x80},
	{.opt = "--hat1",	.val = 0x00},
	{.opt = "--hat2",	.val = 0x01},
	{.opt = "--hat3",	.val = 0x02},
	{.opt = "--hat4",	.val = 0x03},
	{.opt = "--hatneutral",	.val = 0x04},
	{.opt = NULL}
};

int joystick_fill_report(char report[8], char buf[BUF_LEN], int *hold)
{
	char *tok = strtok(buf, " ");
	int mvt = 0;
	int i = 0;

	*hold = 1;

	/* 设置默认摇杆位置：中立 */
	report[3] = 0x04;

	for (; tok != NULL; tok = strtok(NULL, " ")) {

		if (strcmp(tok, "--quit") == 0)
			return -1;

		for (i = 0; jmod[i].opt != NULL; i++)
			if (strcmp(tok, jmod[i].opt) == 0) {
				report[3] = (report[3] & 0xF0) | jmod[i].val;
				break;
			}
		if (jmod[i].opt != NULL)
			continue;

		if (!(tok[0] == '-' && tok[1] == '-') && mvt < 3) {
			errno = 0;
			report[mvt++] = (char)strtol(tok, NULL, 0);
			if (errno != 0) {
				fprintf(stderr, "Bad value:'%s'\n", tok);
				report[mvt--] = 0;
			}
			continue;
		}

		fprintf(stderr, "unknown option: %s\n", tok);
	}
	return 4;
}

void print_options(char c)
{
	int i = 0;

	if (c == 'k') {
		printf("	keyboard options:\n"
		       "		--hold\n");
		for (i = 0; kmod[i].opt != NULL; i++)
			printf("\t\t%s\n", kmod[i].opt);
		printf("\n	keyboard values:\n"
		       "		[a-z] or\n");
		for (i = 0; kval[i].opt != NULL; i++)
			printf("\t\t%-8s%s", kval[i].opt, i % 2 ? "\n" : "");
		printf("\n");
	} else if (c == 'm') {
		printf("	mouse options:\n"
		       "		--hold\n");
		for (i = 0; mmod[i].opt != NULL; i++)
			printf("\t\t%s\n", mmod[i].opt);
		printf("\n	mouse values:\n"
		       "		Two signed numbers\n"
		       "--quit to close\n");
	} else {
		printf("	joystick options:\n");
		for (i = 0; jmod[i].opt != NULL; i++)
			printf("\t\t%s\n", jmod[i].opt);
		printf("\n	joystick values:\n"
		       "		three signed numbers\n"
		       "--quit to close\n");
	}
}

int main(int argc, const char *argv[])
{
	const char *filename = NULL;
	int fd = 0;
	char buf[BUF_LEN];
	int cmd_len;
	char report[8];
	int to_send = 8;
	int hold = 0;
	fd_set rfds;
	int retval, i;

	if (argc < 3) {
		fprintf(stderr, "Usage: %s devname mouse|keyboard|joystick\n",
			argv[0]);
		return 1;
	}

	if (argv[2][0] != 'k' && argv[2][0] != 'm' && argv[2][0] != 'j')
		return 2;

	filename = argv[1];

	if ((fd = open(filename, O_RDWR, 0666)) == -1) {
		perror(filename);
		return 3;
	}

	print_options(argv[2][0]);

	while (42) {

		FD_ZERO(&rfds);
		FD_SET(STDIN_FILENO, &rfds);
		FD_SET(fd, &rfds);

		retval = select(fd + 1, &rfds, NULL, NULL, NULL);
		if (retval == -1 && errno == EINTR)
			continue;
		if (retval < 0) {
			perror("select()");
			return 4;
		}

		if (FD_ISSET(fd, &rfds)) {
			cmd_len = read(fd, buf, BUF_LEN - 1);
			printf("recv report:");
			for (i = 0; i < cmd_len; i++)
				printf(" %02x", buf[i]);
			printf("\n");
		}

		if (FD_ISSET(STDIN_FILENO, &rfds)) {
			memset(report, 0x0, sizeof(report));
			cmd_len = read(STDIN_FILENO, buf, BUF_LEN - 1);

			if (cmd_len == 0)
				break;

			buf[cmd_len - 1] = '\0';
			hold = 0;

			memset(report, 0x0, sizeof(report));
			if (argv[2][0] == 'k')
				to_send = keyboard_fill_report(report, buf, &hold);
			else if (argv[2][0] == 'm')
				to_send = mouse_fill_report(report, buf, &hold);
			else
				to_send = joystick_fill_report(report, buf, &hold);

			if (to_send == -1)
				break;

			if (write(fd, report, to_send) != to_send) {
				perror(filename);
				return 5;
			}
			if (!hold) {
				memset(report, 0x0, sizeof(report));
				if (write(fd, report, to_send) != to_send) {
					perror(filename);
					return 6;
				}
			}
		}
	}

	close(fd);
	return 0;
}
```
