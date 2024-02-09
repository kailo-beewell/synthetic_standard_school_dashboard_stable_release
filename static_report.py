# Generate a non-interactive PDF version of the dashboard

###############################################################################
# Set-up

# Import required packages
import pandas as pd
import os
import weasyprint
import base64
from markdown import markdown
import numpy as np

# Import functions I have defined elsewhere
from utilities.score_descriptions import score_descriptions
from utilities.bar_charts import details_ordered_bar
from utilities.explore_results import (
    write_page_title,
    create_topic_dict,
    write_topic_intro,
    write_response_section_intro,
    get_chosen_result,
    create_bar_charts,
    get_between_schools,
    write_comparison_intro,
    result_box
)

# Create empty list to fill with HTML content for PDF report
content = []

# Set the chosen group and school for this report
chosen_group = 'For all pupils'
chosen_school = 'School A'

# Import data
df_scores = pd.read_csv('data/survey_data/aggregate_scores_rag.csv')
df_prop = pd.read_csv('data/survey_data/aggregate_responses.csv')
counts = pd.read_csv('data/survey_data/overall_counts.csv')

# Create dictionary of topics
topic_dict = create_topic_dict(df_scores)

###############################################################################
# Title page and introduction

# Logo - convert to HTML, then add to the content for the report
data_uri = base64.b64encode(
    open('images/kailo_beewell_logo_padded.png', 'rb').read()).decode('utf-8')
img_tag = f'''
<img src='data:image/png;base64,{data_uri}' alt='Kailo #BeeWell logo'
style='width:300px; height:182px;'>'''
content.append(img_tag)

# Title and introduction
title_page = '''
<div class='section_container'>
    <h1 style='text-align:center;'>The #BeeWell Survey</h1>
    <p style='text-align:center; font-weight:bold;'>
    Thank you for taking part in the #BeeWell survey delivered by Kailo.</p>
    <p>The results from pupils at your school can be explored using the
    interactive dashboard at
    https://synthetic-beewell-kailo-standard-school-dashboard.streamlit.app/.
    This report has been downloaded from that dashboard.<br><br>
    There are four reports available - these have results: (a) from all
    pupils, (b) by gender, (c) by free school meal (FSM) eligibility, and (d)
    by year group.<br><br>
    This report contains the results <b>from all pupils</b>.</p>
</div>
'''
content.append(title_page)

# Illustration - convert to HTML, then add to the content for the report
data_uri = base64.b64encode(
    open('images/home_image_3_transparent.png', 'rb').read()).decode('utf-8')
img_tag = f'''
<img src='data:image/png;base64,{data_uri}' alt='Kailo illustration'
style='width:650px; height:192px;'>'''
illustration = f'''
<div style='width:100%; position:absolute; bottom:0;'>
    {img_tag}
</div>'''
content.append(illustration)

# Introduction page
content.append('''<h1 style='page-break-before:always;'>Introduction</h1>''')

# Using the report (duplicate text with About.py)
content.append('<h2>How to use this report</h2>')
text = '''
These data can provide a useful starting point for discussions about the needs
of your school population and priority areas for development and improvement.
It can also be useful in considering areas of strengths and/or helping pupils
reflect on their positive qualities.

Data in your #BeeWell report may be useful in indicating progress against
targets in your School Improvement Plan or help to identify future target
areas. It may help to identify areas of priority for staff training or be used
as context when considering academic data for participating year groups. It can
also be used as independent evidence in the context of an Ofsted inspection.

Finally, young people consulted during the set-up of #BeeWell in Greater
Manchester felt strongly that pupils should be included in discussions around
feedback, particularly to plan activities and approaches to raise awareness of
strengths or difficulties the #BeeWell survey may highlight. They suggested
involving a range of students (not just those involved in school councils) in
planning how to raise awareness about wellbeing and to support the needs of
young people.'''
content.append(markdown(text))

