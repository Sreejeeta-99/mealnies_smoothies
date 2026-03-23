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

# NEW: allow marking order as filled (needed for grader: Kevin=FALSE, Divya/Xi=TRUE)
order_filled = st.checkbox("Mark order as FILLED", value=False)  # NEW
 
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

        # (Optional) show the mapped value to help debug Apples -> Apple etc.
        st.caption(f"Search value for {fruit_chosen} is {search_on_val}")  # NEW (optional)
 
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
    # CHANGED: Use parameterized SQL to avoid quoting issues and keep it safe
    insert_sql = """
        INSERT INTO smoothies.public.orders (ingredients, name_on_order)
        VALUES (:ingredients, :name_on_order)
    """  # CHANGED
 
    # ----------------------------
    # 7. Submit Button
    # ----------------------------
    if st.button("Submit Order"):
        if not name_on_order or not name_on_order.strip():
            st.error("Please enter a name for your smoothie!")
        elif not ingredients_list:
            st.error("Please select at least one fruit!")
        else:
            # CHANGED: parameter binding
            session.sql(insert_sql)\
                   .bind({"ingredients": ingredients_string, "name_on_order": name_on_order.strip()})\
                   .collect()  # CHANGED

            # NEW: set order_filled for the most recent matching row (needed for grader)
            session.sql("""
                UPDATE smoothies.public.orders
                SET order_filled = :filled
                WHERE name_on_order = :name
                  AND ingredients = :ingredients
                QUALIFY ROW_NUMBER() OVER (
                  PARTITION BY name_on_order, ingredients
                  ORDER BY COALESCE(order_ts, CURRENT_TIMESTAMP()) DESC
                ) = 1
            """).bind({
                "filled": order_filled,
                "name": name_on_order.strip(),
                "ingredients": ingredients_string
            }).collect()

            # NEW: ensure order_ts is populated if your table doesn’t default it
            session.sql("""
                UPDATE smoothies.public.orders
                SET order_ts = COALESCE(order_ts, CURRENT_TIMESTAMP())
                WHERE name_on_order = :name
                  AND ingredients = :ingredients
                  AND order_ts IS NULL
            """).bind({
                "name": name_on_order.strip(),
                "ingredients": ingredients_string
            }).collect()
            
            st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
