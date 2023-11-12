#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 10 11:10:08 2023

@author: hanxu
"""
from View.PAMViewer_UI import Ui_PAMView
from Model.Model_PAM import cPamAnalyzer

from silx.gui import qt
from PyQt5 import QtCore, QtGui, QtWidgets
from silx.gui.plot import Plot1D, Plot2D, PlotWidget
from silx.gui.colors import Colormap
import numpy as np
_backend = 'opengl'

class Control_PAM(Ui_PAMView):
    err_Msg = []

    def setup(self):
        
        self.pamAn = cPamAnalyzer()
        
        self.subWindow_pv = QtWidgets.QMainWindow()
        self.subWindow_pv.setWindowTitle('PAM Viewer with functions')
        self.setupUi(self.subWindow_pv)
        
        self.sb_modu_threshold.setValue( self.pamAn.pam_modulation_threshold)
        
        colormap = Colormap(name='jet',
                    normalization='linear',
                    )
        #create a plot2d object for Gotthard image (frame, pixel)
        self.plot_img = Plot2D(backend = _backend, parent = self.subWindow_pv)
        self.plot_img.setDefaultColormap(colormap)
        self.plot_img.setGraphTitle('image')
        self.plot_img.getXAxis().setLabel('Pixel')
        self.plot_img.getYAxis().setLabel('Frame')     
        
        #create a plot1d object for raw and smoothed pam signal
        self.plot_pam = Plot1D(backend = _backend, parent = self.subWindow_pv)
        self.plot_pam.setGraphTitle('on - off')
        self.plot_pam.getXAxis().setLabel('Pixel')
        self.plot_pam.getYAxis().setLabel('Intensity (arb.u.)') 
        
        #create a plot1d object for raw and smoothed pam signal
        self.plot_pam_grad = Plot1D(backend = _backend, parent = self.subWindow_pv)
        self.plot_pam_grad.setGraphTitle('gradient')
        self.plot_pam_grad.getXAxis().setLabel('Pixel')
        self.plot_pam_grad.getYAxis().setLabel('Gradient (arb.u.)') 
       
        self.layout = qt.QGridLayout()
        self.widget.setLayout(self.layout)
        self.layout.addWidget(self.plot_img,0,0,0,1)
        self.layout.addWidget(self.plot_pam,0,1)
        self.layout.addWidget(self.plot_pam_grad,1,1)
        
        self.btn_UpdatePAM.clicked.connect(self.PAM_set) # define PAM_set
        
    def PAM_set(self):
        x1 = self.sb_ROI_Xmin.value()
        x2 = self.sb_ROI_Xmax.value()
        ROI = [x1,x2]
        smooth_window = self.sb_smooth_size.value()
        smooth_mode = self.cb_smooth_mode.currentText()
        whichPulse = self.sb_whichPulse.value()
        IsShowPulseOnly = self.checkBox_showPulseOnly.isChecked()
        pam_mou_threshold = self.sb_modu_threshold.value()
        
        on_slice_str = self.On_Slice.text()
        off_slice_str = self.Off_Slice.text()
        
        self.pamAn.updateROI(ROI)
        self.pamAn.updateSmoothWindow(size = smooth_window, mode = smooth_mode)
        self.pamAn.updateOnOffSlice(on_slice_str,off_slice_str)
        self.pamAn.whichPulse = whichPulse
        self.pamAn.IsShowPulseOnly = IsShowPulseOnly
        self.pamAn.pam_modulation_threshold = pam_mou_threshold
        try:
            if self.pamAn.processPAM() == False:
                self.err_Msg.append('cannot process PAM')

        except:
            self.err_Msg.append('cant process PAM.')

        self.update_PAMViewer()  
        
    def processData(self):
        self.pamAn.processPAM()
        for m in self.pamAn.err_Msg:
            self.err_Msg.append(m)
        self.pamAn.err_Msg.clear()
        
        
    def update_PAMViewer(self):            
           
        try:
            if self.pamAn.IsShowPulseOnly == False:
                img = self.pamAn.ADC
            else:
                img = self.pamAn.PULSES
            _pam = self.pamAn.pam_sel
            _smoothed_pam = self.pamAn.smoothed_pam_sel
            _g = self.pamAn.pam_gradient_sel
            
            xdata = np.asarray(range(len(_pam)), dtype = float)
            self.lcd_nPulses.display(self.pamAn.nPulses)
            
            self.plot_img.addImage(img, resetzoom = True)
            self.plot_pam.addCurve(x = xdata,
                                   y = _pam,
                                             color = 'green',
                                             symbol = '.',
                                             linestyle = '',
                                             replace = True,
                                             legend = 'pam raw')
            self.plot_pam.addCurve(x = xdata,
                                             y = _smoothed_pam,
                                             color = 'red',
                                             symbol = '',
                                             linestyle = '-',
                                             replace = False,
                                             legend = 'smoothed curve')
            
            self.plot_pam_grad.addCurve(x = xdata,
                                              y = _g,
                                              color = 'blue',
                                              replace = True,
                                              legend = 'gradient')
            
        except:
            self.err_Msg.append('cant update image on beam viewer.')

#%%
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = Control_PAM()
    ui.setup(cPamAnalyzer())
    ui.subWindow_pv.show()
    sys.exit(app.exec_())