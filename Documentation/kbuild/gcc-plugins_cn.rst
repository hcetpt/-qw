=========================
GCC 插件基础设施
=========================


介绍
============

GCC 插件是可加载的模块，为编译器提供额外的功能 [1]_。它们对于运行时仪器化和静态分析非常有用。
我们可以通过回调 [2]_、GIMPLE [3]_、IPA [4]_ 和 RTL 传递 [5]_ 在编译过程中分析、修改和添加代码。
GCC 内核插件基础设施支持树外模块构建、交叉编译以及在单独目录中进行构建。
插件源文件必须能够被 C++ 编译器编译。
目前，GCC 插件基础设施仅支持部分架构。可以通过 grep "select HAVE_GCC_PLUGINS" 查找支持 GCC 插件的架构。
此基础设施移植自 grsecurity [6] 和 PaX [7]。

.. [1] https://gcc.gnu.org/onlinedocs/gccint/Plugins.html
.. [2] https://gcc.gnu.org/onlinedocs/gccint/Plugin-API.html#Plugin-API
.. [3] https://gcc.gnu.org/onlinedocs/gccint/GIMPLE.html
.. [4] https://gcc.gnu.org/onlinedocs/gccint/IPA.html
.. [5] https://gcc.gnu.org/onlinedocs/gccint/RTL.html
.. [6] https://grsecurity.net/
.. [7] https://pax.grsecurity.net/


目的
=======

GCC 插件旨在提供一个实验潜在编译器功能的地方，这些功能既不在 GCC 中也不在 Clang 上游版本中。一旦证明其有用性，目标是将该功能合并到 GCC（和 Clang）中，并最终在所有支持的 GCC 版本中提供该功能后将其从内核中移除。
具体来说，新的插件应只实现没有上游编译器支持的功能（无论是在 GCC 还是 Clang 中）。
当某个功能存在于 Clang 中但不存在于 GCC 中时，应努力将该功能引入上游 GCC（而不仅仅是作为特定于内核的 GCC 插件），以便整个生态系统都能从中受益。
同样地，即使GCC插件提供的某个功能在Clang中*不存在*，但如果该功能已被证明是有用的，则应投入精力将该功能合并到GCC（和Clang）中。

在某个功能被合并到上游GCC之后，对于相应版本的GCC（及之后的版本），该插件将被设置为无法编译。一旦所有内核支持的GCC版本都提供了该功能，该插件将从内核中移除。

文件
====

**$(src)/scripts/gcc-plugins**

这是GCC插件的目录。

**$(src)/scripts/gcc-plugins/gcc-common.h**

这是一个GCC插件的兼容性头文件。
应该始终包含此头文件而不是单独的GCC头文件。

**$(src)/scripts/gcc-plugins/gcc-generate-gimple-pass.h, $(src)/scripts/gcc-plugins/gcc-generate-ipa-pass.h, $(src)/scripts/gcc-plugins/gcc-generate-simple_ipa-pass.h, $(src)/scripts/gcc-plugins/gcc-generate-rtl-pass.h**

这些头文件自动生成GIMPLE、SIMPLE_IPA、IPA和RTL阶段的注册结构。
建议使用这些头文件而不是手动创建这些结构。

使用方法
=====

您必须安装适用于您的GCC版本的GCC插件头文件，例如，在Ubuntu上对于gcc-10:: 

```shell
apt-get install gcc-10-plugin-dev
```

或者在Fedora上:: 

```shell
dnf install gcc-plugin-devel libmpc-devel
```

或者在使用包含插件的交叉编译器时在Fedora上:: 

```shell
dnf install libmpc-devel
```

在内核配置中启用GCC插件基础设施以及您想要使用的插件:: 

```shell
CONFIG_GCC_PLUGINS=y
CONFIG_GCC_PLUGIN_LATENT_ENTROPY=y
..
```

运行GCC（本机或交叉编译器）以确保检测到插件头文件:: 

```shell
gcc -print-file-name=plugin
CROSS_COMPILE=arm-linux-gnu- ${CROSS_COMPILE}gcc -print-file-name=plugin
```

如果输出为“plugin”，则表示未检测到插件。

如果输出为完整路径，则表示已检测到插件:: 

```shell
/usr/lib/gcc/x86_64-redhat-linux/12/plugin
```

要编译包含插件的最小工具集:: 

```shell
make scripts
```

或者只需运行内核编译并使用循环复杂度GCC插件编译整个内核。

4. 如何添加新的GCC插件
==============================

GCC插件位于scripts/gcc-plugins/目录下。您需要将插件源文件放在scripts/gcc-plugins/目录下。不支持创建子目录。
它必须被添加到 `scripts/gcc-plugins/Makefile`、`scripts/Makefile.gcc-plugins` 以及相关的 `Kconfig` 文件中。
