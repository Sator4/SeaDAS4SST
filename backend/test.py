from esa_snappy import ProductIO, GPF  # package to be imported is now esa_snappy instead of snappy
import numpy as np
import matplotlib.pyplot as plt


p = ProductIO.readProduct('/home/sator/.snap/snap-python/esa_snappy/testdata/MER_FRS_L1B_SUBSET.dim')  # package folder is now esa_snappy instead of snappy
rad13 = p.getBand('radiance_13')
w = rad13.getRasterWidth()
h = rad13.getRasterHeight()
rad13_data = np.zeros(w * h, np.float32)
rad13.readPixels(0, 0, w, h, rad13_data)
p.dispose()
rad13_data.shape = h, w
imgplot = plt.imshow(rad13_data)
imgplot.write_png('radiance_13.png')
plt.show()


# print('\n\n')
# def read_sentinel_product(manifest_file_path):
#     r = ProductIO.getProductReader('SENTINEL-3')
#     print(r)
#     p = r.readProductNodes(manifest_file_path, None)
#     return p

# path = '/media/sator/STORAGE/Github/Copernicus/service_vue3/backend/catalogue/S3B_SL_2_WST____20240321T015406_20240321T015706_20240321T035221_0179_091_060_2160_MAR_O_NR_003.SEN3/xfdumanifest.xml'
# output_path = '/media/sator/STORAGE/Github/Copernicus/service_vue3/backend/catalogue/Reprojected'
# p = ProductIO.readProduct(path)
# print(p)

# GPF.createProduct(p)