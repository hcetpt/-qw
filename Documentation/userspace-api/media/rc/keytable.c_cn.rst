```plaintext
SPDX 许可证标识符: GPL-2.0 或 GFDL-1.1 无不变部分或更高版本

文件: uapi/v4l/keytable.c
=========================

.. code-block:: c

    /* keytable.c - 此程序允许在红外线接口检查/替换按键

       版权所有 (C) 2006-2009 Mauro Carvalho Chehab <mchehab@kernel.org>

       本程序是自由软件；您可以根据自由软件基金会发布的 GNU 通用公共许可证的第 2 版重新分发和/或修改它。
       本程序按“原样”提供，不附带任何形式的保证，包括适销性和适用于特定目的的隐含保证。详见 GNU 通用公共许可证。
*/

    #include <ctype.h>
    #include <errno.h>
    #include <fcntl.h>
    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>
    #include <linux/input.h>
    #include <sys/ioctl.h>

    #include "parse.h"

    void prtcode (int *codes)
    {
	    struct parse_key *p;

	    for (p=keynames; p->name!=NULL; p++) {
		    if (p->value == (unsigned)codes[1]) {
			    printf("扫描码 0x%04x = %s (0x%02x)\\n", codes[0], p->name, codes[1]);
			    return;
		    }
	    }

	    if (isprint (codes[1]))
		    printf("扫描码 %d = '%c' (0x%02x)\\n", codes[0], codes[1], codes[1]);
	    else
		    printf("扫描码 %d = 0x%02x\\n", codes[0], codes[1]);
    }

    int parse_code(char *string)
    {
	    struct parse_key *p;

	    for (p=keynames; p->name!=NULL; p++) {
		    if (!strcasecmp(p->name, string)) {
			    return p->value;
		    }
	    }
	    return -1;
    }

    int main (int argc, char *argv[])
    {
	    int fd;
	    unsigned int i, j;
	    int codes[2];

	    if (argc<2 || argc>4) {
		    printf ("用法: %s <设备> 获取表；或者\\n"
			    "       %s <设备> <扫描码> <键码>\\n"
			    "       %s <设备> <键码文件>n", *argv, *argv, *argv);
		    return -1;
	    }

	    if ((fd = open(argv[1], O_RDONLY)) < 0) {
		    perror("无法打开输入设备");
		    return(-1);
	    }

	    if (argc==4) {
		    int value;

		    value=parse_code(argv[3]);

		    if (value==-1) {
			    value = strtol(argv[3], NULL, 0);
			    if (errno)
				    perror("值");
		    }

		    codes [0] = (unsigned) strtol(argv[2], NULL, 0);
		    codes [1] = (unsigned) value;

		    if(ioctl(fd, EVIOCSKEYCODE, codes))
			    perror ("EVIOCSKEYCODE");

		    if(ioctl(fd, EVIOCGKEYCODE, codes)==0)
			    prtcode(codes);
		    return 0;
	    }

	    if (argc==3) {
		    FILE *fin;
		    int value;
		    char *scancode, *keycode, s[2048];

		    fin=fopen(argv[2],"r");
		    if (fin==NULL) {
			    perror ("打开键码文件失败");
			    return -1;
		    }

		    /* 清除旧表 */
		    for (j = 0; j < 256; j++) {
			    for (i = 0; i < 256; i++) {
				    codes[0] = (j << 8) | i;
				    codes[1] = KEY_RESERVED;
				    ioctl(fd, EVIOCSKEYCODE, codes);
			    }
		    }

		    while (fgets(s, sizeof(s), fin)) {
			    scancode=strtok(s, "\\n\\t =:");
			    if (!scancode) {
				    perror ("解析输入文件中的扫描码失败");
				    return -1;
			    }
			    if (!strcasecmp(scancode, "扫描码")) {
				    scancode = strtok(NULL, "\\n\\t =:");
				    if (!scancode) {
					    perror ("解析输入文件中的扫描码失败");
					    return -1;
				    }
			    }

			    keycode=strtok(NULL, "\\n\\t =:");
			    if (!keycode) {
				    perror ("解析输入文件中的键码失败");
				    return -1;
			    }

			    // printf ("解析 %s=%s:", scancode, keycode);
			    value=parse_code(keycode);
			    // printf ("\\tvalue=%d\\n",value);

			    if (value==-1) {
				    value = strtol(keycode, NULL, 0);
				    if (errno)
					    perror("值");
			    }

			    codes [0] = (unsigned) strtol(scancode, NULL, 0);
			    codes [1] = (unsigned) value;

			    // printf("\\t%04x=%04x\\n",codes[0], codes[1]);
			    if(ioctl(fd, EVIOCSKEYCODE, codes)) {
				    fprintf(stderr, "设置扫描码 0x%04x 为 0x%04x 失败 ",codes[0], codes[1]);
				    perror ("EVIOCSKEYCODE");
			    }

			    if(ioctl(fd, EVIOCGKEYCODE, codes)==0)
				    prtcode(codes);
		    }
		    return 0;
	    }

	    /* 获取扫描码表 */
	    for (j = 0; j < 256; j++) {
		    for (i = 0; i < 256; i++) {
			    codes[0] = (j << 8) | i;
			    if (!ioctl(fd, EVIOCGKEYCODE, codes) && codes[1] != KEY_RESERVED)
				    prtcode(codes);
		    }
	    }
	    return 0;
    }
```
