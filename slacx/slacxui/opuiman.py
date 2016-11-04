import time
import os
from functools import partial

from PySide import QtCore, QtGui, QtUiTools
import qdarkstyle
import numpy as np

from ..slacxcore.operations import optools
from ..slacxcore.operations.slacxop import Operation 
from ..slacxcore.workflow.slacxwfman import WfManager
from ..slacxcore import slacxtools
from ..slacxcore.operations.optools import InputLocator
from . import uitools

class OpUiManager(object):
    """
    Stores a reference to the op_builder QGroupBox, 
    performs operations on it
    """

    def __init__(self,wfman,opman):
        ui_file = QtCore.QFile(slacxtools.rootdir+"/slacxui/op_builder.ui")
        # Load the op_builder popup
        ui_file.open(QtCore.QFile.ReadOnly)
        self.ui = QtUiTools.QUiLoader().load(ui_file)
        ui_file.close()
        self.wfman = wfman 
        self.opman = opman 
        self.op = None
        # Dicts to keep track of input widgets,
        # keyed by input variable names
        self.src_widgets = {} 
        self.type_widgets = {} 
        self.val_widgets = {} 
        self.inp_src_windows = {} 
        self.setup_ui()

    def get_op_from_tree(self,trmod,item_indx):
        xitem = trmod.get_item(item_indx)
        if xitem.n_data() > 0:
            x = xitem.data[0]
            # TODO: cleaner type checking?
            try:
                new_op_flag = issubclass(x,Operation)
            except:
                new_op_flag = False
            try:
                existing_op_flag = isinstance(x,Operation)
            except:
                existing_op_flag = False
            if not new_op_flag and not existing_op_flag:  
                self.clear_nameval_list()
                self.ui.op_info.setPlainText('Selected item: {}'.format(x))
            elif new_op_flag:
                # Create a new Operation 
                self.create_op(x)
            elif existing_op_flag:
                # Load existing Operation
                self.set_op(x,xitem.tag())

    def set_op(self,op,uri):
        self.op = op
        self.ui.op_info.setPlainText(self.op.description())
        self.build_nameval_list()
        self.ui.uri_entry.setText(uri)
        # Don't let uri change after already being loaded.
        self.ui.uri_entry.setReadOnly(True)

    def create_op(self,op):
        self.op = op()
        self.ui.op_info.setPlainText(self.op.description())
        self.build_nameval_list()
        self.ui.uri_entry.setText(self.wfman.next_tag())

    def test_op(self):
        print 'Operation testing not yet implemented'

    def load_op(self):
        """
        Package the finished self.op(Operation), ship to self.wfman
        """ 
        # Make sure all text inputs are loaded
        for name,val in self.op.inputs.items():
            src = self.src_widgets[name].currentIndex()
            if src == optools.text_input:
                self.load_text_input(name,self.type_widgets[name],self.val_widgets[name]) 
        uri = self.ui.uri_entry.text()
        result = self.wfman.is_good_tag(uri)
        if result[0]:
            self.wfman.add_op(self.op,uri) 
            #self.ui.close()
            #self.ui.deleteLater()
        elif result[1] == 'Tag not unique':
        # if uri represents existing op in workflow, overwrite
            #if uri in self.wfman.list_tags(QtCore.QModelIndex()):
            self.wfman.update_op(uri,self.op)
        else:
            # Request a different uri 
            msg_ui = slacxtools.start_message_ui()
            msg_ui.setParent(self.ui,QtCore.Qt.Window)
            msg_ui.setWindowTitle("Tag Error")
            msg_ui.message_box.setPlainText(
            'Tag error for {}: \n{} \n\n'.format(uri, result[1])
            + 'Enter a unique alphanumeric uri, '
            + 'using only letters, numbers, -, and _. (no periods). ')
            # Set button to activate on Enter key
            msg_ui.ok_button.setFocus()
            msg_ui.show()

    def clear_nameval_list(self):
        n_inp_widgets = self.ui.input_layout.count()
        for i in range(n_inp_widgets-1,-1,-1):
            item = self.ui.input_layout.takeAt(i)
            item.widget().deleteLater()
        n_out_widgets = self.ui.output_layout.count()
        for i in range(n_out_widgets-1,-1,-1):
            item = self.ui.output_layout.takeAt(i)
            item.widget().deleteLater()

    def clear_input_widgets(self):
        for name,widg in self.inp_src_windows.items():
            src_tup = self.inp_src_windows.pop(name)
            src_tup[1].close()
            src_tup[1].deleteLater()

    def build_nameval_list(self):
        self.clear_nameval_list()
        self.clear_input_widgets()
        inp_count = len(self.op.inputs.items())
        out_count = len(self.op.outputs.items())
        #self.input_rows = []
        #print 'found {} inputs to render'.format(inp_count)
        if inp_count:
            self.input_header_widgets(0)
            i=1
            for name, val in self.op.inputs.items():
                #print 'rendering input {}'.format(i)
                self.add_input_widgets(name,val,i)
                i+=1
        if out_count:
            self.output_header_widgets(0)
            i=1 
            for name, val in self.op.outputs.items():
                self.add_output_widgets(name,i)
                i+=1 

    def input_header_widgets(self,row):
        self.ui.input_layout.addWidget(uitools.hdr_widget('name'),row,self.name_col,1,1)
        self.ui.input_layout.addWidget(uitools.hdr_widget('source'),row,self.src_col,1,1)
        self.ui.input_layout.addWidget(uitools.hdr_widget('type'),row,self.type_col,1,1)
        self.ui.input_layout.addWidget(uitools.hdr_widget('value'),row,self.val_col,1,1)

    def output_header_widgets(self,row):
        self.ui.output_layout.addWidget(uitools.hdr_widget('name'),row,self.name_col,1,1)
        self.ui.output_layout.addWidget(uitools.hdr_widget('description'),row,self.src_col,1,self.btn_col-self.src_col)

    def add_input_widgets(self,name,val,row):
        """Loads a set of widgets for setting or reading input or output data"""
        name_widget = uitools.namewidget(name)
        self.ui.input_layout.addWidget( name_widget,row,self.name_col,1,1 )
        eq_widget = uitools.smalltext_widget('=')
        eq_widget.setMaximumWidth(20)
        self.ui.input_layout.addWidget(eq_widget,row,self.eq_col,1,1)
        src_widget = uitools.src_selection_widget() 
        self.src_widgets[name] = src_widget 
        #val_widget = QtGui.QLineEdit(str(val))
        self.ui.input_layout.addWidget(src_widget,row,self.src_col,1,1)
        src_widget.activated.connect( partial(self.render_input_widgets,name,val,row) )
        src_widget.setCurrentIndex(self.op.input_src[name])
        self.render_input_widgets(name,val,row,self.op.input_src[name]) 
        #name_widget.resize(10,name_widget.size().height())
        ht = name_widget.sizeHint().height()
        name_widget.sizeHint = lambda: QtCore.QSize(8*len(name_widget.text()),ht)
        name_widget.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Fixed)

    def add_output_widgets(self,name,row):
        name_widget = uitools.namewidget(name)
        self.ui.output_layout.addWidget(name_widget,row,self.name_col)
        eq_widget = uitools.smalltext_widget('=')
        eq_widget.setMaximumWidth(20)
        self.ui.output_layout.addWidget(eq_widget,row,self.eq_col)
        desc_widget = uitools.bigtext_widget(self.op.output_doc[name])
        self.ui.output_layout.addWidget(desc_widget,row,self.src_col,1,self.btn_col-self.src_col)
        ht = desc_widget.sizeHint().height()
        name_widget.sizeHint = lambda: QtCore.QSize(8*len(name_widget.text()),ht)
        desc_widget.sizeHint = lambda: QtCore.QSize(20*len(desc_widget.text()),ht)
        name_widget.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Fixed)
        desc_widget.setSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Fixed)

    def render_input_widgets(self,name,val,row,src_indx): 
        # If input widgets exist, close them.
        for col in [self.type_col,self.val_col,self.btn_col]:
            if self.ui.input_layout.itemAtPosition(row,col):
                widg = self.ui.input_layout.itemAtPosition(row,col).widget()
                widg.hide()
                widg.deleteLater()
        if src_indx == optools.no_input:
            type_widget = QtGui.QLineEdit('none')
            val_widget = QtGui.QLineEdit('none')
            type_widget.setReadOnly(True)
            val_widget.setReadOnly(True)
            btn_widget = None
        elif src_indx == optools.text_input:
            type_widget = QtGui.QComboBox()
            type_widget.addItems(optools.input_types)
            #if self.op.input_type[name]:
            type_widget.setCurrentIndex(self.op.input_type[name])
            val_widget = QtGui.QLineEdit()
            if self.op.inputs[name]:
                val_widget.setText(str(self.op.inputs[name]))
            elif uitools.have_qt47:
                val_widget.setPlaceholderText('(enter value)')
            else:
                val_widget.setText('')
            btn_widget = None
        elif (src_indx == optools.op_input
            or src_indx == optools.fs_input):
            if self.op.inputs[name]:
                if isinstance(self.op.inputs[name],InputLocator):
                    # op.inputs[name] should have a uri stored as its val
                    val = self.op.inputs[name].val
                else:
                    # op.inputs[name] has already been loaded from its InputLocator
                    val = self.op.inputs[name]
                val_widget = QtGui.QLineEdit(str(val))
                if src_indx == optools.fs_input:
                    type_widget = QtGui.QLineEdit('file path')
                elif src_indx == optools.op_input:
                    type_widget = QtGui.QLineEdit(type(val).__name__)
            else:
                type_widget = QtGui.QLineEdit('type: auto')
                val_widget = QtGui.QLineEdit('value: select ->')
            type_widget.setReadOnly(True)
            val_widget.setReadOnly(True)
            btn_widget = QtGui.QPushButton('browse...')
            btn_widget.clicked.connect( partial(self.fetch_data,name,src_indx,type_widget,val_widget) )
        else:
            msg = 'source selection {} not recognized'.format(src_indx)
            raise ValueError(msg)
        self.ui.input_layout.addWidget(type_widget,row,self.type_col,1,1)
        self.type_widgets[name] = type_widget
        self.ui.input_layout.addWidget(val_widget,row,self.val_col,1,1)
        self.val_widgets[name] = val_widget
        if btn_widget:
            self.ui.input_layout.addWidget(btn_widget,row,self.btn_col,1,1)
        #self.fetch_data(name,src_indx,type_widget,val_widget)

    def load_text_input(self,name,type_widg,val_widg,edit_text=None):
        type_indx = type_widg.currentIndex()
        if type_indx == optools.int_type:
            val = int(val_widg.text())
        elif type_indx == optools.float_type:
            val = float(val_widg.text())
        #elif src_indx == optools.array_type:
        #    val = np.array(val_widg.text())
        elif type_indx == optools.str_type:
            val = val_widg.text()
        else:
            msg = 'type selection {}, should be between 1 and {}'.format(type_indx,len(optools.valid_types))
            raise ValueError(msg)
        self.op.inputs[name] = optools.InputLocator(optools.text_input,val)
        self.ui.op_info.setPlainText(self.op.description())

    def fetch_data(self,name,src_indx,type_widg,val_widg):
        """Use a popup to select the input data"""
        if name in [k for k,v in self.inp_src_windows.items()]:
            if src_indx == self.inp_src_windows[name][0]:
                self.inp_src_windows[name][1].raise_()
                self.inp_src_windows[name][1].activateWindow()
                return
            else:
                oldwidg = self.inp_src_windows.pop(name)
                oldwidg[1].close()
                oldwidg[1].delteLater()
