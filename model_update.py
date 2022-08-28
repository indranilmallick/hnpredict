# -*- coding: utf-8 -*-
"""
Created on Sat Aug 14 06:38:43 2021

@author: imall
"""

#import numpy as np
import pandas as pd
#import streamlit as st
import requests
from io import StringIO
import pickle
from lifelines import CoxPHFitter
from datetime import datetime



def pull_data():
    data = {
    'token': '720A389305434A0F65BEE0612C7D7BC3',
    'content': 'report',
    'format': 'csv',
    'report_id': '1515',
    'csvDelimiter': '',
    'rawOrLabel': 'raw',
    'rawOrLabelHeaders': 'raw',
    'exportCheckboxLabel': 'false',
    'returnFormat': 'csv'
    }
    r = requests.post('https://redcap.tmckolkata.com:8443/redcap/api/',data=data, verify = False)
    #print('HTTP Status: ' + str(r.status_code))
    oral = pd.read_csv(StringIO(r.text))
    return oral

def prepare_data(oral):
    # select cases where the important variables are not blank

    oral = oral.dropna(subset=['laterality', 'primary', 'lvi', 'pni', 'tsize', 'depth', 'diff', 'marginstatus',
                           'ptstage', 'pnstage','date_of_surgery','date_last_fu'])

    # Identify date fields and convert them to date format

    dates = ['date_of_surgery','rt_start_date', 'rt_end_date', 'date_of_local_failure', 'date_of_nodal_failue', 'date_of_distant_metastasis',
         'date_of_death', 'date_last_fu']
    oral[dates] = oral[dates].apply(pd.to_datetime, errors = 'coerce')

    # calculate DFS. LRF, DM, OS date. 
    oral['date_fail_death'] = oral[['date_of_local_failure', 'date_of_nodal_failue', 'date_of_distant_metastasis', 'date_of_death', 'date_last_fu']].min(axis = 1)
    oral['date_locoregional'] = oral[['date_of_local_failure', 'date_of_nodal_failue', 'date_last_fu']].min(axis = 1)
    oral['date_mets'] = oral[['date_of_distant_metastasis', 'date_last_fu']].min(axis = 1)
    oral['date_death'] = oral[['date_of_death', 'date_last_fu']].min(axis = 1)

    # calculate durations in months
    oral['fu_months'] = ((oral['date_last_fu']- oral['date_of_surgery']).dt.days)//30.3
    oral['failure_months'] = ((oral['date_fail_death']- oral['date_of_surgery']).dt.days)//30.3
    oral['failure_lr_months'] = ((oral['date_locoregional']- oral['date_of_surgery']).dt.days)//30.3
    oral['failure_met_months'] = ((oral['date_fail_death']- oral['date_of_surgery']).dt.days)//30.3
    oral['death_months'] = ((oral['date_death']- oral['date_of_surgery']).dt.days)//30.3
    
    # recode events
    oral['fail_death'] = oral[['local_failure', 'nodal_failure', 'distant_metastasis', 'death_known']].sum(axis = 1)
    oral['any_fail'] = oral['fail_death'].apply(lambda x: 1 if x >4 else 0)
    
    oral['local_nodal'] = oral[['local_failure', 'nodal_failure']].sum(axis = 1)
    oral['lr_fail'] = oral['local_nodal'].apply(lambda x: 1 if x >2 else 0)
    
    oral['met_fail'] = oral['distant_metastasis'].apply(lambda x: 1 if x==2 else 0)
    
    oral['death_fail'] = oral['death_known'].apply(lambda x: 1 if x==2 else 0)
    
    # select subset and primary characteristics
    
    oral = oral[(oral['primary']<6) | (oral['primary']>11)]
    oral['primary_grp'] = oral['primary'].apply(lambda x: 1 if x ==1 else 0)
    oral['lvi_grp'] =  oral['lvi'].apply(lambda x: 0 if x ==0 else 1)
    oral['pni_grp'] =  oral['pni'].apply(lambda x: 0 if x ==0 else 1)
    oral['laterality_grp'] =  oral['laterality'].apply(lambda x: 1 if x > 2 else x)
    
    # recode nodes
    
    cols = oral.columns.to_list()
    involved = []
    for col in cols:
        if 'level' in col and 'inv' in col:
            involved.append(col)
    
    ecelist = []
    for col in cols:
        if 'ece' in col and 'any' not in col:
            ecelist.append(col)
    
    focuslist = []
    for col in cols:
        if 'focus' in col:
            focuslist.append(col)
    
    oral[involved] = oral[involved].fillna(0)
    oral[ecelist] = oral[ecelist].fillna(0)
    
    oral['n_ipsi1b'] = oral.apply(lambda x: x['levelright1binv'] if x['laterality_grp'] == 1 else x['levelleft1binv'], axis = 1)
    oral['n_ipsi2a'] = oral.apply(lambda x: x['levelright2ainv'] if x['laterality_grp'] == 1 else x['levelleft2ainv'], axis = 1)
    oral['n_ipsi2b'] = oral.apply(lambda x: x['levelright2binv'] if x['laterality_grp'] == 1 else x['levelleft2binv'], axis = 1)
    oral['n_ipsi3'] = oral.apply(lambda x: x['levelright3inv'] if x['laterality_grp'] == 1 else x['levelleft3inv'], axis = 1)
    oral['n_ipsi4'] = oral.apply(lambda x: x['levelright4inv'] if x['laterality_grp'] == 1 else x['levelleft4inv'], axis = 1)
    oral['n_ipsi5'] = oral.apply(lambda x: x['levelright5inv'] if x['laterality_grp'] == 1 else x['levelleft5inv'], axis = 1)
    oral['n_ipsi9'] = oral.apply(lambda x: x['levelright9inv'] if x['laterality_grp'] == 1 else x['levelleft9inv'], axis = 1)
    
    oral['n_contra1b'] = oral.apply(lambda x: x['levelright1binv'] if x['laterality_grp'] == 0 else x['levelleft1binv'], axis = 1)
    oral['n_contra2a'] = oral.apply(lambda x: x['levelright2ainv'] if x['laterality_grp'] == 0 else x['levelleft2ainv'], axis = 1)
    oral['n_contra2b'] = oral.apply(lambda x: x['levelright2binv'] if x['laterality_grp'] == 0 else x['levelleft2binv'], axis = 1)
    oral['n_contra3'] = oral.apply(lambda x: x['levelright3inv'] if x['laterality_grp'] == 0 else x['levelleft3inv'], axis = 1)
    oral['n_contra4'] = oral.apply(lambda x: x['levelright4inv'] if x['laterality_grp'] == 0 else x['levelleft4inv'], axis = 1)
    oral['n_contra5'] = oral.apply(lambda x: x['levelright5inv'] if x['laterality_grp'] == 0 else x['levelleft5inv'], axis = 1)
    oral['n_contra9'] = oral.apply(lambda x: x['levelright9inv'] if x['laterality_grp'] == 0 else x['levelleft9inv'], axis = 1)
    
    oral['n_ipsi_total'] = oral.apply(lambda x: x['level1ainv'] + x['level6inv'] + x['n_ipsi1b'] + x['n_ipsi2a'] + x['n_ipsi2b'] + x['n_ipsi3'] + x['n_ipsi4'] + x['n_ipsi5'] + x['n_ipsi9'], axis = 1)
    oral['n_contra_total'] = oral.apply(lambda x: x['level1ainv'] + x['level6inv'] + x['n_contra1b'] + x['n_contra2a'] + x['n_contra2b'] + x['n_contra3'] + x['n_contra4'] + x['n_contra5'] + x['n_contra9'], axis = 1)
    
    oral['n_ece_total'] = oral[ecelist].sum(axis = 1)
    oral['ece_grp'] =  oral['n_ece_total'].apply(lambda x: 1 if x > 0 else 0)
    
    oral = oral[['age', 'sex', 'primary_grp', 'ptstage', 'pnstage', 'tsize', 'depth', 'diff', 'marginstatus', 'lvi_grp', 'pni_grp', 
                 'n_ipsi_total', 'n_contra_total', 'n_ece_total', 'ece_grp', 
                 'fu_months', 'failure_months', 'any_fail', 'failure_lr_months', 'lr_fail',
                 'failure_met_months', 'met_fail', 'death_months', 'death_fail']]
    oral = oral.dropna()
    oral = oral[oral['failure_months']>0]
    oral = oral[(oral['fu_months'] > 6) | (oral['any_fail'] ==1)]
    len_oral = len(oral)
    return oral, len_oral


