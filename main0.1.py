from PyQt5 import QtWidgets, uic #Importamos o QtWidgets para podermos utilizar a QMainWindow
from matplotlib.figure import Figure #Importamos o QtWidgets para podermos utilizar a QMainWindow, o uic para poder importar nosso arquivo .ui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas #Importamos o figure canvas
from PyQt5.QtGui import QIcon #Importamos o QIcon para podermos trocar o ícone da janela
import sys #Importamos o sys para podermos controlar quando saimos do programa

'''Aqui criamos uma classe que herda os métodos da
Figure Canvas do Matplotlib'''

class MatPlotLibCanvas(FigureCanvas):
   def __init__(self, parent=None, width=10, height=3, dpi=100): #criamos o método inicializador da classe e estabelecemos alguns parâmetros padrão
       figura = Figure(figsize=(width, height), dpi=dpi) #Criamos uma figura utilizando a classe Figure
       self.axes = figura.add_subplot(111) #Adicionamos um eixo para plotagem
       super(MatPlotLibCanvas, self).__init__(figura) #Chamamos o método de inicialização da superclasse
       figura.tight_layout() #O método tight_layout ajusta a figura dentro do canvas

'''Criamos nossa classe main window com herança da QMainWindow
e chamamos seu método inicializador'''

class MainWindow(QtWidgets.QMainWindow):
   def __init__(self):
       QtWidgets.QMainWindow.__init__(self)

       self.ui = uic.loadUi("main0.1_integracao_mpl.ui", self) #Podemos importar nosso arquivo ui criado no QT Designer
       self.ui.setWindowIcon(QIcon('ifc.png')) #Carregamos o ícone novo

       self.canvas1 = MatPlotLibCanvas(self, width=6, height=2.1, dpi=100) #Criamos o nosso objeto canvas1
       self.ui.gridLayout_4.addWidget(self.canvas1, 2, 1, 1, 1) #Adicionamos o canvas1 ao nosso layout

app = QtWidgets.QApplication(sys.argv) #Criamos o objeto QApplication

if __name__ == "__main__": #Verifica se estamos no main ou fomos importados como módulo
   mainWindow = MainWindow() #Criamos o objeto com a nossa classe MainWindow
   mainWindow.show() #Mostramos a janela
   sys.exit(app.exec_()) #Caso se saia do programa, o python finaliza o processo