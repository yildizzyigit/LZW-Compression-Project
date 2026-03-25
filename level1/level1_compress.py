import os  # the os module is used for file and directory operations
import math  # the math module provides access to mathematical functions
import csv

# A class that implements the LZW compression algorithm
# as well as the necessary utility methods for text files.
# ------------------------------------------------------------------------------
class LZWCompress:
   # A constructor with two input parameters
   # ---------------------------------------------------------------------------
   def __init__(self, filename, data_type):
      # use the input parameters to set the instance variables
      self.filename = filename
      self.data_type = data_type   # e.g., 'text'
      # initialize the code length as None 
      # (the actual value is determined based on the compressed data)
      self.codelength = None

   # A method that compresses the contents of a text file to a binary output file 
   # and returns the path of the output file.
   # ---------------------------------------------------------------------------
   def compress_text_file(self):
      # get the current directory where this program is placed
      current_directory = os.path.dirname(os.path.realpath(__file__))
      # build the path of the input file
      input_file = self.filename + '.txt'
      input_path = current_directory + '/' + input_file
      # build the path of the output file
      output_file = self.filename + '_compressed.bin'
      output_path = current_directory + '/' + output_file

      # read the contents of the input file
      in_file = open(input_path, 'r')
      text = in_file.read().strip()
      in_file.close()

      self.save_encoding_table(text)

      # encode the text by using the LZW compression algorithm
      encoded_text_as_integers = self.encode(text)
      # get the binary string that corresponds to the compressed text
      encoded_text = self.int_list_to_binary_string(encoded_text_as_integers)
      # add the code length info to the beginning of the encoded text
      # (the compressed data must contain everything needed to decompress it)
      encoded_text = self.add_code_length_info(encoded_text)
      # perform padding if needed
      padded_encoded_text = self.pad_encoded_data(encoded_text)
      # convert the resulting string into a byte array
      byte_array = self.get_byte_array(padded_encoded_text)

      # write the bytes in the byte array to the output file (compressed file)
      out_file = open(output_path, 'wb')   # binary mode
      out_file.write(bytes(byte_array))
      out_file.close()

      # notify the user that the compression process is finished
      print(input_file + ' is compressed into ' + output_file + '.')
      # compute and print the details of the compression process
      uncompressed_size = len(text)
      print('Original Size: ' + '{:,d}'.format(uncompressed_size) + ' bytes')
      print('Code Length: ' + str(self.codelength))
      compressed_size = len(byte_array)
      print('Compressed Size: ' + '{:,d}'.format(compressed_size) + ' bytes')
      compression_ratio = compressed_size / uncompressed_size
      print('Compression Ratio: ' + '{:.2f}'.format(compression_ratio))

      # return the path of the output file
      return output_path
   
   # A method that encodes a text input into a list of integer values by using
   # the LZW compression algorithm and returns the resulting list.
   # ---------------------------------------------------------------------------
   def encode(self, uncompressed_data):
      # build the initial dictionary by mapping the characters in the extended 
      # ASCII table to their indexes
      dict_size = 256
      dictionary = {chr(i): i for i in range(dict_size)}

      # perform the LZW compression algorithm
      w = ''   # initialize a variable to store the current sequence
      result = []   # initialize a list to store the encoded values to output
      # iterate over each item (a character for text files) in the input data
      for k in uncompressed_data:
         # keep forming a new sequence until it is not in the dictionary
         wk = w + k
         if wk in dictionary:   # if wk exists in the dictionary
            w = wk   # update the sequence by adding the current item
         else:   # otherwise
            # add the code for w (the longest sequence found in the dictionary)
            # to the list that stores the encoded values
            result.append(dictionary[w])
            # add wk (the new sequence) to the dictionary
            dictionary[wk] = dict_size
            dict_size += 1
            # reset w to the current character
            w = k
      # add the code for the remaining sequence to the list 
      # that stores the encoded values (integer codes)
      if w:
         result.append(dictionary[w])
      
      # set the code length for compressing the encoded values based on the input 
      # data by using the size of the resulting dictionary (note that real-world 
      # LZW implementations often grow the code length dynamically)
      self.codelength = math.ceil(math.log2(len(dictionary)))

      # return the encoded values (a list of integer dictionary values)
      return result

   # A method that converts the integer list returned by the compress method
   # into a binary string and returns the resulting string.
   # ---------------------------------------------------------------------------
   def int_list_to_binary_string(self, int_list):
      # create a list to store the bits of the binary string 
      # (using a list is more efficient than repeatedly concatenating strings)
      bits = []
      # for each integer in the input list
      for num in int_list:
         # convert each integer code to its codelength-bit binary representation
         for n in range(self.codelength):
            if num & (1 << (self.codelength - 1 - n)):
               bits.append('1')
            else:
               bits.append('0')
      # return the result as a string
      return ''.join(bits)

   # A method that adds the code length to the beginning of the binary string
   # that corresponds to the compressed data and returns the resulting string.
   # (the compressed data should contain everything needed to decompress it)
   # ---------------------------------------------------------------------------
   def add_code_length_info(self, bitstring):
      # create a binary string that stores the code length as a byte
      codelength_info = '{0:08b}'.format(self.codelength)
      # add the code length info to the beginning of the given binary string
      bitstring = codelength_info + bitstring
      # return the resulting binary string
      return bitstring

   # A method for adding zeros to the binary string (the compressed data)
   # to make the length of the string a multiple of 8.
   # (This is necessary to be able to write the values to the file as bytes.)
   # ---------------------------------------------------------------------------
   def pad_encoded_data(self, encoded_data):
      # compute the number of the extra bits to add
      if len(encoded_data) % 8 != 0:
         extra_bits = 8 - len(encoded_data) % 8
         # add zeros to the end (padding)
         for i in range(extra_bits):
            encoded_data += '0'
      else:   # no need to add zeros
         extra_bits = 0
      # add a byte that stores the number of added zeros to the beginning of
      # the encoded data (this is necessary because the decompressor must know
      # how many padding bits were added artificially in order to remove them)
      padding_info = '{0:08b}'.format(extra_bits)
      encoded_data = padding_info + encoded_data
      # return the resulting string after padding
      return encoded_data

   # A method that converts the padded binary string to a byte array and returns 
   # the resulting array. 
   # (This byte array will be written to a file to store the compressed data.)
   # ---------------------------------------------------------------------------
   def get_byte_array(self, padded_encoded_data):
      # the length of the padded binary string must be a multiple of 8
      if (len(padded_encoded_data) % 8 != 0):
         print('The compressed data is not padded properly!')
         exit(0)
      # create a byte array
      b = bytearray()
      # append the padded binary string byte by byte
      for i in range(0, len(padded_encoded_data), 8):
         byte = padded_encoded_data[i : i + 8]
         b.append(int(byte, 2))
      # return the resulting byte array
      return b

   # A method that prints the LZW encoding table step by step for a given text
   # and saves it as a CSV file.
   # ---------------------------------------------------------------------------
   def save_encoding_table(self, text):
      text = text.strip()
      dict_size = 256
      dictionary = {chr(i): i for i in range(dict_size)}
      w = ''
      rows = []

      for k in text:
         wk = w + k
         if wk in dictionary:
            w_display = w if w != '' else 'NIL'
            rows.append([w_display, k, '', '', ''])
            w = wk
         else:
            w_display = w if w != '' else 'NIL'
            rows.append([w_display, k, dictionary[w], dict_size, wk])
            dictionary[wk] = dict_size
            dict_size += 1
            w = k

      if w:
         w_display = w if w != '' else 'NIL'
         rows.append([w_display, 'EOF', dictionary[w], '', ''])

      print(f"{'w':<12} | {'k':<5} | {'Output':<8} | {'Index':<8} | {'Symbol':<12}")
      print('-' * 55)
      for row in rows:
         print(f"{str(row[0]):<12} | {str(row[1]):<5} | {str(row[2]):<8} | {str(row[3]):<8} | {str(row[4]):<12}")

      current_directory = os.path.dirname(os.path.realpath(__file__))
      csv_path = current_directory + '/level1_dict_compress.csv'
      with open(csv_path, 'w', newline='') as csvfile:
         writer = csv.writer(csvfile)
         writer.writerow(['w', 'k', 'Output', 'Index', 'Symbol'])
         writer.writerows(rows)
      print()    
      print('Encoding table saved to level1_dict_compress.csv')


# read and compress the file sample.txt
filename = 'sample'
lzw = LZWCompress(filename, 'text')
output_path = lzw.compress_text_file()
