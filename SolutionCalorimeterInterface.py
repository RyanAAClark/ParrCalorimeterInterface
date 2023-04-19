# -*- coding: utf-8 -*-

"""
Fetch data from a Parr 6755 solution calorimeter connected via ethernet cable.

Sript to collect and display data from a Parr 6755 solution calorimeter on a
GUI. Shows data on a graph in the GUI and will ouptut the data on screen to
selected folder as a .csv file. PLot and data are updated via buttons on the
interface.

last modified on 06/02/2023
Current Version: 0.1.0

Author: Ryan Clark | ryan.clark@chem.ox.ac.uk
"""

from ftplib import FTP
import datetime
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
import threading
from tkinter import Frame, Label, Entry, Button
import matplotlib.dates
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)


class calorimeter():
    """Data class for storing retrieving and analysing calorimter data."""

    def __init__(self, ip):
        self.ip = ip

    def collectDatalog(self):
        """Log into calorimeter using FTP and save datalog file to data."""
        # Log into calorimeter
        ftp = FTP(self.ip)
        print('Collecting datafile...')
        ftp.login(user='root', passwd='rootroot')

        # Change directory to data log file location
        ftp.cwd('../flash/log')

        # # Save data to data file on disk
        # fp = open('datalogB.csv','wb')
        # ftp.retrbinary('RETR datalog.csv', fp.write)
        # fp.close()

        # Save log file to variable 'data'
        self.UnTrimData = []
        ftp.retrbinary('RETR datalog.csv', self.UnTrimData.append)
        # Convert binary into list
        self.UnTrimData = str(self.UnTrimData)
        print('Success')
        ftp.quit()

    def trimData(self):
        """Turn data into two numpy arrays, one time and one bucket temp."""
        # Remove unneccesary characters from string
        for ch in ['b', '[', ']', "'", ","]:
            self.UnTrimData = self.UnTrimData.replace(ch, "")
        # Split into list of strings
        self.UnTrimData = self.UnTrimData.split('\\n')
        # Extract bucket temperature to numpy data array
        bucketData = []
        self.timeData = []
        for line in self.UnTrimData:
            if 'Bucket' in line.replace(" ", ""):
                # Remove spaces and excess text and collect bucket temperature
                tok = line.replace(" ", "").split("=")
                tok = tok[1].replace("JacketT", "")
                bucketData.append(float(tok))
            elif '-' in line:
                # Remove spaces and collect datetime info from tok
                tok = line.replace(" ", "")
                # tok[0:2] day, [3:5] month, [6:8] year
                # tok[8:10] hour, [11:13] minute, [14:16] second
                dateTime = datetime.datetime(2000 + int(tok[6:8]),
                                             int(tok[0:2]), int(tok[3:5]),
                                             int(tok[8:10]), int(tok[11:13]),
                                             int(tok[14:16]))
                self.timeData.append(dateTime)
        self.bucketData = np.array(bucketData)


