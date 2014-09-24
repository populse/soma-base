# -*- coding: utf-8 -*-

#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info". 
# 
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.


'''
soma module documentation is not finished yet

Examples
========

Insert examples here

Module content
==============

The content of soma module is composed of many submodules. However,
all important items can be imported from soma.api. For example, if
one wants to use the Application class defined in the module 
soma.application, he just have to use the following import 
statement::
  from soma.api import Application

Main classes
------------
- :class:`Application <soma.application.Application>`: an Application instance 
  contains all information that is shared across all modules of an application.

Advanced classes
----------------
- :class:`Singleton <soma.singleton.Singleton>`: A class deriving from 
  Singleton can have only one instance.

Information
-----------
- Yann Cointepas
- NeuroSpin (http://www.neurospin.org) and IFR 49 (http://www.ifr49.org)
- License: CeCILL version 2 (http://www.cecill.info/licences/Licence_CeCILL_V2-en.html)
'''


from soma.singleton import Singleton
from soma.application import Application
from soma.controller import Controller
