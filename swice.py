'''
Created on 03.10.2014

@author: Jochen Schlobohm

@license: LGPL

@mail: jochen.schlobohm@gmail.com

@todo: additional sorce files, includes (not tested yet), src-dir, libs & libdirs (not tested yet)
    

'''

import subprocess
import os
from os import path
import numpy as np
# import scipy.weave
import ctypes
import hashlib
import tempfile
import shutil
# from scipy.weave import swigptr2, swigptr
import sys
import importlib
from distutils.core import setup, Extension
import platform

# name of the c function that is generated
# The user does not necessarily know about this.
__NAME__ = "__g"
# suffix of the c-files. 'cpp' forces vs compiler to compile c++
C_FILE_SUFFIX = "cpp"

# suffix of the wrapper c-file. cxx is used when swig is set for c++
__WRAPPER_FILE_SUFFIX__ = "cxx"

# template for the generated c-code.
# has placeholders for the actual code and some definitions.
__CODE_TEMPLATE__ = r'''
/* swice generated c++-file */
#include "Python.h"
#include <stdio.h>

#define double(n1) ((double)n1)
#define int(n1) ((int)n1)
#define float(n1) ((float)n1)

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

# header for the generated swig interface
__INTERFACE_HEADER__ = '''/* '''+__NAME__+'''.i */
%module '''+__NAME__+'''
%{
#define SWIG_FILE_WITH_INIT
#include <stdio.h>
int return_val;
'''


# Footer of the swig interfaces. It generates typemaps for numpy arrays in various types and for up to 4 dimensions.
# There no known way to have typemaps for arbitrary dimensions. (as of June 2015)

__INTERFACE_FOOTER__ = '''
extern int '''+__NAME__+'''();
%}
 
%include "numpy.i"
%init %{
import_array();
%}
%apply (double* INPLACE_ARRAY1, int DIM1) {(double* seq, int n1)};
%apply (double* INPLACE_ARRAY2, int DIM1, int DIM2) {(double* seq, int n1, int n2)};
%apply (double* INPLACE_ARRAY3, int DIM1, int DIM2, int DIM3) {(double* seq, int n1, int n2, int n3)};
%apply (double* INPLACE_ARRAY4, int DIM1, int DIM2, int DIM3, int DIM4) {(double* seq, int n1, int n2, int n3, int n4)};
%apply (float* INPLACE_ARRAY1, int DIM1) {(float* seq, int n1)};
%apply (float* INPLACE_ARRAY2, int DIM1, int DIM2) {(float* seq, int n1, int n2)};
%apply (float* INPLACE_ARRAY3, int DIM1, int DIM2, int DIM3) {(float* seq, int n1, int n2, int n3)};
%apply (float* INPLACE_ARRAY4, int DIM1, int DIM2, int DIM3, int DIM4) {(float* seq, int n1, int n2, int n3, int n4)};
 
%apply (unsigned short* INPLACE_ARRAY1, int DIM1) {(unsigned short* seq, int n1)};
%apply (unsigned short* INPLACE_ARRAY2, int DIM1, int DIM2) {(unsigned short* seq, int n1, int n2)};
%apply (unsigned short* INPLACE_ARRAY3, int DIM1, int DIM2, int DIM3) {(unsigned short* seq, int n1, int n2, int n3)};
%apply (unsigned short* INPLACE_ARRAY4, int DIM1, int DIM2, int DIM3, int DIM4) {(unsigned short* seq, int n1, int n2, int n3, int n4)};
%apply (short* INPLACE_ARRAY1, int DIM1) {(short* seq, int n1)};
%apply (short* INPLACE_ARRAY2, int DIM1, int DIM2) {(short* seq, int n1, int n2)};
%apply (short* INPLACE_ARRAY3, int DIM1, int DIM2, int DIM3) {(short* seq, int n1, int n2, int n3)};
%apply (short* INPLACE_ARRAY4, int DIM1, int DIM2, int DIM3, int DIM4) {(short* seq, int n1, int n2, int n3, int n4)};