class Window(Frame):
    """Class to create and host window for calorimeter script."""

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.init_window()

    def PlotGraph(self):
        """Collect parameters from GUI to update plot."""
        self.mt = float(self.textMonitorTime.get())
        self.expPath = str(self.textExport.get())
        self.trimData()
        self.line.set_xdata(self.timeData)
        self.line.set_ydata(self.bucketData)
        self.ax.set_xlim([min(self.timeData), max(self.timeData)])
        self.ax.set_ylim([min(self.bucketData), max(self.bucketData)])
        self.canvas.draw()

    def Export(self):
        """Export data to file."""
        filename = self.textExport.get() + "/data_" + \
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
        timeData = [self.timeData[-1]-self.timeData[i]
                    for i in range(len(self.timeData))]
        with open(filename, 'w') as f:
            f.write('# Time (s), Temperature (Celcius)\n')
            for i in range(len(self.bucketData)):
                f.write('%i, %f\n' % (timeData[0].seconds-timeData[i].seconds,
                                      self.bucketData[i]))
        self.PlotGraph()

    def ChangeFolder(self):
        """Change output folder for data."""
        expPath = tk.filedialog.askdirectory(mustexist=True)
        if len(expPath) > 0:
            self.expPath = expPath
        while len(self.textExport.get()) > 0:
            self.textExport.delete(0)
        self.textExport.insert(0, self.expPath)

    def UpdateData(self):
        """Update data from datalog file."""
        cal.collectDatalog()
        cal.trimData()
        self.trimData()
        self.labelStatus["text"] = "Data loaded at " +\
            datetime.datetime.now().strftime("%H:%M:%S on %d/%m/%Y")
        self.PlotGraph()

    def startThread(self):
        """Create the thread to collect data to not slow down program."""
        self.labelStatus["text"] = "Updating data..."
        t1 = threading.Thread(target=self.UpdateData)
        t1.start()

    def trimData(self):
        """Trim bucket and time data for plotting and exporting."""
        backIdx = int(self.mt*6)
        self.bucketData = cal.bucketData[-backIdx:]
        self.timeData = cal.timeData[-backIdx:]

    def init_window(self):
        """Create window and start the moitoring of the calorimeter."""
        self.master.title("Solution calorimeter")
        self.pack(fill='both', expand=1)

        # Create labels in window
        self.labelMonitorTime = Label(self, text="Monitor Time (min.)",
                                      width=15)
        self.labelMonitorTime.grid(row=0, column=1)
        self.labelExport = Label(self, text="Output folder for data", width=18)
        self.labelExport.grid(row=0, column=2, columnspan=2)
        self.labelStatus = Label(self, text="Data loaded at " +
                                 datetime.datetime.now().strftime(
                                     "%H:%M:%S on %d/%m/%Y"), width=30,
                                 justify="left", font=("Arial", 20))
        self.labelStatus.grid(row=4, column=0, columnspan=3, sticky="W")

        # Create entry fields in window
        self.textMonitorTime = Entry(self, width=15)
        self.textMonitorTime.grid(row=1, column=1)
        self.textExport = Entry(self, width=60)
        self.textExport.grid(row=1, column=2, columnspan=2)

        # Set default values for entry fields
        self.textExport.insert(0, "T:/Student data 2022-2023/2nd Year")
        self.textMonitorTime.insert(0, "20")
        self.mt = 20
        self.expPath = "T:/Student data 2022-2023/2nd Year"

        # Create buttons
        self.buttonUpdateData = Button(self, text="Refresh Data",
                                       command=self.startThread,
                                       width=15, height=2)
        self.buttonUpdateData.grid(row=0, column=0, rowspan=3)
        self.buttonPlot = Button(self, text="Update Plot",
                                 command=self.PlotGraph, width=15)
        self.buttonPlot.grid(row=2, column=1)
        self.buttonSelect = Button(self, text="Select folder",
                                   command=self.ChangeFolder, width=15)
        self.buttonSelect.grid(row=2, column=2)
        self.buttonExport = Button(self, text="Export plot data",
                                   command=self.Export, width=15)
        self.buttonExport.grid(row=2, column=3)

        # Trim data initially
        self.trimData()

        # Create Figure in window
        self.fig = plt.Figure(figsize=(12, 7))
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot(self.timeData, self.bucketData)
        date_form = matplotlib.dates.DateFormatter("%H:%M:%S")
        self.ax.xaxis.set_major_formatter(date_form)
        self.ax.set_xlim([min(self.timeData), max(self.timeData)])
        self.ax.set_ylim([min(self.bucketData), max(self.bucketData)])
        self.ax.set_xlabel('Time [hh:mm:ss]', fontsize=20)
        self.ax.set_ylabel('Bucket Temperature [°C]', fontsize=20)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(column=0, row=3, columnspan=4)


if __name__ == '__main__':
    # Define IP address of calorimeter
    ipaddr = input('Enter ip address of calorimeter: ')

    # Set up calorimeter class with ip address
    cal = calorimeter(ipaddr)

    # Connect and collect data
    cal.collectDatalog()
    cal.trimData()

    # Creat window for application
    root = tk.Tk()
    root.geometry("860x610")
    root.resizable(False, False)
    app = Window(master=root)
    tk.mainloop()
