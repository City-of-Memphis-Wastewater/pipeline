#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Existing Emerson notice:
# Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
# The contents of this file is proprietary information.

# User notes:
# This is an example of usage of PyEds2, generated on 2 April 2025 by Clayton Bennett at the City of Memphis.

import inspect
import sys
import os
# Assuming your current file is in 'project/scripts/' and the function
# is in 'project/module/'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'C:\\Users\\george.bennett\\AppData\\Local\\EDS92', 'Api')))


import PyEds2 as eds
"""This is an exploration of the functionality of the PyEds2 module"""
def basic_exploration():
    print(eds.__file__)
    print(dir(eds))
    print("createLive_object = PyEds2.createLive()")
    print("createLive_object.connect(asClient=0,asSource=1,Opts=dict())")
    print("import PyEds2 as eds")
    print("eds.createLive().connect(asClient=0,asSource=1,Opts=dict())")
    print("\n")
def exploration():
    print(dir(eds))
    #print(eds.createLive)
    #print(eds.setupLogger)
    print(eds.__file__)
    print("\n")
    createLive_object = eds.createLive()
    print("createLive_object.connect(0,0,None)")
    inspect.getmodule(eds.createLive())
    inspect.getcomments(eds.createLive())
    inspect.getmembers(eds.createLive())
    print("\n")
    cL_o_functions = [createLive_object.connInfo,
                      createLive_object.connect,
                      createLive_object.originate,
                      createLive_object.pointDynamicInfo,
                      createLive_object.pointStaticInfo,
                      createLive_object.shut,
                      createLive_object.subscribe,
                      createLive_object.unoriginate,
                      createLive_object.unsubscribe,
                      createLive_object.waitTillSynced]
    for function in cL_o_functions:
        print(function.__name__)
        print(function.__self__)
        print(function.__doc__)
        try:
            print(function()) # will fail if inputs are expected
            #print(inspect.getmembers(function))
        except:
            pass
        print("\n")

"""Begin using the functions"""
# Create three separate createLive objects, for sending, subscribing, and both
# - sourceconnection()
# - bothconnection()
# - subscriberconnection()
#
# This is the format for using the connect function, though keywords args are not allowed:
#    createLive_object.connect(asClient=0,asSource=1,Opts=dict())

def script_test1():
    pt_inf = "M100FI.UNIT0@NET0"
    pt=pt_inf
    print("source = eds.createLive()")
    print("source.connect(0,1,dict())")
    print("source.originate(pt_inf)")
    source = eds.createLive()
    source.connect(0,1,dict())
    #print(source.connInfo())
    source.originate(pt_inf)
    print("source.pointDynamicInfo(pt)=")
    print(source.pointDynamicInfo(pt))
    print("source.pointStaticInfo(pt)")
    print(source.pointStaticInfo(pt))
    print(source.connInfo())

    sub = eds.createLive()
    sub.connect(1,0,dict())
    sub.subscribe(pt)
    #print(sub.connInfo())

    both = eds.createLive()
    both.connect(1,1,dict())
    both.subscribe(pt)
    print(both.connInfo())
    #for function in cL_o_functions:
    #    print(inspect.getargspec(function))
    print("\n")
    print(eds.setupLogger.__doc__)
    setupLogger_object = eds.setupLogger("fail")
    setupLogger_object = eds.setupLogger(pt) # fail
    #sL_o_functions = [setupLogger_object
    print("\n")

"""Scipt demonstating the connection functions below,
and adding a second point to the returned objects"""
def script_example2_addmultiplepoints():
    pt = "M100FI.UNIT0@NET0"
    lid = 2307
    source_object = sourceconnection(pt)
    both_object = bothconnection(pt)
    subscriber_object = subscriberconnection(pt)
    pt2 = "FI8001.UNIT0@NET0"
    lid2 = 8527
    source_object.originate(pt2)
    both_object.originate(pt2)
    both_object.subscribe(pt2)
    subscriber_object.subscribe(pt2)

    print("\nsource_object.connInfo(connInfo)")
    print(source_object.connInfo())
    print("\nboth_object.connInfo(connInfo)")
    print(both_object.connInfo())
    print("\nsubscriber_object.connInfo(connInfo)")
    print(subscriber_object.connInfo())
    

