'''
Created on 05.10.2014

@author: jochen
'''

from scipy import weave

import numpy as np



A = np.array([[1, 2, 3, ], [4, 5, 6]])

print A

weave.inline("A2(0,0) = 1000;", ['A'])

print A