#        else:
        ui_file = QtCore.QFile(slacxtools.rootdir+"/slacxui/tree_browser.ui")
        ui_file.open(QtCore.QFile.ReadOnly)
        src_ui = QtUiTools.QUiLoader().load(ui_file)
        ui_file.close()
        src_ui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        src_ui.setParent(self.ui,QtCore.Qt.Window)
        if src_indx == optools.op_input:
            trmod = self.wfman
        elif src_indx == optools.fs_input:
            trmod = QtGui.QFileSystemModel()
            trmod.setRootPath('.')
        src_ui.tree.setModel(trmod)
        src_ui.tree_box.setTitle(name)
        self.inp_src_windows[name] = (src_indx,src_ui)
        src_ui.tree.expandAll()
        src_ui.tree.resizeColumnToContents(0)
        src_ui.load_button.setText('Load selected data')
        src_ui.load_button.clicked.connect(partial(self.load_from_tree,name,trmod,src_ui,src_indx,type_widg,val_widg))
        src_ui.tree.doubleClicked.connect(partial(self.load_from_tree,name,trmod,src_ui,src_indx,type_widg,val_widg))
        if src_indx == optools.fs_input:
            src_ui.tree.hideColumn(1)
            src_ui.tree.hideColumn(3)
            src_ui.tree.setColumnWidth(0,400)
        src_ui.show()
        src_ui.raise_()
        src_ui.activateWindow()

    def load_from_tree(self,name,trmod,src_ui,src_indx,type_widg,val_widg,item_indx=None):
        """
        Construct a unique resource identifier (uri) for the selected item.
        Set self.op.inputs[name] to be an optools.InputLocator(src_indx,uri).
        Also set that uri to be the text of val_widg.
        Finally, reset self.ui.op_info to reflect the changes.
        """
        trview = src_ui.tree
        if not item_indx or not item_indx.isValid():
            # Get the selected item in QTreeView trview:
            item_indx = trview.currentIndex()
        if src_indx == optools.fs_input:
            # Get the path of the selection
            item_uri = trmod.filePath(item_indx)
            type_widg.setText('file path')
        elif src_indx == optools.op_input:
            # Build a unique URI for this item
            item_uri = trmod.build_uri(item_indx)
            type_widg.setText(type(trmod.get_item(item_indx).data[0]).__name__)
        val_widg.setText(item_uri)
        #val_widg.setMinimumWidth(min([8*len(item_uri),200]))
        #val_widg.setMaximumWidth(200)
        self.op.inputs[name] = optools.InputLocator(src_indx,item_uri)
        self.ui.op_info.setPlainText(self.op.description())
        src_ui.close()
        src_ui.deleteLater()
        self.inp_src_windows.pop(name)
        
    #def update_op_info(self,text):
    #    self.ui.op_info.setPlainText(text)

    #def update_op_selector(self,sel_indx,desel_indx):
    #    # Send a signal to op_selector to set currentIndex to sel_indx
    #    self.ui.op_selector.setCurrentIndex(sel_indx)

    def setup_ui(self):
        self.ui.setWindowTitle("operation setup")
        self.ui.input_box.setTitle("INPUTS")
        self.ui.output_box.setTitle("OUTPUTS")
        self.ui.finish_box.setTitle("FINISH / LOAD")
        #self.ui.input_box.setMinimumWidth(600)
        #self.ui.op_frame.setMinimumWidth(400)
        #self.ui.op_frame.setMaximumWidth(400)
        ht = self.ui.op_frame.sizeHint().height()
        self.ui.op_frame.sizeHint = lambda: QtCore.QSize(400,ht)
        self.ui.op_frame.setSizePolicy(
        QtGui.QSizePolicy.Minimum,self.ui.op_frame.sizePolicy().verticalPolicy())
        self.ui.wf_selector.setModel(self.wfman)
        self.ui.wf_selector.hideColumn(1)
        self.ui.wf_selector.clicked.connect( partial(self.get_op_from_tree,self.wfman) )
        self.ui.op_selector.setModel(self.opman)
        self.ui.op_selector.hideColumn(1)
        self.ui.op_selector.clicked.connect( partial(self.get_op_from_tree,self.opman) )
        self.ui.op_selector.activated.connect( partial(self.get_op_from_tree,self.opman) )
        # Populate uri entry fields
        self.ui.uri_prompt.setText('operation uri:')
        #self.ui.uri_prompt.setMaximumWidth(150)
        #self.ui.uri_entry.setMaximumWidth(150)
        self.ui.uri_prompt.setReadOnly(True)
        self.ui.uri_prompt.setAlignment(QtCore.Qt.AlignRight)
        self.ui.uri_prompt.setStyleSheet( "QLineEdit { background-color: transparent }" 
        + self.ui.uri_prompt.styleSheet() )
        self.ui.test_button.setText("&Test")
        self.ui.test_button.setEnabled(False)
        self.ui.test_button.clicked.connect(self.test_op)
        self.ui.load_button.setText("&Load")
        self.ui.load_button.clicked.connect(self.load_op)
        self.ui.load_button.setDefault(True)
        self.ui.test_button.setMinimumWidth(100)
        self.ui.load_button.setMinimumWidth(100)
        self.ui.exit_button.setText("E&xit")
        self.ui.exit_button.hide()
        self.ui.exit_button.clicked.connect(self.ui.close)
        self.ui.exit_button.clicked.connect(self.ui.deleteLater)
        self.ui.splitter.setStretchFactor(0,1000)    
        #self.ui.returnPressed.connect(self.load_op)
        self.ui.setStyleSheet( "QLineEdit { border: none }" + self.ui.styleSheet() )
        self.ui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.name_col = 1
        self.eq_col = 2
        self.src_col = 3
        self.type_col = 4
        self.val_col = 5
        self.btn_col = 6