"""Live connection generation test functions"""
def sourceconnection(pointname,birth=True, death=False):
    "eds.createLive().connect(asClient=0,asSource=1,Opts=dict())"
    if birth is True:
        source = eds.createLive()
        # Initialize connection to the EDS2 Live server.
        # asClient(Int) if 1 connect as client
        # asSource(Int) if 1 connect as source
        # Opts(Dict) should contain connection parameters.
        source.connect(0,1,dict())
        print("source = eds.createLive()")
        print("source.connect(0,1,dict())")
    # Originate point to start sending point dynamic data
    source.originate(pointname)
    print("source.originate(pointname)")
    print("source.pointDynamicInfo(pointname)=")
    print(source.pointDynamicInfo(pointname))
    print("source.pointStaticInfo(pointname)=")
    print(source.pointStaticInfo(pointname))
    print("source.connInfo()=")
    print(source.connInfo())
    print("source=")
    print(source)
    if death is True:
        # UnOriginate point to stop sending dynamic data
        both.unoriginate(pointname)
        # Close all the connections to EDS2 Live server.
        both.shut(pointname)
    print("\n")
    # return the connection object for variable assignment
    return source 
    
def bothconnection(pointname,birth = True, death=False):
    "eds.createLive().connect(asClient=1,asSource=1,Opts=dict())"
    if birth is True:
        both = eds.createLive()
        # Initialize connection to the EDS2 Live server.
        # asClient(Int) if 1 connect as client
        # asSource(Int) if 1 connect as source
        # Opts(Dict) should contain connection parameters.
        both.connect(1,1,dict())
        print("both = eds.createLive()")
        print("both.connect(1,1,dict())")
    # Originate point to start sending point dynamic data
    both.originate(pointname)
    # Subscribe point to receive dynamic data
    both.subscribe(pointname)
    print("both.originate(pointname)")
    print("both.subscribe(pointname)")
    print("both.pointDynamicInfo(pointname)=")
    print(both.pointDynamicInfo(pointname))
    print("both.pointStaticInfo(pointname)=")
    print(both.pointStaticInfo(pointname))
    print("both.connInfo()=")
    print(both.connInfo())
    print("both=")
    print(both)
    if death is True:
        # UnSubscribe point to stop receiving dynamic data
        both.unsubscribe(pointname)
        # UnOriginate point to stop sending dynamic data
        both.unoriginate(pointname)
        # Close all the connections to EDS2 Live server.
        both.shut(pointname)
    print("\n")
    # return the connection object for variable assignment
    return both

def subscriberconnection(pointname,birth=True,death=False):
    "eds.createLive().connect(asClient=1,asSource=0,Opts=dict())"
    if birth is True:
        # Generate the connection object
        subscriber = eds.createLive() # Generate the connection object
        # Initialize connection to the EDS2 Live server.
        # asClient(Int) if 1 connect as client
        # asSource(Int) if 1 connect as source
        # Opts(Dict) should contain connection parameters.
        subscriber.connect(1,0,dict())
        print("subscriber = eds.createLive()")
        print("subscriber.connect(1,0,dict())")
    # Subscribe point to receive dynamic data
    subscriber.subscribe(pointname)
    print("subscriber.subscribe(pointname)")
    print("subscriber.pointDynamicInfo(pointname)=")
    print(subscriber.pointDynamicInfo(pointname))
    print("subscriber.pointStaticInfo(pointname)=")
    print(subscriber.pointStaticInfo(pointname))
    print("subscriber.connInfo()=")
    print(subscriber.connInfo())
    print("subscriber=")
    print(subscriber)
    if death is True:
        # UnSubscribe point to stop receiving dynamic data
        subscriber.unsubscribe(pointname)
        # Close all the connections to EDS2 Live server.
        subscriber.shut(pointname)
    print("\n")
    # return the connection object for variable assignment
    return subscriber

if __name__ == "__main__":
    basic_exploration()
    exploration()
    #script_test1()
    pt = "M100FI.UNIT0@NET0"
    lid = 2307
    #pt = lid
    s=sourceconnection(pt)
    b=bothconnection(pt)
    c=subscriberconnection(pt) # client
    # script_example2_addmultiplepoints()
    # s.waitTillSynced()

    """Current analysis:
    The connect() function never succeeds,
    and the connection object stays in the 'Connecting' state.
    So, points are never able to be added,
    and only the default dummy point is shown.
    """


    
    
