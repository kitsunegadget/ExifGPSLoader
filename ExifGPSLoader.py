import sys
import numpy as np
import webbrowser

#bigEndian ">"
#littleEndian "<"
endian = ">"

class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
    
    def read_uint(self, size):
        #単数値を返すとき. ポインタなど
        result = np.frombuffer(self.data, dtype=endian+"u"+str(size), offset=self.pos, count=1)[0]
        self.pos += size
        return result
    
    def read_str(self, size):
        #ASCii文字列を返すとき. 文字数はバイト数で判断
        result = np.frombuffer(self.data, dtype="S"+str(size), offset=self.pos, count=1)[0]
        self.pos += size
        return result
    
    def read_uint_tuple(self, size, num):
        #複数値でtupleを返すとき. short,long
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
    tag_n = reader.read_uint(2) #tag amount
    for i in range(tag_n):
        tag = reader.read_uint(2) #tag
        _type = reader.read_uint(2) #type
        value = reader.read_uint(4) #value
        value_offset = reader.read_uint(4) #value or offset
        #print (t, end="")
        #print (" ... ", end="")

        cur = reader.get_pos()
        tag = tag
        if tag == 0:
            ver = np.frombuffer(value_offset, dtype=endian+"u"+str(1), offset=0, count=value)
            print("GPS Ver. "+str(ver[0])+"."+str(ver[1])+"."+str(ver[2])+"."+str(ver[3]))

        elif tag == 1:
            print("LatitudeRef: ", end="")
            if value > 4:
                reader.set_pos(value_offset)
                print(reader.read_uint(value))
            else:
                print(np.frombuffer(value_offset, dtype=endian+"u"+str(value), offset=0, count=1)[0])
        
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
                print(reader.read_uint(value))
            else:
                print(np.frombuffer(value_offset, dtype=endian+"u"+str(value), offset=0, count=1)[0])

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

jpghead = np.frombuffer(f.read(2), dtype=endian+"u"+str(2), offset=0, count=1)[0]
if jpghead == 0xFFD8: #JPEGヘッダの確認
    exifhead = np.frombuffer(f.read(2), dtype=endian+"u"+str(2), offset=0, count=1)[0]
    if exifhead == 0xFFE1: #Exifヘッダの確認
        print("Header format is Exif.")
    elif exifhead == 0xFFE0: #JFIFヘッダの場合
        print("Header format is JFIF. GPS infomation contains Exif format.")
        sys.exit()
else:
    raise Exception("This file is not JPEG.")

f.read(8) #スキップ


#内部データポインタはここから0として計算されるのでここから全体を参照させる
reader = Reader(f.read())

#Tiffヘッダ エンディアン決定
val = reader.read_uint(2)
if val == 0x4D4D:
    endian = ">" #BIG Endian
elif val == 0x4949:
    endian = "<" #LITTLE Endian

reader.read_skip(2)

#0th IFDへのポインタ
pointer_0th = reader.read_uint(4)
reader.set_pos(pointer_0th)

#0th IFD
tag_n = reader.read_uint(2) #tagの総数
gps = False
for i in range(tag_n):
    tag = reader.read_uint(2) #tag
    _type = reader.read_uint(2) #type
    value = reader.read_uint(4) #value
    value_offset = reader.read_uint(4) #value or offset

    if tag == 34853:
        #print("GPS IFD pointer")
        print("")
        current_pos = reader.get_pos()
        gps = GPS(value_offset, reader)
        reader.set_pos(current_pos)

if not gps:
    print("GPS infomation not found.")

f.close()
