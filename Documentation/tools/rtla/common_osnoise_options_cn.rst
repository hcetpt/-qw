**-a**, **--auto** *us*

    设置自动跟踪模式。此模式会设置一些调试系统时常用的选择项。它等同于使用 **-s** *us* **-T 1 -t**

**-p**, **--period** *us*

    设置 *osnoise* 跟踪器的周期（以微秒为单位）

**-r**, **--runtime** *us*

    设置 *osnoise* 跟踪器的运行时间（以微秒为单位）

**-s**, **--stop** *us*

    如果单个样本高于参数值（以微秒为单位），则停止跟踪
    如果设置了 **-T**，它还会将跟踪结果保存到输出中

**-S**, **--stop-total** *us*

    如果总样本高于参数值（以微秒为单位），则停止跟踪
    如果设置了 **-T**，它还会将跟踪结果保存到输出中

**-T**, **--threshold** *us*

    指定两次时间读取之间被视为噪声的最小差异
    默认阈值是 *5 us*

**-t**, **--trace** \[*file*\]

    将停止的跟踪结果保存到 [*file|osnoise_trace.txt*]
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
