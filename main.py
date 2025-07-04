import cv2
import numpy as np
import pytesseract
import math
from scipy import ndimage
import imutils




lang = "eng+fra+ara+osd"
config = "--psm 11 --oem 3"





def translate(img, x, y):
    transMat = np.float32([[1, 0, x], [0, 1, y]])
    dimensions = (img.shape[1], img.shape[0])
    return cv2.warpAffine(img, transMat, dimensions)


def getcontour(img, blank1):
    contours, hierarchies = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    max_area = 0
    cropped_image = 0
    rect=0
    x, y, w, h = 0, 0, 0, 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 8200:
            print("are",area)
            
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            print(len(approx))
            print(peri)
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            print("im box",box)
            cv2.drawContours(imgcon, [box], 0, (0, 191, 255), 2)
            x, y, w, h = cv2.boundingRect(box)
            print("points:", x, y, w, h)
            print("points addition:", x + h, w + h)
            cv2.rectangle(imgcon, (x - 15, y + 3), (x + w, y + h), (0, 255, 0), 2)
            cropped_image = imgcon[y:y + h, x:x + w]
            print(cropped_image.shape)
            print(len(contours), "countours found")
    return x, y, w, h, cropped_image, rect

def crop_minAreaRect(img, rect,angle):

    
    rows,cols = img.shape[0], img.shape[1]
    M = cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
    img_rot = cv2.warpAffine(img,M,(cols,rows))

    
    rect0 = (rect[0], rect[1], 0.0)
    box = cv2.boxPoints(rect0)
    pts = np.int0(cv2.transform(np.array([box]), M))[0]
    pts[pts < 0] = 0

    
    img_crop = img_rot[pts[1][1]:pts[0][1],
                       pts[1][0]:pts[2][0]]

    return img_crop

def thr(img):
    th = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    th1 = cv2.resize(th, None, fx=1, fy=1, interpolation=cv2.INTER_CUBIC)
    return th1


def sharp(img):
    laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
    print(laplacian_var)
    if laplacian_var < 700:
        print('image is blurry')
        sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpen = cv2.filter2D(img, -1, sharpen_kernel)
    else:
        sharpen = img
    return sharpen

def dilat(img):
    
    dilated_img = cv2.dilate(img[:, :, 1], np.ones((7, 7), np.uint8))
    bg_img = cv2.medianBlur(dilated_img, 21)

    
    diff_img = 255 - cv2.absdiff(img[:, :, 1], bg_img)
    
    resized = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
    
    return resized

def cropcol(img1,cropped_image):
    
    rows, cols, channels = cropped_image.shape
    print(cropped_image.shape)
    roi = cropped_image[0:rows, 0:cols]

    
    img2gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)

    
    img1_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)

    
    img2_fg = cv2.bitwise_and(cropped_image, cropped_image, mask=mask)
    
    dst = cv2.add(img1_bg, img2_fg)
    img1[0:rows, 0:cols] = dst
    return img1

img = cv2.imread("70.jpg")
img = cv2.resize(img, (595, 742), interpolation=cv2.INTER_AREA)
cv2.imshow("orginal",img)
cv2.waitKey(0)
blank1 = np.zeros(img.shape, dtype='uint8')
print(img.shape[1])
print(img.shape[0])


blur = cv2.GaussianBlur(img, (3, 3), cv2.BORDER_DEFAULT)

edges = cv2.Canny(blur, 125, 175)
cv2.imshow("orginal", edges)
cv2.waitKey(0)
translated = translate(img, -100, 100)


imgcon = img.copy()
kernel = np.ones((5, 5))
dilated = cv2.dilate(edges, kernel, iterations=1)
cv2.imshow("dilated",dilated)
cv2.waitKey(0)
box=[]
x, y, w, h, cropped_image,box = getcontour(dilated, imgcon)
cv2.imshow("crop",cropped_image)
cv2.waitKey(0)

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

img = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
sharpu=sharp(img)
gray= cv2.cvtColor(sharpu, cv2.COLOR_RGB2GRAY)
t1 = dilat(sharpu)
t2 = thr(gray)

img1 = cv2.imread('download.png')
img1 = cv2.resize(img1, (595, 742), interpolation=cv2.INTER_AREA)

img_gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
img_edges = cv2.Canny(img_gray, 100, 100, apertureSize=3)
lines = cv2.HoughLinesP(img_edges, 1, math.pi / 180.0, 100, minLineLength=100, maxLineGap=5)

angles = []

for [[x1, y1, x2, y2]] in lines:
    
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    angles.append(angle)
median_angle = np.median(angles)

if median_angle !=0:
    
    
    print(box)
    (h, w) = cropped_image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D((cX, cY), median_angle, 1.0)
    
    rotated = imutils.rotate(cropped_image, median_angle)
    
    print(f"Angle is {median_angle:.04f}")
    
    fromCenter = False
    r = cv2.selectROI(rotated, fromCenter)
    
    

    imCrop = rotated[int(r[1]):int(r[1] + r[3]), int(r[0]):int(r[0] + r[2])]

    cv2.imshow("Mask Applied to Image", imCrop)
    cv2.waitKey(0)
    
    blur = cv2.GaussianBlur(imCrop, (3, 3), cv2.BORDER_DEFAULT)
    
    edges = cv2.Canny(blur, 125, 175)
    dilated = cv2.dilate(edges, kernel, iterations=1)
    x, y, w, h, cropped_image, box = getcontour(dilated, imgcon)

    print(pytesseract.image_to_string(imCrop, lang=lang, config=config))
    img1 = cropcol(img1, imCrop)
else:
    img1 = cropcol(img1, cropped_image)

cv2.imshow('final version',img1)
print(pytesseract.image_to_string(img1, lang=lang, config=config))
cv2.waitKey(0)
cv2.destroyAllWindows()