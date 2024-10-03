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
import folium
from folium import Element
import tempfile
from pyproj import Transformer
from shapely.geometry import Polygon, box, MultiPolygon
import zipfile
import io


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







def save_shapefile_to_zip(gdf, output_folder='./streamlit'):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Define the base file path for the Shapefile components
    shapefile_path = os.path.join(output_folder, 'consultant_output')

    # Save the GeoDataFrame as a Shapefile (will generate .shp, .shx, .dbf, etc.)
    gdf.to_file(f"{shapefile_path}.shp")

    # Create an in-memory ZIP file
    zip_buffer = io.BytesIO()
    
    # Write the Shapefile components to the ZIP file
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        for extension in ['shp', 'shx', 'dbf', 'prj']:
            file_path = f"{shapefile_path}.{extension}"
            if os.path.exists(file_path):
                zipf.write(file_path, os.path.basename(file_path))
    
    # Return the in-memory ZIP file data
    zip_buffer.seek(0)  # Move the pointer to the beginning of the buffer
    return zip_buffer

def sort_by_mean(df, begin_year, end_year, sort_order=True):  
    # Step 1: Define the colors for magnitude calculation
    colors = [
        ("-120", "1"),
        ("-110", "2"),
        ("-100", "3"),
        ("0", "4"),  #downgrade to 3 for mostlyGREEN ?
        ("100", "5"),
        ("110", "6"),
        ("120", "7"),
        ("-99", "8"), ## BRIDGE
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
            #see if nan 
            if pd.isna(value):
                return 'black'
            if int(value) == int(val):
                return color
        return 'black'  # Return black if value is not found
    
    # Convert each column from value to color
    for year in range(begin_year, end_year + 1):
        df_sorted[str(year)] = df_sorted[str(year)].apply(convert_value_to_color)

    #remove mean column
    df_sorted = df_sorted.drop(columns=['mean'])

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
    
        .streamlit-container {
            background-color: #052418;
        }
        

        </style>
        """,

        
        unsafe_allow_html=True
    )
















# def sort_by_mean_difference(df, begin_year, end_year, sort_order=True):
#     # Convert each column from str to numeric values, handle missing values with fillna()
#     for year in range(begin_year, end_year + 1):
#         df[str(year)] = pd.to_numeric(df[str(year)], errors='coerce').fillna(0).astype(int)

#     # Step 3: Calculate the weighted gradient between consecutive years
#     for year in range(begin_year, end_year):
#         # Ensure both years are available before computing the gradient
#         if str(year) in df.columns and str(year + 1) in df.columns:
#             df[f'gradient_{year}'] = df[str(year + 1)] - df[str(year)]

#     # Step 4: Find the year where the weighted gradient is maximum for each row
#     gradient_columns = [f'gradient_{year}' for year in range(begin_year, end_year)]
    
#     # Check if the gradient columns were created correctly and minimum value actually
#     df['max_gradient_year'] = df[gradient_columns].idxmin(axis=1)
#     #print(df[df["Objekt_id"] == "45cd921f-5352-11e2-b3db-00155d01e765"]["max_gradient_year"])
    

#     # Ensure if the max gradient is equal for multiple years, we take the latest year
#     df['max_gradient_year'] = df['max_gradient_year'].apply(lambda x: x.split('_')[-1])
#     df['max_gradient_year'] = df['max_gradient_year'].astype(int)
#     #print(df[df["Objekt_id"] == "45cd921f-5352-11e2-b3db-00155d01e765"]["max_gradient_year"])
#     # Step 5: Calculate the mean for the left and right halves, weighted by the gradients
#     def calculate_means(row):
#         max_grad_year = row['max_gradient_year']
#         left_half_mean = row[[str(year) for year in range(begin_year, max_grad_year + 1)]].mean()
#         right_half_mean = row[[str(year) for year in range(max_grad_year + 1, end_year + 1)]].mean()
#         #if row["Objekt_id"] == "45cb480c-5352-11e2-b18b-00155d01e765":#"75231ccf-2676-4d0a-a1cd-97906ed45d5c":
#             #print(row["Objekt_id"])
#            # print(left_half_mean)
#            # print(right_half_mean, row['max_gradient_year'])
#         return pd.Series({'left_mean': left_half_mean, 'right_mean': right_half_mean})

#     # Apply the function to calculate means
#     df[['left_mean', 'right_mean']] = df.apply(calculate_means, axis=1)

#     # Step 6: Calculate the difference (right_mean - left_mean)
#     df['mean_difference'] = df['right_mean'] - df['left_mean']

#     # Special condition: If the last years (closer to `end_year`) show a drop from high (green) to low (red),
#     # multiply the mean_difference by a factor (e.g., 1.5) to account for significant recent changes.
#     def emphasize_recent_change(row):
#         last_year_values = [row[str(end_year - 1)], row[str(end_year)]]
#         #print(end_year)
#         #if row["Objekt_id"] == "45cd91f1-5352-11e2-bfdf-00155d01e765":
#             #print(row["Objekt_id"])
#             #print(last_year_values)
#         if all(v in ['5', '6', '7'] for v in last_year_values) and row[str(end_year)] in ['1', '2', '3']:
#             #print('ok')
#             return row['mean_difference'] - 1
#         if all(v in [1, 2, 3] for v in last_year_values) and row[str(end_year)] in [5, 6, 7]:
#             return row['mean_difference'] + 1
#         return row['mean_difference']

#     df['mean_difference'] = df.apply(emphasize_recent_change, axis=1)

#     # Step 7: Sort the DataFrame based on the mean difference
#     df_sorted = df.sort_values(by='mean_difference', ascending=sort_order).reset_index(drop=True)

#     # Drop temporary columns for clarity
#     df_sorted = df_sorted.drop(columns=gradient_columns + ['max_gradient_year', 'left_mean', 'right_mean'])

#     # Convert each column from int to str
#     for year in range(begin_year, end_year + 1):
#         df_sorted[str(year)] = df_sorted[str(year)].astype(str)
    
#     return df_sorted



def find_split_point(gradients):
    # Calculate the difference between consecutive years
    diffs = np.diff(gradients)
    # Find the index where the largest change (difference) occurs
    split_idx = np.argmax(np.abs(diffs))
    return split_idx

# Create a function to calculate the average transitions before and after the split
def calculate_before_after_split(gradients, split_idx):
   # print(gradients, split_idx)
    # Split gradients into "before" and "after"
   
    before = gradients[:split_idx + 1]
    after = gradients[split_idx  +1:]
   # print(before)
    #print(after)
    # Calculate average transitions for both periods
    avg_before = np.mean(before)# if len(before) > 0 else 0
    avg_after = np.mean(after) #if len(after) > 0 else 0
 
    return  avg_after-avg_before

# Apply the functions to the DataFrame
def process_row(row, begin_year, end_year):
    year_columns = [f'{year}' for year in range(begin_year, end_year+1)]
    # Extract the gradient values for the object
    gradient_columns = [f'gradient_{year}' for year in range(begin_year, end_year)]
    gradients = row[gradient_columns].values.astype(float)
    years_ = row[year_columns].values.astype(float)
    # Find the split point for this object
    split_idx = find_split_point(gradients)

    # Calculate the average transition before and after the split
    difference=calculate_before_after_split(row[year_columns], split_idx)
    
    # Return the results as new columns
    return pd.Series({'split_idx': split_idx, 'difference': difference})

def sort_by_mean_difference(df, begin_year, end_year, sort_order=True):
    merged_gdf=df.copy()
    for year in range(begin_year, end_year + 1):
        df[str(year)] = pd.to_numeric(df[str(year)], errors='coerce').fillna(0).astype(int)
    df.replace(8, np.nan, inplace=True)
    df.replace(4, np.nan, inplace=True)
    df.replace(1, 1, inplace=True)
    df.replace(2, 2, inplace=True)
    df.replace(3, 3, inplace=True)
    df.replace(5, 10, inplace=True)
    df.replace(6, 11, inplace=True)
    df.replace(7, 12, inplace=True)
    for year in range(begin_year, end_year):
    # Ensure both years are available before computing the gradient
        if str(year) in df.columns and str(year + 1) in df.columns:
            df[f'gradient_{year}'] = df[str(year + 1)] - df[str(year)]
    for year in range(begin_year, end_year ):
        df[f"gradient_{str(year)}"] = pd.to_numeric( df[f"gradient_{str(year)}"], errors='coerce').fillna(0).astype(int)
    year_columns = [f'{year}' for year in range(begin_year, end_year+1)]
    df[year_columns] = df[year_columns].apply(lambda row: row.fillna(row.mean()), axis=1)

   # gradient_columns = [f'gradient_{year}' for year in range(begin_year, end_year)]
    
    # Apply the process to each row in the DataFrame
    df_split = df.apply(process_row, axis=1, args=(begin_year, end_year))
    
    # Add the new columns (split index, avg_before, avg_after) back to the original DataFrame
    df = pd.concat([df, df_split], axis=1)
    
    # Calculate the difference between the average transitions before and after
    #df['transition_difference'] = df['avg_after'] - df['avg_before']
    
    # Sort by the transition difference in descending order
    df_sorted = df.sort_values(by='difference', ascending=sort_order)

    df_=pd.DataFrame(df_sorted["Objekt_id"]).merge(merged_gdf, on='Objekt_id', how='left')

    return df_



def get_labels(bbox, gdf):
    """Generate raster labels for a given bounding box."""
    filtered_gdf = gdf[gdf["geometry"].intersects(bbox)]
    
    # Create an empty raster array
    raster = np.zeros((1024, 1024))
    transform = rasterio.transform.from_bounds(*bbox.bounds, 1024, 1024)

    # Rasterize the filtered GeoDataFrame
    raster = rasterize(
        [(geometry, 1) for geometry in filtered_gdf.geometry],
        out_shape=(1024, 1024),
        transform=transform,
        all_touched=True
    )

    # Convert the raster array to an image
    img = Image.fromarray(np.uint8(raster * 255))  # Scale values for visibility
    return img





def create_map(gdf, gdf_label, objekt_id, year, color_value,  show_label, show_prediction, default_zoom=18):
    # colors = [
    #     ("1", "darkred"),
    #     ("2", "firebrick"),
    #     ("3", "red"),
    #     ("4", "grey"),
    #     ("5", "lightgreen"),
    #     ("6", "forestgreen"),
    #     ("7", "darkgreen"),
    # ]    

    # color = [c for v, c in colors if v == color_value][0]

    t = Transformer.from_crs(25832, 4326)

    # Define the center point for the map (latitude and longitude)
    poly = gdf[gdf['Objekt_id'] == objekt_id].geometry.values[0]
    center = np.array([poly.centroid.x, poly.centroid.y])
    map_center = t.transform(center[0], center[1])

    gdf_id = gdf[gdf["Objekt_id"] == objekt_id].copy()
    gdf_id_label = gdf_label[gdf_label["Objekt_id"] == objekt_id].copy()

    def json_geo(gdf_id):
        if gdf_id.crs is None:
            gdf_id = gdf_id.set_crs(epsg=25832)
        gdf_id = gdf_id.to_crs(epsg=4326)
        geo_j = gdf_id["geometry"].to_json()
        return geo_j

    geo_j_label = json_geo(gdf_id_label)
    geo_j = json_geo(gdf_id)

    # Create the map with the default or previous zoom level
    m = folium.Map(location=map_center, zoom_start=default_zoom, max_zoom=24, max_native_zoom = 24)#, tiles='Cartodb dark_matter')
    

    

    # Add the WMS layers and GeoJson layers as before
    orto = folium.raster_layers.WmsTileLayer(
        url="https://api.dataforsyningen.dk/orto_foraar_DAF?ignoreillegallayers=TRUE",
        name=f"Ortofoto {year}",
        layers=f"geodanmark_{year}_12_5cm",
        fmt="image/png",
        transparent=True,
        attr="Dataforsyningen",
        token='31c2b5dcede0148999f284bd1919e550',
        extra_params={'token': '31c2b5dcede0148999f284bd1919e550'},
        max_zoom=24,
    ).add_to(m)

    geo_json_layer = folium.GeoJson(
        data=geo_j,
        name=f"Predictions {year}",
        style_function=lambda x: {"color": f"{color_value}", "weight": 2, "fillOpacity": 0},
        show=show_prediction, 
        max_zoom=24,
        
    ).add_to(m)
    
    folium.Popup(f"Objekt ID: {objekt_id}").add_to(geo_json_layer)

    geo_json_layer = folium.GeoJson(
        data=geo_j_label,
        name=f"Label",
        style_function=lambda x: {"color": "pink", "weight": 2, "fillOpacity": 0}, 
        max_zoom=24,
        show=show_label,
        
    ).add_to(m)

    nir = folium.raster_layers.WmsTileLayer(
        url="https://api.dataforsyningen.dk/orto_foraar_DAF?ignoreillegallayers=TRUE",
        name="NIR",
        fmt="image/png",
        layers=f"geodanmark_{year}_12_5cm_cir",
        transparent=True,
        token='31c2b5dcede0148999f284bd1919e550',
        extra_params={'token': '31c2b5dcede0148999f284bd1919e550'},
        #by default the layer is not shown
        show = False,
        #max_zoom=26,
        
    ).add_to(m)

    dhm = folium.raster_layers.WmsTileLayer(
        url="https://api.dataforsyningen.dk/dhm_DAF?ignoreillegallayers=TRUE",
        name="DHM",
        layers="dhm_terraen_skyggekort",
        show=False,
        fmt="image/png",
        transparent=True,
        attr="Dataforsyningen",
        token='31c2b5dcede0148999f284bd1919e550',
        extra_params={'token': '31c2b5dcede0148999f284bd1919e550'},
        
    ).add_to(m)

    

    folium.LayerControl().add_to(m)

    return m
