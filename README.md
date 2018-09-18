# ZakazkyAlokace
Cílem je rozlokovat účty, u kterých není uvedena zakázka a vygenerovat soubor, který je pak bez dalších úprav možný nahrát do BPC.

**Rentroll_podklad.csv**  
  * seznam zakazek s výměrou a počtem bytů   
  * podil každé zakázky na celku se použije jako alokaní procento  

**SAP_export_zakazky.csv**  
  * export účtů ze SAP  
  * obsahuje jak údaje s přímým účtováním na zakázky, tak i účty bez zakázky  
  
**Alokace_zakazky.py**  
  * vyvtoří slovník ze souboru Rentroll_podklad.csv, do kterého uloží jak skutečné tak i podílové hodnoty pro jednotlivé zakázky  
  * upraví jednotlivé sloupce v souboru SAP_export_zakazky.csv tak, aby odpovidaly dimenzim v BPC a při importu výsledného souboru nebylo potřeba již nic upravovat  
  * rozděli data ze souboru SAP_export_podklad.csv na čtyři samostatné tabulky podle klíče alokace uvedených ve sloupcích H5 a H6 původního souboru  
  * zapíše tabulku s klíčem VacC do samostatného souboru VacC.csv a s touto již dále nepracuje  
  * vytvoří soubor Import.csv, do kterého zapíše tabulku s účty přímo účtovnými na zakázky  
  * do souboru Import.csv dále zapisuje při každém cyklu alokaci nerozdělených účtů na aktuální zakázku podle podílů ve slovníku  
  * v průběhu vypisuje informační údaje pro kontrolu uživatele (např. počty zakázek, celkové součty částek v souborech, stav zpracování)  

