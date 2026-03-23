import streamlit as st
from snowflake.snowpark.functions import col
import requests
 
# App Title and Header
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("""Choose the fruits you want in your custom smoothie!""")
 
# 1. Capture the User's Name
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your smoothie will be:', name_on_order)
 
# 2. Connect to Snowflake and fetch the Fruit Options
cnx = st.connection("snowflake")
session = cnx.session()
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
 
# 3. Display the Multi-select Widget
ingredients_list = st.multiselect(
    'Select up to 5 fruits:',
    my_dataframe,
    max_selections=5
)
 
# 4. Process the Selection
if ingredients_list:
    ingredients_string = ''
 
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # Pull the SEARCH_ON value for the specific fruit to ensure API success
        search_on_val = my_dataframe.filter(col('FRUIT_NAME') == fruit_chosen).collect()[0]['SEARCH_ON']
        st.write('The search value for ', fruit_chosen, ' is ', search_on_val, '.')
        
        st.subheader(fruit_chosen + ' Nutrition Information')
        
        # Call the SmoothieFroot API using the search_on_val
        smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/" + search_on_val)
        sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
 
    # 5. Build the SQL Insert Statement (Outside the loop, inside the IF)
    my_insert_stmt = """ insert into smoothies.public.orders(ingredients, name_on_order)
                values ('""" + ingredients_string + """', '""" + name_on_order + """')"""
 
    # 6. Create the Submit Button
    time_to_insert = st.button('Submit Order')
 
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered, ' + name_on_order + '!', icon="✅")
