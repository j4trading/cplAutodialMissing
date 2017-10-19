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

# 08/22/2017
# This program takes the Kace extract which is in a given format and creates another csv extract which is in another format
# The input format has a row per IT item along with warranty info for that item and varying number of rows below it
# Program will output a csv extract with only one row per IT item with the Sonic headers for the columns and the desired warranty info selected
#This program takes a csv file and creates another csv file which has its data shifted around to be in another format
#It then calls a Windows batch script to actually place that created file into a directory in another server in another domain
#Both the file creation and the file move operations overwrite files of the same name.
#The following have to be in the same directory:
#1. Python script
#2. file mover windows batch file
#3. the input file that comes form KACE
#
#Also the following conditions must also be met:
#1. Python script will contain the name of the input file that comes from KACE
#2. Python script will contain the name of the output file that will be produced by it
#3. Python script will contain the name of the file mover Windows batch file
#4. Windows batch file will contain the following:
#	a. name of the output file produced by the Python script
#	b. it contains (for the Python script's output file) the destination directory along with the name that that file will have in that destination
#	c. login credentials for the destination directory to be able to copy files to it

#-----------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------

#This section reads the Kace extract and sticks all the info 'as is' into a list of lists (like list of rows)
with open('Footprints Export.csv','r') as f:
    csv_f = csv.reader(f)
    listOfRows = []
    oneRowList = []
    numberOfRows = 0
    numberOfColumns = 0
    rowIndex = 0
    tempCount = 0
    for row in csv_f:
#        print(row)
        oneRowList.clear()
        oneRowList = row[:]
        rowIndex += 1
        numberOfRows += 1
        tempCount += 1
        listOfRows.append(row)
#        if tempCount >= 12:       #debug
#            break                #debug


#This section will take the listOfRows created above (which is a replica of the Kace extract) and create another list of rows
#The new list of rows will be created by modifying the first listOfRows according to warranty info and such so there's only one list element (row) per item
#To do this the code needs to identify if the LOR row is begins an item or is just a warranty info row
#If it is a warranty info row then code needs to keep a running tally of the most future date of all the warranty info it has run across for that given computer/item

#This table shows Kace Extract column numbers associated with what the column represents
#columns 1 adn 2 show 2 different because they are stacked on top of eacch other per item
#columns 9 and 10 is where expiration date and active will be moved away from that atacked location.
dellWarrantyColumnKace =        0
nameAssetColumnKace =           1
serviceTagColumnKace =          2
systemManufacturerColumnKace =  3
systemModelColumnKace =         4
locationCityColumnKace =        5
ipColumnKace =                  6
nameOSColumnKace =              7
labelNamesColumnKace =          8
expirationDateColumnKace =      1       #
warrantyActiveColumnKace =      2
expirationDateNewColumn=        9
warrantyActiveNewColumn=        10

stringFoundKaceFlag = 0
warrantyDateList = []

#state of a row indicates if we're looking at the first row of an item/computer/etc... or if we're looking at warranty date or header that begins warranty info for that item/computer/etc..
#we have current AND previous state because the determine what state a row actually indicatese will also depend on what the state was for the previous row in the spreadsheet
previousState = 0	# state 0 means underfined....see table of states with their correspoding integer values below
currentState = 0

#the states
stateUndefined = 0
notWarrantyRowState = 1
warrantyHeaderState = 2
warrantyFirstDataState = 3
warrantySecondDataState = 4
stateDetermined = 0                 #this variable is probably not really doing anything in the code, but the code works right now

newListOfRows = []
newListRowNumber = 0
numberOfRowsForItem = 0             #keeping a running tally of how many rows a given computer/item is using as we run come across them in the kace extract spreadsheet...this variable is currently not having an effect I think
warrantyCurrentlyStored = ""
warrantyCurrentlyActiveStored = ""

numberOfColumnsKace = 11

#here we will just copy the header row of the entire spreadsheet
listTemp = [""]*numberOfColumnsKace    
newListOfRows.append(list(listTemp))
for itemIndex in range(0,len(listOfRows[0])):       #I have to 'copy' the first list this way because I dont  want to lose the 2 extra columns that newListOfRows has
    newListOfRows[0][itemIndex] = listOfRows[0][itemIndex]

newListOfRows[0][expirationDateNewColumn]="Warranty Expiration Date"
newListOfRows[0][warrantyActiveNewColumn] = "Warranty Expired or Active"