%apply (unsigned char* INPLACE_ARRAY1, int DIM1) {(unsigned char* seq, int n1)};
%apply (unsigned char* INPLACE_ARRAY2, int DIM1, int DIM2) {(unsigned char* seq, int n1, int n2)};
%apply (unsigned char* INPLACE_ARRAY3, int DIM1, int DIM2, int DIM3) {(unsigned char* seq, int n1, int n2, int n3)};
%apply (unsigned char* INPLACE_ARRAY4, int DIM1, int DIM2, int DIM3, int DIM4) {(unsigned char* seq, int n1, int n2, int n3, int n4)};
%apply (char* INPLACE_ARRAY1, int DIM1) {(char* seq, int n1)};
%apply (char* INPLACE_ARRAY2, int DIM1, int DIM2) {(char* seq, int n1, int n2)};
%apply (char* INPLACE_ARRAY3, int DIM1, int DIM2, int DIM3) {(char* seq, int n1, int n2, int n3)};
%apply (char* INPLACE_ARRAY4, int DIM1, int DIM2, int DIM3, int DIM4) {(char* seq, int n1, int n2, int n3, int n4)};

%apply (unsigned int* INPLACE_ARRAY1, int DIM1) {(unsigned int* seq, int n1)};
%apply (unsigned int* INPLACE_ARRAY2, int DIM1, int DIM2) {(unsigned int* seq, int n1, int n2)};
%apply (unsigned int* INPLACE_ARRAY3, int DIM1, int DIM2, int DIM3) {(unsigned int* seq, int n1, int n2, int n3)};
%apply (unsigned int* INPLACE_ARRAY4, int DIM1, int DIM2, int DIM3, int DIM4) {(unsigned int* seq, int n1, int n2, int n3, int n4)};
%apply (int* INPLACE_ARRAY1, int DIM1) {(int* seq, int n1)};
%apply (int* INPLACE_ARRAY2, int DIM1, int DIM2) {(int* seq, int n1, int n2)};
%apply (int* INPLACE_ARRAY3, int DIM1, int DIM2, int DIM3) {(int* seq, int n1, int n2, int n3)};
%apply (int* INPLACE_ARRAY4, int DIM1, int DIM2, int DIM3, int DIM4) {(int* seq, int n1, int n2, int n3, int n4)};

%apply (unsigned long* INPLACE_ARRAY1, int DIM1) {(unsigned long* seq, int n1)};
%apply (unsigned long* INPLACE_ARRAY2, int DIM1, int DIM2) {(unsigned long* seq, int n1, int n2)};
%apply (unsigned long* INPLACE_ARRAY3, int DIM1, int DIM2, int DIM3) {(unsigned long* seq, int n1, int n2, int n3)};
%apply (unsigned long* INPLACE_ARRAY4, int DIM1, int DIM2, int DIM3, int DIM4) {(unsigned long* seq, int n1, int n2, int n3, int n4)};
%apply (long* INPLACE_ARRAY1, int DIM1) {(long* seq, int n1)};
%apply (long* INPLACE_ARRAY2, int DIM1, int DIM2) {(long* seq, int n1, int n2)};
%apply (long* INPLACE_ARRAY3, int DIM1, int DIM2, int DIM3) {(long* seq, int n1, int n2, int n3)};
%apply (long* INPLACE_ARRAY4, int DIM1, int DIM2, int DIM3, int DIM4) {(long* seq, int n1, int n2, int n3, int n4)};
 
