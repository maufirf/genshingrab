'''
from PIL import ImageGrab
import numpy as np
import cv2
from time import sleep
tf = 1
while(True):
    img = ImageGrab.grab(bbox=(100,10,400,780)) #bbox specifies specific region (bbox= x,y,width,height)
    img_np = np.array(img)
    frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
    cv2.imshow("test", frame)
    cv2.waitKey(0)
    #sleep(tf)
    cv2.destroyAllWindows()
'''

from PIL import ImageGrab, Image
import win32gui
from time import sleep
import cv2
from win32api import GetSystemMetrics
import pytesseract
from pytesseract import Output
import numpy as np
import itertools

fullscr_w = GetSystemMetrics(0)
fullscr_h = GetSystemMetrics(1)

def char_list_box():
    return (
        int(round(fullscr_w*.85)),
        int(round(fullscr_h*.3125)),
        int(round(fullscr_w*.925)),
        int(round(fullscr_h*.60))
    )

toplist, winlist = [], []
def enum_cb(hwnd, results):
    winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
win32gui.EnumWindows(enum_cb, toplist)

#print(f'winlist = {winlist}')

windows = [(hwnd, title) for hwnd, title in winlist if 'genshinimpact' in title.lower() or 'genshin impact' in title.lower()]
print(f'windows = {windows}')
# just grab the hwnd for first window matching firefox
app = windows[0]
hwnd = app[0]
sleep(1)
win32gui.SetForegroundWindow(hwnd)
bbox = win32gui.GetWindowRect(hwnd)

cropmaster = char_list_box()
basewidth = 600
hsize = int(round((basewidth/(cropmaster[2]-cropmaster[0]))*(cropmaster[3]-cropmaster[1])))

def get_image():
    img = ImageGrab.grab(bbox)
    imgcrop = img.crop(box=cropmaster)
    imgcrop = imgcrop.resize((basewidth,hsize), Image.ANTIALIAS)
    imgcrop_bw = imgcrop.convert('L')
    imgcrop_bw_np = np.array(imgcrop_bw,dtype='uint8')
    ret,tr = cv2.threshold(imgcrop_bw_np,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    return {
        'imgcrop':imgcrop, 'tr':tr, 'ret':ret
    }

'''
img = ImageGrab.grab(bbox)

# https://stackoverflow.com/questions/48311273/ocr-small-image-with-python
imgcrop = img.crop(box=char_list_box())

basewidth = 600
hsize = int(round((basewidth/imgcrop.size[0])*imgcrop.size[1]))

imgcrop = imgcrop.resize((basewidth,hsize), Image.ANTIALIAS)
#imgcrop.save("debug_plain.png")
imgcrop.show()

imgcrop_np = np.array(imgcrop,dtype='uint8')

imgcrop_bw = imgcrop.convert('L')
imgcrop_bw_np = np.array(imgcrop_bw,dtype='uint8')
ret,tr = cv2.threshold(imgcrop_bw_np,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
'''
#Image.fromarray(tr).save(f"debug_threshold.png")

#imgcrop_np = np.array(imgcrop_bw)[:, :, ::-1].copy()

def get_data(imgcrop, tr):
    outimg=np.array(imgcrop)
    tesdat=pytesseract.image_to_data(tr, output_type=Output.DICT)
    n_boxes = len(tesdat['level'])
    for i in range(n_boxes):
        (x, y, w, h) = (tesdat['left'][i], tesdat['top'][i], tesdat['width'][i], tesdat['height'][i])
        cv2.rectangle(outimg, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return {
        'tesdat':tesdat,
        'outimg':outimg
    }




'''tesdat=pytesseract.image_to_data(tr, output_type=Output.DICT)
n_boxes = len(tesdat['level'])
for i in range(n_boxes):
    (x, y, w, h) = (tesdat['left'][i], tesdat['top'][i], tesdat['width'][i], tesdat['height'][i])
    cv2.rectangle(imgcrop_np, (x, y), (x + w, y + h), (0, 255, 0), 2)

imgcrop_boxed = Image.fromarray(imgcrop_np)
imgcrop_boxed.save("debug_boxed.png")
imgcrop_boxed.show()'''

#print(tesdat['text'])

def filter_names(text_data):
    tex = text_data
    tex_truth = [len(x)>=4 for x in tex]
    tex_i = np.where(tex_truth)[0]
    tex_filtered = [tex[int(i)] for i in tex_i]
    return {
        'tex':tex,
        'tex_truth':tex_truth,
        'tex_i':tex_i,
        'tex_filtered':tex_filtered
    }

'''tex = tesdat['text']
tex_truth = [len(x)>=4 for x in tex]
tex_i = np.where(tex_truth)[0]
print(f'valid texts are on indices: {tex_i}')
tex_filtered = [tex[int(i)] for i in tex_i]
print(f'which are = {tex_filtered}')'''

img_comp = []
data_comp = []
name_comp = []
tries = 100

for i in range(tries):
    print(f'try {i}')
    img_comp.append(get_image())
    data_comp.append(get_data(img_comp[-1]['imgcrop'], img_comp[-1]['tr']))
    name_comp.append(filter_names(data_comp[-1]['tesdat']['text']))

Image.fromarray(data_comp[-1]['outimg']).show()

def finalize_names(name_comp):
    onlyvalids = [x['tex_filtered'] for x in name_comp]
    onlyvalids_flatten = [x for x in itertools.chain.from_iterable(onlyvalids)]
    unique,counts = np.unique(onlyvalids_flatten,return_counts=True)
    counts_sort_ind = np.argsort(-counts)
    unique_sort = unique[counts_sort_ind]
    counts_sort = counts[counts_sort_ind]
    roster = unique_sort[:4]
    return {
        'roster': roster,
        'unique': unique_sort,
        'counts': counts_sort
    }

finale = finalize_names(name_comp)
finname = list(finale['roster'])

print('Gotcha! valid rosters are:')
print("\n".join(finname))