#This for loop determines what "state" a given spreadsheet row corresponds to and performs the corresponding action
for rowNumber in range(1, len(listOfRows)):
    stateDetermined = 0
    previousState = currentState
    cellString = listOfRows[rowNumber][dellWarrantyColumnKace]
    if (len(cellString) != 0) and (stateDetermined == 0):           #This is state that begins an item/computer in the kace spreadsheet. Here we copy stuff from the kace spreadsheet list to a new list.  Also we add warranty info accumulated from the last row over of the kace list over to the new list for the last item/computer
        currentState = notWarrantyRowState
        newListRowNumber += 1

        listTemp = [""]*numberOfColumnsKace    
        newListOfRows.append(list(listTemp))
        for itemIndex in range(0,len(listOfRows[rowNumber])):       #I have to 'copy' the first list this way because I dont  want to lose the 2 extra columns that newListOfRows has
            newListOfRows[newListRowNumber][itemIndex] = listOfRows[rowNumber][itemIndex]
        stateDetermined = 1

        numberOfRowsForItem = 0
        warrantyCurrentlyStored = ""
        warrantyCurrentlyActiveStored = ""

    if (len(cellString) == 0) and (previousState == notWarrantyRowState) and (stateDetermined == 0):        #header of warranty info in the kace spreadsheet...nothing really done here but needed to determine other warranty states
        currentState = warrantyHeaderState
        stateDetermined = 1

        numberOfRowsForItem += 1
        
        
    if (len(cellString) == 0) and (previousState == warrantyHeaderState) and (stateDetermined == 0):        #warranty info is accumulated here
        currentState = warrantyFirstDataState
        stateDetermined = 1

        numberOfRowsForItem += 1
        warrantyCurrentlyStored = listOfRows[rowNumber][expirationDateColumnKace]
        warrantyCurrentlyActiveStored = listOfRows[rowNumber][warrantyActiveColumnKace]
        
    if (len(cellString) == 0) and ((previousState == warrantyFirstDataState) or (previousState == warrantySecondDataState)) and (stateDetermined == 0):     #warranty info is accumulated here for the row and checked with what is already stored for the current computer/item.  Whether we want max or min date we keep the one we want.
        currentState = warrantySecondDataState
        stateDetermined = 1


        # strptime functions necessary to be able to compare date and times to see which one of 2 is more recent/older
        cellTempStringNew = str(listOfRows[rowNumber][expirationDateColumnKace])

        struct_time_new =time.strptime(cellTempStringNew,'%m/%d/%Y %H:%M:%S')
        cellTempStringOld = str(warrantyCurrentlyStored)


        struct_time_old =time.strptime(cellTempStringOld,'%m/%d/%Y %H:%M:%S')
        if warrantyCurrentlyStored == "":
            warrantyCurrentlyStored = listOfRows[rowNumber][expirationDateColumnKace]
            warrantyCurrentlyActiveStored = listOfRows[rowNumber][warrantyActiveColumnKace]
        else:
            if struct_time_new > struct_time_old:
                warrantyCurrentlyStored = listOfRows[rowNumber][expirationDateColumnKace]
                warrantyCurrentlyActiveStored = listOfRows[rowNumber][warrantyActiveColumnKace]


    #After having goen through all of these states we will go ahead and store warrantyCurrentlystored and warrantyActiveStored into the new list or rows
    #Will store these in if either we're at the last row of an item or at the last row of the entire original list of rows
    storeWarrantyInfoFlag = 0
    if (rowNumber + 1) >= (len(listOfRows)):
        storeWarrantyInfoFlag = 1
    if storeWarrantyInfoFlag == 0:      #we had to construct this this way because if we are the last row of original list of rows merely testing for index rowNumber+1 would crash the program
        if len(listOfRows[rowNumber+1][dellWarrantyColumnKace]) != 0:
            storeWarrantyInfoFlag = 1

    if storeWarrantyInfoFlag == 1:
        newListOfRows[newListRowNumber][expirationDateNewColumn] = warrantyCurrentlyStored
        newListOfRows[newListRowNumber][warrantyActiveNewColumn] = warrantyCurrentlyActiveStored
            
    stateDetermined = 0            
#    if rowNumber >= 10:       #debug
#        break                #debug



