# Import python packages
import streamlit as st
#from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col

# Write directly to the app
st.title("🥤 Customize Your Smoothie!")
st.write(
  """Replace this example with your own code!
  **And if you're new to Streamlit,** check
  out our easy-to-follow guides at
  [docs.streamlit.io](https://docs.streamlit.io).
  """
)
 
#st.write("Choose the fruits you want in your custom smoothie!")
#option = st.selectbox(
#    "What is your favorite fruit?",
#    ("Banana", "Strawberries", "Peaches")
#)
#st.write("Your favorite fruit is:", option)


 
name_on_order = st.text_input('Name on smoothie')
st.write('The name on your smoothie will be', name_on_order)

cnx = st.connection("snowflake")
session = cnx.session

#session = get_active_session()
#fetch table data
my_dataframe = session.table("smoothies.public.fruit_options").select (col('fruit_name'))
#display data in app
st.dataframe(data=my_dataframe, use_container_width=True)

# Multiselect widget
ingredients_list = st.multiselect("Select up to 5 fruits:",my_dataframe, max_selections=5)
 
# Show selected fruits
if ingredients_list:
    st.write(ingredients_list)
    st.text(ingredients_list)

    ingredients_string = ''
    for i in ingredients_list:
        ingredients_string += i + " "
    #st.write(ingredients_string)

    # Updated SQL string to include the second column name
    my_insert_stmt = """ insert into smoothies.public.orders(ingredients, name_on_order)
            values ('""" + ingredients_string + """', '""" + name_on_order + """')"""
 
     #st.write(my_insert_stmt)

    st.write(my_insert_stmt)
    #st.stop()
    
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt).collect()

        st.success('Your Smoothie is ordered!', icon="✅")
        
