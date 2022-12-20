from PyQt5 import QtWidgets, uic, QtCore #Importamos o QtWidgets para podermos utilizar a QMainWindow, o uic para poder importar nosso arquivo .ui e o qtcore para podermos criar nossas linhas de processo
from matplotlib.figure import Figure #Importamos a Figura do Matplotlib para que possamos utilizar a classe dentro do nosos canvas
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas #Importamos o figure canvas
from PyQt5.QtGui import QIcon #Importamos o QIcon para podermos trocar o ícone da janela
import sys #Importamos o sys para podermos controlar quando saimos do programa
from PyQt5.QtCore import pyqtSlot #Importamos o pyqtSlot para poder trabalhar com multiplas linhas de código simultâneas
import numpy as np #Importamos o numpy para utilizar suas classes de vetores para receber os dados de som
import sounddevice as sd #Importamos o para poder estabelecer comunicação com os dispositivos de áudio e receber dados
from PyQt5.QtMultimedia import QAudioDeviceInfo, QAudio #Serve simplesmente para listarmos os nomes dos dispositivos de áudio do computador
import queue #Fila para comunicação entre o método recebeDados e o método atualizar_canvas.
'''Podemos utilizar a queue para impedir que 2 funções (que rodam em linhas 
distintas de execução - ou threads, em inglês) tentem acessar o mesmo 
espaço de memória simultâneamente, o que pode causar multiplos erros'''

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

        self.dataY1 = None #Inicializamos a variável que conterá os dados a serem plotados
        self.dataY2 = None

        self.ui = uic.loadUi("main0.4_plotagem_2_canais.ui", self) #Podemos importar nosso arquivo ui criado no QT Designer
        self.ui.setWindowIcon(QIcon('ifc.png')) #Carregamos o ícone novo

        self.threadpool = QtCore.QThreadPool() #Criamos um objeto da classe QThreadPool

        self.lista_dispositivos = [] #Uma lista de dispositivos sem nada ainda

        '''Inserimos o nome dos dispositivos de áudio da lista de dispositivos do computador na nossa lista vazia
        utilizando a lógica: para cada elemento da lista de dispositivos, insira o nome elemento na lista vazia'''
        for item in infos_disp_audio:
            self.lista_dispositivos.append(item.deviceName())

        self.comboBox.addItems(self.lista_dispositivos) #Adicionamos os itens da nossa lista na comboBox
        self.comboBox_2.addItems(self.lista_dispositivos)
        self.comboBox.currentIndexChanged["QString"].connect(self.atualizar_canal1) #Caso o valor da comboBox mude, enviamos esse valor para o método atualizar canal
        self.comboBox_2.currentIndexChanged["QString"].connect(self.atualizar_canal2)
        self.comboBox.setCurrentIndex(0) #Começamos o programa com a comboBox no valor 0
        self.comboBox_2.setCurrentIndex(0)

        self.canvas1 = MatPlotLibCanvas(self, width=6, height=2.1, dpi=100) #Criamos o nosso objeto canvas1
        self.ui.gridLayout_4.addWidget(self.canvas1, 2, 1, 1, 1) #Adicionamos o canvas1 ao nosso layout
        self.reference_plot1 = None #Serve para testar se estamos plotando os dados em um plot já organizado ou não

        self.canvas2 = MatPlotLibCanvas(self, width=6, height=2.1, dpi=100)
        self.ui.gridLayout_6.addWidget(self.canvas2, 1, 1, 1, 1)
        self.reference_plot2 = None

        self.q1 = queue.Queue(maxsize=20) #Inicializamos a fila que será utilizada para comunicação de dados
        self.q2 = queue.Queue(maxsize=20)

        # Intervalo de atualização da plotagem e do programa:
        self.intervalo = 30  #controle do intervalo do temporizador em milisegundos

        #Variáveis para plotagem do sinal
        self.tam_janela1 = 1000  #Tamanho da janela de dados em milisegundos
        self.pular_amostra1 = 1  #Pula 1 amostra
        self.canais1 = [1] #Número de Canais
        self.eixoYmin1 = -0.5 #Valor mínimo do eixo Y do gráfico
        self.eixoYmax1 = 0.5 #Valor máximo do eixo Y do gráfico

        self.tam_janela2 = 1000
        self.pular_amostra2 = 1
        self.canais2 = [1]
        self.eixoYmin2 = -0.5
        self.eixoYmax2 = 0.5

        self.achou_dispositivo = False

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
            self.plotdata1 = np.zeros((tamanho_1, len(self.canais1)))
        else:
            self.desabilitar_botoes_1() #Desligamos os botões
            self.pushButton_2.setEnabled(False)
            self.pushButton_2.setStyleSheet(
                "QPushButton" "{" "background-color : lightblue;" "}"
            )
            self.lista_dispositivos.append("No Devices Found") #Inserimos na lista a informação que não há dispositivos disponíveis
            self.comboBox.addItems(self.lista_dispositivos) #Inserimos a lista na comboBox
        self.achou_dispositivo = False #Resetamos a variável

        for self.dispositivo2 in range(len(infos_disp_audio)):
            try:
                device_info1 = sd.query_devices(self.dispositivo2, "input")
                if device_info1:
                    self.achou_dispositivo = True
                    break
            except:
                pass

        if self.achou_dispositivo:  # run if the device connection is successful
            # print(device_info)
            self.taxa_amostra_2 = device_info1["default_samplerate"]
            length1 = int(self.tam_janela2 * self.taxa_amostra_2 /
                          (1000 * self.pular_amostra2))
            sd.default.samplerate = self.taxa_amostra_2
            self.plotdata2 = np.zeros((length1, len(self.canais2)))
        else:
            self.desabilitar_botoes_2()
            self.pushButton_4.setEnabled(False)
            self.pushButton_4.setStyleSheet(
                "QPushButton" "{" "background-color : lightblue;" "}"
            )
            self.lista_dispositivos.append("No Devices Found")
            self.comboBox_2.addItems(self.lista_dispositivos)
        self.achou_dispositivo = False

        self.timer = QtCore.QTimer() #Criamos um objeto do tipo timer para controle temporal do programa
        self.timer.timeout.connect(self.atualizar_canvas_1) #Conectamos o fim de um ciclo do temporizador ao método que atualiza o canvas
        self.timer.timeout.connect(self.atualizar_canvas_2)
        self.timer.timeout.connect(self.atualizar_threads_ativos) #Método para atualizar o valor dos threads ativos é chamado quando o timer finaliza um ciclo
        self.timer.setInterval(self.intervalo)  #Atribuimos o intervalo do temporizador em milisegundos
        self.timer.start() #Começamos a contar o tempo

        self.data1 = [0] #Variável que recebe os dados da fila
        self.data2 = [0]

        self.lineEdit.textChanged["QString"].connect(self.atualizar_janela_1) #Caso o lineEdit tenha seu valor alterado, é chamado o método atualizar janela com o texto atual do lineEdit como argumento
        self.lineEdit_2.textChanged.connect(self.atualizar_taxa_amostragem_1) #Caso o lineEdit tenha seu valor alterado, é chamado o método atualizar janela com o texto atual do lineEdit como argumento
        self.spinBox_downsample.valueChanged.connect(self.atualizar_pular_amostra_1) #Caso o spinBox tenha seu valor alterado, é chamado o método atualizar janela com o valor atual do lineEdit como argumento
        self.spinBox_updateInterval.valueChanged.connect(self.atualizar_intervalo_1) #Caso o spinBox tenha seu valor alterado, é chamado o método atualizar janela com o valor atual do lineEdit como argumento

        self.lineEdit_3.textChanged["QString"].connect(self.atualizar_janela_2)
        self.lineEdit_4.textChanged.connect(self.atualizar_taxa_amostragem_2)
        self.spinBox_downsample_2.valueChanged.connect(self.atualizar_pular_amostra_2)
        self.spinBox_updateInterval_2.valueChanged.connect(self.atualizar_intervalo_1)

        '''Métodos recebem os valores das spinBoxes
        e atualizam os valores do mínimo e máximo do eixo Y'''
        self.doubleSpinBox.valueChanged.connect(
            self.atualizar_eixoYmin1)
        self.doubleSpinBox_2.valueChanged.connect(
            self.atualizar_eixoYmax1)

        self.doubleSpinBox_3.valueChanged.connect(
            self.atualizar_eixoYmin2)
        self.doubleSpinBox_4.valueChanged.connect(
            self.atualizar_eixoYmax2)

        self.pushButton.clicked.connect(self.start_worker_1) #Caso o botão 1 seja clicado, iniciamos o método start worker
        self.pushButton_2.clicked.connect(self.stop_worker_1) #Caso o botão 2 seja clicado, iniciamos o método stop worker
        self.worker1 = None #O objeto worker é criado, inicialmente como uma variável vazia
        self.go_on1 = True #A variável go_on tem seu valor definido. Por meio desta variável iremos controlar a plotagem e aquisição de dados

        self.pushButton_3.clicked.connect(self.start_worker_2)
        self.pushButton_4.clicked.connect(self.stop_worker_2)
        self.worker2 = None
        self.go_on2 = True

    '''O método que coleta o sinal de audio de um dado dispositivo selecionado pelo método atualizar canal.
    Começamos com o comando try, que realiza o código e caso ocorra uma exceção, se informa um código
    de erro no terminal e chamando o método stop worker com o objetivo de parar o recebimento de dados'''
    def recebeDados_1(self):
        try:
            QtWidgets.QApplication.processEvents() #Método utilizado para processar eventos da interface de usuário, utilizamos para que se possa receber comandos do usuário enquanto esse método é executado

            '''O método audio callback é chamado pelo objeto stream1 do tipo input stream.
            A lógica é que podemos alterar a formação dos dados recebidos do áudio de acordo com o nosso método.
            Também aproveitamos essa método que é chamada constantemente para informar os dados que estamso recebendo'''
            def audio_callback_1(indata, frames, time, status): #O método recebe como parâmetro os dados que estão entrando (indata)
                self.q1.put(indata[:: self.pular_amostra1, [0]])

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

            # uses sounddevice to obtain the input stream, check the InputStream for details
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

    def atualizar_canal1(self, value): #Atualiza o dispositivo atual
        self.dispositivo1 = self.lista_dispositivos.index(value)

    def atualizar_canal2(self, value):
        self.dispositivo2 = self.lista_dispositivos.index(value)

    '''Método desabilitar botões simplesmente
    desativa os botões da interface enquanto estamos
    plotando para evitar que o usuário possa
    alterar valores importantes no meio do processo.'''
    def desabilitar_botoes_1(self):
        self.lineEdit.setEnabled(False)
        self.lineEdit_2.setEnabled(False)
        self.spinBox_downsample.setEnabled(False)
        self.spinBox_updateInterval.setEnabled(False)
        self.comboBox.setEnabled(False)
        self.pushButton.setEnabled(False)
        # Trocamos a cor do botão para indicar que estamos no meio do processo de plotar os dados
        self.pushButton.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        )

        self.canvas1.axes.clear() #Limpamos o canvas para preparar a área para a próxima plotagem

    def desabilitar_botoes_2(self):
        self.lineEdit_3.setEnabled(False)
        self.lineEdit_4.setEnabled(False)
        self.spinBox_downsample_2.setEnabled(False)
        self.spinBox_updateInterval_2.setEnabled(False)
        self.comboBox_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)
        self.pushButton_3.setStyleSheet(
            "QPushButton" "{" "background-color : lightblue;" "}"
        )

        self.canvas2.axes.clear()

    '''Método ativar botões'''
    def ativar_botoes_1(self):
        self.pushButton.setEnabled(True)
        self.lineEdit.setEnabled(True)
        self.lineEdit_2.setEnabled(True)
        self.spinBox_downsample.setEnabled(True)
        self.spinBox_updateInterval.setEnabled(True)
        self.comboBox.setEnabled(True)

    def ativar_botoes_2(self):
        self.pushButton_3.setEnabled(True)
        self.lineEdit_3.setEnabled(True)
        self.lineEdit_4.setEnabled(True)
        self.spinBox_downsample_2.setEnabled(True)
        self.spinBox_updateInterval_2.setEnabled(True)
        self.comboBox_2.setEnabled(True)

    def start_stream_1(self): #Método que puxa o método pegar audio - Essa é o método passado para o objeto worker
        self.recebeDados_1()

    def start_stream_2(self):
        self.receberDados_2()

    def atualizar_eixoYmin1(self, minval): #Método recebe o valor mínimo do eixo da spinBox e atualiza a variável
        self.eixoYmin1 = float(minval)

    def atualizar_eixoYmax1(self, maxval): #Método recebe o valor máximo do eixo da spinBox e atualiza a variável
        self.eixoYmax1 = float(maxval)

    def atualizar_eixoYmax2(self, maxval):
        self.eixoYmax2 = float(maxval)

    def atualizar_eixoYmin2(self, minval):
        self.eixoYmin2 = float(minval)

    def atualizar_threads_ativos(self): #Método insere o valor que é monitorado pela classe threadpool no label
        self.label_16.setText(f"{self.threadpool.activeThreadCount()}")

    def atualizar_intervalo_1(self, value): #Método para atualizar o intervalo de atualização do programa
        self.intervalo = int(value)

    '''Atualiza o tamanho da janela de dados.
    O valor recebido em segundos é convertido
    no tamanho do eixo X do canvas
    plotdata recebe um objeto com as dimensões do tamanho da janela
    e número de canais'''
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
            # print(self.samplerate, sd.default.samplerate)
            self.plotdata2 = np.zeros((tamanho_2, len(self.canais2)))
        except:
            pass

    '''Atualizamos o número de amostras puladas, para o valor 1,
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


    def atualizar_canvas_1(self):
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

            '''Estabelecemos os limites do eixo Y'''
            self.canvas1.axes.set_ylim(
                ymin=self.eixoYmin1, ymax=self.eixoYmax1)

            self.canvas1.axes.grid(True, linestyle="--") #Cria uma grade tracejada no canvas
            self.canvas1.draw() #Redesenha no canvas as atualizações feitas

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

            self.canvas2.axes.set_ylim(
                ymin=self.eixoYmin2, ymax=self.eixoYmax2)

            self.canvas2.axes.grid(True, linestyle="--")
            self.canvas2.draw()

        except Exception as e7:
            print("Error:", e7)
            pass

    def start_worker_1(self): #Começa o worker com o método start stream como parâmetro

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
        self.timer.setInterval(self.intervalo)  #Atualizamos o intervalo, caso tenha sido alterado

    def start_worker_2(self):

        self.desabilitar_botoes_2()

        self.canvas2.axes.clear()

        self.go_on2 = False
        self.worker2 = Worker(
            self.start_stream_2,
        )
        self.threadpool.start(self.worker2)
        self.reference_plot2 = None
        self.timer.setInterval(self.intervalo)  # msec

    def stop_worker_1(self): #Método que pausa o recebimento e a plotagem dos dados

        self.go_on1 = True #Ativação da variável go_on pausa o loop dentro dos métodos receberDados e atualizar_canvas
        with self.q1.mutex: #O método mutex "trava" a fila, não permitindo que os outros métodos do programa a acessem
            self.q1.queue.clear() #No caso, com a fila travada, podemos limpá-la
        #Mudamos o estilo do botão para indicar que já plotamos os dados, mas agora a plotagem está pausada
        self.pushButton.setStyleSheet(
            "QPushButton"
            "{"
            "background-color : rgb(92, 186, 102);"
            "}"
            "QPushButton"
            "{"
            "color : white;"
            "}"
        )
        self.ativar_botoes_1() #Ativamos os botões

    def stop_worker_2(self):

        self.go_on2 = True
        with self.q2.mutex:
            self.q2.queue.clear()
        self.pushButton_3.setStyleSheet(
            "QPushButton"
            "{"
            "background-color : rgb(92, 186, 102);"
            "}"
            "QPushButton"
            "{"
            "color : white;"
            "}"
        )
        self.ativar_botoes_2()

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