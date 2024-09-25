import time
import requests
from PIL import Image
from io import BytesIO
from shapely.geometry import box
import rasterio
from rasterio.features import rasterize
from skimage import measure
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import streamlit as st

def get_dem_terrain(minx, miny, maxx, maxy): #bbox
    #Pixelsize of the ortofoto, which is determined by the dist (the spatial resolution of OrtoFoto is 12.5cm)

    pixel_size = 1024
    #minx, miny, maxx, maxy = bbox.bounds
    

    #WMS url 
    wms_url = "https://services.datafordeler.dk/DHMNedboer/dhm/1.0.0/WMS?username=YIAZPCJMYL&password=Sojukimchi1_"
    wms_request_url = f"{wms_url}&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&BBOX={minx},{miny},{maxx},{maxy}&CRS=EPSG:25832&WIDTH={pixel_size}&HEIGHT={pixel_size}&STYLES=&FORMAT=image/png&DPI=96&MAP_RESOLUTION=96&FORMAT_OPTIONS=dpi:96&Layers=dhm_overflade_skyggekort"# dhm_terraen_skyggekort
    try:
        response = requests.get(wms_request_url)
    except:
        print("downloading error..tries again in 10 sec...")
        time.sleep(10)
        response = requests.get(wms_request_url)
    # Make the WMS request

    
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Save the retrieved image to a file
        #with open("output_imageH.jpg", "wb") as f:

        img = Image.open(BytesIO(response.content))
        
        # Convert the image to a NumPy array
        img_array = np.array(img)

    return img_array[:,:,0]

# Create Raster Labels
def get_labels(bbox, gdf):
    """Generate raster labels for a given bounding box, nature class, and municipality."""
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

    return raster



# @st.cache_data
# def get_DEM_and_labels(bbox, gdf):

#     dem_data = get_dem_terrain(bbox)
#     labels = get_labels(bbox, gdf)
#     return dem_data, labels

@st.cache_data
def get_DEM_and_labels(_bbox_bounds, _gdf):
    """Cache DEM and labels data so they are not reloaded every time."""
    # Recreate the bbox from bounds
    minx, miny, maxx, maxy = _bbox_bounds
    bbox = box(minx, miny, maxx, maxy)
    
    # Fetch DEM data (assuming DEM data is tied to the bbox and year)
    dem_data = get_dem_terrain(minx, miny, maxx, maxy)

    # Filter and generate labels using _gdf (which should still be the GeoDataFrame)
    labels = get_labels(bbox, _gdf)
    
    return dem_data, labels


def get_img_nir_context(bbox, year):
    #Pixelsize of the ortofoto, which is determined by the dist (the spatial resolution of OrtoFoto is 12.5cm)

    pixel_size = 1024
    min_x, min_y, max_x, max_y = bbox.bounds
    minx=((min_x+max_x)/2)-256
    maxx=((min_x+max_x)/2)+256
    miny=((min_y+max_y)/2)-256
    maxy=((min_y+max_y)/2)+256

    #WMS url 
    wms_url = "https://services.datafordeler.dk/GeoDanmarkOrto/orto_foraar/1.0.0/WMS?username=YIAZPCJMYL&password=Sojukimchi1_"
    wms_request_url = f"{wms_url}&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&BBOX={minx},{miny},{maxx},{maxy}&CRS=EPSG:25832&WIDTH={pixel_size}&HEIGHT={pixel_size}&STYLES=&FORMAT=image/png&DPI=96&MAP_RESOLUTION=96&FORMAT_OPTIONS=dpi:96&Layers=geodanmark_{year}_12_5cm"

    # Make the WMS request
  
    try:
        response = requests.get(wms_request_url)
    except:
        print("downloading error..tries again in 10 sec...")
        time.sleep(10)
        response = requests.get(wms_request_url)
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Save the retrieved image to a file
        #with open("output_imageH.jpg", "wb") as f:

        img = Image.open(BytesIO(response.content))
        
        # Convert the image to a NumPy array
        img_array = np.array(img)


        wms_request_url_ = f"{wms_url}&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&BBOX={minx},{miny},{maxx},{maxy}&CRS=EPSG:25832&WIDTH={1024}&HEIGHT={1024}&STYLES=&FORMAT=image/png&DPI=96&MAP_RESOLUTION=96&FORMAT_OPTIONS=dpi:96&Layers=geodanmark_{year}_12_5cm_cir"

        try:
            # Make the WMS request
            response_ = requests.get(wms_request_url_)
        except:
            print("downloading error..tries again in 10 sec...")
            time.sleep(10)
            response_ = requests.get(wms_request_url_)
        # Check if the request was successful (status code 200)
        if response_.status_code == 200:
            # Save the retrieved image to a file
            #with open("output_imageH.jpg", "wb") as f:
            #    f.write(response.content)

            NIR = Image.open(BytesIO(response_.content))

            # Convert the image to a NumPy array
            NIR = np.array(NIR)

            return img_array, NIR[:,:,0]
    else: 
        print("Ballade")



