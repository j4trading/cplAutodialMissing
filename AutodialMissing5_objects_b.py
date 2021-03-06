# works

import csv
import datetime
import time

#new
#import win32wnet
import shutil
import os

import smtplib

import re

from operator import itemgetter

import mysql.connector
#from python_mysql_dbconfig import read_db_config

#-----------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------
# Every day kbase produces phone record for all autodial groups from yesterday to 10 days before that
# Turn that into a csv file
# We put that into a list of lists
# we need to filter out undesirables like fax from inquiries using autodial group table which will be pulled from kbase on a monthly or weekly basis.
# Process list of lists to get a list of "bad autodial groups"
# Filter inhouse autodial groups, dummy groups.  Keep inactive autodial groups but call to my attention...also note where all clients under one autodial group are all inactive  These will be emailed to me or someone in data or IT.
# Use monthly or weekly kbase flat files to get the revenue center, territory, client name, client number from the filtered bad autodial list above to email to correct regional managers

#-----------------------------------------------------------------------------------------------------
#    TO DO:

# we need to filter out undesirables like fax from inquiries using autodial group table which will be pulled from kbase on a monthly or weekly basis.
#Fidn a way to get python to sort on its own and not rely on kbase
#     sort not just aht phone record one but the other ones too
# do everything that follows after a rough "bad autodial list" is produced.
# fix the whole noon midnight thing that it does: "12:00 N"....BUT I don'tt think we have to worry about that because nothing in our stuff relies on this.
# delete lists as needed
# make it all object oriented because it's getting pretty difficult to understand
# what to do about those without a normala revenue center

#ARCHIVED THIS VERSION (AutodialMissing2.py):
#IT SUCCESSFULLY DOES THIE FOLLOWING:
# IT TAKES a csv file soreted sorted by kbase
# takes out all the fax form inquiries
# gets a lits of bad autodial/autofax/etc... which have attempteed to report yesterday, and 7 days before today and have vhad no code 10 nor 14 in all that time in between and boundaries inclusive


# new changes in AutodialMissing3.py as of 10/14/17:
# NOw adds the badautodiallist stuff into a detailed list which includes stuff form the autodial table....I still neeed to make sure that all tables from kbase are well sorted. without using kbase to sort.
# THE badautodialdetailed lsit thing appears to be working...10/16/2017.  I  haven't tested stuff.  Also the phone number is in exponential because too big...need to make it string.
# I tested and it looks like badautodialdeteailed list is just fine.   10/16/17 night
# Next now: 1. figure out how to do email through Python...then organize what emails will look like
# findAutodialsWithNoClients(badAutodialsDetailed).....this added today  10/17/2017  works fine

# new changes in AutodialMissing4.py as of 10/19/17:
# 10/19/2017  I added distributeToVariousLists which creates slaes list and IT only list.  SEems to work fine...except that I only tested autofax and autodial...test list didn't have enough data to test he others
#             everyting else seems to work fine.

# new changes in AutodialMissing5.py as of 10/19/17:
#i ADDED to include the network node stuff...I th ink tit's pretty straightforward...but I haven't tested any consequences of it nor know what it looks like besides the file from kbase
#To Do : I still need to test functionality of numberOfActiveClients in the badAutodialsDetailed thing
# I get discrepancy with SANBAP...I need to fix the the it changes the phone nubmer on SANBAP after I do stuff like I'm not sure what...maybe after sorting in Excel or what not.  I thinkI need to change all phone nubmers to strings in python

#Autodial5object.py as of 10.21.17
# alsmost tests fine for email message creation.
# note that the sorting function works just fine.
#the email creation one almost works fine...it just has a fine poitn that it fails on....see notes in notes_171020.txt

#Now all I have to do is fill out that email contacts table
#Also cliean up the mesage string so that its oly per revenue center

#index variable for overall list of lists
mainListAutodialRow = 0   
mainListDayRow = 1
mainListResponseRow = 4 
listOfRows = []         # multidimentional list produced from phone records file

#index variables for multidimentional list for single autodial group
dayListDayRow = 0
dayListResponseRow = 1
dayList = []            # list for single autodial group

autodialErrorTableList = []

badAutodialList = []          #not just modem "autodials" but also any except fax from inquiry, such as inhouse printing, autofax, dummy groups