extern int '''+__NAME__+'''();
'''

# get the python types of numbers
INT_TYPE = type(5)
FLOAT_TYPE = type(5.5)

# Dictionary for mapping python types to c-types
# TODO: Find a more convenient and platform independend way
__TYPEDICT__ = {INT_TYPE:"int",
            FLOAT_TYPE:"double"}

# Dictionary to map ndarray types tp c-types
# TODO: Find a more convenient and platform independend way
__NUMPY_TYPE_DICT__ = {np.dtype("ubyte"): "unsigned char",
                   np.dtype("byte"): "char",
                   np.dtype("uint16"): "unsigned short",
                   np.dtype("int16"): "short",
                   np.dtype("uint32"): "unsigned int",
                   np.dtype("int32"): "int",
                   np.dtype("uint64"): "unsigned long",
                   np.dtype("int64"): "long",
                   np.dtype("float32"): "float",
                   np.dtype("float64"): "double"}

# c-style macros for convenient array access
# the placeholder "%s" are reserved for the variable name and the dimension count, if needed (weave style array access) 
#
# one to four dimensions should be sufficient
__C_ACCESS_DEFINE__ = {1:r'''#define %s%s(n1)  (%s[(n1)])''',
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
        if cLocals and cLocals.has_key(var):
            varDict.update({var:cLocals[var]})
        elif cGlobals and cGlobals.has_key(var):
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
    
    for key in varDict:
        
        var = varDict[key]
        
        if type(var) in [INT_TYPE, FLOAT_TYPE]:
            typeString = __TYPEDICT__[type(var)]
            varString += "%s %s;\n" % (typeString, key)
        elif type(var) == type(np.zeros(0)):
            varString += __genNumpyHead__(key, var)
            
        else:
            raise "Cannot handle variable type: %s" % type(var)
        
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
    
    for key in varDict:
        var = varDict[key]
        
        if type(var) in [type(5), type(5.)]:
            typeString = __TYPEDICT__[type(var)]
            varCode += "extern %s %s;\n" % (typeString, key)
        elif type(var) == type(np.zeros(0)):
            
            varCode += __genNumpyHead__(key, var, True, extern = True)
            varCode += "\n"
            
            dimNum = len(var.shape)
            keyList = [key, ""]
            keyList.extend([key] * (1 + np.sum(range(dimNum))))
            varCode += __C_ACCESS_DEFINE__[dimNum] % tuple(keyList) + "\n"
            
            if genClassicAccess:
                keyList = [key.capitalize(), "%d" % dimNum]
                keyList.extend([key] * (1 + np.sum(range(dimNum))))
                varCode += __C_ACCESS_DEFINE__[dimNum] % tuple(keyList) + "\n"
            
        else:
            raise('Error, datatype not understood. Was "%s" for variable "%s"'%(str(type(var)), key))
            
            
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
            # f._setb(val)
            getattr(f, '_set%s' % key)(val)
        
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
        
            if cLocals and cLocals.has_key(key):
                cLocals.update({key:val})
            elif cGlobals and cGlobals.has_key(key):
                cGlobals.update({key:val})
            else:
                raise Exception('Could not assign result value "%s"' % key)
        
    
def __compileDistUtils__(hash, includeDirs, lib_dirs, libraries, doOptimizeGcc = True):
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
    
