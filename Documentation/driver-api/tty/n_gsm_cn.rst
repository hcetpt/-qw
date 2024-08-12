GSM 0710 多路复用器 HOWTO
==================================

.. contents:: 目录
   :local:

本行规程实现了以下 3GPP 文档中详述的 GSM 07.10 多路复用协议：

    https://www.3gpp.org/ftp/Specs/archive/07_series/07.10/0710-720.zip

本文档提供了一些如何使用该驱动程序与通过物理串口连接的 GPRS 和 3G 调制解调器的提示。
如何使用它
===========

配置发起者
-------------

#. 通过其串口初始化调制解调器到 0710 多路复用模式（通常为 `AT+CMUX=` 命令）。根据所使用的调制解调器，您可以向此命令传递或多或少的参数。
#. 通过使用 `TIOCSETD` ioctl 将串行线切换到使用 n_gsm 行规程。
#. 如果需要，使用 `GSMIOC_GETCONF_EXT`/`GSMIOC_SETCONF_EXT` ioctl 配置多路复用器。
#. 使用 `GSMIOC_GETCONF`/`GSMIOC_SETCONF` ioctl 配置多路复用器。
#. 对于非默认设置，使用 `GSMIOC_GETCONF_DLCI`/`GSMIOC_SETCONF_DLCI` ioctl 配置 DLC。
#. 获取用于串行端口的基本 gsmtty 号码。
初始化程序的主要部分
   （一个很好的起点是 util-linux-ng/sys-utils/ldattach.c）如下所示：

      #include <stdio.h>
      #include <stdint.h>
      #include <linux/gsmmux.h>
      #include <linux/tty.h>

      #define DEFAULT_SPEED B115200
      #define SERIAL_PORT /dev/ttyS0

      int ldisc = N_GSM0710;
      struct gsm_config c;
      struct gsm_config_ext ce;
      struct gsm_dlci_config dc;
      struct termios configuration;
      uint32_t first;

      /* 打开连接到调制解调器的串行端口 */
      fd = open(SERIAL_PORT, O_RDWR | O_NOCTTY | O_NDELAY);

      /* 配置串行端口：速度、流控制等 */

      /* 发送 AT 命令以将调制解调器切换到 CMUX 模式
         并检查是否成功（应返回 OK） */
      write(fd, "AT+CMUX=0\r", 10);

      /* 实验表明，某些调制解调器在能够回答第一个 MUX 数据包之前需要一些时间
         因此在某些情况下可能需要延迟 */
      sleep(3);

      /* 使用 n_gsm 行规程 */
      ioctl(fd, TIOCSETD, &ldisc);

      /* 获取 n_gsm 扩展配置 */
      ioctl(fd, GSMIOC_GETCONF_EXT, &ce);
      /* 每隔 5 秒使用一次保持活动以监视调制解调器连接 */
      ce.keep_alive = 500;
      /* 设置新的扩展配置 */
      ioctl(fd, GSMIOC_SETCONF_EXT, &ce);
      /* 获取 n_gsm 配置 */
      ioctl(fd, GSMIOC_GETCONF, &c);
      /* 我们是发起者并且需要编码 0（基本） */
      c.initiator = 1;
      c.encapsulation = 0;
      /* 我们的调制解调器默认最大大小为 127 字节 */
      c.mru = 127;
      c.mtu = 127;
      /* 设置新配置 */
      ioctl(fd, GSMIOC_SETCONF, &c);
      /* 获取 DLC 1 配置 */
      dc.channel = 1;
      ioctl(fd, GSMIOC_GETCONF_DLCI, &dc);
      /* 第一个用户通道具有更高的优先级 */
      dc.priority = 1;
      /* 设置新的 DLC 1 特定配置 */
      ioctl(fd, GSMIOC_SETCONF_DLCI, &dc);
      /* 获取第一个 gsmtty 设备节点 */
      ioctl(fd, GSMIOC_GETFIRST, &first);
      printf("第一个多路复用线路: /dev/gsmtty%i\n", first);

      /* 等待永远以保持行规程启用 */
      daemon(0,0);
      pause();