badAutodialsDetailed = []
#List with everything.
# this has: autodialGroup, isAGroupActive, revcent, territory, portclass, typeOfDevice, phoneNumber, clientNumber, isClientActive
#     it will be ordered by autodialGroup.  Although each AutodialGroup may be eentered multiple times acacording to the autodialtable csv
#     which has a different client on each autodial Group entry

badAutodialsDetailedToIT = []   # This is badAutodialsDetailed filtered and is only of interest to IT...these dont' require any correspondence with client to fix.

badAutodialsDetailedToSales = []    # This is badAutodialsDetailed filtered and are autodials that account reps woudl need to be made aware of in order to fix.

bList1AGroupColumn = 0
bList1AGroupInactiveColumn = 1
bList1NumberOfActiveClients = 2
bList1ClientAcctNumberColumn = 3
bList1ClientName = 4
bList1ClientActiveColumn = 5
bList1RevCentColumn = 6
bList1TerritoryColumn = 7
bList1PortClassColumn = 8
bList1DeviceTypeColumn = 9
bList1PNumberColumn = 10
bList1ResponseColumn = 11
bList1AGType = 12
bList1Comment = 13
bList1NetworkNodeColumn = 14

ADTableADGroupColumn = 0
ADTableADPhoneNumberColumn = 1
ADTableIsADInactiveColumn = 2
ADTableRevCentColumn = 3
ADTableClientNumberColumn = 4
ADTableClientNameColumn = 5
ADTableTerritoryColumn = 6
ADTableSalesPersonColumn = 7
ADTableIsClientActiveColumn = 8
ADTableClientReportRoutineColumn = 9
ADTableAdditionalADGroupColumn = 10
ADTablePortClassColumn = 11
ADTablePorClass1Column = 12
ADTablePortClass2Column = 13
ADTablePortClass3Column = 14
ADTableADReportRoutineColumn = 15
ADTableReportRoutineInhouseColumn = 16
ADTableNetworkNodeColumn = 17

emailContactsList = []
emailContactRevCentColumn = 0
emailContactsManagerFirstNameColumn = 1
emailContactsManagerLastNameColumn = 2
emailContactsEmailAddressColumn = 3
emailContactsMessage = 4

emailContactsList = [
                     ["DALLAS", "Dan", "Helminsky", "dhelminsky@cpllabs.com", ""],
                     ["HOUSTON", "Jim", "Gebhart", "jgebhart@cpllabs.com", ""],
                     ["AUSTIN", "Tony", "Jones", "tjones@cpllabs.com", ""],
                     ["LASVEGAS", "John", "Evans", "jevans@cpllabs.com", ""],
                     ["OKCITY", "Leah", "Nickell", "lnichell@cpllabs.com", ""],
                     ["TULSA", "Leah", "Nickell", "lnichell@cpllabs.com", ""]
                    ]

badClientList = []
# This is basically the badAutodialDetailed but accomodated for a sales reep
# it will be in order of clients and secondly in order by autodial groups
# it will include modem autodials and autofaxes.
# it will also include inhouseu printers

listForMe = []
#This is stuff that only I need to be looking at but which sales reps cannot address.
#Includes autodial groups with not active clients, inactive autodial groups

#the list presented 

#todayDate = datetime.date.today()
todayDate = datetime.datetime.strptime("10/11/2017","%m/%d/%Y").date()

#class PhoneRecord(object):
    

def prepareSalesEmail (badAutodialsDetailedToSales):
    initialMessage = "These clients' autodials/autofax have not been reporting for at least the past 7 days.  \nPlease remember that if a client does not report then CPL does not get paid.\n  This is true whether or not the clientn is on Atlas or an EMR.\n"
    emailMessageList = []
#    emailMessageDict = dict{"":"one","dos":"two"}
    
    sortedBadAutodialsList = sorted(badAutodialsDetailedToSales, key=itemgetter(bList1RevCentColumn, bList1TerritoryColumn, bList1AGroupColumn, bList1ClientAcctNumberColumn))
    currentIndex = 0
    message = initialMessage

    lastRevenueCenterAlreadyProcessedFlag = 0
    revCentTempList = []
    territoryTempList = []
    autodialTempList = []