#     includeDirs.extend([numpy_include,
#                 os.curdir,
#                 os.environ['PYTHON_INCLUDE']])
    
    iFileName = hash + ".i"
    cFileName = hash + "."+C_FILE_SUFFIX
    cWrapFileName = hash + "_wrap."+__WRAPPER_FILE_SUFFIX__
    
    
    subprocess.check_call(["swig", "-python", "-c++", iFileName])

    
    extra_compile_args = []
    if doOptimizeGcc:
        extra_compile_args = ["-pthread","-O3","-march=native","-mtune=native"]
    
    
    module1 = Extension('_%s' % hash,
                        sources=[cFileName, cWrapFileName],
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
    hash.update(code)
    hash.update(interface)
    return "m" + (hash.digest().encode("hex"))
    

def __checkCreateTempPath__():
    '''
        @brief Checks presence of an temporary swice folder for the generation of inline c modules. If not present folder is created.
        
        @return String with temporary Folder. 
    '''
    
    tempdir = tempfile.gettempdir()
    
    
    swicePath = path.join(tempdir, "swice", getPlatformString())
    if not path.exists(swicePath):
        os.mkdir(swicePath)
    if not path.exists(path.join(swicePath, "numpy.i")):
        shutil.copy2(path.join(path.dirname(os.path.realpath(__file__)), "numpy.i"), swicePath)
        
    return swicePath

def __checkCreateLib__(code, interface, swicePath, name, recompile, includeDirs, lib_dirs, libraries):
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
    '''
    
    libPath = path.join(swicePath, "_" + name + ".pyd")
    if not path.exists(libPath) or recompile:
        olddir = os.curdir
        os.chdir(swicePath)
        __createFiles__(code, interface, name)
    
        __compileDistUtils__(name, includeDirs, lib_dirs, libraries)
        for dirpath, dirnames, filenames in os.walk(path.join(swicePath, "build")):
            for f in filenames:
                if f == "_" + name + ".pyd":
                    shutil.copy2(path.join(dirpath, f), swicePath)
                    break
            
        os.chdir(olddir)

def inline(code, vars=None, cLocals=None, cGlobals=None, extracode="", includeDirs=[], recompile=False, lib_dirs=[], libraries=[]):
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
        @param recompile If True, the lib is recreated, even if it already exists.
        @param lib_dirs List of directories in which distutils looks for libs needed
        @param libraries List of libraries which distutils uses for binding
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
        
    __checkCreateLib__(code, interface, swicePath, hash, recompile, includeDirs, lib_dirs, libraries)
    
    
    tempModule = importlib.import_module(hash)
    reload(tempModule)
    
    __copyToObject__(tempModule, varDict)
    
    methodToCall = getattr(tempModule, __NAME__)
    
    return_val = methodToCall()
    __copyFromObject__(tempModule, varDict, cLocals, cGlobals)
    
    return return_val


def getPlatformString():
    return platform.architecture()[0]+"_"+platform.architecture()[1]

if __name__ == "__main__":
    
    a = 2
    
    print "a was %d"%(a)
    
    b = np.array([1, 2, 3], dtype=np.double)
    c = np.zeros((2, 3, 4), dtype=np.uint16)
    for i in range(2):
        for j in range(3):
            for k in range(4):
                c[i, j, k] = 1000 + i * 100 + j * 10 + k
    
    d = np.zeros((4, 3), dtype=np.uint16)
    for i in range(4):
        for j in range(3):
            d[i, j] = 100 + i * 10 + j
    
    e = np.zeros((2, 3, 4, 5), dtype=np.uint16)
    for i in range(2):
        for j in range(3):
            for k in range(4):
                for l in range(5):
                    e[i, j, k, l] = 10000 + i * 1000 + j * 100 + k * 10 + l
    
    code = r'''
    int i;
    int j;
    int l;
    a = a*2;
    int k;
    
    i = 0;
    j = 0;
    k = 0;
    l = 0;
    for (i = 0; i < Nc[0]; i++){
        for (j = 0; j < Nc[1]; j++){
            for (k = 0; k < Nc[2]; k++){
                if (1000+100*i+10*j+1*k != c(i,j,k))
                    printf("%d%d%d is not equal to %4d\n", i,j,k,c(i,j,k));
            }
        }
    }
    
    for (i = 0; i < Ne[0]; i++){
        for (j = 0; j < Ne[1]; j++){
            for (k = 0; k < Ne[2]; k++){
                for (l = 0; l < Ne[3]; l++){
                    if (10000+1000*i+100*j+10*k+l != e(i,j,k,l))
                        printf("%d%d%d%d is not equal to %4d\n", i,j,k,l,e(i,j,k,l));
                }
            }
        }
    }
    for (i = 0; i < Nd[0]; i++){
    for (j = 0; j < Nd[1]; j++){
    if (100+10*i+1*j != d(i,j))
    printf("%d%d is not equal to %4d\n", i,j,d(i,j));
    
    
    }}
    
    printf("extracode PI: %f\n", PI);
    return_val = 5;
    printf("returnVal: %d\n", return_val);
    '''

    extracode = ''' 
    #define PI 3.14
    '''
    
    print inline(code, ['a', 'b', 'c', 'd', 'e'], locals(), globals(), recompile=True, extracode = extracode)
    print "a is %d"%(a)
    print "done"
    
    
