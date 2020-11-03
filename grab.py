#####################################
#                                   #
#           genshin lol             #        
#                                   #
#####################################


from PIL import ImageGrab, Image
import win32gui
from win32api import GetSystemMetrics
from time import sleep
import cv2
import pytesseract
from pytesseract import Output
import numpy as np
import itertools
import json

from utils import exceptions

def _phase_0_init(return_globals=False):
    """
    Initialize basic global constants
    """
    global fullscr_w, fullscr_h, cut_profile
    fullscr_w = GetSystemMetrics(0)
    fullscr_h = GetSystemMetrics(1)
    with open('settings/cut_profile.json' , 'r') as f:
        cut_profile = json.load(f)
        f.close()
    if return_globals:
        return fullscr_w, fullscr_h, cut_profile

_phase_0_init()

def get_cut_pos(cut_profile_name):
    """
    Get cutting positions of selected profile. returns a tuple
    of four integers describing which section of screen that
    should be cut. Currently, only works with relative sizes,
    assuming:
    - initial x (left)
    - initial y (top)
    - end x (left)
    - end y (bottom)
    """
    return tuple(cut_profile[cut_profile_name][cut_pos] for cut_pos in cut_profile['common_attribute']['cut_pos'])

def box_char_list():
    """
    Get cutting positions for character list profile
    """
    _l, _t, _r, _b = get_cut_pos('box_char_list')
    return (
        int(round(fullscr_w*_l)),
        int(round(fullscr_h*_t)),
        int(round(fullscr_w*_r)),
        int(round(fullscr_h*_b))
    )

COLLECTION_TYPES = [tuple, list]  

def get_window(interval=1):
    """
    Get current Genshin Impact game screen
    """
    global winlist, hwnd
    toplist, winlist = [], []

    def _enum_cb(hwnd, results):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))

    win32gui.EnumWindows(_enum_cb, toplist)
    windows = [(hwnd, title) for hwnd, title in winlist if 'genshinimpact' in title.lower() or 'genshin impact' in title.lower()]
    print(f'windows = {windows}')
    # just grab the hwnd for first window matching genshin impact
    app = windows[0]
    hwnd = app[0]
    sleep(interval)
    win32gui.SetForegroundWindow(hwnd)
    bbox = win32gui.GetWindowRect(hwnd)

    return bbox

def resized_box_size(box, as_tuple=True, **kwargs):
    """
    Get the second axis size by the given first axis size
    based on the aspect ratio given derived from box
    """

    if type(box) not in COLLECTION_TYPES:
        raise TypeError(f'Argument box has to be a tuple or list. Passed argument is {type(box)}')
    if len(box)!=4:
        raise exceptions.ImproperArgumentError(
            error_type=exceptions.IMPROPER_ARGUMENT_TYPE.WRONG_FORMAT,
            message=f'Argument box has to be a tuple or list with exactly 4 items. Your argument has {len(box)} item(s).',
            args=box
        )
    if any([type(x)!=int for x in box]):
        raise TypeError('All 4 items of argument box tuple/list must be an integer.')
    bwidth = box[2]-box[0]
    bheight = box[3]-box[1]
    if 'basewidth' in kwargs:
        if 'baseheight' in kwargs:
            raise exceptions.ImproperArgumentError(
                error_type=exceptions.IMPROPER_ARGUMENT_TYPE.TOO_MUCH,
                message=f'You may only pass either basewidth or baseheight keyword argument, not both.',
                args=kwargs
            )
        axis_first = kwargs['basewidth']
        axis_second = int(round((axis_first*bheight)/bwidth))
        return (axis_first, axis_second) if as_tuple else axis_second
    elif 'baseheight' in kwargs:
        axis_first = kwargs['baseheight']
        axis_second = int(round((axis_first*bwidth)/bheight))
        return (axis_second, axis_first) if as_tuple else axis_second
    else:
        raise exceptions.ImproperArgumentError(
            error_type=exceptions.IMPROPER_ARGUMENT_TYPE.NOT_MUCH,
            message=f'You may only pass either basewidth or baseheight keyword argument, not none of them.',
            args=kwargs
        )

def _phase_1_init(return_globals=False, interval=1):
    """
    Initialize advanced constants after processing the setting files.
    """
    global box_cl, bbox, _cl_base_default_key, _cl_base, cl_resized_size, cl_basewidth, cl_baseheight
    box_cl = box_char_list()
    bbox = get_window(interval=interval)
    _cl_base_default_key = cut_profile['box_char_list']['base_default_key']
    if _cl_base_default_key not in cut_profile['box_char_list']['valid_base_default_keys']:
        raise exceptions.SettingsError(
            "base_default_key can only be either basewidth or baseheight"
        )
    _cl_base = cut_profile['box_char_list'][_cl_base_default_key]
    if _cl_base_default_key == 'basewidth':
        cl_resized_size = resized_box_size(box_cl, basewidth=_cl_base)
    else:
        cl_resized_size = resized_box_size(box_cl, baseheight=_cl_base)
    cl_basewidth, cl_baseheight = cl_resized_size
    if return_globals:
        return box_cl, bbox, cl_resized_size, cl_basewidth, cl_baseheight

_phase_1_init()  

def get_image(bbox=bbox):
    img = ImageGrab.grab(bbox)
    return img

def crop_image(img, box):
    imgcrop = img.crop(box=box_cl)
    imgcrop = imgcrop.resize((cl_basewidth,cl_baseheight), Image.ANTIALIAS)
    imgcrop_bw = imgcrop.convert('L')
    imgcrop_bw_np = np.array(imgcrop_bw,dtype='uint8')
    ret,tr = cv2.threshold(imgcrop_bw_np,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    return {
        'imgcrop':imgcrop, 'tr':tr, 'ret':ret
    }

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

def get_roster(shots=100, bbox=bbox):
    global img_comp, imgcrop_comp, data_comp, name_comp, finale, finname
    img_comp = []
    imgcrop_comp = []
    data_comp = []
    name_comp = []
    shots = 100

    for i in range(shots):
        print(f'try {i}')
        img_comp.append(get_image(bbox=bbox))
        imgcrop_comp.append(crop_image(img_comp[-1], box_cl))
        data_comp.append(get_data(imgcrop_comp[-1]['imgcrop'], imgcrop_comp[-1]['tr']))
        name_comp.append(filter_names(data_comp[-1]['tesdat']['text']))

    Image.fromarray(data_comp[-1]['outimg']).show()

    finale = finalize_names(name_comp)
    finname = list(finale['roster'])

    print('Gotcha! valid rosters are:')
    print("\n".join(finname))

    return img_comp, imgcrop_comp, data_comp, name_comp, finale, finname

get_roster(100)