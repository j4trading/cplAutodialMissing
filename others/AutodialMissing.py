# works

import csv
import datetime
import time

#new
#import win32wnet
import shutil
import os

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
# Filter inhouse autodial groups, dummy groups.  Keep inactive autodial groups but call to my attention.  These will be emailed to me or someone in data or IT.
# Use monthly or weekly kbase flat files to get the revenue center, territory, client name, client number from the filtered bad autodial list above to email to correct regional managers

#-----------------------------------------------------------------------------------------------------
#    TO DO:

# we need to filter out undesirables like fax from inquiries using autodial group table which will be pulled from kbase on a monthly or weekly basis.
# test current functionaility
# do everything that follows after a rough "bad autodial list" is produced.

#index variable for overall list of lists
mainListAutodialRow = 0   
mainListDayRow = 1
mainListResponseRow = 4 
listOfRows = []         # multidimentional list produced from phone records file

#index variables for multidimentional list for single autodial group
dayListDayRow = 0
dayListResponseRow
dayList = []            # list for single autodial group

badAutodialList = []

todayDate = datetime.date.today()

def sortTable(listOfLists):
    #This sorts a table (a list of lists) and will return a table sorted out
    return sorted(listOfLists, key=itemgetter(0,1))

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
        
        

def checkDayForSuccess(dayList):
    """ Takes a list that holds a whole day's worth of phone records
        It outputs 0 if there was no success throughout that entire day"""
    successFlag = 0
    for i in dayList:
        if dayList[i][responseRow] == 10:
            successFlag = 1
            break
    return successFlag

def isBadAutodial(currentAutodial, dayList):
    """ This checks if it's a bad autodial.  IT's bad if
        there was activity for at least 7 days with no success therein
        We want to make sure there was activity at leasts 7 days ago so as to not catch autodial/autofax groups that were recently created in that time."""
    sevenDaysAgoActivityFlag = 0
    yesterdayAttemptedFlag = 0
    successEncounteredFlag = 0
    #look 7 days back
    week_ago = todayDate - datetime.timedelta(days=7)
    yesterday = todayDate - datetime.timedelta(days=1)
    for i in dayList:
        thisDay = datetime.datetime.strptime(dayList[i][dayListDayRow],"%m/%d/%Y").date()
        if thisDay == week_ago:
            sevenDaysAgoActivityFlag = 1
        if (thisDay == yesterday):
            yesterdayAttemptedFlag = 1
        if dayList[i][dayListResponseRow] == 10:
            successEncounteredFlag = 1
    if sevenDaysAgoActivityFlag == 1 and yesterdayAttemptedFlag == 1 and successEncounteredFlag == 0:
        return 1
    else
        return 0

def badAutodialProcedure(badAutodialList):
    """ finds the client name, client number for a given autodial/autofax group
        It it's a dummy groups, inhouse groups, or inactive group it sends a special email to me.
        If it's a autodial (CPL printer) or autofax group (inactive or not) it finds the revenue center and territory name.
        It then uses that to send an email to the corresponding regional manager including the clients names and account numbers
        If it's an inactive group it will send an email to me too."""
    pass

with open('Phone_record.csv','r') as f:
    csv_f = csv.reader(f)
    for row in csv_f:
        oneRowList = row[:]
        listOfRows.append(row)

###listOfRows = sortTable(listOfRows)

sortTable(listOfRows)

newAutodialFlag = 1
newDateFlag = 1
dayList.clear()
for row in range(1,len(listOfRows)):
    if row == 1:
        currentAutodial = listOfRows[row][mainListAutodialRow]
        newAutodialFlag = 0
        dayList.append(list(listOfRows[row][mainListDayRow],listOfRows[row][mainListResponseRow]))
        newDateFlag = 0

    else:
        if (listOfRows[row][mainListAutodialRow] != listOfRows[row-1][mainListAutodialRow]) and (row != 1):
            newAutodialFlag = 1
            newDateFlag = 1
        else:
            dayList.append(list(listOfRows[row][mainListDayRow],listOfRows[row][mainListResponseRow]))

        if newAutodialFlag == 1:
            if isBadAutodial(currentAutodial,dayList):
                badAutodialList.append(currentAutodial)
            currentAutodial = listOfRows[row][mainListAutodialRow]
            newAutodialFlag = 0
            dayList.clear()
            dayList.append(list(listOfRows[row][mainListDayRow],listOfRows[row][mainListResponseRow]))
            newDateFlag = 0
        
            
#111dayString = "9/01/2017"
#111#print(datetime.date.today()-5)
#111#dayFunct = time.strptime(dayString,"%m/%d/%Y")
#111dayFunct = date(
#111print(dayFunct)
#111stuff = (day - dayFunct)
#111print (stuff.days)

dayString = "9/01/2017"
dayStringDate = datetime.datetime.strptime(dayString,"%m/%d/%Y").date()
print(dayStringDate)
print(type(dayStringDate))
print(type(day - dayStringDate))
diff = day - dayStringDate
print(diff.days)
print(diff.days - 9)
print(("5/5/16").date())
###for row in range(1,len(listOfRows)):
###    currentAutodialGroup = listOfRows[row][mainListAutodialRow]
###    while currentAutodialGroup != listOfRows[row-1][mainListAutodialRow]:
        #LOOK AT 7 days bacak and see if attempts made with no succss

        #look at all days until now and see if there was any success theree
        #see if attempt was made yestesrday
        

