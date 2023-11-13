from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import string
from matplotlib.ticker import PercentFormatter
import plotly.express as px
import plotly.io as pio
from scipy import stats

def DeterminarCausas(fusionCodes, S4Codes, CopernicusReleaseDate, Timeline, CopernicusStatus, PhWEBStatus, Factory, CTR, LaunchDate, ERD, SEAssigned, ReportDate, LaunchChange):
    if Factory in fusionCodes:
        cause = "Fusion Factory Code"
    else: #El código de fábrica no es de Fusion
        if (LaunchDate.year <2022 and LaunchDate.year >2000) or (CopernicusReleaseDate.year <2022 and CopernicusReleaseDate.year >2000): #Se agrega que sea mayor a 2000 porque para programas cancelados o inactivos se mueven a lanzamientos con fecha de 1999
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
                        cause = "SKU Inactive in Copernicus; CANCEL in phWeb/RAS" 
                    elif PhWEBStatus=="OBS":
                        cause = "SKU Inactive in Copernicus; OBS in phWeb/RAS" 
                    else: #Product went GA en una base de datos
                        cause = "SKU Inactive in Copernicus; product went GA and shows as SUST in phWeb/RAS" 
                    
                else: #Copernicus Status es Active
                    if Factory not in S4Codes:
                        cause = "No Factory code/Unknown Factory Code. Cause cannot be accurately determined"
                    else:
                        if CopernicusReleaseDate > ReportDate and LaunchDate < ReportDate:
                            cause = "Program release date changed - ERD wasn’t updated"
                        elif LaunchDate > ReportDate:
                            if LaunchChange == "Y":
                                cause = "Program moved to a future launch, ERD wasn't updated"
                            else: #El launch date del programa es posterior al reporte pero no hubo cambio de launch
                                cause = "Program in future launch, ERD wasn't set up correctly"
                        else: #el date de release es anterior al reporte (el producto debió haber salido ya) 
                            if Factory == "801M":
                                if SEAssigned == "Y":
                                    cause = "Chippewa Falls Factory - delayed CTR"
                                else:
                                    cause = "Chippewa Falls Factory - no SE assigned on Copernicus"
                                    
                            elif Factory == "401E":
                                if SEAssigned == "Y":
                                    cause = "Brazil factory - delayed CTR"
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

#Función que agrega información necesaria para la agrupación y posterior graficación de los datos
def CategorizarDatos(FactoryCode, AMSFactory, EMEAFactory, APJFactory, Cause, ERD_Causes, Status_Causes, ExceptionPlants_Causes, Other_Causes):
    if FactoryCode in AMSFactory:
        Region = 'AMS'
        if FactoryCode == '21BE' or FactoryCode == '210E':
            Factory = 'FMX'
        elif FactoryCode == '22BE' or FactoryCode == '220E':
            Factory = 'IMX'
        else:
            pass
        
    elif FactoryCode in EMEAFactory:
        Region = 'EMEA'
        if FactoryCode == '1A1E' or FactoryCode == '11BE':
            Factory = 'FCZ'
        elif FactoryCode == '1B1E' or FactoryCode == '12BE':
            Factory = 'ICZ'
        else:
            pass
        
    elif FactoryCode in APJFactory:
        Region = 'APJ'
        if FactoryCode == '302M':
            Factory = 'EMAP'
        elif FactoryCode == '3C2E' or FactoryCode == '3C1E':
            Factory = 'HPE China'
        else:
            pass
    else: #Para esta parte se deja Region vacio ya que estas fábricas no importan para los análisis de gráficos referentes a regiones
        if FactoryCode == '801M':
            Region =''
            Factory = 'CF'
        elif FactoryCode == '401E':
            Region =''
            Factory = 'BRZ'
        elif FactoryCode == '3J1D' or FactoryCode == '3J1E': 
            Region =''
            Factory = 'JPN'
        else:
            Region =''
            Factory = ''
    
    #EXPLICAR PORQUE SOLO SE TOMAN ESTAS FÁBRICAS
    
    if Cause in ERD_Causes:
       cause_type = 'ERD related' 
        
    elif Cause in Status_Causes:
        cause_type = 'Status related'
             
    elif Cause in ExceptionPlants_Causes:
        cause_type = 'Special Plant related (CF, Japan, Brazil)'
        
    elif Cause in Other_Causes:
        cause_type = 'Other causes'
    
    
    return Region, Factory, cause_type