#with open('Footprints Export22.csv', "w", newline = '') as csv_file:
#     writer = csv.writer(csv_file, delimiter=',')
#     for line in newListOfRows:
#         writer.writerow(line)


#This section creates a list of rows which will be a replica of what we want the output extract to look like
#This will done simply by taking the list of rows created above and shuffling the columns around to what we want.
# To do so wwe will need another list of lists which is in order of how we want the columns to be sorted
# Each item of that list will be a list which for each column has both the header title for it and also what column it corresponds to in the original kace extract
# Then we run a double for loop (for row and then for columns for each row) in order to create outputList stuff in accordance with the list of lists with the column descriptions


#IGNORE: The following has all of the information for the new Output spreadsheet in this dictionary of lists
#IGNORE: For each column of the new spreadsheet the dictionary key is the description
#IGNORE: the value list has
#IGNORE:  1. new column number, and next it has column header name, and last it has what the corresponding Kace column name is
#IGNORE:  The column indices are a way to access the dictionary's list's elements without having to hard-code them throughout the program.

#outputColumnsDictionary =dict{assetNumberOutputList :          [0,"Asset #", nameAssetColumnKace]
#serialNumberOutputList :         [1,"Serial Number", serviceTagColumnKace]
#vendorOutputList :               [2,"Vendor", systemManufacturerColumnKace]
#desktopModelOutputList :         [3,"Desktop Model", systemModelColumnKace]
#locationOutputList :             [4,"Location", locationCityColumnKace]
#detailsOutputList :              [5,"Details", noneExisting]
#ipAddressOutputList :            [6,"IP Address", ipColumnKace]
#operatingSystemOutputList :      [7,"Operating System", nameOSColumnKace]
#configurationIDOutputList :      [8,"Configuration ID", noneExisting]
#invoiceDateOutputList :          [9,"Invoice Date", noneExisting]
#warrantyExpiryDateOutputList :   [10,"Warranty Expiry Date", expirationDateNewColumn]
#warrantyExpiredOutputList :      [11,"Warranty Expired", warrantyActiveNewColumn]
#poNumberOutputList :             [12,"PO #", noneExisting]
#invoiceNumberOutputList :        [13,"Invoice #", noneExisting]
#costCentreOutputList :           [14,"Cost Centre", noneExisting]
#purchasePriceOutputList :        [15,"Purchase Price", noneExisting]
#purchasingApprovedOutputList :   [16,"Purchasing Approved", noneExisting]
#statusOutputList :               [17,"Status", noneExisting]
#}

noneExisting = 999
columnHeaderIndex = 0
correspondingKaceColumnIndex = 1

outputColumnDescriptionList =   [
 ["Asset #", nameAssetColumnKace]
,["Serial Number", serviceTagColumnKace]
,["Vendor", systemManufacturerColumnKace]
,["Desktop Model", systemModelColumnKace]
,["Location", locationCityColumnKace]
,["Details", noneExisting]
,["IP Address", ipColumnKace]
,["Operating System", nameOSColumnKace]
,["Configuration ID", noneExisting]
,["Invoice Date", noneExisting]
,["Warranty Expiry Date", expirationDateNewColumn]
,["Warranty Expired", warrantyActiveNewColumn]
,["PO #", noneExisting]
,["Invoice #", noneExisting]
,["Cost Centre", noneExisting]
,["Purchase Price", noneExisting]
,["Purchasing Approved", noneExisting]
,["Status", noneExisting]
]

outputNumberOfColumns = len(outputColumnDescriptionList)
outputListOfRows = []

#Creating first row with the header title info
listTemp = [""]*outputNumberOfColumns    
outputListOfRows.append(list(listTemp))
for itemIndex in range(0,outputNumberOfColumns):
    outputListOfRows[0][itemIndex] = outputColumnDescriptionList[itemIndex][0]

#Creating rest of output list of rows
for rowIndex in range(1, len(newListOfRows)):
    listTemp = [""]*outputNumberOfColumns    
    outputListOfRows.append(list(listTemp))
    for columnIndex in range(0,outputNumberOfColumns):
        if (outputColumnDescriptionList[columnIndex][correspondingKaceColumnIndex]) != noneExisting:
            outputListOfRows[rowIndex][columnIndex] = newListOfRows[rowIndex][(outputColumnDescriptionList[columnIndex][correspondingKaceColumnIndex])]
        else:
            outputListOfRows[rowIndex][columnIndex] = ""

