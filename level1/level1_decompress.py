import os  # the os module is used for file and directory operations
import csv

# A class that implements the LZW decompression algorithm
# as well as the necessary utility methods for text files.
# ------------------------------------------------------------------------------
class LZWDecompress:
   # A constructor with two input parameters
   # ---------------------------------------------------------------------------
   def __init__(self, filename, data_type):
      # use the input parameters to set the instance variables
      self.filename = filename
      self.data_type = data_type   # e.g., 'text'
      # initialize the code length as None
      # (the actual value is determined based on the compressed data)
      self.codelength = None

   # A method that reads the contents of a compressed binary file, performs
   # decompression and writes the decompressed output to a text file.
   # ---------------------------------------------------------------------------
   def decompress_text_file(self):
      # get the current directory where this program is placed
      current_directory = os.path.dirname(os.path.realpath(__file__))
      # build the path of the input file
      input_file = self.filename + '_compressed.bin'
      input_path = current_directory + '/' + input_file
      # build the path of the output file
      output_file = self.filename + '_decompressed.txt'
      output_path = current_directory + '/' + output_file

      # read the contents of the input file
      in_file = open(input_path, 'rb')   # binary mode
      compressed_data = in_file.read()
      in_file.close()

      # create a binary string from the bytes read from the compressed file
      from io import StringIO   # using StringIO for efficiency
      bit_string = StringIO()
      for byte in compressed_data:
         bits = bin(byte)[2:].rjust(8, '0')
         bit_string.write(bits)
      bit_string = bit_string.getvalue()

      # remove padding
      bit_string = self.remove_padding(bit_string)
      # remove the code length info and set the instance variable codelength
      bit_string = self.extract_code_length_info(bit_string)
      # convert the compressed binary string to a list of integer values
      encoded_text = self.binary_string_to_int_list(bit_string)
      # decode the encoded text by using the LZW decompression algorithm
      decompressed_text = self.decode(encoded_text)

      # write the decompression output to the output file
      out_file = open(output_path, 'w')
      out_file.write(decompressed_text)
      out_file.close()

      # notify the user that the decompression process is finished
      print(input_file + ' is decompressed into ' + output_file + '.')
      
      # return the path of the output file
      return output_path

   # A method to remove the padding info and the added zeros from the compressed
   # binary string and return the resulting string.
   def remove_padding(self, padded_encoded_data):
      # extract the padding info (the first 8 bits of the input string)
      padding_info = padded_encoded_data[:8]
      encoded_data = padded_encoded_data[8:]
      # remove the extra zeros (if any) and return the resulting string
      extra_padding = int(padding_info, 2) 
      if extra_padding != 0:
         encoded_data = encoded_data[:-1 * extra_padding]
      return encoded_data

   # A method to extract the code length info from the compressed binary string
   # and return the resulting string.
   # ---------------------------------------------------------------------------
   def extract_code_length_info(self, bitstring):
      # the first 8 bits of the input string contain the code length info
      codelength_info = bitstring[:8]
      self.codelength = int(codelength_info, 2)
      # return the resulting binary string after removing the code length info
      return bitstring[8:]

   # A method that converts the compressed binary string to a list of int codes
   # and returns the resulting list.
   # ---------------------------------------------------------------------------
   def binary_string_to_int_list(self, bitstring):
      # generate the list of integer codes from the binary string
      int_codes = []
      # for each compressed value (a binary string with codelength bits)
      for bits in range(0, len(bitstring), self.codelength):
         # compute the integer code and add it to the list
         int_code = int(bitstring[bits: bits + self.codelength], 2)
         int_codes.append(int_code)
      # return the resulting list
      return int_codes
   
   # A method that decodes a list of encoded integer values into a string (text) 
   # by using the LZW decompression algorithm, prints and saves the decoding
   # table as a CSV file, and returns the resulting output.
   # ---------------------------------------------------------------------------
   def decode(self, encoded_values):
      # build the initial dictionary by mapping the index values in the extended 
      # ASCII table to their corresponding characters
      dict_size = 256
      dictionary = {i: chr(i) for i in range(dict_size)}

      # perform the LZW decompression algorithm
      # ------------------------------------------------------------------------
      from io import StringIO   # using StringIO for efficiency
      result = StringIO()
      rows = []

      # initialize w as the character corresponding to the first encoded value
      # in the list and add this character to the output string
      w = chr(encoded_values.pop(0))
      result.write(w)
      rows.append(['', w, w, '', ''])

      # iterate over each encoded value in the list
      for k in encoded_values:
         k_display = chr(k) if k < 256 else k

         # if the value is in the dictionary
         if k in dictionary:
            # retrieve the corresponding string
            entry = dictionary[k]
         # if the value is equal to the current dictionary size
         elif k == dict_size:
            # construct the entry
            entry = w + w[0]   # a special case where the entry is formed
         # if k is invalid (not in the dictionary and not equal to dict_size)
         else:
            # raise an error
            raise ValueError('Bad compressed k: %s' % k)
         # add the entry to the output
         result.write(entry)
         # w + the first character of the entry is added to the dictionary 
         # as a new sequence
         new_symbol = w + entry[0]
         rows.append([w, k_display, entry, dict_size, new_symbol])
         dictionary[dict_size] = new_symbol
         dict_size += 1
         # update w to the current entry
         w = entry

      print(f"{'w':<12} | {'k':<8} | {'Output':<12} | {'Index':<8} | {'Symbol':<12}")
      print('-' * 62)
      for row in rows:
         print(f"{str(row[0]):<12} | {str(row[1]):<8} | {str(row[2]):<12} | {str(row[3]):<8} | {str(row[4]):<12}")

      current_directory = os.path.dirname(os.path.realpath(__file__))
      csv_path = current_directory + '/level1_dict_decompress.csv'
      with open(csv_path, 'w', newline='') as csvfile:
         writer = csv.writer(csvfile)
         writer.writerow(['w', 'k', 'Output', 'Index', 'Symbol'])
         writer.writerows(rows)
      print()
      print('Decoding table saved to level1_dict_decompress.csv')

      # return the resulting output (the decompressed string/text)
      return result.getvalue()


# read and decompress the file sample_compressed.bin
filename = 'sample'
lzw = LZWDecompress(filename, 'text')
output_path = lzw.decompress_text_file()

# compare the decompressed file with the original file
# ------------------------------------------------------------------------------
current_directory = os.path.dirname(os.path.realpath(__file__))
original_file = filename + '.txt'
original_path = current_directory + '/' + original_file
decompressed_file = filename + '_decompressed.txt'
decompressed_path = current_directory + '/' + decompressed_file
with open(original_path, 'r') as file1, open(decompressed_path, 'r') as file2:
   original_text = file1.read()
   decompressed_text = file2.read()
if original_text.strip() == decompressed_text.strip():
   print(original_file + ' and ' + decompressed_file + ' are the same.')
else:
   print(original_file + ' and ' + decompressed_file + ' are NOT the same.')