#Programa Principal
#Creo listas con los códigos de fábrica en S4 (base de datos actual) y los códigos usados en fusion (base de datos antigua)
fusionCodes = ["5200","5252","5223","5248","9010","S700","S7EM","H100","JK01","JK03","AC01","BF05","8O00","Z400","XG01","EF00","G100","G111","G110","ER00","BF05","G101","32F2","33SC","33C1","0581","PD90"]
S4Codes = ["11BE", "1A1E", "12BE", "1B1E", "210E", "21BE", "302M", "401E", "801M", "220E", "22BE", "3C2E", "3J1E", "3C1E", "3J1D", "2H0E", "230E", "23BE", "29BE", "23AE", "2A0E", "2B0E", "2C0E", "2D0E", "2G0E", "290E", "8P2M", "802N", "8P1M", "1C0E", "1C2E", "1C9E", "1D1E", "3J2E", "804N"]

#"PUNR overdue 20231005"
#LINEA QUE CARGA EL ARCHIVO EN BASE AL NOMBRE DE ESTE
archivo = "PUNR overdue 20231005" #Nombre del archivo, esto puede cambiarse a un input
archivoSeparado = archivo.split(' ') #Separa el nombre del archivo usando el espacio como separador y mete esos valores en una lista
reportDateTexto = archivoSeparado[-1] #Agarra el último valor de la lista anterior y lo toma como fecha, para estos archivos el ultimo valor siempre es la fecha de generación del reporte
reportDate = datetime.strptime(reportDateTexto, "%Y%m%d") #cambia el texto de la fecha en una fecha en formato datetime
df = pd.read_excel(archivo+".xlsx") #Lee el archivo de excel y lo convierte en un dataframe
df["Cause"] = "" #Genera una columna para almacenar las causas en el dataframe
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
        
nombre_excel = 'Results_Causes_' + reportDateTexto + '.xlsx'
df.to_excel(nombre_excel, index=False) #Genera un archivo de excel con el nuevo dataframe que contiene las causas. 


#Gráficos de datos


#Categorización extra de los datos para la graficación
#Se categorizan los datos en Region y Fábrica (para una misma fábrica pueden haber 2 codigos de fábrica distintos, por lo que es necesario que ambos caigan a una misma categoría)
df['Region'] = ''
df['Factory'] = ''
df['Cause type'] = ''

AMSFactory = ['220E', '22BE', '210E', '21BE']
EMEAFactory = ['1A1E', '11BE', '1B1E', '12BE']
APJFactory = ['302M', '3C2E', '3C1E']

ERD_Causes = ["Program hasn't CTR - within 15 days past release date", "Program release date changed - ERD wasn’t updated", "Program moved to a future launch, ERD wasn't updated", "Program in future launch, ERD wasn't set up correctly", "Program has CTR - ERD does align with its release date on Copernicus", "Program has CTR - ERD doesn't align with its release date on Copernicus", "Program hasn't CTR - ERD does align with its release date on Copernicus", "Program hasn't CTR - ERD doesn't align with its release date on Copernicus"]
Status_Causes = ["SKU Cancelled; CANCEL in phWeb/RAS","SKU Cancelled; OBS in phWeb/RAS", "SKU Cancelled; product went GA and shows as SUST in phWeb/RAS", "SKU Inactive in Copernicus; CANCEL in phWeb/RAS", "SKU Inactive in Copernicus; OBS in phWeb/RAS", "SKU Inactive in Copernicus; product went GA and shows as SUST in phWeb/RAS"]
ExceptionPlants_Causes = ["Chippewa Falls Factory - delayed CTR", "Chippewa Falls Factory - no SE assigned on Copernicus", "Brazil factory - delayed CTR", "Brazil factory - no SE assigned on Copernicus", "Japan Plant - delayed CTR", "Japan Plant - no SE assigned on Copernicus"]
Other_Causes = ["Fusion Factory Code", "Platform Migration Issue", "Autobahn SKU", "Storage SKU", "No Factory code/Unknown Factory Code. Cause cannot be accurately determined"]