#new
with open('Footprints Export_Output_py.csv', "w", newline = '') as csv_file:
     writer = csv.writer(csv_file, delimiter=',')
     for line in outputListOfRows:
         writer.writerow(line)

#-------------------------------------------------------------
# This bunch here works for just using spart1
s1="SELECT CS_MODEL, "
s2="	MACHINE.IP, "
s3=""
s4="	(SELECT "
s5="		 group_concat(distinct   if(LABEL.NAME not like 'HDN_LABEL_%', LABEL.NAME, 'System Hidden') "
s6="		 separator '\\n') "
s7="		FROM MACHINE_LABEL_JT MLJT INNER JOIN LABEL ON MLJT.LABEL_ID = LABEL.ID WHERE MACHINE.ID = MLJT.MACHINE_ID ORDER BY LABEL.NAME) as LABEL_NAME, "
s8=""
s9="	OS_NAME, CSP_ID_NUMBER, CS_MANUFACTURER, "
s10="	ASSET.NAME AS ASSET_NAME, "
s11="	ASSET_LOCATION.NAME AS LOCATION, "
s12="	MACHINE.ID as TOPIC_ID, "
s13="	ifnull(MACHINE.ID,0) as SEED_COLUMN, "
s14="	DELL_WARRANTY.END_DATE, case when DW.ENDDATE < curdate() then 'Expired' else 'Active' end as DW_EXPIRED "
#S150="	MACHINE.ID as TOPIC_ID, "
s15= ""#"	GROUP_CONCAT(DISTINCT REPORT_TEMP.TT1.ROW ORDER BY REPORT_TEMP.TT1.ROW) AS PARENT_ROW "
s16=""
s17=""
s18="FROM MACHINE  "
s19="LEFT JOIN MACHINE_LABEL_JT ON (MACHINE_LABEL_JT.MACHINE_ID = MACHINE.ID)  "
s20="LEFT JOIN LABEL ON (LABEL.ID = MACHINE_LABEL_JT.LABEL_ID) "
s21="LEFT JOIN ASSET ON ASSET.MAPPED_ID = MACHINE.ID AND ASSET.ASSET_TYPE_ID=5 "
s22="LEFT JOIN ASSET ASSET_LOCATION ON ASSET_LOCATION.ID = ASSET.LOCATION_ID   "
s23=""
s24=""
s25="right join DELL_WARRANTY on MACHINE.BIOS_SERIAL_NUMBER = DELL_WARRANTY.SERVICE_TAG "
s26="right join (select @limitct :=0) T on 1=1   "
s27="right join (select max(END_DATE) ENDDATE, SERVICE_TAG as TAG, SERVICE_LEVEL_CODE as SVCCODE         "
s28="	from             DELL_WARRANTY DW group by SERVICE_TAG, SERVICE_LEVEL_CODE) "
s29=""
s30="DW \t\ton DW.TAG = DELL_WARRANTY.SERVICE_TAG and "
s31="	DW.SVCCODE = DELL_WARRANTY.SERVICE_LEVEL_CODE \t\t\tand DW.ENDDATE = DELL_WARRANTY.END_DATE "
s32=""#"JOIN REPORT_TEMP.TT1 ON (REPORT_TEMP.TT1.ID = MACHINE.ID)   "
s33=""
s34=""
s35=""
s36=""
s37=""
s38=""
s39=""
s40=""
s41=""
s42=""
s43=""
s44=""
s45=""
s46=""
s47="ORDER BY CS_MODEL "

#szzzzz="SELECT DELL_WARRANTY.END_DATE, case when DW.ENDDATE < curdate() then 'Expired' else 'Active' end as DW_EXPIRED, MACHINE.ID as TOPIC_ID, GROUP_CONCAT(DISTINCT REPORT_TEMP.TT1.ROW ORDER BY REPORT_TEMP.TT1.ROW) AS PARENT_ROW FROM DELL_WARRANTY left join MACHINE on MACHINE.BIOS_SERIAL_NUMBER = DELL_WARRANTY.SERVICE_TAG left join (select @limitct :=0) T on 1=1   left join (select max(END_DATE) ENDDATE, SERVICE_TAG as TAG, SERVICE_LEVEL_CODE as SVCCODE         from             DELL_WARRANTY DW group by SERVICE_TAG, SERVICE_LEVEL_CODE) DW \t\ton DW.TAG = DELL_WARRANTY.SERVICE_TAG and DW.SVCCODE = DELL_WARRANTY.SERVICE_LEVEL_CODE \t\t\tand DW.ENDDATE = DELL_WARRANTY.END_DATE JOIN REPORT_TEMP.TT1 ON (REPORT_TEMP.TT1.ID = MACHINE.ID)   GROUP BY DELL_WARRANTY.SERVICE_TAG,START_DATE,END_DATE ORDER BY END_DATE"
syyyyy = "SELECT * FROM KBSYS.DELL_CATALOG"





