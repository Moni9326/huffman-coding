import heapq
import os
import struct

class BinaryTree:
    def __init__(self, value, frequ):
        self.value = value
        self.frequ = frequ
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.frequ < other.frequ

    def __eq__(self, other):
        return self.frequ == other.frequ

class Huffmancode:
    def __init__(self, path):
        self.path = path
        self.__heap = []
        self.__code = {}
        self.__reversecode = {}

    def __frequency_from_text(self, text):
        frequ_dict = {}
        for char in text:
            if char not in frequ_dict:
                frequ_dict[char] = 0
            frequ_dict[char] += 1
        return frequ_dict

    def __Build_heap(self, frequency_dict):
        for key in frequency_dict:
            frequency = frequency_dict[key]
            binary_tree_node = BinaryTree(key, frequency)
            heapq.heappush(self.__heap, binary_tree_node)

    def __Build_Binary_Tree(self):
        while len(self.__heap) > 1:
            binary_tree_node_1 = heapq.heappop(self.__heap)
            binary_tree_node_2 = heapq.heappop(self.__heap)
            sum_of_freq = binary_tree_node_1.frequ + binary_tree_node_2.frequ
            newnode = BinaryTree(None, sum_of_freq)
            newnode.left = binary_tree_node_1
            newnode.right = binary_tree_node_2
            heapq.heappush(self.__heap, newnode)

    def __Build_Tree_Code_Helper(self, root, curr_bits):
        if root is None:
            return
        if root.value is not None:
            self.__code[root.value] = curr_bits
            self.__reversecode[curr_bits] = root.value
            return
        self.__Build_Tree_Code_Helper(root.left, curr_bits + '0')
        self.__Build_Tree_Code_Helper(root.right, curr_bits + '1')

    def __Build_Tree_Code(self):
        root = heapq.heappop(self.__heap)
        self.__Build_Tree_Code_Helper(root, '')

    def __Build_Encoded_Text(self, text):
        encoded_text = ''
        for char in text:
            encoded_text += self.__code[char]
        return encoded_text

    def __Build_Padded_Text(self, encoded_text):
        padding_value = 8 - (len(encoded_text) % 8)
        for _ in range(padding_value):
            encoded_text += '0'
        padded_info = "{0:08b}".format(padding_value)
        padded_encoded_text = padded_info + encoded_text
        return padded_encoded_text

    def __Build_Byte_Array(self, padded_text):
        array = []
        for i in range(0, len(padded_text), 8):
            byte = padded_text[i:i + 8]
            array.append(int(byte, 2))
        return array

    def __write_header(self, frequency_dict, output_file):
        n = len(frequency_dict)
        header_bytes = struct.pack('>H', n)
        output_file.write(header_bytes)
        
        for char, freq in frequency_dict.items():
            char_bytes = char.encode('utf-8')
            output_file.write(bytes([len(char_bytes)]))
            output_file.write(char_bytes)
            freq_bytes = struct.pack('>I', freq)
            output_file.write(freq_bytes)

    def compression(self):
        self.__heap = []
        self.__code = {}
        self.__reversecode = {}
        
        filename, _ = os.path.splitext(self.path)
        output_path = filename + '.bin'
        
        with open(self.path, 'r', encoding='utf-8') as file, open(output_path, 'wb') as output:
            text = file.read().rstrip()
            frequency_dict = self.__frequency_from_text(text)
            self.__write_header(frequency_dict, output)
            self.__Build_heap(frequency_dict)
            self.__Build_Binary_Tree()
            self.__Build_Tree_Code()
            encoded_text = self.__Build_Encoded_Text(text)
            padded_text = self.__Build_Padded_Text(encoded_text)
            bytes_array = self.__Build_Byte_Array(padded_text)
            final_bytes = bytes(bytes_array)
            output.write(final_bytes)
        
        print("Compression successful. Output file:", output_path)
        return output_path

    def __read_header(self, file):
        n_bytes = file.read(2)
        if not n_bytes:
            return None
        n = struct.unpack('>H', n_bytes)[0]
        frequency_dict = {}
        
        for _ in range(n):
            len_char = ord(file.read(1))
            char_bytes = file.read(len_char)
            char = char_bytes.decode('utf-8')
            freq_bytes = file.read(4)
            freq = struct.unpack('>I', freq_bytes)[0]
            frequency_dict[char] = freq
            
        return frequency_dict

    def __Remove_Padding(self, text):
        padded_info = text[:8]
        extra_padding = int(padded_info, 2)
        text = text[8:]
        padding_removed_text = text[:-1 * extra_padding]
        return padding_removed_text

    def __Decompress_Text(self, text):
        decoded_text = ''
        current_bits = ''
        for bit in text:
            current_bits += bit
            if current_bits in self.__reversecode:
                character = self.__reversecode[current_bits]
                decoded_text += character
                current_bits = ""
        return decoded_text

    def decompress(self, input_path):
        filename, _ = os.path.splitext(input_path)
        output_path = filename + '_decompressed.txt'
        
        with open(input_path, 'rb') as file, open(output_path, 'w', encoding='utf-8') as output:
            frequency_dict = self.__read_header(file)
            if frequency_dict is None:
                raise ValueError("Compressed file is empty or invalid")
            
            self.__heap = []
            self.__code = {}
            self.__reversecode = {}
            self.__Build_heap(frequency_dict)
            self.__Build_Binary_Tree()
            self.__Build_Tree_Code()
            
            bit_string = ''
            byte = file.read(1)
            while byte:
                byte_val = byte[0]
                bits = bin(byte_val)[2:].rjust(8, '0')
                bit_string += bits
                byte = file.read(1)
                
            actual_text = self.__Remove_Padding(bit_string)
            decompressed_text = self.__Decompress_Text(actual_text)
            output.write(decompressed_text)
        
        print("Decompression successful. Output file:", output_path)
        return output_path

if __name__ == "__main__":
    path = input("Enter the path of your file: ")
    h = Huffmancode(path)
    compressed_file = h.compression()
    h.decompress(compressed_file)