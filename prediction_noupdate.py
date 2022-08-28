# -*- coding: utf-8 -*-
"""
Created on Thu Aug 12 20:58:48 2021

@author: imall
"""

import numpy as np
import pandas as pd
from bokeh.plotting import figure
from bokeh.io import reset_output
from bokeh.models import Range1d
#from bokeh.models.tickers import FixedTicker
import streamlit as st
import pickle
from lifelines import CoxPHFitter
from datetime import datetime


@st.cache
def getmodels():
    dfsmodel = pickle.load(open('dfscoxmodel.pkl', 'rb'))
    lrcmodel = pickle.load(open('lrccoxmodel.pkl', 'rb'))
    mfsmodel = pickle.load(open('mfscoxmodel.pkl', 'rb'))
    osmodel = pickle.load(open('oscoxmodel.pkl', 'rb'))
    return dfsmodel, lrcmodel, mfsmodel, osmodel

st.set_page_config(page_title="PREDICT-OR", page_icon=":microscope:", layout="wide", initial_sidebar_state="expanded")
st.title('PREDICT-OR: Oral Cancer Dynamic Outcome Prediction Model')

# sidebar info
st.sidebar.title('About this tool:')
st.sidebar.subheader('This is a dynamically updating clinical prediction model for individualized outcome prediction in oral cancer.')
st.sidebar.subheader('This tool was built at Tata Medical Center, Kolkata, India.')

st.sidebar.header('Instructions for use:')
st.sidebar.write('Using this tool is simple.')
st.sidebar.write('Simply key in the clinico-pathological features of an individual and press the Predict button.')

st.sidebar.header('Model Updates')
st.sidebar.write('The models are typically auto-updated once a week.')

file1 = open('update.txt', 'r')
Lines = file1.readlines()
file1.close()
st.sidebar.write(Lines[0])

#st.sidebar.header('This tool is under clinical peer review and should not yet be used to counsel patients.')

#st.write('Loading Models')
dfsmodel, lrcmodel, mfsmodel, osmodel = getmodels()
#st.write('Models loaded successfully')


primary_choices = {0:"Gingivobuccal", 1:"Tongue"}
diff_choices = {1:"Well-differentiated", 2:"Moderately Differentiated", 3: "Poorly Differentiated"}
ap_choices = {0:"Absent", 1:"Present"}
margin_choices = {0:"Clear", 1:"Close <0.5cm", 2: "Involved"}



with st.form("Input"):
    st.title("""Key in the individual's parameters""")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input('Age:', min_value = 18, max_value = 100, value = 50)
        primary = st.selectbox("Primary", options = list(primary_choices.keys()), format_func=lambda x: primary_choices[x])
        diff = st.selectbox("Differentiation", options = list(diff_choices.keys()), format_func=lambda x: diff_choices[x])
        tsize = st.number_input('Max dimension:', min_value = 0.1, max_value = 15.0, value = 0.5)
        depth = st.number_input('Depth:', min_value = 0.1, max_value = 10.0, value = 0.3)
        lvi = st.selectbox("Lymphovascular invasion", options = list(ap_choices.keys()), format_func=lambda x: ap_choices[x])
    with col2:
        pni= st.selectbox("Perineural invasion", options = list(ap_choices.keys()), format_func=lambda x: ap_choices[x])
        margin = st.selectbox("Margins of resection", options = list(margin_choices.keys()), format_func=lambda x: margin_choices[x])
        ipsi = st.number_input('Ipsilateral nodes:', min_value = 0, max_value = 40, value = 0)
        contra = st.number_input('Contralateral nodes:', min_value = 0, max_value = 40, value = 0)
        ece = st.selectbox("Extranodal extension", options = list(ap_choices.keys()), format_func=lambda x: ap_choices[x])
        st.write('When all the parameters are entered, press the Predict button.')
        submitted = st.form_submit_button("Predict")
        if not submitted:
            st.stop()

example = {
    'age': age,
    'primary_grp': primary,
    'tsize': tsize,
    'depth': depth,
    'diff': diff,
    'marginstatus': margin,
    'lvi_grp': lvi,
    'pni_grp': pni,
    'n_ipsi_total':ipsi,
    'n_contra_total': contra,
    'ece_grp':ece}
ex_df = pd.DataFrame(example, index = ['Prediction'])
#st.write(ex_df) 

dfstimes = dfsmodel.predict_survival_function(ex_df, times = [12, 24, 36, 48, 60])
lrctimes = lrcmodel.predict_survival_function(ex_df, times = [12, 24, 36, 48, 60])
mfstimes = mfsmodel.predict_survival_function(ex_df, times = [12, 24, 36, 48, 60])
ostimes = osmodel.predict_survival_function(ex_df, times = [12, 24, 36, 48, 60])
times = pd.concat([dfstimes, lrctimes, mfstimes, ostimes], axis=1)
times.columns=['DFS','LRC', 'DMFS', 'OS']
times.index = ['1-year', '2-year', '3-year', '4-year', '5-year']


#reset_output()
TOOLTIPS = [("Outcome","$name"),("Months","$x{0}"),("Probability", "$y{0.00}")]

plots = figure(plot_width=600, plot_height=400, title="Outcome Prediction", tooltips=TOOLTIPS)

dfs = dfsmodel.predict_survival_function(ex_df)
dfs = dfs.loc[:72,:]
plots.line(dfs.index, dfs.Prediction, line_width=3, name = 'DFS', color = 'red', legend_label = 'Disease-free Survival')

lrc = lrcmodel.predict_survival_function(ex_df)
lrc = lrc.loc[:72,:]
plots.line(lrc.index, lrc.Prediction, line_width=2, name = 'LRC', color = 'blue', legend_label = 'Locoregional Control')

mfs = mfsmodel.predict_survival_function(ex_df)
mfs = mfs.loc[:72,:]
plots.line(mfs.index, mfs.Prediction, line_width=2, name = 'DMFS', color = 'green', legend_label = 'Distant Metastasis-free Survival')

os = osmodel.predict_survival_function(ex_df)
os = os.loc[:72,:]
plots.line(os.index, os.Prediction, line_width=2, name = 'OS', color = 'orange', legend_label = 'Overall Survival')

plots.legend.location = "bottom_left"
plots.legend.label_text_font_size = "7pt"
plots.xaxis.axis_label = "Time (months)"
plots.xaxis.axis_line_width = 3
plots.xaxis.axis_line_color = "red"
plots.yaxis.axis_label = "Predicted Probability"
plots.yaxis.axis_line_width = 3
plots.yaxis.axis_line_color = "blue"
plots.legend.background_fill_color = "white"
plots.legend.background_fill_alpha = 0.5
plots.legend.click_policy="hide"
plots.y_range = Range1d(0, 1.05)
plots.xaxis.ticker = [0,12,24,36,48,60,72]

st.title('Predicted outcomes')
col3, col4 = st.columns(2)
with col3:
    st.header('Survival Probabilities over 5 years')
    st.table(times.style.set_precision(2))
    st.write('DFS: Disease-free survival; LRC: Locoregional Control')
    st.write('DMFS: Distant-metastasis-free survival; OS: Overall survival')
with col4:
    st.header('Survival Plots')
    st.bokeh_chart(plots, use_container_width=True)

with st.expander("""Model Details: (click to expand)"""):
    for line in Lines:
        st.write(line.strip())


    