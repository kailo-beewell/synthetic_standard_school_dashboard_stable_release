from ast import literal_eval
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from utilities.fixed_params import page_setup
from utilities.details import details_stacked_bar, details_ordered_bar
from utilities.details_text import create_stacked_descrip

# Set page configuration
page_setup('wide')

# Import the scores and the proportion each response
df_scores = pd.read_csv('data/survey_data/aggregate_scores_rag.csv')
df_prop = pd.read_csv('data/survey_data/aggregate_responses.csv')

###############################################################################

# Get the unique topics
topic_df = df_scores[['variable', 'variable_lab']].drop_duplicates()

# Drop those we don't create detailed pages about
topic_df = topic_df[~topic_df['variable'].isin([
    'birth_you_age_score', 'staff_talk_score', 'home_talk_score',
    'peer_talk_score', 'overall_count'])]

# Remove '_score'
topic_df['variable'] = topic_df['variable'].str.replace('_score', '')

# Convert to dictionary
topic_dict = pd.Series(topic_df.variable.values, index=topic_df.variable_lab).to_dict()

# If session state doesn't contain chosen variable, default to Autonomy
# If it does (i.e. set from Summary page), use that
if 'chosen_variable_lab' not in st.session_state:
    st.session_state['chosen_variable_lab'] = 'Autonomy'

# Convert topics to list and find index of the session state variable
topic_list = list(topic_dict.keys())
default = topic_list.index(st.session_state['chosen_variable_lab'])

# Create selectbox with available topics (excluding demographic) using label
chosen_variable_lab = st.sidebar.radio(
    'Topic', topic_dict.keys(), index=default)
chosen_variable = topic_dict[chosen_variable_lab]

###############################################################################
# Breakdown of question responses chart

# Title 
st.title(chosen_variable_lab)

# Create table of descriptions, where index is the variable
description = df_scores[['variable', 'description']].drop_duplicates().set_index('variable').to_dict()['description']

# Write the short topic description (centred and bold)
st.markdown(f'''<p style='text-align: center;'><b>These questions are about {description[f'{chosen_variable}_score'].lower()}</b></p>''', unsafe_allow_html=True)

# Blank space
st.markdown('')
st.markdown('')

# Select pupils to view results for
cols = st.columns([0.3, 0.7])
with cols[0]:
    st.selectbox('**View results:**', ['For all pupils', 'By year group', 'By gender', 'By FSM', 'By SEN'])

# Blank space
st.markdown('')
st.markdown('')

st.header('Responses from pupils at your school')

# Filter to chosen variable and school
chosen = df_prop[
    (df_prop['group'] == chosen_variable) &
    (df_prop['school_lab'] == st.session_state.school) &
    (df_prop['year_group_lab'] == 'All') &
    (df_prop['gender_lab'] == 'All') &
    (df_prop['fsm_lab'] == 'All') &
    (df_prop['sen_lab'] == 'All')]

# Extract the lists with results stored in the dataframe
# e.g. ['Yes', 'No'], [20, 80], [2, 8] in the original data will become
# seperate columns with [Yes, 20, 2] and [No, 80, 8]
df_list = []
for index, row in chosen.iterrows():
    df = pd.DataFrame(zip(literal_eval(row['cat'].replace('nan', 'None')),
                          literal_eval(row['cat_lab']),
                          literal_eval(row['percentage']),
                          literal_eval(row['count'])),
                      columns=['cat', 'cat_lab', 'percentage', 'count'])
    # Replace NaN with max number so stays at end of sequence
    df['cat'] = df['cat'].fillna(df['cat'].max()+1)
    # Add measure (don't need to extract as string rather than list in df)
    df['measure'] = row['measure']
    df['measure_lab'] = row['measure_lab']
    df_list.append(df)
chosen_result = pd.concat(df_list)

