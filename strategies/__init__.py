# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################
# linux支持python3.6 windows支持64位python3.8,python3.7
import platform

if platform.system() == 'Windows':
    if '3.8' in platform.python_version():
        try:
            from .base import Base

        except Exception as e:
            raise ValueError("请将本目前下的base_w38重命名为base替换原来的base")
    elif '3.7' in platform.python_version():
        try:
            from .base import Base

        except Exception as e:
            raise ValueError("请将本目前下的base_w37重命名为base替换原来的base")
    else:
        raise ValueError("python版本未提供支持")
elif platform.system() == 'Linux':
    if '3.6' in platform.python_version():
        try:
            from .base import Base

        except Exception as e:
            raise ValueError("请将本目前下的base_l36.so重命名为base.so替换原来的base.so")
    else:
        raise ValueError("python版本未提供支持")
else:
    raise ValueError("操作系统未提供支持")
