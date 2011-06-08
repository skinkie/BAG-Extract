import os

try:
    import lxml.etree as ET
except ImportError:
    try:
        import cElementTree as ET
    except ImportError:
        try:
            import elementtree.ElementTree as ET
        except ImportError:
            import xml.etree.ElementTree as ET

def tagVolledigeNS(tag, nsmap):
    sep = tag.split(':')
    return '{%s}%s' % (nsmap[sep[0]], sep[1])

def bestandVerwerkExtractPad(log, pad, bagObjecten, appyield=None):
    verwerkteBestanden = 0
    # Loop door alle bestanden binnen de gekozen directory en verwerk deze
    for (root, subdirectories, files) in os.walk(pad):
        for subdirectoryNaam in subdirectories:
            # Sla de mutatiebestanden over in deze verwerking. Deze zijn
            # herkenbaar aan de aanduiding MUT in de naam.
            if not "MUT" in subdirectoryNaam:
                subdirectory = os.path.join(root, subdirectoryNaam)
                log(subdirectory)
                for xmlFileNaam in os.listdir(subdirectory):
                    if xmlFileNaam == ".":
                        break
                    (naam,extensie) = os.path.splitext(xmlFileNaam)
                    if extensie.upper() == ".XML":
                        xmlFile = os.path.join(subdirectory, xmlFileNaam)
                        log(xmlFileNaam + "...")
                        log.startTimer()
                        
                        try:
                            xml = ET.parse(xmlFile)
                            teller = 0
                            for bagObject in bagObjecten:
                                for xmlObject in xml.iterfind('.//'+tagVolledigeNS(bagObject.tag(), xml.getroot().nsmap)):
                                    bagObject.leesUitXML(xmlObject)
                                    bagObject.voegToeInDatabase()
                                    teller += 1
                                    if appyield is not None:
                                        appyield.Yield(True)
                            log.schrijfTimer("=> %d objecten toegevoegd" %(teller))
                            xml = None
                            verwerkteBestanden += 1
                        except Exception, foutmelding:
                            log("*** FOUT *** Fout in verwerking xml-bestand '%s':\n %s" %(xmlFileNaam, foutmelding))
                            raise
                log("")
        return verwerkteBestanden

def bestandVerwerkMutatiePad(log, pad, appyield=None):
    verwerkteBestanden = 0
    wWPL = 0
    wOPR = 0
    wNUM = 0
    wLIG = 0
    wSTA = 0
    wVBO = 0
    wPND = 0
    nWPL = 0
    nOPR = 0
    nNUM = 0
    nLIG = 0
    nSTA = 0
    nVBO = 0
    nPND = 0
    tellerFout = 0
    # Loop door alle mutatiebestanden binnen de gekozen directory en verwerk deze
    for (root, subdirectories, files) in os.walk(pad):
        for subdirectoryNaam in subdirectories:
            # De mutatiebestanden zijn herkenbaar aan de aanduiding MUT in de naam
            if "MUT" in subdirectoryNaam:
                subdirectory = os.path.join(root, subdirectoryNaam)
                log(subdirectory)
                for xmlFileNaam in os.listdir(subdirectory):
                    if xmlFileNaam == ".":
                        break
                    (naam,extensie) = os.path.splitext(xmlFileNaam)
                    if extensie.upper() == ".XML":
                        xmlFile = os.path.join(subdirectory, xmlFileNaam)
                        log(xmlFileNaam + "...")
                        log.startTimer()
                        
                        try:
                            xml = ET.parse(xmlFile)
                            tellerNieuw  = 0
                            tellerWijzig = 0
                            for xmlMutatie in xml.iterfind(tagVolledigeNS("product_LVC:Mutatie-product", xml.nsmap)):
                                xmlObjectType = xmlMutatie.find(tagVolledigeNS("product_LVC:Mutatie-product", xml.nsmap))
                                if xmlObjectType is not None:
                                    bagObjectOrigineel = bagOBjectWijziging = bagObjectNieuw = getBAGobjectBijType(getText(xmlObjectType))

                                    xmlOrigineel = xmlMutatie.find(tagVolledigeNS("product_LVC:Origineel", xml.nsmap))
                                    xmlWijziging = xmlMutatie.find(tagVolledigeNS("product_LVC:Wijziging", xml.nsmap))
                                    xmlNieuw     = xmlMutatie.find(tagVolledigeNS("product_LVC:Nieuw", xml.nsmap))
                                    if xmlOrigineel is not None and bagObjectOrigineel and xmlWijziging is not None and bagObjectWijziging:
                                        bagObjectOrigineel.leesUitXML(xmlOrigineel.find(tagVolledigeNS(bagObjectOrigineel.tag(), xml.nsmap)))
                                        bagObjectWijziging.leesUitXML(xmlWijziging.find(tagVolledigeNS(bagObjectWijziging.tag(), xml.nsmap)))
                                        bagObjectOrigineel.wijzigInDatabase(bagObjectWijziging)
                                        tellerWijzig += 1
                                        if bagObjectOrigineel.objectType() == "WPL":
                                            wWPL += 1
                                        if bagObjectOrigineel.objectType() == "OPR":
                                            wOPR += 1
                                        if bagObjectOrigineel.objectType() == "NUM":
                                            wNUM += 1
                                        if bagObjectOrigineel.objectType() == "LIG":
                                            wLIG += 1
                                        if bagObjectOrigineel.objectType() == "STA":
                                            wSTA += 1
                                        if bagObjectOrigineel.objectType() == "VBO":
                                            wVBO += 1
                                        if bagObjectOrigineel.objectType() == "PND":
                                            wPND += 1
                                    if xmlNieuw is not None:
                                        bagObjectNieuw.leesUitXML(xmlNieuw.find(tagVolledigeNS(bagObjectNieuw.tag(), xml.nsmap)))
                                        bagObjectNieuw.voegToeInDatabase()
                                        #bagObjectNieuw.controleerLevenscyclus(toonResultaat=True)
                                        #if not bagObjectNieuw.levenscyclusCorrect:
                                        #    tellerFout += 1
                                        tellerNieuw += 1
                                        if bagObjectNieuw.objectType() == "WPL":
                                            nWPL += 1
                                        if bagObjectNieuw.objectType() == "OPR":
                                            nOPR += 1
                                        if bagObjectNieuw.objectType() == "NUM":
                                            nNUM += 1
                                        if bagObjectNieuw.objectType() == "LIG":
                                            nLIG += 1
                                        if bagObjectNieuw.objectType() == "STA":
                                            nSTA += 1
                                        if bagObjectNieuw.objectType() == "VBO":
                                            nVBO += 1
                                        if bagObjectNieuw.objectType() == "PND":
                                            nPND += 1
                                if appyield is not None:
                                    appyield.Yield(True)
                            log.schrijfTimer("=> %d objecten toegevoegd, %d objecten gewijzigd" %(tellerNieuw, tellerWijzig))
                            xml = None
                            verwerkteBestanden += 1
                        except Exception, foutmelding:
                            log("*** FOUT *** Fout in verwerking xml-bestand '%s':\n %s" %(xmlFileNaam, foutmelding))
                log("")

def dbInit(bagObjecten):
    for bagObject in bagObjecten:
        bagObject.maakTabel()
        bagObject.maakIndex()
        bagObject.maakViews()
    
def dbMaakIndex(bagObjecten):
    for bagObject in bagObjecten:
        bagObject.maakIndex()