#-----------------------------------------------
#abc123
#This area is used as temporary sql trial:
#works fine and has all of the fields that we want.
#now I'm just trying to make it be put in order
#haven't done that yet
stemp1="SELECT ASSET.NAME AS ASSET_NAME,"
stemp2=""
stemp3="MACHINE.BIOS_SERIAL_NUMBER,"
stemp4="        CS_MANUFACTURER, "
stemp5="        CS_MODEL, "
stemp6="        ASSET_LOCATION.NAME AS LOCATION, "
stemp7=""
stemp8="        MACHINE.IP,"
stemp9="        OS_NAME, "
stemp10=""
stemp11="#     DELL_WARRANTY.START_DATE, #DELL_WARRANTY.END_DATE,"
stemp12="#     DELL_WARRANTY.ENTITLEMENT_TYPE,DELL_WARRANTY.ITEM_NUMBER, DELL_WARRANTY.SERVICE_LEVEL_CODE, "
stemp13="#     DELL_WARRANTY.SERVICE_LEVEL_GROUP, DELL_WARRANTY.SERVICE_PROVIDER, "
stemp14="#     DELL_WARRANTY.SERVICE_LEVEL_DESCRIPTION,"
stemp15=""
stemp16=""
stemp17="DELL_WARRANTY.END_DATE, case when DW.ENDDATE < curdate() then 'Expired' else 'Active' end as DW_EXPIRED,"
stemp18=""
stemp19="      "
stemp20=""
stemp21="     (SELECT "
stemp22="          group_concat(distinct   if(LABEL.NAME not like 'HDN_LABEL_%', LABEL.NAME, 'System Hidden') "
stemp23="          separator '\\n') "
stemp24="          FROM MACHINE_LABEL_JT MLJT INNER JOIN LABEL ON MLJT.LABEL_ID = LABEL.ID WHERE MACHINE.ID = MLJT.MACHINE_ID ORDER BY LABEL.NAME) as LABEL_NAME, "
stemp25=""
stemp26="     CSP_ID_NUMBER, "
stemp27=""
stemp28=""
stemp29="     MACHINE.ID as TOPIC_ID, "
stemp30="     ifnull(MACHINE.ID,0) as SEED_COLUMN "
stemp31=""
stemp32="     "
stemp33=""
stemp34="FROM MACHINE "
stemp35=""
stemp36=""
stemp37=""
stemp38="LEFT OUTER JOIN DELL_WARRANTY ON MACHINE.BIOS_SERIAL_NUMBER = DELL_WARRANTY.SERVICE_TAG "
stemp39=""
stemp40=" left join (select max(END_DATE) ENDDATE, SERVICE_TAG as TAG, SERVICE_LEVEL_CODE as SVCCODE "
stemp41=" from             DELL_WARRANTY DW group by SERVICE_TAG, SERVICE_LEVEL_CODE) "
stemp42=" DW \t\ton DW.TAG = DELL_WARRANTY.SERVICE_TAG and DW.SVCCODE = DELL_WARRANTY.SERVICE_LEVEL_CODE \t\t\tand DW.ENDDATE = DELL_WARRANTY.END_DATE "
stemp43=""
stemp44=""
stemp45="LEFT JOIN MACHINE_LABEL_JT ON (MACHINE_LABEL_JT.MACHINE_ID = MACHINE.ID)  "
stemp46="LEFT JOIN LABEL ON (LABEL.ID = MACHINE_LABEL_JT.LABEL_ID) "
stemp47="LEFT JOIN ASSET ON ASSET.MAPPED_ID = MACHINE.ID AND ASSET.ASSET_TYPE_ID=5 "
stemp48="LEFT JOIN ASSET ASSET_LOCATION ON ASSET_LOCATION.ID = ASSET.LOCATION_ID   "
stemp49=""
stemp50=""
stemp51=" LEFT JOIN (select @limitct :=0) T on 1=1 "
stemp52=" WHERE ((DELL_WARRANTY.SERVICE_LEVEL_DESCRIPTION LIKE '%Onsite%') OR (DELL_WARRANTY.SERVICE_LEVEL_DESCRIPTION LIKE '%ProSupport%') OR (DELL_WARRANTY.SERVICE_LEVEL_DESCRIPTION IS NULL)) "
stemp53=""
stemp54=" GROUP BY MACHINE.BIOS_SERIAL_NUMBER ,START_DATE,END_DATE"
stemp55=""
stemp56=" ORDER BY MACHINE.IP "


