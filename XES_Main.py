#!/usr/bin/env /gpfs/exfel/sw/software/mambaforge/22.11/envs/202302/bin/python
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.Qt import Qt
import numpy as np

from silx.gui import qt
from silx.gui.plot import Plot1D, Plot2D
from silx.gui.colors import Colormap
from silx.gui.plot.tools.roi import RegionOfInterestManager
from silx.gui.plot.items.roi import RectangleROI
from karabo_bridge.qt import QBridgeClient

# import controls (including view)
from Control_PAM import Control_PAM # Ui_PAMView
from Control_DataSourcesViewer import Control_Datasources #Ui_View_Datasources_withFunc
from Control_XESUI import Control_XES

# import models
# from Model.Model_PAM import cPamAnalyzer
# from Model.Model_Jungfrau import cJF16Analyzer
# from Model.Model_Digitizer import cDigitizerAnalyzer

#import main window view
from View.MainWindowUI import Ui_MainWindow as MW


colormap = Colormap(name='jet',
                    normalization='linear',
)
_backend = 'opengl'#'matplotlib'

#%% cInstrument
class cInstrument:
    
    def __init__(self, Name, Instrument_key, data_key, IsActive):
        self.Name = Name
        self.Instrument_key = Instrument_key
        self.data_key = data_key
        self.IsActive = IsActive
    
    def disable(self):
        self.IsActive = False

#%% cDataBuffer
import pandas as pd

class cDataBuffer:
    def __init__(self, keys=[], streamBufferSize = 5):
        self.keys = keys

        self.streamBufferSize = streamBufferSize
        self.streamCount = 0

        self.allDataBuff = {}
        self.allDataCount = 0
        
        for k in self.keys:
            self.allDataBuff[k] = []
    
    def get_Pandas_DataFrame(self):
        df = pd.DataFrame(self.allDataBuff)
        return df
        
    def push(self, dataDic):

        try:
            for k in dataDic.keys():
                self.allDataBuff[k].append(dataDic[k])

            # self.streamCount += 1
            self.allDataCount += 1

            # if self.streamCount >= self.streamBufferSize:
            #     self.streamCount = 0
        except:
            print('wrong data!')
    
    def clearAll(self):
        self.allDataCount = 0
        self.streamCount = 0
        for k in self.keys:
            self.allDataBuff[k].clear()

