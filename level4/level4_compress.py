import os
import math
import numpy as np
from PIL import Image

class LZWCompressColorImage:
   def __init__(self, filename):
      self.filename = filename
      self.codelength = None

   def compress_image_file(self):
      current_directory = os.path.dirname(os.path.realpath(__file__))
      input_path = current_directory + '/' + self.filename
      output_file = os.path.splitext(self.filename)[0] + '_color_compressed.bin'
      output_path = current_directory + '/' + output_file

      # read the color image
      img = Image.open(input_path)
      img_array = np.array(img)
      img_shape = img_array.shape

      # separate R, G, B channels and encode each one
      r_pixels = list(img_array[:, :, 0].flatten())
      g_pixels = list(img_array[:, :, 1].flatten())
      b_pixels = list(img_array[:, :, 2].flatten())

      # encode each channel
      r_encoded = self.encode(r_pixels)
      r_bits = self.int_list_to_binary_string(r_encoded)
      r_codelength = self.codelength

      g_encoded = self.encode(g_pixels)
      g_bits = self.int_list_to_binary_string(g_encoded)
      g_codelength = self.codelength

      b_encoded = self.encode(b_pixels)
      b_bits = self.int_list_to_binary_string(b_encoded)
      b_codelength = self.codelength

      # add code length info and pad each channel
      r_bits = self.add_code_length_info(r_bits, r_codelength)
      r_bits = self.pad_encoded_data(r_bits)
      r_bytes = self.get_byte_array(r_bits)

      g_bits = self.add_code_length_info(g_bits, g_codelength)
      g_bits = self.pad_encoded_data(g_bits)
      g_bytes = self.get_byte_array(g_bits)

      b_bits = self.add_code_length_info(b_bits, b_codelength)
      b_bits = self.pad_encoded_data(b_bits)
      b_bytes = self.get_byte_array(b_bits)

      # save image shape and all three channel byte arrays
      out_file = open(output_path, 'wb')
      out_file.write(img_shape[0].to_bytes(4, 'big'))
      out_file.write(img_shape[1].to_bytes(4, 'big'))
      # write the size of each channel so we know where each one ends
      out_file.write(len(r_bytes).to_bytes(4, 'big'))
      out_file.write(len(g_bytes).to_bytes(4, 'big'))
      out_file.write(len(b_bytes).to_bytes(4, 'big'))
      out_file.write(bytes(r_bytes))
      out_file.write(bytes(g_bytes))
      out_file.write(bytes(b_bytes))
      out_file.close()

      # compute and print compression details
      original_size = img_shape[0] * img_shape[1] * 3
      compressed_size = len(r_bytes) + len(g_bytes) + len(b_bytes)
      r_entropy = self.calculate_entropy(r_pixels)
      g_entropy = self.calculate_entropy(g_pixels)
      b_entropy = self.calculate_entropy(b_pixels)
      avg_entropy = (r_entropy + g_entropy + b_entropy) / 3
      avg_code_length = (compressed_size * 8) / original_size
      compression_ratio = compressed_size / original_size

      print(self.filename + ' is compressed into ' + output_file + '.')
      print('Image Size: ' + str(img_shape[1]) + 'x' + str(img_shape[0]))
      print('Original Size: ' + '{:,d}'.format(original_size) + ' bytes')
      print('Compressed Size: ' + '{:,d}'.format(compressed_size) + ' bytes')
      print('R Entropy: ' + '{:.4f}'.format(r_entropy) + ' bits/pixel')
      print('G Entropy: ' + '{:.4f}'.format(g_entropy) + ' bits/pixel')
      print('B Entropy: ' + '{:.4f}'.format(b_entropy) + ' bits/pixel')
      print('Average Entropy: ' + '{:.4f}'.format(avg_entropy) + ' bits/pixel')
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

   def add_code_length_info(self, bitstring, codelength):
      return '{0:08b}'.format(codelength) + bitstring

   def pad_encoded_data(self, encoded_data):
      if len(encoded_data) % 8 != 0:
         extra_bits = 8 - len(encoded_data) % 8
         for i in range(extra_bits):
            encoded_data += '0'
      else:
         extra_bits = 0
      return '{0:08b}'.format(extra_bits) + encoded_data

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


# compress the color image
filename = 'small_image.bmp'
lzw = LZWCompressColorImage(filename)
lzw.compress_image_file()