# Comparison warning (duplicate text with Explore results.py)
content.append('<h2>Comparing between schools</h2>')
text = '''
Always be mindful when making comparisons between different schools. There are
a number of factors that could explain differences in scores (whether you are
above average, average, or below average). These include:

* Random chance ('one-off' findings).
* Differences in the socio-economic characteristics of pupils and the areas
where they live (e.g. income, education, ethnicity, access to services and
amenities).
* The number of pupils taking part - schools that are much smaller are more
likely to have more "extreme" results (i.e. above or below average), whilst
schools with a larger number of pupils who took part are more likely to
see average results

It's also worth noting that the score will only include results from pupils who
completed each of the questions used to calculate that topic - so does not
include any reflection of results from pupils who did not complete some or all
of the questions for that topic.
'''
content.append(markdown(text))

###############################################################################
# Table of contents

# Get all of the explore results pages as lines for the table of contents
explore_results_pages = []
for key, value in topic_dict.items():
    line = f'''<li><a href='#{value}'>{key}</a></li>'''
    explore_results_pages.append(line)

content.append(f'''
<div>
    <h1 style='page-break-before:always;'>Table of Contents</h1>
    <ul>
        <li><a href='#summary'>Summary</a> - See a simple overview of results
            from pupils at your school, compared with other schools</li>
        <br>
        <li><a href='#explore_results'>Explore results</a> - Explore how your
pupils responded to each survey question, and see further information on how
the summary page's comparison to other schools was generated
            <ul>{''.join(explore_results_pages)}</ul>
        </li>
        <br>
        <li><a href='#who_took_part'>Who took part</a> - See the
            characteristics of the pupils who took part in the survey</li>
    </ul>
</div>
''')

###############################################################################
# Summary page

temp_content = []

# Title
title = '''Summary of your school's results'''
temp_content.append(f'''
<h1 style='page-break-before:always;' id='summary'>{title}</h1>''')

# Filter to relevant school and get total school size
school_counts = counts.loc[counts['school_lab'] == chosen_school]
school_size = school_counts.loc[
    (school_counts['year_group_lab'] == 'All') &
    (school_counts['gender_lab'] == 'All') &
    (school_counts['fsm_lab'] == 'All') &
    (school_counts['sen_lab'] == 'All'), 'count'].values[0].astype(int)
descrip = f'''
At your school, a total of {school_size} pupils took part in the #BeeWell
survey. This page shows how the answers of pupils at your school compare with
pupils from other schools in Northern Devon.'''
temp_content.append(f'<p>{descrip}</p>')


def rag_intro_column(rag, rag_descrip):
    '''
    Generate a row for the introduction to the summary section, with a RAG
    box and description of that box across 2 columns.

    Parameters
    ----------
    rag : string
        RAG performance - either 'above', 'average', 'below', or np.nan
    rag_descrip : string
        Description of the RAG rating

    Returns
    -------
    html : string
        Section of HTML that creates the RAG introductory columns
    '''
    rag_box = result_box(rag)
    html = f'''
<div class='row'>
    <div class='column' style='margin-top:0.5em;'>
        {rag_box}
    </div>
    <div class='column'>
        {rag_descrip}
    </div>
</div>
'''
    return html


rag_descrip = '''
This means that average scores for students in your school are **worse** than
average scores for pupils at other schools.'''
temp_content.append(rag_intro_column('below', markdown(rag_descrip)))

rag_descrip = '''
This means that average scores for students in your school are **similar** to
average scores for pupils at other schools.'''
temp_content.append(rag_intro_column('average', markdown(rag_descrip)))

rag_descrip = '''
This means that average scores for students in your school are **better** than
average scores for pupils at other schools.'''
temp_content.append(rag_intro_column('above', markdown(rag_descrip)))

rag_descrip = '''
This means that **less than ten** students in your school completed questions
for this topic, so the results cannot be shown.'''
temp_content.append(rag_intro_column(np.nan, markdown(rag_descrip)))

caveat = f'''
*Please note that  although a total of {school_size} pupils took part, the
topic summaries below are based only on responses from pupils who completed all
the questions of a given topic. The count of pupils who completed a topic is
available on each topic's "Explore results" page. However, the other figures
on the "Explore results" page present data from all pupils who took part.*'''
temp_content.append(markdown(caveat))

content.append(f'''
<div class='page'>
    <div class='section_container'>
        {''.join(temp_content)}
    </div>
</div>
''')

###############################################################################
# Explore results section

content = write_page_title(output='pdf', content=content)


