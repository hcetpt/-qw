SA1100 串行端口
==================

SA1100 串行端口的主要/次要编号已正式分配：

  > 日期：2000年9月24日，星期日 21:40:27 -0700
  > 发件人：H. Peter Anvin <hpa@transmeta.com>
  > 收件人：Nicolas Pitre <nico@CAM.ORG>
  > 抄送：设备列表维护者 <device@lanana.org>
  > 主题：Re: 设备
  >
  > 好的。请注意，设备编号204和205用于“低密度
  > 串行设备”，因此这些主设备号将有一系列的次设备号（tty设备层能很好地处理这种情况，因此您不必担心做任何特殊处理。）
  >
  > 因此您的分配如下：
  >
  > 204 字符型 低密度串行端口
  >                   5 = /dev/ttySA0               SA1100 内置串行端口 0
  >                   6 = /dev/ttySA1               SA1100 内置串行端口 1
  >                   7 = /dev/ttySA2               SA1100 内置串行端口 2
  >
  > 205 字符型 低密度串行端口（备用设备）
  >                   5 = /dev/cusa0                /dev/ttySA0 的呼叫设备
  >                   6 = /dev/cusa1                /dev/ttySA1 的呼叫设备
  >                   7 = /dev/cusa2                /dev/ttySA2 的呼叫设备
  >

您必须在您的 SA1100 基础设备使用的根文件系统的 /dev 目录中创建这些节点：

	mknod ttySA0 c 204 5
	mknod ttySA1 c 204 6
	mknod ttySA2 c 204 7
	mknod cusa0 c 205 5
	mknod cusa1 c 205 6
	mknod cusa2 c 205 7

除了上面创建适当的设备节点之外，您还必须确保用户空间的应用程序使用正确的设备名称。一个典型的例子是 /etc/inittab 文件的内容，在该文件中您可能有一个在 ttyS0 上启动的 getty 进程。
在这种情况下：

- 将 ttyS0 的出现替换为 ttySA0，将 ttyS1 替换为 ttySA1 等等
- 别忘了在 /etc/securetty 中添加 'ttySA0'、'console' 或适当的 tty 名称，以便允许 root 登录
