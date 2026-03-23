import streamlit as st
from snowflake.snowpark.functions import col
import requests
 
# ----------------------------
# 1. App Title and Header
# ----------------------------
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom smoothie!")
 
# ----------------------------
# 2. Capture the User's Name
# ----------------------------
name_on_order = st.text_input("Name on Smoothie:")
if name_on_order:
    st.write("The name on your smoothie will be:", name_on_order)
 
# ----------------------------
# 3. Connect to Snowflake and fetch Fruit Options
# ----------------------------
cnx = st.connection("snowflake")
session = cnx.session()
 
# Fetch fruit options from Snowflake
fruit_df = session.table("smoothies.public.fruit_options").select(
    col("FRUIT_NAME"), col("SEARCH_ON")
).collect()  # Collect into a list of rows
 
# Create a mapping from FRUIT_NAME -> SEARCH_ON
fruit_map = {row["FRUIT_NAME"]: row["SEARCH_ON"] for row in fruit_df}
 
# Convert fruit names to a list for the multi-select widget
fruit_names = list(fruit_map.keys())
 
# ----------------------------
# 4. Display the Multi-select Widget
# ----------------------------
ingredients_list = st.multiselect(
    "Select up to 5 fruits:",
    options=fruit_names,
    max_selections=5
)
 
# ----------------------------
# 5. Process the Selection
# ----------------------------
if ingredients_list:
    # Join ingredients for SQL insert
    ingredients_string = ", ".join(ingredients_list)
 
    for fruit_chosen in ingredients_list:
        search_on_val = fruit_map[fruit_chosen]
 
        st.subheader(f"{fruit_chosen} Nutrition Information")
 
        # Call the SmoothieFroot API
        smoothiefroot_response = requests.get(
            f"https://my.smoothiefroot.com/api/fruit/{search_on_val}"
        )
        # Display API data in a dataframe
        sf_df = st.dataframe(
            data=smoothiefroot_response.json(),
            use_container_width=True
        )
 
    # ----------------------------
    # 6. Build the SQL Insert Statement
    # ----------------------------
    my_insert_stmt = f"""
    INSERT INTO smoothies.public.orders (ingredients, name_on_order)
    VALUES ('{ingredients_string}', '{name_on_order}')
    """
 
    # ----------------------------
    # 7. Submit Button
    # ----------------------------
    if st.button("Submit Order"):
        if not name_on_order.strip():
            st.error("Please enter a name for your smoothie!")
        elif not ingredients_list:
            st.error("Please select at least one fruit!")
        else:
            session.sql(my_insert_stmt).collect()
            st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
 