for i in df.index:
    FactoryCode = str(df.at[i,"Factory Plant"])
    Cause = df.at[i, "Cause"]
    Resultados = CategorizarDatos(FactoryCode, AMSFactory, EMEAFactory, APJFactory, Cause, ERD_Causes, Status_Causes, ExceptionPlants_Causes, Other_Causes)
    df.at[i, "Region"] = Resultados[0]
    df.at[i, "Factory"] = Resultados[1]
    df.at[i, "Cause type"] = Resultados[2]



#Gráficos

################################################   Gráfico de barras: frecuancia de cada causa
df_barras = df['Cause'].value_counts()
#print(df_barras)
df_barras=df_barras.reset_index(level='Cause').rename(columns={'Cause': 'Causes', 'count': 'Count'})
#print(df_barras)

ax=df_barras.plot.barh(x='Causes', color = 'steelblue', figsize=(10,8))
plt.grid(axis='x')

#Código para generar etiquetas del eje
valores_x=df_barras['Count'].values.tolist()
valores_x.sort()
#print(valores_x)
num_etiquetas = 20
espaciado_entre_etiquetas = max(valores_x) / (num_etiquetas - 1)
xticks = np.around(np.linspace(0, max(valores_x) + 10, num_etiquetas))
plt.xticks(xticks)

#Agregar los valores individuales a cada barra
for p in ax.patches:
    ax.annotate("%.0f" % p.get_width(), (p.get_x() + p.get_width(), p.get_y()), xytext=(2, 0), textcoords='offset points')

ax.get_legend().remove()
plt.title('Overdue PUNR holds by cause')
plt.xlabel('Frequency')
plt.show()



################################################  Gráfico circular: proporcion de las causas por región
df_pie = df['Region'].value_counts()
#print(df_pie)
df_pie=df_pie.reset_index(level='Region').rename(columns={'Region': 'Region', 'count': 'Cantidad'})
df_pie= df_pie[df_pie['Region'] != '']  #Filtra los valores que no tienen nada (fábricas especiales)
#print(df_pie)

datos = df_pie['Cantidad']


#Función para que salga en el gráfico tanto el porcentaje como el valor numérico
def etiqueta_porcentaje(val):
    cantidad_numerica = int(val/100.*datos.sum())
    return f'{val:.1f}%\n({cantidad_numerica})'


total = len(datos)
plt.pie(datos, autopct=etiqueta_porcentaje, startangle=140)
plt.legend(df_pie['Region'], title='Regions', loc='upper right')
plt.axis('equal')
plt.title('Overdue PUNR holds by region')
plt.show()




################################################  Treemap para ver distribución de causas


d={'Region': df['Region'], 'Factory': df['Factory'], 'Cause': df['Cause']}
df_TM = pd.DataFrame(d)
df_TM=df_TM[df_TM['Region'] != '']
#print(df_TM)
df_TM=df_TM.groupby(['Region', 'Factory']).size().reset_index()
df_TM.columns = ['Region', 'Factory', 'count']
#print(df_TM)


fig = px.treemap(df_TM, path=[px.Constant("All regions"),'Region', 'Factory'], values='count')
fig.update_traces(root_color="lightgrey")
fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))

fig.update_traces(texttemplate='%{label}: %{value}')

fig.layout.hovermode = False

# Add a title
fig.update_layout(title='Distribution of overdue PUNR holds by region and factory')

pio.renderers.default='svg' #cambiar por 'browser' para ver en el navegador
fig.show()


