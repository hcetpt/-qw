SPDX 许可证标识符: (LGPL-2.1 或 BSD-2-Clause)

构建 libbpf
==========

libelf 和 zlib 是 libbpf 的内部依赖项，因此需要链接到 libbpf 并且必须在系统上安装才能使应用程序正常工作。
默认使用 pkg-config 来查找 libelf，并且可以通过 PKG_CONFIG 覆盖调用的程序。
如果在构建时不想使用 pkg-config，可以通过设置 NO_PKG_CONFIG=1 在调用 make 时禁用它。
要同时构建静态库 libbpf.a 和共享库 libbpf.so：

.. 代码块:: bash

    $ cd src
    $ make

仅构建目录 build/ 中的静态库 libbpf.a 并将它们与 libbpf 头文件一起安装到临时目录 root/：

.. 代码块:: bash

    $ cd src
    $ mkdir build root
    $ BUILD_STATIC_ONLY=y OBJDIR=build DESTDIR=root make install

针对安装在 /build/root/ 中的自定义 libelf 依赖项构建静态库 libbpf.a 和共享库 libbpf.so，并将它们与 libbpf 头文件一起安装到构建目录 /build/root/：

.. 代码块:: bash

    $ cd src
    $ PKG_CONFIG_PATH=/build/root/lib64/pkgconfig DESTDIR=/build/root make
