#------------------------------------------------------------------------------
# Naam:         libBAG.py
# Omschrijving: Classes voor de BAG-objecten
#
# Per BAG-objecttype (woonplaats, openbareruimte, nummeraanduiding,
# ligplaats, standplaats, verblijfsobject, pand) is er een aparte class
# met functionaliteit voor het lezen uit XML, het schrijven in de database
# en het lezen uit de database. Ook bevat elke BAG-objectype-class functies
# voor het initialiseren van de database (maken van tabellen, indexen en
# views).
# De BAG-objecttype-classes zijn afgeleid van de basisclass BAGobject.
# Hierin is een BAG-object een verzameling van BAG-attributen met elk
# hun eigen eigenschappen.
#
# Auteur:       Matthijs van der Deijl
#
# Versie:       1.7
#               - objecttype LPL vervangen door LIG
#               - objecttype SPL vervangen door STA
# Datum:        11 maart 2011
#
# Versie:       1.6
#               - Veldlengte voor tekstwaarde van geometrie verhoogt naar 1000000
# Datum:        8 oktober 2010
#
# Versie:       1.3
#               - Tag voor VerkorteOpenbareRuimteNaam verbeterd
#               - GeomFromText vervangen door GeomFromEWKT
#                 (dit voorkomt Warnings in de database logging)
#               - Functie controleerTabel toegevoegd
#               - Primaire index op tabel uniek gemaakt
#               - Ophalen van waardes uit database met leestekens verbeterd
# Datum:        28 december 2009
#
# Versie:       1.2
# Datum:        24 november 2009
#
# Ministerie van Volkshuisvesting, Ruimtelijke Ordening en Milieubeheer
#------------------------------------------------------------------------------
from libLog import *
from libDatabase import *

# Geef de waarde van een textnode in XML
def getText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc

# Geef de waardes van alle elementen met de gegeven tag binnen de XML (parent).
# De tag kan een samengestelde tag zijn opgebouwd uit verschillende niveaus gescheiden door een '/'.
def getValues(parent, tag):
    data = []
    # Splits de tag bij het eerste voorkomen van '/' met behulp van de partition-functie
    tags = tag.partition("/")
    for node in parent.getElementsByTagName(tags[0]):
        # getElementsByTagName geeft alle elementen met die tag die ergens onder de parent hangen.
        # We gebruiken hier echter alleen die elementen die rechtstreeks onder de parent hangen.
        # Immers als we op zoek zijn naar de identificatie van een verblijfsobject dan willen we niet de
        # identificaties van gerelateerde objecten van dat verblijfsobject hebben.
        # Daarom controleren we dat de tag van de parent van de gevonden node, gelijk is aan de tag van de parent
        if node.parentNode.tagName == parent.tagName:    
            if tags[1] == "/":
                data.extend(getValues(node, tags[2]))
            else:
                data.append(getText(node.childNodes))
    return data        

# Geef de waarde van het eerste element met de gegeven tag binnen de XML (parent). Als er geen eerste
# element gevonden wordt, is het resultaat een lege string.
def getValue(parent, tag):
    values = getValues(parent, tag)
    if len(values) > 0:
        return values[0]
    else:
        return ""


#--------------------------------------------------------------------------------------------------------
# Class         BAGattribuut
# Omschrijving  Bevat binnen een BAGobject 1 attribuut met zijn waarde
# Bevat         - tag
#               - naam
#               - waarde
#--------------------------------------------------------------------------------------------------------
class BAGattribuut:
    # Constructor
    def __init__(self, lengte, naam, tag):
        self._lengte  = lengte
        self._naam    = naam
        self._tag     = tag
        self._waarde  = ""

    # Attribuut lengte
    def lengte(self):
        return self._lengte

    # Attribuut naam
    def naam(self):
        return self._naam

    # Attribuut tag
    def tag(self):
        return self._tag

    # Attribuut sqltype. Deze method kan worden overloaded
    def sqltype(self):
        return "VARCHAR(%d)" % (self._lengte)
    
    # Attribuut waarde. Deze method kan worden overloaded
    def waarde(self):
        return self._waarde

    # Wijzig de waarde.
    def setWaarde(self, waarde):
        self._waarde = waarde
        
    # Geef aan dat het attribuut enkelvoudig is (maar 1 waarde heeft). Deze method kan worden overloaded.
    def enkelvoudig(self):
        return True
    
    # Initialiseer database
    def sqlinit(self):
        return ''

    # Initialisatie vanuit XML
    def leesUitXML(self, xml):
        self._waarde = getValue(xml, self._tag)
        # Door een bug in BAG Extract bevat de einddatum een fictieve waarde 31-12-2299 in het geval dat
        # deze leeg hoort te zijn. Om dit te omzeilen, controleren we hier de waarde en maken deze zo nodig
        # zelf leeg.
        # if self._naam == "einddatumTijdvakGeldigheid" and self._waarde == "2299123100000000":
        #    self._waarde = None

    # Print informatie over het attribuut op het scherm
    def schrijf(self):
        print "- %-27s: %s" %(self._naam, self._waarde)

#--------------------------------------------------------------------------------------------------------
# Class         BAGenumAttribuut
# Afgeleid van  BAGattribuut
# Omschrijving  Bevat een of meerdere waarden binnen een restrictie 
#--------------------------------------------------------------------------------------------------------
class BAGenumAttribuut(BAGattribuut):
    # Constructor
    def __init__(self, lijst, naam, tag):
        self._lijst   = lijst
        self._lengte  = len(max(lijst, key=len))
        self._naam    = naam
        self._tag     = tag
        self._waarde  = ""

    # Attribuut sqltype. Deze method kan worden overloaded
    def sqltype(self):
        return self._naam

    # Initialiseer database
    def sqlinit(self):
        return "CREATE TYPE %s AS ENUM ('%s');" % (self._naam, "', '".join(self._lijst))

#--------------------------------------------------------------------------------------------------------
# Class         BAGnumeriekAttribuut
# Afgeleid van  BAGattribuut
# Omschrijving  Bevat een numerieke waarde 
#--------------------------------------------------------------------------------------------------------
class BAGnumeriekAttribuut(BAGattribuut):
    # Attribuut sqltype. Deze method kan worden overloaded
    def sqltype(self):
        return "NUMERIC(%d)" % (self._lengte)

#--------------------------------------------------------------------------------------------------------
# Class         BAGintegerAttribuut
# Afgeleid van  BAGattribuut
# Omschrijving  Bevat een numerieke waarde 
#--------------------------------------------------------------------------------------------------------
class BAGintegerAttribuut(BAGattribuut):
    # Constructor
    def __init__(self, naam, tag):
        self._naam    = naam
        self._tag     = tag
        self._waarde  = None

    # Attribuut sqltype. Deze method kan worden overloaded
    def sqltype(self):
        return "INTEGER"


#--------------------------------------------------------------------------------------------------------
# Class         BAGdatumAttribuut
# Afgeleid van  BAGattribuut
# Omschrijving  Bevat een waarheid attribuut
#--------------------------------------------------------------------------------------------------------
class BAGbooleanAttribuut(BAGattribuut):
    # Constructor
    def __init__(self, naam, tag):
        self._naam    = naam
        self._tag     = tag
        self._waarde  = None

    # Attribuut sqltype. Deze method kan worden overloaded
    def sqltype(self):
        return "BOOLEAN"
    
    # Initialisatie vanuit XML
    def leesUitXML(self, xml):
        self._waarde = getValue(xml, self._tag)
        if self._waarde == 'N':
            self._waarde = 'FALSE'
        elif self._waarde == 'J':
            self._waarde = 'TRUE'
        elif self._waarde == '':
            self._waarde = None
        else:
            print 'Onverwacht: %s'%(self._waarde)