################################################   gráfico de barras apiladas: tipo de causa en cada fábrica, para cada región

#####################    AMS
d={'Region': df['Region'], 'Factory': df['Factory'], 'Cause type': df['Cause type'], 'Cause': df['Cause']}
df_SB_AMS = pd.DataFrame(d)
df_SB_AMS=df_SB_AMS[df_SB_AMS['Cause type'] != 'Other causes']
df_SB_AMS=df_SB_AMS[df_SB_AMS['Region'] == 'AMS']
df_SB_AMS=df_SB_AMS.groupby(['Factory', 'Cause type']).count()

pivot = pd.pivot_table(data=df_SB_AMS, index=['Factory'], columns=['Cause type'], values='Cause')
pivot = pivot.reset_index()
#print(pivot)

ax = pivot.plot(kind = 'bar', rot= 0, stacked= True)
plt.grid(axis='y')

categorias = pivot['Factory']
valor1 = pivot['ERD related']
valor2 = pivot['Status related']
posiciones = range(len(categorias))

ax.set_xticks(posiciones)
ax.set_xticklabels(categorias)

ancho_barras = 0.35

# Crear las barras apiladas
bar1 = ax.bar(posiciones, valor1, width=ancho_barras, label='Valor1')
bar2 = ax.bar(posiciones, valor2, width=ancho_barras, label='Valor2', bottom=valor1)


# Agregar etiquetas de datos en cada barra
for bar, val1, val2 in zip(bar1, valor1, valor2):
    ax.text(bar.get_x() + bar.get_width() / 2, val1 / 2, str(int(val1)), ha='center', va='center')
    ax.text(bar.get_x() + bar.get_width() / 2, val1 + val2 / 2, str(int(val2)), ha='center', va='center')



plt.title('Amount of ERD and Status related overdue PUNR holds for AMS region by factory')
plt.xlabel('Factory')
plt.ylabel('Frequency')
plt.show()

#####################    EMEA
d={'Region': df['Region'], 'Factory': df['Factory'], 'Cause type': df['Cause type'], 'Cause': df['Cause']}
df_SB_EMEA = pd.DataFrame(d)
df_SB_EMEA=df_SB_EMEA[df_SB_EMEA['Cause type'] != 'Other causes']
df_SB_EMEA=df_SB_EMEA[df_SB_EMEA['Region'] == 'EMEA']
df_SB_EMEA=df_SB_EMEA.groupby(['Factory', 'Cause type']).count()


pivot = pd.pivot_table(data=df_SB_EMEA, index=['Factory'], columns=['Cause type'], values='Cause')
pivot = pivot.reset_index()
#print(pivot)

ax = pivot.plot(kind = 'bar', rot= 0, stacked= True)
plt.grid(axis='y')

categorias = pivot['Factory']
valor1 = pivot['ERD related']
valor2 = pivot['Status related']
posiciones = range(len(categorias))

ax.set_xticks(posiciones)
ax.set_xticklabels(categorias)

ancho_barras = 0.35

# Crear las barras apiladas
bar1 = ax.bar(posiciones, valor1, width=ancho_barras, label='Valor1')
bar2 = ax.bar(posiciones, valor2, width=ancho_barras, label='Valor2', bottom=valor1)


# Agregar etiquetas de datos
for bar, val1, val2 in zip(bar1, valor1, valor2):
    ax.text(bar.get_x() + bar.get_width() / 2, val1 / 2, str(int(val1)), ha='center', va='center')
    ax.text(bar.get_x() + bar.get_width() / 2, val1 + val2 / 2, str(int(val2)), ha='center', va='center')

plt.title('ERD and Status related overdue PUNR holds for EMEA region by factory')
plt.xlabel('Factory')
plt.ylabel('Frequency')
plt.show()

