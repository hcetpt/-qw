固件搜索路径
=============

以下的搜索路径用于在您的根文件系统中查找固件：
* fw_path_para - 模块参数 - 默认为空，因此会被忽略
* /lib/firmware/updates/UTS_RELEASE/
* /lib/firmware/updates/
* /lib/firmware/UTS_RELEASE/
* /lib/firmware/

可以通过向 firmware_class 模块传递模块参数 "path" 来激活第一个可选的自定义 fw_path_para。自定义路径的长度最多只能为 256 个字符。传递给内核的参数应为：

* 'firmware_class.path=$CUSTOMIZED_PATH'

还有一个在启动后运行时自定义路径的替代方法，您可以使用以下文件：

* /sys/module/firmware_class/parameters/path

您需要将自定义路径写入此文件，之后请求的固件将会首先在此路径下被搜索。请注意，换行符也会被考虑进去，可能不会产生预期的效果。例如，您可以使用：

echo -n /path/to/script > /sys/module/firmware_class/parameters/path

以确保正在使用您的脚本。
