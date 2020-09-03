import datetime
import os

import numpy
from PIL import ImageCms, ImageDraw, Image, ImageFont, TiffImagePlugin

import io
from TT_sql import TT_sql

style_OK = "color: #cdd6e6;  font-size: 22px; font-family: Arial;"
style_not_OK = "color: #ff0000;  font-size: 22px; font-family: Arial;"
style_norm = "color: #cdd6e6;  font-size: 20px; font-family: Arial; background-color: rgba(55, 55, 68, " \
             "0.4); margin-bottom: 13px; margin-top: 13px; border: 1px solid; border-color: #516588; "
style_warning = "color: #cdd6e6;  font-size: 20px; font-family: Arial; background-color: rgba(55, 55, " \
                "68, 0.4); margin-bottom: 13px; margin-top: 13px; border: 4px solid; border-color: " \
                "#ff0000; "

euroscale_profile = ImageCms.getOpenProfile('icc/CMYK/EuroscaleCoated.icc')
screen_profile = ImageCms.getOpenProfile('icc/RGB/AppleRGB.icc')
image_tag_directory = TiffImagePlugin.ImageFileDirectory_v2()
image_tag_directory[305] = 'LayoutQC'
image_tag_directory[33432] = 'LayoutQC by Fedotov R.'


class Layout:

    def __init__(self, im):
        self.image = im
        self.compression = self.image.info.get('compression')
        # self.profile_ICC = self.image.info.get('icc_profile', '')
        self.resolution = self.image.info.get('dpi')[0]
        self.width_layout = round(self.image.size[0] / self.resolution * 25.4)
        self.height_layout = round(self.image.size[1] / self.resolution * 25.4)
        # self.mode = self.image.mode
        self.size = self.image.size
        self.comment = None

        if self.image.tag[296][0] == 2:
            self.unit_resolution = 'inch'
        elif self.image.tag[296][0] == 3:
            self.unit_resolution = 'cm'
            self.resolution = round(self.image.size[0] / self.width_layout * 10, 2)
        else:
            self.unit_resolution = 'Unknown'
            self.width_layout = 0
            self.height_layout = 0
        self.layout_db = TT_sql()
        self.layout_db_tabeles = self.layout_db.tables

        self.locations = [' ']
        self.prw_name = 'temp/input_temp.png'
        self.folderMaked = False

    def layout_mode_status(self):
        if self.image.mode != 'CMYK':
            style = style_warning
        else:
            style = style_norm
        return style

    def layout_profile_status(self):
        style = style_warning
        if self.image.info.get('icc_profile', ''):
            if ImageCms.getProfileName(io.BytesIO(self.image.info.get('icc_profile', ''))) == ImageCms.getProfileName(
                    euroscale_profile):
                style = style_norm
        return style

    def layout_profile_name(self):
        profile_name = "Untagged CMYK (8bpc)"
        if self.image.info.get('icc_profile', ''):
            profile_name = ImageCms.getProfileName(io.BytesIO(self.image.info.get('icc_profile', ''))).split('\n')[0]
        return profile_name

    def make_prw(self, prw_name, image=None, LayoutQC_DEBAG=False):
        if not image:
            image = self.image
        if not self.image.info.get('icc_profile', ''):
            profile_assighned = ImageCms.ImageCmsProfile(io.BytesIO(euroscale_profile.tobytes()))
            if LayoutQC_DEBAG:
                print("Untagged layout, assighned profile Euroscale Coated for converting to RGB preview")
        else:
            profile_assighned = ImageCms.ImageCmsProfile(io.BytesIO(self.image.info.get('icc_profile', '')))
        screen = ImageCms.profileToProfile(image, profile_assighned, screen_profile, 0, 'RGB')
        screen.save(prw_name, quality=100, dpi=(self.resolution, self.resolution), )

    def table_Activated(self, name_table_activate):
        if name_table_activate == ' ':
            self.locations = [' ']
        else:
            self.locations = self.layout_db.table_Activated(name_table_activate)
        return self.locations

    def location_Activated(self, name_locatoin_activate):
        if name_locatoin_activate == ' ':
            self.name = [' ']
        else:
            self.name = self.layout_db.location_Activated(name_locatoin_activate)
        return self.name

    def name_Activated(self, name_name_activate):
        if name_name_activate == ' ':
            self.code = [' ']
        else:
            self.code = self.layout_db.name_Activated(name_name_activate)
        return self.code

    def Auto_SelectTT(self):
        self.layout_db.Auto_SelectTT(self.width_layout, self.height_layout)
        autoselect_result = self.layout_db.result
        return autoselect_result

    def Auto_SelectTT_warning(self):
        autoselect_result_one_percent = self.layout_db.result_one_percent
        return autoselect_result_one_percent

    def CheckLayOut_func(self):
        self.width_layout = round(self.image.size[0] / self.resolution * 25.4)
        self.height_layout = round(self.image.size[1] / self.resolution * 25.4)

        all_TT_Value = self.layout_db.CheckLayOut_func_sql()

        self.dpi = all_TT_Value[3]
        self.dis_x = all_TT_Value[4]
        self.dis_y = all_TT_Value[5]
        self.vip_top = all_TT_Value[8]
        self.vip_left = all_TT_Value[9]
        self.vip_bottom = all_TT_Value[10]
        self.vip_right = all_TT_Value[11]
        unprint_top = all_TT_Value[14]
        unprint_left = all_TT_Value[15]
        unprint_bottom = all_TT_Value[16]
        unprint_right = all_TT_Value[17]
        frame = all_TT_Value[18]
        self.comment = all_TT_Value[23]

        if self.width_layout == self.dis_x and self.height_layout == self.dis_y:
            self.CheckResult = 'Ширина и высота по ТТ ОК'
        elif self.width_layout != self.dis_x and self.height_layout == self.dis_y:
            self.CheckResult = 'Ширина не по ТТ, а высота по ТТ ОК'
        elif self.width_layout == self.dis_x and self.height_layout != self.dis_y:
            self.CheckResult = 'Ширина по ТТ ОК, а высота не по ТТ'
        else:
            self.CheckResult = 'Ширина и высота не по ТТ'
        if self.resolution >= self.dpi - 4:
            self.CheckResult_DPI = 'Разрешение по ТТ ОК'
        else:
            self.CheckResult_DPI = 'Разрешение не по ТТ'
        if self.image.mode == 'CMYK':
            self.CheckResult_mode = 'Цветовой режим CMYK OK'
        else:
            self.CheckResult_mode = 'Цветовой режим не CMYK!!!'

        if self.image.info.get('icc_profile', ''):
            if ImageCms.getProfileName(io.BytesIO(self.image.info.get('icc_profile', ''))) == ImageCms.getProfileName(
                    euroscale_profile):
                self.CheckResult_ICC = 'Цветовой профиль Euroscale Coated v2 ОК'
            else:
                self.CheckResult_ICC = 'Цветовой профиль не Euroscale Coated v2'

            if self.width_layout == self.dis_x and self.height_layout == self.dis_y and self.image.mode == 'CMYK':
                self.unprint_and_frame(unprint_top, unprint_left, unprint_bottom, unprint_right, frame)
        else:
            self.CheckResult_ICC = 'Цветовой профиль не Euroscale Coated v2'

    def FitDimensions(self):
        self.width_layout = round(self.image.size[0] / self.resolution * 25.4)
        self.height_layout = round(self.image.size[1] / self.resolution * 25.4)
        proportion = self.width_layout / self.height_layout
        if self.dis_y * proportion > self.dis_x:
            self.width_layout = self.dis_y * proportion
            self.height_layout = self.dis_y
            resized = self.image.resize(
                (round(self.mm_to_pix(self.width_layout)), round(self.mm_to_pix(self.height_layout))), 3)
            left = (round(self.mm_to_pix(self.width_layout)) - self.mm_to_pix(self.dis_x)) / 2
            up = 0
            right = (round(self.mm_to_pix(self.width_layout)) -
                     self.mm_to_pix(self.dis_x)) / 2 + self.mm_to_pix(self.dis_x)
            bottom = round(self.mm_to_pix(self.height_layout))
            croped = resized.crop((left, up, right, bottom))
            self.image = croped
        else:
            self.width_layout = self.dis_x
            self.height_layout = self.width_layout / proportion
            resized = self.image.resize(
                (round(self.mm_to_pix(self.width_layout)), round(self.mm_to_pix(self.height_layout))), 3)
            left = 0
            up = (round(self.mm_to_pix(self.height_layout)) - self.mm_to_pix(self.dis_y)) / 2
            right = round(self.mm_to_pix(self.width_layout))
            bottom = (round(self.mm_to_pix(self.height_layout)) -
                      self.mm_to_pix(self.dis_y)) / 2 + self.mm_to_pix(self.dis_y)
            croped = resized.crop((left, up, right, bottom))
            self.image = croped

    def mm_to_pix(self, mm):
        pix_result = mm / 25.4 * self.resolution
        return pix_result

    def make_VIP_zone(self):
        vip_zone_image = self.image.copy()
        draw_vip_zone = ImageDraw.Draw(vip_zone_image)
        pixVIP_top = self.vip_top / 25.4 * self.resolution
        pixVIP_right = self.vip_right / 25.4 * self.resolution
        pixVIP_left = self.vip_left / 25.4 * self.resolution
        pixVIP_bottom = self.vip_bottom / 25.4 * self.resolution
        draw_vip_zone.line([(pixVIP_left, pixVIP_top), (self.image.size[0] - pixVIP_right, pixVIP_top),
                            (self.image.size[0] - pixVIP_right, self.image.size[1] - pixVIP_bottom),
                            (pixVIP_left, self.image.size[1] - pixVIP_bottom), (pixVIP_left, pixVIP_top)],
                           fill=(0, 0, 0, 0), width=13)
        draw_vip_zone.line([(pixVIP_left, pixVIP_top), (self.image.size[0] - pixVIP_right, pixVIP_top),
                            (self.image.size[0] - pixVIP_right, self.image.size[1] - pixVIP_bottom),
                            (pixVIP_left, self.image.size[1] - pixVIP_bottom), (pixVIP_left, pixVIP_top)],
                           fill=(255, 0, 255, 0), width=9)
        font = ImageFont.truetype('font/impact.ttf', 300)
        draw_vip_zone.text((self.image.size[0] / 10, self.image.size[1] / 8),
                           'Зона значимых элементов',
                           font=font, fill=(255, 0, 255, 0))
        self.make_prw('temp/vip_temp.png', image=vip_zone_image)

    def unprint_and_frame(self, unprint_top, unprint_left, unprint_bottom, unprint_right, frame):
        draw = ImageDraw.Draw(self.image)
        if unprint_top or unprint_left or unprint_bottom or unprint_right is not None or 0:
            f = (0, 0, 0, 0)
            pixUNPRINT_top = self.mm_to_pix(unprint_top)
            pixUNPRINT_left = self.mm_to_pix(unprint_left)
            pixUNPRINT_right = self.mm_to_pix(unprint_right)
            pixUNPRINT_bottom = self.mm_to_pix(unprint_bottom)
            draw.rectangle(((0, 0), (pixUNPRINT_left, self.image.size[1])), fill=f)
            draw.rectangle(((self.image.size[0] - pixUNPRINT_right, 0),
                            (self.image.size[0], self.image.size[1])), fill=f)
            draw.rectangle(((pixUNPRINT_left, 0), (self.image.size[0] - pixUNPRINT_right, pixUNPRINT_top)), fill=f)
            draw.rectangle(((pixUNPRINT_left, self.image.size[1] - pixUNPRINT_bottom),
                            (self.image.size[0] - pixUNPRINT_right, self.image.size[1])), fill=f)
            draw.line([(pixUNPRINT_left, pixUNPRINT_top), (self.image.size[0] - pixUNPRINT_right, pixUNPRINT_top),
                       (self.image.size[0] - pixUNPRINT_right, self.image.size[1] - pixUNPRINT_bottom),
                       (pixUNPRINT_left, self.image.size[1] - pixUNPRINT_bottom),
                       (pixUNPRINT_left, pixUNPRINT_top)], fill=(80, 80, 80, 80), width=1)
            self.prw_name = 'temp/convert_ICC_temp.png'
        elif frame is not None or 0:
            fn_frame = 'frames/' + frame + '.tif'
            fn_frame_mask = 'frames/' + frame + '_mask.tif'
            im_frame = Image.open(fn_frame)
            im_frame_resized = im_frame.resize((self.image.size[0], self.image.size[1]), 3)
            im_frame_mask = Image.open(fn_frame_mask).convert('L')
            im_frame_mask_resized = im_frame_mask.resize((self.image.size[0], self.image.size[1]), 3)
            framed = Image.composite(self.image, im_frame_resized, im_frame_mask_resized)
            self.image.paste(framed)
            self.prw_name = 'temp/convert_ICC_temp.png'
        else:
            self.prw_name = 'temp/input_temp.png'

        # контур в 1 пиксель по краю макета
        draw.line([(0, 0), (self.image.size[0] - 1, 0), (self.image.size[0] - 1, self.image.size[1] - 1),
                   (0, self.image.size[1] - 1), (0, 0)], fill=(80, 80, 80, 80), width=1)
        self.make_prw(self.prw_name)

    def ConvertMode_and_Icc(self, prof=euroscale_profile):
        conv_mode_profile = ImageCms.ImageCmsProfile(io.BytesIO(prof.tobytes()))
        im_mode_profile = ImageCms.ImageCmsProfile(io.BytesIO(self.image.info.get('icc_profile', '')))
        self.image = ImageCms.profileToProfile(self.image, im_mode_profile, conv_mode_profile, 0, 'CMYK')
        self.prw_name = 'temp/convert_ICC_temp.png'
        self.make_prw(self.prw_name)

    def Assign_Icc(self, prof=euroscale_profile):
        conv_mode_profile = prof.tobytes()
        tr = Image.fromarray(numpy.array(self.image), mode='CMYK')
        image_tag_directory[317] = 2
        image_tag_directory[34675] = conv_mode_profile
        tr.save("temp/temp.tif", tiffinfo=image_tag_directory, compression='tiff_lzw',
                resolution_unit=self.unit_resolution,
                x_resolution=self.resolution, y_resolution=self.resolution)
        self.image = Image.open("temp/temp.tif")
        self.prw_name = 'temp/convert_ICC_temp.png'
        self.make_prw(self.prw_name)

    def makeFolder(self, name_folder, name_suget=''):
        self.folderMaked = True
        fol = 'D:/LayOutQC/' + name_folder + '/'
        date_fol = str(datetime.date.today()).replace('-', '.')
        home_folder = os.listdir('D:/LayOutQC/')
        if not name_folder in home_folder:
            os.mkdir(fol)
            home_folder_folder = os.listdir(fol)
            if not date_fol in home_folder_folder:
                os.mkdir('D:/LayOutQC/' + name_folder + '/' + date_fol)
                for folders in ('input', 'preview', 'print', 'cp'):
                    os.mkdir('D:/LayOutQC/' + name_folder + '/' + date_fol + '/' + folders + '/')
        else:
            home_folder_folder = os.listdir(fol)
            if not date_fol in home_folder_folder:
                os.mkdir('D:/LayOutQC/' + name_folder + '/' + date_fol)
                for folders in ('input', 'preview', 'print', 'cp'):
                    os.mkdir('D:/LayOutQC/' + name_folder + '/' + date_fol + '/' + folders + '/')
        self.path = ('D:/LayOutQC/' + name_folder + '/' + date_fol)
        print(self.path)

    def makeSignature(self):
        sign_desm = ''
        if str(self.width_layout / 1000)[-1] == '0':
            sign_w = int(self.width_layout / 1000)
        else:
            sign_w = round(self.width_layout / 1000, 4)
        if str(self.height_layout / 1000)[-1] == '0':
            sign_h = int(self.height_layout / 1000)
        else:
            sign_h = round(self.height_layout / 1000, 4)

        sign_formats = (301, 214, 'A4h+2mm'), (214, 301, 'A4v+2mm'), (297, 210, 'A4h'), (210, 297, 'A4v'), (
            424, 301, 'A3h+2mm'), (301, 424, 'A3v+2mm'), (420, 297, 'A3h'), (297, 420, 'A3v'), (598, 424, 'A2h+2mm'), (
                           424, 598, 'A2v+2mm'), (594, 420, 'A2h'), (420, 594, 'A2v')
        for formats in sign_formats:
            if self.width_layout == formats[0] and self.height_layout == formats[1]:
                sign_desm = formats[2]
                break
            else:
                sign_desm = str(str(sign_w) + 'x' + str(sign_h) + 'm')
        add_signature = '_' + str(datetime.date.today()).replace('-', '') + '_' + sign_desm + '_' + str(
            round(self.width_layout * self.height_layout / 1000000, 3)) + 'm2_'
        return add_signature

    def makeComment(self):
        comment = ''
        if self.comment:
            comment = self.comment
        return comment

    def saveLayout(self, FileName, loaded, pathLoaded):
        prwSaveName = ''
        prw_vip_SaveName = ''
        if self.folderMaked:
            finSaveName = self.path + '/print/' + FileName + '_FRA.tif'
            prwSaveName = self.path + '/preview/' + FileName + '_FRA.png'
            prw_vip_SaveName = self.path + '/preview/' + FileName + '_FRA_важные_элементы.png'
        else:
            finSaveName = pathLoaded + FileName + '.tif'
        tr = Image.fromarray(numpy.array(self.image), mode='CMYK')
        image_tag_directory[317] = 2
        if self.image.info.get('icc_profile', ''):
            image_tag_directory[34675] = self.image.info.get('icc_profile', '')
        tr.save(finSaveName, tiffinfo=image_tag_directory, compression='tiff_lzw',
                resolution_unit=self.unit_resolution,
                x_resolution=self.resolution, y_resolution=self.resolution)
        if self.folderMaked:
            if os.path.exists('temp/convert_ICC_temp.png'):
                pr = Image.open('temp/convert_ICC_temp.png')
            else:
                pr = Image.open('temp/input_temp.png')

            if self.image.size[0] >= self.image.size[1]:
                x = 2000
                y = round(x / (self.image.size[0] / self.image.size[1]))
            else:
                y = 2000
                x = round(y / (self.image.size[0] / self.image.size[1]))
            pr_res = pr.resize((x, y))
            pr_res.save(prwSaveName, quality=80, )
            if os.path.exists('temp/vip_temp.png'):
                pr_vip = Image.open('temp/vip_temp.png')
                pr_res = pr_vip.resize((x, y))
                pr_res.save(prw_vip_SaveName, quality=80, )
            os.rename(loaded, self.path + '/input/' + loaded.split("/")[-1])

    def _DEBAG(self, LayoutQC_DEBAG=False):
        if LayoutQC_DEBAG:
            if self.image.info.get('icc_profile', ''):
                profile_print = ImageCms.getProfileName(io.BytesIO(self.image.info.get('icc_profile', '')))
            else:
                profile_print = "Untagged CMYK (8bpc)"
            print("Mode: " + self.image.mode + "\n" +
                  "Compression: " + self.compression + "\n" +
                  "Resolution: " + str(self.resolution) + "\n" +
                  "Unit resolution: " + self.unit_resolution + "\n" +
                  "Icc Profile: " + profile_print + "\n" +
                  "Size: " + str(self.image.size[0]) + " x " + str(self.image.size[1]) + " pix" + "\n" +
                  "Dismentions: " + str(self.width_layout) + " x " + str(self.height_layout) + 'mm')
