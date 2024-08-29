import os
import numpy as np
import rasterio

# Define input and output paths
input_raster_path = 'data/rwanda/rw_lulc_10m.tif'
output_dir = 'data/rwanda/spatial'

# Define the classes and their output file names
classes = {
    5: 'crop_10m.tif',
    2: 'forest_10m.tif',
    7: 'built_10m.tif'
}

# Function to extract classes into binary rasters
def extract_classes_binary(input_path, classes, output_dir):
    with rasterio.open(input_path) as dataset:
        data = dataset.read(1)
        
        for class_value, output_file in classes.items():
            class_data = (data == class_value).astype(np.uint8)  # Binary raster (0 or 1)
            
            output_path = os.path.join(output_dir, output_file)
            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=dataset.height,
                width=dataset.width,
                count=1,
                dtype='uint8',
                crs=dataset.crs,
                transform=dataset.transform,
            ) as dest:
                dest.write(class_data, 1)

# Function to resample raster to 100m resolution using fractional values
def resample_raster_fractional(input_path, output_path, scale_factor):
    with rasterio.open(input_path) as dataset:
        data = dataset.read(1)
        height, width = data.shape
        new_height = height // scale_factor
        new_width = width // scale_factor
        
        fractional_data = np.zeros((new_height, new_width), dtype=np.float32)
        
        for i in range(new_height):
            for j in range(new_width):
                # Create a window of size (scale_factor x scale_factor) to calculate the class proportions
                window = data[i*scale_factor:(i+1)*scale_factor, j*scale_factor:(j+1)*scale_factor]
                fractional_data[i, j] = np.sum(window) / (scale_factor**2)
        
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=new_height,
            width=new_width,
            count=1,
            dtype='float32',
            crs=dataset.crs,
            transform=dataset.transform * dataset.transform.scale(scale_factor, scale_factor),
        ) as dest:
            dest.write(fractional_data, 1)

# Extract classes into binary rasters
extract_classes_binary(input_raster_path, classes, output_dir)

# Resample the binary rasters to 100m resolution using fractional values
scale_factor = 10  # From 10m to 100m

for class_value, binary_file in classes.items():
    input_path = os.path.join(output_dir, binary_file)
    output_file = f"{binary_file.split('_')[0]}_mean_100m.tif"
    output_path = os.path.join(output_dir, output_file)
    resample_raster_fractional(input_path, output_path, scale_factor)