#########################################################################
#a1
    while currentIndex < len(sortedBadAutodialsList):
        #This section is done when ever Revenue Center changes
        revCentTempList.clear()
        currentRevCent = sortedBadAutodialsList[currentIndex][bList1RevCentColumn]
        message = message + "Revenue Center: " + currentRevCent + "\n"

        while (currentIndex < len(sortedBadAutodialsList)) and sortedBadAutodialsList[currentIndex][bList1RevCentColumn] == currentRevCent:
            #This section done when revenue center stays the same and territory changes
            revCentTempList.append(sortedBadAutodialsList[currentIndex])
            currentTerritory = sortedBadAutodialsList[currentIndex][bList1TerritoryColumn]
            territoryTempList.clear()
            message = message + "Territory ID: " + currentTerritory + "\n"

            while (currentIndex < len(sortedBadAutodialsList)) and sortedBadAutodialsList[currentIndex][bList1RevCentColumn] == currentRevCent and sortedBadAutodialsList[currentIndex][bList1TerritoryColumn] == currentTerritory:
            #This section done when territory stays the same
                territoryTempList.append(sortedBadAutodialsList[currentIndex])
                #This section doen when autodial group changes
                autodialTempList.clear()
                currentAutodial = sortedBadAutodialsList[currentIndex][bList1AGroupColumn]
                message = message + "   Autodial/autofax group using autodial/autofax phone number: " + sortedBadAutodialsList[currentIndex][bList1PNumberColumn] +" is not reporting.\n"
                message = message + "     It is used by the following clients:"
                while (currentIndex < len(sortedBadAutodialsList)) and sortedBadAutodialsList[currentIndex][bList1RevCentColumn] == currentRevCent and sortedBadAutodialsList[currentIndex][bList1TerritoryColumn] == currentTerritory and sortedBadAutodialsList[currentIndex][bList1AGroupColumn] == currentAutodial:
                    #This section done when autoeiasl group stays the same
                    autodialTempList.append(sortedBadAutodialsList[currentIndex])
                    message = message + "        Client: " + sortedBadAutodialsList[currentIndex][bList1ClientAcctNumberColumn] +" (" + sortedBadAutodialsList[currentIndex][bList1ClientName] +")"
                    if len(sortedBadAutodialsList[currentIndex][bList1NetworkNodeColumn]) > 0:
                        message += " NOTE: CLIENT IS ON ATLAS OR AN EMR"
                    else:
                        message += "NOTE: CLIENT DOES NOT HAVE ATLAS OR AN EMR"
                    message += "\n"

                    currentIndex += 1

                message += "\n"  #End of current Autodial
            message += "\n"  #End of current Territory
        message += "\n" #End of current Revenue cetner
#########################################################################
                
        #This section is done at the end of a given Revenue Center within the outer most loop
        emailRevCentFoundFlag = 0
        for emailIndex in range(0,len(emailContactsList)):
            if emailContactsList[emailIndex][emailContactRevCentColumn] == currentRevCent:
                emailContactsList[emailIndex][emailContactsMessage] = message
                emailRevCentFoundFlag = 1
                break
        if emailRevCentFoundFlag == 0:
            writeToLog("\n " + todayDate.strftime('%Y/%m/%d') + " Revenue Center was not found in email Contacts List...so no email sent to regional manager....message was: " + message + "\n")
    print("start of message")
    print("message is: " + message)
    print("end of message")

    

def storeAutodialTable():
    with open('autodialmissingref.csv','r') as f:
        csv_f = csv.reader(f)
        for row in csv_f:
#            oneRowList = row[:]
            autodialErrorTableList.append(row)