#####################    APJ
d={'Region': df['Region'], 'Factory': df['Factory'], 'Cause type': df['Cause type'], 'Cause': df['Cause']}
df_SB_APJ = pd.DataFrame(d)
df_SB_APJ=df_SB_APJ[df_SB_APJ['Cause type'] != 'Other causes']
df_SB_APJ=df_SB_APJ[df_SB_APJ['Region'] == 'APJ']
df_SB_APJ=df_SB_APJ.groupby(['Factory', 'Cause type']).count()


pivot = pd.pivot_table(data=df_SB_APJ, index=['Factory'], columns=['Cause type'], values='Cause')
pivot = pivot.reset_index()
#print(pivot)

ax = pivot.plot(kind = 'bar', rot= 0, stacked= True)
plt.grid(axis='y')

categorias = pivot['Factory']
valor1 = pivot['ERD related']
valor2 = pivot['Status related']
posiciones = range(len(categorias))

ax.set_xticks(posiciones)
ax.set_xticklabels(categorias)

ancho_barras = 0.35

# Crear las barras apiladas
bar1 = ax.bar(posiciones, valor1, width=ancho_barras, label='Valor1')
bar2 = ax.bar(posiciones, valor2, width=ancho_barras, label='Valor2', bottom=valor1)


# Agregar etiquetas de datos
for bar, val1, val2 in zip(bar1, valor1, valor2):
    ax.text(bar.get_x() + bar.get_width() / 2, val1 / 2, str(int(val1)), ha='center', va='center')
    ax.text(bar.get_x() + bar.get_width() / 2, val1 + val2 / 2, str(int(val2)), ha='center', va='center')
 
plt.title('ERD and Status related overdue PUNR holds for APJ region by factory')
plt.xlabel('Factory')
plt.ylabel('Frequency')
plt.show()
    

################################################ Barras agrupadas: Información anterior pero para cada región
d={'Region': df['Region'], 'Cause': df['Cause'], 'Cause type': df['Cause type']}
df_GB = pd.DataFrame(d)
df_GB=df_GB[df_GB['Region'] != ''] #Esto filtra las fábricas especiales
df_GB=df_GB[df_GB['Cause type'] != 'Other causes'] #Esto filtra other causes para que solo queden Status y ERD related

df_GB=df_GB.groupby(['Region', 'Cause type']).count()

pivot = pd.pivot_table(data=df_GB, index=['Region'], columns=['Cause type'], values='Cause')

ax = pivot.plot(kind = 'bar', rot= 0)
plt.grid(axis='y')

for container in ax.containers:
    ax.bar_label(container)

plt.title('ERD and Status related overdue PUNR holds in each region')
plt.ylabel('Frequency')

plt.show()

################################################   #Gráfico de treemap: Distribución de causas ERD y Status relared en las fábricas por region


d={'Region': df['Region'], 'Factory': df['Factory'], 'Cause': df['Cause'], 'Cause type': df['Cause type']}
df_TM = pd.DataFrame(d)
df_TM=df_TM[df_TM['Region'] != '']
df_TM=df_TM[df_TM['Cause type'] != 'Other causes']
#print(df_TM)
df_TM=df_TM.groupby(['Region', 'Factory', 'Cause type']).size().reset_index()
df_TM.columns = ['Region', 'Factory', 'Cause type', 'count']
#print(df_TM)


fig = px.treemap(df_TM, path=[px.Constant("All regions"),'Region', 'Factory', 'Cause type'], values='count')
fig.update_traces(root_color="lightgrey")
fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
fig.update_traces(texttemplate='%{label}: %{value}')

fig.layout.hovermode = False

#Agregar titulo
fig.update_layout(title='Distribution of ERD and Status related causes by region and factory')

pio.renderers.default='svg' #cambiar por 'browser' para ver en el navegador
fig.show()



################################################   Gráfico para las fábricas especiales/excepciones.

d={'Factory': df['Factory'], 'Cause': df['Cause'], 'Cause type': df['Cause type']}
df_exp = pd.DataFrame(d)
df_exp=df_exp[df_exp['Cause type'] == 'Special Plant related (CF, Japan, Brazil)']
#print(df_exp)

