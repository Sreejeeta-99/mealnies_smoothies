# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
 
# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom smoothie!
    """
)
 
# Input for the name on the order
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your smoothie will be:', name_on_order)
 
# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()
 
# Fetch table data including the new SEARCH_ON column
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
 
# Multiselect widget
ingredients_list = st.multiselect(
    'Select up to 5 fruits:',
    my_dataframe,
    max_selections=5
)
 
if ingredients_list:
    ingredients_string = ''
 
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # Look up the search value for the API call
        search_on_val = my_dataframe.filter(col('FRUIT_NAME') == fruit_chosen).collect()[0]['SEARCH_ON']
        st.write('The search value for ', fruit_chosen, ' is ', search_on_val, '.')
        
        st.subheader(fruit_chosen + ' Nutrition Information')
        
        # Call the SmoothieFroot API using the SEARCH_ON value
        smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/" + search_on_val)
        sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
 
    # Build the SQL Insert Statement
    my_insert_stmt = """ insert into smoothies.public.orders(ingredients, name_on_order)
                values ('""" + ingredients_string + """', '""" + name_on_order + """')"""
 
    # Create a button to submit the order
    time_to_insert = st.button('Submit Order')
 
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered, ' + name_on_order + '!', icon="✅")
 
