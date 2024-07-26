========================
内核驱动 i2c-amd756
========================

支持的适配器：
  * AMD 756
  * AMD 766
  * AMD 768
  * AMD 8111

    数据手册：在AMD官网上公开可用

  * nVidia nForce

    数据手册：不可用

作者：
	- Frodo Looijaard <frodol@dds.nl>,
	- Philip Edelbrock <phil@netroedge.com>

描述
-----------

此驱动支持 AMD 756、766、768 和 8111 周边总线控制器，以及 nVidia nForce。
请注意，对于 8111，有两种 SMBus 适配器。SMBus 1.0 适配器由本驱动支持，而 SMBus 2.0 适配器则由 i2c-amd8111 驱动支持。