for i in df_exp.index:
    if 'no SE assigned on Copernicus' in df_exp.at[i,'Cause']:
        df_exp.at[i, 'Cause type'] = 'No SE assigned'
    else:
        df_exp.at[i, 'Cause type'] = 'Delayed CTR'

df_exp=df_exp.groupby(['Factory', 'Cause type']).count()
#print(df_exp)

pivot = pd.pivot_table(data=df_exp, index=['Factory'], columns=['Cause type'], values='Cause')
#print(pivot)

ax = pivot.plot(kind = 'bar', rot= 0)
plt.grid(axis='y')

for container in ax.containers:
    ax.bar_label(container)

plt.title('Overdue PUNR holds in special plants by factory')
plt.ylabel('Frequency')

plt.show()




################################################   #Gráfico de treemap: Distribución de Autobahn y Storage Causes por Región (Son las 2 causas más importantes en other causes)

d={'Factory': df['Factory'], 'Cause': df['Cause'], 'Cause type': df['Cause type']}
df_TM2 = pd.DataFrame(d)
df_TM2=df_TM2[df_TM2['Factory'] != '']
df_TM2=df_TM2[df_TM2['Cause type'] == 'Other causes']
val_filter = ['Autobahn SKU', 'Storage SKU']
df_TM2=df_TM2[df_TM2['Cause'].isin(val_filter)] #Filtra para solo ver los datos de las causas en val_filter
df_TM2 = pd.DataFrame({'Factory': df_TM2['Factory'], 'Cause': df_TM2['Cause']})  #Ya no necesito causetype entonces hago un df sin esta columna
#print(df_TM2)


df_TM2=df_TM2.groupby(['Factory', 'Cause']).size().reset_index()
df_TM2.columns = ['Factory', 'Cause', 'count']
#print(df_TM2)


fig = px.treemap(df_TM2, path=[px.Constant("All factories"), 'Factory', 'Cause'], values='count')
fig.update_traces(root_color='lightgrey')
fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))

fig.update_traces(texttemplate='%{label}: %{value}')

fig.layout.hovermode = False

# Add a title
fig.update_layout(title='Distribution of Storage and Autobahn SKUs with overdue PUNR holds by factory')
pio.renderers.default='svg' #cambiar a 'browser' para abrir en navegador y ver mejor


fig.update_layout(
    autosize=False,
    width=800,
    height=400,
)

fig.show()



################################################   ESTADÍSTICA

################################################   Chi-Squared

#Primer Chi-Squared: Verificamos si existe relación entre región y el tipo de causa (ERD o Status related)

#Filtrar el dataframe para que solo los tipos de causa relevantes se muestres

d={'Region': df['Region'], 'Cause type': df['Cause type']}
df_Chi1 = pd.DataFrame(d)
df_Chi1=df_Chi1[df_Chi1['Region'] != ''] #Esto filtra las fábricas especiales
df_Chi1=df_Chi1[df_Chi1['Cause type'] != 'Other causes'] #Esto filtra other causes
crosstab1 = pd.crosstab(df_Chi1['Region'], df_Chi1['Cause type'])
#print(crosstab1)

stat1, p1, dof1, expected1 = stats.chi2_contingency(crosstab1)
alpha = 0.05 #Porcentaje de confianza del 95%

print('\n----------First Chi-square test----------')
print('- Null Hypothesis: There is no relationship between region and type of cause.')
print('- Alternative Hypothesis: There is a relationship between region and type of cause.')
print('Confidence level: 95% (5% chance to reject the Null Hypothesis when it is true).\n')
print("For the first chi-square test the p value is " + str(p1) +'\n')
if p1 <= alpha:
    print('The p-value is less than the alpha value: Null Hypothesis is rejected. \nThere is a significant relation between region and the type of cause.\n')
else:
    print('The p-value is greater than the alpha value: Null Hypothesis cannot be rejected. \nThere is not a significant relation between region and the type of cause.\n')