def placeInBadDetailedList(badAutodialList):
    currentIndex = 0
    for i in range(0, len(badAutodialList)):
        for j in range(1,len(autodialErrorTableList)):

            #printdebug
            if i == 0 and j == 5:
               writeToLog(autodialErrorTableList[j][ADTableADGroupColumn])
               print("length: ",len(autodialErrorTableList))
               print("index: ",autodialErrorTableList[j][ADTableADGroupColumn])
               print("j: ",j)
               print("ADTableADGroupColumn: ",ADTableADGroupColumn)

            if autodialErrorTableList[j][ADTableADGroupColumn] != badAutodialList[i][0]:
                continue
            else:
                tempList = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
                badAutodialsDetailed.append(tempList)
                badAutodialsDetailed[currentIndex][bList1AGroupColumn] = autodialErrorTableList[j][ADTableADGroupColumn]
                badAutodialsDetailed[currentIndex][bList1AGroupInactiveColumn] = autodialErrorTableList[j][ADTableIsADInactiveColumn]
                badAutodialsDetailed[currentIndex][bList1ClientAcctNumberColumn] = autodialErrorTableList[j][ADTableClientNumberColumn]
                badAutodialsDetailed[currentIndex][bList1ClientName] = autodialErrorTableList[j][ADTableClientNameColumn]
                badAutodialsDetailed[currentIndex][bList1ClientActiveColumn] = autodialErrorTableList[j][ADTableIsClientActiveColumn]
                badAutodialsDetailed[currentIndex][bList1RevCentColumn] = autodialErrorTableList[j][ADTableRevCentColumn]
                badAutodialsDetailed[currentIndex][bList1TerritoryColumn] = autodialErrorTableList[j][ADTableTerritoryColumn]
                badAutodialsDetailed[currentIndex][bList1PortClassColumn] = autodialErrorTableList[j][ADTablePortClassColumn]
                badAutodialsDetailed[currentIndex][bList1PNumberColumn] = autodialErrorTableList[j][ADTableADPhoneNumberColumn]
                badAutodialsDetailed[currentIndex][bList1NetworkNodeColumn] = autodialErrorTableList[j][ADTableNetworkNodeColumn]
                
                currentIndex = currentIndex + 1
                
def writeToLog(stringHere):
    file = open("LogIt.txt","a")
    file.write(stringHere)
    file.close()

def sortTable(listOfLists):
    #This sorts a table (a list of lists) and will return a table sorted out by autodial group and then by date
    return sorted(listOfLists, key=itemgetter(0,1,2))

def removeFromTable(listOfRows):
    """ takes a list of lists and removes undesirable rows from it
        It returns 0 if nothing deleted from listOfRows...1 otherwise"""
    faxInqExistsFlag = 0
    faxInqFirstIndex = 0
    faxInqLastIndex = 0
    somethingDeletedFlag = 0    #equals 0 if nothing deleted...1 otherwise
    for i in range(1,len(listOfRows)):
        if listOfRows[i][mainListAutodialRow][:6] == "FAXINQ" and faxInqFirstIndex == 0:
            faxInqExistsFlag = 1
            faxInqFirstIndex = i
        if faxInqExistsFlag == 1 and faxInqFirstIndex != 0 and listOfRows[i][mainListAutodialRow][:6] != "FAXINQ" and faxInqLastIndex == 0:
            faxInqLastIndex = i-1
            break
    if faxInqExistsFlag != 0 and faxInqFirstIndex != 0 and faxInqLastIndex != 0 and faxInqLastIndex > faxInqFirstIndex:
        del listOfRows[faxInqFirstIndex:(faxInqLastIndex+1)]
        somethingDeletedFlag = 1
    return somethingDeletedFlag
        
        
#this function appears to not be used by anoyone... 10/21/17
def checkDayForSuccess(dayList):
    """ Takes a list that holds a whole day's worth of phone records
        It outputs 0 if there was no success throughout that entire day"""
    successFlag = 0
    for i in dayList:
        if dayList[i][responseRow] == '10' or dayList[i][responseRow] == '14':
            successFlag = 1
            break
    return successFlag

def isBadAutodial(currentAutodial,dayList):
    """ This checks if it's a bad autodial.  IT's bad if
        there was activity for at least 7 days with no success therein
        We want to make sure there was activity at leasts 7 days ago so as to not catch autodial/autofax groups that were recently created in that time."""
    sevenDaysAgoActivityFlag = 0
    yesterdayAttemptedFlag = 0
    successEncounteredFlag = 0
    #look 7 days back
    for i in range(0,len(dayList)):
        thisDay = datetime.datetime.strptime(dayList[i][dayListDayRow],"%m/%d/%Y").date()
        if thisDay == week_ago:
            sevenDaysAgoActivityFlag = 1
        if (thisDay == yesterday):
            yesterdayAttemptedFlag = 1
        if dayList[i][dayListResponseRow] == '10' or dayList[i][dayListResponseRow] == '14':
            successEncounteredFlag = 1
