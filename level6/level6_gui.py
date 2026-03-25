import os
import math
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import Counter

# LZW Compression/Decompression functions for all levels

def encode_pixels(pixels, offset=0, dict_start=256):
   dict_size = dict_start
   dictionary = {(i,): i for i in range(dict_size)}
   w = ()
   result = []
   for k in pixels:
      wk = w + (k + offset,)
      if wk in dictionary:
         w = wk
      else:
         result.append(dictionary[w])
         dictionary[wk] = dict_size
         dict_size += 1
         w = (k + offset,)
   if w:
      result.append(dictionary[w])
   codelength = math.ceil(math.log2(len(dictionary)))
   return result, codelength

def decode_pixels(encoded_values, offset=0, dict_start=256):
   dict_size = dict_start
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

def int_list_to_bits(int_list, codelength):
   bits = []
   for num in int_list:
      for n in range(codelength):
         bits.append('1' if num & (1 << (codelength - 1 - n)) else '0')
   return ''.join(bits)

def pack_bits(bitstring, codelength):
   cl_bits = '{0:08b}'.format(codelength) + bitstring
   extra = (8 - len(cl_bits) % 8) % 8
   cl_bits += '0' * extra
   pad_info = '{0:08b}'.format(extra)
   cl_bits = pad_info + cl_bits
   b = bytearray()
   for i in range(0, len(cl_bits), 8):
      b.append(int(cl_bits[i:i+8], 2))
   return bytes(b)

def unpack_bits(data):
   from io import StringIO
   bs = StringIO()
   for byte in data:
      bs.write(bin(byte)[2:].rjust(8, '0'))
   bs = bs.getvalue()
   extra = int(bs[:8], 2)
   bs = bs[8:]
   codelength = int(bs[:8], 2)
   bs = bs[8:]
   if extra:
      bs = bs[:-extra]
   codes = []
   for i in range(0, len(bs), codelength):
      codes.append(int(bs[i:i+codelength], 2))
   return codes

def compute_diff(channel):
   n_rows, n_cols = channel.shape
   diff = np.zeros((n_rows, n_cols), dtype=np.int32)
   for i in range(n_rows):
      diff[i][0] = channel[i][0]
      for j in range(1, n_cols):
         diff[i][j] = channel[i][j] - channel[i][j-1]
   for i in range(1, n_rows):
      diff[i][0] = channel[i][0] - channel[i-1][0]
   return diff

def restore_diff(diff):
   n_rows, n_cols = diff.shape
   arr = np.zeros((n_rows, n_cols), dtype=np.int32)
   arr[0][0] = diff[0][0]
   for i in range(1, n_rows):
      arr[i][0] = diff[i][0] + arr[i-1][0]
   for i in range(n_rows):
      for j in range(1, n_cols):
         arr[i][j] = diff[i][j] + arr[i][j-1]
   return np.uint8(arr)

def calculate_entropy(pixels):
   counts = Counter(pixels)
   total = len(pixels)
   return -sum((c/total) * math.log2(c/total) for c in counts.values())


# Compress/Decompress for each level


def level1_compress(filepath):
   with open(filepath, 'r') as f:
      text = f.read().strip()
   pixels = [ord(c) for c in text]
   encoded, cl = encode_pixels(pixels)
   packed = pack_bits(int_list_to_bits(encoded, cl), cl)
   out_path = filepath.replace('.txt', '_compressed.bin')
   with open(out_path, 'wb') as f:
      f.write(packed)
   entropy = calculate_entropy(pixels)
   original_size = len(text)
   compressed_size = len(packed)
   avg_cl = (compressed_size * 8) / original_size
   cr = compressed_size / original_size
   return out_path, entropy, avg_cl, cr, original_size, compressed_size, None

def level1_decompress(filepath):
   with open(filepath, 'rb') as f:
      data = f.read()
   codes = unpack_bits(data)
   pixels = decode_pixels(codes)
   text = ''.join(chr(p) for p in pixels)
   out_path = filepath.replace('_compressed.bin', '_decompressed.txt')
   with open(out_path, 'w') as f:
      f.write(text)
   return out_path, None

