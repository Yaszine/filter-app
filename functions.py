import matplotlib.pyplot as plt
import numpy as np
from skimage import measure  # Import necessary for contouring
import streamlit as st
import base64
from pathlib import Path
import pandas as pd
import os
import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import time
import rasterio
from rasterio.features import rasterize
import matplotlib.pyplot as plt
import streamlit as st
from shapely.geometry import box

def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded

def img_to_html(img_path):
    img_html = "<img src='data:image/png;base64,{}' class='logo' style='width:300px;'>".format(
      img_to_bytes(img_path)
    )
    return img_html





def background_colorize(val):
    color = val if val in ['red', 'green', 'lightgreen', 'grey', 'darkgreen', 'darkred', 'firebrick', 'forestgreen'] else 'black'
    return f'background-color: {color}; color: {color}'


def simplify_comment(comment):
    if pd.isna(comment):
        return ''
    # Keep only the first 3 words or characters up to a reasonable length
    words = comment.split()
    if len(words) > 5:
        return ' '.join(words[:5]) + '...'
    return comment


import numpy as np
import matplotlib.pyplot as plt
from skimage import measure  # Import necessary for contouring

def display_image(object_id, year, show_label=True, show_prediction=True, image_chosen = 'images'):
    """
    Returns a modified image with contours for label and prediction based on user selection.
    
    Parameters:
        object_id (str): The object ID to identify the image file.
        year (str): The year to identify the image file.
        show_label (bool): Whether to display the label on the image. Defaults to True.
        show_prediction (bool): Whether to display the prediction on the image. Defaults to True.
    
    Returns:
        np.ndarray: The modified image with contours as an RGB array.
    """
    
    
    # Construct paths to the files
    image_path = f"./{image_chosen}/{object_id}_{year}.npy" 
    label_path = f"./labels/{object_id}_2016.npy"
    prediction_path = f"./predictions/{object_id}_{year}.npy"

    try:
        # Load the image, label, and prediction arrays
        image = np.load(image_path)
        label = np.load(label_path)
        prediction = np.load(prediction_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"One or more files for Objekt ID {object_id} in year {year} are missing.")
    
    # Ensure the image is in a format suitable for RGB display
    if image.ndim == 2:  # If grayscale, convert to RGB
        modified_image = np.stack((image,) * 3, axis=-1)
    elif image.ndim == 3 and image.shape[2] == 1:  # If single-channel but 3D
        modified_image = np.repeat(image, 3, axis=2)
    else:
        modified_image = image.copy()

    # Create a prediction mask based on a threshold
    prediction_mask = prediction > 0.7
    if image_chosen == 'context':
        show_label = False
        show_prediction = False

    # Overlay contours for label if required
    if show_label:
        label_contours = measure.find_contours(label, 0.5)  # Find contours in label
        for contour in label_contours:
            for coord in contour:
                y, x = int(coord[0]), int(coord[1])
                modified_image[y, x] = [0, 255, 0]  # Green color for label contours

    # Overlay contours for prediction if required
    if show_prediction:
        prediction_contours = measure.find_contours(prediction_mask, 0.5)  # Find contours in prediction
        for contour in prediction_contours:
            for coord in contour:
                y, x = int(coord[0]), int(coord[1])
                modified_image[y, x] = [255, 0, 0]  # Red color for prediction contours

    return modified_image




# Convert the DataFrame to HTML with custom CSS for styling
def dataframe_to_html(df):
    # Convert DataFrame to HTML without index
    df_html = df.to_html(index=False, escape=False)

    # Add custom CSS to control column widths and alignment
    custom_css = """
    <style>
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th, td {
        border: 1px solid #dddddd;
        text-align: center;
        padding: 8px;
    }
    th {
        background-color: #052418;
        color: white;
    }
    td {
        background-color: #052418;
        color: white;
    }
    .col-Objekt_id {
        width: 50px;  /* Adjust width for 'Objekt_id' */
    }
    </style>
    """
    
    # Inject the custom CSS into the HTML
    styled_html = custom_css + df_html
    return styled_html








import zipfile
import io

def save_shapefile_to_zip(gdf, zip_filename="consultant_output.zip"):
    # Create an in-memory buffer
    memory_zip = io.BytesIO()

    # Write shapefile to a temporary directory
    with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        with io.BytesIO() as shp_buffer:
            gdf.to_file(shp_buffer, driver='ESRI Shapefile')
            shp_buffer.seek(0)
            zf.writestr("consultant_output.shp", shp_buffer.getvalue())
        # Repeat the same process for other necessary files (.shx, .dbf, .prj)
    
    memory_zip.seek(0)  # Rewind the buffer
    return memory_zip