# For categories with multiple charts, list the variables for each chart
multiple_charts = {
    'optimism': {'optimism_future': ['optimism_future'],
                 'optimism_other': ['optimism_best', 'optimism_good', 'optimism_work']},
    'appearance': {'appearance_happy': ['appearance_happy'],
                   'appearance_feel': ['appearance_feel']},
    'physical': {'physical_days': ['physical_days'],
                 'physical_hours': ['physical_hours']},
    'places': {'places_freq': ['places_freq'],
               'places_barriers': ['places_barriers___1', 'places_barriers___2',
                                   'places_barriers___3', 'places_barriers___4',
                                   'places_barriers___5', 'places_barriers___6',
                                   'places_barriers___7', 'places_barriers___8',
                                   'places_barriers___9']},
    'talk': {'talk_yesno': ['staff_talk', 'home_talk', 'peer_talk'],
             'talk_listen': ['staff_talk_listen', 'home_talk_listen', 'peer_talk_listen'],
             'talk_helpful': ['staff_talk_helpful', 'home_talk_helpful', 'peer_talk_helpful'],
             'talk_if': ['staff_talk_if', 'home_talk_if', 'peer_talk_if']},
    'local_env': {'local_safe': ['local_safe'],
                  'local_other': ['local_support', 'local_trust',
                                  'local_neighbours', 'local_places']},
    'future': {'future_options': ['future_options'],
               'future_interest': ['future_interest'],
               'future_support': ['future_support']}
}

# Import descriptions for stacked bar charts
stacked_descrip = create_stacked_descrip()

# Categories to reverse
reverse = ['esteem', 'negative', 'support', 'media', 'free_like', 'local_safe',
           'local_other', 'belong_local', 'bully']

def reverse_categories(df):
    '''
    Resorts dataframe so categories are in reverse order, but missing is still
    at the end (despite being max value).
    Inputs:
    df - dataframe to sort
    '''
    # Resort everything except for the "Missing" responses
    new_df = df[df['cat'] != df['cat'].max()].sort_values(by=['cat'], ascending=False)
    # Append missing back to the end
    new_df = pd.concat([new_df, df[df['cat'] == df['cat'].max()]])
    # Return the resorted dataframe
    return(new_df)

# Create stacked bar chart with seperate charts if required
if chosen_variable in multiple_charts:
    var_dict = multiple_charts[chosen_variable]
    for key, value in var_dict.items():
        # Add description
        st.markdown(stacked_descrip[key])
        # Create plot (reversing the categories if required)
        to_plot = chosen_result[chosen_result['measure'].isin(value)]
        if key in reverse:
            to_plot = reverse_categories(to_plot)
        details_stacked_bar(to_plot)
# Otherwise create a single stacked bar chart
else:
    # Add description
    st.markdown(stacked_descrip[chosen_variable])
    # Create plot (reversing the categories if required)
    if chosen_variable in reverse:
        chosen_result = reverse_categories(chosen_result)
    details_stacked_bar(chosen_result)

###############################################################################
# Blank space
st.text('')
st.text('')
st.text('')

###############################################################################
# Initial basic example of doing the comparator chart between schools...

st.header('Comparison of overall mean score to other schools')

# Create dataframe based on chosen variable
between_schools = df_scores[
    (df_scores['variable'].str.replace('_score', '') == chosen_variable) &
    (df_scores['year_group_lab'] == 'All') &
    (df_scores['gender_lab'] == 'All') &
    (df_scores['fsm_lab'] == 'All') &
    (df_scores['sen_lab'] == 'All')]

# Add box with RAG rating
devon_rag = between_schools.loc[between_schools['school_lab'] == st.session_state.school, 'rag'].to_list()[0]
cols = st.columns(2)
with cols[0]:
    st.subheader('Comparison to other schools in Northern Devon')
    st.markdown(f'The average score for {chosen_variable_lab.lower()} at your school, compared to other schools in Northern Devon, was:')
    if devon_rag == 'below':
        st.error('↓ Below average')
    elif devon_rag == 'average':
        st.warning('~ Average')
    elif devon_rag == 'above':
        st.success('↑ Above average')

# Show figure within column
with cols[1]:
    details_ordered_bar(between_schools, st.session_state.school)

# Note schools that don't have a match (might be able to do that based on
# what variables are present in their data v.s. not)
no_match = ['support', 'places', 'talk', 'accept', 'belong_local', 'wealth', 'future', 'climate']

# Create duplicate to show example of what having matched schools as well looks like
cols = st.columns(2)
if chosen_variable in no_match:
    st.markdown('This question was unique to Northern Devon and cannot be compared to other schools.')
else:
    with cols[0]:
        st.subheader('Comparison to matched schools from across the country')
        st.markdown('Your school:')
        if devon_rag == 'below':
            st.error('↓ Below average')
        elif devon_rag == 'average':
            st.warning('~ Average')
        elif devon_rag == 'above':
            st.success('↑ Above average')
        st.markdown('Note: Just a duplicate of the above')
    with cols[1]:
        details_ordered_bar(between_schools, st.session_state.school)