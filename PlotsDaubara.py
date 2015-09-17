# -*- coding: UTF-8 -*-
from __main__ import qt, slicer
import os
import math
import vtk
import json
import numpy

class PlotsDaubara:
    def __init__(self, parent):
        parent.title = 'PlotsDaubara'
        parent.icon = qt.QIcon(':Icons/Small/Tracker.png')
        self.parent = parent

class PlotsDaubaraWidget:
    def __init__(self, parent=None):
        self.observerTags = []
        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
            self.layout = parent.layout()
        if not parent:
            #self.layout = self.parent.layout()
            self.setup()
            self.parent.show()
        #banderas

        # Variables globales
        self.StatusModifiedEvent = slicer.vtkMRMLCommandLineModuleNode()\
        .StatusModifiedEvent
        self.Observations = []

        self.inc = 0.1
        self.seg = 0
        self.cnt = 0

    def setup(self):
        self.logic = PlotsDaubaraLogic()
        # configuración de la interfaz gráfica
        loader = qt.QUiLoader()
        moduleName = 'PlotsDaubara'
        # devuelve la ruta del .py
        scriptedModulesPath = \
        eval('slicer.modules.%s.path' % moduleName.lower())
        # lleva a la carpeta del modulo
        self.scriptedModulesPath = os.path.dirname(scriptedModulesPath)
        # devuelve la ruta del moduloName.ui
        path = os.path.join(self.scriptedModulesPath, 'Resources', 'UI', 'PlotsDaubara.ui')

        qfile = qt.QFile(path)
        qfile.open(qt.QFile.ReadOnly)
        widget = loader.load(qfile, self.parent)
        self.layout = self.parent.layout()
        self.widget = widget
        self.layout.addWidget(widget)

        # Conectar la escena con el widget
        self.widget.setMRMLScene(slicer.mrmlScene)

        #Obterner Botones
        self.label = self.get("label")
        self.chartView = self.get("ChartView")
        self.chartView.title = 'Señal EEG'
        self.label.setText(u"Modulo para visualización de señales")
        self.chartViewSEEG = self.get("cv_seeg")
        self.chartViewSEEG.title = 'SEEG'
        self.plotSine()
        self.plotSEEG()
        #self.setupChartView()

    def plotSine(self):

        #chart = vtk.vtkChartXY()
        self.chart = self.chartView.chart()
        self.chart.SetShowLegend(False)

        #line.SetMarkerStyle(vtk.vtkPlotPoints.CROSS)
        #pl = vtk.vtkPlotLine()
        #self.chartView.addPlot(pl)
        # create a table with some points in it
        self.table = vtk.vtkTable()

        arrX = vtk.vtkFloatArray()
        arrX.SetName('x')

        arrS = vtk.vtkFloatArray()
        arrS.SetName('Sine')

        self.table.AddColumn(arrS)
        self.table.AddColumn(arrX)

        # cargar los coeficientes
        fileJson = os.path.join(self.scriptedModulesPath,'Datos','Coeficientes','coeff_ar.json')
        #nombreJson = "/home/jhon/Dropbox/Trabajo_GIBIC/SimuladorNeuroFuncional/SignalsEEG/coeff_ar.json"
        os.path.exists(fileJson)

        jsonData = open(fileJson)
        data = json.load(jsonData)
        jsonData.close()

        ECR1_clean = data['Clean_ECR1'] # Tamaño 129x24.
        
        canal = 58  # Cambiar canal. El numero del canal a simular y graficar es (canal+1), los indices comienzan en cero.

        channel = ECR1_clean[canal][:]
        print ("valores del canal")
        print(channel)

        cont = 0
        ch = []
        for j in channel:
            if not numpy.isnan(j):
                ch.insert( cont, j)
                cont = cont + 1
        # Convierte lista a numpy array.
        self.ch = numpy.array(ch)
        # Simulación señal EEG.
        numPoints = 1001

        # Vector de ruido (White Noise)
        # Longitud señal 201 datos.
        self.VectorNoise = math.sqrt(ch[2])*numpy.random.normal(0.0, 1.0, numPoints)
        #VectorNoise = numpy.random.normal(0, 1.0, 201)

        self.sim_senal = range(numPoints)     # 1000 datos son 10 seg. original 201
        self.coeff = ch[4:]

        # fill the table with some example values

        self.inc = 10.0 / (numPoints - 1)
        self.table.SetNumberOfRows(numPoints)
        for k in range(0, numPoints):
            sim = 0
            for i in (range(self.ch[1].astype(numpy.int64))):
                if (k > i):
                    sim = sim - (self.coeff[i]*self.sim_senal[k-i-1])
            self.sim_senal[k] = sim + self.VectorNoise[k]

            self.table.SetValue(k, 0, k * self.inc)
            self.table.SetValue(k, 1, self.sim_senal[k])
            #print (k*inc)
            #print (sim_senal[k])

        self.line = self.chart.AddPlot(vtk.vtkChart.LINE)
        #line = vtk.vtkPlotLine()
        self.line.SetInput(self.table, 0, 1)
        self.line.SetColor(0, 0, 0, 255)
        self.line.SetWidth(0.3)
        # cambiar el legend de los ejes
        self.line.GetXAxis().SetTitle("Tiempo (s)")
        self.line.GetYAxis().SetTitle("Amplitud")
        #line.Update()
        self.chartView.addPlot(self.line)

        self.setupTimer()
        
    def plotSEEG(self):
        
        #chart = vtk.vtkChartXY()
        self.chartSEEG = self.chartViewSEEG.chart()
        self.chartSEEG.SetShowLegend(False)
        
        #line.SetMarkerStyle(vtk.vtkPlotPoints.CROSS)
        #pl = vtk.vtkPlotLine()
        #self.chartView.addPlot(pl)
        # create a table with some points in it
        self.tableSEEG = vtk.vtkTable()
        
        arrX = vtk.vtkFloatArray()
        arrX.SetName('x')
        
        arrS = vtk.vtkFloatArray()
        arrS.SetName('SEEG')
        
        self.tableSEEG.AddColumn(arrS)
        self.tableSEEG.AddColumn(arrX)
        
        # Simulación señal EEG.
        a,b = self.leerCoeficientes()
        signalSEEG, tiempo = self.simularTotal(a,b,10,[0])
        y = len(signalSEEG)
        x = len(tiempo)
        print (y,x)
        self.tableSEEG.SetNumberOfRows(y)
        for k in range(0,y):
            self.tableSEEG.SetValue(k,0,tiempo[k])
            self.tableSEEG.SetValue(k,1,signalSEEG[k])
        
        self.lineSEEG = self.chartSEEG.AddPlot(vtk.vtkChart.LINE)
        #line = vtk.vtkPlotLine()
        self.lineSEEG.SetInput(self.tableSEEG, 0, 1)
        self.lineSEEG.SetColor(0, 0, 0, 255)
        self.lineSEEG.SetWidth(1.0)
        # cambiar el legend de los ejes
        self.lineSEEG.GetXAxis().SetTitle("Tiempo (s)")
        self.lineSEEG.GetYAxis().SetTitle("Amplitud")
        #line.Update()
        self.chartViewSEEG.addPlot(self.lineSEEG)
        
        
    def setupTimer(self):
        self.timer = qt.QTimer()
        self.timer.timeout.connect(self.plotwithTimer)
        self.timer.setInterval(self.inc)
        self.timer.start()

    def plotwithTimer(self):
        self.chart.RemovePlot(0)

        # aumenta el contador
        self.cnt += 1
        # eliminamos el primer valor del vector
        self.sim_senal = self.sim_senal[1:]
        # agremos un valor nuevo al final
        sim = 0
        for i in (range(self.ch[1].astype(numpy.int64))):
            if (self.cnt > i):
                sim = sim - (self.coeff[i] * self.sim_senal[self.cnt - i - 1])
                sim = 15 if (sim > 15) else (-15 if sim < - 15 else sim)
        self.sim_senal.append(sim + self.VectorNoise[self.cnt])
        
        # se redimensiona la tabla
        
        for i in range(0, 1001):
            self.table.SetValue(i, 0, i * self.inc)
            self.table.SetValue(i, 1, self.sim_senal[i])
        if self.cnt > 1:
            line = self.chart.AddPlot(0)
            line.SetInput(self.table, 0, 1)

        if self.cnt == 1000:
            self.cnt = 0
        
    def leerCoeficientes(self):
        # cargar los coeficientes
        aFile = os.path.join(self.scriptedModulesPath,'Datos','Coeficientes','sujeto1_dystonia_gpe.json')
        bFile = os.path.join(self.scriptedModulesPath,'Datos','Coeficientes','sujeto1_dystonia_gpe_transiente.json')
        
        if (os.path.exists(aFile) and os.path.exists(bFile)):
            ajson = open(aFile)
            bjson = open(bFile)
            
            a = json.load(ajson)
            b = json.load(bjson)
            
            ajson.close()
            bjson.close()
        return a,b
    
    def simularSeeg(self,coef_AR, orderModel, noise, timeSimul, fs):
        """
            signalSimul = simularSeeg(coef_AR, orderModel, noise, timeSimul,fs)
            Función que genera una señal de EEG a partir de los parámetros de modelo AR
            Variables de entrada:
            coef_AR - Parámetros del modelo AR, vector.
            orderModel - Orden del modelo AR, escalar.
            noise - Información del ruido del proceso. Si es un escalar
                        representa la varianza del ruido, si es un vector
                        corresponde al ruido blanco del proceso. 
            timeSimul - Tiempo que se simulara la señal EEG en segundos,
                        # escalar.
            fs - frecuencia de muestreo de la señal EEG original, escalar.      
        
            Variable de salida:
            signalSimul - Señal EEG simulada, vector.
        #time - tiempo de simulación de la señal EEG, vector. #deshabilitado
        """
        time = numpy.linspace(0,timeSimul,timeSimul*fs)
        length_time = len(time)
        whiteNoise = numpy.sqrt(noise)*numpy.random.normal(0,1,length_time)
            
        signalSimul = numpy.zeros(length_time)
            
        for k in range(length_time):
            simul = 0
            for i in range(orderModel):
                if k > i:
                    simul = simul - coef_AR[i]*signalSimul[k-i-1]
            signalSimul[k] = simul + whiteNoise[k]
        return signalSimul

    def simularTotal(self,a,b,tiempoSimulacion=10,EEGSimulTotal=[0]):
        fs = a["fs"]
        print(fs)
        while len(EEGSimulTotal) <= (tiempoSimulacion*fs):
            #--------------------------------------------------------------------------
            # simulación segmento corto.
            segm_EEGsimul= [0]
            segm_t = (0.2*numpy.random.rand()) + 0.2
            while (len(segm_EEGsimul) <= (segm_t*fs)):
                t = (0.003*numpy.random.rand()) + 0.001
                segm_EEGsimul1 = self.simularSeeg(a["coef_AR"],a["ordenModelo"], a["varianzaRuido"], t, a["fs"])
                    
                t = (0.0003 *numpy.random.rand()) + 0.0007
                segm_EEGsimul2 = self.simularSeeg(b["coef_AR"],b["ordenModelo"], b["varianzaRuido"], t, b["fs"])
                segm_EEGsimul  = numpy.concatenate((segm_EEGsimul, segm_EEGsimul1, segm_EEGsimul2))
            #--------------------------------------------------------------------------
            
            #--------------------------------------------------------------------------
            # Simulación segmento largo.
            timeSimul1 = (0.2 *numpy.random.rand()) + 0.3
            EEGsimul1 = [0]
            while (len(EEGsimul1) <= timeSimul1*fs):
                t = (0.001*numpy.random.rand()) + 0.004
                EEGsimul_A = self.simularSeeg(a["coef_AR"], a["ordenModelo"],a["varianzaRuido"], t, a["fs"])    
                if (numpy.random.rand() >= 0.7):
                    t = (0.0003 * numpy.random.rand()) + 0.0007
                    segm_EEGsimul_rand = self.simularSeeg(b["coef_AR"],b["ordenModelo"], b["varianzaRuido"], t, b["fs"])
                    EEGsimul_A = numpy.concatenate((EEGsimul_A,segm_EEGsimul_rand))
                EEGsimul1 = numpy.concatenate((EEGsimul1,EEGsimul_A))
            #------------------------------------------------------------------------------------------
            EEGSimulTotal = numpy.concatenate((EEGSimulTotal,segm_EEGsimul,EEGsimul1))
        
        EEGSimulTotal = EEGSimulTotal[0:fs*tiempoSimulacion]
        tiempoSimul = numpy.linspace(0,((len(EEGSimulTotal)-1)/fs),len(EEGSimulTotal))
        return EEGSimulTotal,tiempoSimul
        #print(len(EEGSimulTotal))
            
        #tiempoSimul = numpy.linspace(0,((len(EEGSimulTotal)-1)/fs),len(EEGSimulTotal))