def level2_compress(filepath):
   img = Image.open(filepath)
   arr = np.array(img)
   h, w = arr.shape
   pixels = list(arr.flatten())
   encoded, cl = encode_pixels(pixels)
   packed = pack_bits(int_list_to_bits(encoded, cl), cl)
   out_path = filepath.replace('.bmp', '_L2_compressed.bin')
   with open(out_path, 'wb') as f:
      f.write(h.to_bytes(4,'big') + w.to_bytes(4,'big') + packed)
   entropy = calculate_entropy(pixels)
   original_size = h * w
   compressed_size = len(packed)
   avg_cl = (compressed_size * 8) / original_size
   cr = compressed_size / original_size
   return out_path, entropy, avg_cl, cr, original_size, compressed_size, img

def level2_decompress(filepath):
   with open(filepath, 'rb') as f:
      h = int.from_bytes(f.read(4),'big')
      w = int.from_bytes(f.read(4),'big')
      data = f.read()
   pixels = decode_pixels(unpack_bits(data))
   arr = np.array(pixels, dtype=np.uint8).reshape(h, w)
   img = Image.fromarray(arr)
   out_path = filepath.replace('_L2_compressed.bin', '_L2_decompressed.bmp')
   img.save(out_path)
   return out_path, img

def level3_compress(filepath):
   img = Image.open(filepath)
   arr = np.array(img, dtype=np.int32)
   h, w = arr.shape
   diff = compute_diff(arr)
   pixels = list(diff.flatten())
   encoded, cl = encode_pixels(pixels, offset=255, dict_start=511)
   packed = pack_bits(int_list_to_bits(encoded, cl), cl)
   out_path = filepath.replace('.bmp', '_L3_compressed.bin')
   with open(out_path, 'wb') as f:
      f.write(h.to_bytes(4,'big') + w.to_bytes(4,'big') + packed)
   entropy = calculate_entropy(pixels)
   original_size = h * w
   compressed_size = len(packed)
   avg_cl = (compressed_size * 8) / original_size
   cr = compressed_size / original_size
   return out_path, entropy, avg_cl, cr, original_size, compressed_size, img

def level3_decompress(filepath):
   with open(filepath, 'rb') as f:
      h = int.from_bytes(f.read(4),'big')
      w = int.from_bytes(f.read(4),'big')
      data = f.read()
   pixels = decode_pixels(unpack_bits(data), offset=255, dict_start=511)
   diff = np.array(pixels, dtype=np.int32).reshape(h, w)
   arr = restore_diff(diff)
   img = Image.fromarray(arr)
   out_path = filepath.replace('_L3_compressed.bin', '_L3_decompressed.bmp')
   img.save(out_path)
   return out_path, img

def compress_color_channel(channel, use_diff=False):
   if use_diff:
      pixels = list(compute_diff(channel).flatten())
      encoded, cl = encode_pixels(pixels, offset=255, dict_start=511)
   else:
      pixels = list(channel.flatten())
      encoded, cl = encode_pixels(pixels)
   packed = pack_bits(int_list_to_bits(encoded, cl), cl)
   return packed, pixels

def decompress_color_channel(data, h, w, use_diff=False):
   if use_diff:
      pixels = decode_pixels(unpack_bits(data), offset=255, dict_start=511)
      arr = restore_diff(np.array(pixels, dtype=np.int32).reshape(h, w))
   else:
      pixels = decode_pixels(unpack_bits(data))
      arr = np.array(pixels, dtype=np.uint8).reshape(h, w)
   return arr

