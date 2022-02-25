# -*- coding: utf-8 -*-
"""
Created on Fri Sep 24 14:12:39 2021

@author: AVALENTIN
"""

# Import des modules
import pandas as pd #permet de manipuler des matrices ou tableaux 
import matplotlib.pyplot as plt #permet de tracer et visualiser des données sous formes de graphiques
import math #fonction mathématique (RACINE)
from pycaret.regression import * 
import streamlit as st #permet de créer une application web
#from PIL import Image

def reading_dataset(): #fonction lire un jeu de données en excel ou csv
    global dataset
    try:
        dataset = pd.read_excel(uploaded_file)
    except ValueError:
        dataset = pd.read_csv(uploaded_file)
    return dataset


def calculconso(temps,intensiteh,cosphi):
    conso = (temps*intensiteh*1.65*400*math.sqrt(3)*cosphi)/(1000*3600)
    return conso



st.title('Wave concept estimation') #titre de l'application web

#st.sidebar.image(Image.open('logoalstefgroup.jpg'))
uploaded_file = st.sidebar.file_uploader("Upload le fichier excel", type=["xlsx"]) #Permet d'upload la liste des équipements sous format excel 
    
st.sidebar.title('Parametres') #Titre parametres 

genre = st.sidebar.radio("Choix mode d'entrée des paramètres",('Curseur', 'Saisie numérique'))

if genre == 'Curseur': #parametre mode SLIDER
        high = st.sidebar.slider('flux haut(sur 1h)',0,200,100)
        thigh = st.sidebar.slider('Temps flux haut par jour (en h)',0,24,5)
        low = st.sidebar.slider('flux bas (sur 1h)',0,200,50)
        tlow = st.sidebar.slider('Temps flux bas par jour (en h)',0,24,5)
        cosphi = st.sidebar.slider('cosphi',0.00,1.00,0.64)
        prix = st.sidebar.slider('prix du kWh',0.00,0.50,0.12)
        annee = st.sidebar.slider('Durée investisement',0,24,5)
        invest = st.sidebar.slider('Investisement (en €)',0,200000,50000)
        
else: #parametre mode NUMBER_INPUT : 

        high = st.sidebar.number_input('flux haut(sur 1h)',0,200,100)
        thigh = st.sidebar.number_input('Temps flux haut par jour (en h)',0,24,5)
        low = st.sidebar.number_input('flux bas (sur 1h)',0,200,50)
        tlow = st.sidebar.number_input('Temps flux bas par jour (en h)',0,24,5)
        cosphi = st.sidebar.number_input('cosphi',0.00,1.00,0.64)
        prix = st.sidebar.number_input('prix du kWh',0.00,0.50,0.12)
        annee = st.sidebar.number_input('Durée investisement',0,24,5)
        invest = st.sidebar.number_input('Investisement (en €)',0,200000,50000)


    
