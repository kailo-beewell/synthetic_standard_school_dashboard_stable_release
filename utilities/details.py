'''
Functions used for the streamlit page Details.py
'''
import numpy as np
import plotly.express as px
import streamlit as st
import textwrap as tr
from utilities.colours import linear_gradient

def wrap_text(string, width):
    '''
    Wrap the provided string to the specified width, producing a single string
    with new lines indicated by '<br>'. If string length is less than the
    specified width, add blank space to the start of the string (so it will
    still occupy the same amount of space on the chart)
    Inputs:
    - string: str, to wrap
    - width: int, maximum length per line
    '''
    # Wrap string with new lines indicated by <br>
    wrap = '<br>'.join(tr.wrap(string, width=width))
    # If the whole string is less than the chosen width, at blank spaces to
    # the start to it reaches that width
    if len(wrap) < width:
        blank = width - len(wrap)
        wrap=(' '*blank) + wrap
    # If string is greater than width (will therefore have breaks), at blank
    # space to the beginning of the first line so that it reaches the 
    # maximum width
    elif len(wrap) > width:
        first_line = wrap.split('<br>')[0]
        if len(first_line) < width:
            blank = width - len(first_line)
            wrap=(' '*blank) + wrap
    return(wrap)


def details_stacked_bar(df):
    '''
    Create stacked bar chart for detail page using the provided dataframe,
    which should contain results for one/a set of variables with the same
    response options
    Inputs:
    - df, dataframe - e.g. chosen_result
    '''
    # Get colour spectrum between the provided colours, for all except one category
    # Use 'cat_lab' rather than 'cat' as sometimes cat is 0-indexed or 1-indexed
    start_colour = '#CFE7F0'
    end_colour = '#5D98AB'
    n_cat = df['cat_lab'].drop_duplicates().size
    # If there is a missing category, create n-1 colours and set last as grey
    if df['cat_lab'].eq('Missing').any():
        colours = linear_gradient(start_colour, end_colour, n_cat-1)['hex']
        colours += ['#DDDDDD']
    # Otherwise, just create colour spectrum using all categories
    else:
        colours = linear_gradient(start_colour, end_colour, n_cat)['hex']

    # Wrap the labels for each measure
    df['measure_lab_wrap'] = df['measure_lab'].apply(
        lambda x: wrap_text(x, 50))

    # Create plot
    fig = px.bar(
        df, x='percentage', y='measure_lab_wrap', color='cat_lab',
        text_auto=True, orientation='h', color_discrete_sequence=colours,
        # Resort y axis order to match order of questions in survey
        category_orders={'measure_lab_wrap': 
                         df['measure_lab_wrap'].drop_duplicates().to_list()},
        # Specify what is shown when hover over the chart barts
        hover_data={'cat_lab': True, 'percentage': True,
                    'measure_lab_wrap': False, 'count': True},)

    # Add percent sign to the numbers labelling the bars
    fig.for_each_trace(lambda t: t.update(texttemplate = t.texttemplate + ' %'))

    # Set x axis ticks to include % sign, and remove the axis titles
    fig.update_layout(xaxis = dict(
        tickmode='array',
        tickvals=[0, 20, 40, 60, 80, 100],
        ticktext=['0%', '20%', '40%', '60%', '80%', '100%'],
        title=''))
    fig.update_layout(yaxis_title=None)

    # Set y axis label colour (as defaults to going pale grey)
    fig.update_yaxes(tickfont=dict(color='#05291F'))

    # Set font size
    font_size = 18
    fig.update_layout(
        font = dict(size=font_size),
        xaxis = dict(tickfont=dict(size=font_size)),
        yaxis = dict(tickfont=dict(size=font_size)),
        legend = dict(font_size=font_size)
    )

    # Find number of variables being plot, then set height of figure based on that
    # so the bars appear to be fairly consistent height between different charts
    n_var = df['measure_lab'].drop_duplicates().size
    height = {
        1: 200,
        2: 270,
        3: 350,
        4: 400,
        5: 500,
        6: 600,
        7: 600,
        8: 700,
        9: 800,
        10: 750
    }
    fig.update_layout(autosize=True, height=height[n_var])

    # Make legend horizontal, above axis and centered
    fig.update_layout(
        legend=dict(
            orientation='h',
            xanchor='center',
            x=0.4,
            yanchor='bottom',
            y=1,
            title=''))

    # Disable zooming and panning
    fig.layout.xaxis.fixedrange = True
    fig.layout.yaxis.fixedrange = True

    # Create plot on streamlit app
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def details_ordered_bar(df, school_name):
    '''
    Created ordered bar chart with the results from each school, with the
    chosen school highlighted
    Inputs:
    - df, dataframe with mean score at each school (e.g. between_schools)
    - school_name, string, name of school (matching name in 'school_lab' col)
    '''
    # Add colour for bar based on school
    df['colour'] = np.where(
        df['school_lab']==school_name, 'Your school', 'Other schools')

    # Create column with mean rounded to 2 d.p.
    df['Mean score'] = round(df['mean'], 2)

    # Plot the results, specifying colours and hover data
    fig = px.bar(
        df, x='school_lab', y='mean', color='colour',
        color_discrete_map={'Your school': '#5D98AB', 'Other schools': '#BFD8E0'},
        category_orders={'colour': ['Your school', 'Other schools']},
        hover_data={'school_lab': False, 'colour': False,
                    'mean': False, 'Mean score': True})

    # Reorder x axis so in ascending order
    fig.update_layout(xaxis={'categoryorder':'total ascending'})

    # Set y axis limits so the first and last bars of the chart a consistent height
    # between different plots - find 15% of range and adj min and max by that
    min = df['mean'].min()
    max = df['mean'].max()
    adj_axis = (max - min)*0.15
    ymin = min - adj_axis
    ymax = max + adj_axis
    fig.update_layout(yaxis_range=[ymin, ymax])

    # Extract lower and upper rag boundaries amd shade the RAG areas
    # (Colours used were matched to those from the summary page)
    lower = df['lower'].to_list()[0]
    upper = df['upper'].to_list()[0]
    fig.add_hrect(y0=ymin, y1=lower, fillcolor='#F8DCDC', layer='below',
                line={'color': '#9A505B'}, line_width=0.5,
                annotation_text='Below average', annotation_position='top left')
    fig.add_hrect(y0=lower, y1=upper, fillcolor='#F8ECD4', layer='below',
                line={'color': '#B3852A'}, line_width=0.5,
                annotation_text='Average', annotation_position='top left')
    fig.add_hrect(y0=upper, y1=ymax, fillcolor='#E0ECDC', layer='below',
                line={'color': '#3A8461'}, line_width=0.5,
                annotation_text='Above average', annotation_position='top left')

    # Set font size and hide x axis tick labels (but seems to be a bug that
    # means the axis label is then above the plot, so had to use a work around
    # of replacing the axis labels with spaces
    font_size = 18
    fig.update_layout(
        font = dict(size=font_size),
        xaxis = dict(title='Northern Devon schools (ordered by mean score)',
                     title_font_size=font_size,
                     tickvals=df['school_lab'],
                     ticktext=[' ']*len(df['school_lab'])),
        yaxis = dict(title='Mean score',
                     title_font_size=font_size,
                     tickfont=dict(size=font_size)),
        legend = dict(font_size=font_size),
        legend_title_text=''
    )

    # Prevent zooming and panning, remove grid, and hide plotly toolbar
    fig.layout.xaxis.fixedrange = True
    fig.layout.yaxis.fixedrange = True
    fig.update_yaxes(showgrid=False)

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})