#Segundo Chi-Sauqared: Ahora verificamos si existe relación entre el tipo de causa para las fábricas especiales
d={'Factory': df['Factory'],'Cause': df['Cause'], 'Cause type': df['Cause type']}
df_Chi2 = pd.DataFrame(d)
df_Chi2=df_Chi2[df_Chi2['Cause type'] == 'Special Plant related (CF, Japan, Brazil)'] #Esto filtra para solo tener las plantas especiales

for i in df_Chi2.index:
    if 'no SE assigned on Copernicus' in df_Chi2.at[i,'Cause']:
        df_Chi2.at[i, 'Cause type'] = 'No SE assigned'
    else:
        df_Chi2.at[i, 'Cause type'] = 'delayed CTR'
        

crosstab2 = pd.crosstab(df_Chi2['Factory'], df_Chi2['Cause type'])
#print(crosstab2)


stat2, p2, dof2, expected2 = stats.chi2_contingency(crosstab2)
alpha = 0.05 #Porcentaje de confianza del 95%

print('\n----------Second Chi-square test----------')
print('- Null Hypothesis: There is no relationship between factory and type of cause.')
print('- Alternative Hypothesis: There is a relationship between factory and type of cause.')
print('Confidence level: 95% (5% chance to reject the Null Hypothesis when it is true).\n')
print("For the second chi-square test the p value is " + str(p2) +'\n')
if p2 <= alpha:
    print('The p-value is less than the alpha value: Null Hypothesis is rejected. \nThere is a significant relation between factory and the type of cause for special factories.\n')
else:
    print('The p-value is greater than the alpha value: Null Hypothesis cannot be rejected. \nThere is not a significant relation between factory and the type of cause for special factories.\n')






################################################   ANOVA


#Primer ANOVA: Vemos si hay diferencias significativas entre grupos de causas ERD/STATUS 


d={'Region': df['Region'], 'Factory': df['Factory'], 'Cause type': df['Cause type'], 'Cause': df['Cause']}
df_ANOVA1 = pd.DataFrame(d)
df_ANOVA1=df_ANOVA1[df_ANOVA1['Region'] != '']
val_filter = ['Status related', 'ERD related']
df_ANOVA1=df_ANOVA1[df_ANOVA1['Cause type'].isin(val_filter)]
df_ANOVA1=df_ANOVA1.groupby(['Factory', 'Cause type']).count()

pivot1 = pd.pivot_table(data=df_ANOVA1, index=['Factory'], columns=['Cause type'], values='Cause')
#print(pivot1)


fvalue1, pvalue1 = stats.f_oneway(pivot1['ERD related'], pivot1['Status related'])
#print(pvalue1)

alpha = 0.05 #Porcentaje de confianza del 95%

print('\n----------First ANOVA----------')
print('- Null Hypothesis: There is no difference between ERD related casuses and Status related causes.')
print('- Alternative Hypothesis: There is a difference between ERD related causes and Status related causes.')
print('Confidence level: 95% (5% chance to reject the Null Hypothesis when it is true).\n')
print("For the First ANOVA the p value is " + str(p2) +'\n')
if p2 <= alpha:
    print('The p-value is less than the alpha value: Null Hypothesis is rejected. \nThere is a significant difference between the 2 types of causes.\n')
else:
    print('The p-value is greater than the alpha value: Null Hypothesis cannot be rejected. \nThere is not a significant difference between the 2 types of causes.\n')



#Segunda ANOVA: Vemos si para cada fábrica especial hay diferencias entre grupos de causas SE/CTR

d={'Factory': df['Factory'], 'Cause': df['Cause'], 'Cause type': df['Cause type']}
df_ANOVA2 = pd.DataFrame(d)
df_ANOVA2=df_ANOVA2[df_ANOVA2['Cause type'] == 'Special Plant related (CF, Japan, Brazil)']
#print(df_ANOVA2)

