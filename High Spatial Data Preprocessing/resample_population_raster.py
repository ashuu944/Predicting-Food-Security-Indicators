import os
import numpy as np
import rasterio
from rasterio.enums import Resampling

def replace_nodata(src_data, nodata_value):
    # Replace only the nodata_value with np.nan, leave other values unchanged
    src_data[src_data == nodata_value] = np.nan
    return src_data

def resample_raster(src_path, dst_path, ref_path, nodata_value):
    with rasterio.open(ref_path) as ref:
        ref_meta = ref.meta.copy()

        with rasterio.open(src_path) as src:
            src_data = src.read(
                out_shape=(
                    src.count,
                    ref_meta['height'],
                    ref_meta['width']
                ),
                resampling=Resampling.nearest
            )
            
            # Replace no-data values with np.nan
            src_data = replace_nodata(src_data, nodata_value)

            src_transform = src.transform
            src_transform = src.transform * src.transform.scale(
                (src.width / src_data.shape[-1]),
                (src.height / src_data.shape[-2])
            )

            ref_meta.update({
                'transform': src_transform,
                'width': src_data.shape[-1],
                'height': src_data.shape[-2],
                'dtype': src.dtypes[0],  # Ensure the data type is the same as the input raster
                'nodata': nodata_value  # Set the no-data value to the input no-data value
            })

            with rasterio.open(dst_path, 'w', **ref_meta) as dst:
                # Replace np.nan back with nodata_value before writing
                src_data[np.isnan(src_data)] = nodata_value
                dst.write(src_data)

def process_directory(directory, ref_file, nodata_value):
    if not os.path.isdir(directory):
        print(f"The directory {directory} does not exist.")
        return

    raster_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.tif')]

    for raster_file in raster_files:
        if raster_file != ref_file:
            resampled_file = raster_file.replace('.tif', '_res.tif')
            resample_raster(raster_file, resampled_file, ref_file, nodata_value)
            print(f"Resampled {raster_file} to {resampled_file}")

def main():
    directory = 'data/tanzania/spatial/population_100m'
    ref_file = 'data/tanzania/spatial/built_mean_100m.tif'
    nodata_value = -200
    process_directory(directory, ref_file, nodata_value)

if __name__ == "__main__":
    main()

