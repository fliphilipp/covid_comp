import pandas as pd
import pickle as pkl
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import ipywidgets as widgets
from ipywidgets import interact
print('imported dependencies')

class coviddata:
    def __init__(self):
        print('Load newest data:')
        url = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"
        self.df_nyt = pd.read_csv(url)
        print('--> Loaded newest COVID-19 data for the US from the New York Times.')

        url = "https://www.arcgis.com/sharing/rest/content/items/f10774f1c63e40168479a1feb6c7ca74/data"
        self.df_rki = pd.read_csv(url)
        print('--> Loaded newest COVID-19 data for Germany from the Robert-Koch-Institut.')

        url = 'https://opendata.arcgis.com/datasets/ef4b445a53c1406892257fe63129a8ea_0.csv'
        self.df_blpop = pd.read_csv(url)
        print('--> Loaded population data for German states from the Robert-Koch-Institut.')

        url = 'https://opendata.arcgis.com/datasets/917fc37a709542548cc3be077a786c17_0.csv'
        self.df_lkpop = pd.read_csv(url)
        print('--> Loaded population data for German counties from the Robert-Koch-Institut.')

        url = 'https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/counties/totals/co-est2019-alldata.csv'
        self.df_uspop =  pd.read_csv(url, encoding = "ISO-8859-1", engine='python')
        print('--> Loaded population data for US states and counties from the US Census Bureau.')

        url = 'https://raw.githubusercontent.com/OxCGRT/covid-policy-tracker/master/data/OxCGRT_latest.csv'
        self.df_policy = pd.read_csv(url)
        print('--> Loaded government response data from Oxford Blavatnik School of Government.')
        
    def getStates(self):
        self.bl_list = list(np.unique(self.df_blpop.LAN_ew_GEN))
        self.state_list = list(np.unique(self.df_uspop.STNAME))
        bl_w = widgets.Dropdown(
            options=self.bl_list,
            value='Bayern',
            description='Bundesland:',
            disabled=False)
        state_w = widgets.Dropdown(
            options=self.state_list,
            value='California',
            description='US State:',
            disabled=False)
        display(bl_w)
        display(state_w)
        
    def getCounties(self):
        self.lk_list = list(np.unique(self.df_blpop.LAN_ew_GEN))
        self.state_list = list(np.unique(self.df_uspop.STNAME))
        bl_w = widgets.Dropdown(
            options=self.bl_list,
            value='Bayern',
            description='Bundesland:',
            disabled=False)
        state_w = widgets.Dropdown(
            options=self.state_list,
            value='California',
            description='US State:',
            disabled=False)
        display(bl_w)
        display(state_w)
        
    def processData(self):
        
        # population data
        einwohner_bl = dict(zip(df_blpop['LAN_ew_GEN'], df_blpop['LAN_ew_EWZ']))
        einwohner_lk = dict(zip(df_lkpop['county'], df_lkpop['EWZ']))
        pop_de = np.sum(list(einwohner_bl.values()))
        pop_bl = einwohner_bl[bundesland]
        pop_lk = einwohner_lk[landkreis]
        pop_us = np.sum(df_uspop[df_uspop.SUMLEV==40]['POPESTIMATE2019'])
        pop_state = np.int64(df_uspop[df_uspop.CTYNAME==state]['POPESTIMATE2019'])[0]
        pop_county = np.int64(df_uspop[[county in c for c in df_uspop.CTYNAME]]['POPESTIMATE2019'])[0]
        keys = ['USA', state, county, 'Germany', bundesland, landkreis]
        vals = [pop_us, pop_state, pop_county, pop_de, pop_bl, pop_lk]
        pop = dict(zip(keys,vals))
        for k in pop:
            print('population ', k, ': ', pop[k]/1e6, ' million', sep='')
        
        # policy response data
        df_us_policy = df_policy[df_policy.CountryCode.eq('USA')]
        df_de_policy = df_policy[df_policy.CountryCode.eq('DEU')]
        for df in [df_us_policy, df_de_policy]:
            df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
        
        # RKI covid data
        df_rki['Meldedatum'] = pd.to_datetime(df_rki['Meldedatum'], format='%Y/%m/%d %H:%M:%S')
        df_rki['new_cases'] = [a if n in [0,1] else 0 for (a,n) in zip(df_rki['AnzahlFall'],df_rki['NeuerFall'])]
        df_de = df_rki.groupby(['Meldedatum']).sum()
        df_bl = df_rki[df_rki.Bundesland.eq(bundesland)].groupby(['Meldedatum']).sum()
        df_lk = df_rki[df_rki.Landkreis.eq(landkreis)].groupby(['Meldedatum']).sum()
        
        # NYT covid data
        df_nyt['date'] = pd.to_datetime(df_nyt.date, format='%Y-%m-%d')
        df_us = df_nyt.groupby(['date']).sum()
        df_us['new_cases'] = np.diff(np.hstack((0,df_us.cases)))
        df_state = df_nyt[df_nyt.state.eq(state)].groupby(['date']).sum()
        df_state['new_cases'] = np.diff(np.hstack((0,df_state.cases)))
        df_county = df_nyt[df_nyt.county.eq(county)].groupby(['date']).sum()
        df_county['new_cases'] = np.diff(np.hstack((0,df_county['cases'])))
        
        dfs = [df_us, df_state, df_county, df_de, df_bl, df_lk]
        min_date = pd.to_datetime('2020-01-15', format='%Y/%m/%d')
        max_date = min_date
        # idx = pd.date_range('09-01-2013', '09-30-2013')
        for i, df in enumerate(dfs):
            this_pop = list(pop.values())[i]
            df['new_cases_per_1e5'] = df.new_cases / this_pop * 1e5
            mt = np.max(df.index)
            if mt > max_date:
                max_date = mt
        idx = pd.date_range(min_date,max_date)
        for i, df in enumerate(dfs):
            dfs[i] = df.reindex(idx, fill_value=0)
        
    