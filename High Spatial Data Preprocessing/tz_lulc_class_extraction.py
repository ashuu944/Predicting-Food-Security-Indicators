import os
import numpy as np
import rasterio
from rasterio.enums import Resampling

# Define input and output paths
input_raster_path = 'data/tanzania/tz_lulc_10m.tif'
output_dir = 'data/tanzania/spatial'

# Define the classes and their output file names
classes = {
    5: 'crop_mean_100m.tif',
    2: 'forest_mean_100m.tif',
    7: 'built_mean_100m.tif'
}

# Function to resample raster to 100m resolution
def resample_raster(input_path, output_path, scale_factor, resampling_method):
    with rasterio.open(input_path) as dataset:
        # Calculate the new dimensions (moving from 10m to 100m resolution)
        new_width = int(dataset.width / scale_factor)
        new_height = int(dataset.height / scale_factor)

        # Resample the data
        data = dataset.read(
            out_shape=(dataset.count, new_height, new_width),
            resampling=resampling_method
        ).astype(np.float32)  # Ensure the data type is float32

        # Scale image transform
        transform = dataset.transform * dataset.transform.scale(
            (dataset.width / data.shape[-1]),
            (dataset.height / data.shape[-2])
        )

        # Write resampled raster
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=new_height,
            width=new_width,
            count=dataset.count,
            dtype='float32',  # Set output data type to float32
            crs=dataset.crs,
            transform=transform,
        ) as dest:
            dest.write(data)

# Function to extract and save each class with fractional values
def extract_classes_fractional(input_path, classes, output_dir, scale_factor):
    with rasterio.open(input_path) as dataset:
        data = dataset.read(1)
        height, width = data.shape
        new_height = height // scale_factor
        new_width = width // scale_factor
        
        for class_value, output_file in classes.items():
            class_data = np.zeros((new_height, new_width), dtype=np.float32)
            
            for i in range(new_height):
                for j in range(new_width):
                    # Create a window of size (scale_factor x scale_factor) to calculate the class proportions
                    window = data[i*scale_factor:(i+1)*scale_factor, j*scale_factor:(j+1)*scale_factor]
                    class_data[i, j] = np.sum(window == class_value) / (scale_factor**2)
            
            output_path = os.path.join(output_dir, output_file)
            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=new_height,
                width=new_width,
                count=1,
                dtype='float32',  # Set output data type to float32
                crs=dataset.crs,
                transform=dataset.transform * dataset.transform.scale(scale_factor, scale_factor),
            ) as dest:
                dest.write(class_data, 1)

# Resample the raster using the chosen method
resampling_method = Resampling.average  # Change this to the desired method
resampled_raster_path = os.path.join(output_dir, 'resampled_raster.tif')
resample_raster(input_raster_path, resampled_raster_path, 10, resampling_method)

# Extract and save classes with fractional values
extract_classes_fractional(resampled_raster_path, classes, output_dir, 10)