#--------------------------------------------------------------------------------------------------------
# Class         BAGdateAttribuut
# Afgeleid van  BAGattribuut
# Omschrijving  Bevat een waarheid attribuut
#--------------------------------------------------------------------------------------------------------
class BAGdateAttribuut(BAGattribuut):
    # Constructor
    def __init__(self, naam, tag):
        self._naam    = naam
        self._tag     = tag
        self._waarde  = None

    # Attribuut sqltype. Deze method kan worden overloaded
    def sqltype(self):
        return "DATE"
    
    # Initialisatie vanuit XML
    def leesUitXML(self, xml):
        self._waarde = getValue(xml, self._tag)
        if self._waarde == '':
            self._waarde = None

#--------------------------------------------------------------------------------------------------------
# Class         BAGdatetimeAttribuut
# Afgeleid van  BAGattribuut
# Omschrijving  Bevat een waarheid attribuut
#--------------------------------------------------------------------------------------------------------
class BAGdatetimeAttribuut(BAGattribuut):
    # Constructor
    def __init__(self, naam, tag):
        self._naam    = naam
        self._tag     = tag
        self._waarde  = None

    # Attribuut sqltype. Deze method kan worden overloaded
    def sqltype(self):
        return "TIMESTAMP WITHOUT TIME ZONE"
    
    # Initialisatie vanuit XML
    def leesUitXML(self, xml):
        self._waarde = getValue(xml, self._tag)
        if self._waarde != '':
            jaar = self._waarde[0:4]
            maand = self._waarde[4:6]
            dag = self._waarde[6:8]
            uur = self._waarde[8:10]
            minuut = self._waarde[10:12]
            seconden = self._waarde[12:14]
            msec = self._waarde[14:16]

            if jaar != '2299':
                self._waarde = '%s%s%s %s%s%s'%(jaar, maand, dag, uur, minuut, seconden)
            else:
                print 'Onverwacht: %s'%(self._waarde)


#--------------------------------------------------------------------------------------------------------
# Class         BAGgeoAttribuut
# Afgeleid van  BAGattribuut
# Omschrijving  Bevat een geometrie attribuut 
#--------------------------------------------------------------------------------------------------------
class BAGgeoAttribuut(BAGattribuut):
    # Attribuut dimensie
    def dimensie(self):
        return ""

    # Attribuut soort
    def soort(self):
        return ""

#--------------------------------------------------------------------------------------------------------
# Class         BAGpoint
# Afgeleid van  BAGgeoAttribuut
# Omschrijving  Bevat een Puntgeometrie attribuut (geometrie van een verblijfsobject)
#--------------------------------------------------------------------------------------------------------
class BAGpoint(BAGgeoAttribuut):
    # Attribuut dimensie
    def dimensie(self):
        return "3"

    # Attribuut soort
    def soort(self):
        return "POINT"
    
    # Initialisatie vanuit XML
    def leesUitXML(self, xml):
        try:
            pos       = ""
            teller    = 0
            geometrie = xml.getElementsByTagName(self._tag)[0]
            point     = geometrie.getElementsByTagName("gml:Point")[0]            
            for na in point.getElementsByTagName("gml:pos"):
                teller += 1
                pos = pos + na.firstChild.nodeValue + ","
              
            if teller > 0:
                pos = pos[:-1]
            self._waarde = "POINT(" + pos + ")"
        except:
            self._waarde = "POINT(0 0 0)"  
        
#--------------------------------------------------------------------------------------------------------
# Class         BAGpolygoon
# Afgeleid van  BAGgeoAttribuut
# Omschrijving  Bevat een Polygoongeometrie attribuut (pand, ligplaats, standplaats of woonplaats)
#               De dimensie (2D of 3D) is variabel.
#--------------------------------------------------------------------------------------------------------
class BAGpolygoon(BAGgeoAttribuut):
    # Constructor
    def __init__(self, dimensie, lengte, naam, tag):
        self._dimensie = dimensie
        BAGgeoAttribuut.__init__(self, lengte, naam, tag)
        
    # Attribuut dimensie
    def dimensie(self):
        return self._dimensie

    # Attribuut soort
    def soort(self):
        return "POLYGON"

    # Converteer een posList uit de XML-string naar een WKT-string. De XML-string bevat een opsomming
    # van coordinaten waarbij alle coordinaten en punten zijn gescheiden door een spatie. In de WKT-string
    # worden de punten gescheiden door een komma en de coordinaten van een punt gescheiden door een spatie.
    def _leesXMLposList(self, xml):
        wktPosList = ""
        puntTeller = 0
        for xmlPosList in xml.getElementsByTagName("gml:posList"):
            for coordinaat in xmlPosList.firstChild.nodeValue.split(" "):
                puntTeller += 1
                if puntTeller > self.dimensie():
                    wktPosList += ","
                    puntTeller  = 1
                wktPosList += " " + coordinaat
        return wktPosList

    # Converteer een polygoon uit de XML-string naar een WKT-string.
    # Een polygoon bestaat uit een buitenring en 0 of meerdere binnenringen (gaten).
    def _leesXMLpolygoon(self, xmlPolygoon):
        xmlExterior = xmlPolygoon.getElementsByTagName("gml:exterior")[0]
        wktExterior = "(" + self._leesXMLposList(xmlExterior) + ")"
                    
        wktInteriors = ""
        for xmlInterior in xmlPolygoon.getElementsByTagName("gml:interior"):
            wktInteriors += ",(" + self._leesXMLposList(xmlInterior) + ")"

        return "(" + wktExterior + wktInteriors + ")"    
        
    # Initialisatie vanuit XML
    def leesUitXML(self, xml):
        xmlGeometrie = xml.getElementsByTagName(self._tag)[0]
        xmlPolygoon  = xmlGeometrie.getElementsByTagName("gml:Polygon")[0]
        self._waarde = "POLYGON" + self._leesXMLpolygoon(xmlPolygoon)

#--------------------------------------------------------------------------------------------------------
# Class         BAGmultiPolygoon
# Afgeleid van  BAGpolygoon
# Omschrijving  Bevat een MultiPolygoongeometrie attribuut (woonplaats)
#--------------------------------------------------------------------------------------------------------
class BAGmultiPolygoon(BAGpolygoon):
    # Attribuut soort
    def soort(self):
        return "MULTIPOLYGON"

    # Initialisatie vanuit XML
    def leesUitXML(self, xml):
        wktGeometrie = ""
        xmlGeometrie = xml.getElementsByTagName(self._tag)[0]
        for xmlPolygoon in xmlGeometrie.getElementsByTagName("gml:Polygon"):
            if wktGeometrie <> "":
                wktGeometrie += ","
            wktGeometrie += self._leesXMLpolygoon(xmlPolygoon)
        self._waarde = "MULTIPOLYGON(" + wktGeometrie + ")"
            
