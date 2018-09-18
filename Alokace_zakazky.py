import csv
import os

# vymery k jednotlivym zakazkam, podle kterych se bude provaddet alokace

RR_soubor='Rentroll_podklad.csv'

#-----------------------------------------------------------------------------'
def uprava_cisla(hodnota):
	try:
		return int(hodnota)	
	except ValueError:
		return float(hodnota.replace(',','.'))


# vytvori seznam zakazek a k nim nacte plochy a volnych bytu do slovniku

Zakazky_all=[]
SQM_total=0
Vacant_total=0


with open(RR_soubor, 'r', encoding='utf-8') as zakazky_source:
    zakazky_data = csv.reader(zakazky_source, delimiter=';', quotechar='|')
    next(zakazky_data)

    for row in zakazky_data:
    	SQM_upraveno= uprava_cisla(row[1])
    	Vacant_upraveno=uprava_cisla(row[2])
    	zakazka={'Zak':row[0], 'SQM':SQM_upraveno, 'Vacant':Vacant_upraveno}
    	Zakazky_all.append(zakazka)
    	SQM_total+=SQM_upraveno
    	Vacant_total+=Vacant_upraveno

# ke kazde zakazce prida podil na sqm a vacant
for zakazka in Zakazky_all:
	zakazka['Sqm_podil']=zakazka['SQM']/SQM_total
	zakazka['Vacant_podil']=zakazka['Vacant']/Vacant_total

#vytiskne kontrolni info k zakazkam

print('Celkovy pocet zakazek :',len(Zakazky_all))
print('Celkovy pocet sqm :', round(SQM_total,2))
print('Celkovy pocet volnych bytu :', Vacant_total)

#-----------------------------------------------------------------------------'

#nacteni a uprava SAP exportu do formatu pro import do BPC

#nacte do dataframe soubor za SAP 

import pandas
import numpy

zahlavi = ['Month','Year','Zak','Account','Amount','NS','PC','H5','H6',"Acctype"]

types = {'Month': numpy.str, 'Year': numpy.str,'Zak':numpy.str, 'Account': numpy.str, 'Amount': numpy.str, 'NS': numpy.str, 'PC': numpy.str, 'H5': numpy.str, 'H6': numpy.str, 'Acctype': numpy.str}

export = pandas.read_csv('SAP_export_zakazky.csv', sep=';', delimiter=None, skiprows=1, names=zahlavi, index_col=None, usecols=None, squeeze=False, prefix=None, mangle_dupe_cols=True, dtype=types, engine='python', converters=None, true_values=None, false_values=None, nrows=None, na_values=None, keep_default_na=True, na_filter=True, parse_dates=False, keep_date_col=False, date_parser=None, thousands=None, decimal=b'.', lineterminator=None, skipfooter=1, delim_whitespace=False, float_precision=None)

# uprava castky na desetinne misto
export['Amount'] = export['Amount'].str.replace(',','.')
export['Amount'] = export['Amount'].str.replace(' ','')
export['Amount'] = export['Amount'].astype(numpy.float64)

# uprava time

Month=export['Month']
if (len(Month[0])) == 1:
	export['Month'] = '0'+ export['Month']
else:
	export['Month']

export['Year'] = export['Year'].str.replace('20','')
export['Month'] = export.Month.astype(str).str.cat(export.Year.astype(str), sep='.')
export = export.drop('Year', 1)
export = export.rename(columns={'Month': 'Time'})

#nahrazeni EPM chyby ve sloupcich H5 a H6

export['H5'] = export['H5'].str.replace('The member requested does not exist in the specified hierarchy.','x')
export['H6'] = export['H6'].str.replace('The member requested does not exist in the specified hierarchy.','x')

# smazani sloupce NS

export = export.drop('NS', 1)

# pridani EPM dimenzi

export['IntCo'] = 'Non_Interco'
export['Currency'] = 'LC'
export['Measures'] = 'Periodic'
export['Entity'] = '0'+ export['PC'].str.get(0) + export['PC'].str.get(1)
export['Datasrc'] = numpy.where(export['Account'].str.get(0) == 'P', 'IFRS', numpy.where(export['Account'].str.get(0) == 'R', 'IFRS', 'REP'))

blank_zak = ['800000000','800000001','800000002','800000003','800000004','810000000','820000000','830000000','840000000']

export['Zak'] = numpy.where(export['Zak'].isin(blank_zak), 'nan', export['Zak'])

#duplicity na zaklade kombinace cisla zakazky a cisla uctu vyhazuji, pomijime PC, pro tento druh reportu nepodstatne

export['Amount'] = export.groupby(['Zak', 'Account'])['Amount'].transform('sum')

export.drop_duplicates(subset=['Zak', 'Account'], keep='first', inplace=True)

#-----------------------------------------------------------------------------'

#alokace upravene tabulky podle zpusobu alokace na zaklade podilu daneho klice na celkovych zakazkach

#pomocny sloupec pro alokace

conditions = [
    (export['Zak'] == 'nan') & (export['H6'].str.contains('JC09', na=False, regex=False) == True),
    (export['H5'] == 'VacC') & (export['Entity'] == '065'),
    (export['Zak'] == 'nan')]

klic = ['Vacant', 'VacC', 'Area']

export['Alokace'] = numpy.select(conditions, klic, default='OK')