stotaltemp = stemp1+stemp2+stemp3+stemp4+stemp5+stemp6+stemp8+stemp9+stemp17+stemp21+stemp22+stemp23+stemp24+stemp26+stemp29+stemp30+stemp34+stemp38+stemp40+stemp41+stemp42+stemp45+stemp46+stemp47+stemp48+stemp50+stemp51+stemp52+stemp54+stemp56


#-----------------------------------------------
#Just Dell warranty part of the original query

stemp1="SELECT DELL_WARRANTY.END_DATE, case when DW.ENDDATE < curdate() then 'Expired' else 'Active' end as DW_EXPIRED, "
stemp2=" MACHINE.ID as TOPIC_ID "
#stemp3=" GROUP_CONCAT(DISTINCT REPORT_TEMP.TT1.ROW ORDER BY REPORT_TEMP.TT1.ROW) AS PARENT_ROW "
stemp3=""
stemp4=""
stemp5="FROM DELL_WARRANTY "
stemp6=""
stemp7="left join MACHINE on MACHINE.BIOS_SERIAL_NUMBER = DELL_WARRANTY.SERVICE_TAG "
stemp8="left join (select @limitct :=0) T on 1=1 "
stemp9=""
stemp10="left join (select max(END_DATE) ENDDATE, SERVICE_TAG as TAG, SERVICE_LEVEL_CODE as SVCCODE "
stemp11=" from DELL_WARRANTY DW group by SERVICE_TAG, SERVICE_LEVEL_CODE) "
stemp12=" DW \t\ton DW.TAG = DELL_WARRANTY.SERVICE_TAG and DW.SVCCODE = DELL_WARRANTY.SERVICE_LEVEL_CODE \t\t\tand DW.ENDDATE = DELL_WARRANTY.END_DATE "
stemp13=""
stemp14=""
#stemp15="JOIN REPORT_TEMP.TT1 ON f(REPORT_TEMP.TT1.ID = MACHINE.ID) "
stemp15=""
stemp16=""
stemp17="GROUP BY DELL_WARRANTY.SERVICE_TAG,START_DATE,END_DATE "
stemp18="ORDER BY END_DATE "

sDellOrig = stemp1+stemp2+stemp3+stemp5+stemp7+stemp8+stemp10+stemp11+stemp12+stemp15+stemp17+stemp18



#-----------------------------------------------
#Just Machine part of original query

stemp1="SELECT CS_MODEL, "
stemp2=" MACHINE.IP, "
stemp3=" (SELECT "
stemp4="  group_concat(distinct   if(LABEL.NAME not like 'HDN_LABEL_%', LABEL.NAME, 'System Hidden') "
stemp5="  separator '\\n') "
stemp6=" FROM MACHINE_LABEL_JT MLJT INNER JOIN LABEL ON MLJT.LABEL_ID = LABEL.ID WHERE MACHINE.ID = MLJT.MACHINE_ID ORDER BY LABEL.NAME) as LABEL_NAME, "
stemp7=""
stemp8=" OS_NAME, CSP_ID_NUMBER, CS_MANUFACTURER, "
stemp9=" ASSET.NAME AS ASSET_NAME, "
stemp10=" ASSET_LOCATION.NAME AS LOCATION, "
stemp11=" MACHINE.ID as TOPIC_ID, "
stemp12=" ifnull(MACHINE.ID,0) as SEED_COLUMN "
stemp13=""
stemp14="FROM MACHINE "
stemp15="LEFT JOIN MACHINE_LABEL_JT ON (MACHINE_LABEL_JT.MACHINE_ID = MACHINE.ID) "
stemp16="LEFT JOIN LABEL ON (LABEL.ID = MACHINE_LABEL_JT.LABEL_ID) "
stemp17="LEFT JOIN ASSET ON ASSET.MAPPED_ID = MACHINE.ID AND ASSET.ASSET_TYPE_ID=5 "
stemp18="LEFT JOIN ASSET ASSET_LOCATION ON ASSET_LOCATION.ID = ASSET.LOCATION_ID "