def level4_compress(filepath):
   img = Image.open(filepath)
   arr = np.array(img, dtype=np.int32)
   h, w = arr.shape[:2]
   r_packed, r_px = compress_color_channel(arr[:,:,0])
   g_packed, g_px = compress_color_channel(arr[:,:,1])
   b_packed, b_px = compress_color_channel(arr[:,:,2])
   out_path = filepath.replace('.bmp', '_L4_compressed.bin')
   with open(out_path, 'wb') as f:
      f.write(h.to_bytes(4,'big') + w.to_bytes(4,'big'))
      f.write(len(r_packed).to_bytes(4,'big') + len(g_packed).to_bytes(4,'big') + len(b_packed).to_bytes(4,'big'))
      f.write(r_packed + g_packed + b_packed)
   entropy = (calculate_entropy(r_px) + calculate_entropy(g_px) + calculate_entropy(b_px)) / 3
   original_size = h * w * 3
   compressed_size = len(r_packed) + len(g_packed) + len(b_packed)
   avg_cl = (compressed_size * 8) / original_size
   cr = compressed_size / original_size
   return out_path, entropy, avg_cl, cr, original_size, compressed_size, img

def level4_decompress(filepath):
   with open(filepath, 'rb') as f:
      h = int.from_bytes(f.read(4),'big')
      w = int.from_bytes(f.read(4),'big')
      rs = int.from_bytes(f.read(4),'big')
      gs = int.from_bytes(f.read(4),'big')
      bs = int.from_bytes(f.read(4),'big')
      r_data = f.read(rs); g_data = f.read(gs); b_data = f.read(bs)
   r = decompress_color_channel(r_data, h, w)
   g = decompress_color_channel(g_data, h, w)
   b = decompress_color_channel(b_data, h, w)
   img = Image.fromarray(np.stack([r, g, b], axis=2))
   out_path = filepath.replace('_L4_compressed.bin', '_L4_decompressed.bmp')
   img.save(out_path)
   return out_path, img

def level5_compress(filepath):
   img = Image.open(filepath)
   arr = np.array(img, dtype=np.int32)
   h, w = arr.shape[:2]
   r_packed, r_px = compress_color_channel(arr[:,:,0], use_diff=True)
   g_packed, g_px = compress_color_channel(arr[:,:,1], use_diff=True)
   b_packed, b_px = compress_color_channel(arr[:,:,2], use_diff=True)
   out_path = filepath.replace('.bmp', '_L5_compressed.bin')
   with open(out_path, 'wb') as f:
      f.write(h.to_bytes(4,'big') + w.to_bytes(4,'big'))
      f.write(len(r_packed).to_bytes(4,'big') + len(g_packed).to_bytes(4,'big') + len(b_packed).to_bytes(4,'big'))
      f.write(r_packed + g_packed + b_packed)
   entropy = (calculate_entropy(r_px) + calculate_entropy(g_px) + calculate_entropy(b_px)) / 3
   original_size = h * w * 3
   compressed_size = len(r_packed) + len(g_packed) + len(b_packed)
   avg_cl = (compressed_size * 8) / original_size
   cr = compressed_size / original_size
   return out_path, entropy, avg_cl, cr, original_size, compressed_size, img

def level5_decompress(filepath):
   with open(filepath, 'rb') as f:
      h = int.from_bytes(f.read(4),'big')
      w = int.from_bytes(f.read(4),'big')
      rs = int.from_bytes(f.read(4),'big')
      gs = int.from_bytes(f.read(4),'big')
      bs = int.from_bytes(f.read(4),'big')
      r_data = f.read(rs); g_data = f.read(gs); b_data = f.read(bs)
   r = decompress_color_channel(r_data, h, w, use_diff=True)
   g = decompress_color_channel(g_data, h, w, use_diff=True)
   b = decompress_color_channel(b_data, h, w, use_diff=True)
   img = Image.fromarray(np.stack([r, g, b], axis=2))
   out_path = filepath.replace('_L5_compressed.bin', '_L5_decompressed.bmp')
   img.save(out_path)
   return out_path, img

# GUI
current_file = None
current_img = None
decompressed_img = None

