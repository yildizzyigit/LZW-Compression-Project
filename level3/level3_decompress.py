import os
import numpy as np
from PIL import Image

class LZWDecompressImageDiff:
   def __init__(self, filename):
      self.filename = filename
      self.codelength = None

   def decompress_image_file(self):
      current_directory = os.path.dirname(os.path.realpath(__file__))
      input_file = os.path.splitext(self.filename)[0] + '_diff_compressed.bin'
      input_path = current_directory + '/' + input_file
      output_file = os.path.splitext(self.filename)[0] + '_diff_decompressed.bmp'
      output_path = current_directory + '/' + output_file

      # read the compressed file
      in_file = open(input_path, 'rb')
      height = int.from_bytes(in_file.read(4), 'big')
      width = int.from_bytes(in_file.read(4), 'big')
      compressed_data = in_file.read()
      in_file.close()

      # create binary string from bytes
      from io import StringIO
      bit_string = StringIO()
      for byte in compressed_data:
         bits = bin(byte)[2:].rjust(8, '0')
         bit_string.write(bits)
      bit_string = bit_string.getvalue()

      # remove padding and extract code length
      bit_string = self.remove_padding(bit_string)
      bit_string = self.extract_code_length_info(bit_string)
      encoded = self.binary_string_to_int_list(bit_string)
      # decode the pixel differences
      diff_pixels = self.decode(encoded)

      # reshape to difference image array
      diff_array = np.array(diff_pixels, dtype=np.int32).reshape(height, width)
      # restore original image from difference image
      img_array = self.restore_image(diff_array)
      # save the decompressed image
      img = Image.fromarray(img_array)
      img.save(output_path)

      print(input_file + ' is decompressed into ' + output_file + '.')

      # compare the original and decompressed images
      original_img = Image.open(current_directory + '/' + self.filename)
      original_array = np.array(original_img)
      if np.array_equal(original_array, img_array):
         print('Original and decompressed images are the same.')
      else:
         print('Original and decompressed images are NOT the same.')

      return output_path

   def restore_image(self, diff_array):
      n_rows, n_cols = diff_array.shape
      img_array = np.zeros((n_rows, n_cols), dtype=np.int32)

      # restore first column using column-wise differences
      img_array[0][0] = diff_array[0][0]
      for i in range(1, n_rows):
         img_array[i][0] = diff_array[i][0] + img_array[i - 1][0]

      # restore remaining columns using row-wise differences
      for i in range(n_rows):
         for j in range(1, n_cols):
            img_array[i][j] = diff_array[i][j] + img_array[i][j - 1]

      return np.uint8(img_array)

   def remove_padding(self, padded_encoded_data):
      padding_info = padded_encoded_data[:8]
      encoded_data = padded_encoded_data[8:]
      extra_padding = int(padding_info, 2)
      if extra_padding != 0:
         encoded_data = encoded_data[:-1 * extra_padding]
      return encoded_data

   def extract_code_length_info(self, bitstring):
      codelength_info = bitstring[:8]
      self.codelength = int(codelength_info, 2)
      return bitstring[8:]

   def binary_string_to_int_list(self, bitstring):
      int_codes = []
      for bits in range(0, len(bitstring), self.codelength):
         int_code = int(bitstring[bits: bits + self.codelength], 2)
         int_codes.append(int_code)
      return int_codes

   def decode(self, encoded_values):
      offset = 255
      dict_size = 511
      dictionary = {i: (i,) for i in range(dict_size)}

      result = []
      w = dictionary[encoded_values.pop(0)]
      result.extend([v - offset for v in w])

      for k in encoded_values:
         if k in dictionary:
            entry = dictionary[k]
         elif k == dict_size:
            entry = w + (w[0],)
         else:
            raise ValueError('Bad compressed k: %s' % k)
         result.extend([v - offset for v in entry])
         dictionary[dict_size] = w + (entry[0],)
         dict_size += 1
         w = entry

      return result


# decompress the grayscale difference image
filename = 'small_image_grayscale.bmp'
lzw = LZWDecompressImageDiff(filename)
lzw.decompress_image_file()