#    if successEncounteredFlag == 1:
#        print("successenc")
    if sevenDaysAgoActivityFlag == 1 and yesterdayAttemptedFlag == 1 and successEncounteredFlag == 0:
        return 1
    else:
        return 0

def badAutodialProcedure(badAutodialList):
    """ finds the client name, client number for a given autodial/autofax group
        It it's a dummy groups, inhouse groups, or inactive group it sends a special email to me.
        If it's a autodial (CPL printer) or autofax group (inactive or not) it finds the revenue center and territory name.
        It then uses that to send an email to the corresponding regional manager including the clients names and account numbers
        If it's an inactive group it will send an email to me too."""
    pass

#abc123
def findAutodialsWithNoClients(badAutodialsDetailed):
    """ This function looks in the list of bad Autodials which is detailed and sees if any of those bad autodial groups
        have no clients which are active.
        The bad autodial detailed list right now would have all the clients for that bad autodial since the initial filtering out into the badAutodialsDetailed list was done by autodial group"""
    noClientIsActive = 1
    for i in range(1,len(badAutodialsDetailed)):
        if len(badAutodialsDetailed) <= 1:         #This is to guard against run-time errors since we will be comparing with the previous element in list.
            break
        if badAutodialsDetailed[i][bList1AGroupColumn] != badAutodialsDetailed[i -1][bList1AGroupColumn]:
            noClientIsActive = 1
            if badAutodialsDetailed[i][bList1ClientActiveColumn] == "YES":
                noClientIsActive = 0
                print("in here")
        if badAutodialsDetailed[i][bList1AGroupColumn] == badAutodialsDetailed[i -1][bList1AGroupColumn]:
            if noClientIsActive != 0:
                if badAutodialsDetailed[i][bList1ClientActiveColumn] == "YES":
                    noClientIsActive = 0
        if noClientIsActive == 1:
            badAutodialsDetailed[i][bList1Comment] = str(badAutodialsDetailed[i][bList1Comment]) + " bad Autodial with no clients;"
            badAutodialsDetailedToIT.append(badAutodialsDetailed[i])

def countActiveClientsPerAutodial(badAutodialsDetailed):
    """ This function goes through badAutodialsDetailed list and counts the number of active clients that exist for each autodial group"""
    currentCount = 0
    indexOfFirstOccurenceOfAutodial = 0
    for i in range(0,len(badAutodialsDetailed)):
        if len(badAutodialsDetailed) == 0:
            break
        if len(badAutodialsDetailed) == 1:
            if badAutodialsDetailed[i][bList1ClientActiveColumn].lower() == "yes":
                badAutodialsDetailed[i][bList1NumberOfActiveClients] = 1
            else:
                badAutodialsDetailed[i][bList1NumberOfActiveClients] = 0
            break

        else:           #case where we have more than 1 in badAutodislDetailed list
            if i != 0:
                if badAutodialsDetailed[i][bList1AGroupColumn] != badAutodialsDetailed[i-1][bList1AGroupColumn]:
                    for j in range(indexOfFirstOccurenceOfAutodial, i):
                        badAutodialsDetailed[j][bList1NumberOfActiveClients] = currentCount
                    currentCount = 0
                    indexOfFirstOccurenceOfAutodial = i

                if badAutodialsDetailed[i][bList1ClientActiveColumn].lower() == "yes":
                    currentCount += 1

                #This if/else block is for the last autodial group in the last.
                #This if else block was necessary because the other if/else blocks add the number of active clients at the element after the last element of the autodial group in question.
                    #but in this case doing that would cause an exception error since we are at the end of the list.
                if i == len(badAutodialsDetailed)-1:
                    for j in range(indexOfFirstOccurenceOfAutodial, i+1):
                        badAutodialsDetailed[j][bList1NumberOfActiveClients] = currentCount
                    break
            else:
                indexOfFirstOccurenceOfAutodial = 0
                currentCount = 0
                if badAutodialsDetailed[i][bList1ClientActiveColumn].lower() == "yes":
                    currentCount += 1

emailToSalesList = []


