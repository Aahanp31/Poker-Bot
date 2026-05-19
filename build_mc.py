from setuptools import setup, Extension
import pybind11
import sys

extra_args = (
    ['/O2', '/std:c++14']
    if sys.platform == 'win32'
    else ['-O3', '-std=c++17', '-march=native']
)

ext = Extension(
    name='poker_ai.mc_cpp',
    sources=['poker_ai/mc_cpp/monte_carlo.cpp'],
    include_dirs=[pybind11.get_include()],
    language='c++',
    extra_compile_args=extra_args,
)

setup(name='poker_ai_mc', ext_modules=[ext])