### === Metodos convenientes para leer los widgets === ###
    def get(self, objectName):
        return self.findWidget(self.widget, objectName)

    def findWidget(self, widget, objectName):
        if widget.objectName == objectName:
            return widget
        else:
            for w in widget.children():
                resulting_widget = self.findWidget(w, objectName)
                if resulting_widget:
                    return resulting_widget
            return None

class PlotsDaubaraLogic:
    def __ini__():
        pass

    def cambiarModulo(self, modulo='PlotsDaubara'):
        slicer.util.selectModule(modulo)

    def mostrarMensaje(self, mensaje, titulo="Mensaje", duracion=2000):
        """Este metódo muestra un mensaje y espera por un tiempo.
        """
        print(mensaje)
        self.info = qt.QDialog()
        self.infoLayout = qt.QVBoxLayout()
        self.info.setLayout(self.infoLayout)
        self.info.windowTitle = titulo
        self.label = qt.QLabel(mensaje, self.info)
        self.font = qt.QFont("Times", 18, Bold=True)
        self.label.setFont(self.font)
        #self.label.setStyleSheet("color:red")
        #self.label.setFixedSize(500,120)
        self.infoLayout.addWidget(self.label)
        qt.QTimer.singleShot(duracion, self.info.close)
        self.info.exec_()