#--------------------------------------------------------------------------------------------------------
# Class         BAGrelatieAttribuut
# Afgeleid van  BAGattribuut
# Omschrijving  Bevat een attribuut dat meer dan 1 waarde kan hebben.
#--------------------------------------------------------------------------------------------------------
class BAGrelatieAttribuut(BAGattribuut):
    # Constructor
    def __init__(self, relatieNaam, lengte, naam, tag):
        BAGattribuut.__init__(self, lengte, naam, tag)
        self._relatieNaam = relatieNaam
        self._waarde = []

    # Attribuut relatienaam
    def relatieNaam(self):
        return self._relatieNaam
    
    # Attribuut waarde. Deze waarde overload de waarde in de basisclass 
    def waarde(self):
        return self._waarde

    # Wijzig de waarde.
    def setWaarde(self, waarde):
        self._waarde.append(waarde)

    # Geef aan dat het attribuut niet enkelvoudig is (meerdere waardes kan hebben). 
    def enkelvoudig(self):
        return False

    # Initialisatie vanuit XML
    def leesUitXML(self, xml): 
        self._waarde = getValues(xml, self.tag())

    # Print informatie over het attribuut op het scherm
    def schrijf(self):
        first = True
        for waarde in self._waarde:
            if first:
                print "- %-27s: %s" %(self.naam(), waarde)
                first = False
            else:
                print "- %-27s  %s" %("", waarde)

#--------------------------------------------------------------------------------------------------------
# Class         BAGrelatieNumeriekAttribuut
# Afgeleid van  BAGrelatieAttribuut
# Omschrijving  Bevat een nummeriek attribuut dat meer dan 1 waarde kan hebben.
#--------------------------------------------------------------------------------------------------------
class BAGrelatieNumeriekAttribuut(BAGrelatieAttribuut):
    def sqltype(self):
        return "NUMERIC(%d)" % (self._lengte)

