import numpy as np
import pandas as pd
import streamlit as st
from utilities.fixed_params import page_setup

# Set page configuration
page_setup()

# Need to change to globally set school depending on login
school = st.selectbox(
    'School', ['School A', 'School B', 'School C', 'School D',
               'School E', 'School F', 'School G'])

st.title('''Your school's results''')

##########################################################

# Import data
data = pd.read_csv('data/survey_data/aggregate_scores_rag.csv')

# Choose what to show
chosen_group = st.selectbox('Results:', ['All pupils', 'By year group', 'By gender', 'By FSM', 'By SEN'])
comparator = st.selectbox('Compared against:', ['Other schools in Northern Devon'])

# Filter data depending on choice
year_group = ['All']
gender = ['All']
fsm = ['All']
sen = ['All']
if chosen_group == 'By year group':
    pivot_var = 'year_group_lab'
    year_group = ['Year 8', 'Year 10']
    order = ['Year 8', 'Year 10']
elif chosen_group == 'By gender':
    pivot_var = 'gender_lab'
    gender = ['Girl', 'Boy']
              #'I describe myself in another way', 'Non-binary',
              #'Prefer not to say']
    order = ['Girl', 'Boy']
elif chosen_group == 'By FSM':
    pivot_var = 'fsm_lab'
    fsm = ['FSM', 'Non-FSM']
    order = ['FSM', 'Non-FSM']
elif chosen_group == 'By SEN':
    pivot_var = 'sen_lab'
    sen = ['SEN', 'Non-SEN']
    order = ['SEN', 'Non-SEN']

# Filter data
chosen = data[
    (data['school_lab'] == school) &
    (data['year_group_lab'].isin(year_group)) &
    (data['gender_lab'].isin(gender)) &
    (data['fsm_lab'].isin(fsm)) &
    (data['sen_lab'].isin(sen)) &
    (~data['variable'].isin([
        'birth_you_age_score', 'overall_count', 'staff_talk_score',
        'home_talk_score', 'peer_talk_score']))]

if chosen_group != 'All pupils':
    # Pivot from wide to long whilst maintaining row order
    chosen = pd.pivot_table(
        chosen[['variable_lab', pivot_var, 'rag', 'description']],
        values='rag', index=['variable_lab', 'description'], columns=pivot_var,
        aggfunc='sum', sort=False).reset_index().replace(0, np.nan)
    # Reorder columns
    chosen = chosen[['variable_lab'] + order + ['description']]
else:
    chosen = chosen[['variable_lab', 'rag', 'description']]

##########################################################

# Show the detail pages on the sidebar when on summary or a detail page
page = st.sidebar.radio(
    '''Your school's results''',
    options=['All results'] + chosen['variable_lab'].to_list())

##########################################################

st.markdown('#')

description = chosen['description']
chosen = chosen.drop('description', axis=1)

# Set number of columns
ncol = len(chosen.columns)

# Rename columns if in the dataframe
colnames = {
    'variable_lab': 'Topic',
    'rag': 'All pupils',
}
chosen = chosen.rename(columns=colnames)

# Set up columns with custom dimensions if just 2
if ncol == 2:
    cols = st.columns([0.333, 0.333, 0.333])
else:
    cols = st.columns(ncol)

# Add column names
for i in range(ncol):
    with cols[i]:
        st.markdown('**' + chosen.columns[i] + '**')

# For each row of dataframe, create streamlit columns and write data from cell
for index, row in chosen.iterrows():
    if ncol == 2:
        cols = st.columns([0.333, 0.333, 0.333])
    else:
        cols = st.columns(ncol)
    for i in range(ncol):
        with cols[i]:
            if row[i] == 'below':
                st.error('↓ Below average')
            elif row[i] == 'average':
                st.warning('~ Average')
            elif row[i] == 'above':
                st.success('↑ Above average')
            elif pd.isnull(row[i]):
                st.info('n<10')
            else:
                st.markdown('')
                st.markdown('**' + row[i] + '**', help=description[index])