def sort_by_mean(df, begin_year, end_year, sort_order=True):  
    # Step 1: Define the colors for magnitude calculation
    colors = [
        ("-100", "1"),
        ("-110", "2"),
        ("-120", "3"),
        ("0", "4"),  #downgrade to 3 for mostlyGREEN ?
        ("100", "5"),
        ("110", "6"),
        ("120", "7"),
    ]

    color_to_value = {color: int(value) for value, color in colors}

    def convert_color_to_value(color):
        return color_to_value.get(color, np.nan) 

    
    # Convert each column from color to value
    for year in range(begin_year, end_year + 1):
        df[str(year)] = df[str(year)].map(convert_color_to_value)

    
    df["mean"] = df[[str(year) for year in range(begin_year, end_year + 1)]].mean(axis=1)

    #sort the dataframe based on the mean
    df_sorted = df.sort_values(by='mean', ascending=sort_order).reset_index(drop=True)

    #convert the numeric values back to colors
    def convert_value_to_color(value):
        for val, color in colors:
            if int(value) == int(val):
                return color
        return 'black'  # Return black if value is not found
    
    # Convert each column from value to color
    for year in range(begin_year, end_year + 1):
        df_sorted[str(year)] = df_sorted[str(year)].apply(convert_value_to_color)

    return df_sorted



