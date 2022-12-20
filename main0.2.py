from PyQt5 import QtWidgets, uic, QtCore #Importamos o QtWidgets para podermos utilizar a QMainWindow, o uic para poder importar nosso arquivo .ui e o qtcore para podermos criar nossas linhas de processo
from matplotlib.figure import Figure #Importamos a Figura do Matplotlib para que possamos utilizar a classe dentro do nosos canvas
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas #Importamos o figure canvas
from PyQt5.QtGui import QIcon #Importamos o QIcon para podermos trocar o ícone da janela
import sys #Importamos o sys para podermos controlar quando saimos do programa
from PyQt5.QtCore import pyqtSlot #Importamos o pyqtSlot para poder trabalhar com multiplas linhas de código simultâneas
import numpy as np #Importamos o numpy para utilizar suas classes de vetores para receber os dados de som
import sounddevice as sd #Importamos o para poder estabelecer comunicação com os dispositivos de áudio e receber dados
from PyQt5.QtMultimedia import QAudioDeviceInfo, QAudio #Serve simplesmente para listarmos os nomes dos dispositivos de áudio do computador

infos_disp_audio = QAudioDeviceInfo.availableDevices(QAudio.AudioInput)# criamos um objeto que contem os dispositivos de áudio disponíveis no computador

'''Aqui criamos uma classe que herda os métodos da
Figure Canvas do Matplotlib'''

class MatPlotLibCanvas(FigureCanvas):
   def __init__(self, parent=None, width=10, height=3, dpi=100): #Criamos o método inicializador da classe e estabelecemos alguns parâmetros padrão
       figura = Figure(figsize=(width, height), dpi=dpi) #Criamos uma figura utilizando a classe Figure
       self.axes = figura.add_subplot(111) #Adicionamos um eixo para plotagem
       super(MatPlotLibCanvas, self).__init__(figura) #Chamamos o método de inicialização da superclasse
       figura.tight_layout() #O método tight_layout ajusta a figura dentro do canvas

'''Criamos nossa classe main window com herança da QMainWindow
e chamamos seu método inicializador'''

