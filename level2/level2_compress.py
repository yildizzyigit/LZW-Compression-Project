import os
import math
import csv
import numpy as np
from PIL import Image

class LZWCompressImage:
   def __init__(self, filename):
      self.filename = filename
      self.codelength = None

   def compress_image_file(self):
      current_directory = os.path.dirname(os.path.realpath(__file__))
      input_path = current_directory + '/' + self.filename
      output_file = os.path.splitext(self.filename)[0] + '_compressed.bin'
      output_path = current_directory + '/' + output_file

      # read the grayscale image and convert to a flat list of pixel values
      img = Image.open(input_path)
      img_array = np.array(img)
      pixels = list(img_array.flatten())
      img_shape = img_array.shape

      # encode the pixel values using the LZW compression algorithm
      encoded = self.encode(pixels)
      # convert the encoded integer list to a binary string
      bit_string = self.int_list_to_binary_string(encoded)
      # add code length info to the beginning
      bit_string = self.add_code_length_info(bit_string)
      # perform padding
      padded = self.pad_encoded_data(bit_string)
      # convert to byte array
      byte_array = self.get_byte_array(padded)

      # save image shape info (height, width) at the beginning of the file
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

      print(input_path + ' is compressed into ' + output_file + '.')
      print('Image Size: ' + str(img_shape[1]) + 'x' + str(img_shape[0]))
      print('Original Size: ' + '{:,d}'.format(original_size) + ' bytes')
      print('Code Length: ' + str(self.codelength))
      print('Compressed Size: ' + '{:,d}'.format(compressed_size) + ' bytes')
      print('Entropy: ' + '{:.4f}'.format(entropy) + ' bits/pixel')
      print('Average Code Length: ' + '{:.4f}'.format(avg_code_length) + ' bits/pixel')
      print('Compression Ratio: ' + '{:.4f}'.format(compression_ratio))

      return output_path

   def encode(self, pixels):
      dict_size = 256
      dictionary = {(i,): i for i in range(dict_size)}

      w = ()
      result = []
      for k in pixels:
         wk = w + (k,)
         if wk in dictionary:
            w = wk
         else:
            result.append(dictionary[w])
            dictionary[wk] = dict_size
            dict_size += 1
            w = (k,)
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
      bitstring = codelength_info + bitstring
      return bitstring

   def pad_encoded_data(self, encoded_data):
      if len(encoded_data) % 8 != 0:
         extra_bits = 8 - len(encoded_data) % 8
         for i in range(extra_bits):
            encoded_data += '0'
      else:
         extra_bits = 0
      padding_info = '{0:08b}'.format(extra_bits)
      encoded_data = padding_info + encoded_data
      return encoded_data

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


# compress the grayscale image
filename = 'small_image_grayscale.bmp'
lzw = LZWCompressImage(filename)
lzw.compress_image_file()