for i in df_ANOVA2.index:
    if 'no SE assigned on Copernicus' in df_ANOVA2.at[i,'Cause']:
        df_ANOVA2.at[i, 'Cause type'] = 'No SE assigned'
    else:
        df_ANOVA2.at[i, 'Cause type'] = 'delayed CTR'

df_ANOVA2=df_ANOVA2.groupby(['Factory', 'Cause type']).count()
#print(df_ANOVA2)

pivot2 = pd.pivot_table(data=df_ANOVA2, index=['Factory'], columns=['Cause type'], values='Cause')
#print(pivot2)


fvalue2, pvalue2 = stats.f_oneway(pivot2['No SE assigned'], pivot2['delayed CTR'])
#print(pvalue2)

alpha = 0.05 #Porcentaje de confianza del 95%

print('\n----------Second ANOVA----------')
print('- Null Hypothesis: There is no difference between delayed CTR causes and No SE assigned causes for special factories.')
print('- Alternative Hypothesis: There is a relationship between delayed CTR causes and No SE assigned causes for special factories.')
print('Confidence level: 95% (5% chance to reject the Null Hypothesis when it is true).\n')
print("For the second ANOVA the p value is " + str(p2) +'\n')
if p2 <= alpha:
    print('The p-value is less than the alpha value: Null Hypothesis is rejected. \nThere is a significant difference between the 2 types of causes.\n')
else:
    print('The p-value is greater than the alpha value: Null Hypothesis cannot rejected. \nThere is not a significant difference between the 2 types of causes.\n')




################################################   Pareto

df_pareto = pd.DataFrame({'Count': df_barras['Count']})
df_pareto.index = df_barras['Causes'].values.tolist()
df_pareto = df_pareto.sort_values(by='Count', ascending=False) #Ordena los datos de mayor a menor
df_pareto['cumperc'] = df_pareto['Count'].cumsum()/df_pareto['Count'].sum()*100 #Calcula porcentajes acumulativos necesarios para Pareto
#print (df_pareto)

#Debido a que las causas son largas, para una visualización más sencilla se cambia cada causa por una letra del alfabero

#Codificar las causas en letras del abecedario para facilitar su visualización
valores_x=df_pareto.index.values.tolist()
#print(valores_x)
abecedario = list(string.ascii_uppercase)

# Asignar las letras del abecedario a los elementos de la lista
valores_x = abecedario[:len(valores_x)]
#print(valores_x)

#Genero un DF que almacene que letra corresponde a cada causa:
df_clave= pd.DataFrame({'Letter': valores_x, 'Cause': df_pareto.index.values.tolist()})
df_clave = df_clave.reset_index(drop=True)
print('\n----------Pareto Chart Legend----------\n')
print(df_clave)

df_pareto.index = valores_x #Cambio las causas del dataframe de pareto por la lista de letras

fig, ax = plt.subplots(figsize=(10,6))
ax.bar(df_pareto.index, df_pareto['Count'], color='steelblue')
ax.bar_label(ax.containers[0])
plt.grid(axis='x')
plt.xticks(valores_x)
ax.set_ylabel('Frequency')
ax.set_xlabel('Cause')


#Agrega la linea de porcentaje acumulado al gráfico
ax2 = ax.twinx()
ax2.plot(df_pareto.index, df_pareto['cumperc'], color='red', marker="D", ms=4)
ax2.yaxis.set_major_formatter(PercentFormatter())
ax2.set_ylabel('Cumulative percentage')
#Anota sobre la linea roja, el punto donde el porcentaje es mayor o igual a 80% y el porcentaje correspondiente
target_percentage = 80
index_closest_to_80 = (np.abs(df_pareto['cumperc'] - target_percentage)).idxmin()
closest_value = df_pareto.loc[index_closest_to_80, 'cumperc']

ax2.annotate(f'{closest_value:.2f}%', (index_closest_to_80, closest_value), textcoords="offset points", xytext=(0, 10), ha='center')


plt.grid(axis='y')

plt.title('Pareto Chart of Overdue PUNR holds by cause')
plt.show()
