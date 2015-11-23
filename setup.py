#!/bin/python
# -*- coding: utf-8 -*-'''


'''
Created on 23.11.2015

@author: schlobohm
'''



from distutils.core import setup
setup(name='swice',
      version='0.1',
      description="Module for using c-code inside python in very simple way. For an example run the module a a program.",
      author='Jochen Schlobohm',
      author_email='jochen.schlobohm@gmail.com',
      maintainer="Jochen Schlobohm",
      maintainer_email="jochen.schlobohm@gmail.com",
      py_modules=['swice'],
      data_files=[('', ['numpy.i'])],
      license="LGPL",
      url='https://github.com/jochenn/swice')