def create_explore_topic_page(chosen_variable_lab, topic_dict, df_scores,
                              chosen_school, counts, content):
    '''
    Add an explore results page with responses to a given topic to report HTML.

    Parameters
    ----------
    chosen_variable_lab : string
        Chosen variable in label format (e.g. 'Psychological wellbeing')
    topic_dict : dictionary
        Dictionary of topics where key is variable_lab and value is variable
    df_scores : dataframe
        Dataframe with scores for each topic
    chosen_school : string
        Name of the chosen school
    counts : dataframe
        Dataframe with the counts of pupils at each school
    content : list
        Optional input used when output=='pdf', contains HTML for report.

    Returns
    -------
    content : list
        Optional return, used when output=='pdf', contains HTML for report.
    '''
    # Convert from variable_lab to variable
    chosen_variable = topic_dict[chosen_variable_lab]

    # Topic header and description
    content = write_topic_intro(chosen_variable, chosen_variable_lab,
                                df_scores, output='pdf', content=content)

    # Section header and description
    content = write_response_section_intro(
        chosen_variable_lab, output='pdf', content=content)

    # Get dataframe with results for the chosen variable, group and school
    chosen_result = get_chosen_result(
        chosen_variable, chosen_group, df_prop, chosen_school)

    # Produce bar charts, plus their chart section descriptions and titles
    content = create_bar_charts(
        chosen_variable, chosen_result, output='pdf', content=content)

    # Create dataframe based on chosen variable
    between_schools = get_between_schools(df_scores, chosen_variable)

    # Write the comparison intro text (title, description, RAG rating)
    content = write_comparison_intro(
        counts, chosen_school, chosen_variable, chosen_variable_lab,
        score_descriptions, between_schools, output='pdf', content=content)

    # Create ordered bar chart
    content = details_ordered_bar(
        school_scores=between_schools, school_name=chosen_school, font_size=16,
        output='pdf', content=content)

    return content


# Create pages for all of the topics
for chosen_variable_lab in topic_dict.keys():
    content = create_explore_topic_page(
        chosen_variable_lab, topic_dict, df_scores,
        chosen_school, counts, content)

###############################################################################
# Create HTML report...

# Remove the final temporary image file
if os.path.exists('report/temp_image.png'):
    os.remove('report/temp_image.png')

# Source Sans Pro is the sans-serif font used by Streamlit, but was having
# issues with getting bold typeface, so switched to use default 'sans-serif'
# which was fine. #05291F is Kailo's dark green colour.
css_style = '''

/* Page style */
/* No background colour (a) for printing (b) avoids problems w/ page number */
body {
    font-family: sans-serif;
    color: #05291F;
}
@page {
    size: A4;
    @top-right{
        content: 'Page ' counter(page) ' of ' counter(pages);
        font-family: sans-serif;
        font-size: 10px;
    }
}

/* DIV container style */
.section_container {
    position: absolute;
    top: 30%;
    justify-content: center;
    align-items: center;
    text-align: center;
}
.responses_container {
    border-radius: 25px;
    border: 2px solid #D7D7D7;
    padding-left: 20px;
    padding-right: 20px;
    padding-top: 15px;
    padding-bottom: 10px;
    page-break-inside: avoid;
}
.comparison_container {
    padding: 5px;
    page-break-inside: avoid;
}
.result_box {
    border-radius: 15px;
    padding: 5px;
    text-align: center;
    page-break-inside: avoid;
}
.page {
    page-break-after: always;
}
.column {
    float: left;
    width: 50%;
}
.row:after {
    content: '';
    display: table;
    clear: both;
}

/* Text style */
p {
    font-size: 14px;
}
li {
    font-size: 14px;
}
.column p {
    font-size: 14px;
}
'''

html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>#BeeWell Kailo School Report 2024</title>
    <style>
        {css_style}
    </style>
</head>
<body>
    {''.join(content)}
</body>
</html>
'''

# Generate HTML (not used currently to make the PDF report, but useful if
# you want to inspect the HTML code we have produced)
with open('report/report.html', 'w') as f:
    f.write(html_content)

# Create PDF using Weasyprint (better)
weasyprint.HTML(string=html_content).write_pdf('report/report.pdf')
