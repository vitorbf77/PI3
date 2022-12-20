from PyQt5 import uic, QtCore, QtWidgets #Importamos o QtWidgets para podermos utilizar a QMainWindow, o uic para poder importar nosso arquivo .ui e o qtcore para podermos criar nossas linhas de processo
from PyQt5.QtMultimedia import QAudioDeviceInfo, QAudio #Serve simplesmente para listarmos os nomes dos dispositivos de áudio do computador
from PyQt5.QtCore import pyqtSlot #Importamos o pyqtSlot para poder trabalhar com multiplas linhas de código simultâneas
from PyQt5.QtCore import QUrl #Módulo para lidar com endereços url
from PyQt5.QtWebEngineWidgets import QWebEngineView #Módulo para utilizar um navegador compacto dentro da interface
from PyQt5.QtGui import QIcon #Importamos o QIcon para podermos trocar o ícone da janela

import sounddevice as sd #Importamos o para poder estabelecer comunicação com os dispositivos de áudio e receber dados

import numpy as np #Importamos o numpy para utilizar suas classes de vetores para manipulação dos dados

import queue #Fila para comunicação entre o método recebeDados e o método atualizar_canvas.
'''Podemos utilizar a queue para impedir que 2 funções (que rodam em linhas 
distintas de execução - ou threads, em inglês) tentem acessar o mesmo 
espaço de memória simultâneamente, o que pode causar multiplos erros'''

from matplotlib.figure import Figure #Importamos a Figura do Matplotlib para que possamos utilizar a classe dentro do nosos canvas
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas #Importamos o figure canvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavTool
'''Classe navigation tool do figure canvas, nos permite alterar
algumas propriedades dos gráficos do matplotlib enquanto
estamos plotando'''

import sys #Importamos o sys para podermos controlar quando saimos do programa

import pandas as pd #Pandas é uma biblioteca extremamente útil para manipulação de dados

