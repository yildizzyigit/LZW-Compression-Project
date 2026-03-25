import os
import numpy as np
from PIL import Image

class LZWDecompressColorImageDiff:
   def __init__(self, filename):
      self.filename = filename
      self.codelength = None

   def decompress_image_file(self):
      current_directory = os.path.dirname(os.path.realpath(__file__))
      input_file = os.path.splitext(self.filename)[0] + '_color_diff_compressed.bin'
      input_path = current_directory + '/' + input_file
      output_file = os.path.splitext(self.filename)[0] + '_color_diff_decompressed.bmp'
      output_path = current_directory + '/' + output_file

      # read the compressed file
      in_file = open(input_path, 'rb')
      height = int.from_bytes(in_file.read(4), 'big')
      width = int.from_bytes(in_file.read(4), 'big')
      r_size = int.from_bytes(in_file.read(4), 'big')
      g_size = int.from_bytes(in_file.read(4), 'big')
      b_size = int.from_bytes(in_file.read(4), 'big')
      r_data = in_file.read(r_size)
      g_data = in_file.read(g_size)
      b_data = in_file.read(b_size)
      in_file.close()

      # decode each channel and restore from differences
      r_pixels = self.decode_channel(r_data)
      g_pixels = self.decode_channel(g_data)
      b_pixels = self.decode_channel(b_data)

      r_array = self.restore_channel(np.array(r_pixels, dtype=np.int32).reshape(height, width))
      g_array = self.restore_channel(np.array(g_pixels, dtype=np.int32).reshape(height, width))
      b_array = self.restore_channel(np.array(b_pixels, dtype=np.int32).reshape(height, width))

      img_array = np.stack([r_array, g_array, b_array], axis=2)
      img = Image.fromarray(img_array)
      img.save(output_path)

      print(input_file + ' is decompressed into ' + output_file + '.')

      # compare the original and decompressed images
      original_array = np.array(Image.open(current_directory + '/' + self.filename))
      if np.array_equal(original_array, img_array):
         print('Original and decompressed images are the same.')
      else:
         print('Original and decompressed images are NOT the same.')

      return output_path

   def restore_channel(self, diff_array):
      n_rows, n_cols = diff_array.shape
      channel = np.zeros((n_rows, n_cols), dtype=np.int32)
      channel[0][0] = diff_array[0][0]
      for i in range(1, n_rows):
         channel[i][0] = diff_array[i][0] + channel[i - 1][0]
      for i in range(n_rows):
         for j in range(1, n_cols):
            channel[i][j] = diff_array[i][j] + channel[i][j - 1]
      return np.uint8(channel)

   def decode_channel(self, compressed_data):
      from io import StringIO
      bit_string = StringIO()
      for byte in compressed_data:
         bits = bin(byte)[2:].rjust(8, '0')
         bit_string.write(bits)
      bit_string = bit_string.getvalue()
      bit_string = self.remove_padding(bit_string)
      bit_string = self.extract_code_length_info(bit_string)
      encoded = self.binary_string_to_int_list(bit_string)
      return self.decode(encoded)

   def remove_padding(self, padded_encoded_data):
      extra_padding = int(padded_encoded_data[:8], 2)
      encoded_data = padded_encoded_data[8:]
      if extra_padding != 0:
         encoded_data = encoded_data[:-1 * extra_padding]
      return encoded_data

   def extract_code_length_info(self, bitstring):
      self.codelength = int(bitstring[:8], 2)
      return bitstring[8:]

   def binary_string_to_int_list(self, bitstring):
      int_codes = []
      for bits in range(0, len(bitstring), self.codelength):
         int_codes.append(int(bitstring[bits: bits + self.codelength], 2))
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


# decompress the color difference image
filename = 'small_image.bmp'
lzw = LZWDecompressColorImageDiff(filename)
lzw.decompress_image_file()
