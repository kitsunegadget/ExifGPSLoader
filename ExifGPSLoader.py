import sys
import numpy as np
import struct
import webbrowser

#bigEndian ">"
#littleEndian "<"
endian = ">"

class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
    
    def read(self, size):
        if size == 2:
            result = struct.unpack(endian+"H", self.data[self.pos: self.pos+2])[0]
            self.pos += 2
            return result

        elif size == 4:
            result = struct.unpack(endian+"I", self.data[self.pos: self.pos+4])[0]
            self.pos += 4
            return result
    
    def read_str(self, size):
        #ASCii文字列を返すとき. 文字数はバイト数で判断
        result = np.frombuffer(self.data, dtype="S"+str(size), offset=self.pos, count=1)[0]
        self.pos += size
        return result
    
    def read_uint_tuple(self, size, num):
        #複数値の配列を返すとき. short,long
        result = np.frombuffer(self.data, dtype=endian+"u"+str(size), offset=self.pos, count=num)
        self.pos += size
        return result
    
    def read_skip(self, size):
        self.pos += size
    
    def set_pos(self, pos):
        self.pos = pos
    
    def get_pos(self):
        return self.pos


def tude(tude): #60進法を10進法に
    sec = (tude[2]//tude[3])/60
    min = (tude[4]/tude[5])/3600
    tudew = tude[0]//tude[1] + sec + min
    return tudew

#GPS IFD のロード
def GPS(pointer, reader):
    latitude = False
    longitude = False
    print("---GPS infomation was found!---")

    reader.set_pos(pointer)
    tag_n = reader.read(2) #tag amount
    for i in range(tag_n):
        tag = reader.read(2) #tag
        _type = reader.read(2) #type
        value = reader.read(4) #value
        value_offset = reader.read(4) #value or offset
        #print (t, end="")
        #print (" ... ", end="")

        cur = reader.get_pos()
        tag = tag
        if tag == 0:
            if endian == ">":
                en = "big"
            else:
                en = "little"
            
            ver = np.frombuffer(value_offset.to_bytes(value, en), dtype=endian+"u1", offset=0, count=value)
            #print("GPS Ver. "+str(ver[0])+"."+str(ver[1])+"."+str(ver[2])+"."+str(ver[3]))
            print(f"GPS Ver. {ver[0]}.{ver[1]}.{ver[2]}.{ver[3]}") # f-strings 

        elif tag == 1:
            print("LatitudeRef: ", end="")
            if value > 4:
                reader.set_pos(value_offset)
                print(reader.read(value))
            else:
                print(value_offset)
        
        elif tag == 2:
            print("Latitude: ",end="")
            reader.set_pos(value_offset)
            latiw = tude(reader.read_uint_tuple(4,value*2))
            print(latiw)
            latitude = True
        
        elif tag == 3:
            print("LongitudeRef: ",end="")
            if value > 4:
                reader.set_pos(value_offset)
                print(reader.read(value))
            else:
                print(value_offset)

        elif tag == 4:
            print("Longitude: ",end="")
            reader.set_pos(value_offset)
            longiw = tude(reader.read_uint_tuple(4,value*2))
            print(longiw)
            longitude = True
        
        reader.set_pos(cur)

    print()
    if latitude and longitude:
        print ("Access to this point on Google Map? [YES:y / NO:other key]")
        select = input()
        if select == "y":
            webbrowser.open("https://google.co.jp/maps/search/"+str(latiw)+","+str(longiw))

    return True

########################
#----ここからmain---------
########################
if len(sys.argv) == 1:
    print("Require input file name. ", end="")
    print("Example: python exifGPSLoad.py <filename>")
    sys.exit()

param = sys.argv[1]
f = open(param, 'rb')

jpghead = struct.unpack(endian+"H", f.read(2))[0]
if jpghead == 0xFFD8: #JPEGヘッダの確認
    exifhead = struct.unpack(endian+"H", f.read(2))[0]
    if exifhead == 0xFFE1: #Exifヘッダの確認
        print("Header format is Exif.")
    elif exifhead == 0xFFE0: #JFIFヘッダの場合
        raise Exception("Header format is JFIF. GPS infomation contains Exif format.")
else:
    raise Exception("This file is not JPEG.")

f.read(8) #スキップ


#内部データポインタはここから0として計算されるのでここから全体を参照させる
reader = Reader(f.read())

#Tiffヘッダ エンディアン決定
val = reader.read(2)
if val == 0x4D4D:
    endian = ">" #BIG Endian
elif val == 0x4949:
    endian = "<" #LITTLE Endian

reader.read_skip(2)

#0th IFDへのポインタ
pointer_0th = reader.read(4)
reader.set_pos(pointer_0th)

#0th IFD
tag_n = reader.read(2) #tagの総数
gps = False
for i in range(tag_n):
    tag = reader.read(2) #tag
    _type = reader.read(2) #type
    value = reader.read(4) #value
    value_offset = reader.read(4) #value or offset

    current_pos = reader.get_pos()
    if tag == 34853:
        #print("GPS IFD pointer")
        print("")
        gps = GPS(value_offset, reader)
        
    reader.set_pos(current_pos)

if not gps:
    print("GPS infomation not found.")

f.close()