#abc456            
def distributeToVariousLists(badAutodialsDetailed):
    """ This function does 2 things
        1. It analyzes the individual autodial groups and sees if it's a dummy group,autodial,autofax, or inhouse printing..and it adds this info to the list.
        2. It creates 2 others lists: 1 for sales and 1 for IT.  The sales list is destined to be used to be able to send out emails to sales team.
    """
    PossiblyInhousePrinterFlag = 1             #everything left over after dummy, autodial, autofax groups can possibly be inhouse printing.  This flag helps keep track of that.
    for i in range(0,len(badAutodialsDetailed)):
        if "dummy" in badAutodialsDetailed[i][bList1PortClassColumn].lower():
            badAutodialsDetailed[i][bList1AGType] = "Dummy"
            badAutodialsDetailed[i][bList1Comment] = " bad dummy group; "
            badAutodialsDetailedToIT.append(badAutodialsDetailed[i])
            PossiblyInhousePrinterFlag = 0

        string1 = str(badAutodialsDetailed[i][bList1PortClassColumn].lower())
        matchObj = re.match(r'2,|3,|4,|7,|10,|11,|29,|30,|31,|69,|70,|71' ,string1,re.I)          #port class will begin with modem number followed by a comma or will have just one modem number
        matchObj2 = re.match(r'^2$|^3$|^4$|^7$|^10$|^11$|^29$|^30$|^31$|^69$|^70$|^71$' ,string1,re.I)
        if matchObj or matchObj2:
            badAutodialsDetailed[i][bList1AGType] = "Autodial"
            badAutodialsDetailed[i][bList1Comment] = " bad Autodial group; "            
            badAutodialsDetailedToIT.append(badAutodialsDetailed[i])
            PossiblyInhousePrinterFlag = 0

        if "t4fax" in badAutodialsDetailed[i][bList1PortClassColumn].lower() or "t4faxdrl" in badAutodialsDetailed[i][bList1PortClassColumn].lower():
            badAutodialsDetailed[i][bList1AGType] = "Autofax"
            badAutodialsDetailed[i][bList1Comment] = " bad autofax group; "
            badAutodialsDetailedToSales.append(badAutodialsDetailed[i])        
            PossiblyInhousePrinterFlag = 0

        if PossiblyInhousePrinterFlag == 1:
            badAutodialsDetailed[i][bList1AGType] = "Inhouse Printer"
            badAutodialsDetailed[i][bList1Comment] = " possibly bad inhouse printer; "
            badAutodialsDetailedToIT.append(badAutodialsDetailed[i])                    

def mainProgPart():
    newAutodialFlag = 1
    newDateFlag = 1
    dayList.clear()
    for row in range(1,len(listOfRows)):
        if row == 1:
            currentAutodial = listOfRows[row][mainListAutodialRow]
            newAutodialFlag = 0
            dayList.append([listOfRows[row][mainListDayRow],listOfRows[row][mainListResponseRow]])
            newDateFlag = 0
        else:
            if (listOfRows[row][mainListAutodialRow] != listOfRows[row-1][mainListAutodialRow]) and (row != 1):
                newAutodialFlag = 1
                newDateFlag = 1
            else:
                dayList.append([(listOfRows[row][mainListDayRow]),(listOfRows[row][mainListResponseRow])])
    
            if newAutodialFlag == 1:
                if isBadAutodial(currentAutodial,dayList):
                    badAutodialList.append([currentAutodial,listOfRows[row][mainListDayRow], listOfRows[row][mainListResponseRow]])
                    #print("adding to badautodiallis")
                currentAutodial = listOfRows[row][mainListAutodialRow]
                newAutodialFlag = 0
                dayList.clear()
                dayList.append([(listOfRows[row][mainListDayRow]),(listOfRows[row][mainListResponseRow])])
                newDateFlag = 0

def outputToCSV():
    with open('OutputCSV.csv', "w", newline = '') as csv_file:
     writer = csv.writer(csv_file, delimiter=',')
     for line in listOfRows:
         writer.writerow(line)

def appendBadListToCSV():
    with open('OutputCSV.csv',"a", newline = '') as csv_file2:
        writer = csv.writer(csv_file2, delimiter=',')
        writer.writerow("zzzzz")
        for line in badAutodialList:
            writer.writerow(line)

def writeTestListToCSV(listToWrite):
    with open('TestCSV.csv',"w", newline = '') as csv_file2:
        writer = csv.writer(csv_file2, delimiter=',')
        for line in listToWrite:
            writer.writerow(line)            