#--------------------------------------------------------------------------------------------------------
# Class         BAGobject
# Omschrijving  Basisclass voor de 7 types BAG-objecten. Deze class bevat de generieke attributen die
#               in al deze types BAG-objecten voorkomen.
#--------------------------------------------------------------------------------------------------------
class BAGobject:
    # Constructor
    def __init__(self):
        self.identificatie               = BAGnumeriekAttribuut(16, "identificatie", "bag_LVC:identificatie")
        self.aanduidingRecordInactief    = BAGbooleanAttribuut("aanduidingRecordInactief", "bag_LVC:aanduidingRecordInactief")
        self.aanduidingRecordCorrectie   = BAGintegerAttribuut("aanduidingRecordCorrectie", "bag_LVC:aanduidingRecordCorrectie")
        self.officieel                   = BAGbooleanAttribuut("officieel", "bag_LVC:officieel")
        self.inOnderzoek                 = BAGbooleanAttribuut("inOnderzoek", "bag_LVC:inOnderzoek")
        self.begindatumTijdvakGeldigheid = BAGdatetimeAttribuut("begindatumTijdvakGeldigheid", "bag_LVC:tijdvakgeldigheid/bagtype:begindatumTijdvakGeldigheid")
        self.einddatumTijdvakGeldigheid  = BAGdatetimeAttribuut("einddatumTijdvakGeldigheid", "bag_LVC:tijdvakgeldigheid/bagtype:einddatumTijdvakGeldigheid")
        self.documentnummer              = BAGattribuut(20, "documentnummer", "bag_LVC:bron/bagtype:documentnummer")
        self.documentdatum               = BAGdateAttribuut("documentdatum", "bag_LVC:bron/bagtype:documentdatum")

        self.attributen = []
        self.attributen.append(self.identificatie)
        self.attributen.append(self.aanduidingRecordInactief)
        self.attributen.append(self.aanduidingRecordCorrectie)
        self.attributen.append(self.officieel)
        self.attributen.append(self.inOnderzoek)
        self.attributen.append(self.begindatumTijdvakGeldigheid)
        self.attributen.append(self.einddatumTijdvakGeldigheid)
        self.attributen.append(self.documentnummer)
        self.attributen.append(self.documentdatum)       
    
    # Geef de XML-tag bij het type BAG-object.
    # Deze method moet worden overloaded in de afgeleide classes
    def tag(self):
        return ""

    # Geef de naam bij het type BAG-object.
    # Deze method moet worden overloaded in de afgeleide classes
    def naam(self):
        return ""

    # Geef het objecttype bij het type BAG-object.
    # Deze method moet worden overloaded in de afgeleide classes
    def objectType(self):
        return ""
    
    # Geef aan of het object een geometrie heeft.
    # Deze method kan worden overloaded in de afgeleide classes
    def heeftGeometrie(self):
        return False

    # Geef het geometrie attribuut van het object.
    # Deze method kan worden overloaded in de afgeleide classes
    def geometrie(self):
        return ""
    
    # Initialisatie vanuit XML
    def leesUitXML(self, xml):
        for attribuut in self.attributen:
            attribuut.leesUitXML(xml)

    # Retourneer het attribuut met de gegeven naam
    def attribuut(self, naam):
        for attribuut in self.attributen:
            if attribuut.naam == naam:
                return attribuut

    # Retourneer een adres van het object
    # Deze method moet worden overloaded in de afgeleide classes
    def adres(self):
        return ""

    # Retourneer een omschrijving van het object, bestaande uit de identificatie en het adres
    def omschrijving(self):
        return "%s %s - %s" %(self.objectType(), self.identificatie.waarde(), self.adres())
    
    # Maak een tabel in de database
    def maakTabel(self):
        sql = ""
        for attribuut in self.attributen:
            sqlinit = attribuut.sqlinit()
            if sqlinit != '':
                database.execute(sqlinit)

            if attribuut.enkelvoudig() and attribuut.naam()[0] != '_':
                if sql == "":
                    sql  = "CREATE TABLE " + self.naam() + " (" + attribuut.naam() + " " + attribuut.sqltype()
                else:
                    sql += "," + attribuut.naam() + " " + attribuut.sqltype()
        sql += ",begindatum DATE"
        sql += ",einddatum  DATE"
        sql += ")"
        if self.heeftGeometrie():
            sql += " WITH (OIDS=true)"
       
        database.maakTabel(self.naam(), sql)

        if self.heeftGeometrie():
            inhoud = (self.naam().lower(), self.geometrie().soort(), self.geometrie().dimensie(),)
            database.execute("SELECT AddGeometryColumn('public', %s, 'geometrie', 28992, %s, %s)", inhoud)

    # Controleer of een tabel bestaat in de database
    def controleerTabel(self):
        return database.controleerTabel(self.naam())
    
    # Maak voor een relatie een tabel in de database
    def maakTabelRelatie(self, relatie):
        sql  = "CREATE TABLE " + relatie.relatieNaam() + " " 
        sql += "(identificatie               NUMERIC(16,0)"
        sql += ",aanduidingrecordinactief    BOOLEAN"
        sql += ",aanduidingrecordcorrectie   INTEGER"
        sql += ",begindatumtijdvakgeldigheid TIMESTAMP WITHOUT TIME ZONE"
        sql += "," + relatie.naam() + " " + relatie.sqltype()
        sql += ")"
        database.maakTabel(relatie.relatieNaam(), sql)

    # Controleer of een tabel voor een relatie bestaat in de database
    def controleerTabelRelatie(self, relatie):
        return database.controleerTabel(relatie.relatieNaam())

    # Maak een index op de tabel voor het objecttype in de database.
    def maakIndex(self):
        sql  = "CREATE UNIQUE INDEX " + self.naam() + "key"
        sql += " ON " + self.naam() + " "
        sql += "(identificatie"
        sql += ",aanduidingrecordinactief"
        sql += ",aanduidingrecordcorrectie"
        sql += ",begindatumtijdvakgeldigheid"
        sql += ")"
        database.maakIndex(self.naam() + "key", sql)

        if self.heeftGeometrie():
            sql  = "CREATE UNIQUE INDEX " + self.naam() + "OID"
            sql += " ON " + self.naam() + " (oid)"
            database.maakIndex(self.naam() + "OID", sql)
            
            sql  = "CREATE INDEX " + self.naam() + "GIST"
            sql += " ON " + self.naam() + " USING GIST(geometrie)"
            database.maakIndex(self.naam() + "GIST", sql)
        
    # Maak een index op een relatie op het objecttype in de database
    def maakIndexRelatie(self, relatie):
        sql  = "CREATE INDEX " + relatie.relatieNaam() + "key"
        sql += " ON " + relatie.relatieNaam() + " "
        sql += "(identificatie"
        sql += ",aanduidingrecordinactief"
        sql += ",aanduidingrecordcorrectie"
        sql += ",begindatumtijdvakgeldigheid"
        sql += "," + relatie.naam()
        sql += ")"
        database.maakIndex(relatie.relatieNaam() + "key", sql)

    # Maak een view om alleen actieve, actuele voorkomens te selecteren
    def maakViewActueel(self):
        sql  = "CREATE VIEW " + self.naam() + "actueel" 
        sql += " AS SELECT "
        if self.heeftGeometrie():
            sql += self.naam() + ".oid::bigint as oid," 
        sql += " * FROM " + self.naam()
        sql += " WHERE begindatum <= current_date"
        sql += "   AND einddatum  >= current_date"
        sql += "   AND aanduidingrecordinactief = FALSE"
        database.maakView(self.naam() + "actueel", sql)

    # Maak een view op de opgegeven tabel om alleen actieve, actuele voorkomens te selecteren
    # welke bovendien niet zijn ingetrokken, gesloopt enz.
    def maakViewActueelBestaand(self, statusveld, status1, status2):
        sql  = "CREATE VIEW " + self.naam() + "actueelBestaand"
        sql += " AS SELECT "
        if self.heeftGeometrie():
            sql += self.naam() + ".oid::bigint as oid," 
        sql += " * FROM " + self.naam()
        sql += " WHERE begindatum <= current_date"
        sql += "   AND einddatum  >= current_date"
        sql += "   AND aanduidingrecordinactief = FALSE"
        sql += "   AND " + statusveld + " <> '" + status1 + "'" 
        if status2 <> "":
            sql += "   AND " + statusveld + " <> '" + status2 + "'" 
        database.maakView(self.naam() + "actueelBestaand", sql)

    # Voeg het object toe in de database        
    def voegToeInDatabase(self):
        velden  = ""
        waardes = ""
        inhoud  = []
        for attribuut in self.attributen:
            if attribuut.enkelvoudig() and attribuut.naam()[0] != '_':
                if velden == "":
                    velden  = "(" + attribuut.naam()
                    waardes = "(%s" 
                else:
                    velden  += "," + attribuut.naam()
                    waardes += ", %s"
                if attribuut.waarde() == '':
                    inhoud.append(None)
                else:
                    inhoud.append(attribuut.waarde())
        if self.heeftGeometrie():
            velden  += ",geometrie"
            waardes += ",GeomFromEWKT(%s)"
            inhoud.append('SRID=28992;'+self.geometrie().waarde())
        velden  += ",begindatum,einddatum)"
        waardes += ", %s"
        waardes += ", %s)"
        inhoud.append(database.datum(self.begindatumTijdvakGeldigheid.waarde()))
        inhoud.append(database.datum(self.einddatumTijdvakGeldigheid.waarde()))
        sql = "INSERT INTO " + self.naam() + " " + velden + " VALUES " + waardes
        database.insert(sql, tuple(inhoud), self.identificatie.waarde(),)

        for attribuut in self.attributen:
            if not attribuut.enkelvoudig() and attribuut.naam()[0] != '_':
                for waarde in attribuut.waarde():
                    sql  = "INSERT INTO " + attribuut.relatieNaam() + " "
                    sql += "(identificatie"
                    sql += ",aanduidingrecordinactief"
                    sql += ",aanduidingrecordcorrectie"
                    sql += ",begindatumtijdvakgeldigheid"
                    sql += "," + attribuut.naam()
                    sql += ") VALUES (%s, %s, %s, %s, %s)"
                    inhoud = (self.identificatie.waarde(), \
                              self.aanduidingRecordInactief.waarde(), \
                              self.aanduidingRecordCorrectie.waarde(), \
                              self.begindatumTijdvakGeldigheid.waarde(), \
                              waarde,)
                    database.insert(sql, inhoud, self.identificatie.waarde())

    # Update het object in de database.
    # Alleen de volgende attributen kunnen hierbij wijzigen
    #        - einddatumTijdvakGeldigheid (+ einddatum)
    #        - aanduidingRecordInactief
    #        - aanduidingRecordCorrectie
    def wijzigInDatabase(self, wijziging):
        sql  = "UPDATE " + self.naam() 
        sql += "   SET einddatumtijdvakgeldigheid  = %s"
        sql += "     , einddatum                   = %s"
        sql += "     , aanduidingrecordinactief    = %s"
        sql += "     , aanduidingrecordcorrectie   = %s"
        sql += " WHERE identificatie               = %s"
        sql += "   AND aanduidingrecordinactief    = %s"
        sql += "   AND aanduidingrecordcorrectie   = %s"
        sql += "   AND begindatumtijdvakgeldigheid = %s"
        inhoud = (wijziging.einddatumTijdvakGeldigheid.waarde(), \
                  database.datum(wijziging.einddatumTijdvakGeldigheid.waarde()), \
                  wijziging.aanduidingRecordInactief.waarde(), \
                  wijziging.aanduidingRecordCorrectie.waarde(), \
                  self.identificatie.waarde(), \
                  self.aanduidingRecordInactief.waarde(), \
                  self.aanduidingRecordCorrectie.waarde(), \
                  self.begindatumTijdvakGeldigheid.waarde(),)
        database.execute(sql, inhoud)
        if database.cursor.rowcount == 0:
            log("Waarschuwing: wijziging op niet bestaand voorkomen van " + self.naam() + " " + self.identificatie.waarde() + " niet uitgevoerd.") 

        for attribuut in self.attributen:
            if not attribuut.enkelvoudig():    
                # Update een relatie van het object in de database.
                # Alleen de volgende attributen kunnen hierbij wijzigen
                #        - aanduidingRecordInactief
                #        - aanduidingRecordCorrectie
                sql  = "UPDATE " + attribuut.relatieNaam() 
                sql += "   SET aanduidingrecordinactief    = %s"
                sql += "     , aanduidingrecordcorrectie   = %s"
                sql += " WHERE identificatie               = %s"
                sql += "   AND aanduidingrecordinactief    = %s"
                sql += "   AND aanduidingrecordcorrectie   = %s"
                sql += "   AND begindatumtijdvakgeldigheid = %s"
                inhoud = (wijziging.aanduidingRecordInactief.waarde(), \
                          wijziging.aanduidingRecordCorrectie.waarde(), \
                          self.identificatie.waarde(), \
                          self.aanduidingRecordInactief.waarde(), \
                          self.aanduidingRecordCorrectie.waarde(), \
                          self.begindatumTijdvakGeldigheid.waarde(),)
                database.execute(sql, inhoud)

    # Initaliseer het object vanuit de database op basis van de sleutelvelden identificatie,
    # begindatum tijdvak geldigheid, aanduiding record inactief en aanduiding record correctie
    def leesUitDatabase(self):
        sql = ""
        for attribuut in self.attributen:
            if attribuut.enkelvoudig():
                if sql == "":
                    sql = "SELECT " + attribuut.naam()
                else:
                    sql += "," + attribuut.naam()
        sql += "  FROM " + self.naam()
        sql += " WHERE identificatie               = %s"
        sql += "   AND begindatumTijdvakGeldigheid = %s"
        sql += "   AND aanduidingRecordInactief    = %s"
        sql += "   AND aanduidingRecordCorrectie   = %s"
        inhoud = (self.identificatie.waarde(), \
                  self.begindatumTijdvakGeldigheid.waarde(), \
                  self.aanduidingRecordInactief.waarde(), \
                  self.aanduidingRecordCorrectie.waarde(),)
        database.cursor.execute(sql, inhoud)
        if database.cursor.rowcount >= 1:
            rows = database.cursor.fetchall()
            i = 0
            for attribuut in self.attributen:
                if attribuut.enkelvoudig():
                    attribuut.setWaarde(unicode(rows[0][i],"utf-8"))
                    i += 1
        
        for attribuut in self.attributen:
            if not attribuut.enkelvoudig():
                sql  = "SELECT " + attribuut.naam()
                sql += " FROM " + attribuut.relatieNaam()
                sql += " WHERE identificatie               = %s"
                sql += "   AND begindatumTijdvakGeldigheid = %s"
                sql += "   AND aanduidingRecordInactief    = %s"
                sql += "   AND aanduidingRecordCorrectie   = %s"
                inhoud = (self.identificatie.waarde(), \
                          self.begindatumTijdvakGeldigheid.waarde(), \
                          self.aanduidingRecordInactief.waarde(), \
                          self.aanduidingRecordCorrectie.waarde(),)
                database.cursor.execute(sql, inhoud)
                rows = database.cursor.fetchall()
                for row in rows:
                    attribuut.setWaarde(row[0])

    # Geef het actuele voorkomen van het object, geselecteerd uit de database op basis van
    # de identificatie
    def leesActueelVoorkomenUitDatabase(self):
        sql  = "SELECT begindatumTijdvakGeldigheid"
        sql += "     , aanduidingRecordInactief"
        sql += "     , aanduidingRecordCorrectie"
        sql += " FROM " + self.naam() + "actueel"
        sql += " WHERE identificatie = %s"
        inhoud = (self.identificatie.waarde(),)
        database.cursor.execute(sql, inhoud)
        rows = database.cursor.fetchall()
        if len(rows) == 0:
            return False
        else:
            self.begindatumTijdvakGeldigheid.setWaarde(rows[0][0])
            self.aanduidingRecordInactief.setWaarde(rows[0][1])
            self.aanduidingRecordCorrectie.setWaarde(rows[0][2])
            self.leesUitDatabase()
            return True
               
    # Geef een lijst met alle voorkomens van het object, geselecteerd uit de database
    def getLevenscyclus(self):
        # Initialiseer self met het actuele voorkomen
        self.leesActueelVoorkomenUitDatabase()
        objs = []

        sql  = "SELECT begindatumTijdvakGeldigheid"
        sql += "     , aanduidingRecordInactief"
        sql += "     , aanduidingRecordCorrectie"
        sql += " FROM " + self.naam()
        sql += " WHERE identificatie = %s"
        sql += " ORDER BY begindatumTijdvakGeldigheid, aanduidingRecordCorrectie"
        inhoud = (self.identificatie.waarde(),)
        database.cursor.execute(sql, inhoud)
        rows = database.cursor.fetchall()
        for row in rows:
            obj = getBAGobjectBijIdentificatie(self.identificatie.waarde())
            obj.begindatumTijdvakGeldigheid.setWaarde(row[0])
            obj.aanduidingRecordInactief.setWaarde(row[1])
            obj.aanduidingRecordCorrectie.setWaarde(row[2])
            obj.leesUitDatabase()
            objs.append(obj)
        return objs

    # Controleer de levenscyclus van het object. Hierbij wordt uitsluitend gekeken naar de actieve voorkomens.
    # Deze actieve voorkomens moeten een aaneengesloten tijdlijn beschrijven dus zonder gaten en zonder overlap tussen
    # de opvolgende voorkomens. 
    def controleerLevenscyclus(self, toonResultaat):
        objs = self.getLevenscyclus()

        self.levenscyclusCorrect = True
        laatsteActieve = -1
        i = 0
        while i < len(objs):
            objs[i].opmerking = ""
            if objs[i].aanduidingRecordInactief.waarde() == "N":
                if laatsteActieve <> -1:
                    if objs[laatsteActieve].einddatumTijdvakGeldigheid.waarde() <> objs[i].begindatumTijdvakGeldigheid.waarde():
                        if objs[laatsteActieve].einddatumTijdvakGeldigheid.waarde() == "":
                            self.levenscyclusCorrect = False
                            objs[laatsteActieve].opmerking = "Voorkomen heeft geen einddatum maar wel opvolgende voorkomens"
                        elif objs[laatsteActieve].einddatumTijdvakGeldigheid.waarde() < objs[i].begindatumTijdvakGeldigheid.waarde():
                            self.levenscyclusCorrect = False
                            objs[i].opmerking = "Voorkomen sluit niet aan op einddatum %s van voorgaande voorkomen" %(objs[laatsteActieve].einddatumTijdvakGeldigheid.waarde())
                        elif objs[laatsteActieve].einddatumTijdvakGeldigheid.waarde() > objs[i].begindatumTijdvakGeldigheid.waarde():
                            self.levenscyclusCorrect = False
                            objs[i].opmerking = "Voorkomen overlapt over de einddatum %s van voorgaande voorkomen" %(objs[laatsteActieve].einddatumTijdvakGeldigheid.waarde())
                laatsteActieve = i
            i += 1

        if laatsteActieve <> -1:
            if objs[laatsteActieve].einddatumTijdvakGeldigheid.waarde() <> "":
                self.levenscyclusCorrect = False
                objs[laatsteActieve].opmerking = "Laatste voorkomen heeft geen lege einddatum geldigheid"

        if not self.levenscyclusCorrect and toonResultaat:
            log("Fout in de levenscyclus van " + self.naam() + " " + self.identificatie.waarde())
            log("  Actieve voorkomens:")
            log("    Begindatum       Einddatum        Opmerking")
            for obj in objs:
                if obj.aanduidingRecordInactief.waarde() == "N":
                    log("    %16s %16s %s" %(obj.begindatumTijdvakGeldigheid.waarde(),
                                             obj.einddatumTijdvakGeldigheid.waarde(),
                                             obj.opmerking))
        return objs
            
    # Print informatie over het object op het scherm
    def schrijf(self):
        print "*** %s ***" %(self.naam())
        for attribuut in self.attributen:
            attribuut.schrijf()

