#!/bin/python
# -*- coding: utf-8 -*-
'''
Created on 03.10.2014

@author: Jochen Schlobohm

@license: LGPL

@mail: jochen.schlobohm@gmail.com

@todo: additional sorce files (not tested yet), includes (not tested yet), src-dir, libs & libdirs (not tested yet), add different fileTypes
    
'''

import subprocess
import os, sys
from os import path
import numpy as np
import ctypes
import hashlib
import tempfile
import shutil
import importlib
from distutils.core import setup, Extension
import platform
import imp

# name of the c function that is generated
# The user does not necessarily know about this.
__NAME__ = "__g"
# suffix of the c-files. 'cpp' forces VISUAL STUDIO compiler to compile c++
C_FILE_SUFFIX = "cpp"

# suffix of the wrapper c-file. cxx is used when swig is set for c++
__WRAPPER_FILE_SUFFIX__ = "cxx"

# template for the generated c-code.
# has placeholders for the actual code and some definitions.
__CODE_TEMPLATE__ = r'''
/* swice generated c++-file */
#include "Python.h"
#include <stdio.h>
#include <stdint.h>

#define double(n1) ((double)n1)
#define int(n1) ((int)n1)
#define float(n1) ((float)n1)
#define int8_t(n1) ((int8_t)n1)
#define uint8_t(n1) ((uint8_t)n1)
#define int16_t(n1) ((int16_t)n1)
#define uint16_t(n1) ((uint16_t)n1)
#define int32_t(n1) ((int32_t)n1)
#define uint32_t(n1) ((uint32_t)n1)
#define int64_t(n1) ((int64_t)n1)
#define uint64_t(n1) ((uint64_t)n1)


extern int return_val;

%s
int '''+__NAME__+r'''(){
#line 1 "user.code"
%s

return return_val;
}'''

CODE_PATH = __NAME__ + ".c"

# path to the generated c++-file
__CODE_PATH__ = __NAME__ + "."+C_FILE_SUFFIX

# get the python types of numbers
INT_TYPE = type(5)
FLOAT_TYPE = type(5.5)

# Dictionary for mapping python types to c-types
# TODO: Find a more convenient and platform independend way
__TYPEDICT__ = {INT_TYPE:"int",
            FLOAT_TYPE:"double"}

# Dictionary to map ndarray types tp c-types
# TODO: Find a more convenient and platform independend way
__NUMPY_TYPE_DICT__ = {np.dtype("ubyte"): "uint8_t",
                   np.dtype("byte"): "int8_t",
                   np.dtype("uint16"): "uint16_t",
                   np.dtype("int16"): "int16_t",
                   np.dtype("uint32"): "uint32_t",
                   np.dtype("int32"): "int32_t",
                   np.dtype("uint64"): "uint64_t",
                   np.dtype("int64"): "int64_t",
                   np.dtype("float32"): "float",
                   np.dtype("float64"): "double"}

# Dictionary to map ndarray types tp c-types
# TODO: Find a more convenient and platform independend way
__NUMPY_TYPE_DICT__TEST = {np.dtype("ubyte"): "unsigned char",
                   np.dtype("byte"): "char",
                   np.dtype("uint16"): "unsigned short",
                   np.dtype("int16"): "short",
                   np.dtype("uint32"): "unsigned int",
                   np.dtype("int32"): "int",
                   np.dtype("uint64"): "unsigned long long",
                   np.dtype("int64"): "long long",
                   np.dtype("float32"): "float",
                   np.dtype("float64"): "double"}



__SWIG_INTERFACE_TYPEMAPS_ARRAYS__=[]
   
for key, typeString in __NUMPY_TYPE_DICT__.items():
    __SWIG_INTERFACE_TYPEMAPS_ARRAYS__.append("%%apply (%s* INPLACE_ARRAY1, int DIM1) {(%s* seq, int n1)};"%(typeString, typeString))
    __SWIG_INTERFACE_TYPEMAPS_ARRAYS__.append("%%apply (%s* INPLACE_ARRAY2, int DIM1, int DIM2) {(%s* seq, int n1, int n2)};"%(typeString, typeString))
    __SWIG_INTERFACE_TYPEMAPS_ARRAYS__.append("%%apply (%s* INPLACE_ARRAY3, int DIM1, int DIM2, int DIM3) {(%s* seq, int n1, int n2, int n3)};"%(typeString, typeString))
    __SWIG_INTERFACE_TYPEMAPS_ARRAYS__.append("%%apply (%s* INPLACE_ARRAY4, int DIM1, int DIM2, int DIM3, int DIM4) {(%s* seq, int n1, int n2, int n3, int n4)};"%(typeString, typeString))
       