class MainWindow(QtWidgets.QMainWindow):
   def __init__(self):
       QtWidgets.QMainWindow.__init__(self)

       self.ui = uic.loadUi("main0.2_aquisição_de_dados.ui", self) #Podemos importar nosso arquivo ui criado no QT Designer
       self.ui.setWindowIcon(QIcon('ifc.png')) #Carregamos o ícone novo

       self.threadpool = QtCore.QThreadPool() #Criamos um objeto da classe QThreadPool

       self.lista_dispositivos = [] #Uma lista de dispositivos sem nada ainda

       '''Inserimos o nome dos dispositivos de áudio da lista de dispositivos do computador na nossa lista vazia
       utilizando a lógica: para cada elemento da lista de dispositivos, insira o nome elemento na lista vazia'''
       for item in infos_disp_audio:
           self.lista_dispositivos.append(item.deviceName())

       self.comboBox.addItems(self.lista_dispositivos) #Adicionamos os itens da nossa lista na comboBox
       self.comboBox.currentIndexChanged["QString"].connect(self.atualizar_canal1) #Caso o valor da comboBox mude, enviamos esse valor para a função atualizar canal
       self.comboBox.setCurrentIndex(0) #Começamos o programa com a comboBox no valor 0

       self.canvas1 = MatPlotLibCanvas(self, width=6, height=2.1, dpi=100) #Criamos o nosso objeto canvas1
       self.ui.gridLayout_4.addWidget(self.canvas1, 2, 1, 1, 1) #Adicionamos o canvas1 ao nosso layout

       # Intervalo de atualização da plotagem e do programa:
       self.intervalo = 30  #controle do intervalo do temporizador em milisegundos

       #Variáveis para plotagem do sinal
       self.tam_janela1 = 1000  #Tamanho da janela de dados em milisegundos
       self.pular_amostra1 = 1  #Pula 1 amostra
       self.canais1 = [1] #Número de Canais

       '''Fazemos um teste utilizando nossa lista de dispositivos e checamos se podemos
       captar se eles são identificados pela biblioteca sounddevice. Caso sejam, marcamos a variável
       achou_dispositivo indicando sucesso'''
       for self.dispositivo1 in range(len(infos_disp_audio)):
           try:
               device_info = sd.query_devices(self.dispositivo1, "input")
               if device_info:
                   self.achou_dispositivo = True
                   break
           except:
               pass

       '''Caso exista um dispositivo acessável pela biblioteca sounddevice, seguimos com o código.
       Caso não exista, podemos desativar o botão para mostrar os dados e marcar que não existem
       dispositivos acessíveis no comboBox'''
       if self.achou_dispositivo:  #Roda caso se ache um dispositivo
           self.taxa_amostra_1 = device_info["default_samplerate"] #Coletamos a taxa de amostragem padrão do dispositivo
           tamanho_1 = int(self.tam_janela1 * self.taxa_amostra_1 /
                        (1000 * self.pular_amostra1)) #Calculamos o tamanho da janela para futura plotagem dos dados
           sd.default.samplerate = self.taxa_amostra_1 #Setamos a taxa de amostragem do dispositivo (Que nesse caso é a taxa de amostragem padrão)
       else:
           self.pushButton.setEnabled(False) #Desligamos o botão para adquirir os dados
           self.lista_dispositivos.append("No Devices Found") #Inserimos na lista a informação que não há dispositivos disponíveis
           self.comboBox.addItems(self.lista_dispositivos) #Inserimos a lista na comboBox
       self.achou_dispositivo = False #Resetamos a variável

       self.timer = QtCore.QTimer() #Criamos um objeto do tipo timer para controle temporal do programa
       self.timer.setInterval(self.intervalo)  #Atribuimos o intervalo do temporizador em milisegundos
       self.timer.start() #Começamos a contar o tempo

       self.pushButton.clicked.connect(self.start_worker_1) #Caso o botão 1 seja clicado, iniciamos a função start worker
       self.pushButton_2.clicked.connect(self.stop_worker_1) #Caso o botão 2 seja clicado, iniciamos a função stop worker

   '''A função que coleta o sinal de audio de um dado dispositivo selecionado na função atualizar canal.
   Começamos com o comando try, que realiza o código e caso ocorra uma exceção, se informa um código
   de erro no terminal e se chama a função stop worker com o objetivo de parar o recebimento de dados'''
   def pegarAudio_1(self):
       try:
           QtWidgets.QApplication.processEvents() #Método utilizado para processar eventos da interface de usuário, utilizamos para que se possa receber comandos do usuário enquanto essa função é executada

           '''A função audio callback é chamada pelo objeto stream1 do tipo input stream.
           A lógica é que podemos alterar a formação dos dados recebidos do áudio de acordo com a nossa função.
           Também aproveitamos essa função que é chamada constantemente para informar os dados que estamso recebendo'''
           def audio_callback_1(indata, frames, time, status): #A função recebe como parâmetro os dados que estão entrando (indata)
               self.printdata = (indata[:: self.pular_amostra1, [0]]) #Utilizamos a variável pular amostra para pular algumas amostras da torrente de dados (indata)
               print(self.printdata) #Escrevemos no terminal os dados recebidos
               print('Dados Adquiridos') #Escrevemos no terminal a mensagem Dados Adquiridos
               print(self.dispositivo1) #Escrevemos o númeor do dispositivo de onde vem os dados

           '''Criamos o objeto stream, que constantemente recebe os valores do dispositivo de audio de acordo
           com nossas variáveis'''
           stream1 = sd.InputStream(
               device=self.dispositivo1,
               channels=max(self.canais1),
               samplerate=self.taxa_amostra_1,
               callback=audio_callback_1,
           )
           with stream1: #Enquanto tivermos valores para stream1

               '''Entramos no loop que procura atualizações da interface e por consequencia, dos valores das variáveis'''
               while True:
                   QtWidgets.QApplication.processEvents()
                   if self.go_on1: #Caso a variável para seguir com o programa seja ativada, paramos o loop e continuamos com o programa
                       break

       except Exception as e: #Caso uma exceção seja encontrada
           print("ERROR: ", e) #Mostramos o erro
           self.stop_worker_1 #Paramos o recebimento dos dados
           pass

   def atualizar_canal1(self, value): #Atualiza o dispositivo atual
       self.dispositivo1 = self.lista_dispositivos.index(value)

   def start_stream_1(self): #Função que puxa a função pegar audio - Essa é a função passada para o objeto worker
       self.pegarAudio_1()

   def start_worker_1(self): #Começa o worker com a nossa função start stream como parâmetro

       self.go_on1 = False #Variável falsa para que possamos mostrar o audio - Ver a função pegar Audio
       '''O trabalhador é iniciado com a função start stream para que possamos rodá-la em paralelo
       com a interface principal'''
       self.worker1 = Worker(
           self.start_stream_1,
       )
       self.threadpool.start(self.worker1) #O administrador inicia o trabalhador
       self.timer.setInterval(self.intervalo)  #Atualizamos o intervalo, caso tenha sido alterado

   def stop_worker_1(self): #Ativamos a variável que pausa o recebimento de dados

       self.go_on1 = True

class Worker(QtCore.QRunnable): #Criamos a classe worker utilizando o Qrunnable como superclasse
   def __init__(self, function, *args, **kwargs): #Criamos o método de inicialização da classe, e indicamos que não temos um número específico de argumentos na função com *args e *kwargs, além de receber a função como argumento
       super(Worker, self).__init__()
       self.function = function #A função do argumento é recebida
       self.args = args #Os argumentos são recebidos
       self.kwargs = kwargs #Os argumentos chave são recebidos

   @pyqtSlot() #Decorador utilizado para indicar que esse método deve ser usado como slot Qt
   def run(self): #O método run, nesse caso
       self.function(*self.args, **self.kwargs) #Rodamos a função em uma linha de código separada por meio do método Run do QRunnable

app = QtWidgets.QApplication(sys.argv) #Criamos o objeto QApplication

if __name__ == "__main__": #Verifica se estamos no main ou fomos importados como módulo
   mainWindow = MainWindow() #Criamos o objeto com a nossa classe MainWindow
   mainWindow.show() #Mostramos a janela
   sys.exit(app.exec_()) #Caso se saia do programa, o python para também