#%% MainLoop
class MainLoop(qt.QMainWindow):
    
    bridge_client = None
    dataBuff = None

    
    myInstruments = {}
    myInstruments['Gotthard'] = cInstrument(Name = 'Gotthard', 
                       Instrument_key = 'FXE_OGT3_PAM/DET/RECEIVER_REF:daqOutput', 
                       data_key = 'data.adc',
                       IsActive = False)
    
    myInstruments['Delay Stage'] = cInstrument(Name = 'Delay Stage', 
                       Instrument_key = 'FXE_SMS_USR/MOTOR/UM13', 
                       data_key = 'actualPosition.value', 
                       IsActive = False)
    
    myInstruments['PPODL'] = cInstrument(Name = 'PPODL', 
                       Instrument_key = 'FXE_AUXT_LIC/DOOCS/PPODL',  
                       data_key = 'actualPosition.value', 
                       IsActive = False)
    
    myInstruments['JF1'] = cInstrument(Name = 'JF1', 
                       Instrument_key = 'FXE_XAD_JF1M/DET/JNGFR01:daqOutput',  
                       data_key =  'data.adc', 
                       IsActive = True)
    
    myInstruments['JF2'] = cInstrument(Name = 'JF2', 
                       Instrument_key = 'FXE_XAD_JF1M/DET/JNGFR02:daqOutput',  
                       data_key =  'data.adc', 
                       IsActive = True)
    
    myInstruments['Digi Raw'] = cInstrument(Name = 'Digi Raw', 
                       Instrument_key = 'FXE_RR_DAQ/ADC/1:network',  
                       data_key =  'digitizers.channel_2_C.raw.samples',
                       IsActive = True)
    
    myInstruments['Digi APD'] = cInstrument(Name = 'Digi APD', 
                       Instrument_key = 'FXE_RR_DAQ/ADC/1:network',  
                       data_key =  'digitizers.channel_2_C.apd.pulseIntegral',
                       IsActive = False)
    
    #output data key list
    keys = ['tid',
            'pam_peak',
            'arrive_time',
            'pam_modulation',
            'PPODL',
            'Delay Stage',
            'I0',
            'JF_SP',
            'JF_SP_diff'
            ]
    
    def __init__(self, *args, **kwargs):
        super(MainLoop, self).__init__(*args, **kwargs)
  
        self.myDataBuffer = cDataBuffer(self.keys,5)
        
        # main UI window
        self.u = MW() 
        self.u.setupUi(self)
        
        # data source controller
        self.DSController = Control_Datasources()
        self.DSController.setup(self.myInstruments)
        
        # PAM controller
        self.PAMController = Control_PAM()
        self.PAMController.setup()
        
        # XES controller
        self.XESController = Control_XES()
        self.XESController.setup()
        
        # add keys to user defined fig axis:
        for key in self.myDataBuffer.keys:
            self.u.cb_fig_xaxis.addItem(key)
            self.u.cb_fig_yaxis.addItem(key)
        
        self.layout = qt.QGridLayout()
        self.u.widget.setLayout(self.layout)
        
        # self.u.plot_pam = Plot1D(backend = _backend, parent = self)
        # self.u.plot_pam.setGraphTitle('PAM signal')
        # self.u.plot_pam.getXAxis().setLabel('X (pixel)')
        # self.u.plot_pam.getYAxis().setLabel('PAM Modulation')
        # self.layout.addWidget(self.u.plot_pam,0,0)    
        self.u.plot_SPvsFrame_img = Plot2D(backend = _backend, parent = self)
        self.u.plot_SPvsFrame_img.setDefaultColormap(colormap)
        self.u.plot_SPvsFrame_img.setGraphTitle('JF image raw')
        self.u.plot_SPvsFrame_img.getXAxis().setLabel('X (pix)')
        self.u.plot_SPvsFrame_img.getYAxis().setLabel('Frame ') 
        self.layout.addWidget(self.u.plot_SPvsFrame_img,0,0)
        
        self.u.plot_UserDefinedFigure = Plot1D(backend = _backend, parent = self)
        self.u.plot_UserDefinedFigure.setGraphTitle('user defined figure')
        self.layout.addWidget(self.u.plot_UserDefinedFigure,0,1)    
        
        self.u.cb_fig_xaxis.setCurrentIndex(1)
        self.u.cb_fig_yaxis.setCurrentIndex(2)
        
        self.u.btn_getOneTrain.clicked.connect(self.receive_one)
        self.u.btn_streaming.toggled.connect(self.set_autorefresh)
        self.u.btn_connect.clicked.connect(self.connect_QBridgeClient)
        
        self.u.actionShow_PAM.triggered.connect(self.open_PAMController_window)
        self.u.actionShow_DataSource.triggered.connect(self.open_DataSourcesViewer_window)
        self.u.actionXES_setting.triggered.connect(self.open_XESController_window)
        
        self.u.cb_fig_xaxis.currentIndexChanged.connect(self.update_UserDefinedFigure)
        self.u.cb_fig_yaxis.currentIndexChanged.connect(self.update_UserDefinedFigure)
        
        self.u.btn_clearMyData.clicked.connect(self.reset)

        self.connect_QBridgeClient()      
        # self.reset()

    def keyPressEvent(self, event):
        ind_x = self.u.cb_fig_xaxis.currentIndex()
        ind_y = self.u.cb_fig_yaxis.currentIndex()
        nkeyx = self.u.cb_fig_xaxis.count()
        nkeyy = self.u.cb_fig_yaxis.count()
        
        if event.key() == Qt.Key_Plus:
            self.u.cb_fig_yaxis.setCurrentIndex((ind_y + nkeyy + 1) % nkeyy)
        if event.key() == Qt.Key_Minus:
            self.u.cb_fig_yaxis.setCurrentIndex((ind_y + nkeyy - 1) % nkeyy)
            
        if event.key() == Qt.Key_Asterisk:
            self.u.cb_fig_xaxis.setCurrentIndex((ind_x + nkeyx + 1) % nkeyx)
        if event.key() == Qt.Key_Slash:
            self.u.cb_fig_xaxis.setCurrentIndex((ind_x + nkeyx - 1) % nkeyx)
                
    @property        
    def Update_rate(self):
        try:
            rate = int(self.u.sb_updateRate.value())
        except:
            self.u.Message.append('Invalid update rate input! ')
        return rate

    @property
    def zmq_endpoint(self):
        return f'tcp://{self.u.IP.currentText()}:{self.u.PortNum.value()}'

    def connect_QBridgeClient(self):
        """IP address or port changed - update bridge_client"""
        if self.bridge_client is not None:
            self.bridge_client.stop()
            self.bridge_client = None
        try:
            self.bridge_client = QBridgeClient(endpoint = self.zmq_endpoint, parent=self)
            self.bridge_client.new_data.connect(self.train_received)
            self.bridge_client.start(stop_after=1)
            self.u.Message.append('connect OK')            
        except:
            self.u.Message.append('cant connect')
        self.u.rB_connected.setChecked(self.bridge_client is not None)

    def open_DataSourcesViewer_window(self):
        self.DSController.ReadData(self.dataBuff) # pass current data to DSController
        if self.DSController.subWindow_dsView.isVisible():
            self.DSController.subWindow_dsView.hide()
            self.DSController.subWindow_dsView.show()
        else:
            self.DSController.subWindow_dsView.show()

    def open_PAMController_window(self):
        if self.PAMController.subWindow_pv.isVisible():
            self.PAMController.subWindow_pv.hide()
            self.PAMController.subWindow_pv.show()

        else:
            self.PAMController.subWindow_pv.show()
        
        self.PAMController.update_PAMViewer()
    

    def open_XESController_window(self):
        if self.XESController.subWindow_xes.isVisible():
            self.XESController.subWindow_xes.hide()
            self.XESController.subWindow_xes.show()

        else:
            self.XESController.subWindow_xes.show()
        
        self.XESController.update_XESViewer()
    
    def set_autorefresh(self, on):        
        """Enable or disable continuous updates"""
        if self.bridge_client is not None:
            if not on:
                try:
                    self.bridge_client.stop()
                except:
                    self.u.Message.append('bridge client not responding')
            else:
                try:
                    self.bridge_client.start()
                except:
                    self.u.Message.append('bridge client not responding')

    def receive_one(self):
        """Update with 1 train from Karabo bridge"""
        if self.bridge_client is not None:
            try:
                self.bridge_client.start(stop_after=1)
            except:
                self.u.Message.append('bridge client not responding')

    def reset(self):
        """Clear data buffer"""
        self.myDataBuffer.clearAll()

    def train_received(self, data, metadata):

        self.dataBuff = data
        tid = -1        
        start = time.time()        
        event_is_good = True     
        
        
        # load PAM data
        if self.myInstruments['Gotthard'].IsActive == True:            
            try:
                inst_key = self.myInstruments['Gotthard'].Instrument_key
                data_key = self.myInstruments['Gotthard'].data_key
                ADC = data[inst_key][data_key]       

            except:
                self.u.Message.append('Gotthard signal is missing')
                event_is_good = False
            
            try:
                inst_key = self.myInstruments['Gotthard'].Instrument_key
                tid = metadata[inst_key]['timestamp.tid']
                self.u.Message.append(f'train {tid} received!')
                self.u.TrainID_disp.display(tid)
            except:
                self.u.Message.append('tid missing')
        else:

            ADC = None
            # event_is_good = False

        # load Delay stage data
        if self.myInstruments['Delay Stage'].IsActive == True:            
            try:
                inst_key = self.myInstruments['Delay Stage'].Instrument_key
                data_key = self.myInstruments['Delay Stage'].data_key
                DelayStage_pos = data[inst_key][data_key]
            except:
                self.u.Message.append('Delay stage postion is missiong')
                event_is_good = False
        else:
            DelayStage_pos = 0
        
        #load PPODL data:
        if self.myInstruments['PPODL'].IsActive == True:               
            try:
                inst_key = self.myInstruments['PPODL'].Instrument_key
                data_key = self.myInstruments['PPODL'].data_key
                Delay = data[inst_key][data_key]
            except:
                self.u.Message.append('PPODL data is missiong')
                event_is_good = False
        else:
            Delay = 0        
        
        # load JungFrau data
        if self.myInstruments['JF1'].IsActive == True:
            try:
                inst_key = self.myInstruments['JF1'].Instrument_key
                data_key = self.myInstruments['JF1'].data_key
                JF1 = data[inst_key][data_key]
                print(JF1.shape)

            except:
                self.u.Message.append('JF1 data is missiong')
                event_is_good = False
            try:
                inst_key = self.myInstruments['JF1'].Instrument_key
                tid = metadata[inst_key]['timestamp.tid']
                self.u.Message.append(f'train {tid} received!')
                self.u.TrainID_disp.display(tid)

            except:
                self.u.Message.append('tid missing')
        else:
            JF1 = None       
        
        
        if self.myInstruments['JF2'].IsActive == True:
            try:
                inst_key = self.myInstruments['JF2'].Instrument_key
                data_key = self.myInstruments['JF2'].data_key
                JF2 = data[inst_key][data_key]
                print(JF2.shape)

            except:
                self.u.Message.append('JF2 data is missiong')
                event_is_good = False
            try:
                inst_key = self.myInstruments['JF2'].Instrument_key
                tid = metadata[inst_key]['timestamp.tid']
                self.u.Message.append(f'train {tid} received!')
                self.u.TrainID_disp.display(tid)

            except:
                self.u.Message.append('tid missing')
        else:
            JF2 = None

        # load Digitizer data
        
        if self.myInstruments['Digi Raw'].IsActive == True:
            try:
                inst_key = self.myInstruments['Digi Raw'].Instrument_key
                data_key = self.myInstruments['Digi Raw'].data_key
                digi_raw = data[inst_key][data_key]

            except:
                self.u.Message.append('digi raw is missiong')
                # event_is_good = False
        else:
            digi_raw = None
        

        if self.myInstruments['Digi APD'].IsActive == True:
            try:
                inst_key = self.myInstruments['Digi APD'].Instrument_key
                data_key = self.myInstruments['Digi APD'].data_key
                digi_apd = data[inst_key][data_key]
            except:
                self.u.Message.append('digi apd is missiong')
                # event_is_good = False
        else:
            digi_apd = None
        
        end = time.time()
        print(f'load data in {end-start} s')
        
        start = time.time()
        
        if event_is_good == True:            
            if self.myInstruments['Gotthard'].IsActive == True:
                self.PAMController.pamAn.updateADC(ADC) 
                if self.PAMController.processData() == False:
                    self.u.Message.append('PAM process mistake in train_received function')
                    for m in self.PAMController.err_Msg:
                        self.u.Message.append(m)
                    self.PAMController.err_Msg.clear()
                    # return

            if self.myInstruments['JF1'].IsActive == True:
                print(JF1.shape)
                self.XESController.model_Jungfrau.updateJF(JF1,1)
                
            if self.myInstruments['JF2'].IsActive == True:
                print(JF2.shape)
                self.XESController.model_Jungfrau.updateJF(JF2,2)            
            
            if self.myInstruments['Digi Raw'].IsActive == True or self.myInstruments['Digi APD'].IsActive == True:
                self.XESController.model_digitizer.update_digi_data(digi_raw, digi_apd)
            
            # process loaded data in all analyzers 
            if self.XESController.processData() == False:
                self.u.Message.append('XES process mistake in train_received function')
                for m in self.XESController.err_Msg:
                    self.u.Message.append(m)
                self.XESController.err_Msg.clear()
                return 
            end = time.time()
            print(f'process data in {end-start} s')
            
            start = time.time()

            n_Xray_pulse = self.XESController.model_digitizer.nPulses # number of xray pulse on digitizer
            n_PP_pulse = self.XESController.model_XES.nPulses # number of on/off pairs on JF, or number of PP laser pulse
            n_pam_pulse = self.PAMController.pamAn.nPulses # number of white light pulse on Gotthard1 detector of PAM
            
            self.u.lcdNumber_digi_nPulse.display(n_Xray_pulse)
            self.u.lcdNumber_JF_nPulse.display(n_PP_pulse)
            self.u.lcdNumber_pam_pulse.display(n_pam_pulse)
             
            
            
            if self.XESController.model_XES.isIntraTrain == True:
                if 2*n_PP_pulse != n_Xray_pulse:
                    print(f'digitizer detect xray pulse number{n_Xray_pulse} is not equal to JF {n_PP_pulse*2}')
                    return
                
                for i in range(n_PP_pulse):
                    if self.myInstruments['Gotthard'].IsActive == True:  
                        pam_peak = self.PAMController.pam_peak_all[i]
                        pam_modulation = self.PAMController.pamAn.pam_modulation_all[i]
                        arrive_time = self.pamAn.pix_to_fs * self.PAMController.pam_peak_all[i]
                    else:
                        pam_peak = np.nan
                        pam_modulation = np.nan
                        arrive_time = np.nan
                        
                    _JF_sp = self.XESController.model_XES.output['JF_SP'][i] # JF signal intensity
                       
                    diff =  self.XESController.model_XES.output['SP_diff'][i//2]
                    # else:
                    outputData = {}
                    outputData['tid'] = tid
                    outputData['pam_peak'] = pam_peak
                    outputData['arrive_time'] = arrive_time
                    outputData['pam_modulation'] = pam_modulation
                    outputData['PPODL'] = Delay
                    outputData['Delay Stage'] = DelayStage_pos
                    try:
                        outputData['I0'] = self.XESController.model_XES.output['I0'][i]
                    except:
                        outputData['I0'] = np.nan
                    outputData['JF_SP'] = _JF_sp
                    outputData['JF_SP_diff'] = diff
                    self.myDataBuffer.push(outputData)
            else: # inter train mode:
                    
                    diff = self.XESController.model_XES.output['SP_diff']
                    _JF_sp = self.XESController.model_XES.output['JF_SP']
                    
                    if self.myInstruments['Gotthard'].IsActive == True:  
                        pam_peak = np.nanmean(self.PAMController.pam_peak_all)
                        pam_modulation = np.nanmean(self.PAMController.pamAn.pam_modulation_all)
                        arrive_time = np.nanmean(-self.pamAn.pix_to_fs * self.PAMController.pam_peak_all)
                    else:
                        pam_peak = np.nan
                        pam_modulation = np.nan
                        arrive_time = np.nan
                    
                    outputData = {}
                    outputData['tid'] = tid
                    outputData['pam_peak'] = pam_peak
                    outputData['arrive_time'] = arrive_time
                    outputData['pam_modulation'] = pam_modulation
                    outputData['PPODL'] = Delay
                    outputData['Delay Stage'] = DelayStage_pos
                    try:
                        outputData['I0'] = self.XESController.model_XES.output['I0']
                    except:
                        outputData['I0'] = np.nan
                    outputData['JF_SP'] = _JF_sp
                    outputData['JF_SP_diff'] = diff
                    self.myDataBuffer.push(outputData)
            '''
   keys = ['tid',
           'pam_peak',
           'arrive_time'
           'pam_modulation',
           'PPODL',
           'Delay Stage',
           'I0',
           # 'JF_SP',
           'JF_SP_diff'
           ]
            '''

            # self.myDataBuffer.push(outputData)
            self.u.Message.append(f'{self.myDataBuffer.allDataCount} data in buffer')
            
            # if self.PAMController.subWindow_pv.isVisible() == True:                
                # self.PAMController.update_PAMController()            
            self.update_UserDefinedFigure()
            self.update_SPdiff_img()
            # if self.myDataBuffer.streamCount == 0:
                # self.show_processed_img()
            if self.XESController.subWindow_xes.isVisible() == True:
                self.XESController.update_XESViewer()
     
        else:
            self.u.Message.append('bad event')
            
        end = time.time()
        print(f'update viwer in {end-start} s')  

            
    def update_UserDefinedFigure(self):
        try:
            df = self.myDataBuffer.get_Pandas_DataFrame()
            

            xkey = self.u.cb_fig_xaxis.currentText()
            ykey = self.u.cb_fig_yaxis.currentText()          
            xdata = df[xkey]
            ydata = df[ykey]

            gd = df.groupby(xkey)
            #xdata = np.asarray(gd[xkey].mean())

            #ydata = np.asarray(gd[ykey].mean())

            if xkey != 'tid':
                yerror = np.asarray(gd[ykey].std())
            else:
                yerror = 0

            self.u.plot_UserDefinedFigure.addCurve(x = xdata,
                                          y = ydata,
                                          # yerror = yerror,
                                          legend = f'{xkey} vs {ykey}',
                                          replace = True,
                                          color = 'blue',
                                          symbol = '.',
                                          linestyle = ''                                          
                                          )

            self.u.plot_UserDefinedFigure.getXAxis().setLabel(f'{xkey}')
            self.u.plot_UserDefinedFigure.getYAxis().setLabel(f'{ykey}')
        except:
            print('error ploting user defined figure')
    
    def update_UserDefinedFigure_new(self):
        try:
           
            xkey = self.u.cb_fig_xaxis.currentText()
            ykey = self.u.cb_fig_yaxis.currentText()
            
            xdata = self.myDataBuffer.avgBuff[xkey]
            xstreamdata = self.myDataBuffer.streamBuff[xkey]
            xerror = self.myDataBuffer.errorBuff[xkey]
                
            ydata = self.myDataBuffer.avgBuff[ykey]
            ystreamdata = self.myDataBuffer.streamBuff[ykey]
            yerror = self.myDataBuffer.errorBuff[ykey]            
            
            self.u.plot_UserDefinedFigure.addCurve(x = xdata,
                                          y = ydata,
                                          xerror = xerror,
                                          yerror = yerror,
                                          legend = f'{xkey} vs {ykey}',
                                          replace = True,
                                          color = 'blue',
                                          symbol = '.',
                                          linestyle = '-'                                          
                                          )
            self.u.plot_UserDefinedFigure.addCurve(x = xstreamdata,
                                          y = ystreamdata,
                                          replace = False,
                                          color = 'green',
                                          symbol = 'o',
                                          linestyle = ' '                                          
                                          )
            self.u.plot_UserDefinedFigure.getXAxis().setLabel(f'{xkey}')
            self.u.plot_UserDefinedFigure.getYAxis().setLabel(f'{ykey}')
            
        except:
            self.u.Message.append('cannot update user defined figure!')
 
    def update_SPdiff_img(self):

            df = self.myDataBuffer.get_Pandas_DataFrame()
            
            sp = []
            n=0
            for _s in df['JF_SP_diff'].values:
                if _s is not np.nan:
                    _s = np.asarray(_s, dtype = float)
                    n=n+1

                    sp.append(_s)
            

            try:
                _SP_diff = np.stack(sp)
                self.u.plot_SPvsFrame_img.addImage(_SP_diff[-300:])
            except:
                print('update_SPdiff_img wrong')

            
            
    def show_processed_img(self): 
        try:
            _pam = self.pamAn.pam_curve
            _smoothed_pam = self.pamAn.smoothed_pam
            xdata = np.asarray(range(len(_pam)), dtype = float)
            
            self.u.plot_pam.addCurve(x = xdata,
                                             y = _pam,
                                             color = 'green',
                                             symbol = '.',
                                             linestyle = '',
                                             replace = True,
                                             legend = 'pam raw')
            self.u.plot_pam.addCurve(x = xdata,
                                             y = _smoothed_pam,
                                             color = 'red',
                                             symbol = '',
                                             linestyle = '-',
                                             replace = False,
                                             legend = 'smoothed curve') 
        except:
            self.u.Message.append('cannot update image in main window!')
 
if __name__=="__main__":
    qapp = qt.QApplication([])
    window = MainLoop()
    window.show()
    qapp.exec_()
