#!/usr/bin/env python
#from Geant4 import *
import sys
import argparse
import logging
from StringIO import StringIO

# Grab stdout so Geant4 doesn't announce itself
#temp = sys.stdout
#sys.stdout = StringIO()
import Geant4 as G4


from Geant4 import HepRandom, gRunManager
from Geant4 import gTransportationManager, gApplyUICommand
from Geant4 import mm
import g4py.ExN03geom
import g4py.ExN03pl
import g4py.ParticleGun

import argparse
import logging
import logging.config

import Configuration
import EventAction
import ToroidField
from GenieGeneratorAction import GenieGeneratorAction
from GUI import VlenfApp
from DetectorConstruction import VlenfDetectorConstruction

class StreamToLogger(object):
   """                                                                                                                                              
   Fake file-like stream object that redirects writes to a logger instance.                                                                         
   """
   def __init__(self, logger, log_level=logging.INFO):
      self.logger = logger
      self.log_level = log_level
      self.linebuf = ''

   def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simulate the VLENF')
    parser.add_argument('NAME', help='name for the simulation output')
    parser.add_argument('--number_events', help='how many events to simulate',
                        type=int, default=0)
    parser.add_argument('--run', help='run number',
                        type=int, default=1)

    parser.add_argument('--gui', action='store_true')
    parser.add_argument('--event_display', action='store_true')
    parser.add_argument('--view', choices=['XY', 'ZY', 'ZX'], default='ZX')

    parser.add_argument('--pause',
                        help='pause after each event, require return')

    # should test these correspond to numeric errors
    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    parser.add_argument('--log_level', choices=log_levels, default='WARNING')
    args = parser.parse_args()

    #args.log_level
    #logging.getLogger('test').setLevel("WARNING")
    #logging.config.fileConfig('logging.conf')
    #logging.basicConfig(filename='example.log', mode='w', level=logging.DEBUG)
    # create console handler and set level to debug

    logging.basicConfig(filename='example.log', mode='w', level=logging.DEBUG)

    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.setLevel(args.log_level)
    formatter = logging.Formatter('%(levelname)s(%(name)s): %(message)s')
    console_handler.setFormatter(formatter)

    #file_handler = logging.FileHandler('testlog', mode='w')
    #file_handler.setLevel('DEBUG')

    logger = logging.getLogger('root')
    #logger.setLevel(logging.NOTSET)
    logger.addHandler(console_handler)
    #logger.addHandler(file_handler)

    stdout_logger = logging.getLogger('root').getChild('STDOUT')
    sl = StreamToLogger(stdout_logger, logging.INFO)
    sys.stdout = sl
 
    stderr_logger = logging.getLogger('root').getChild('STDERR')
    sl = StreamToLogger(stderr_logger, logging.ERROR)
    sys.stderr = sl

    #logger = logging.getLogger('gnomon')
    ##logger.basicConfig(filename='example.log',level=logging.DEBUG)
    #logger.setLevel(args.log_level)

    """ SHOULD CHECK IF NAME EXISTS, and warn if yes!!"""

    Configuration.run = args.run
    Configuration.name = args.NAME

    rand_engine = G4.Ranlux64Engine()
    HepRandom.setTheEngine(rand_engine)
    HepRandom.setTheSeed(20050830)

    exN03geom = VlenfDetectorConstruction()
    gRunManager.SetUserInitialization(exN03geom)

    exN03PL = g4py.ExN03pl.PhysicsList()
    gRunManager.SetUserInitialization(exN03PL)
    exN03PL.SetDefaultCutValue(1.0 * mm)
    exN03PL.SetCutsWithDefault()

    myEA = EventAction.VlenfEventAction()
    gRunManager.SetUserAction(myEA)

    pgPGA = GenieGeneratorAction()
    gRunManager.SetUserAction(pgPGA)

    fieldMgr = gTransportationManager.GetFieldManager()

    myField = ToroidField.ToroidField()
    fieldMgr.SetDetectorField(myField)
    fieldMgr.CreateChordFinder(myField)

    gRunManager.Initialize()

    #  This is a trick that, if enabled, lets the event action notify the
    #  detector when the event is over.  This allows the sensitive detector
    #  to perform a bulk commit of 'mchit's to the event store.  It's meant
    #  to be an optimization since writing tons of small 'mchit's individually
    #  to the database is slow.
    #
    #  This can be disabled for conceptually clarify in SD.py
    sd = exN03geom.getSensitiveDetector()
    myEA.setSD(sd)

    if args.event_display:
        gApplyUICommand("/vis/sceneHandler/create OGLSX OGLSX")
        gApplyUICommand("/vis/viewer/create OGLSX oglsxviewer")
        gApplyUICommand("/vis/drawVolume")
        gApplyUICommand("/vis/scene/add/trajectories")
        gApplyUICommand("/tracking/storeTrajectory 1")
        gApplyUICommand("/vis/scene/endOfEventAction accumulate")
        gApplyUICommand("/vis/scene/endOfRunAction accumulate")
        gApplyUICommand("/vis/viewer/select oglsxviewer")
        gApplyUICommand("/vis/scene/add/trajectories")

        if args.view == 'XY':
            gApplyUICommand("/vis/viewer/set/viewpointVector 0 0 -1")
        elif args.view == 'ZY':
            gApplyUICommand("/vis/viewer/set/viewpointVector -1 0 0")
        elif args.view == 'ZX':
            gApplyUICommand("/vis/viewer/set/viewpointVector -1 100000 0")

    if args.gui:
        app = VlenfApp()
        app.mainloop()

    if args.pause:
        for i in range(args.number_events):
            gRunManager.BeamOn(1)
            raw_input()
    else:
        gRunManager.BeamOn(args.number_events)

    