def get_img_nir(bbox, year):
    #Pixelsize of the ortofoto, which is determined by the dist (the spatial resolution of OrtoFoto is 12.5cm)

    pixel_size = 1024
    minx, miny, maxx, maxy = bbox.bounds


    #WMS url 
    wms_url = "https://services.datafordeler.dk/GeoDanmarkOrto/orto_foraar/1.0.0/WMS?username=YIAZPCJMYL&password=Sojukimchi1_"
    wms_request_url = f"{wms_url}&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&BBOX={minx},{miny},{maxx},{maxy}&CRS=EPSG:25832&WIDTH={pixel_size}&HEIGHT={pixel_size}&STYLES=&FORMAT=image/png&DPI=96&MAP_RESOLUTION=96&FORMAT_OPTIONS=dpi:96&Layers=geodanmark_{year}_12_5cm"

    # Make the WMS request
    try:
        response = requests.get(wms_request_url)
    except:
        print("downloading error..tries again in 10 sec...")
        time.sleep(10)
        response = requests.get(wms_request_url)
    

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Save the retrieved image to a file
        #with open("output_imageH.jpg", "wb") as f:

        img = Image.open(BytesIO(response.content))
        
        # Convert the image to a NumPy array
        img_array = np.array(img)


        wms_request_url_ = f"{wms_url}&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&BBOX={minx},{miny},{maxx},{maxy}&CRS=EPSG:25832&WIDTH={1024}&HEIGHT={1024}&STYLES=&FORMAT=image/png&DPI=96&MAP_RESOLUTION=96&FORMAT_OPTIONS=dpi:96&Layers=geodanmark_{year}_12_5cm_cir"

        try:
            # Make the WMS request
            response_ = requests.get(wms_request_url_)
        except:
            print("downloading error..tries again in 10 sec...")
            time.sleep(10)
            response_ = requests.get(wms_request_url_)
        # Check if the request was successful (status code 200)
        if response_.status_code == 200:
            # Save the retrieved image to a file
            #with open("output_imageH.jpg", "wb") as f:
            #    f.write(response.content)

            NIR = Image.open(BytesIO(response_.content))

            # Convert the image to a NumPy array
            NIR = np.array(NIR)

            return img_array, NIR[:,:,0], img
    else: 
        print("Ballade")






############################################################################################################






def modify_image(image, prediction, bbox, gdf, show_label=True, show_prediction=True):
    # Ensure the image is in RGB format
    if image.ndim == 2:  # If the image is grayscale (2D array), convert it to RGB
        image = np.stack((image,) * 3, axis=-1)
    elif image.ndim == 3 and image.shape[2] == 1:  # If it's single-channel (3D), repeat it for 3 channels
        image = np.repeat(image, 3, axis=2)

    modified_image = image.copy()

    # Create a prediction mask based on a threshold
    prediction_mask = prediction > 0.7

    # Overlay contours for label if required
    if show_label:
        label = get_labels(bbox, gdf)
        label_contours = measure.find_contours(label, 0.5)
        for contour in label_contours:
            for coord in contour:
                y, x = int(coord[0]), int(coord[1])
                modified_image[y, x] = [0, 255, 0]  # Green for label contours

    # Overlay contours for prediction if required
    if show_prediction:
        prediction_contours = measure.find_contours(prediction_mask, 0.5)  # Find contours in prediction
        for contour in prediction_contours:
            for coord in contour:
                y, x = int(coord[0]), int(coord[1])
                modified_image[y, x] = [255, 0, 0]  # Red color for prediction contours

    return modified_image



