import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

st.set_page_config(page_title="Customize Your Smoothie", page_icon="🥤", layout="centered")

# App Title and Header
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom smoothie!")

# 1) Capture the User's Name
name_on_order = st.text_input('Name on Smoothie:')
if name_on_order:
    st.write('The name on your smoothie will be:', name_on_order)

# 2) Connect to Snowflake and fetch Fruit Options once
@st.cache_data(show_spinner=False)
def load_fruit_options():
    cnx = st.connection("snowflake")
    session = cnx.session()

    sp_df = (
        session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
        .select(col('FRUIT_NAME'), col('SEARCH_ON'))
    )
    # Convert to pandas for Streamlit widgets
    pdf = sp_df.to_pandas()
    return pdf

fruit_options_df = load_fruit_options()
fruit_names = fruit_options_df['FRUIT_NAME'].tolist()
search_on_map = dict(zip(fruit_options_df['FRUIT_NAME'], fruit_options_df['SEARCH_ON']))

# 3) Display the Multi-select Widget (strings only)
ingredients_list = st.multiselect(
    'Select up to 5 fruits:',
    options=fruit_names,
    max_selections=5
)

# 4) Process the Selection
if ingredients_list:
    # Build a nicely formatted string
    ingredients_string = ", ".join(ingredients_list)

    for fruit_chosen in ingredients_list:
        st.subheader(f"{fruit_chosen} Nutrition Information")

        # Lookup the search_on value locally (no Snowflake call per fruit)
        search_on_val = search_on_map.get(fruit_chosen)

        # Defensive check
        if not search_on_val:
            st.warning(f"Could not find SEARCH_ON for {fruit_chosen}.")
            continue

        # Call the SmoothieFroot API
        try:
            url = f"https://my.smoothiefroot.com/api/fruit/{search_on_val}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Show as a tidy table
            df = pd.json_normalize(data)
            st.dataframe(df, use_container_width=True)
        except requests.RequestException as e:
            st.error(f"API error for {fruit_chosen}: {e}")
        except ValueError:
            st.error(f"Unexpected response format for {fruit_chosen}.")

    # 5) Submit the Order
    st.divider()
    submit = st.button('Submit Order')
    if submit:
        if not name_on_order:
            st.warning("Please enter a name for the order before submitting.")
        else:
            # Insert the order into Snowflake
            try:
                cnx = st.connection("snowflake")
                session = cnx.session()

                # Safer insert using the underlying connector cursor for parameter binding
                cursor = session.connection.cursor()
                cursor.execute(
                    "INSERT INTO SMOOTHIES.PUBLIC.ORDERS(INGREDIENTS, NAME_ON_ORDER) VALUES (%s, %s)",
                    (ingredients_string, name_on_order)
                )
                cursor.close()

                st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
            except Exception as ex:
                st.error(f"Could not insert order into Snowflake: {ex}")
