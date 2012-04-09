"""The EventAction is used by Geant4 to determine what to do before and after
each MC event."""

import logging

import Geant4 as G4
import Configuration
from Digitizer import VlenfSimpleDigitizer
from Fitter import VlenfPolynomialFitter
from Truth import AppendTruth
from processors.Utils import Compactor
from DataManager import CouchManager, FileManager
from Classifier import Length, ContinousLength

class VlenfEventAction(G4.G4UserEventAction):
    """The VLENF Event Action"""

    def __init__(self, pga=None):
        """execute the constructor of the parent class G4UserEventAction"""
        G4.G4UserEventAction.__init__(self)

        self.log = logging.getLogger('root')
        self.log = self.log.getChild(self.__class__.__name__)
        
        self.config = Configuration.DEFAULT()

        self.processors = []
        self.processors.append(VlenfSimpleDigitizer())
        self.processors.append(VlenfPolynomialFitter())
        self.processors.append(AppendTruth(pga))
        self.processors.append(Length())
        self.processors.append(ContinousLength())
        self.processors.append(CouchManager())
        
        # used to fetch mchits, only way given geant
        self.sd = None

    def BeginOfEventAction(self, event):
        """Executed at the beginning of an event, print hits"""
        self.log.debug("Beggining event %s", event.GetEventID())
        self.sd.setEventNumber(event.GetEventID())

    def setSD(self, sd):
        self.sd = sd

    def EndOfEventAction(self, event):
        """Executed at the end of an event, do nothing"""
        self.log.info('Processed event %d', event.GetEventID())

        docs = self.sd.getDocs()
        self.sd.clearDocs()

        for processor in self.processors:
            docs = processor.Process(docs)

    def Shutdown(self):
        for processor in self.processors:
            processor.Shutdown()


        
        