def load_image_data_async(bbox, year, gdf):
    """Load different image types asynchronously for faster display."""
    with ThreadPoolExecutor() as executor:
        future_image = executor.submit(get_img_nir, bbox, year)
        future_context = executor.submit(get_img_nir_context, bbox, year)
        future_DEM_labels = executor.submit(get_DEM_and_labels, bbox.bounds, gdf)  # Pass gdf here

        img_nir, nir_channel, _ = future_image.result()
        context_img, context_nir = future_context.result()
        dem_data, labels = future_DEM_labels.result()
        
    return img_nir, nir_channel, context_img, context_nir, dem_data, labels


def load_image_and_prediction(gdf, object_id, year, image_chosen='image', dem_data=None, labels=None):
    # Get bounding box for the object
    poly = gdf[gdf['Objekt_id'] == object_id].geometry.values[0]
    center = np.array([poly.centroid.x, poly.centroid.y])
    minx, miny = center[0] - 64, center[1] - 64
    maxx, maxy = center[0] + 64, center[1] + 64
    bbox = box(minx, miny, maxx, maxy)

    # Load image based on choice
    img_nir, nir_channel, context_img, context_nir, _, _ = load_image_data_async(bbox, year, gdf)

    # Ensure DEM and labels are cached (gdf passed as _gdf to prevent caching issue)
    if dem_data is None or labels is None:
        dem_data, labels = get_DEM_and_labels(bbox.bounds, gdf)  # Pass gdf as is
    # Choose image type images nir context_img
    image = img_nir if image_chosen == 'image' else nir_channel if image_chosen == 'nir' else context_img if image_chosen == 'context' else context_nir if image_chosen == 'nir_context' else  dem_data
    # Load prediction data
    prediction_path = f"./predictions/{object_id}_{year}.npy"
    prediction = np.load(prediction_path)

    return image, prediction, bbox


def display_image_API(gdf, object_id, year, show_label=True, show_prediction=True, image_chosen='image'):
    # Load image and prediction
    image, prediction, bbox = load_image_and_prediction(gdf, object_id, year, image_chosen)
    
    # Modify image with labels and/or predictions
    if image_chosen == 'context' or image_chosen == 'nir_context':
        show_prediction = False
        show_label = False
        
    modified_image = modify_image(image, prediction, bbox, gdf, show_label, show_prediction)
    
    return modified_image



# import matplotlib.pyplot as plt
# import io
# from PIL import Image

# def display_image_with_overlays(gdf, object_id, year, show_label=True, show_prediction=True, image_chosen='images'):
#     # Load image and prediction
#     image, prediction, bbox = load_image_and_prediction(gdf, object_id, year, image_chosen)

#     # Prepare figure and axis
#     fig, ax = plt.subplots(figsize=(10, 10))

#     # Show the image in the background
#     ax.imshow(image, cmap='gray' if image.ndim == 2 else None)

#     # Overlay labels if required
#     if show_label:
#         label = get_labels(bbox, gdf)
#         ax.contour(label, colors='green', linewidths=2, levels=[0.5])  # Green contour for labels

#     # Overlay prediction if required
#     if show_prediction:
#         prediction_mask = prediction > 0.7
#         ax.contour(prediction_mask, colors='red', linewidths=2, levels=[0.5])  # Red contour for predictions

#     # Hide axes
#     ax.axis('off')

#     # Save the figure to a buffer
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
#     buf.seek(0)
#     plt.close(fig)

#     # Convert buffer to PIL Image and return
#     return Image.open(buf)