def start():
   global gui, original_panel, decompressed_panel
   global lbl_entropy, lbl_avg_cl, lbl_cr, lbl_input_size, lbl_comp_size, lbl_diff
   global channel_frame

   gui = tk.Tk()
   gui.title('LZW Image Compression')
   gui['bg'] = 'SteelBlue3'

   # top bar: File + Methods
   top_frame = tk.Frame(gui, bg='SteelBlue4')
   top_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=8)

   tk.Button(top_frame, text='Select File', width=12, command=select_file).grid(row=0, column=0, padx=6)

   methods = [
      ('Level 1: Compress',     lambda: run_compress(1)),
      ('Level 1: Decompress',   lambda: run_decompress(1)),
      ('Level 2: Compress',     lambda: run_compress(2)),
      ('Level 2: Decompress',   lambda: run_decompress(2)),
      ('Level 3: Compress',     lambda: run_compress(3)),
      ('Level 3: Decompress',   lambda: run_decompress(3)),
      ('Level 4: Compress',     lambda: run_compress(4)),
      ('Level 4: Decompress',   lambda: run_decompress(4)),
      ('Level 5: Compress',     lambda: run_compress(5)),
      ('Level 5: Decompress',   lambda: run_decompress(5)),
   ]

   method_var = tk.StringVar(value='Select Method')
   method_menu = tk.OptionMenu(top_frame, method_var, *[m[0] for m in methods])
   method_menu.config(width=20)
   method_menu.grid(row=0, column=1, padx=6)

   def on_method_select(*args):
      selected = method_var.get()
      for name, cmd in methods:
         if name == selected:
            cmd()
            break
   method_var.trace('w', on_method_select)

   # image panels
   img_frame = tk.Frame(gui, bg='SteelBlue3')
   img_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

   original_box = tk.Frame(img_frame, bg='white', width=320, height=260)
   original_box.grid(row=0, column=0, padx=15)
   original_box.grid_propagate(False)
   tk.Label(original_box, text='Original Image', bg='white', font=('Arial', 11, 'bold')).place(relx=0.5, rely=0.08, anchor='center')
   original_panel = tk.Label(original_box, bg='white')
   original_panel.place(relx=0.5, rely=0.55, anchor='center')

   decompressed_box = tk.Frame(img_frame, bg='white', width=320, height=260)
   decompressed_box.grid(row=0, column=1, padx=15)
   decompressed_box.grid_propagate(False)
   tk.Label(decompressed_box, text='Decompressed Image', bg='white', font=('Arial', 11, 'bold')).place(relx=0.5, rely=0.08, anchor='center')
   decompressed_panel = tk.Label(decompressed_box, bg='white')
   decompressed_panel.place(relx=0.5, rely=0.55, anchor='center')

   # channel buttons
   channel_frame = tk.Frame(gui, bg='SteelBlue3')
   channel_frame.grid(row=2, column=0, pady=5)
   for txt, cmd in [('Color', lambda: show_channel('color')),
                    ('GrayScale', lambda: show_channel('gray')),
                    ('Red', lambda: show_channel('red')),
                    ('Green', lambda: show_channel('green')),
                    ('Blue', lambda: show_channel('blue'))]:
      tk.Button(channel_frame, text=txt, width=9, command=cmd).pack(side='left', padx=3)

   # stats
   stats_frame = tk.Frame(gui, bg='SteelBlue3')
   stats_frame.grid(row=2, column=1, padx=10, pady=5, sticky='w')

   lbl_entropy    = tk.Label(stats_frame, text='Entropy: -',               bg='SteelBlue3', fg='white', font=('Arial', 10))
   lbl_avg_cl     = tk.Label(stats_frame, text='Average Code Length: -',   bg='SteelBlue3', fg='white', font=('Arial', 10))
   lbl_cr         = tk.Label(stats_frame, text='Compression Ratio: -',     bg='SteelBlue3', fg='white', font=('Arial', 10))
   lbl_input_size = tk.Label(stats_frame, text='Input Image Size: -',      bg='SteelBlue3', fg='white', font=('Arial', 10))
   lbl_comp_size  = tk.Label(stats_frame, text='Compressed Image Size: -', bg='SteelBlue3', fg='white', font=('Arial', 10))
   lbl_diff       = tk.Label(stats_frame, text='Difference: -',            bg='SteelBlue3', fg='white', font=('Arial', 10))

   for lbl in [lbl_entropy, lbl_avg_cl, lbl_cr, lbl_input_size, lbl_comp_size, lbl_diff]:
      lbl.pack(anchor='w')

   gui.mainloop()

