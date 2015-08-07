This project makes it possible to use c-code inside python code. It is inspired by weave but tries to keep it as simple as possible.

The code relies on swig and distutils to generate and compile the module. Both have to be installed.

One example can be seen in swice.py when running as main-program.

Another Example:

import swice
code = '''
    a = a*5;
'''
a = np.array([1,2,3,4])
swice.inline(code, ['a'], locals(), globals())
print a # will print [5,10,15,20]