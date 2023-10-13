"""
Created on Mon Oct  2 16:02:58 2023

@author: Johnny
"""

#Instalar librerias que no trae python
#En el prompt de Anaconda: conda install package-name
#luego hacer la de reiniciar el kernel y poner pip install package-name en la consola

from datetime import datetime
import pandas as pd
#import numpy as np



def DeterminarCausas(fusionCodes, S4Codes, CopernicusReleaseDate, Timeline, CopernicusStatus, PhWEBStatus, Factory, CTR, LaunchDate, ERD, SEAssigned, ReportDate, LaunchChange):
    if Factory in fusionCodes:
        cause = "Fusion Factory Code"
    else: #El código de fábrica no es de Fusion
        if LaunchDate.year <2022 or CopernicusReleaseDate.year <2022:
            cause = "Platform Migration Issue"
        else: #El producto salió en 2022 o después
            if Timeline == "Hyper Options" or Timeline == "Hyper-ODM High Comp" or Timeline == "3PO-CFE":
                cause = "Autobahn SKU"
                
            elif "Storage" in Timeline:
                cause = "Storage SKU"
                
            else: #Timeline de Servers/Compute
                if CopernicusStatus == "OPEN":
                    cause= "Autobahn SKU"
                    
                elif CopernicusStatus == "CANCELLED":
                    if PhWEBStatus=="CANCEL":
                        cause = "SKU Cancelled; CANCEL in phWeb/RAS" 
                    elif PhWEBStatus=="OBS":
                        cause = "SKU Cancelled; OBS in phWeb/RAS" 
                    else: #Product went GA en una base de datos phweb/RAS = SUST
                        cause = "SKU Cancelled; product went GA and shows as SUST in phWeb/RAS" 
        
                elif CopernicusStatus == "INACTIVE":
                    if PhWEBStatus=="CANCEL":
                        cause = "SKU INACTIVE in Copernicus; CANCEL in phWeb/RAS" 
                    elif PhWEBStatus=="OBS":
                        cause = "SKU INACTIVE in Copernicus; OBS in phWeb/RAS" 
                    else: #Product went GA en una base de datos
                        cause = "SKU INACTIVE in Copernicus; product went GA and shows as SUST in phWeb/RAS" 
                    
                else: #Copernicus Status es Active
                    if Factory not in S4Codes:
                        cause = "No Factory code/Unknown Factory Code. Cause cannot be accurately determined"
                    else:
                        if CopernicusReleaseDate > ReportDate and LaunchDate < ReportDate:
                            cause = "Program release date changed - ERD wasn’t updated"
                        elif LaunchDate > ReportDate:
                            if LaunchChange == "Y":
                                cause = "Program moved to a future launch, ERD wasn't updated"
                            else: #El launchdate del programa es posterior al reporte pero no hubo cambio de launch
                                cause = "Program in future launch, ERD wasn't set up correctly"
                        else: #el date de launch es anterior al reporte (el producto debió haber salido ya) 
                            if Factory == "801M":
                                if SEAssigned == "Y":
                                    cause = "Chippewa Falls Factory - delayed CTR"
                                else:
                                    cause = "Chippewa Falls Factory - no SE assigned on Copernicus"
                                    
                            elif Factory == "401E":
                                if SEAssigned == "Y":
                                    cause = "Brazil factory - Copernicus doesn't have task to track this site"
                                else:
                                    cause = "Brazil factory - no SE assigned on Copernicus"
                            
                            elif Factory == "3J1D" or Factory == "3J1E" :
                                if SEAssigned == "Y":
                                    cause = "Japan Plant - delayed CTR"
                                else:
                                    cause = "Japan Plant - no SE assigned on Copernicus"
                            else: #La fábrica no es de las excepciones (CF, Brazil, Japon)
                                if CTR == "Y":
                                    if ERD == CopernicusReleaseDate:
                                        cause = "Program has CTR - ERD does align with its release date on Copernicus"
                                    else: #la ERD no se alinea con la release date
                                        cause = "Program has CTR - ERD doesn't align with its release date on Copernicus"
                                else: #el producto no ha hecho CTR
                                    if (abs(ReportDate - CopernicusReleaseDate)).days <= 15: #.days me tira la diferencia solo en cantidad de días, sino pongo .days me tira un formato que no es compatible con int
                                        cause = "Program hasn't CTR - within 15 days past release date"
                                    else: #Han pasado más de 15 días de cuando el producto debió de haber salido
                                        if ERD == CopernicusReleaseDate:
                                            cause = "Program hasn't CTR - ERD does align with its release date on Copernicus"
                                        else: #la ERD no se alinea con la release date
                                            cause = "Program hasn't CTR - ERD doesn't align with its release date on Copernicus"#el date de launch es anterior al reporte (el producto debió haber salido ya) 
                                              
    return cause


def EtiquetarDatos(df):
    
    
    
    
    return df.analisis