#vytvoreni alokacni tabulky a jeji rozdeleni na ctyri casti podle zpusobu alokace
# tabulka VacC, ktera se dale nealokuje se rovnou ulozi do souboru VacC

Table_Alokace=pandas.DataFrame()
Table_Alokace=export.copy()

Table_VacC = pandas.DataFrame(columns=Table_Alokace.columns)
VacC_rows = Table_Alokace.loc[Table_Alokace['Alokace'] == 'VacC',:]
Table_VacC = Table_VacC.append(VacC_rows ,ignore_index=True)
Table_Alokace.drop(VacC_rows.index, inplace=True)
print('Tabulka VacC obsahuje',len(Table_VacC), 'zaznamu.')
Table_VacC.to_csv('VacC.csv')

Table_Zakazky =	pandas.DataFrame(columns=Table_Alokace.columns)
Zakazky_rows = Table_Alokace.loc[Table_Alokace['Alokace'] == 'OK',:]
Table_Zakazky = Table_Zakazky.append(Zakazky_rows ,ignore_index=True)
Table_Alokace.drop(Zakazky_rows.index, inplace=True)
print('Tabulka s primym uctovanim na zakazky obsahuje',len(Table_Zakazky), 'zaznamu.')

Table_Vacant = pandas.DataFrame(columns=Table_Alokace.columns)
Vacant_rows = Table_Alokace.loc[Table_Alokace['Alokace'] == 'Vacant',:]
Table_Vacant = Table_Vacant.append(Vacant_rows ,ignore_index=True)
Table_Alokace.drop(Vacant_rows.index, inplace=True)
print('Tabulka s ucty, ktere se alokuji podle volnych bytu, obsahuje',len(Table_Vacant), 'zaznamu.')

Table_Area = pandas.DataFrame(columns=Table_Alokace.columns)
Area_rows = Table_Alokace.loc[Table_Alokace['Alokace'] == 'Area',:]
Table_Area = Table_Area.append(Area_rows ,ignore_index=True)
Table_Alokace.drop(Area_rows.index, inplace=True)
print('Tabulka s ucty, ktere se alokuji podle zapocetene plochy, obsahuje',len(Table_Area), 'zaznamu.')

#-----------------------------------------------------------------------------'

# alokace jednotlivych tabulek podle seznamu podilu na zakazky a zapsani do souboru import.csv na konci kazdeho cyklu

#prazdna tabulka se zahlavim a zapsani zahlavi do souboru import.csv
Table_Import=pandas.DataFrame(columns=export.columns)

Table_Import.to_csv('Import.csv', mode='w', header=True)

#tabulka, ktera robnou obsahuje zakazky se do souboru zapisuje primo, neni potreba s ni dale pracovat
Table_Zakazky.to_csv('Import.csv', mode='a', header=False)

#pomocne tabulky pro zapis roalokovanych dat
Table_Area_help=pandas.DataFrame(columns=Table_Area.columns)
Table_Vacant_help=pandas.DataFrame(columns=Table_Vacant.columns)

#vypocet poctu zakazek, pro kontrolu a dalsi info o stavu zpracovani
pocet_zakazek=0

#vypocet celkovecastky, ktera byla rozalokovana a ulozena do souboru import
total_sum_Import = 0
total_sum_Import += Table_Zakazky['Amount'].sum()

for zakazka in Zakazky_all:
	Table_Area_help=Table_Area.copy()
	Table_Area_help['Zak']=Table_Area['Zak'].str.replace('nan',zakazka['Zak'])
	Table_Area_help['Datasrc']=(Table_Area['Datasrc']+'_ALOK')
	Table_Area_help['Amount']=round((Table_Area['Amount'] * zakazka['Sqm_podil']),3)
	Table_Area_help.to_csv('Import.csv', mode='a', header=False)
	total_sum_Import += Table_Area_help['Amount'].sum()
	
	if zakazka['Vacant']!=0:
		Table_Vacant_help=Table_Vacant.copy()
		Table_Vacant_help['Zak']=Table_Vacant['Zak'].str.replace('nan',zakazka['Zak'])
		Table_Vacant_help['Amount']=round((Table_Vacant['Amount'] * zakazka['Vacant_podil']),3)
		Table_Vacant_help.to_csv('Import.csv', mode='a', header=False)
		total_sum_Import += Table_Vacant_help['Amount'].sum()
	
	#vypis infa o aktualnim stavu alokace, abych vedela, ze se neco deje :)
	pocet_zakazek+=1
	if pocet_zakazek % 10 == 0:
		stav_zpracovani=int(pocet_zakazek)/len(Zakazky_all)*100
		print('Ucty k alokaci rozalokovany jiz na', pocet_zakazek, 'zakazek z', len(Zakazky_all), '. (', round(stav_zpracovani,2), '%)')
		

print('Alokace neprirazenych uctu na', pocet_zakazek,'zakazek dokoncena. (100%)')

# kontrola souctem tabulek
total_sum_export = export['Amount'].sum()
print(total_sum_export)

total_sum_Zakazky = Table_Zakazky['Amount'].sum()
total_sum_VacC = Table_VacC['Amount'].sum()
total_sum_Vacant = Table_Vacant['Amount'].sum()
total_sum_Area = Table_Area['Amount'].sum()
total_sum_help = total_sum_Area + total_sum_Vacant +total_sum_Zakazky + total_sum_VacC
print(total_sum_help)

total_sum_impVac = total_sum_Import + total_sum_VacC
print(total_sum_impVac)