#--------------------------------------------------------------------------------------------------------
# Class         Woonplaats
# Afgeleid van  BAGobject
# Omschrijving  Class voor het BAG-objecttype Woonplaats.
#--------------------------------------------------------------------------------------------------------
class Woonplaats(BAGobject):
    def __init__(self):
        BAGobject.__init__(self)
        self.woonplaatsNaam      = BAGattribuut(80, "woonplaatsNaam", "bag_LVC:woonplaatsNaam")
        self.woonplaatsStatus    = BAGenumAttribuut(['Woonplaats aangewezen', 'Woonplaats ingetrokken'],
                                                    "woonplaatsStatus", "bag_LVC:woonplaatsStatus")
        self.woonplaatsGeometrie = BAGmultiPolygoon(2, 1000000, "_woonplaatsGeometrie", "bag_LVC:woonplaatsGeometrie")
        self.attributen.append(self.woonplaatsNaam)       
        self.attributen.append(self.woonplaatsStatus)       
        self.attributen.append(self.woonplaatsGeometrie)

    def tag(self):
        return "bag_LVC:Woonplaats"

    def naam(self):
        return "woonplaats"
    
    def objectType(self):
        return "WPL"
    
    def heeftGeometrie(self):
        return True

    def geometrie(self):
        return self.woonplaatsGeometrie

    def adres(self):
        return self.woonplaatsNaam.waarde()
    
    def maakIndex(self):
        BAGobject.maakIndex(self)
        sql  = "CREATE INDEX woonplaatsNaam"
        sql += " ON woonplaats" 
        sql += "(woonplaatsNaam)"
        database.maakIndex("woonplaatsNaam", sql)

    def maakViews(self):
        self.maakViewActueel()
        self.maakViewActueelBestaand(self.woonplaatsStatus.naam(), "Woonplaats ingetrokken", "")
        