def create_models(surv):
    surv_dfs = surv[['age', 'primary_grp', 'tsize', 'depth', 'diff', 'marginstatus', 'lvi_grp', 'pni_grp', 'n_ipsi_total', 'n_contra_total', 'ece_grp', 'failure_months', 'any_fail']]
    surv_lrc = surv[['age', 'primary_grp', 'tsize', 'depth', 'diff', 'marginstatus', 'lvi_grp', 'pni_grp', 'n_ipsi_total', 'n_contra_total', 'ece_grp', 'failure_lr_months', 'lr_fail']]
    surv_mfs = surv[['age', 'primary_grp', 'tsize', 'depth', 'diff', 'marginstatus', 'lvi_grp', 'pni_grp', 'n_ipsi_total', 'n_contra_total', 'ece_grp', 'failure_met_months', 'met_fail']]
    surv_os = surv[['age', 'primary_grp', 'tsize', 'depth', 'diff', 'marginstatus', 'lvi_grp', 'pni_grp', 'n_ipsi_total', 'n_contra_total', 'ece_grp', 'death_months', 'death_fail']]
    
    cph_dfs = CoxPHFitter()
    cph_dfs.fit(surv_dfs, 'failure_months', event_col='any_fail')
    cph_lrc = CoxPHFitter()
    cph_lrc.fit(surv_lrc, 'failure_lr_months', event_col='lr_fail')
    cph_mfs = CoxPHFitter()
    cph_mfs.fit(surv_mfs, 'failure_met_months', event_col='met_fail')
    cph_os = CoxPHFitter()
    cph_os.fit(surv_os, 'death_months', event_col='death_fail')
    
    dfs_pickle = "dfscoxmodel.pkl"  
    with open(dfs_pickle, 'wb') as file:  
        pickle.dump(cph_dfs, file)
        
    lrc_pickle = "lrccoxmodel.pkl"  
    with open(lrc_pickle, 'wb') as file:  
        pickle.dump(cph_lrc, file)
            
    mfs_pickle = "mfscoxmodel.pkl"  
    with open(mfs_pickle, 'wb') as file:  
        pickle.dump(cph_mfs, file)
        
    os_pickle = "oscoxmodel.pkl"  
    with open(os_pickle, 'wb') as file:  
        pickle.dump(cph_os, file)
            
    tod_date = datetime.now()
    update = open('update.txt', "w")
    update.write("Model last updated: " + str(tod_date) + " \n")
    update.write("Number of training cases: " + str(len(surv))+ " \n")
    update.write("Cox proportional hazards regression model \n")
    update.write("Model indices: \n")
    update.write("DFS c-index: " + str(cph_dfs.concordance_index_)+ " \n")
    update.write("LRC c-index: " + str(cph_lrc.concordance_index_)+ " \n")
    update.write("DMFS c-index: " + str(cph_mfs.concordance_index_)+ " \n")
    update.write("OS c-index: "+ str(cph_os.concordance_index_)+ " \n")
    update.close()
    print('Models updated')
    

oraldf = pull_data()
surv, length_surv = prepare_data(oraldf)
#features = ['age', 'sex','primary_grp', 'tsize', 'depth', 'diff', 'marginstatus', 'lvi_grp', 'pni_grp', 'n_ipsi_total', 'n_contra_total', 'ece_grp']    
create_models(surv)