__SWIG_INTERFACE_TYPEMAPS_ARRAYS__ = "\n".join(__SWIG_INTERFACE_TYPEMAPS_ARRAYS__)



# header for the generated swig interface
__INTERFACE_HEADER__ = '''/* '''+__NAME__+'''.i */
%module '''+__NAME__+'''
%{
#define SWIG_FILE_WITH_INIT
#include <stdio.h>
#include <stdint.h>
int return_val;
'''


# Footer of the swig interfaces. It generates typemaps for numpy arrays in various types and for up to 4 dimensions.
# There no known way to have typemaps for arbitrary dimensions. (as of June 2015)

__INTERFACE_FOOTER__ = '''
extern int '''+__NAME__+'''();
%}
%include "stdint.i"
%include "numpy.stdint.i"
 
%init %{
import_array();
%}
'''+__SWIG_INTERFACE_TYPEMAPS_ARRAYS__+'''
 
extern int '''+__NAME__+'''();
'''



# c-style macros for convenient array access
# the placeholder "%s" are reserved for the variable name and the dimension count, if needed (weave style array access) 
#
# one to four dimensions should be sufficient
__C_ACCESS_DEFINE__ = {
                   1:r'''#define %s%s(n1)  (%s[(n1)])''',
                   2:r'''#define %s%s(n1, n2)  (%s[N%s[1]*(n1)+(n2)])''',
                   3:r'''#define %s%s(n1, n2, n3)  (%s[N%s[1]*N%s[2]*(n1)+N%s[2]*(n2)+(n3)])''',
                   4:r'''#define %s%s(n1, n2, n3, n4)  (%s[N%s[1]*N%s[2]*N%s[3]*(n1)+N%s[3]*N%s[2]*(n2)+N%s[3]*(n3)+(n4)])'''}


def __createFiles__(code, interface, name):
    '''
        Creates two files: The i-file for swig and the code file to compile with swig. Before writing to those files, cleans existing files with same names.
        
        @brief Creates c and i files for swig interface generation and code compilation
        
        @param code Source code to compile
        @param interface Interface source code for swig
        @param name Name of the files (e.g. hash of content) 
        @return None
    '''
    cFileName = name + "."+C_FILE_SUFFIX

    iFileName = name + ".i"
    if os.path.exists(cFileName):
        os.unlink(cFileName)
    
    with open(cFileName, "w") as f:
        f.write(code)
        
    if os.path.exists(iFileName):
        os.unlink(iFileName)
    
    with open(iFileName, "w") as f:
        f.write(interface)
    
def __handleVars__(vars, cLocals, cGlobals=None):
    '''
        Creates a dictionary of all varibales that should be mapped into the c-domain. If "vars" is a dictionary , vars is returned. If vars is a list of strings, 
        each string is the c-name of a variabel in the created c-domain. The values are than taken from cLocals (first) or cGLobals (second) if not present.
        
        @brief Creates a variable dictionary {<var name in c>:value, ...}.
        
        @param vars Either a dictionary which is than returned as the result or a list of variable names which are looked up in cLocals and cGlobals.
        @param cLocals Dictionary of possible variables.
        @param cGlobals Dictionary of possible variables. If None globals() is used instead.
        @return dictionary holding the variable name and value
        
    '''
    varDict = dict()
    
    if type(vars) == type(varDict):
        return vars
    
    if not cGlobals:
        cGlobals = globals()
    
    for var in vars:
        if cLocals and var in cLocals:
            varDict.update({var:cLocals[var]})
        elif cGlobals and var in cGlobals:
            varDict.update({var:cGlobals[var]})
        else:
            raise Exception('Var "%s" could not be found in locals and globals' % var)
    
    
    return varDict

def __genNumpyHead__(key, var, genBody=False, extern = False):
    '''
        Generates c variables and functions to set and access ndarrays in c. Is used for swig interface generation and c code generation. Might as well generate a functon body to 
        set the variabel from python into the c domain.
    
        @brief Generates a header for swig interface generation and smart ndarray access in c.
        
        @param key Name of the variable
        @param var The variable itself
        @param genBody Boolean: If True, the function will generate a function body with wich the ndarray pointer can be "copied" into the c domain
        @param extern If True, the varibales will be generated as 'extern'. Needfull for compilating with cpp compiler. If not set in either the interface or the c++-code it will bring up multiple defined symbols.
        @return header as string
    '''
    
    externString = ""
    if extern:
        externString = "extern "
    
    
    dtypeString = __NUMPY_TYPE_DICT__[var.dtype]
    varString = ''
    varString += externString+"%s %s;\n" % (dtypeString + "*", key)
    varString += externString+"int D%s;\n" % (key)
    
    varString += externString+"int N%s[4];\n" % (key)
    
    dimArgString = ""
    i = 1
    for dim in var.shape:
        dimArgString += ", int n%d" % i
        i += 1
    
    varString += "void _set%s(%s *seq%s)" % (key, dtypeString, dimArgString)
     
    if not genBody:
        return varString + ';\n'
     
    varString += '''\n{
    %s = seq;\n''' % (key)
     
    for i in range(len(var.shape)):
        varString += "    N%s[%d] = n%d;\n" % (key, i, i + 1) 
    varString += "}\n"
    
    return varString

