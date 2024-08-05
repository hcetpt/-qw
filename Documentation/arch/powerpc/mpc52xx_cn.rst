=============================
Linux 2.6.x 在 MPC52xx 系列上的使用
=============================

对于最新信息，请访问 https://www.246tNt.com/mpc52xx/

编译/使用方法：

  - U-Boot:

     # <编辑 Makefile 设置 ARCH=ppc 和 CROSS_COMPILE=...（如果需要，也可以设置 EXTRAVERSION）
# make lite5200_defconfig
     # make uImage

     接着，在 U-Boot 中：
     => tftpboot 200000 uImage
     => tftpboot 400000 pRamdisk
     => bootm 200000 400000

  - DBug:

     # <编辑 Makefile 设置 ARCH=ppc 和 CROSS_COMPILE=...（如果需要，也可以设置 EXTRAVERSION）
# make lite5200_defconfig
     # 将 your_initrd.gz 复制到 arch/ppc/boot/images/ramdisk.image.gz
     # make zImage.initrd
     # make

     接着在 DBug 中：
     DBug> dn -i zImage.initrd.lite5200


一些说明：

 - 此端口命名为 mpc52xxx，配置选项为 PPC_MPC52xx。不支持 MGT5100，我不确定是否有人有兴趣为此工作。我没有选择 5xxx，因为似乎有很多与 MPC5200 无关的 5xxx。我也包含了 'MPC' 出于同样的原因。
- 当然，我受到了 2.4 版本的启发。如果你认为我在某些代码的版权中遗漏了你或你的公司，请告诉我，我会尽快更正。
