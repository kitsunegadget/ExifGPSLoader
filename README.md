# Exif GPS Loader

EXIFヘッダで保存されている jpeg 画像から GPS 情報を取得したかっただけのプログラム。


## 実行例

``` 
>python ExifGPSLoader.py ebishake.jpg
Header format is Exif.

---GPS infomation was found!---
LatitudeRef: 78
Latitude: 43.2138888889
LongitudeRef: 69
Longitude: 141.6425

Access to this point on Google Map? [YES:y / NO:other key]
y
```

位置情報があった場合、Access on this point ~ と聞かれたときに y を押すと Google Map 上で表示します。(実行例の位置情報は北海道のスポットです。)