# -*- coding: UTF-8 -*-
from __main__ import qt, slicer
import os
import math
import vtk

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
        scriptedModulesPath = os.path.dirname(scriptedModulesPath)
        # devuelve la ruta del moduloName.ui
        path = os.path.join(scriptedModulesPath, 'Resources', 'UI', 'PlotsDaubara.ui')

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
        self.label.setText(u"Modulo para visualización de señales")

        self.plotSine()
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

        # fill the table with some example values
        numPoints = 100

        inc = 7.5 / (numPoints - 1)
        self.table.SetNumberOfRows(numPoints)
        for i in range(0, numPoints):
            self.table.SetValue(i, 0, i * inc)
            self.table.SetValue(i, 1, math.sin(i * inc))

        self.line = self.chart.AddPlot(vtk.vtkChart.LINE)
        #line = vtk.vtkPlotLine()
        self.line.SetInput(self.table, 0, 1)
        self.line.SetColor(0, 0, 0, 255)
        self.line.SetWidth(1.0)
        # cambiar el legend de los ejes
        self.line.GetXAxis().SetTitle("Tiempo (s)")
        self.line.GetYAxis().SetTitle("Amplitud")
        #line.Update()
        self.chartView.addPlot(self.line)

        self.setupTimer()

    def setupTimer(self):
        self.timer = qt.QTimer()
        self.timer.timeout.connect(self.plotwithTimer)
        self.timer.setInterval(self.inc * 1000)
        self.timer.start()

    def plotwithTimer(self):
        self.chart.RemovePlot(0)

        # aumenta el contador
        self.cnt += 1
        # se redimensiona la tabla
        self.table.SetNumberOfRows(self.cnt)
        for i in range(0, self.cnt):
            self.table.SetValue(i, 0, i * self.inc)
            self.table.SetValue(i, 1, 5 * math.sin(i * self.inc))
        if self.cnt > 1:
            line = self.chart.AddPlot(0)
            line.SetInput(self.table, 0, 1)

        if self.cnt == 100:
            self.cnt = 0



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