#--------------------------------------------------------------------------------------------------------
# Class         OpenbareRuimte
# Afgeleid van  BAGobject
# Omschrijving  Class voor het BAG-objecttype OpenbareRuimte.
#--------------------------------------------------------------------------------------------------------
class OpenbareRuimte(BAGobject):
    def __init__(self):
        BAGobject.__init__(self)
        self.openbareRuimteNaam         = BAGattribuut(80, "openbareRuimteNaam", "bag_LVC:openbareRuimteNaam")
        self.openbareRuimteStatus       = BAGenumAttribuut(['Naamgeving uitgegeven', 'Naamgeving ingetrokken'], 
                                                            "naamgevingStatus", "bag_LVC:openbareruimteStatus")
        self.openbareRuimteType         = BAGenumAttribuut(['Weg',
                                                            'Water',
                                                            'Spoorbaan',
                                                            'Terrein',
                                                            'Kunstwerk',
                                                            'Landschappelijk gebied',
                                                            'Administratief gebied'], "openbareRuimteType", "bag_LVC:openbareRuimteType")
        self.gerelateerdeWoonplaats     = BAGnumeriekAttribuut(16, "gerelateerdeWoonplaats", "bag_LVC:gerelateerdeWoonplaats/bag_LVC:identificatie")
        self.verkorteOpenbareRuimteNaam = BAGattribuut(80, "verkorteOpenbareRuimteNaam", "nen5825:VerkorteOpenbareruimteNaam")
        self.attributen.append(self.openbareRuimteNaam)       
        self.attributen.append(self.openbareRuimteStatus)       
        self.attributen.append(self.openbareRuimteType)
        self.attributen.append(self.gerelateerdeWoonplaats)
        self.attributen.append(self.verkorteOpenbareRuimteNaam)

    def tag(self):
        return "bag_LVC:OpenbareRuimte"

    def naam(self):
        return "openbareruimte"
    
    def objectType(self):
        return "OPR"
    
    def adres(self):
        woonplaats = Woonplaats()
        woonplaats.identificatie.setWaarde(self.gerelateerdeWoonplaats.waarde())
        woonplaats.leesActueelVoorkomenUitDatabase()
        return "%s in %s" %(self.openbareRuimteNaam.waarde(), woonplaats.woonplaatsNaam.waarde())
        
    def maakIndex(self):
        BAGobject.maakIndex(self)
        sql  = "CREATE INDEX openbareruimteNaam"
        sql += " ON openbareruimte" 
        sql += "(openbareruimtenaam)"
        database.maakIndex("openbareruimteNaam", sql)

    def maakViews(self):
        self.maakViewActueel()
        self.maakViewActueelBestaand(self.openbareRuimteStatus.naam(), "Naamgeving ingetrokken", "")
        
#--------------------------------------------------------------------------------------------------------
# Class         Nummeraanduiding
# Afgeleid van  BAGobject
# Omschrijving  Class voor het BAG-objecttype Nummeraanduiding.
#--------------------------------------------------------------------------------------------------------
class Nummeraanduiding(BAGobject):
    def __init__(self):
        BAGobject.__init__(self)
        self.huisnummer                 = BAGnumeriekAttribuut(5, "huisnummer", "bag_LVC:huisnummer")
        self.huisletter                 = BAGattribuut( 1, "huisletter", "bag_LVC:huisletter")
        self.huisnummertoevoeging       = BAGattribuut( 4, "huisnummertoevoeging", "bag_LVC:huisnummertoevoeging")
        self.postcode                   = BAGattribuut( 6, "postcode", "bag_LVC:postcode")
        self.nummeraanduidingStatus     = BAGenumAttribuut(['Naamgeving uitgegeven', 'Naamgeving ingetrokken'],
                                                            "naamgevingStatus", "bag_LVC:nummeraanduidingStatus")
        self.typeAdresseerbaarObject    = BAGenumAttribuut(['Verblijfsobject',
                                                            'Standplaats',
                                                            'Ligplaats'], "typeAdresseerbaarObject", "bag_LVC:typeAdresseerbaarObject")
        self.gerelateerdeOpenbareRuimte = BAGnumeriekAttribuut(16, "gerelateerdeOpenbareRuimte", "bag_LVC:gerelateerdeOpenbareRuimte/bag_LVC:identificatie")
        self.gerelateerdeWoonplaats     = BAGnumeriekAttribuut(16, "gerelateerdeWoonplaats", "bag_LVC:gerelateerdeWoonplaats/bag_LVC:identificatie")
        self.attributen.append(self.huisnummer)       
        self.attributen.append(self.huisletter)       
        self.attributen.append(self.huisnummertoevoeging)
        self.attributen.append(self.postcode)
        self.attributen.append(self.nummeraanduidingStatus)
        self.attributen.append(self.typeAdresseerbaarObject)
        self.attributen.append(self.gerelateerdeOpenbareRuimte)
        self.attributen.append(self.gerelateerdeWoonplaats)

    def tag(self):
        return "bag_LVC:Nummeraanduiding"

    def naam(self):
        return "nummeraanduiding"
    
    def objectType(self):
        return "NUM"
    
    def adres(self):
        openbareRuimte = OpenbareRuimte()
        openbareRuimte.identificatie.setWaarde(self.gerelateerdeOpenbareRuimte.waarde())
        openbareRuimte.leesActueelVoorkomenUitDatabase()

        woonplaats = Woonplaats()
        if self.gerelateerdeWoonplaats.waarde() <> "":
            woonplaats.identificatie.setWaarde(self.gerelateerdeWoonplaats.waarde())
        else:
            woonplaats.identificatie.setWaarde(openbareRuimte.gerelateerdeWoonplaats.waarde())
        woonplaats.leesActueelVoorkomenUitDatabase()
        return "%s %s%s%s %s" %(openbareRuimte.openbareRuimteNaam.waarde(),
                                self.huisnummer.waarde(),
                                self.huisletter.waarde(),
                                self.huisnummertoevoeging.waarde(),
                                woonplaats.woonplaatsNaam.waarde())

    def getAdresseerbaarObject(self):
        adresseerbaarObject = None
        if self.typeAdresseerbaarObject.waarde().lower() == "ligplaats":
            adresseerbaarObject = Ligplaats()
        elif self.typeAdresseerbaarObject.waarde().lower() == "standplaats":
            adresseerbaarObject = Standplaats()
        elif self.typeAdresseerbaarObject.waarde().lower() == "verblijfsobject":
            adresseerbaarObject = Verblijfsobject()
        
        sql  = "SELECT DISTINCT identificatie"
        sql += "  FROM " + self.typeAdresseerbaarObject.waarde().lower() + "actueel"
        sql += " WHERE hoofdadres = %s"
        inhoud = (self.identificatie.waarde(),)
        database.cursor.execute(sql, inhoud)
        if database.cursor.rowcount == 0:
            sql  = "SELECT DISTINCT identificatie"
            sql += "  FROM adresseerbaarobjectnevenadres"
            sql += " WHERE nevenadres = %s"
            inhoud = (self.identificatie.waarde(),)
            database.cursor.execute(sql, inhoud)
        if database.cursor.rowcount == 0:
            adresseerbaarObject = None
        elif database.cursor.rowcount > 0:
            rows = database.cursor.fetchall()
            adresseerbaarObject.identificatie.setWaarde(rows[0][0])
            adresseerbaarObject.leesActueelVoorkomenUitDatabase()
        return adresseerbaarObject              

    def maakIndex(self):
        BAGobject.maakIndex(self)
        sql  = "CREATE INDEX nummeraanduidingPostcode"
        sql += " ON nummeraanduiding" 
        sql += "(postcode)"
        database.maakIndex("nummeraanduidingPostcode", sql)
        
    def maakViews(self):
        self.maakViewActueel()
        self.maakViewActueelBestaand(self.nummeraanduidingStatus.naam(), "Naamgeving ingetrokken", "")

        sql  = "CREATE VIEW %s"  
        sql += " AS SELECT NUM.identificatie AS nummeraanduidingidentificatie"
        sql += "         , OPR.identificatie AS openbareruimteidentificatie"
        sql += "         , WPL.identificatie AS woonplaatsidentificatie"
        sql += "         , WPL.woonplaatsnaam"
        sql += "         , OPR.openbareruimtenaam"
        sql += "         , NUM.postcode"
        sql += "         , NUM.huisnummer"
        sql += "         , NUM.huisletter"
        sql += "         , NUM.huisnummertoevoeging"
        sql += "         , NUM.typeadresseerbaarobject"
        sql += "  FROM woonplaats       WPL"
        sql += "     , openbareruimte   OPR"
        sql += "     , nummeraanduiding NUM"
        sql += " WHERE NUM.begindatum <= current_date"
        sql += "   AND NUM.einddatum  >= current_date"
        sql += "   AND NUM.aanduidingrecordinactief = FALSE"
        sql += "   AND OPR.identificatie = NUM.gerelateerdeopenbareruimte"
        sql += "   AND OPR.begindatum <= current_date"
        sql += "   AND OPR.einddatum  >= current_date"
        sql += "   AND OPR.aanduidingrecordinactief = FALSE"
        sql += "   AND (   (    WPL.identificatie = OPR.gerelateerdewoonplaats"
        sql += "            AND NUM.gerelateerdewoonplaats = NULL)"
        sql += "        OR (WPL.identificatie = NUM.gerelateerdewoonplaats))"
        sql += "   AND WPL.begindatum <= current_date"
        sql += "   AND WPL.einddatum  >= current_date"
        sql += "   AND WPL.aanduidingrecordinactief = FALSE"
        database.maakView("adresActueel", sql %("adresActueel"))
        
        sql += "   AND NUM.naamgevingStatus <> 'Naamgeving ingetrokken'"
        database.maakView("adresActueelBestaand", sql %("adresActueelBestaand"))
        
        
