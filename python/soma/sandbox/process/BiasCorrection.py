## -*- coding: utf-8 -*-
#Process BiasCorrection
import os
import subprocess
from traits.api import HasTraits,Str, Int, Enum, Float, File

class BiasCorrection(HasTraits):
   
    
    def __init__(self):   
        #Definition des paramètres du process 
        self.mode=Enum(['write_minimal','write_all','delete_useless','write_minimal without correction'])
        self.write_wridges = Enum(['yes','no','read'])
        self.write_field = Enum(['no','yes'])
        self.write_hfiltered = Enum(['yes','no'])
        self.write_variance = Enum(['yes','no'])
        self.write_meancurvature = Enum(['no','yes'])
        self.write_edges = Enum(['yes','no'])
        self.field_rigidity = Float(20.0)
        self.wridges_weight = Float(20.0)
        self.sampling = Float(16.0)
        self.ngrid =  Float(2.0)
        self.zdir_multiply_regul = Float(0.5)
        self.variance_fraction = Int(75)
        self.edge_mask =Enum(['yes','no'])
        self.delete_last_n_slices = Enum(['auto','0','10','20','30'])
        
        #Input
        self.mri=File(exists=True)
        self.commissure_coordinates=File(exists=True)
        
        #Ouput
        self.mri_corrected=File(exists=False)
        self.field=File(exists=False)
        self.hfiltered=File(exists=False)
        self.white_ridges=File(exists=False)
        self.meancurvature=File(exists=False)
        self.variance=File(exists=False)
        self.edges=File(exists=False)
        
        
    def run(self,path,input):
        print 'RUN'   
        if self.mode == 'write_all':            
            self.write_wridges = 'yes'
            self.write_field = 'yes'
            self.write_hfiltered = 'yes'
            self.write_variance = 'yes'
            self.write_meancurvature = 'yes'
            self.write_edges = 'yes'          
        if self.edge_mask == 'yes':
            self.edge= '3'
        else:
            self.edge= 'n'
       
        #Input
        self.mri=input
        self.commissure_coordinates='/neurospin/lnao/Panabase/data_icbm/icbm/icbm350T/t1mri/default_acquisition/icbm350T.APC'
   
        # RUN       
        args=['VipT1BiasCorrection','-i',self.mri,\
        '-o',self.mri_corrected,\
        '-Fwrite',self.write_field,\
        '-field',self.field,\
        '-Wwrite',self.write_wridges,\
        '-wridge',self.white_ridges,\
        '-Kregul',self.field_rigidity,\
        '-sampling',self.sampling,\
        '-Kcrest',self.wridges_weight,\
        '-Grid',self.ngrid,\
        '-ZregulTuning',self.zdir_multiply_regul,\
        '-vp',self.variance_fraction,\
        '-e',self.edge,\
        '-eWrite',self.write_edges,\
        '-ename',self.edges,\
        '-vWrite',self.write_variance,\
        '-vname',self.variance,\
        '-mWrite',self.write_meancurvature,\
        '-mname',self.meancurvature,\
        '-hWrite',self.write_hfiltered,\
        '-hname',self.hfiltered,\
        '-Last',self.delete_last_n_slices,\
        '-Points',self.commissure_coordinates]
        str_args = [ str(x) for x in args ] 
        subprocess.call(str_args)      
 