def readFromCSV(csvFile,listToWriteTo):
    with open(csvFile,'r') as f:
        csv_f = csv.reader(f)
        for row in csv_f:
            oneRowList = row[:]
            listToWriteTo.append(row)    

def sendEmail():

    sender = 'from@fromdomain.com'
    receivers = ['to@todomain.com']

    message = """From: From Person <jcarter@cpllabs.com>
    To: To Person <jamesabce12345@gmail.com>
    Subject: SMTP e-mail test
    
    This is a test e-mail message.
    """

#    try:
    smtpObj = smtplib.SMTP('casarray.cpllabs.com')
    smtpObj.sendmail(sender, receivers, message)         
#       print ("Successfully sent email")
#    except Exception:
#       print ("Error: unable to send email"    )

###listOfRows = sortTable(listOfRows)

def testCode():
    readFromCSV('phone_record.csv',listOfRows)
    removeFromTable(listOfRows)
    storeAutodialTable()
    mainProgPart()
    placeInBadDetailedList(badAutodialList)
    distributeToVariousLists(badAutodialsDetailed)
    prepareSalesEmail(badAutodialsDetailedToSales)
    for i in range(0,len(emailContactsList)):
        print(emailContactsList[i][emailContactsMessage])
    writeTestListToCSV(badAutodialsDetailedToSales)
    
def testCode2():
    readFromCSV('phone_record.csv',listOfRows)
    removeFromTable(listOfRows)
    storeAutodialTable()
    mainProgPart()
    placeInBadDetailedList(badAutodialList)
    distributeToVariousLists(badAutodialsDetailed)
    sortedBadAutodialsList = sorted(badAutodialsDetailedToSales, key=itemgetter(bList1RevCentColumn, bList1TerritoryColumn, bList1AGroupColumn, bList1ClientAcctNumberColumn))
    writeTestListToCSV(sortedBadAutodialsList)

######listStuff = []  #debug
#listOfRows = sortTable(listOfRows)
week_ago = todayDate - datetime.timedelta(days=7)
yesterday = todayDate - datetime.timedelta(days=1)



#################THis is the main program part ########################################
#################THis is the main program part ########################################
#################THis is the main program part ########################################
#run
#readFromCSV('phone_record.csv',listOfRows)
#removeFromTable(listOfRows)
#storeAutodialTable()
#mainProgPart()
#placeInBadDetailedList(badAutodialList)
#distributeToVariousLists(badAutodialsDetailed)
#writeTestListToCSV(badAutodialsDetailed)
################################################################################
################################################################################
################################################################################

#readFromCSV('phone_record.csv',listOfRows)
#removeFromTable(listOfRows)
#storeAutodialTable()
#mainProgPart()
#placeInBadDetailedList(badAutodialList)
#findAutodialsWithNoClients(badAutodialsDetailed)


#writeTestListToCSV(badAutodialsDetailedToIT)

######removeFromTable(listOfRows)
######mainProgPart()
######outputToCSV()
######appendBadListToCSV()
######print(badAutodialList)
######listOfRows.clear()
######storeAutodialTable()
######placeInBadDetailedList(badAutodialList)
######print("detailed list:")
######print(badAutodialsDetailed)
#print(dayList)
######print(len(badAutodialsDetailed))
######writeTestListToCSV(badAutodialList)
#sendEmail()
print("start of program")
#run
testCode()
print("end of program")

        
            
#111dayString = "9/01/2017"
#111#print(datetime.date.today()-5)
#111#dayFunct = time.strptime(dayString,"%m/%d/%Y")
#111dayFunct = date(
#111print(dayFunct)
#111stuff = (day - dayFunct)
#111print (stuff.days)

####dayString = "9/01/2017"
####dayStringDate = datetime.datetime.strptime(dayString,"%m/%d/%Y").date()
####print(dayStringDate)
####print(type(dayStringDate))
####print(type(day - dayStringDate))
####diff = day - dayStringDate
####print(diff.days)
####print(diff.days - 9)
####print(("5/5/16").date())
###for row in range(1,len(listOfRows)):
###    currentAutodialGroup = listOfRows[row][mainListAutodialRow]
###    while currentAutodialGroup != listOfRows[row-1][mainListAutodialRow]:
        #LOOK AT 7 days bacak and see if attempts made with no succss

        #look at all days until now and see if there was any success theree
        #see if attempt was made yestesrday
        