def __genInterface__(varDict):
    '''
        Creates an swig interface out of the variables listet in varDict. VarDict has the form {<variabel name in c>:value, ...}
        
        @brief Generate an interface file for swig
        @param varDict Dictionary with variables to map: {<variabel name in c>:value, ...}.
        @return interface as string
        
    '''
    varString = ""
    
    keyIterator = list(varDict.keys())
    keyIterator.sort()
    
    for key in keyIterator:
        
        var = varDict[key]
        
        if type(var) in [INT_TYPE, FLOAT_TYPE]:
            typeString = __TYPEDICT__[type(var)]
            varString += "%s %s;\n" % (typeString, key)
        elif type(var) == type(np.zeros(0)):
            varString += __genNumpyHead__(key, var)
            
        else:
            raise Exception("Cannot handle variable type: %s" % type(var))
        
    return __INTERFACE_HEADER__ + varString + __INTERFACE_FOOTER__ + varString

def __genCode__(code, varDict, genClassicAccess=True, extracode = ""):
    '''
        Generates a c++ source file and wraps the given code in a header for the access of python variable inside that c domain.
        If desired, additional macros in weave style are generated: <capitalized var name><dimNum>(dim1,...). 
        Otherwise only convenient macros are generated: <varName>(dim1,...).
        
        
        @brief Generates c code for inline c.
        
        @param code C-code to excecute
        @param varDict Dictionary of variables that are accessible in the generated c-domain
        @param genClassicAccess If True, additional macros are generated
        @param extracode Some extracode with special functions etc.
        @return code 
        
    '''
    
    resultCode = '#line 1 "user.extracode" \n'+extracode+"\n"+__CODE_TEMPLATE__
    varCode = ""
    
    keyIterator = list(varDict.keys())
    keyIterator.sort()
    
    for key in keyIterator:
        var = varDict[key]
        
        if type(var) in [INT_TYPE, FLOAT_TYPE]:
            typeString = __TYPEDICT__[type(var)]
            varCode += "extern %s %s;\n" % (typeString, key)
        elif type(var) == type(np.zeros(0)):
            
            varCode += __genNumpyHead__(key, var, True, extern = True)
            varCode += "\n"
            
            dimNum = len(var.shape)
            if dimNum == 0:
                raise Exception("0-dimensional numpy arrays are not supported by swig :(")
            keyList = [key, ""]
            keyList.extend([key] * (1 + np.sum(list(range(dimNum)))))
            varCode += __C_ACCESS_DEFINE__[dimNum] % tuple(keyList) + "\n"
            
            if genClassicAccess:
                keyList = [key.capitalize(), "%d" % dimNum]
                keyList.extend([key] * (1 + np.sum(list(range(dimNum)))))
                varCode += __C_ACCESS_DEFINE__[dimNum] % tuple(keyList) + "\n"
                varCode += "#define N%s(n1) N%s[n1]\n" % (key, key)
                
            
        else:
            raise Exception('Error, datatype not understood. Was "%s" for variable "%s"'%(str(type(var)), key))
            
            
    resultCode = resultCode % (varCode, code)
    
    return resultCode


def __copyToObject__(f, varDict):
    '''
        Copies values from varDict into the newly created c-wrapper module f.
        
        @brief Copies variable from the python scope into the newly created c wrapper module.
        @param f The python-c wrapper module.
        @param varDict Dictionery of the variables to copy
        @return None  
    '''
    for key in varDict:
        val = varDict[key]
        # if it is a single value
        if type(val) in [INT_TYPE, FLOAT_TYPE]:
            setattr(f.cvar, key, val)
        
        else:
            try:
                getattr(f, '_set%s' % key)(val)
            except Exception as e:
                raise Exception("Error setting array %s: %s"%(key, str(e)))
            pass
        
