import sys
import numpy as np
import webbrowser

#bigEndian ">"
#littleEndian "<"
endian = ">"
gps = False

#単数値を返すとき. ポインタなど
def frombuffer(entrypoint, outbyte, data):
    return np.frombuffer(data, dtype=endian +"u"+ str(outbyte), offset=entrypoint, count=1)[0]

#ASCii文字列を返すとき. 文字数はバイト数で判断
def frombufferStr(entrypoint, outbyte, data):
    return np.frombuffer(data, dtype="S"+str(outbyte), offset=entrypoint, count=1)[0]

#複数値のtupleを返すとき. short,long
def frombuffernum(entrypoint, outbyte, num, data):
    return np.frombuffer(data, dtype=endian +"u"+ str(outbyte), offset=entrypoint, count=num)

def tude(tude):
    sec = (tude[2]//tude[3])/60
    min = (tude[4]/tude[5])/3600
    tudew = tude[0]//tude[1] + sec + min
    return tudew

#GPS IFD のロード
def GPS(p, data):
    latitude = False
    Longitude = False
    print("---GPS infomation found!---")
    tn = frombuffer(p,2,data) #tag amount
    t = np.array([0]*4, dtype="uint32")
    for i in range(tn):
        t[0] = frombuffer(i*12 + p+2, 2, data) #tag
        t[1] = frombuffer(i*12 + p+4, 2, data) #type
        t[2] = frombuffer(i*12 + p+6, 4, data) #value
        t[3] = frombuffer(i*12 + p+10, 4, data) #value or offset
        #print (t, end="")
        #print (" ... ", end="")

        ta = t[0]
        if ta == 0:
            ver = frombuffernum(0,1, t[2], t[3])
            print("GPS Ver. "+str(ver[0])+"."+str(ver[1])+"."+str(ver[2])+"."+str(ver[3]))

        if ta == 1:
            print("LatitudeRef: ",end="")
            if tag_in[2] > 4:
                print(frombuffer(t[3], t[2], data))
            else:
                print(frombuffer(0,t[2],t[3]))
        
        if ta == 2:
            print("Latitude: ",end="")
            latiw = tude(frombuffernum(t[3],4,t[2]*2,data))
            print(latiw)
            latitude = True
        
        if ta == 3:
            print("LongitudeRef: ",end="")
            if tag_in[2] > 4:
                print(frombuffer(t[3], t[2], data))
            else:
                print(frombuffer(0,t[2],t[3]))

        if ta == 4:
            print("Longitude: ",end="")
            longiw = tude(frombuffernum(t[3],4,t[2]*2,data))
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
    print ("Require input file name. ",end="")
    print ("Example: run exifLoad.py <filename>")
    sys.exit()

param = sys.argv[1]
f = open(param,'rb')

head = f.read(4)
val = frombuffer(0, 2, head)
if val == 0xFFD8:
    val = frombuffer(2, 2, head)
    if val == 0xFFE1:
        print ("Header format is Exif.")
    elif val == 0xFFE0:
        print ("Header format is JFIF. GPS infomation contains Exif format.")
        sys.exit()
else:
    print ("This file is not JPEG.")
    sys.exit()

f.read(8) #スキップ

#ポインタをわかりやすくするためここですべてread
bin = f.read()
#Tiffヘッダ エンディアン決定
val = frombuffer(0, 2, bin)
if val==0x4D4D:
    endian = ">"
elif val==0x4949:
    endian = "<"

#0th IFDへのポインタ
point = frombuffer(4,4,bin)

#0th IFD
tag_n = frombuffer(point,2,bin) #tag amount
tag_in = np.array([0]*4, dtype="uint32")
for i in range(tag_n):
    tag_in[0] = frombuffer(i*12 + point+2, 2, bin) #tag
    tag_in[1] = frombuffer(i*12 + point+4, 2, bin) #type
    tag_in[2] = frombuffer(i*12 + point+6, 4, bin) #value
    tag_in[3] = frombuffer(i*12 + point+10, 4, bin) #value or offset

    tag = tag_in[0]
    if tag == 34853:
        #print("GPS IFD pointer")
        print("")
        gps = GPS(tag_in[3], bin)

if not gps:
    print ("GPS infomation not found.")

f.close()
