# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'View_DataSources.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

# import sys, os
# sys.path.append(os.path.join(os.path.dirname(sys.path[0]),'View'))


from PyQt5 import QtCore, QtGui, QtWidgets
from View.View_DataSourcesUI import Ui_View_Datasources

class Control_Datasources(Ui_View_Datasources):
    
    def setup(self, myInstruments):
        self.myInstruments = myInstruments
        self.subWindow_dsView = QtWidgets.QMainWindow()
        self.subWindow_dsView.setWindowTitle('Data Source Viewer')
        self.setupUi(self.subWindow_dsView)
        
        for row, k in enumerate(myInstruments.keys()):
            item_name = QtWidgets.QTableWidgetItem(myInstruments[k].Name)
            # item_name.setFlags(~QtCore.Qt.ItemIsEditable)
            item_inst_key = QtWidgets.QTableWidgetItem(myInstruments[k].Instrument_key)
            item_data_key = QtWidgets.QTableWidgetItem(myInstruments[k].data_key)
            item_isActive = QtWidgets.QTableWidgetItem(f'{myInstruments[k].IsActive}')
            
            
            self.tableWidget.setItem(row,0,item_name)
            self.tableWidget.setItem(row,1,item_inst_key)
            self.tableWidget.setItem(row,2,item_data_key)
            self.tableWidget.setItem(row,3,item_isActive)
        
        self.tableWidget.clicked.connect(self._get_target_instrument)
        self.btn_disable.clicked.connect(self._disable_target_instrument)
        self.btn_enable.clicked.connect(self._enable_target_instrument)
        self.btn_UpdateInstrument.clicked.connect(self.updateInstrument)
    
    def _get_target_instrument(self, item):
        self.target_row = item.row()
        item = self.tableWidget.item(self.target_row,0)
        if item is not None:
            self.Target_Instr_name.setText(item.text())
        else:
            self.Target_Instr_name.setText('')
    
    def _disable_target_instrument(self):
        item = self.tableWidget.item(self.target_row,0)
        if item is not None:
            self.tableWidget.setItem(self.target_row,3,QtWidgets.QTableWidgetItem('False'))
    
    def _enable_target_instrument(self):
        item = self.tableWidget.item(self.target_row,0)
        if item is not None:
            self.tableWidget.setItem(self.target_row,3,QtWidgets.QTableWidgetItem('True'))

    def _loadSources(self, root, gen, source):
        if type(source) == dict:
            for key in source.keys():                       
                _item = QtWidgets.QTreeWidgetItem(root) # add an item to 1st column of tree
                _item.setText(gen, key)
                root.addChild(_item)
                self._loadSources(_item, gen, source[key])
        else:
                _item = QtWidgets.QTreeWidgetItem(root)
                _item.setText(gen, f'{source}')
                root.addChild(_item)
                
    def ReadData(self,data):
        self.treeWidget.clear()
        self.root = QtWidgets.QTreeWidgetItem(self.treeWidget)
        self.root.setText(0,'All Data')
        self._loadSources(self.root, 0, data)
        
    def _getSelData(self):
        sel = self.treeWidget.selectedItems()
        if len(sel) > 0:
            data_key = sel[0].text(0)
            ins_key = sel[0].parent().text(0)
            return [ins_key, data_key]
        else:
            return None
        
    def LoadInstrumentsTable(self):
        nRow = self.tableWidget.rowCount()

        self.myInstruments.clear()
        for row in range(nRow):
            if self.tableWidget.item(row,0) is not None:
                _name = self.tableWidget.item(row,0).text()
                _instr_key = self.tableWidget.item(row,1).text()
                _data_key = self.tableWidget.item(row,2).text()
                _isActive = eval(self.tableWidget.item(row,3).text()) == True
                inst =cInstrument(Name = _name, 
                                   Instrument_key = _instr_key, 
                                   data_key = _data_key,
                                   IsActive = _isActive)
                
                self.myInstruments[_name] = inst

    
    def updateInstrument(self):
        r = self._getSelData()
        if r is not None:
            _instr_key = QtWidgets.QTableWidgetItem(r[0])
            _data_key = QtWidgets.QTableWidgetItem(r[1])
            item = self.tableWidget.item(self.target_row,0)
            if item is not None:
                self.tableWidget.setItem(self.target_row,1,_instr_key)
                self.tableWidget.setItem(self.target_row,2,_data_key)
                if self.tableWidget.item(self.target_row,3) is None:
                    self.tableWidget.setItem(self.target_row,3,QtWidgets.QTableWidgetItem('False'))
        try:
            self.LoadInstrumentsTable()
        except:
            print('canot update myInstruments')
        



#%% cInstrument
class cInstrument:
    
    def __init__(self, Name, Instrument_key, data_key, IsActive):
        self.Name = Name
        self.Instrument_key = Instrument_key
        self.data_key = data_key
        self.IsActive = IsActive
    
    def disable(self):
        self.IsActive = False
        
        
#%%
if __name__ == "__main__":
    data = {'FXE_OGT2_CRL/MOTOR/CHAM_Z': {'metadata': {'source': 'FXE_OGT2_CRL/MOTOR/CHAM_Z',
       'timestamp.tid': 1803613837},
      'actualPosition.value': -78.06169802799559},
     'FXE_SMS_MOV/CAM/XEYE:daqOutput': {'metadata': {'source': 'FXE_SMS_MOV/CAM/XEYE:daqOutput',
       'timestamp.tid': 1803613837},
      'data.image.pixels': '2d array data'}}
    myInstruments = {}
    myInstruments['Gotthard'] = cInstrument(Name = 'Gotthard', 
                       Instrument_key = 'FXE_OGT3_PAM/DET/RECEIVER_REF:daqOutput', 
                       data_key = 'data.adc',
                       IsActive = True)
    
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
                       data_key = 'data.adc', 
                       IsActive = False)
    
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = Control_Datasources()
    ui.setup(myInstruments,data)
    ui.subWindow_dsView.show()
    sys.exit(app.exec_())