sMachineOrig = stemp1+stemp2+stemp3+stemp4+stemp5+stemp6+stemp8+stemp9+stemp10+stemp11+stemp12+stemp14+stemp15+stemp16+stemp17+stemp18

#-----------------------------------------------
# this here works wonderfully as it does the whole 1st sql half withoutth
#   any problem.
#   There we use the spart1 and query off of that.
saz = s1+s2+s3+s4+s5+s6+s7+s8+s9+s10
sbz = s11+s12+s13+s14+s15+s16
scz= s17+s18+s19+s20+s21+s22+s23+s24
sdz= s25+s26+s27+s28+s29+s30+s31+s32+s33+s34+s35+s36
sez= s37+s38+s39+s40+s41+s42+s43+s44+s45+s46+s47
szpart1 = saz+sbz+scz+sdz+sez

#-----------------------------------------------
####debug
#szpart1 = syyyyy
#-----------------------------------------------

#THis one is one we try to use the 2 sql parts together but where a double
#   quote sorrounds each part
#   It doesn't work.
##sa = s1+s2+s3+s4+s5+s6+s7+s8+s9+s10
##sb = s11+s12+s13+s14+s15+s16a
##
##spart1b = sa+sb
##
##sc=s170+s17+s18+s19+s20+s21+s22+s23
##sd = s24+s25+s26+s27+s28+s29+s30+s31+s32
##
##spart2 = sc+sd
##
##stotalb = spart1b + s16comma + spart2
#-----------------------------------------------
#print(stotalb)
#-------------------------------------------------------------

#-----------------------------------------------
# this here works wonderfully as it does the whole 1st sql half withoutth
#   any problem.
#   There we use the spart1 and query off of that.
##sa = s1+s2+s3+s4+s5+s6+s7+s8+s9+s10
##sb = s11+s12+s13+s14+s15+s16
##
##sc=s170b+s17+s18+s19+s20+s21+s22+s23
##sd = s24+s25+s26+s27+s28+s29+s30+s31+s32
##
##stotalc = sa + sb + s16comma + sc + sd
##
##print("stotalc is: ",stotalc)


#-----------------------------------------------


#new
#win32wnet.WNetAddConnection2(0, None, '\\\\'+host, None, username, password)
#shutil.copy(source_file, '\\\\'+host+dest_share_path+'\\')
#win32wnet.WNetCancelConnection2('\\\\'+host, 0, 0) # optional disconnect    


#debug#os.system('CSVFileMover.bat')
#print("end of program")
cnx = mysql.connector.connect(user='R1', password='box747',
                              host='10.148.1.18'
                              , database='ORG1')