infos_disp_audio = QAudioDeviceInfo.availableDevices(QAudio.AudioInput) #Criamos um objeto que contem os dispositivos de áudio disponíveis no computador

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

        '''Inicializamos as variáveis que conterão os dados a serem plotados para cada canal'''
        self.dataY1 = None
        self.dataY2 = None
        self.dataY3 = None
        self.dataY4 = None
        self.dataY5 = None

        self.ui = uic.loadUi("main_programa_final.ui", self) #Podemos importar nosso arquivo ui criado no QT Designer
        self.showMaximized() #Mostramos a janela maximizada assim que ela é aberta
        self.ui.setWindowIcon(QIcon('ifc.png')) #Carregamos o ícone novo

        self.threadpool = QtCore.QThreadPool() #Criamos um objeto da classe QThreadPool para controle dos workers

        self.lista_dispositivos = [] #Uma lista de dispositivos sem nada ainda

        '''Inserimos o nome dos dispositivos de áudio da lista de dispositivos do computador na nossa lista vazia
        utilizando a lógica: para cada elemento da lista de dispositivos, insira o nome elemento na lista vazia'''
        for item in infos_disp_audio:
            self.lista_dispositivos.append(item.deviceName())

        '''Adicionamos os itens da nossa lista nas comboBoxes de cada canal'''
        self.comboBox.addItems(self.lista_dispositivos)
        self.comboBox_2.addItems(self.lista_dispositivos)
        self.comboBox_3.addItems(self.lista_dispositivos)
        self.comboBox_4.addItems(self.lista_dispositivos)
        self.comboBox_19.addItems(self.lista_dispositivos)

        '''Caso o valor da comboBox mude, enviamos esse valor para o método atualizar canal respectivo'''
        self.comboBox.currentIndexChanged["QString"].connect(self.atualizar_canal1)
        self.comboBox_2.currentIndexChanged["QString"].connect(self.atualizar_canal2)
        self.comboBox_3.currentIndexChanged["QString"].connect(self.atualizar_canal3)
        self.comboBox_4.currentIndexChanged["QString"].connect(self.atualizar_canal4)
        self.comboBox_19.currentIndexChanged["QString"].connect(self.atualizar_canal5)

        '''Começamos o programa com todas as comboBoxes de dispositivo no valor 0'''
        self.comboBox.setCurrentIndex(0)
        self.comboBox_2.setCurrentIndex(0)
        self.comboBox_3.setCurrentIndex(0)
        self.comboBox_4.setCurrentIndex(0)
        self.comboBox_19.setCurrentIndex(0)


        '''Criação dos canvas de cada canal'''
        self.canvas1 = MatPlotLibCanvas(self, width=6, height=2.1, dpi=100) #Criamos o nosso objeto canvas1
        self.ui.gridLayout_4.addWidget(self.canvas1, 1, 1, 1, 1) #Adicionamos o canvas1 ao nosso layout
        self.reference_plot1 = None #Serve para testar se estamos plotando os dados em um plot já organizado ou não

        self.canvas2 = MatPlotLibCanvas(self, width=6, height=2.1, dpi=100)
        self.ui.gridLayout_7.addWidget(self.canvas2, 1, 1, 1, 1)
        self.reference_plot2 = None

        self.canvas3 = MatPlotLibCanvas(self, width=6, height=2.1, dpi=100)
        self.ui.gridLayout_16.addWidget(self.canvas3, 1, 1, 1, 1)
        self.reference_plot3 = None

        self.canvas4 = MatPlotLibCanvas(self, width=6, height=2.1, dpi=100)
        self.ui.gridLayout_22.addWidget(self.canvas4, 1, 1, 1, 1)
        self.reference_plot4 = None

        self.canvas5 = MatPlotLibCanvas(self, width=6, height=2.1, dpi=100)
        self.ui.gridLayout_94.addWidget(self.canvas5, 1, 1, 1, 1)
        self.reference_plot5 = None

        '''Criação dos NavTools de para cada canvas'''
        self.navtool1 = NavTool(self.canvas1) #Criamos o objeto Navigation Tool vinculado ao canvas 1
        self.ui.gridLayout.addWidget(self.navtool1,2,0,1,2) #Adicionamos ele ao layout no local apropriadado

        self.navtool2 = NavTool(self.canvas2)
        self.ui.gridLayout_14.addWidget(self.navtool2, 2, 0, 1, 2)

        self.navtool3 = NavTool(self.canvas3)
        self.ui.gridLayout_20.addWidget(self.navtool3, 2, 0, 1, 2)

        self.navtool4 = NavTool(self.canvas4)
        self.ui.gridLayout_26.addWidget(self.navtool4, 2, 0, 1, 2)

        self.navtool5 = NavTool(self.canvas5)
        self.ui.gridLayout_98.addWidget(self.navtool5, 2, 0, 1, 2)

        '''Criamos as filas que cada um dos canais irá utilizar'''
        self.q1 = queue.Queue(maxsize=20)
        self.q2 = queue.Queue(maxsize=20)
        self.q3 = queue.Queue(maxsize=20)
        self.q4 = queue.Queue(maxsize=20)
        self.q5 = queue.Queue(maxsize=20)

        '''Intervalo de atualização da plotagem e do programa:'''
        self.intervalo = 30 #Controle do intervalo do temporizador em milisegundos

        '''Variáveis para plotagem do sinal'''
        self.tam_janela1 = 1000  # Tamanho da janela de dados em milisegundos
        self.pular_amostra1 = 1  # Pula 1 amostra
        self.canais1 = [1]  # Número de Canais
        self.eixoYmin1 = -0.5  # Valor mínimo do eixo Y do gráfico
        self.eixoYmax1 = 0.5  # Valor máximo do eixo Y do gráfico

        self.tam_janela2 = 1000
        self.pular_amostra2 = 1
        self.canais2 = [1]
        self.eixoYmin2 = -0.5
        self.eixoYmax2 = 0.5

        self.tam_janela3 = 1000
        self.pular_amostra3 = 1
        self.canais3 = [1]
        self.eixoYmin3 = -0.5
        self.eixoYmax3 = 0.5

        self.tam_janela4 = 1000
        self.pular_amostra4 = 1
        self.canais4 = [1]
        self.eixoYmin4 = -0.5
        self.eixoYmax4 = 0.5

        self.tam_janela5 = 1000
        self.pular_amostra5 = 1
        self.canais5 = [1]
        self.eixoYmin5 = -0.5
        self.eixoYmax5 = 0.5

        '''Variáveis para salvamento do sinal'''
        self.fulldata1 = [] #Vetor que armazena os dados
        self.datataxaamostra1 = 0 #Variável que armazena a taxa de amostra dos dados
        self.play1 = False #Variável de controle da gravação dos dados no vetor de armazenamento

        self.fulldata2 = []
        self.datataxaamostra2 = 0
        self.play2 = False

        self.fulldata3 = []
        self.datataxaamostra3 = 0
        self.play3 = False

        self.fulldata4 = []
        self.datataxaamostra4 = 0
        self.play4 = False

        self.fulldata5 = []
        self.datataxaamostra5 = 0
        self.play5 = False

        self.achou_dispositivo = 0 #Variável de controle

        '''Organização dos dados para mostrar no campo localização.
        Como não foi possível estabelecer ligação com os dados reais
        de protótipo, foram selecionados valores disponíveis na internet
        para verificar o funcionamento do programa'''

        self.cidades_eua = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/us-cities-top-1k.csv") #Criamos um objeto contendo os dados extraídos do endereço
        self.lat = self.cidades_eua['lat'].tolist() #Utilizamos o método tolist para transformar a coluna latitude da tabela em uma lista de valores
        self.lon = self.cidades_eua['lon'].tolist() #Utilizamos o método tolist para transformar a coluna longitude da tabela em uma lista de valores
        self.local = str(self.lat[2])+","+str(self.lon[2]) #Somamos os 2 valores extraidos transformados em string e atribuimos a variável local
        self.label_19.setText(self.local) #O texto do label é substituido pelo texto da variável local

        '''Organização dos dados de temperatura.
        De maneira similar aos dados de localização, os dados são somente 
        ilustrativos com o objetivo de testar funcionalidades do programa.
        Nesse caso estamos separando 2 valores de temperatura para inserir
        nos respectivos labels além de verificar as possibilidades de manipulação
        de dados da biblioteca pandas. É possível encontrar a tabela
        de dados utilizada no repositório do projeto.'''

        self.temperatura = pd.read_csv("Average Temperature of Cities.csv") #Criamos um objeto contendo os dados extraídos do endereço
        self.tempPAC = self.temperatura.loc[:, 'Jan'] #Utilizamos o método loc para separar uma das colunas da tabela, no caso a das temperaturas referentes a janeiro
        self.tempLOC = self.temperatura.loc[:, 'Jun'] #Utilizamos o método loc para separar uma das colunas da tabela, no caso a das temperaturas referentes a junho
        self.tempPACC = self.tempPAC.str.split(pat='\n', expand=True) #Separamos a coluna utilizando \n como separador(Os valores em Ceusius e Farenheit estão separados pelo indicador \n). Agora temos uma matriz com 2 colunas.
        self.tempLOCC = self.tempLOC.str.split(pat='\n', expand=True) #Separamos a coluna utilizando \n como separador(Os valores em Ceusius e Farenheit estão separados pelo indicador \n). Agora temos uma matriz com 2 colunas.
        self.valorTempPac = self.tempPACC.iloc[0][0] #Atribuimos o valor[0, 0] da matriz a variável de temperatura do paciente
        self.valorTempLoc = self.tempLOCC.iloc[0][0] #Atribuimos o valor[0, 0] da matriz a variável de temperatura do ambiente

        self.lineEdit_9.setText(str(self.valorTempLoc)) #Inserimos o valor da variável de temperatura do paciente convertido para string no lineEdit
        self.lineEdit_10.setText(str(self.valorTempPac)) #Inserimos o valor da variável de temperatura do ambiente convertido para string no lineEdit
        self.lineEdit_10.textChanged["QString"].connect(self.avalia_temp) #Caso o lineEdit de temperatura do paciente tenha seu valor alterado, o método avalia_temp é chamado

        '''Fazemos um teste utilizando nossa lista de dispositivos e checamos se podemos 
        captar se eles são identificados pela biblioteca sounddevice. Caso sejam, marcamos a variável
        achou_dispositivo indicando sucesso'''
        for self.dispositivo1 in range(len(infos_disp_audio)):
            try:
                device_info = sd.query_devices(self.dispositivo1, "input")
                if device_info:
                    self.achou_dispositivo = 1
                    break
            except:
                pass

        '''Caso exista um dispositivo acessável pela biblioteca sounddevice, seguimos com o código.
        Caso não exista, podemos desativar o botão para mostrar os dados e marcar que não existem
        dispositivos acessíveis no comboBox'''
        if self.achou_dispositivo: #Roda caso se ache um dispositivo
            self.taxa_amostra_1 = device_info["default_samplerate"] #Coletamos a taxa de amostragem padrão do dispositivo
            tamanho_1 = int(self.tam_janela1 * self.taxa_amostra_1 /
                         (1000 * self.pular_amostra1))  #Calculamos o tamanho da janela para futura plotagem dos dados
            sd.default.samplerate = self.taxa_amostra_1  #Setamos a taxa de amostragem do dispositivo (Que nesse caso é a taxa de amostragem padrão)
            self.plotdata1 = np.zeros((tamanho_1, len(self.canais1)))
        else:
            self.desabilitar_botoes_1()  #Desligamos os botões
            self.pushButton_2.setEnabled(False)
            self.pushButton_2.setStyleSheet(
                "QPushButton" "{" "background-color : lightblue;" "}"
            )
            self.lista_dispositivos.append("No Devices Found") #Inserimos na lista a informação que não há dispositivos disponíveis
            self.comboBox.addItems(self.lista_dispositivos) #Inserimos a lista na comboBox
        self.achou_dispositivo = 0 #Resetamos a variável
        '''Repetimos a operação para o canal 2'''
        for self.dispositivo2 in range(len(infos_disp_audio)):
            try:
                device_info1 = sd.query_devices(self.dispositivo2, "input")
                if device_info1:
                    self.achou_dispositivo = 1
                    break
            except:
                pass

        if self.achou_dispositivo:
            self.taxa_amostra_2 = device_info1["default_samplerate"]
            length1 = int(self.tam_janela2 * self.taxa_amostra_2 /
                          (1000 * self.pular_amostra2))
            sd.default.samplerate = self.taxa_amostra_2
            self.plotdata2 = np.zeros((length1, len(self.canais2)))
        else:
            self.desabilitar_botoes_2()
            self.pushButton_3.setEnabled(False)
            self.pushButton_3.setStyleSheet(
                "QPushButton" "{" "background-color : lightblue;" "}"
            )
            self.lista_dispositivos.append("No Devices Found")
            self.comboBox_2.addItems(self.lista_dispositivos)
        self.achou_dispositivo = 0

        '''Repetimos a operação para o canal 3'''
        for self.dispositivo3 in range(len(infos_disp_audio)):
            try:
                device_info3 = sd.query_devices(self.dispositivo3, "input")
                if device_info3:
                    self.achou_dispositivo = 1
                    break
            except:
                pass

        if self.achou_dispositivo:
            self.taxa_amostra_3 = device_info["default_samplerate"]
            tamanho_3 = int(self.tam_janela3 * self.taxa_amostra_3 /
                         (1000 * self.pular_amostra3))
            sd.default.samplerate = self.taxa_amostra_3
            self.plotdata3 = np.zeros((tamanho_3, len(self.canais3)))
        else:
            self.desabilitar_botoes_3()
            self.pushButton_7.setEnabled(False)
            self.pushButton_7.setStyleSheet(
                "QPushButton" "{" "background-color : lightblue;" "}"
            )
            self.lista_dispositivos.append("No Devices Found")
            self.comboBox_3.addItems(self.lista_dispositivos)
        self.achou_dispositivo = 0

        '''Repetimos a operação para o canal 2'''
        for self.dispositivo4 in range(len(infos_disp_audio)):
            try:
                device_info4 = sd.query_devices(self.dispositivo4, "input")
                if device_info4:
                    self.achou_dispositivo = 1
                    break
            except:
                pass

        if self.achou_dispositivo:
            self.taxa_amostra_4 = device_info["default_samplerate"]
            tamanho_4 = int(self.tam_janela4 * self.taxa_amostra_4 /
                         (1000 * self.pular_amostra4))
            sd.default.samplerate = self.taxa_amostra_4
            self.plotdata4 = np.zeros((tamanho_4, len(self.canais4)))
        else:
            self.desabilitar_botoes_4()
            self.pushButton_10.setEnabled(False)
            self.pushButton_10.setStyleSheet(
                "QPushButton" "{" "background-color : lightblue;" "}"
            )
            self.lista_dispositivos.append("No Devices Found")
            self.comboBox_4.addItems(self.lista_dispositivos)
        self.achou_dispositivo = 0

        '''Repetimos a operação para o canal 2'''
        for self.dispositivo5 in range(len(infos_disp_audio)):
            try:
                device_info5 = sd.query_devices(self.dispositivo5, "input")
                if device_info5:
                    self.achou_dispositivo = 1
                    break
            except:
                pass

        if self.achou_dispositivo:
            self.taxa_amostra_5 = device_info["default_samplerate"]
            tamanho_5 = int(self.tam_janela5 * self.taxa_amostra_5 /
                         (1000 * self.pular_amostra5))
            sd.default.samplerate = self.taxa_amostra_5
            self.plotdata5 = np.zeros((tamanho_5, len(self.canais5)))
        else:
            self.desabilitar_botoes_5()
            self.pushButton_35.setEnabled(False)
            self.pushButton_35.setStyleSheet(
                "QPushButton" "{" "background-color : lightblue;" "}"
            )
            self.lista_dispositivos.append("No Devices Found")
            self.comboBox_19.addItems(self.lista_dispositivos)
        self.achou_dispositivo = 0

        '''Criamos o temporizador e criamos algumas condições'''
        self.timer = QtCore.QTimer() #Criamos um objeto do tipo timer para controle temporal do programa
        self.timer.setInterval(self.intervalo) #Atribuimos o intervalo do temporizador em milisegundos
        self.timer.timeout.connect(self.if_plot_1) #Conectamos o fim de um ciclo do temporizador ao método verifica se o canvas 1 está liberado para ser atualizado
        self.timer.timeout.connect(self.if_plot_2) #Conectamos o fim de um ciclo do temporizador ao método verifica se o canvas 2 está liberado para ser atualizado
        self.timer.timeout.connect(self.if_plot_3) #Conectamos o fim de um ciclo do temporizador ao método verifica se o canvas 3 está liberado para ser atualizado
        self.timer.timeout.connect(self.if_plot_4) #Conectamos o fim de um ciclo do temporizador ao método verifica se o canvas 4 está liberado para ser atualizado
        self.timer.timeout.connect(self.if_plot_5) #Conectamos o fim de um ciclo do temporizador ao método verifica se o canvas 5 está liberado para ser atualizado
        self.timer.timeout.connect(self.atualizar_threads_ativos) #Método para atualizar o valor dos threads ativos é chamado quando o timer finaliza um ciclo
        self.timer.start() #Começamos a contar o tempo

        '''Variáveis que recebem os dados da fila'''
        self.data1 = [0]
        self.data2 = [0]
        self.data3 = [0]
        self.data4 = [0]
        self.data5 = [0]

        '''Na inicialização, os botões de gravação dos dados estão
        todos desligados, pois não há dados para gravar enquanto
        a plotagem não começar'''
        self.pushButton_21.setEnabled(False)
        self.pushButton_20.setEnabled(False)
        self.pushButton_13.setEnabled(False)
        self.pushButton_12.setEnabled(False)
        self.pushButton_15.setEnabled(False)
        self.pushButton_14.setEnabled(False)
        self.pushButton_17.setEnabled(False)
        self.pushButton_16.setEnabled(False)
        self.pushButton_19.setEnabled(False)
        self.pushButton_18.setEnabled(False)

        '''Conectamos o método de gravação dos dados (set_play)
        e interrupção da gravação dos dados (stop_play) para cada
        um dos canais, com seus respectivos botões'''
        self.pushButton_21.clicked.connect(self.set_play_1)
        self.pushButton_20.clicked.connect(self.stop_play_1)

        self.pushButton_13.clicked.connect(self.set_play_2)
        self.pushButton_12.clicked.connect(self.stop_play_2)

        self.pushButton_15.clicked.connect(self.set_play_3)
        self.pushButton_14.clicked.connect(self.stop_play_3)

        self.pushButton_17.clicked.connect(self.set_play_4)
        self.pushButton_16.clicked.connect(self.stop_play_4)

        self.pushButton_19.clicked.connect(self.set_play_5)
        self.pushButton_18.clicked.connect(self.stop_play_5)

        '''Conectamos cada método de atualização de variável com seu respectivo campo na interface'''
        self.lineEdit.textChanged["QString"].connect(self.atualizar_janela_1) #Caso o lineEdit tenha seu valor alterado, é chamado o método atualizar janela com o texto atual do lineEdit como argumento
        self.lineEdit_2.textChanged.connect(self.atualizar_taxa_amostragem_1) #Caso o lineEdit tenha seu valor alterado, é chamado o método atualizar janela com o texto atual do lineEdit como argumento
        self.spinBox_downsample.valueChanged.connect(self.atualizar_pular_amostra_1) #Caso o spinBox tenha seu valor alterado, é chamado o método atualizar janela com o valor atual do lineEdit como argumento
        self.spinBox_updateInterval.valueChanged.connect(self.atualizar_intervalo_1) #Caso o spinBox tenha seu valor alterado, é chamado o método atualizar janela com o valor atual do lineEdit como argumento

        self.lineEdit_3.textChanged["QString"].connect(self.atualizar_janela_2)
        self.lineEdit_4.textChanged.connect(self.atualizar_taxa_amostragem_2)
        self.spinBox_downsample_2.valueChanged.connect(self.atualizar_pular_amostra_2)
        self.spinBox_updateInterval_2.valueChanged.connect(self.atualizar_intervalo_1)

        self.lineEdit_5.textChanged["QString"].connect(self.atualizar_janela_3)
        self.lineEdit_6.textChanged.connect(self.atualizar_taxa_amostragem_3)
        self.spinBox_downsample_3.valueChanged.connect(self.atualizar_pular_amostra_3)
        self.spinBox_updateInterval_3.valueChanged.connect(self.atualizar_intervalo_1)

        self.lineEdit_7.textChanged["QString"].connect(self.atualizar_janela_4)
        self.lineEdit_8.textChanged.connect(self.atualizar_taxa_amostragem_4)
        self.spinBox_downsample_4.valueChanged.connect(self.atualizar_pular_amostra_4)
        self.spinBox_updateInterval_4.valueChanged.connect(self.atualizar_intervalo_1)

        self.lineEdit_29.textChanged["QString"].connect(self.atualizar_janela_5)
        self.lineEdit_30.textChanged.connect(self.atualizar_taxa_amostragem_5)
        self.spinBox_downsample_15.valueChanged.connect(self.atualizar_pular_amostra_5)
        self.spinBox_updateInterval_15.valueChanged.connect(self.atualizar_intervalo_1)

        '''Métodos recebem os valores das spinBoxes
        e atualizam os valores do mínimo e máximo do eixo Y'''
        self.doubleSpinBox_yrangemin.valueChanged.connect(
            self.atualizar_eixoYmin1)
        self.doubleSpinBox_yrangemin_2.valueChanged.connect(
            self.atualizar_eixoYmin2)
        self.doubleSpinBox_yrangemin_3.valueChanged.connect(
            self.atualizar_eixoYmin3)
        self.doubleSpinBox_yrangemin_4.valueChanged.connect(
            self.atualizar_eixoYmin4)
        self.doubleSpinBox_yrangemin_15.valueChanged.connect(
            self.atualizar_eixoYmin5)

        self.doubleSpinBox_yrangemax.valueChanged.connect(
            self.atualizar_eixoYmax1)
        self.doubleSpinBox_yrangemax_2.valueChanged.connect(
            self.atualizar_eixoYmax2)
        self.doubleSpinBox_yrangemax_3.valueChanged.connect(
            self.atualizar_eixoYmax3)
        self.doubleSpinBox_yrangemax_4.valueChanged.connect(
            self.atualizar_eixoYmax4)
        self.doubleSpinBox_yrangemax_15.valueChanged.connect(
            self.atualizar_eixoYmax5)

        '''Conectamos os métodos stop e start worker com seus respectivos botões(Começar Plotagem e Pausar Plotagem)'''
        self.pushButton.clicked.connect(self.start_worker_1) #Caso o botão seja clicado, iniciamos o método start worker
        self.pushButton_2.clicked.connect(self.stop_worker_1) #Caso o botão seja clicado, iniciamos o método stop worker
        self.worker1 = None #O objeto worker é criado, inicialmente como uma variável vazia
        self.go_on1 = True #A variável go_on tem seu valor definido. Por meio desta variável iremos controlar a plotagem e aquisição de dados

        self.pushButton_4.clicked.connect(self.start_worker_2)
        self.pushButton_3.clicked.connect(self.stop_worker_2)
        self.worker2 = None
        self.go_on2 = True

        self.pushButton_8.clicked.connect(self.start_worker_3)
        self.pushButton_7.clicked.connect(self.stop_worker_3)
        self.worker3 = None
        self.go_on3 = True

        self.pushButton_11.clicked.connect(self.start_worker_4)
        self.pushButton_10.clicked.connect(self.stop_worker_4)
        self.worker4 = None
        self.go_on4 = True

        self.pushButton_36.clicked.connect(self.start_worker_5)
        self.pushButton_35.clicked.connect(self.stop_worker_5)
        self.worker5 = None
        self.go_on5 = True

        self.ListaCanal = ['Canal 1', 'Canal 2', 'Canal 3', 'Canal 4', 'Canal 5'] #Criamos uma lista de canais com o nome de cada canal
        self.comboBox_6.addItems(self.ListaCanal) #Inserimos a lista de canais na comboBox de salvamento dos dados
        self.comboBox_9.addItems(self.ListaCanal) #Inserimos a lista de canais na comboBox de recuperação dos dados

        self.pushButton_5.clicked.connect(self.salvar_arquivo)
        self.pushButton_9.clicked.connect(self.abrir_arquivo)

        self.pushButton_6.clicked.connect(self.plotar_localizacao)

        self.actionGerar.triggered.connect(self.plotar_espectro_1)
        self.actionGerar.setEnabled(False)

        self.actionGerar_2.triggered.connect(self.plotar_espectro_2)
        self.actionGerar_2.setEnabled(False)

    '''O método que coleta o sinal de audio de um dado dispositivo selecionado pelo método atualizar canal.
    Começamos com o comando try, que realiza o código e caso ocorra uma exceção, se informa um código
    de erro no terminal e chamando o método stop worker com o objetivo de parar o recebimento de dados'''
    def receberDados_1(self):
        try:
            QtWidgets.QApplication.processEvents()

            '''O método audio callback é chamado pelo objeto stream1 do tipo input stream.
            A lógica é que podemos alterar a formação dos dados recebidos do áudio de acordo com o nosso método.
            Também aproveitamos essa método que é chamada constantemente para informar os dados que estamso recebendo'''
            def audio_callback_1(indata, frames, time, status): #O método recebe como parâmetro os dados que estão entrando (indata)
                self.q1.put(indata[:: self.pular_amostra1, [0]])
                if self.play1 is True:
                    self.fulldata1 = np.append(self.fulldata1, indata[:: self.pular_amostra1, [0]])
                    self.datataxaamostra1 = self.taxa_amostra_1

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
            self.ativar_botoes_1()

        except Exception as e: #Caso uma exceção seja encontrada
            print("ERROR: ", e) #Mostramos o erro
            self.stop_worker_1 #Paramos o recebimento dos dados
            pass

    def receberDados_2(self):
        try:
            QtWidgets.QApplication.processEvents()

            def audio_callback_2(indata, frames, time, status):
                self.q2.put(indata[:: self.pular_amostra2, [0]])
                if self.play2 is True:
                    self.fulldata2 = np.append(self.fulldata2, indata[:: self.pular_amostra2, [0]])
                    self.datataxaamostra2 = self.taxa_amostra_2

            stream2 = sd.InputStream(
                device=self.dispositivo2,
                channels=max(self.canais2),
                samplerate=self.taxa_amostra_2,
                callback=audio_callback_2,
            )
            with stream2:

                while True:
                    QtWidgets.QApplication.processEvents()
                    if self.go_on2:
                        break
            self.ativar_botoes_2()

        except Exception as e2:
            print("ERROR: ", e2)
            self.stop_worker_2()
            pass

    def receberDados_3(self):
        try:
            QtWidgets.QApplication.processEvents()

            def audio_callback_3(indata, frames, time, status):
                self.q3.put(indata[:: self.pular_amostra3, [0]])
                if self.play3 is True:
                    self.fulldata3 = np.append(self.fulldata3, indata[:: self.pular_amostra3, [0]])
                    self.datataxaamostra3 = self.taxa_amostra_3

            stream3 = sd.InputStream(
                device=self.dispositivo3,
                channels=max(self.canais3),
                samplerate=self.taxa_amostra_3,
                callback=audio_callback_3,
            )
            with stream3:

                while True:
                    QtWidgets.QApplication.processEvents()
                    if self.go_on3:
                        break
            self.ativar_botoes_3()

        except Exception as e3:
            print("ERROR: ", e3)
            self.stop_worker_3()
            pass

    def receberDados_4(self):
        try:
            QtWidgets.QApplication.processEvents()

            def audio_callback_4(indata, frames, time, status):
                self.q4.put(indata[:: self.pular_amostra4, [0]])
                if self.play4 is True:
                    self.fulldata4 = np.append(self.fulldata4, indata[:: self.pular_amostra4, [0]])
                    self.datataxaamostra4 = self.taxa_amostra_4

            stream4 = sd.InputStream(
                device=self.dispositivo4,
                channels=max(self.canais4),
                samplerate=self.taxa_amostra_4,
                callback=audio_callback_4,
            )
            with stream4:

                while True:
                    QtWidgets.QApplication.processEvents()
                    if self.go_on4:
                        break
            self.ativar_botoes_4()

        except Exception as e4:
            print("ERROR: ", e4)
            self.stop_worker_4()
            pass

    def receberDados_5(self):
        try:
            QtWidgets.QApplication.processEvents()

            def audio_callback_5(indata, frames, time, status):
                self.q5.put(indata[:: self.pular_amostra5, [0]])
                if self.play5 is True:
                    self.fulldata5 = np.append(self.fulldata5, indata[:: self.pular_amostra5, [0]])
                    self.datataxaamostra5 = self.taxa_amostra_5

            stream5 = sd.InputStream(
                device=self.dispositivo5,
                channels=max(self.canais5),
                samplerate=self.taxa_amostra_5,
                callback=audio_callback_5,
            )
            with stream5:

                while True:
                    QtWidgets.QApplication.processEvents()
                    if self.go_on5:
                        break
            self.ativar_botoes_5()

        except Exception as e5:
            print("ERROR: ", e5)
            self.stop_worker_5()
            pass

    '''As funções set_play tem como objetivo ativar a variável de controle
    do processo de gravação dos dados para seus respectivos canais'''
    def set_play_1(self):
        self.play1=True #Ativamos a variável de controle do canal 1
        self.pushButton_21.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        ) #Ajustamos o estilo do botão para obter uma indicação visual de que os dados estão sendo gravados
        self.fulldata1 = [] #Resetamos o vetor que armazena os dados
        self.datataxaamostra1 = 0 #Resetamos a variável que armazena a taxa de amostragem do canal

    def set_play_2(self):
        self.play2=True
        self.pushButton_13.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        )
        self.fulldata2 = []
        self.datataxaamostra2 = 0

    def set_play_3(self):
        self.play3=True
        self.pushButton_15.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        )
        self.fulldata3 = []
        self.datataxaamostra3 = 0

    def set_play_4(self):
        self.play4=True
        self.pushButton_17.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        )
        self.fulldata4 = []
        self.datataxaamostra4 = 0

    def set_play_5(self):
        self.play5=True
        self.pushButton_19.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        )
        self.fulldata5 = []
        self.datataxaamostra5 = 0

    '''As funções stop_play tem como objetivo desativar a variável de controle
        do processo de gravação dos dados para seus respectivos canais'''
    def stop_play_1(self):
        self.play1=False #Desativamos a variável de controle do canal 1
        self.pushButton_21.setStyleSheet(
            "QPushButton" "{" "background-color : normal;" "}"
        )#Resetamos o estilo do botão para indicar que não estamos gravando mais os dados

    def stop_play_2(self):
        self.play2=False
        self.pushButton_13.setStyleSheet(
            "QPushButton" "{" "background-color : normal;" "}"
        )

    def stop_play_3(self):
        self.play3=False
        self.pushButton_15.setStyleSheet(
            "QPushButton" "{" "background-color : normal;" "}"
        )

    def stop_play_4(self):
        self.play4=False
        self.pushButton_17.setStyleSheet(
            "QPushButton" "{" "background-color : normal;" "}"
        )

    def stop_play_5(self):
        self.play5=False
        self.pushButton_19.setStyleSheet(
            "QPushButton" "{" "background-color : normal;" "}"
        )

    '''Método desabilitar botões simplesmente
    desativa os botões da interface enquanto estamos
    plotando para evitar que o usuário possa
    alterar valores importantes no meio do processo.
    Cada canal possui um método desabilitar botões'''
    def desabilitar_botoes_1(self):
        self.lineEdit.setEnabled(False)
        self.lineEdit_2.setEnabled(False)
        self.spinBox_downsample.setEnabled(False)
        self.spinBox_updateInterval.setEnabled(False)
        self.comboBox.setEnabled(False)
        self.pushButton.setEnabled(False)
        self.pushButton.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        )

        self.canvas1.axes.clear()

    def desabilitar_botoes_2(self):
        self.lineEdit_3.setEnabled(False)
        self.lineEdit_4.setEnabled(False)
        self.spinBox_downsample_2.setEnabled(False)
        self.spinBox_updateInterval_2.setEnabled(False)
        self.comboBox_2.setEnabled(False)
        self.pushButton_4.setEnabled(False)
        self.pushButton_4.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        )

        self.canvas2.axes.clear()

    def desabilitar_botoes_3(self):
        self.lineEdit_5.setEnabled(False)
        self.lineEdit_6.setEnabled(False)
        self.spinBox_downsample_3.setEnabled(False)
        self.spinBox_updateInterval_3.setEnabled(False)
        self.comboBox_3.setEnabled(False)
        self.pushButton_8.setEnabled(False)
        self.pushButton_8.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        )

        self.canvas3.axes.clear()

    def desabilitar_botoes_4(self):
        self.lineEdit_7.setEnabled(False)
        self.lineEdit_8.setEnabled(False)
        self.spinBox_downsample_4.setEnabled(False)
        self.spinBox_updateInterval_4.setEnabled(False)
        self.comboBox_4.setEnabled(False)
        self.pushButton_11.setEnabled(False)
        self.pushButton_11.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        )

        self.canvas4.axes.clear()

    def desabilitar_botoes_5(self):
        self.lineEdit_29.setEnabled(False)
        self.lineEdit_30.setEnabled(False)
        self.spinBox_downsample_15.setEnabled(False)
        self.spinBox_updateInterval_15.setEnabled(False)
        self.comboBox_19.setEnabled(False)
        self.pushButton_36.setEnabled(False)
        self.pushButton_36.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        )

        self.canvas5.axes.clear()

    '''Métodos ativar botões reabilita os botões
    desabilitados. Cada canal possui um método
    ativar botões.'''
    def ativar_botoes_1(self):
        self.pushButton.setEnabled(True)
        self.lineEdit.setEnabled(True)
        self.lineEdit_2.setEnabled(True)
        self.spinBox_downsample.setEnabled(True)
        self.spinBox_updateInterval.setEnabled(True)
        self.comboBox.setEnabled(True)

    def ativar_botoes_2(self):
        self.pushButton_4.setEnabled(True)
        self.lineEdit_3.setEnabled(True)
        self.lineEdit_4.setEnabled(True)
        self.spinBox_downsample_2.setEnabled(True)
        self.spinBox_updateInterval_2.setEnabled(True)
        self.comboBox_2.setEnabled(True)

    def ativar_botoes_3(self):
        self.pushButton_8.setEnabled(True)
        self.lineEdit_5.setEnabled(True)
        self.lineEdit_6.setEnabled(True)
        self.spinBox_downsample_3.setEnabled(True)
        self.spinBox_updateInterval_3.setEnabled(True)
        self.comboBox_3.setEnabled(True)

    def ativar_botoes_4(self):
        self.pushButton_11.setEnabled(True)
        self.lineEdit_7.setEnabled(True)
        self.lineEdit_8.setEnabled(True)
        self.spinBox_downsample_4.setEnabled(True)
        self.spinBox_updateInterval_4.setEnabled(True)
        self.comboBox_4.setEnabled(True)

    def ativar_botoes_5(self):
        self.pushButton_36.setEnabled(True)
        self.lineEdit_29.setEnabled(True)
        self.lineEdit_30.setEnabled(True)
        self.spinBox_downsample_15.setEnabled(True)
        self.spinBox_updateInterval_15.setEnabled(True)
        self.comboBox_19.setEnabled(True)

    '''Começa o worker com o método start stream como parâmetro'''
    def start_worker_1(self):

        self.desabilitar_botoes_1() #Chama o método desabilitar botões

        self.canvas1.axes.clear() #Chama o método para limpar o canvas

        self.go_on1 = False #Variável falsa para que possamos mostrar o audio - Ver o método pegar Audio

        '''O worker é iniciado com o método start stream para que possamos rodá-la em paralelo
        com a interface principal'''
        self.worker1 = Worker(
            self.start_stream_1,
        )

        self.threadpool.start(self.worker1) #O administrador inicia o worker
        self.reference_plot1 = None #Quando começamos a plotar, sempre desativamos a variável de controle da organização da plotagem, para recomeçar a plotagem com as novas configurações
        self.timer.setInterval(self.intervalo) #Atualizamos o intervalo, caso tenha sido alterado
        self.pushButton_20.setEnabled(True) #Ativamos o botão de gravação de dados
        self.pushButton_21.setEnabled(True) #Ativamos o botão de interrupção da gravação de dados

    def start_worker_2(self):

        self.desabilitar_botoes_2()

        self.canvas2.axes.clear()

        self.go_on2 = False
        self.worker2 = Worker(
            self.start_stream_2,
        )
        self.threadpool.start(self.worker2)
        self.reference_plot2 = None
        self.timer.setInterval(self.intervalo)

        self.pushButton_12.setEnabled(True)
        self.pushButton_13.setEnabled(True)

    def start_worker_3(self):

        self.desabilitar_botoes_3()

        self.canvas3.axes.clear()

        self.go_on3 = False
        self.worker3 = Worker(
            self.start_stream_3,
        )
        self.threadpool.start(self.worker3)
        self.reference_plot3 = None
        self.timer.setInterval(self.intervalo)

        self.pushButton_14.setEnabled(True)
        self.pushButton_15.setEnabled(True)

    def start_worker_4(self):

        self.desabilitar_botoes_4()

        self.canvas4.axes.clear()

        self.go_on4 = False
        self.worker4 = Worker(
            self.start_stream_4,
        )
        self.threadpool.start(self.worker4)
        self.reference_plot4 = None
        self.timer.setInterval(self.intervalo)

        self.pushButton_16.setEnabled(True)
        self.pushButton_17.setEnabled(True)

    def start_worker_5(self):

        self.desabilitar_botoes_5()

        self.canvas5.axes.clear()

        self.go_on5 = False
        self.worker5 = Worker(
            self.start_stream_5,
        )
        self.threadpool.start(self.worker5)
        self.reference_plot5 = None
        self.timer.setInterval(self.intervalo)

        self.pushButton_18.setEnabled(True)
        self.pushButton_19.setEnabled(True)

    '''Método que pausa o recebimento e a plotagem dos dados'''
    def stop_worker_1(self):
        self.go_on1 = True #Ativação da variável go_on pausa o loop dentro dos métodos receberDados e atualizar_canvas
        with self.q1.mutex: #O método mutex "trava" a fila, não permitindo que os outros métodos do programa a acessem
            self.q1.queue.clear() #No caso, com a fila travada, podemos limpá-la
        self.ativar_botoes_1() #Ativamos os botões
        self.pushButton_20.setEnabled(False) #Desligamos o botão de gravação dos dados
        self.pushButton_21.setEnabled(False) #Desligamos o botão de interrupção da gravação dos dados

    def stop_worker_2(self):
        self.go_on2 = True
        with self.q2.mutex:
            self.q2.queue.clear()
        self.ativar_botoes_2()
        self.pushButton_12.setEnabled(False)
        self.pushButton_13.setEnabled(False)

    def stop_worker_3(self):

        self.go_on3 = True
        with self.q3.mutex:
            self.q3.queue.clear()
        self.ativar_botoes_3()
        self.pushButton_14.setEnabled(False)
        self.pushButton_15.setEnabled(False)

    def stop_worker_4(self):

        self.go_on4 = True
        with self.q4.mutex:
            self.q4.queue.clear()
        self.ativar_botoes_4()
        self.pushButton_16.setEnabled(False)
        self.pushButton_17.setEnabled(False)

    def stop_worker_5(self):

        self.go_on5 = True
        with self.q5.mutex:
            self.q5.queue.clear()
        self.ativar_botoes_5()
        self.pushButton_18.setEnabled(False)
        self.pushButton_19.setEnabled(False)

    def start_stream_1(self): #Método que puxa o método pegar audio - Essa é o método passado para o objeto worker
        self.receberDados_1()

    def start_stream_2(self):
        self.receberDados_2()

    def start_stream_3(self):
        self.receberDados_3()

    def start_stream_4(self):
        self.receberDados_4()

    def start_stream_5(self):
        self.receberDados_5()

    def atualizar_canal1(self, value): #Atualiza o dispositivo atual do canal
        self.dispositivo1 = self.lista_dispositivos.index(value)

    def atualizar_canal2(self, value):
        self.dispositivo2 = self.lista_dispositivos.index(value)

    def atualizar_canal3(self, value):
        self.dispositivo3 = self.lista_dispositivos.index(value)

    def atualizar_canal4(self, value):
        self.dispositivo4 = self.lista_dispositivos.index(value)

    def atualizar_canal5(self, value):
        self.dispositivo5 = self.lista_dispositivos.index(value)

    '''Atualiza o tamanho da janela de dados.
    O valor recebido em segundos é convertido no tamanho do eixo X do canvas.
    Plotdata recebe um objeto com as dimensões do tamanho da janela
    e número de canais do dispositivo'''
    def atualizar_janela_1(self, value):
        self.tam_janela1 = int(value)
        tamanho_1 = int(self.tam_janela1 * self.taxa_amostra_1 /
                     (1000 * self.pular_amostra1))
        self.plotdata1 = np.zeros((tamanho_1, len(self.canais1)))

    def atualizar_janela_2(self, value):
        self.tam_janela2 = int(value)
        tamanho_2 = int(self.tam_janela2 * self.taxa_amostra_2 /
                     (1000 * self.pular_amostra2))
        self.plotdata2 = np.zeros((tamanho_2, len(self.canais2)))

    def atualizar_janela_3(self, value):
        self.tam_janela3 = int(value)
        tamanho_3 = int(self.tam_janela3 * self.taxa_amostra_3 /
                     (1000 * self.pular_amostra3))
        self.plotdata3 = np.zeros((tamanho_3, len(self.canais3)))

    def atualizar_janela_4(self, value):
        self.tam_janela4 = int(value)
        tamanho_4 = int(self.tam_janela4 * self.taxa_amostra_4 /
                     (1000 * self.pular_amostra4))
        self.plotdata4 = np.zeros((tamanho_4, len(self.canais4)))

    def atualizar_janela_5(self, value):
        self.tam_janela5 = int(value)
        tamanho_5 = int(self.tam_janela5 * self.taxa_amostra_5 /
                     (1000 * self.pular_amostra5))
        self.plotdata5 = np.zeros((tamanho_5, len(self.canais5)))

    '''Atualiza a taxa de amostragem no programa, assim como
    a taxa de amostragem do dispositivo de áudio. Os valores do tamanho
    e do plotdata também são atualizados, pois eles dependem da taxa de amostragem'''
    def atualizar_taxa_amostragem_1(self, value):
        try:
            self.taxa_amostra_1 = int(value)
            sd.default.samplerate = self.taxa_amostra_1
            tamanho_1 = int(
                self.tam_janela1 * self.taxa_amostra_1 / (1000 * self.pular_amostra1)
            )
            self.plotdata1 = np.zeros((tamanho_1, len(self.canais1)))
        except:
            pass

    def atualizar_taxa_amostragem_2(self, value):
        try:
            self.taxa_amostra_2 = int(value)
            sd.default.samplerate = self.taxa_amostra_2
            tamanho_2 = int(
                self.tam_janela2 * self.taxa_amostra_2 / (1000 * self.pular_amostra2)
            )
            self.plotdata2 = np.zeros((tamanho_2, len(self.canais2)))
        except:
            pass

    def atualizar_taxa_amostragem_3(self, value):
        try:
            self.taxa_amostra_3 = int(value)
            sd.default.samplerate = self.taxa_amostra_3
            tamanho_3 = int(
                self.tam_janela3 * self.taxa_amostra_3 / (1000 * self.pular_amostra3)
            )
            self.plotdata3 = np.zeros((tamanho_3, len(self.canais3)))
        except:
            pass

    def atualizar_taxa_amostragem_4(self, value):
        try:
            self.taxa_amostra_4 = int(value)
            sd.default.samplerate = self.taxa_amostra_4
            tamanho_4 = int(
                self.tam_janela4 * self.taxa_amostra_4 / (1000 * self.pular_amostra4)
            )
            self.plotdata4 = np.zeros((tamanho_4, len(self.canais4)))
        except:
            pass

    def atualizar_taxa_amostragem_5(self, value):
        try:
            self.taxa_amostra_5 = int(value)
            sd.default.samplerate = self.taxa_amostra_5
            tamanho_5 = int(
                self.tam_janela5 * self.taxa_amostra_5 / (1000 * self.pular_amostra5)
            )
            self.plotdata5 = np.zeros((tamanho_5, len(self.canais5)))
        except:
            pass

    '''Atualiza o número de amostras puladas, para o valor 1,
    não pulamos nenhuma amostra, para o valor 2, pegamos uma em cada 2 amostras,
    para o valor 3, uma em cada 3 amostras e assim em diante.
    Os valores do tamanho e do plotdata também são atualizados, 
    pois eles dependem do número de amostras puladas'''
    def atualizar_pular_amostra_1(self, value):
        self.pular_amostra1 = int(value)
        tamanho_1 = int(self.tam_janela1 * self.taxa_amostra_1 /
                      (1000 * self.pular_amostra1))
        self.plotdata1 = np.zeros((tamanho_1, len(self.canais1)))

    def atualizar_pular_amostra_2(self, value):
        self.pular_amostra2 = int(value)
        tamanho_2 = int(self.tam_janela2 * self.taxa_amostra_2 /
                      (1000 * self.pular_amostra2))
        self.plotdata2 = np.zeros((tamanho_2, len(self.canais2)))

    def atualizar_pular_amostra_3(self, value):
        self.pular_amostra3 = int(value)
        tamanho_3 = int(self.tam_janela3 * self.taxa_amostra_3 /
                      (1000 * self.pular_amostra3))
        self.plotdata3 = np.zeros((tamanho_3, len(self.canais3)))

    def atualizar_pular_amostra_4(self, value):
        self.pular_amostra4 = int(value)
        tamanho_4 = int(self.tam_janela4 * self.taxa_amostra_4 /
                      (1000 * self.pular_amostra4))
        self.plotdata4 = np.zeros((tamanho_4, len(self.canais4)))

    def atualizar_pular_amostra_5(self, value):
        self.pular_amostra5 = int(value)
        tamanho_5 = int(self.tam_janela5 * self.taxa_amostra_5 /
                      (1000 * self.pular_amostra5))
        self.plotdata5 = np.zeros((tamanho_5, len(self.canais5)))

    def atualizar_intervalo_1(self, value): #Método para atualizar o intervalo de atualização do programa
        self.intervalo = int(value)

    def atualizar_eixoYmin1(self, minval): #Método recebe o valor mínimo do eixo da spinBox e atualiza a variável
        self.eixoYmin1 = float(minval)

    def atualizar_eixoYmin2(self, minval):
        self.eixoYmin2 = float(minval)

    def atualizar_eixoYmin3(self, minval):
        self.eixoYmin3 = float(minval)

    def atualizar_eixoYmin4(self, minval):
        self.eixoYmin4 = float(minval)

    def atualizar_eixoYmin5(self, minval):
        self.eixoYmin5 = float(minval)

    def atualizar_eixoYmax1(self, maxval): #Método recebe o valor máximo do eixo da spinBox e atualiza a variável
        self.eixoYmax1 = float(maxval)

    def atualizar_eixoYmax2(self, maxval):
        self.eixoYmax2 = float(maxval)

    def atualizar_eixoYmax3(self, maxval):
        self.eixoYmax3 = float(maxval)

    def atualizar_eixoYmax4(self, maxval):
        self.eixoYmax4 = float(maxval)

    def atualizar_eixoYmax5(self, maxval):
        self.eixoYmax5 = float(maxval)

    def atualizar_threads_ativos(self): #Método insere o valor que é monitorado pela classe threadpool no label
        self.label_17.setText(f"{self.threadpool.activeThreadCount()}")

    def if_plot_1(self): #Método que checa se a variável go_on está ativada antes de começar a plotar, serve para poupar processamento caso poucos canais estejam ativados
        if self.go_on1 is False:
            self.atualizar_canvas_1()

    def if_plot_2(self):
        if self.go_on2 is False:
            self.atualizar_canvas_2()

    def if_plot_3(self):
        if self.go_on3 is False:
            self.atualizar_canvas_3()

    def if_plot_4(self):
        if self.go_on4 is False:
            self.atualizar_canvas_4()

    def if_plot_5(self):
        if self.go_on5 is False:
            self.atualizar_canvas_5()

    '''As funções atualizar canvas fazem justamente isso, atualizar o gráfico do
    seu respectivo canal de acordo com as configurações estabelecidas, caso elas
    sejam permitidas pelas variáveis de controle'''
    def atualizar_canvas_1(self): #
        try: #Tentamos executar o código e caso ocorra algum erro, ele é informado ao usuário
            while self.go_on1 is False: #Enquanto a variável de controle go_on for falsa o código continua em loop
                QtWidgets.QApplication.processEvents() #A interface verifica se eventos aconteceram em seu interior(Por exemplo, um botão foi clicado)
                try:
                    self.data1 = self.q1.get_nowait() #Pegamos o primeiro valor da fila, se ele existir

                except queue.Empty: #Caso a fila esteja vazia, continuamos o código
                    break

                '''Nas 3 linhas abaixo, recebemos o tamanho do pacote de dados e utilizamos esse valor
                para rodar os dados ao longo do vetor plotdata, que tem o tamanho conforme a janela definida.
                Por exemplo:
                Com o vetor plotadata = [0 0 0 0 0 0 0 0 0]
                Os pacotes de dados = [1 2 3]
                Fazemos o vetor plotada ser alterado da seguinte maneira:
                [0 0 0 0 0 0 0 0 0]
                [0 0 0 0 0 0 1 2 3]
                [0 0 0 1 2 3 1 2 3]
                [1 2 3 1 2 3 1 2 3]'''
                shift1 = len(self.data1)
                self.plotdata1 = np.roll(self.plotdata1, -shift1, axis=0)
                self.plotdata1[-shift1:, :] = self.data1

                self.dataY1 = self.plotdata1[:] #A variável dataY recebe todos os valores do vetor plotdata

                '''Caso seja nossa primeira plotagem, organizamos os dados no eixo do canvas
                e atribuimos uma cor, nesse caso verde. Caso já esteja organizada a plotagem, só atribuímos
                os valores de dataY ao eixo Y da do gráfico'''
                if self.reference_plot1 is None:
                    plot_refs1 = self.canvas1.axes.plot(
                        self.dataY1, color="green")
                    self.reference_plot1 = plot_refs1[0]
                else:
                    self.reference_plot1.set_ydata(self.dataY1)

            self.canvas1.axes.set_ylabel('Amplitude(V)',labelpad=0) #Cria uma legenda para o eixo Y com o texto indicado entre aspas e com a distância(labelpad) 0 do eixo
            self.canvas1.axes.set_xlabel(str(self.taxa_amostra_1/self.pular_amostra1)+" amostras por segundo", labelpad=-27) #Cria uma legenda para o eixo X de acordo com o número de amostras e distância bem próxima do eixo(labelpad=-27)

            '''Estabelecemos os limites do eixo Y'''
            self.canvas1.axes.set_ylim(
                ymin=self.eixoYmin1, ymax=self.eixoYmax1)

            self.canvas1.axes.grid(True, linestyle="--") #Cria uma grade tracejada no canvas
            self.canvas1.draw() #Redesenha no canvas 'as atualizações feitas

        except Exception as e6: #Caso seja encontrado um erro, ele é mostrado
            print("Error:", e6)
            pass

    def atualizar_canvas_2(self):
        try:
            while self.go_on2 is False:
                QtWidgets.QApplication.processEvents()
                try:
                    self.data2 = self.q2.get_nowait()

                except queue.Empty:
                    break

                shift2 = len(self.data2)
                self.plotdata2 = np.roll(self.plotdata2, -shift2, axis=0)
                self.plotdata2[-shift2:, :] = self.data2

                self.dataY2 = self.plotdata2[:]

                if self.reference_plot2 is None:
                    plot_refs2 = self.canvas2.axes.plot(
                        self.dataY2, color="green")
                    self.reference_plot2 = plot_refs2[0]
                else:
                    self.reference_plot2.set_ydata(self.dataY2)

            self.canvas2.axes.set_ylabel('Amplitude(V)', labelpad=0)
            self.canvas2.axes.set_xlabel(str(self.taxa_amostra_2/self.pular_amostra2)+" amostras por segundo", labelpad=-27)
            self.canvas2.axes.set_ylim(
                ymin=self.eixoYmin2, ymax=self.eixoYmax2)

            self.canvas2.axes.grid(True, linestyle="--")
            self.canvas2.draw()

        except Exception as e7:
            print("Error:", e7)
            pass

    def atualizar_canvas_3(self):
        try:
            while self.go_on3 is False:
                QtWidgets.QApplication.processEvents()
                try:
                    self.data3 = self.q3.get_nowait()

                except queue.Empty:
                    break

                shift3 = len(self.data3)
                self.plotdata3 = np.roll(self.plotdata3, -shift3, axis=0)
                self.plotdata3[-shift3:, :] = self.data3

                self.dataY3 = self.plotdata3[:]

                if self.reference_plot3 is None:
                    plot_refs3 = self.canvas3.axes.plot(
                        self.dataY3, color="green")
                    self.reference_plot3 = plot_refs3[0]
                else:
                    self.reference_plot3.set_ydata(self.dataY3)

            self.canvas3.axes.set_ylabel('Amplitude(V)', labelpad=0)
            self.canvas3.axes.set_xlabel(str(self.taxa_amostra_3/self.pular_amostra3)+" amostras por segundo", labelpad=-27)
            self.canvas3.axes.set_ylim(
                ymin=self.eixoYmin3, ymax=self.eixoYmax3)

            self.canvas3.axes.grid(True, linestyle="--")
            self.canvas3.draw()

        except Exception as e8:
            print("Error:", e8)
            pass

    def atualizar_canvas_4(self):
        try:
            while self.go_on4 is False:
                QtWidgets.QApplication.processEvents()
                try:
                    self.data4 = self.q4.get_nowait()

                except queue.Empty:
                    break

                shift4 = len(self.data4)
                self.plotdata4 = np.roll(self.plotdata4, -shift4, axis=0)
                self.plotdata4[-shift4:, :] = self.data4

                self.dataY4 = self.plotdata4[:]

                if self.reference_plot4 is None:
                    plot_refs4 = self.canvas4.axes.plot(
                        self.dataY4, color="green")
                    self.reference_plot4 = plot_refs4[0]
                else:
                    self.reference_plot4.set_ydata(self.dataY4)

            self.canvas4.axes.set_ylabel('Amplitude(V)', labelpad=0)
            self.canvas4.axes.set_xlabel(str(self.taxa_amostra_4/self.pular_amostra4)+" amostras por segundo", labelpad=-27)
            self.canvas4.axes.set_ylim(
                ymin=self.eixoYmin4, ymax=self.eixoYmax4)

            self.canvas4.axes.grid(True, linestyle="--")
            self.canvas4.draw()

        except Exception as e9:
            print("Error:", e9)
            pass

    def atualizar_canvas_5(self):
        try:
            while self.go_on5 is False:
                QtWidgets.QApplication.processEvents()
                try:
                    self.data5 = self.q5.get_nowait()

                except queue.Empty:
                    break

                shift5 = len(self.data5)
                self.plotdata5 = np.roll(self.plotdata5, -shift5, axis=0)
                self.plotdata5[-shift5:, :] = self.data5

                self.dataY5 = self.plotdata5[:]

                if self.reference_plot5 is None:
                    plot_refs5 = self.canvas5.axes.plot(
                        self.dataY5, color="green")
                    self.reference_plot5 = plot_refs5[0]
                else:
                    self.reference_plot5.set_ydata(self.dataY5)

            self.canvas5.axes.set_ylabel('Amplitude(V)', labelpad=0)
            self.canvas5.axes.set_xlabel(str(self.taxa_amostra_5/self.pular_amostra5)+" amostras por segundo", labelpad=-27)
            self.canvas5.axes.set_ylim(
                ymin=self.eixoYmin5, ymax=self.eixoYmax5)

            self.canvas5.axes.grid(True, linestyle="--")
            self.canvas5.draw()

        except Exception as e10:
            print("Error:", e10)
            pass

    '''Método para salvar o arquivo.
    Salva os valores de amplitude e taxa de amostragem
    do canal escolhido no comboBox'''
    def salvar_arquivo(self):
        self.salvarcaminho = QtWidgets.QFileDialog.getSaveFileName(self, 'Salvar Dados', filter='*.csv') #Abre uma janela de diálogo para que o usuário selecione o nome do arquivo a ser salvo e o caminho
        if self.salvarcaminho[0] != '': #Caso o caminho seja diferente de uma string vazia

            if self.comboBox_6.currentIndex()==0: #Se o index escolhido for 0 salvamos os dados do canal 1
                self.arquivo1 = {'tensão': self.fulldata1, 'taxa de amostragem':self.datataxaamostra1/self.pular_amostra1} #criamos um dicionário com uma coluna de amplitude e outra de taxa de amostragem
                df = pd.DataFrame(self.arquivo1) #Criamos um objeto dataframe do pandas com a nossa tabela de dados
                df.to_csv(self.salvarcaminho[0], index=False) #Utilizamos o método to_csv para converter o objeto dataframe em um arquivo .csv

            if self.comboBox_6.currentIndex()==1:
                self.arquivo2 = {'tensão': self.fulldata2, 'taxa de amostragem': self.datataxaamostra2/self.pular_amostra2}
                df = pd.DataFrame(self.arquivo2)
                df.to_csv(self.salvarcaminho[0], index=False)

            if self.comboBox_6.currentIndex()==2:
                self.arquivo3 = {'tensão': self.fulldata3, 'taxa de amostragem': self.datataxaamostra3/self.pular_amostra3}
                df = pd.DataFrame(self.arquivo3)
                df.to_csv(self.salvarcaminho[0], index=False)

            if self.comboBox_6.currentIndex()==3:
                self.arquivo4 = {'tensão': self.fulldata4, 'taxa de amostragem': self.datataxaamostra4/self.pular_amostra4}
                df = pd.DataFrame(self.arquivo4)
                df.to_csv(self.salvarcaminho[0], index=False)

            if self.comboBox_6.currentIndex()==4:
                self.arquivo5 = {'tensão': self.fulldata5, 'taxa de amostragem': self.datataxaamostra5/self.pular_amostra5}
                df = pd.DataFrame(self.arquivo5)
                df.to_csv(self.salvarcaminho[0], index=False)

    '''O método abrir arquivo permite ao usuário selecionar o endereço
    do arquivo .csv e escolher o canal em que quer plotar os dados.'''
    def abrir_arquivo(self):
        self.abrircaminho = QtWidgets.QFileDialog.getOpenFileName(self, 'Abrir .csv', filter='*.csv') #Abre uma janela de diálogo para que o usuário selecione o nome do arquivo a ser recuperado e o seu caminho
        if self.abrircaminho[0] != '': #Caso o caminho seja diferente de uma string vazia
            self.abrirdata = pd.read_csv(self.abrircaminho[0]) #Criamos um objeto contendo os dados do arquivo .csv utilizando o método read_csv da biblioteca pandas

            if self.comboBox_9.currentIndex()==0: #Se o index escolhido for 0 abrimos os dados no canvas do canal 1
                self.actionGerar.setEnabled(True) #Ativamos o botão para gerar o espectrograma do canal 1, na barra de ferramentas
                self.stop_worker_1() #Chamamos o método stop worker do canal 1, para impedir que mais dados sejam plotados no canvas 1
                self.canvas1.axes.clear() #Limpamos o canvas para prepará-lo para plotagem
                self.reference_plot1 = None #Desativamos a variável de controle da organização da plotagem, para recomeçar a plotagem com as novas configurações
                self.canvas1.axes.set_facecolor("#D5F9FF") #Pintamos o canvas de azul para termos uma indicação de que os dados são provenientes de um arquivo .csv recuperado

                self.abrirdatataxaamostra1 = self.abrirdata.iat[1, 1] #Recuperamos o valor da taxa de amostragem pelo método iat, que recupera uma célula em um objeto dataframe
                self.abrirdatavalores1 = self.abrirdata.loc[:, 'tensão'] #Recuperamos o valor das amplitudes utilizando o método loc, que separa uma das colunas do objeto dataframe

                '''Caso seja nossa primeira plotagem, organizamos os dados no eixo do canvas
                e atribuimos uma cor, nesse caso azul.'''
                plot_refs1 = self.canvas1.axes.plot(
                    self.abrirdatavalores1, color="blue")
                self.reference_plot1 = plot_refs1[0]

                self.canvas1.axes.yaxis.grid(True, linestyle="--") #Cria uma grade tracejada no canvas
                self.canvas1.axes.set_xlabel(str(self.abrirdatataxaamostra1) + " amostras por segundo", labelpad=-27) #Cria uma legenda para o eixo X de acordo com o número de amostras e distância bem próxima do eixo(labelpad=-27)
                self.canvas1.axes.set_ylabel("Tensão(V)", labelpad=0) #Cria uma legenda para o eixo Y com o texto indicado entre aspas e com a distância(labelpad) 0 do eixo

                '''Estabelecemos os limites do eixo Y'''
                self.canvas1.axes.set_ylim(
                    ymin=self.eixoYmin1, ymax=self.eixoYmax1)

                self.canvas1.draw() #Desenha no canvas 'as atualizações feitas

            if self.comboBox_9.currentIndex()==1:
                self.stop_worker_2()
                self.canvas2.axes.clear()
                self.reference_plot2 = None
                self.canvas2.axes.set_facecolor("#D5F9FF")

                self.abrirdatataxaamostra2 = self.abrirdata.iat[1, 1]
                self.abrirdatavalores2 = self.abrirdata.loc[:, 'tensão']

                plot_refs2 = self.canvas2.axes.plot(
                    self.abrirdatavalores2, color="blue")
                self.reference_plot2 = plot_refs2[0]


                self.canvas2.axes.yaxis.grid(True, linestyle="--")
                self.canvas2.axes.set_xlabel(str(self.abrirdatataxaamostra2)+" amostras por segundo", labelpad=-27)
                self.canvas2.axes.set_ylabel("Tensão(V)", labelpad=0)
                self.canvas2.axes.set_ylim(
                    ymin=self.eixoYmin2, ymax=self.eixoYmax2)

                self.canvas2.draw()

            if self.comboBox_9.currentIndex()==2:
                self.actionGerar_2.setEnabled(True)
                self.stop_worker_3()
                self.canvas3.axes.clear()
                self.reference_plot3 = None
                self.canvas3.axes.set_facecolor("#D5F9FF")

                self.abrirdatataxaamostra3 = self.abrirdata.iat[1, 1]
                self.abrirdatavalores3 = self.abrirdata.loc[:, 'tensão']

                plot_refs3 = self.canvas3.axes.plot(
                    self.abrirdatavalores3, color="blue")
                self.reference_plot3 = plot_refs3[0]


                self.canvas3.axes.yaxis.grid(True, linestyle="--")
                self.canvas3.axes.set_xlabel(str(self.abrirdatataxaamostra3) + " amostras por segundo", labelpad=-27)
                self.canvas3.axes.set_ylabel("Tensão(V)", labelpad=0)
                self.canvas3.axes.set_ylim(
                    ymin=self.eixoYmin3, ymax=self.eixoYmax3)

                self.canvas3.draw()

            if self.comboBox_9.currentIndex()==3:
                self.stop_worker_4()
                self.canvas4.axes.clear()
                self.reference_plot4 = None
                self.canvas4.axes.set_facecolor("#D5F9FF")

                self.abrirdatataxaamostra4 = self.abrirdata.iat[1, 1]
                self.abrirdatavalores4 = self.abrirdata.loc[:, 'tensão']

                plot_refs4 = self.canvas4.axes.plot(
                    self.abrirdatavalores4, color="blue")
                self.reference_plot4 = plot_refs4[0]

                self.canvas4.axes.yaxis.grid(True, linestyle="--")
                self.canvas4.axes.set_xlabel(str(self.abrirdatataxaamostra4) + " amostras por segundo", labelpad=-27)
                self.canvas4.axes.set_ylabel("Tensão(V)", labelpad=0)
                self.canvas4.axes.set_ylim(
                    ymin=self.eixoYmin4, ymax=self.eixoYmax4)

                self.canvas4.draw()

            if self.comboBox_9.currentIndex()==4:
                self.stop_worker_5()
                self.canvas5.axes.clear()
                self.reference_plot5 = None
                self.canvas5.axes.set_facecolor("#D5F9FF")

                self.abrirdatataxaamostra5 = self.abrirdata.iat[1, 1]
                self.abrirdatavalores5 = self.abrirdata.loc[:, 'tensão']

                if self.reference_plot5 is None:
                    plot_refs5 = self.canvas5.axes.plot(
                        self.abrirdatavalores5, color="blue")
                    self.reference_plot5 = plot_refs5[0]
                else:
                    self.reference_plot5.set_ydata(self.abrirdatavalores5)

                self.canvas5.axes.yaxis.grid(True, linestyle="--")
                start, end = self.canvas5.axes.get_ylim()
                self.canvas5.axes.yaxis.set_ticks(np.arange(self.eixoYmin5, self.eixoYmax5, 0.1))
                self.canvas5.axes.yaxis.set_major_formatter(
                    ticker.FormatStrFormatter("%0.1f")
                )
                self.canvas5.axes.set_xlabel(str(self.abrirdatataxaamostra5) + " amostras por segundo", labelpad=-27)
                self.canvas5.axes.set_ylabel("Tensão(V)", labelpad=0)
                self.canvas5.axes.set_ylim(
                    ymin=self.eixoYmin5, ymax=self.eixoYmax5)

                self.canvas5.draw()

    '''O método plotar localização recebe duas variáveis,
    latitude e longitude, abre um navegador em uma nova janela
    e busca pelas coordenadas informadas no Maps'''
    def plotar_localizacao(self):
        self.novajanela = QtWidgets.QMainWindow() #Criamos uma nova janela
        self.novajanela.setWindowTitle("Localização") #Adicionamos o título da janela
        self.novajanela.setWindowIcon(QIcon('ifc.png')) #Carregamos o ícone novo
        self.novajanela.show() #Mostramos a janela
        self.novajanela.resize(800,600) #Alteramos o tamanho da janela
        self.web=QWebEngineView() #Criamos um objeto do tipo navegador QWebEngineView
        self.url="http://www.google.com/maps/place/" + str(self.lat[2]) + "," + str(self.lon[2]) #Criamos a Url que deve ser informada ao navegador somando vários strings, incluindo latitude e longitude
        self.web.setUrl(QUrl(self.url)) #Informamos ao navegador a Url
        self.novajanela.setCentralWidget(self.web) #Adicionamos o navegador a nossa nova janela

    '''O método plotar espectro 1 utiliza os dados do
    recuperados do canal 1 para gerar um espectrograma no canvas 2.
    Ele só pode ser chamado quando existem dados recuperados
    de um arquivo .csv no canal 1'''
    def plotar_espectro_1(self):
        self.stop_worker_2() #Chamamos o método stop worker do canal 2, para impedir que mais dados sejam plotados no canvas 2
        self.canvas2.axes.clear() #Limpamos o canvas para prepará-lo para plotagem
        self.reference_plot2 = None #Desativamos a variável de controle da organização da plotagem, para recomeçar a plotagem com as novas configurações

        '''Organizamos os dados no eixo do canvas
        e atribuimos uma cor, nesse caso azul.'''
        plot_refs2 = self.canvas2.axes.specgram(
            self.abrirdatavalores1, Fs=self.abrirdatataxaamostra1)
        self.reference_plot2 = plot_refs2[0]

        self.canvas2.axes.grid(True, linestyle="--") #Cria uma grade tracejada no canvas
        start, end = self.canvas2.axes.get_ylim() #A função get_ylim verifica os 2 maiores valores do eixo Y e os guarda nas variáveis
        self.canvas2.axes.yaxis.set_ticks(np.arange(start, end, 500)) #Organizamos o eixo Y em divisões de 500Hz entre o valor máximo e o mínimo
        self.canvas2.axes.set_ylabel("Frequência(Hz)") #Cria uma legenda para o eixo Y
        self.canvas2.axes.set_xlabel("Tempo(s)", labelpad=-27) #Cria uma legenda para o eixo X a uma distância bem próxima do eixo(labelpad=-27)
        '''Estabelecemos os limites do eixo Y'''
        self.canvas2.axes.set_ylim(
            ymin=0, ymax=5000)

        self.canvas2.draw() #Desenha no canvas 'as atualizações feitas


    '''O método plotar espectro 2 utiliza os dados do
    recuperados do canal 3 para gerar um espectrograma no canvas 4.
    Ele só pode ser chamado quando existem dados recuperados
    de um arquivo .csv no canal 3
    Em termos de estrutura, é idêntico ao plotar espectro 1'''
    def plotar_espectro_2(self):
        self.stop_worker_4()
        self.canvas4.axes.clear()
        self.reference_plot4 = None

        if self.reference_plot4 is None:
            plot_refs4 = self.canvas4.axes.specgram(
                self.abrirdatavalores3, Fs=self.abrirdatataxaamostra3)
            self.reference_plot4 = plot_refs4[0]

        self.canvas4.axes.grid(True, linestyle="--")
        start, end = self.canvas4.axes.get_ylim()
        self.canvas4.axes.yaxis.set_ticks(np.arange(start, end, 500))
        self.canvas4.axes.set_ylabel("Frequência(Hz)")
        self.canvas4.axes.set_xlabel("Tempo(s)", labelpad=-27)
        self.canvas4.axes.set_ylim(
            ymin=0, ymax=5000)

        self.canvas4.draw()

    '''O método avalia tempe verifica se a temperatura
    do paciente passou de 37 graus e avisa o usuário do software'''
    def avalia_temp(self, value):
        self.tempcalc = float(value) #Recebe a temperatura por parâmetro
        if self.tempcalc > 37.0: #Se a temperatura for maior que 37 Graus
            self.cuidado = QtWidgets.QMessageBox() #Cria uma janela de mensagem
            self.cuidado.setIcon(QtWidgets.QMessageBox.Warning) #Substitui o ícone da janela por um ícone de aviso
            self.cuidado.setText("Atenção") #O texto principal da janela é colocado
            self.cuidado.setInformativeText("A temperatura corporal do paciente ultrapassou 37°C") #O texto secundário da janela é colocado
            self.cuidado.setWindowTitle("Aviso de Temperatura do Paciente") #O título da janela é alterado
            self.cuidado.show() #Mostra a janela

class Worker(QtCore.QRunnable): #Criamos a classe worker utilizando o Qrunnable como superclasse
    def __init__(self, método, *argumentos, **argumentoschave): #Criamos o método de inicialização da classe, e indicamos que não temos um número específico de argumentos no método com *args e *kwargs, além de receber o método como argumento
        super(Worker, self).__init__()
        self.function = método #O método do argumento é recebido
        self.args = argumentos #Os argumentos são recebidos
        self.kwargs = argumentoschave #Os argumentos chave são recebidos

    @pyqtSlot() #Decorador utilizado para indicar que esse método deve ser usado como slot Qt
    def run(self): #O método run, nesse caso
        self.function(*self.args, **self.kwargs) #Rodamos o método em uma linha de código separada por meio do método Run do QRunnable


app = QtWidgets.QApplication(sys.argv) #Criamos o objeto QApplication

if __name__ == "__main__": #Verifica se estamos no main ou fomos importados como módulo
    mainWindow = MainWindow() #Criamos o objeto com a nossa classe MainWindow
    mainWindow.show() #Mostramos a janela
    sys.exit(app.exec_()) #Caso se saia do programa, o python para também