def __copyFromObject__(f, varDict, cLocals, cGlobals):
    '''
        Copies eventually modified values from the generated python-c wrapper module f back into the python domain.
        
        @brief Copies eventuelly modified values from the python-c wrapper module back into the python domain.
        @param f The python-c wrapper module.
        @param varDict Dictionary of the variables to copy
        @param cLocals First dictionary to find the vlaue to change
        @param cGLobals Second dictionary to find the value to change
        @thows Exception if the value could not be found
    '''
    for key in varDict:
        # only copy if it is a single value. ndarray are altered in place
        if type(varDict[key]) in [INT_TYPE, FLOAT_TYPE]:
            val = getattr(f.cvar, key)
        
            if cLocals and key in cLocals:
                cLocals.update({key:val})
            elif cGlobals and key in cGlobals:
                cGlobals.update({key:val})
            else:
                raise Exception('Could not assign result value "%s"' % key)
        
    
def __compileDistUtils__(hash, includeDirs, lib_dirs, libraries, doOptimizeGcc = True, additonalSources = []):
    '''
        Compiles a inline c module with the distutils. First a swig interface is used to generated swig wrapper coder which is than compiled into a python module.
        
        @brief Compiles a inline c module with distutils.
        @param hash Name of the c, interface and module files
        @param includeDirs List of directories in which distutils looks for headers needed
        @param lib_dirs List of directories in which distutils looks for libs needed
        @param libraries List of libraries which distutils uses for binding
        @return None
    '''
    try:
        numpy_include = np.get_include()
    except AttributeError:
        numpy_include = np.get_numpy_include()
    
    includeDirs.extend([numpy_include,
                os.curdir])
    
    
    iFileName = hash + ".i"
    cFileName = hash + "."+C_FILE_SUFFIX
    cWrapFileName = hash + "_wrap."+__WRAPPER_FILE_SUFFIX__
    
    
    subprocess.check_call(["swig", "-python", "-c++", iFileName])

    
    extra_compile_args = []
    if doOptimizeGcc:
        extra_compile_args = ["-pthread","-O3","-march=native","-mtune=native"]


    sourcesList = [cFileName, cWrapFileName]
    sourcesList.extend(additonalSources)
    
    module1 = Extension('_%s' % hash,
                        sources=sourcesList,
                        library_dirs=lib_dirs,
                        libraries=libraries,
                        include_dirs=includeDirs,
                        extra_compile_args = extra_compile_args)
    
    setup (script_args=['build'],
           name='_%s' % hash,
           version='1.0',
           description='SWICE JIT lib',
           ext_modules=[module1],
           include_dirs=includeDirs)

def __getHash__(code, interface):
    '''
        @brief Generates a hash from given c-code and interface
        
        @return Hash from code and interface
    '''
    
    hash = hashlib.md5()
    if sys.version_info[0] == 3:
        hash.update(code.encode("utf8"))
        hash.update(interface.encode("utf8"))
    else:
        hash.update(code)
        hash.update(interface)
    return "m" + (hash.hexdigest())
    

def __checkCreateTempPath__():
    '''
        @brief Checks presence of an temporary swice folder for the generation of inline c modules. If not present folder is created.
        
        @return String with temporary Folder. 
    '''
    
    tempdir = tempfile.gettempdir()
    
    
    swicePath = path.join(tempdir, "swice", getPlatformString())
    if not path.exists(swicePath):
        os.makedirs(swicePath) #recursive
    if not path.exists(path.join(swicePath, "numpy.stdint.i")):
        shutil.copy2(path.join(path.dirname(os.path.realpath(__file__)), "numpy.stdint.i"), swicePath)
        
    return swicePath

def __createLib__(code, interface, swicePath, name, includeDirs, lib_dirs, libraries, additionalSources = []):
    '''
        @brief Checks if a module with given code and interface has already been created. If not, a lib is created.
        
        @param code C-code to excecute 
        @param interface Swig interface code
        @param swicePath Path to the swice temporary diectory
        @param name Name of the c, interface and module files (e.g. hash of code)
        @param recompile If True, the lib is recreated, even if it already exists.
        @param includeDirs List of directories in which distutils looks for headers needed
        @param lib_dirs List of directories in which distutils looks for libs needed
        @param libraries List of libraries which distutils uses for binding
        @param additionalSources List of additional source files that are needed for the module. Should include full path or be in the local directory.
    '''
    
    olddir = os.curdir
    os.chdir(swicePath)
    __createFiles__(code, interface, name)

    __compileDistUtils__(name, includeDirs, lib_dirs, libraries, additionalSources)
    for dirpath, dirnames, filenames in os.walk(path.join(swicePath, "build")):
        for f in filenames:
            if f.startswith("_" + name + "."):
                shutil.copy2(path.join(dirpath, f), swicePath)
                break
        
    os.chdir(olddir)

