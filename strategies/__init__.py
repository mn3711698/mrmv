# -*- coding: utf-8 -*-

##############################################################################
# Author：QQ173782910
##############################################################################
# linux支持python3.6 windows支持64位python3.8,python3.7
import platform
import shutil
import os

dll_map = {
    'Windows': {
        'pyv_dll_map': {
            '3.7': 'base_w37.pyd',
            '3.8': 'base_w38.pyd',
        },
        'target_dll_name': 'base.pyd'
    },
    'Linux': {
        'pyv_dll_map': {
            '3.6': 'base_l36.so'
        },
        'target_dll_name': 'base.so'
    }
}
target_name_map = {
    'Windows'
}

platform_type = platform.system()
python_version = platform.python_version()

if platform_type not in dll_map:
    raise ValueError("操作系统未提供支持")

platform_dll_map = dll_map[platform_type]
pyv_dll_map = platform_dll_map['pyv_dll_map']

dll_name = None
for python_version_prefix in pyv_dll_map:
    if python_version.startswith(python_version_prefix):
        dll_name = pyv_dll_map[python_version_prefix]
        break

if dll_name is None:
    raise ValueError("python版本未提供支持")

target_dll_name = platform_dll_map['target_dll_name']

load_path = os.path.abspath(os.path.dirname(__file__))
candidate_dll_path = os.path.join(load_path, dll_name)
target_dll_path = os.path.join(load_path, target_dll_name)

candidate_dll_exists = os.path.isfile(candidate_dll_path)
target_dll_exists = os.path.isfile(target_dll_path)
if not target_dll_exists:
    if not candidate_dll_exists:
        raise ValueError("策略文件加载失败, 请重新下载项目或联系作者")
    else:
        shutil.copyfile(candidate_dll_path, target_dll_path)

from .base import Base