import sys
from ocr import OCR
from datetime import datetime

st = datetime.now()
ocr = OCR()
a = open(sys.argv[1])
b = a.read()
c = ocr.annotate(b)
for i in c.views:
    a = i.__dict__
    print (a)
    c = a.get("contains")
    bd = a.get("annotations")
    for d in bd:
        print (d.__dict__)
print (datetime.now()-st)