cursor = cnx.cursor()
query = ("SELECT * FROM MACHINE LIMIT 10")
#####query = ("SELECT CS_MODEL, MACHINE.IP, (SELECT group_concat(distinct if(LABEL.NAME not like 'HDN_LABEL_%', LABEL.NAME, 'System Hidden') separator '\\n') FROM MACHINE_LABEL_JT MLJT INNER JOIN LABEL ON MLJT.LABEL_ID = LABEL.ID WHERE MACHINE.ID = MLJT.MACHINE_ID ORDER BY LABEL.NAME) as LABEL_NAME, OS_NAME, CSP_ID_NUMBER, CS_MANUFACTURER, ASSET.NAME AS ASSET_NAME, ASSET_LOCATION.NAME AS LOCATION, MACHINE.ID as TOPIC_ID, ifnull(MACHINE.ID,0) as SEED_COLUMN FROM MACHINE  LEFT JOIN MACHINE_LABEL_JT ON (MACHINE_LABEL_JT.MACHINE_ID = MACHINE.ID)  LEFT JOIN LABEL ON (LABEL.ID = MACHINE_LABEL_JT.LABEL_ID) LEFT JOIN ASSET ON ASSET.MAPPED_ID = MACHINE.ID AND ASSET.ASSET_TYPE_ID=5 LEFT JOIN ASSET ASSET_LOCATION ON ASSET_LOCATION.ID = ASSET.LOCATION_ID   GROUP BY MACHINE.ID ORDER BY CS_MODEL","SELECT DELL_WARRANTY.END_DATE, case when DW.ENDDATE < curdate() then 'Expired' else 'Active' end as DW_EXPIRED, MACHINE.ID as TOPIC_ID, GROUP_CONCAT(DISTINCT REPORT_TEMP.TT1.ROW ORDER BY REPORT_TEMP.TT1.ROW) AS PARENT_ROW FROM DELL_WARRANTY left join MACHINE on MACHINE.BIOS_SERIAL_NUMBER = DELL_WARRANTY.SERVICE_TAG left join (select @limitct :=0) T on 1=1   left join (select max(END_DATE) ENDDATE, SERVICE_TAG as TAG, SERVICE_LEVEL_CODE as SVCCODE         from             DELL_WARRANTY DW group by SERVICE_TAG, SERVICE_LEVEL_CODE) DW \t\ton DW.TAG = DELL_WARRANTY.SERVICE_TAG and DW.SVCCODE = DELL_WARRANTY.SERVICE_LEVEL_CODE \t\t\tand DW.ENDDATE = DELL_WARRANTY.END_DATE JOIN REPORT_TEMP.TT1 ON (REPORT_TEMP.TT1.ID = MACHINE.ID)   GROUP BY DELL_WARRANTY.SERVICE_TAG,START_DATE,END_DATE ORDER BY END_DATE")
#cursor.execute(szpart1)
cursor.execute(stotaltemp)
#cursor.execute(sDellOrig)
#cursor.execute(sMachineOrig)
#string1 = r.cursor.fetchone()


#debug....take this "with open stuff" for writing to file out once all works right
#only delete the lines that end with #debug
#####with open('testsql1.csv', "w", newline = '') as csv_file:  #debug
#####    writer2 = csv.writer(csv_file, delimiter=',')  #debug
#####    row = cursor.fetchone()
#####    writer2.writerow(row)  #debug
#####    #print(row)
#####    while row is not None:
#####        #print(row)
#####        row = cursor.fetchone()
#####        #print(cursor.fetchone())
#####    #for line in outputListOfRows:  #debug
#####        writer2.writerow(row)  #debug




#debug....take this "with open stuff" for writing to file out once all works right
#only delete the lines that end with #debug
with open('testsql1.csv', "w", newline = '') as csv_file:  #debug
    writer2 = csv.writer(csv_file, delimiter=',')  #debug
    row = cursor.fetchone()
#    writer2.writerow(row)  #debug
#####    #print(row)
    while row is not None:
        #print(row)
        writer2.writerow(row)  #debug
        row = cursor.fetchone()
#####        #print(cursor.fetchone())
#####    #for line in outputListOfRows:  #debug

         





#r = cnx.store_result()
#r.fetch_row()
cnx.close()

s1="abcd"
s2="efg"
s3=s1+s2
print(s3)

print("stotaltemp = ",stotaltemp)

print("end of program");#debug



#print("with task schelduer")

#documnet why you had the extra line output with writerow
#https://stackoverflow.com/questions/3191528/csv-in-python-adding-an-extra-carriage-return

#Also figure out how you should copy one properly a list to another like copying listOfRows[0] to newListOfRows[0]

#maybe consider using objects and classes

#DOCument about task scheduler stuff

#assert that the number of items in the kace extract I mean columns equals that constant
#speacial cases to test...have it have 3 or more warranty things...
#   put those 3 oro more also at the end  of file
#   put an item with no warranty at the end of file
#   put an item with 1 warranty at end of file

#document how path stuff for windows is done in python
#document about how python 3 would not use wb and why.. it's in that 
#stackoverflow deal
#don't forget to mention how file1.close() is unnecessary when using with as

# In the first section with numberOfColumnsKace = 11 I should refactor this as the number of kace extract columns could change....maybe you should make it more similar to the last section

#IS doing the following necesary?  Is there not a better way of doing this for mutable lists?:
#listTemp = [""]*numberOfColumnsKace newListOfRows.append(list(listTemp))

#document about time.strptime