def select_file():
   global current_file, current_img
   path = filedialog.askopenfilename(
      title='Select a file',
      filetypes=[('Image/Text/Bin files', '*.bmp *.txt *.bin'), ('All files', '*.*')]
   )
   if not path:
      messagebox.showinfo('Warning', 'No file selected.')
      return
   current_file = path
   if path.endswith('.bmp'):
      current_img = Image.open(path)
      show_image(original_panel, current_img)
   elif path.endswith('.txt'):
      current_img = None
      original_panel.config(image='', text=f'Text: {os.path.basename(path)}', fg='black', bg='white')

def run_compress(level):
   if not current_file:
      messagebox.showinfo('Warning', 'Please select a file first.')
      return
   try:
      fns = {1: level1_compress, 2: level2_compress, 3: level3_compress,
             4: level4_compress, 5: level5_compress}
      result = fns[level](current_file)
      out_path, entropy, avg_cl, cr, orig_size, comp_size, img = result
      update_stats(entropy, avg_cl, cr, orig_size, comp_size)
      if img:
         show_image(original_panel, img)
      messagebox.showinfo('Done', f'Compressed to:\n{os.path.basename(out_path)}')
   except Exception as e:
      messagebox.showerror('Error', str(e))

def run_decompress(level):
   path = filedialog.askopenfilename(
      title='Select compressed file',
      filetypes=[('Binary files', '*.bin'), ('All files', '*.*')]
   )
   if not path:
      return
   try:
      fns = {1: level1_decompress, 2: level2_decompress, 3: level3_decompress,
             4: level4_decompress, 5: level5_decompress}
      out_path, img = fns[level](path)
      if img:
         global decompressed_img
         decompressed_img = img
         show_image(decompressed_panel, img)
      messagebox.showinfo('Done', f'Decompressed to:\n{os.path.basename(out_path)}')
   except Exception as e:
      messagebox.showerror('Error', str(e))

def show_image(panel, img):
   img_copy = img.copy()
   img_copy.thumbnail((300, 240))
   tk_img = ImageTk.PhotoImage(img_copy)
   panel.config(image=tk_img, text='')
   panel.photo_ref = tk_img

def show_channel(channel):
   global current_img
   if not current_img:
      messagebox.showinfo('Warning', 'Please select an image first.')
      return
   img = current_img.copy()
   if channel == 'color':
      show_image(original_panel, img)
   elif channel == 'gray':
      show_image(original_panel, img.convert('L'))
   else:
      if img.mode != 'RGB':
         img = img.convert('RGB')
      arr = np.array(img)
      idx = {'red': 0, 'green': 1, 'blue': 2}[channel]
      mask = np.zeros_like(arr)
      mask[:, :, idx] = arr[:, :, idx]
      show_image(original_panel, Image.fromarray(mask))

def update_stats(entropy, avg_cl, cr, orig_size, comp_size):
   lbl_entropy.config(text=f'Entropy: {entropy:.4f} bits/pixel')
   lbl_avg_cl.config(text=f'Average Code Length: {avg_cl:.4f} bits/pixel')
   lbl_cr.config(text=f'Compression Ratio: {cr:.4f}')
   lbl_input_size.config(text=f'Input Image Size: {orig_size:,} bytes')
   lbl_comp_size.config(text=f'Compressed Image Size: {comp_size:,} bytes')
   lbl_diff.config(text=f'Difference: {orig_size - comp_size:,} bytes')

if __name__ == '__main__':
   start()
