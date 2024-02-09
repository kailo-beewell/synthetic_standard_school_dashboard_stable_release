from ast import literal_eval
import numpy as np
import pandas as pd
import streamlit as st
from utilities.page_setup import page_setup, blank_lines
from utilities.authentication import check_password
from utilities.bar_charts import survey_responses
from utilities.bar_charts_text import create_response_description
from utilities.import_data import import_tidb_data

# Set page configuration
page_setup()

if check_password():

    # Import the data from TiDB Cloud if not already in session state
    import_tidb_data()

    # Add name of school (to help with monitoring)
    st.markdown(st.session_state.school)

    # Assign data from the session state
    dem_prop = st.session_state.demographic
    counts = st.session_state.counts

    ###########################################################################
    # Introduction including total pupil number

    # Title
    st.title('Who took part?')

    # Filter to relevant school
    school_counts = counts.loc[counts['school_lab'] == st.session_state.school]

    # Find total school size
    school_size = school_counts.loc[
        (school_counts['year_group_lab'] == 'All') &
        (school_counts['gender_lab'] == 'All') &
        (school_counts['fsm_lab'] == 'All') &
        (school_counts['sen_lab'] == 'All'), 'count'].values[0].astype(int)

    # Print school size
    st.markdown(f'''
There were {school_size} pupils at your school who took part in the #BeeWell
survey. This page describes the sample of pupils who completed the survey.''')
    blank_lines(1)

    # Select whether to view results alongside other schools or not
    chosen_group = st.selectbox(
        '**View results:**', ['For your school',
                              'Compared with other schools in Northern Devon'])
    blank_lines(2)

    ###########################################################################
    # Figures

    # Filter to results from current school
    chosen = dem_prop[dem_prop['school_lab'] == st.session_state.school]

    # If only looking at that school, drop the comparator school group data
    if chosen_group == 'For your school':
        chosen = chosen[chosen['school_group'] == 1]

    # Extract the lists with results stored in the dataframe
    # e.g. ['Yes', 'No'], [20, 80], [2, 8] in the original data will become
    # seperate columns with [Yes, 20, 2] and [No, 80, 8]
    df_list = []
    for index, row in chosen.iterrows():
        # Extract results as long as it isn't NaN (e.g. NaN when n<10)
        if ~np.isnan(row.n_responses):
            df = pd.DataFrame(zip(
                literal_eval(row['cat'].replace('nan', 'None')),
                literal_eval(row['cat_lab']),
                literal_eval(row['percentage']),
                literal_eval(row['count'])),
                columns=['cat', 'cat_lab', 'percentage', 'count'])
            # Replace NaN with max number so stays at end of sequence
            df['cat'] = df['cat'].fillna(df['cat'].max()+1)
            # Add strings
            df['measure'] = row['measure']
            df['measure_lab'] = row['measure_lab']
            df['group'] = row['school_group_lab']
            df['plot_group'] = row['plot_group']
            df_list.append(df)
        # As we still want a bar when n<10, we create a record still but label
        # as such
        else:
            df = row.to_frame().T[['measure', 'measure_lab']]
            df['group'] = row['school_group_lab']
            df['plot_group'] = row['plot_group']
            df['cat'] = 0
            df['cat_lab'] = 'Less than 10 responses'
            df['count'] = np.nan
            df['percentage'] = 100
            df_list.append(df)

    # Combine into single dataframe
    chosen_result = pd.concat(df_list)

    # Define headers for each of the plot groups - this will also define the
    # order in which these groups are shown
    header_dict = {
        'year_group': 'Year group',
        'fsm': 'Eligible for free school meals (FSM)',
        'gender': 'Gender and transgender',
        'sexual_orientation': 'Sexual orientation',
        'care_experience': 'Care experience',
        'young_carer': 'Young carers',
        'neuro': 'Special educational needs and neurodivergence',
        'ethnicity': 'Ethnicity',
        'english_additional': 'English as an additional language',
        'birth': 'Background'
    }

    # Import descriptions for the charts
    response_descrip = create_response_description()

    # This plots measures in loops, basing printed text on the measure names
    # and basing the titles of groups on the group names (which differs to the
    # survey responses page, which bases printed text on group names)
    for plot_group in header_dict.keys():

        # Add the title for that group
        st.header(header_dict[plot_group])

        # Find the measures in that group and loop through them
        measures = chosen_result.loc[
            chosen_result['plot_group'] == plot_group,
            'measure'].drop_duplicates()
        for measure in measures:

            # Add descriptive text if there is any
            if measure in response_descrip.keys():
                st.markdown(response_descrip[measure])

            # Filter to current measure and plot
            to_plot = chosen_result[chosen_result['measure'] == measure]
            survey_responses(to_plot)