#. 将这些设备作为普通的串行端口使用
例如，可以：

   - 在 `ttygsm1` 上使用 *gnokii* 发送 / 接收 SMS
   - 在 `ttygsm2` 上使用 *ppp* 建立数据链路

#. 在关闭物理端口之前先关闭所有虚拟端口
请注意，在关闭物理端口后，调制解调器仍然处于多路复用模式。这可能会阻止稍后成功重新打开端口。为了避免这种情况，要么重置调制解调器（如果您的硬件允许），要么在第二次初始化多路复用模式之前手动发送断开连接命令帧。断开连接命令帧的字节序列如下：

      0xf9, 0x03, 0xef, 0x03, 0xc3, 0x16, 0xf9

配置请求者
-------------

#. 通过其串口接收 `AT+CMUX=` 命令，初始化多路复用模式配置
#. 通过使用 `TIOCSETD` ioctl 将串行线路切换到使用 *n_gsm* 线律。
#. 如有必要，使用 `GSMIOC_GETCONF_EXT`/`GSMIOC_SETCONF_EXT` ioctl 来配置多路复用器。
#. 使用 `GSMIOC_GETCONF`/`GSMIOC_SETCONF` ioctl 来配置多路复用器。
#. 对于非默认设置，使用 `GSMIOC_GETCONF_DLCI`/`GSMIOC_SETCONF_DLCI` ioctl 来配置数据链路连接标识符（DLCIs）。
#. 获取所用串行端口的基本 gsmtty 编号：

        #include <stdio.h>
        #include <stdint.h>
        #include <linux/gsmmux.h>
        #include <linux/tty.h>
        #define DEFAULT_SPEED B115200
        #define SERIAL_PORT "/dev/ttyS0"

        int ldisc = N_GSM0710;
        struct gsm_config c;
        struct gsm_config_ext ce;
        struct gsm_dlci_config dc;
        struct termios configuration;
        uint32_t first;

        /* 打开串行端口 */
        fd = open(SERIAL_PORT, O_RDWR | O_NOCTTY | O_NDELAY);

        /* 配置串行端口：速度、流控制... */

        /* 获取串行数据并检查 "AT+CMUX=command" 参数... */

        /* 使用 n_gsm 线律 */
        ioctl(fd, TIOCSETD, &ldisc);

        /* 获取 n_gsm 扩展配置 */
        ioctl(fd, GSMIOC_GETCONF_EXT, &ce);
        /* 每隔 5 秒使用一次保活机制来监督对等方连接 */
        ce.keep_alive = 500;
        /* 设置新的扩展配置 */
        ioctl(fd, GSMIOC_SETCONF_EXT, &ce);
        /* 获取 n_gsm 配置 */
        ioctl(fd, GSMIOC_GETCONF, &c);
        /* 我们是请求者且需要编码 0（基本） */
        c.initiator = 0;
        c.encapsulation = 0;
        /* 我们的调制解调器默认的最大尺寸为 127 字节 */
        c.mru = 127;
        c.mtu = 127;
        /* 设置新的配置 */
        ioctl(fd, GSMIOC_SETCONF, &c);
        /* 获取 DLC 1 的配置 */
        dc.channel = 1;
        ioctl(fd, GSMIOC_GETCONF_DLCI, &dc);
        /* 第一个用户通道具有更高的优先级 */
        dc.priority = 1;
        /* 设置新的 DLC 1 特定配置 */
        ioctl(fd, GSMIOC_SETCONF_DLCI, &dc);
        /* 获取第一个 gsmtty 设备节点 */
        ioctl(fd, GSMIOC_GETFIRST, &first);
        printf("第一个多路复用线路: /dev/gsmtty%i\n", first);

        /* 无限期等待以保持线律启用 */
        daemon(0,0);
        pause();

11-03-08 - Eric Bénard - <eric@eukrea.com>
