import sys
import numpy as np
import webbrowser

#bigEndian ">"
#littleEndian "<"
endian = ">"
gps = False

#単数値を返すとき. ポインタなど
def BinToInt(entrypoint, inputbytes, data):
    return np.frombuffer(data, dtype=endian +"u"+ str(inputbytes), offset=entrypoint, count=1)[0]

#ASCii文字列を返すとき. 文字数はバイト数で判断
def BinToStr(entrypoint, inputbytes, data):
    return np.frombuffer(data, dtype="S"+str(inputbytes), offset=entrypoint, count=1)[0]

#複数値のtupleを返すとき. short,long
def BinToTuple(entrypoint, inputbytes, num, data):
    return np.frombuffer(data, dtype=endian +"u"+ str(inputbytes), offset=entrypoint, count=num)

def tude(tude): #60進法を10進法に
    sec = (tude[2]//tude[3])/60
    min = (tude[4]/tude[5])/3600
    tudew = tude[0]//tude[1] + sec + min
    return tudew

#GPS IFD のロード
def GPS(p, data):
    latitude = False
    longitude = False
    print("---GPS infomation was found!---")

    tag_n = BinToInt(p, 2, data) #tag amount
    tag_inside = np.array([0]*4, dtype="uint32")
    for i in range(tag_n):
        tag_inside[0] = BinToInt(i*12 + p+2, 2, data) #tag
        tag_inside[1] = BinToInt(i*12 + p+4, 2, data) #type
        tag_inside[2] = BinToInt(i*12 + p+6, 4, data) #value
        tag_inside[3] = BinToInt(i*12 + p+10, 4, data) #value or offset
        #print (t, end="")
        #print (" ... ", end="")

        tag = tag_inside[0]
        if tag == 0:
            ver = BinToTuple(0, 1, tag_inside[2], tag_inside[3])
            print("GPS Ver. "+str(ver[0])+"."+str(ver[1])+"."+str(ver[2])+"."+str(ver[3]))

        if tag == 1:
            print("LatitudeRef: ", end="")
            if tag_inside[2] > 4:
                print(BinToInt(tag_inside[3], tag_inside[2], data))
            else:
                print(BinToInt(0, tag_inside[2], tag_inside[3]))
        
        if tag == 2:
            print("Latitude: ",end="")
            latiw = tude(BinToTuple(tag_inside[3],4,tag_inside[2]*2,data))
            print(latiw)
            latitude = True
        
        if tag == 3:
            print("LongitudeRef: ",end="")
            if tag_inside[2] > 4:
                print(BinToInt(tag_inside[3], tag_inside[2], data))
            else:
                print(BinToInt(0,tag_inside[2],tag_inside[3]))

        if tag == 4:
            print("Longitude: ",end="")
            longiw = tude(BinToTuple(tag_inside[3],4,tag_inside[2]*2,data))
            print(longiw)
            longitude = True

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

head = f.read(4)
val = BinToInt(0, 2, head)
if val == 0xFFD8: #JPEGヘッダの確認
    val = BinToInt(2, 2, head)
    if val == 0xFFE1: #Exifヘッダの確認
        print("Header format is Exif.")
    elif val == 0xFFE0: #JFIFヘッダの場合
        print("Header format is JFIF. GPS infomation contains Exif format.")
        sys.exit()
else:
    print("This file is not JPEG.")
    sys.exit()

f.read(8) #スキップ

#ポインタをわかりやすくするためここですべてread
binar = f.read()
#Tiffヘッダ エンディアン決定
val = BinToInt(0, 2, binar)
if val == 0x4D4D:
    endian = ">" #BIG Endian
elif val == 0x4949:
    endian = "<" #LITTLE Endian

#0th IFDへのポインタ
pointer = BinToInt(4, 4, binar)

#0th IFD
tag_n = BinToInt(pointer, 2, binar) #tagの総数
tag_inside = np.array([0]*4, dtype="uint32") #配列初期化
for i in range(tag_n):
    tag_inside[0] = BinToInt(i*12 + pointer+2, 2, binar) #tag
    tag_inside[1] = BinToInt(i*12 + pointer+4, 2, binar) #type
    tag_inside[2] = BinToInt(i*12 + pointer+6, 4, binar) #value
    tag_inside[3] = BinToInt(i*12 + pointer+10, 4, binar) #value or offset

    tag = tag_inside[0]
    if tag == 34853:
        #print("GPS IFD pointer")
        print("")
        gps = GPS(tag_inside[3], binar)

if not gps:
    print("GPS infomation not found.")

f.close()