def apply_page_config_and_styles():
    # Set Streamlit page configuration
    st.set_page_config(page_title="Lake Geometry Analysis", layout="wide")

    # Custom CSS for background color and text color
    st.markdown(
        """
        <style>
        /* Main content and background color */
        .main, .block-container, .css-18e3th9, .stApp {
            background-color: #052418;
            color: white;
        }

        /* Sidebar background */
        [data-testid="stSidebar"] {
            background-color: #052418;
            color: white;
        }

        /* Container background */
        .css-1d391kg, .css-1adrfps, .css-16idsys, .stContainer {
            background-color: #052418;
            color: white;
        }

        /* Title and text color */
        h1, h2, h3, h4, h5, h6, p, .stMarkdown, .stTextInput, .stSelectbox, .stDataFrame {
            color: white;
        }

        /* Button color */
        .stButton button {
            background-color: #1a472a;
            color: white;
            border: 1px solid #1a472a;
            cursor: pointer; /* Ensure the cursor is a pointer to indicate clickable */
        }

        /* Style for the clickable image button */
        .logo-button {
            background-color: transparent;  /* Transparent to see the image */
            border: none;  /* No border */
            padding: 0;  /* No padding */
            cursor: pointer;  /* Pointer on hover */
        }

        /* DataFrame and table color */
        .stDataFrame, .stTable, .stMarkdown {
            background-color: #052418;
            color: white;
        }

        /* Maximize the width of the DataFrame */
        .stDataFrame {
            width: 100%;
        }

        # /* Center the DataFrame */
        # .dataframe-container {
        #     display: flex;
        #     justify-content: center;
        #     width: 100%;
        # }

        /* Style for Summary Box */
        .summary-box {
            background-color: #083c2b;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
        }

        /* Corrected CSS */
        .stRadio > label {
            display: flex;
            justify-content: center;
            color: #ffffff;
            margin-bottom: 10px;
        }

        .stRadio > div {
            display: flex;
            justify-content: center;
        }

        .centered-radio > div {
            display: flex;
            justify-content: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )







# def display_image_API(gdf, object_id, year, show_label=True, show_prediction=True, image_chosen = 'images'):

#     poly = gdf[gdf['Objekt_id'] == object_id].geometry.values[0]
#     center = np.array([poly.centroid.x,poly.centroid.y]) 
#     center_easting = center[0]
#     center_northing = center[1]
#     minx = center_easting - 64
#     miny = center_northing - 64
#     maxx = center_easting + 64
#     maxy = center_northing + 64
#     bbox = box(minx,miny,maxx,maxy)
    

#     prediction_path = f"./predictions/{object_id}_{year}.npy"
    
#     try:
#         prediction = np.load(prediction_path)
#         if image_chosen == 'images':
#             image = get_img_nir(bbox, year)[0]
#         elif image_chosen == 'nir':
#             image = get_img_nir(bbox, year)[1]
#         elif image_chosen == 'context':
#             image = get_img_nir_context(bbox, year)[0]
#         elif image_chosen == 'nir_context':
#             image = get_img_nir_context(bbox, year)[1]
#         else:
#             raise ValueError("Invalid value for image_chosen. Please choose from 'images', 'nir', 'context', or 'nir_context'.")
#     except ValueError:
#         raise ValueError("Invalid bounding box. The specified bounding box is not available in the API.")


    
#     # Ensure the image is in a format suitable for RGB display
#     if image.ndim == 2:  # If grayscale, convert to RGB
#         modified_image = np.stack((image,) * 3, axis=-1)
#     elif image.ndim == 3 and image.shape[2] == 1:  # If single-channel but 3D
#         modified_image = np.repeat(image, 3, axis=2)
#     else:
#         modified_image = image.copy()

#     # Create a prediction mask based on a threshold
#     prediction_mask = prediction > 0.7
#     if image_chosen == 'context' or image_chosen == 'nir_context':
#         show_label = False
#         show_prediction = False

#     # Overlay contours for label if required
#     if show_label:
#         label = get_labels(bbox, gdf)
#         label_contours = measure.find_contours(label, 0.5)
#         for contour in label_contours:
#             for coord in contour:
#                 y, x = int(coord[0]), int(coord[1])
#                 modified_image[y, x] = [0, 255, 0]

#     # Overlay contours for prediction if required
#     if show_prediction:
#         prediction_contours = measure.find_contours(prediction_mask, 0.5)  # Find contours in prediction
#         for contour in prediction_contours:
#             for coord in contour:
#                 y, x = int(coord[0]), int(coord[1])
#                 modified_image[y, x] = [255, 0, 0]  # Red color for prediction contours

#     return modified_image


# Function to sort DataFrame based on mean difference after calculating gradient and splitting
def sort_by_mean_difference(df, begin_year, end_year, sort_order=True):  

    
    # # Step 1: Define the colors for magnitude calculation
    # colors = [
    #     ("1", "darkred"),
    #     ("2", "firebrick"),
    #     ("3", "red"),
    #     ("4", "grey"), 
    #     ("5", "lightgreen"),
    #     ("6", "forestgreen"),
    #     ("7", "darkgreen"),
    # ]
    
    # # Create a dictionary to map color to a numeric value
    # color_to_value = {color: int(value) for value, color in colors}
    
    # # Step 2: Convert the color values in the DataFrame to numeric values
    # def convert_color_to_value(color):
    #     return color_to_value.get(color, np.nan)  # Replace missing values with NaN

    # Convert each column from str  to numeric values
    for year in range(begin_year, end_year + 1):
        df[str(year)] = df[str(year)].astype(int)


    # Step 3: Calculate the gradient between consecutive years
    for year in range(begin_year, end_year):
        df[f'gradient_{year}'] = df[str(year + 1)] - df[str(year)]
    
    # Step 4: Find the year where the gradient is maximum for each row
    gradient_columns = [f'gradient_{year}' for year in range(begin_year, end_year)]
    df['max_gradient_year'] = df[gradient_columns].idxmax(axis=1)
    #if the max gradient in two years, take the last one
    #df['max_gradient_year'] = df['max_gradient_year'].apply(lambda x: x.split('_')[-1]) # TAKE THE LAST COLUMN
    
    df['max_gradient_year'] = df['max_gradient_year'].str.extract('(\d+)').astype(int)  # Extract the year as integer
    
    # Step 5: Calculate the mean for the left and right halves
    def calculate_means(row):
        max_grad_year = row['max_gradient_year']
        left_half_mean = row[[str(year) for year in range(begin_year, max_grad_year + 1)]].mean()
        right_half_mean = row[[str(year) for year in range(max_grad_year + 1, end_year + 1)]].mean()
        return pd.Series({'left_mean': left_half_mean, 'right_mean': right_half_mean})

    # Apply the function to calculate means
    df[['left_mean', 'right_mean']] = df.apply(calculate_means, axis=1)
    
    # Step 6: Calculate the difference (right_mean - left_mean)
    df['mean_difference'] = df['right_mean'] - df['left_mean']
    
    # Step 7: Sort the DataFrame based on the mean difference
    df_sorted = df.sort_values(by='mean_difference', ascending=sort_order).reset_index(drop=True)
    
    # Drop temporary columns for clarity
    df_sorted = df_sorted.drop(columns=gradient_columns + ['max_gradient_year', 'left_mean', 'right_mean'])

    # #convert the numeric values back to colors
    # def convert_value_to_color(value):
    #     for val, color in colors:
    #         if int(value) == int(val):
    #             return color
    #     return 'black'  # Return black if value is not found
    
    # Convert each column from int to str
    for year in range(begin_year, end_year + 1):
        df_sorted[str(year)] = df_sorted[str(year)].astype(str)


    
    return df_sorted