if uploaded_file is not None: #si un fichier est upload
    data = reading_dataset() #le fichier est lu et enregistré dans la table data
    
    datafluxhaut = data.assign(fluxh=high) #nouvelle table datafluxhaut, ajout de la colonne flux haut (d'après les parametres choisis)
    datafluxbas = data.assign(fluxh=low) #nouvelle table datafluxbas, ajout de la colonne flux bas (d'après les parametres choisis)
    
    model = load_model('model0802v2') # chargement du model1 de machine learning, détermine la consommation des convoyeurs selon leurs caractéristiques 
    model2 = load_model('modelfluxecov2')# chargement du model2 de machine learning, détermine le % d'économie en fonction du flux et des caractéristique des convoyeurs

    pred = model.predict(data) #utilisation du model1 pour l'économie en flux haut
    economiefluxhaut = model2.predict(datafluxhaut) #utilisation du model2  pour l'économie en flux haut
    economiefluxbas = model2.predict(datafluxbas) #utilisation du model2 pour l'économie en flux bas
    
    
    data['intensityH']= pred #data aprend une nouvelle colonne intensityH, consommation par heure des convoyeurs
    data['redhigh']= economiefluxhaut #data aprend une nouvelle colonne redhigh, % de réduction en flux haut
    data['redlow']= economiefluxbas #data aprend une nouvelle colonne intensityH, % de réduction en flux bas
    
            
    conso = pd.DataFrame(columns = ['id', 'consoJ', 'consoJWC','PconsoJ', 'PconsoJWC']) #nouvelle table pour les calcule de consomation et prix (avant et après waveconcept)
    
    conso['id']=data['id'] #Récupération des id des convoyeurs de la table data
    
    #initialisation des sommes de l'ensemble des convoyeurs
    sumconsoJ=0 #somme consommation par jours
    sumconsoJWC=0 #somme consommation par jours avec waveconcept
    sumPconsoJ=0 #somme du prix de la consommation par jours
    sumPconsoJWC=0 #somme du prix de la consommation par jours avec waveconcept

    for i in conso.index :
        
        conso['consoJ'][i]= calculconso((thigh+tlow),data['intensityH'][i],cosphi)
        consofh = calculconso(thigh,data['intensityH'][i],cosphi)*(1-data['redhigh'][i])
        consofb = calculconso(tlow,data['intensityH'][i],cosphi)*(1-data['redlow'][i])

        conso['consoJWC'][i]=consofh+consofb
        conso['PconsoJ'][i]=conso['consoJ'][i]*prix
        conso['PconsoJWC'][i]=conso['consoJWC'][i]*prix
        
        sumconsoJ=sumconsoJ+conso['consoJ'][i]
        sumconsoJWC=sumconsoJWC+conso['consoJWC'][i]
        sumPconsoJ=sumPconsoJ+conso['PconsoJ'][i]
        sumPconsoJWC=sumPconsoJWC+conso['PconsoJWC'][i]
      
    
        
    projection = pd.DataFrame(index=range(1, annee*365),columns = ['jour','consoEE', 'consoWC','PconsoEE', 'PconsoWC','Pdif'])
    for i in projection.index:
        projection['jour'][i]=i
        projection['consoEE'][i]=sumconsoJ*i
        projection['consoWC'][i]=sumconsoJWC*i
        projection['PconsoEE'][i]=sumPconsoJ*i
        projection['PconsoWC'][i]=sumPconsoJWC*i+invest
        projection['Pdif'][i]=projection['PconsoEE'][i]-projection['PconsoWC'][i]
    
    profit = projection['PconsoEE'][annee*365-1]-projection['PconsoWC'][annee*365-1]
    profit = round(profit, 2)
    Jroi= 'A'
    for i in projection.index:    
        if projection['Pdif'][i]>0:
            Jroi= i
            break
        
    if Jroi=="A":  
        st.write("Durée d'investisement nécessaire insuffisant. Durée indiqué : ",annee,"an(s)")
    else:
        st.write('Le seuil de rentabilité (point mort) sera atteint dans ', Jroi,'jours.')
        st.write('Le profit dans ', annee, 'an(s) sera de ', profit ,'€.')
        
        
        moyenne = round((data['redhigh'].mean()*thigh+data['redlow'].mean()*tlow)/(thigh+tlow)*100,2)
        st.write("Le % d'économie moyen par jour est de ", moyenne,"%")
        
        
        co2 = round((sumconsoJ-sumconsoJWC)*0.1,0)
        st.write("Le mode wave concept permettrait d'éviter de produire ", co2*30,"kg de CO2 par mois" )
    
        
        
    plt.figure()
    plt.plot(projection["jour"], projection["PconsoEE"],label='Consomation EE') 
    plt.plot(projection["jour"], projection["PconsoWC"],label='Consomation WC') 
    plt.title('Prix consomation EE vs WC')
    plt.xlabel('jour')
    plt.ylabel('€')
    plt.scatter(Jroi, projection["PconsoEE"][Jroi], c = 'red') 
    plt.axvline(Jroi, 0, projection["PconsoEE"][Jroi]/projection["PconsoEE"][annee*365-1],linestyle='--', color='r')
    plt.legend()
    st.pyplot(plt.show())
     
    plt.figure()
    plt.plot(projection["jour"], projection["consoEE"],label='Consomation EE') 
    plt.plot(projection["jour"], projection["consoWC"],label='Consomation WC') 
    plt.title('Consomation EE vs WC')
    plt.xlabel('jour')
    plt.ylabel('KWh')
    plt.legend()   
