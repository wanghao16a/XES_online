from silx.gui import qt
from PyQt5 import QtCore, QtGui, QtWidgets

from silx.gui.plot import Plot1D, Plot2D
from silx.gui.plot.tools.roi import RegionOfInterestManager
from silx.gui.plot.items.roi import RectangleROI
from silx.gui.colors import Colormap
import numpy as np

from View.View_XESUI import Ui_XES_Viewer
from Model.Model_XES import cXESAnalyzer
from Model.Model_Jungfrau import cJF16Analyzer
from Model.Model_Digitizer import cDigitizerAnalyzer

_backend =  'opengl'#'matplotlib'
colormap = Colormap(name='jet',
                    normalization='log',
                    )

class Control_XES(Ui_XES_Viewer):
    err_Msg = []
    model_digitizer = cDigitizerAnalyzer()
    model_Jungfrau = cJF16Analyzer()
    model_XES = cXESAnalyzer()
    
    def setup(self):   
        # self.model_digitizer = cDigitizerAnalyzer()
        # self.model_Jungfrau = cJF16Analyzer()
        # self.model_XES = cXESAnalyzer()
        
        self.subWindow_xes = QtWidgets.QTabWidget()
        self.subWindow_xes.setWindowTitle('XES Viewer')
        self.setupUi(self.subWindow_xes)
        
        #create a plot1d object for raw digitizer signal
        self.plot_digi = Plot1D(backend = _backend, parent = self.subWindow_xes)
        self.plot_digi.setGraphTitle('Digi 2c Raw signal')
        self.plot_digi.getXAxis().setLabel('x')
        self.plot_digi.getYAxis().setLabel('ADU') 
        
        #create a plot1d object for retrieved I0
        self.plot_I0 = Plot1D(backend = _backend, parent = self.subWindow_xes)
        self.plot_I0.setGraphTitle('Xray I0 in current train')
        self.plot_I0.getXAxis().setLabel('peak position')
        self.plot_I0.getYAxis().setLabel('I0') 
        
        #create a plot2d object for Raw JF image , sum over all frames
        self.plot_JF_img = Plot2D(backend = _backend, parent = self.subWindow_xes)
        self.plot_JF_img.setDefaultColormap(colormap)
        self.plot_JF_img.setGraphTitle('JF image raw')
        self.plot_JF_img.getXAxis().setLabel('X (pix)')
        self.plot_JF_img.getYAxis().setLabel('Y (pix)')  
        
        self.roiManager = RegionOfInterestManager(self.plot_JF_img)
        self.roiManager.setColor('pink')  # Set the color of ROI
        
        self.roi = RectangleROI()
        self.roi.setSelectable(True)
        self.roi.setEditable(True)
        self.roi.setGeometry(origin=(50, 50), size=(200, 200))
        self.roi.setName('Initial ROI')
        self.roi.sigRegionChanged.connect(self.getROI)
        self.roiManager.addRoi(self.roi)

        
        #create a plot1d object for F SP in ROI vs Frame
        self.plot_JF_I0 = Plot1D(backend = _backend, parent = self.subWindow_xes)
        # self.plot_JF_I0.setDefaultColormap(colormap)
        self.plot_JF_I0.setGraphTitle('JF SP in ROI vs Frame')
        self.plot_JF_I0.getXAxis().setLabel('Frame#')
        self.plot_JF_I0.getYAxis().setLabel('SP in ROI')  
        
        #create a plot2d object for On-off difference JF image , sum over all frames
        self.plot_SP_diff = Plot1D(backend = _backend, parent = self.subWindow_xes)
        # self.plot_SP_diff.setDefaultColormap(colormap)
        self.plot_SP_diff.setGraphTitle('JF SP_diff')
        self.plot_SP_diff.getXAxis().setLabel('X (pix)')
        self.plot_SP_diff.getYAxis().setLabel('SP (Intensity)') 
        
               
        self.layout_digi = qt.QGridLayout()
        self.Plot_I0_widget.setLayout(self.layout_digi)
        self.layout_digi.addWidget(self.plot_digi,0,0)
        self.layout_digi.addWidget(self.plot_I0,0,1)

        self.layout_JF = qt.QGridLayout()
        self.plot_JF_widget.setLayout(self.layout_JF)
        self.layout_JF.addWidget(self.plot_JF_img,0,0)
        self.layout_JF.addWidget(self.plot_JF_I0,0,1)
        
        self.layout_XES = qt.QGridLayout()
        self.plot_XES_widget.setLayout(self.layout_XES)
        self.layout_XES.addWidget(self.plot_SP_diff,0,0)

        self.Digi_set()
        self.JF_set()
        self.XES_set()        
        
        self.btn_update_I0.clicked.connect(self.Digi_set)
        # self.sb_I0_mdp_firstPeak.valueChanged.connect(self.Digi_set)
        # self.sb_I0_mdp_Spacing.valueChanged.connect(self.Digi_set)
        # self.sb_I0_mdp_nPeaks.valueChanged.connect(self.Digi_set)
        # self.sb_I0_pkf_minHeight.valueChanged.connect(self.Digi_set)
        # self.sb_I0_pkf_minSpacing.valueChanged.connect(self.Digi_set)
        # self.UseI0APD.clicked.connect(self.Digi_set)
        # self.UseDefinePeak.clicked.connect(self.Digi_set)
        # self.UsePeakFinding.clicked.connect(self.Digi_set)
        
        self.btn_JF_update.clicked.connect(self.JF_set)
        self.btn_XES_update.clicked.connect(self.XES_set)
        
        self.subWindow_xes.currentChanged.connect(self.update_XESViewer)
    
    def getROI(self):

        x1,y1 = self.roi.getOrigin()

        x1 = int(x1)
        y1 = int(y1)
        dx,dy = self.roi.getSize()
        x2 = x1 + int(dx)
        y2 = y1 + int(dy)

        self.JF_ROI_x1.setValue(x1)        
        self.JF_ROI_x2.setValue(x2)
        self.JF_ROI_y1.setValue(y1)
        self.JF_ROI_y2.setValue(y2)
        # self.JF_set()
        
        
    def Digi_set(self):
        Use_apd = self.UseI0APD.isChecked()
        Use_peakFinding = self.UsePeakFinding.isChecked()
        height =  self.sb_I0_pkf_minHeight.value()
        spacing = self.sb_I0_pkf_minSpacing.value()
        peakFinding_Para = [height, spacing]
       
        p0 = self.sb_I0_mdp_firstPeak.value()
        sep = self.sb_I0_mdp_Spacing.value()
        nPeaks = self.sb_I0_mdp_nPeaks.value()
        udf_Para = [p0, sep, nPeaks]        
        self.model_digitizer.updatePara(Use_apd, Use_peakFinding, peakFinding_Para, udf_Para)
        self.update_XESViewer()
    
    def JF_set(self):
        mode = self.cb_JF_module.currentText()

        x1 = self.JF_ROI_x1.value()        
        x2 = self.JF_ROI_x2.value()
        y1 = self.JF_ROI_y1.value()
        y2 = self.JF_ROI_y2.value()
        ROI = [y1,y2,x1,x2]
 
        self.model_Jungfrau.updataPara(ROI, mode)
        self.update_XESViewer()
    
    def XES_set(self):
        on_slice_string = self.JF_OnSlice.text()
        off_slice_string = self.JF_OffSlice.text()
        Digi_on_slice_string = self.I0_on_slice.text()
        Dig_off_slice_string = self.I0_off_slice.text()        
        XrayPulse_slice_string = self.JF_data_Slice.text()
        
        isIntraTrain = self.cb_isIntraTrain.isChecked()
        
        self.model_XES.updatePara(isIntraTrain, 
                                  on_slice_string, 
                                  off_slice_string, 
                                  XrayPulse_slice_string,
                                  Digi_on_slice_string,
                                  Dig_off_slice_string
                                  )
        if len(self.model_XES.buffer) == 1:
            self.model_XES.buffer.clear()
        self.update_XESViewer()
    
    def processData(self):
        
        '''
        process data from digitizer and Jungfrau.
        From model_digitizer, we get I0[nPulses]
        From model_Jungfrau, we get JF_data[nFrame,ny,nx]
        then pass the I0 and JF_data to model_XES, 
        calculate diff_img and SP_diff from normalized JF data by digitizer
 
        Returns
        -------
        Bool.

        '''
        flag_process_digi = True
        if self.model_digitizer.processDigi() == False:
            self.err_Msg.append('Digitizer process mistake')
            for m in self.model_digitizer.err_Msg:
                self.err_Msg.append(m)
            self.model_digitizer.err_Msg.clear()
            flag_process_digi = False
            # return False
            
        flag_process_JF = True
        if self.model_Jungfrau.processJF() == False:
            self.err_Msg.append('Jungfrau process mistake')
            for m in self.model_Jungfrau.err_Msg:
                self.err_Msg.append(m)
            self.model_Jungfrau.err_Msg.clear()
            flag_process_JF = False
            # return False
            
        if flag_process_digi:
            _I0 = self.model_digitizer.I0
        else:
            _I0 = None
        # print(f'XES controller get I0 from model digitizer: {_I0}')
        if flag_process_JF:
            _JF_data = self.model_Jungfrau.JF_data
        else:
             _JF_data = None
        

        self.model_XES.updateData(_I0, _JF_data)        

        if self.model_XES.processXES() == False:
            self.err_Msg.append('XES process mistake')
            for m in self.model_XES.err_Msg:
                self.err_Msg.append(m)
            self.model_XES.err_Msg.clear()            
            # self.diff_img = np.nan
            self.SP_diff = np.nan
            self.I0 = np.nan
            self.nPulses = 0
            return False
        else:
            #output data
            # self.diff_img = self.model_XES.diff_img
            self.SP_diff = self.model_XES.SP_diff    
            self.nPulses = self.model_XES.nPulses
            return True
    
    def update_XESViewer(self):            
            if self.processData() == False:
                self.err_Msg.append('cant process XES data.')
        # try:
            if self.model_Jungfrau.isOnline:
                self.rB_isOnline.setChecked(True)
            else:
                self.rB_isOnline.setChecked(False)
                
            _digi_raw = self.model_digitizer.digi_raw
            _peaks = self.model_digitizer.peaks
            _I0 = self.model_digitizer.I0
            # print(f'XES controller, update_XESviewer get I0: {_I0}')
            
            if self.UsePeakFinding.isChecked():
                self.lcdNumber_Npeak.display(len(_peaks))
            else:
                self.lcdNumber_Npeak.display(0)
            
            
            # show digi_raw data, and peaks we found/identified
            if self.subWindow_xes.currentWidget().objectName() == 'XrayDiode': 
                if self.model_digitizer.Use_apd == False and _digi_raw is not None:
                    xdata = np.asarray(range(len(_digi_raw))) 
                    self.plot_digi.addCurve(x = xdata,
                                            y = _digi_raw,
                                            color = 'blue',
                                            symbol = '',
                                            linestyle = '-',
                                            replace = True,
                                            legend = 'digi raw')
                    self.plot_digi.addCurve(x = _peaks,
                                            y = _digi_raw[_peaks],
                                            color = 'red',
                                            symbol = 'o',
                                            linestyle = '',
                                            replace = False,
                                            legend = 'peaks')

                
                # show the I0
                if _I0 is not None:
                    self.plot_I0.addCurve(x = np.arange(len(_I0)),
                                                  y = _I0,
                                                  color = 'blue',
                                                  symbol = 'o',
                                                  linestyle = '-',
                                                  replace = True,
                                                  legend = 'I0')
                
            if self.subWindow_xes.currentWidget().objectName() == 'Jungfrau':
                _img_roi = self.model_Jungfrau.JF_Img_ROI
                _img = self.model_Jungfrau.JF_Img
                print(f'receive image {_img.shape}')
                
                # raw JF image
                self.plot_JF_img.addImage(_img, resetzoom = False)
                # self.plot_JFROI_img.addImage(_img_roi,resetzoom = True)
            
            
            # JF SP for all 16 Frames added
                _x = np.arange(len(self.model_XES.JF_SP_allFrame))
                # print('model_XES.JF_SP_allFrame')
                # print(self.model_XES.JF_SP_allFrame.shape)
                self.plot_JF_I0.addCurve(x = _x, 
                                         y = self.model_XES.JF_SP_allFrame,
                                         color = 'blue',
                                         symbol = 'o',
                                         linestyle = '',
                                         replace = True,
                                         legend = 'JF I0',
                                         resetzoom = True)
                
            if self.subWindow_xes.currentWidget().objectName() == 'XESsetting':
                
                if self.model_XES.SP_diff is not np.nan:

                    if self.model_XES.isIntraTrain:
                        _sp_diff = np.average(self.model_XES.SP_diff,axis = 0)
                    else:
                        _sp_diff = self.model_XES.SP_diff
                    print(_sp_diff)
                    self.plot_SP_diff.addCurve(x = np.arange(len(_sp_diff)),
                                                  y = _sp_diff, 
                                                  color = 'blue',
                                                  symbol = 'o',
                                                  linestyle = '-',
                                                  replace = True,
                                                  legend = 'JF SP_diff',
                                                  resetzoom = True
                                                 )
            
        # except:
        #     self.err_Msg.append('canot update XES viewer.')
       