#--------------------------------------------------------------------------------------------------------
# Class         BAGadresseerbaarObject
# Afgeleid van  BAGobject
# Omschrijving  Basisclass voor de adresseerbare objecten ligplaats, standplaats en verblijfsobject.
#               Deze class definieert het hoofdadres en de nevenadressen.
#--------------------------------------------------------------------------------------------------------
class BAGadresseerbaarObject(BAGobject):
    _tabel_nevenadres_aangemaakt = False
    _index_nevenadres_aangemaakt = False
    
    def __init__(self):
        BAGobject.__init__(self)
        self.hoofdadres = BAGattribuut(       16, "hoofdadres", "bag_LVC:gerelateerdeAdressen/bag_LVC:hoofdadres/bag_LVC:identificatie")
        self.nevenadres = BAGrelatieAttribuut("adresseerbaarobjectnevenadres",
                                              16, "nevenadres", "bag_LVC:gerelateerdeAdressen/bag_LVC:nevenadres/bag_LVC:identificatie")
        self.attributen.append(self.hoofdadres)       
        self.attributen.append(self.nevenadres)       

    def adres(self):
        nummeraanduiding = Nummeraanduiding()
        nummeraanduiding.identificatie.setWaarde(self.hoofdadres.waarde())
        nummeraanduiding.leesActueelVoorkomenUitDatabase()
        return nummeraanduiding.adres()

    def maakTabel(self):
        BAGobject.maakTabel(self)
        if not BAGadresseerbaarObject._tabel_nevenadres_aangemaakt:
            BAGobject.maakTabelRelatie(self, self.nevenadres)
            BAGadresseerbaarObject._tabel_nevenadres_aangemaakt = True

    def controleerTabel(self):
        return (BAGobject.controleerTabel(self)
                and BAGobject.controleerTabelRelatie(self, self.nevenadres))
        
    def maakIndex(self):
        BAGobject.maakIndex(self)
        if not BAGadresseerbaarObject._index_nevenadres_aangemaakt:
            BAGobject.maakIndexRelatie(self, self.nevenadres)
            BAGadresseerbaarObject._index_nevenadres_aangemaakt = True

        
#--------------------------------------------------------------------------------------------------------
# Class         Ligplaats
# Afgeleid van  BAGadresseerbaarObject
# Omschrijving  Class voor het BAG-objecttype Ligplaats.
#--------------------------------------------------------------------------------------------------------
class Ligplaats(BAGadresseerbaarObject):
    def __init__(self):
        BAGadresseerbaarObject.__init__(self)
        self.ligplaatsStatus = BAGenumAttribuut(['Plaats aangewezen', 'Plaats ingetrokken'],
                                                 "plaatsStatus", "bag_LVC:ligplaatsStatus")
        self.ligplaatsGeometrie = BAGpolygoon(3, 1000000, "ligplaatsGeometrie", "bag_LVC:ligplaatsGeometrie")
        self.attributen.append(self.ligplaatsStatus)       
        # self.attributen.append(self.ligplaatsGeometrie)       

    def tag(self):
        return "bag_LVC:Ligplaats"

    def naam(self):
        return "ligplaats"
    
    def objectType(self):
        return "LIG"
    
    def heeftGeometrie(self):
        return True

    def geometrie(self):
        return self.ligplaatsGeometrie
    
    def maakViews(self):
        self.maakViewActueel()
        self.maakViewActueelBestaand(self.ligplaatsStatus.naam(), "Plaats ingetrokken", "")

#--------------------------------------------------------------------------------------------------------
# Class         Standplaats
# Afgeleid van  BAGadresseerbaarObject
# Omschrijving  Class voor het BAG-objecttype Standplaats.
#--------------------------------------------------------------------------------------------------------
class Standplaats(BAGadresseerbaarObject):
    def __init__(self):
        BAGadresseerbaarObject.__init__(self)
        self.standplaatsStatus = BAGenumAttribuut(['Plaats uitgegeven', 'Plaats ingetrokken'],
                                                   "plaatsStatus", "bag_LVC:standplaatsStatus")
        self.standplaatsGeometrie = BAGpolygoon(3, 1000000, "_standplaatsGeometrie", "bag_LVC:standplaatsGeometrie")
        self.attributen.append(self.standplaatsStatus)       
        self.attributen.append(self.standplaatsGeometrie)       

    def tag(self):
        return "bag_LVC:Standplaats"

    def naam(self):
        return "standplaats"
    
    def objectType(self):
        return "STA"
    
    def heeftGeometrie(self):
        return True

    def geometrie(self):
        return self.standplaatsGeometrie
    
    def maakViews(self):
        self.maakViewActueel()
        self.maakViewActueelBestaand(self.standplaatsStatus.naam(), "Plaats ingetrokken", "")