#Programa Principal
#Creo listas con los códigos de fábrica en S4 (base de datos actual) y los códigos usados en fusion (base de datos antigua)
fusionCodes = ["5200","5252","5223","5248","9010","S700","S7EM","H100","JK01","JK03","AC01","BF05","8O00","8SWE","Z400","XG01","EF00","G100","G111","G110","ER00","BF05","G101","32F2","33SC","33C1","0581","PD90"]
S4Codes = ["11BE", "1A1E", "12BE", "1B1E", "210E", "21BE", "302M", "401E", "801M", "220E", "22BE", "3C2E", "3J1E", "3C1E", "3J1D", "2H0E", "230E", "23BE", "29BE", "23AE", "2A0E", "2B0E", "2C0E", "2D0E", "2G0E", "290E", "8P2M", "802N", "8P1M", "1C0E", "1C2E", "1C9E", "1D1E", "3J2E", "804N"]


archivo = "PUNR overdue 20231005" #Nombre del archivo, esto puede cambiarse a un input
df = pd.read_excel(archivo+".xlsx") #Lee el archivo de excel y lo convierte en un dataframe
df["Cause"] = "" #Genera una columna para almacenar las causas en el dataframe
archivoSeparado = archivo.split(' ') #Separa el nombre del archivo usando el espacio como separador y mete esos valores en una lista
reportDateTexto = archivoSeparado[-1] #Agarra el último valor de la lista anterior y lo toma como fecha, para estos archivos el ultimo valor siempre es la fecha de generación del reporte
reportDate = datetime.strptime(reportDateTexto, "%Y%m%d") #cambia el texto de la fecha en una fecha en formato datetime
#print (reportDate)


#Hay que eliminar del reporte todos los bloqueos cuyo ERD es mayor a la fecha del reporte, es decir, hay que dejar solo los bloqueos cuya remoción está atrasada
df = df[df['Expected Resolution Date'] <= int(reportDateTexto)]


#Ciclo que lee las columnas del dataframe y determina la causa
for i in df.index:
    CopernicusReleaseDate = datetime.strptime(str(df.at[i,"Copernicus Release Date"]), "%Y%m%d.%f")
    Timeline = df.at[i,"Timeline"]
    CopernicusStatus = df.at[i,"Copernicus Status"]
    PhWEBStatus = df.at[i,"phWeb/RAS Status"]
    Factory = str(df.at[i,"Factory Plant"])
    CTR = df.at[i,"CTR"]
    LaunchDate = datetime.strptime(str(df.at[i,"Launch Date"]), "%Y%m%d.%f")
    ERD = datetime.strptime(str(df.at[i,"Expected Resolution Date"]), "%Y%m%d.%f")
    SEAssigned = df.at[i,"SE assigned"]
    LaunchChange = df.at[i,"Change of Launch"]
    
    cause = DeterminarCausas(fusionCodes, S4Codes, CopernicusReleaseDate, Timeline, CopernicusStatus, PhWEBStatus, Factory, CTR, LaunchDate, ERD, SEAssigned, reportDate, LaunchChange)
    df.at[i, "Cause"] = cause
        

df.to_excel('Resultados-Causas.xlsx', index=False) #Genera un archivo de excel con el nuevo dataframe que contiene las causas. 


"""
df = pd.read_excel('sample.xlsx')


df["cringe o basado"] = ""

print(df)


#df.algo[fila, columna] 

for i in df.index:
    alpha = df.at[i,"cars"]
    if alpha == "BMW":
        df.at[i, "cringe o basado"] = "apesta"
        print(alpha+" apesta") 
    else:
        df.at[i, "cringe o basado"] = "basado"
        print(alpha+" es basado")

print(df)

print(df["cringe o basado"].values)

df.to_excel('sample.xlsx', index=False)
"""

#puedo usar df.cars[i] o df.at[i,j]


"""
Fecha = "20231002"
d1 = datetime.strptime(Fecha, "%Y%m%d")
print(d1)
print(d1.year)
"""

"""
Fecha = "20231002"
d1 = datetime.strptime(Fecha, "%Y%m%d")
print(d1)
print(d1.year)
"""

"""
Timeline = "HPE Storage Disk Standard Setup"
if "Storage" in Timeline:
    print("lmao storage kekL")
else:
    (print("bASED"))
"""

"""
Fecha1 = "20231002"
d1 = datetime.strptime(Fecha1, "%Y%m%d")
d1A = date(d1.year, d1.month, d1.day)

Fecha2 = "20231015"
d2 = datetime.strptime(Fecha2, "%Y%m%d")

dif=abs(d2-d1)

print(dif.days)


if abs(dif.days) <= 15:
    print ("15 days grace period")
else:
    print("vas tarde papirrico")
"""
  

""" 
array = ["2C2E","3J1D","804N","401E","210E"]
if "210E" in array:
    print("Mexico we")
else:
    print ("Keep trying")
"""   