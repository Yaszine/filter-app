import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import base64
from pathlib import Path
from functions import display_image, img_to_html, img_to_bytes, dataframe_to_html, simplify_comment, background_colorize, sort_by_mean_difference, save_shapefile_to_zip, sort_by_mean
from functions import apply_page_config_and_styles
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import firebase_admin
from firebase_admin import credentials, firestore
import time
import geopandas as gpd
import pandas as pd

from image_function import load_image_and_prediction, modify_image, display_image_API
# Set Streamlit page configuration


apply_page_config_and_styles()




# Function to load shapefile based on selected municipality
def load_shapefile(municipality):
    shapefile_paths = {
        "Ringsted": '../Ringsted/Koordinat_2020_stats.shp',
        "Copenhagen": '../Copenhagen/Koordinat_2020_stats.shp',
        "Roskilde": '../Roskilde/Koordinat_2020_stats.shp',
        "Høje Taastrup": '../Høje_Taastrup/Koordinat_2020_stats.shp'
    }
    if municipality in shapefile_paths:
        return gpd.read_file(shapefile_paths[municipality])
    else:
        st.error("Selected municipality does not have an available shapefile.")
        return None

# Improved login page for selecting the municipality
def login_page():
    st.markdown(
        """
        <style>
        body {
            background: linear-gradient(to bottom right, #052418, #1a472a);  /* Gradient background */
        }
        .login-container {
            background-color: #083c2b;  /* Dark green background */
            padding: 30px;
            border-radius: 15px;  /* Rounded corners */
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.25);  /* Subtle shadow */
            max-width: 400px;  /* Max width for the container */
            margin: auto;  /* Center the container */
            margin-top: 100px;  /* Center vertically */
            text-align: center;  /* Center text */
        }
        .login-title {
            font-size: 24px;  /* Larger title font size */
            font-weight: bold;  /* Bold title */
            color: white;
            margin-bottom: 20px;  /* Space below title */
        }
        .login-selectbox, .login-button {
            margin-top: 20px;  /* Space above the selectbox and button */
        }
        .login-button button {
            background-color: #1a472a;  /* Button background color */
            color: white;  /* Button text color */
            border: none;  /* No border */
            padding: 10px 20px;  /* Button padding */
            border-radius: 8px;  /* Rounded button */
            cursor: pointer;  /* Pointer cursor on hover */
            transition: background-color 0.3s ease;  /* Transition effect */
        }
        .login-button button:hover {
            background-color: #145a35;  /* Darker green on hover */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Login form container
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    
    # Title
    st.markdown("<div class='login-title'>Lake Geometry Analysis Tool - Login</div>", unsafe_allow_html=True)
    
    # Municipality selection
    municipalities = ["Copenhagen", "Ringsted", "Roskilde", "Høje Taastrup"]
    selected_municipality = st.selectbox("Select Municipality", municipalities, key='municipality', label_visibility='collapsed', help="Select your municipality from the list.")
    
    # Button to confirm selection and proceed
    if st.button("Load Data", key='load_data', use_container_width=True):
        # Load the shapefile for the selected municipality
        predicted_gdf = load_shapefile(selected_municipality)
        if predicted_gdf is not None:
            st.session_state["predicted_gdf"] = predicted_gdf
            st.session_state["municipality_selected"] = True
            st.success(f"Data loaded for {selected_municipality}!")
            #st.experimental_rerun()  # Refresh the page to move to the main application
        else:
            st.error("Failed to load the shapefile. Please try again.")
    
    st.markdown("</div>", unsafe_allow_html=True)  # Close login container

# Main application function
def main():
    if "municipality_selected" not in st.session_state or not st.session_state["municipality_selected"]:
        login_page()  # Display login page if no municipality is selected
    else:
        # Proceed with the main application logic
        st.title(f"Lake Geometry Analysis")# - {st.session_state['municipality_selected']}")
        # Initialize Firestore DB

    
######

                # Initialize Firestore DB
        if 'firebase_initialized' not in st.session_state:
            if not firebase_admin._apps:
                # Use the downloaded service account key
                cred = credentials.Certificate("./streamlitkoordinat-firebase-adminsdk-i88eo-174da6429f.json")
                firebase_admin.initialize_app(cred)
            st.session_state.firebase_initialized = True

        db = firestore.client()
        # Function to load feedback data from Firestore

        #@st.cache_data
        def load_feedback_data():
            feedback_ref = db.collection('feedback')
            feedback_docs = feedback_ref.stream()

            feedback_data = []
            for doc in feedback_docs:
                feedback_data.append(doc.to_dict())

            return pd.DataFrame(feedback_data)
        # Load feedback if it exists in Firestore

        #predicted_gdf = gpd.read_file('../classified/Koordinat_2020_stats.shp')  # Replace with your file path
        predicted_gdf = gpd.read_file('../prediction_final/merged_shapefile.shp')# Replace with your file path
        try:
            feedback_df = load_feedback_data()
            if not feedback_df.empty:
                # Merge the feedback data with the GeoDataFrame
                predicted_gdf = predicted_gdf.merge(feedback_df[['Objekt_id', 'agreeness', 'comment_consultant']], on='Objekt_id', how='left')
        except Exception as e:
            st.error(f"Error loading feedback data: {e}")


        def save_feedback_to_firestore(objekt_id, agreeness, comment):
            feedback_ref = db.collection('feedback').document(str(objekt_id))
            feedback_ref.set({
                'Objekt_id': objekt_id,
                'agreeness': agreeness,
                'comment_consultant': comment
            })
        ####


        st.markdown(
            """
            <style>
            .fixed-bottom-right {
                position: fixed;
                bottom: 10px;
                right: 10px;
                z-index: 100;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Displaying the image using the custom CSS class
        st.markdown(
            f"<div class='fixed-bottom-right'>{img_to_html('./logokoordinat.png')}</div>", 
            unsafe_allow_html=True
        )



        color_dict = {
            "1": 'darkred', "2": 'firebrick', "3": 'red', "4": 'grey', "5": 'lightgreen', "6": 'forestgreen', "7": 'darkgreen', "5/4" : 'red' }


        colors = [
            ("1", "darkred"),
            ("2", "firebrick"),
            ("3", "red"),
            ("4", "grey"),
            ("5", "lightgreen"),
            ("6", "forestgreen"),
            ("7", "darkgreen"),
        # ("5/4", "red")
        ]
        color_map = {label: color for label, color in colors}

        def apply_color(val):
            return f'background-color: {color_map.get(val, "white")}; color: {color_map.get(val, "black")}'


        # Function to initialize session state if not set
        def initialize_session_state():
            if "filtered_df" not in st.session_state:
                st.session_state.filtered_df = display_gdf.copy()
            if "selected_color" not in st.session_state:
                st.session_state.selected_color = {color: False for _, color in colors}
            if "filter_option" not in st.session_state:
                st.session_state.filter_option = "Alle"  # Set default value to "All"
            if "selected_year_range" not in st.session_state:
                st.session_state.selected_year_range = (15, 24) ## YEAR MODIF


        # Function to reset checkbox selection
        def reset_color():
            for color in st.session_state.selected_color:
                st.session_state.selected_color[color] = False
                st.session_state[f"checkbox_{color}"] = False  # Also reset the checkbox state 
            
            #st.sess
            

        def reset():
            for color in st.session_state.selected_color:
                st.session_state.selected_color[color] = False
                st.session_state[f"checkbox_{color}"] = False  # Also reset the checkbox state 
            
            st.session_state.filter_option = "Alle"  # Reset the radio button to "All"
            st.session_state.selected_year_range = (15, 24) ## YEAR MODIF
            #st.sess
            




        # Map colors and prepare display dataframe
        #for year in [2019,2020]:
        #    predicted_gdf[str(year)] = predicted_gdf[str(year)].map(color_dict).fillna('black')

            
        display_gdf = predicted_gdf#.drop(columns=['new_color']).rename(columns={'color': '2020'})
        objekt_id_to_display = None

        # Drop unnecessary columns and prepare display DataFrame
        #display_gdf = display_gdf[['Objekt_id', '2020', 'kommentar']]
        for year in [2015, 2016, 2017, 2018, 2021, 2022, 2023, 2024]:
            display_gdf[str(year)] = display_gdf['2020'].sample(frac=1).reset_index(drop=True)
        #value between 2018 and 2024

        display_gdf['sys_frid'] = np.random.choice([2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024], size=len(display_gdf))
        display_gdf = display_gdf[['Objekt_id', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', 'kommentar', 'sys_frid', 'agreeness', 'comment_consultant', 'geometry']]

        display_gdf['kommentar'] = display_gdf['kommentar'].apply(simplify_comment)
        #create a sys_frid column that take random value from 2018 to 2024

        # change the year 2015 to 15, 2016 to 16... 2020 to 20
        display_gdf.columns = display_gdf.columns.str.replace('2015', '15')
        display_gdf.columns = display_gdf.columns.str.replace('2016', '16')
        display_gdf.columns = display_gdf.columns.str.replace('2017', '17')
        display_gdf.columns = display_gdf.columns.str.replace('2018', '18')
        display_gdf.columns = display_gdf.columns.str.replace('2019', '19')
        display_gdf.columns = display_gdf.columns.str.replace('2020', '20')
        display_gdf.columns = display_gdf.columns.str.replace('2021', '21')
        display_gdf.columns = display_gdf.columns.str.replace('2022', '22')
        display_gdf.columns = display_gdf.columns.str.replace('2023', '23')
        display_gdf.columns = display_gdf.columns.str.replace('2024', '24')


        #replace all the value of the column 15-24  '5/4' to '5' 
        display_gdf = display_gdf.replace('5/4', '5')


        # Initialize session state
        initialize_session_state()

        # Sidebar Filters
        st.sidebar.header("Filterindstillinger")

        # Define the range of years available for selection
        years = list(range(15, 25)) ## YEAR MODIF

        selected_year_range = st.sidebar.slider(
            "Vælg årsinterval",
            min_value=min(years),
            max_value=max(years),
            value=st.session_state.selected_year_range,  # Use session state for default value
            step=1
        )


        # Extract unique and simplified comments for selection
        unique_kommentars = sorted(display_gdf['kommentar'].dropna().unique())
        selected_comment = st.sidebar.selectbox("Filtrer efter kommentar", options=["Alle"] + unique_kommentars)

        # Year for color filter selection
        col1, col2 = st.sidebar.columns([3, 4])
        with col1:
            st.markdown("<p class='sidebar-text'>Vælg farver i:</p>", unsafe_allow_html=True)
        with col2:
            selected_year_for_color = st.selectbox(
                "År for farvefilter",
                options=[str(year) for year in range(selected_year_range[0], selected_year_range[1] + 1)],
                label_visibility="collapsed",
                key="year_color_filter",
                on_change=reset_color  # Call the reset function when selection changes
            )



        # Create checkboxes for colors
        selected_color = []
        cols = st.sidebar.columns([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])  
        for idx, color in enumerate(["1", "2", "3", "4", "5", "6", "7"]):
            with cols[idx]:
                st.markdown(
                    f"<div style='height: 10px; width: 19px; background-color: {color_dict[color]}; border-radius: 5px; border-color: black; border-width: 1em;'></div>",
                    unsafe_allow_html=True
                )
                is_selected = st.checkbox(
                    "",  
                    key=f"checkbox_{color_dict[color]}",  
                    value=st.session_state.selected_color[color_dict[color]],  # Use session state for default value
                )
                st.session_state.selected_color[color] = is_selected
                if is_selected:
                    selected_color.append(color)

        #time.sleep(1)

        selected_id = st.sidebar.text_input("Enter Objekt ID")



        #selected_id = selected_id.strip() 

        # button to filter out the consultant comment if there is or isn't so two buttons
        filter_option = st.sidebar.radio(
            "Filtrer efter konsulentkommentar:",
            ("Alle", "Med", "Uden"), horizontal=True, key="filter_option"
        )

        # Button to reset color selection
        colx, coly, colz = st.sidebar.columns(3)
        with colx:
            pass
        with coly:
            selected_reset =  st.sidebar.button("Nulstil",on_click=reset)
        with colz:
            pass
            

        # Sorting options in the sidebar
        st.sidebar.header("Sorteret Efter")
        selected_green_to_red = st.sidebar.button("Sorter fra Grøn til Rød")
        selected_red_to_green = st.sidebar.button("Sorter fra Rød til Grøn")
        selected_all_red = st.sidebar.button("Mest Rød")
        selected_all_green = st.sidebar.button("Mest Grøn")
        selected_alphabetical = st.sidebar.button("Alfabetisk")
        selected_sys_frid = st.sidebar.button("Sys Frid")

        # Data processing and filtering logic
        filtered_df = st.session_state.filtered_df.copy()
        selected_years = list(range(selected_year_range[0], selected_year_range[1] + 1))
        year_columns = [str(year) for year in selected_years if str(year) in filtered_df.columns]

        if selected_years:
            filtered_df = filtered_df[['Objekt_id'] + year_columns + ['kommentar']+ ['sys_frid'] + ['agreeness'] + ['comment_consultant']] ### !!!!!! sys_frid
            if selected_color and selected_year_for_color in year_columns:
                filtered_df = filtered_df[filtered_df[selected_year_for_color].isin(selected_color)]
            if selected_comment != "Alle":
                filtered_df = filtered_df[filtered_df['kommentar'].str.contains(selected_comment, na=False)]
            if selected_id:
                filtered_df = filtered_df[filtered_df['Objekt_id'].str.contains(selected_id, na=False)]
            if selected_reset:
                filtered_df = display_gdf.copy()
            # Filtering the dataframe based on user selection
            if filter_option == "Med":
                filtered_df = filtered_df[filtered_df['comment_consultant'].notnull()]
            elif filter_option == "Uden":
                filtered_df = filtered_df[filtered_df['comment_consultant'].isnull()]
            else:
                filtered_df = filtered_df



            # Sort and display data based on user choices
            if selected_red_to_green:
                filtered_df = sort_by_mean_difference(filtered_df, selected_years[0], selected_years[-1], sort_order=False)
            elif selected_green_to_red:
                filtered_df = sort_by_mean_difference(filtered_df, selected_years[0], selected_years[-1], sort_order=True)
            elif selected_all_red:
                filtered_df = sort_by_mean(filtered_df, selected_years[0], selected_years[-1], sort_order=True)
            elif selected_all_green:
                filtered_df = sort_by_mean(filtered_df, selected_years[0], selected_years[-1], sort_order=False)
            elif selected_alphabetical:
                filtered_df = filtered_df.sort_values('kommentar')
            elif selected_sys_frid:
                filtered_df = filtered_df.sort_values('sys_frid')

            # Save filtered state and display results
            st.session_state.filtered_df = filtered_df
            #col1, col2 = st.columns([4, 3])

            #with col1:
            st.markdown("<div align='center'><h3>Filtreret DataFrame</h3></div>", unsafe_allow_html=True)

            #st.dataframe supports pandas styler only support background color, font color & display values and not set_table_styles....##
            


            event = st.dataframe(
                st.session_state.filtered_df[["Objekt_id"] + year_columns + ["kommentar"] + ["sys_frid"] + ['agreeness'] + ['comment_consultant']].style.applymap(
                    apply_color, subset=year_columns
                ),
                column_config={
                    "Objekt_id": st.column_config.Column(
                        width="small"
                    ),
                },

                use_container_width=True,
                on_select="rerun",
                selection_mode='single-row',  # Add selection mode for each row
                hide_index=True,  # Drop index column
            )

            #event.selection


            #list index not  out of range
            if event.selection and event.selection["rows"]:
                number_selected = int(event.selection["rows"][0])
                objekt_id_to_display = st.session_state.filtered_df.iloc[number_selected]['Objekt_id']
                #print(objekt_id_to_display)
                #print(number_selected)



            if len(filtered_df) == len(display_gdf):
                st.markdown(f"<div align='center'>Total Længde: {len(filtered_df)}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div align='center'>Filtreret: {len(filtered_df)} ud af {len(display_gdf)} valgte områder</div>", unsafe_allow_html=True)

            col10, col11, col12 , col13, col14 = st.columns(5)
            with col10:
                pass
            with col11:
                pass
            with col13:
                pass
            with col14:
                pass
            with col12 :
                
                # Add logic for the button
                col_button_center = st.columns([1, 1.75, 1])
                with col_button_center[1]:
                    if st.button("Gemme", key="save_button"):
                        if not isinstance(filtered_df, gpd.GeoDataFrame):
                            filtered_df = gpd.GeoDataFrame(filtered_df, geometry=predicted_gdf.geometry)
                        filtered_df.to_file("filtered_output.shp")
                        save_shapefile_to_zip(filtered_df, "filtered_output.zip")
                        st.success("Gemt")


        ###################  DISPLAY IMAGE  ####################

        #with col2:
            st.markdown("<div class='summary-box'>", unsafe_allow_html=True) #truc vert bizzare 
            
            # Title for the box
            st.markdown("<div align='center'><h3>Vis Billede</h3></div>", unsafe_allow_html=True)
            
            
            # Checkboxes for `show_label` and `show_prediction` options
            col_image, col_option  = st.columns(2)

            with col_option:
                display_options = st.radio("Visningsmuligheder", ("Begge", "Etiket", "Forudsigelse", "Skjul Alle"),  horizontal=True)

                # Determine boolean values based on selected option
                show_label = display_options in ("Begge", "Etiket")
                show_prediction = display_options in ("Begge", "Forudsigelse")

                display_choices = st.radio("Visningsvalg", ("image", "nir", "context", "nir_context", "dem_data"), horizontal=True)

                st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
                st.write("Venligst giv din feedback:")

                agreeness = st.radio("Er du enig i forudsigelsen?", ("Enig", "Uenig"), horizontal=True)
                consultant_comment = st.text_area("Konsulent Kommentar", "", height=100)

                if 'gdf_copy' not in st.session_state:
                    st.session_state.gdf_copy = predicted_gdf.copy()
                    st.session_state.gdf_copy['agreeness'] = None
                    st.session_state.gdf_copy['comment_consultant'] = None

                if st.button("OK"):
                    st.session_state.gdf_copy.loc[st.session_state.gdf_copy['Objekt_id'] == objekt_id_to_display, 'agreeness'] = (agreeness == "Enig")
                    st.session_state.gdf_copy.loc[st.session_state.gdf_copy['Objekt_id'] == objekt_id_to_display, 'comment_consultant'] = consultant_comment

                    save_feedback_to_firestore(objekt_id_to_display, agreeness == "Enig", consultant_comment)
                    st.success("Din feedback er blevet tilføjet succesfuldt.")
                    st.write(st.session_state.gdf_copy[st.session_state.gdf_copy['agreeness'].notnull()][['Objekt_id', 'agreeness', 'comment_consultant']])

            with col_image:
                selected_year = st.selectbox("Vælg År", options=[2018, 2019, 2020, 2021, 2022, 2023, 2024], index=2)
                if (objekt_id_to_display in filtered_df['Objekt_id'].astype(str).values) and (objekt_id_to_display is not None):
                    try:
                        #image, prediction, bbox = load_image_and_prediction(display_gdf, objekt_id_to_display, selected_year, image_chosen=display_choices)
                        #modified_image = modify_image(image, prediction, bbox, display_gdf, show_label, show_prediction)
                        modified_image = display_image_API(display_gdf, objekt_id_to_display, selected_year, show_label=show_label, show_prediction=show_prediction, image_chosen=display_choices)
                        st.image(modified_image, use_column_width=True)
                    except FileNotFoundError as e:
                        st.error(str(e))
                else:
                    st.warning("Vælg venligst et Objekt_id fra DataFrame.")
        # else:
        #     # Display message if no years are selected
        #     st.markdown("<div align='center'><h3 style='color: red;'>Ingen År Valgt</h3></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()