#--------------------------------------------------------------------------------------------------------
# Class         Verblijfsobject
# Afgeleid van  BAGadresseerbaarObject
# Omschrijving  Class voor het BAG-objecttype Verblijfsobject.
#--------------------------------------------------------------------------------------------------------
class Verblijfsobject(BAGadresseerbaarObject):
    def __init__(self):
        BAGadresseerbaarObject.__init__(self)
        self.verblijfsobjectStatus       = BAGenumAttribuut(['Verblijfsobject gevormd', \
                                                             'Niet gerealiseerd verblijfsobject', \
                                                             'Verblijfsobject in gebruik (niet ingemeten)', \
                                                             'Verblijfsobject in gebruik', \
                                                             'Verblijfsobject ingetrokken', \
                                                             'Verblijfsobject buiten gebruik'],
                                                             "verblijfsobjectStatus", "bag_LVC:verblijfsobjectStatus")
        self.oppervlakteVerblijfsobject  = BAGnumeriekAttribuut(6, "oppervlakteVerblijfsobject",  "bag_LVC:oppervlakteVerblijfsobject")
        self.verblijfsobjectGeometrie    = BAGpoint(          100, "_verblijfsobjectGeometrie", "bag_LVC:verblijfsobjectGeometrie")
        self.gebruiksdoelVerblijfsobject = BAGrelatieAttribuut("verblijfsobjectgebruiksdoel",
                                                               50, "gebruiksdoelVerblijfsobject", "bag_LVC:gebruiksdoelVerblijfsobject")
        self.gerelateerdPand             = BAGrelatieNumeriekAttribuut("verblijfsobjectpand",
                                                               16, "gerelateerdPand", "bag_LVC:gerelateerdPand/bag_LVC:identificatie")
        self.attributen.append(self.verblijfsobjectStatus)       
        self.attributen.append(self.oppervlakteVerblijfsobject)       
        self.attributen.append(self.verblijfsobjectGeometrie)       
        self.attributen.append(self.gebruiksdoelVerblijfsobject)       
        self.attributen.append(self.gerelateerdPand)       

    def tag(self):
        return "bag_LVC:Verblijfsobject"

    def naam(self):
        return "verblijfsobject"
    
    def objectType(self):
        return "VBO"
    
    def heeftGeometrie(self):
        return True

    def geometrie(self):
        return self.verblijfsobjectGeometrie
    
    def maakTabel(self):
        BAGadresseerbaarObject.maakTabel(self)
        BAGobject.maakTabelRelatie(self, self.gebruiksdoelVerblijfsobject)
        BAGobject.maakTabelRelatie(self, self.gerelateerdPand)

    def controleerTabel(self):
        return (BAGobject.controleerTabel(self)
                and BAGobject.controleerTabelRelatie(self, self.gebruiksdoelVerblijfsobject)
                and BAGobject.controleerTabelRelatie(self, self.gerelateerdPand))

    def maakIndex(self):
        BAGadresseerbaarObject.maakIndex(self)
        BAGobject.maakIndexRelatie(self, self.gebruiksdoelVerblijfsobject)
        BAGobject.maakIndexRelatie(self, self.gerelateerdPand)

    def maakViews(self):
        self.maakViewActueel()
        self.maakViewActueelBestaand(self.verblijfsobjectStatus.naam(), "Niet gerealiseerd verblijfsobject","Verblijfsobject ingetrokken")
       
#--------------------------------------------------------------------------------------------------------
# Class         Pand
# Afgeleid van  BAGobject
# Omschrijving  Class voor het BAG-objecttype Pand.
#--------------------------------------------------------------------------------------------------------
class Pand(BAGobject):
    def __init__(self):
        BAGobject.__init__(self)
        self.pandStatus    = BAGenumAttribuut(['Bouwvergunning verleend', \
                                               'Niet gerealiseerd pand', \
                                               'Bouw gestart', \
                                               'Pand in gebruik (niet ingemeten)', \
                                               'Pand in gebruik', \
                                               'Sloopvergunning verleend', \
                                               'Pand gesloopt', \
                                               'Pand buiten gebruik'], "pandStatus", "bag_LVC:pandstatus")
        self.bouwjaar      = BAGnumeriekAttribuut(4, "bouwjaar", "bag_LVC:bouwjaar")
        self.pandGeometrie = BAGpolygoon(3, 1000000, "_pandGeometrie", "bag_LVC:pandGeometrie")
        self.attributen.append(self.pandStatus)       
        self.attributen.append(self.bouwjaar)       
        self.attributen.append(self.pandGeometrie)       

    def tag(self):
        return "bag_LVC:Pand"

    def naam(self):
        return "pand"

    def objectType(self):
        return "PND"
    
    def heeftGeometrie(self):
        return True

    def geometrie(self):
        return self.pandGeometrie

    def adres(self):
        adres = ""
        verblijfsobjecten = self.getVerblijfsobjecten()
        if len(verblijfsobjecten) > 0:
            adres = verblijfsobjecten[0].adres()
        if len(verblijfsobjecten) > 1:
            adres += "...(%d)" %(len(verblijfsobjecten))
        return adres

    def getVerblijfsobjecten(self):
        verblijfsobjecten = []
        
        sql  = "SELECT DISTINCT identificatie"
        sql += "  FROM verblijfsobjectpand" 
        sql += " WHERE gerelateerdpand = %s"
        inhoud = (self.identificatie.waarde(),)
        database.cursor.execute(sql, inhoud)
        for row in database.cursor.fetchall():
            verblijfsobject = Verblijfsobject()
            verblijfsobject.identificatie.setWaarde(row[0])
            verblijfsobject.leesActueelVoorkomenUitDatabase()
            verblijfsobjecten.append(verblijfsobject)
        return verblijfsobjecten
    
    def maakViews(self):
        self.maakViewActueel()
        self.maakViewActueelBestaand(self.pandStatus.naam(), "Niet gerealiseerd pand","Pand gesloopt")


#--------------------------------------------------------------------------------------------------------
# Geef een BAGobject van het juiste type bij het gegeven type.
#--------------------------------------------------------------------------------------------------------
def getBAGobjectBijType(objectType):
    if objectType.upper() == "WPL":
        return Woonplaats()
    if objectType.upper() == "OPR":
        return OpenbareRuimte()
    if objectType.upper() == "NUM":
        return Nummeraanduiding()
    if objectType.upper() == "LIG":
        return Ligplaats()
    if objectType.upper() == "STA":
        return Standplaats()
    if objectType.upper() == "VBO":
        return Verblijfsobject()
    if objectType.upper() == "PND":
        return Pand()
    return None

#--------------------------------------------------------------------------------------------------------
# Geef een BAGobject van het juiste type bij de gegeven identificatie.
# Het type wordt afgeleid uit de identificatie.
#--------------------------------------------------------------------------------------------------------
def getBAGobjectBijIdentificatie(identificatie):
    obj = None
    if len(identificatie) == 4:
        obj = Woonplaats()
    elif identificatie[4:6] == "30":
        obj = OpenbareRuimte()
    elif identificatie[4:6] == "20":
        obj = Nummeraanduiding()
    elif identificatie[4:6] == "02":
        obj = Ligplaats()
    elif identificatie[4:6] == "03":
        obj = Standplaats()
    elif identificatie[4:6] == "01":
        obj = Verblijfsobject()
    elif identificatie[4:6] == "10":
        obj = Pand()
    if obj:
        obj.identificatie.setWaarde(identificatie)
    return obj