def inline(code, vars=None, cLocals=None, cGlobals=None, extracode="", includeDirs=[], lib_dirs=[], libraries=[], additionalSources = [], recompile=False):
    '''
        Excecutes given c-code. Generates a swig wrapper module and maps paython variables into the c-domain. May handle int, float and ndarray. ndarray are not cipied but mapped.
        Makes variables from "vars" accesible in the c-domain.
        
        Vars may be a list of variable names. In that case values are taken from cLocals and cGLobals. Vars may also be a dictionary {<name of variable in c>:value,...} 
        
        @brief Excecutes given c-code
        
        @param code C-code to excecute
        @param vars List of variable names to map into the c-domain.
        @param cLocals First dictionary to find the vlaue to change
        @param cGLobals Second dictionary to find the value to change 
        @param extracode c-code which is accessible in the c-domain
        @param includeDirs List of directories in which distutils looks for headers needed
        @param lib_dirs List of directories in which distutils looks for libs needed
        @param libraries List of libraries which distutils uses for binding
        @param additionalSources List of additional source files that are needed for the module. Should include full path or be in the local directory.
        @param recompile If True, the lib is recreated, even if it already exists.
    '''
    varDict = dict()
    if vars:
        varDict = __handleVars__(vars, cLocals, cGlobals)
    else:
        raise Exception('Must specify "vars"')
    
    if len(varDict) == 0:
        raise Exception('Must specify at least one variable in "vars"')
    
    
    interface = __genInterface__(varDict)
    
    code = __genCode__(code, varDict, extracode = extracode)
    
    hash = __getHash__(code, interface)
    interface = interface.replace("module %s"%(__NAME__), "module " + hash)
    
    swicePath = __checkCreateTempPath__()
    
    try:
        sys.path.index(swicePath)
    except ValueError as e:
        sys.path.append(swicePath)
        
    
    if not recompile:
        try:
            tempModule = importlib.import_module(hash)
            imp.reload(tempModule)
        except ImportError as e:
            recompile = True
    
    if recompile:
        __createLib__(code, interface, swicePath, hash, includeDirs, lib_dirs, libraries, additionalSources)
        tempModule = importlib.import_module(hash)
        imp.reload(tempModule)
    
    
    
    __copyToObject__(tempModule, varDict)
    
    methodToCall = getattr(tempModule, __NAME__)
    
    return_val = methodToCall()
    __copyFromObject__(tempModule, varDict, cLocals, cGlobals)
    
    return return_val


def getPlatformString():
    return platform.architecture()[0]+"_"+platform.architecture()[1]

if __name__ == "__main__":
    
    from time import time
    
    a = 2
    
    b = np.random.rand(300,400,500)
    c = np.array(b)
    d = np.zeros_like(b)
    
    e = np.array(b * 1000, dtype = np.uint16)
    f = np.array(e)
    
    
    code = r'''
    a = a*2;
    
    for (int x = 0; x < Nb[0]; x++){
        for (int y = 0; y < Nb[1]; y++){
            for (int z = 0; z < Nc[2]; z++){
                d(x, y, z) = b(x, y, z) * c(x, y, z);
            }
        }
    }
    
    for (int x = 0; x < Nb[0]; x++){
        for (int y = 0; y < Nb[1]; y++){
            for (int z = 0; z < Nc[2]; z++){
                e(x, y, z) = e(x, y, z) * uint16_t(PI);
            }
        }
    }
    
    
    return_val = -5;
    '''

    extracode = ''' 
    #define PI 3.14
    '''
    
    tRecompile = time()
    errorCode = inline(code, ['a', 'b', 'c', 'd', 'e'], locals(), globals(), extracode = extracode, recompile=True)
    tRecompile = time() - tRecompile
    assert -5 == errorCode
    
    assert a == 4
    assert np.allclose(b*c, d)
    assert np.allclose(e ,f*3)
    tNoCompile = time()
    errorCode = inline(code, ['a', 'b', 'c', 'd', 'e'], locals(), globals(), extracode = extracode)
    tNoCompile = time() - tNoCompile
    assert -5 == errorCode
    assert a == 8
    assert np.allclose(b*c, d)
    assert np.allclose(e ,f*3*3)
    
    print "Everything went fine!"
    print "%f seconds with compiling and \n%f seconds without."%(tRecompile, tNoCompile)
    