import os
import math
import numpy as np
from PIL import Image

class LZWCompressImageDiff:
   def __init__(self, filename):
      self.filename = filename
      self.codelength = None

   def compress_image_file(self):
      current_directory = os.path.dirname(os.path.realpath(__file__))
      input_path = current_directory + '/' + self.filename
      output_file = os.path.splitext(self.filename)[0] + '_diff_compressed.bin'
      output_path = current_directory + '/' + output_file

      # read the grayscale image
      img = Image.open(input_path)
      img_array = np.array(img, dtype=np.int32)
      img_shape = img_array.shape

      # compute the difference image
      diff_array = self.compute_difference_image(img_array)

      # flatten the difference image to a list
      pixels = list(diff_array.flatten())

      # encode using LZW
      encoded = self.encode(pixels)
      bit_string = self.int_list_to_binary_string(encoded)
      bit_string = self.add_code_length_info(bit_string)
      padded = self.pad_encoded_data(bit_string)
      byte_array = self.get_byte_array(padded)

      # save image shape and compressed data
      out_file = open(output_path, 'wb')
      out_file.write(img_shape[0].to_bytes(4, 'big'))
      out_file.write(img_shape[1].to_bytes(4, 'big'))
      out_file.write(bytes(byte_array))
      out_file.close()

      # compute and print compression details
      original_size = img_shape[0] * img_shape[1]
      compressed_size = len(byte_array)
      entropy = self.calculate_entropy(pixels)
      avg_code_length = (compressed_size * 8) / original_size
      compression_ratio = compressed_size / original_size

      print(self.filename + ' is compressed into ' + output_file + '.')
      print('Image Size: ' + str(img_shape[1]) + 'x' + str(img_shape[0]))
      print('Original Size: ' + '{:,d}'.format(original_size) + ' bytes')
      print('Code Length: ' + str(self.codelength))
      print('Compressed Size: ' + '{:,d}'.format(compressed_size) + ' bytes')
      print('Entropy: ' + '{:.4f}'.format(entropy) + ' bits/pixel')
      print('Average Code Length: ' + '{:.4f}'.format(avg_code_length) + ' bits/pixel')
      print('Compression Ratio: ' + '{:.4f}'.format(compression_ratio))

      return output_path

   def compute_difference_image(self, img_array):
      n_rows, n_cols = img_array.shape
      diff_array = np.zeros((n_rows, n_cols), dtype=np.int32)

      # compute row-wise differences (starting from second pixel in each row)
      for i in range(n_rows):
         diff_array[i][0] = img_array[i][0]
         for j in range(1, n_cols):
            diff_array[i][j] = img_array[i][j] - img_array[i][j - 1]

      # compute column-wise differences for the first column (starting from second row)
      for i in range(1, n_rows):
         diff_array[i][0] = img_array[i][0] - img_array[i - 1][0]

      return diff_array

   def encode(self, pixels):
      # shift pixel values to avoid negative keys (differences range from -255 to 255)
      offset = 255
      dict_size = 511
      dictionary = {(i,): i for i in range(dict_size)}

      w = ()
      result = []
      for k in pixels:
         k_shifted = k + offset
         wk = w + (k_shifted,)
         if wk in dictionary:
            w = wk
         else:
            result.append(dictionary[w])
            dictionary[wk] = dict_size
            dict_size += 1
            w = (k_shifted,)
      if w:
         result.append(dictionary[w])

      self.codelength = math.ceil(math.log2(len(dictionary)))
      return result

   def int_list_to_binary_string(self, int_list):
      bits = []
      for num in int_list:
         for n in range(self.codelength):
            if num & (1 << (self.codelength - 1 - n)):
               bits.append('1')
            else:
               bits.append('0')
      return ''.join(bits)

   def add_code_length_info(self, bitstring):
      codelength_info = '{0:08b}'.format(self.codelength)
      return codelength_info + bitstring

   def pad_encoded_data(self, encoded_data):
      if len(encoded_data) % 8 != 0:
         extra_bits = 8 - len(encoded_data) % 8
         for i in range(extra_bits):
            encoded_data += '0'
      else:
         extra_bits = 0
      padding_info = '{0:08b}'.format(extra_bits)
      return padding_info + encoded_data

   def get_byte_array(self, padded_encoded_data):
      if (len(padded_encoded_data) % 8 != 0):
         print('The compressed data is not padded properly!')
         exit(0)
      b = bytearray()
      for i in range(0, len(padded_encoded_data), 8):
         byte = padded_encoded_data[i : i + 8]
         b.append(int(byte, 2))
      return b

   def calculate_entropy(self, pixels):
      from collections import Counter
      counts = Counter(pixels)
      total = len(pixels)
      entropy = 0
      for count in counts.values():
         p = count / total
         entropy -= p * math.log2(p)
      return entropy


# compress the grayscale image using difference encoding
filename = 'small_image_grayscale.bmp'
lzw = LZWCompressImageDiff(filename)
lzw.compress_image_file()
