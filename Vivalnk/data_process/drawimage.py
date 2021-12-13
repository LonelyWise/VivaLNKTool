#!/usr/bin/env python 
# coding:utf-8

from PIL import Image,ImageFilter,ImageOps

img = Image.open('/Users/xuwei/Desktop/手机照片/IMG_0801.JPG')

def dodge(a,b,alpha):

    print(a)
    print(b)
    return min(int(a*255/(256-121*alpha)),255)

def draw(img,blur=25,alpha=1.0):
    img1 = img.convert('L')
    img2 = img.copy()
    img2 = ImageOps.invert(img2)
    for i in range(blur):
        img2 = img2.filter(ImageFilter.BLUR)
    width,height = img1.size
    for x in range(width):
        for y in range(height):
            a = img1.getpixel((x,y))
            b = img2.getpixel((x,y))
            img1.putpixel((x,y),dodge(a,b,alpha))
    img1.show()
    img1.save('/Users/xuwei/Desktop/手机照片/sumiao_0801.JPG')

if __name__ == '__main__':
    draw(img)

