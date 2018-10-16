import datetime
import glob
import json
import os
import random
import sys
import urllib
import uuid

from kivy.app import App
from kivy.clock import Clock, mainthread
# from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.garden.mapview import MapMarkerPopup, MapView
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.properties import (BooleanProperty, NumericProperty, ObjectProperty,
                             StringProperty)
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from plyer import gps

from mapview.clustered_marker_layer import ClusteredMarkerLayer
from mapview.view import MapMarker

from PIL import Image, ImageDraw, ImageFont

# kivy.require('1.10.1')

# LabelBase.register(DEFAULT_FONT, os.path.join(
#     os.path.dirname(os.path.abspath(__file__)), "FreeMono.ttf"))

class GpsApp(App):
    # UUID = str(uuid.uuid3(uuid.NAMESPACE_DNS, str(uuid.getnode())))
    ID_FILE = "id.txt"
    AP_DIR = os.path.dirname(os.path.abspath(__file__))
    CARD = os.path.join(AP_DIR, 'comment.png')
    # FONT = ImageFont.truetype(os.path.join(AP_DIR, "NotoMono-Regular.ttf"), 12)
    try:
        FONT = ImageFont.truetype("/system/fonts/Roboto-Regular.ttf", 12)
    except IOError:
        FONT = ImageFont.load_default()
        FONT.size = 12
    CARD_IMG = Image.open(CARD)
    JPN_IMG = Image.open(os.path.join(AP_DIR, 'flag093_mini.png'))
    USA_IMG = Image.open(os.path.join(AP_DIR, 'flag198_mini.png'))
    CHI_IMG = Image.open(os.path.join(AP_DIR, 'flag039_mini.png'))
    KOR_IMG = Image.open(os.path.join(AP_DIR, 'flag099_mini.png'))

    latitude = StringProperty()
    longitude = StringProperty()
    # map_view = ObjectProperty(MapView)

    lat = NumericProperty()
    lon = NumericProperty()

    gps_status = StringProperty('booting')
    name_input_text = StringProperty('')
    comment_input_text = StringProperty('')
    male_check_status = StringProperty('normal')
    female_check_status = StringProperty('normal')
    japanese_check_status = BooleanProperty(False)
    english_check_status = BooleanProperty(False)
    chinese_check_status = BooleanProperty(False)
    korean_check_status = BooleanProperty(False)

    my_marker = None
    get_result = None
    layer = None

    def build(self):
        self.rest_get()
        id_file_path = os.path.join(self.AP_DIR, self.ID_FILE)
        if os.path.isfile(id_file_path):
            with open(id_file_path, 'r') as f:
                self.UUID = f.read()
        else:
            self.UUID = str(uuid.uuid4())
            with open(id_file_path, 'w') as f:
                f.write(self.UUID)

        try:
            gps.configure(on_location=self.on_location,
                          on_status=self.on_status)
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            self.gps_status = 'GPS is not implemented for your platform'
        self.start()

        for p in self.get_result:
            if self.UUID == p['uuid']:
               print('match! name -> {}'.format(p['name']))
               self.name_input_text = p['name']
               self.male_ckeck_status = 'down' if p['male_status'] == True else 'normal'
               self.female_check_status = 'down' if p['female_status'] == True else 'normal'
               self.japanese_check_status = p['japanese_status']
               self.english_check_status = p['english_status']
               self.chinese_check_status = p['chinese_status']
               self.korean_check_status = p['korean_status']
               self.comment_input_text = p['comment']

        return Builder.load_file('gps.kv')

    def start(self, minTime=1000, minDistance=0):
        try:
            gps.start(minTime, minDistance)
        except NotImplementedError:
            self.gps_status = 'GPS is not implemented for your platform'

    def stop(self):
        gps.stop()

    @mainthread
    def on_location(self, **kwargs):
        self.longitude = str(kwargs['lon'])
        self.latitude = str(kwargs['lat'])

        self.lon = float('{:.6f}'.format(kwargs['lon']))
        self.lat = float('{:.6f}'.format(kwargs['lat']))
        # self.root.map_view.center_on(self.lat, self.lon)
        # if self.my_marker is not None:
        #     self.root.map_view.remove_marker(self.my_marker)
        # self.my_marker = MapMarkerPopup(lon=self.lon, lat=self.lat)
        # self.root.map_view.add_marker(self.my_marker)
        # self.gps_status = 'lat: {}, lon: {}'.format(self.latitude, self.longitude)

    @mainthread
    def on_status(self, stype, status):
        self.gps_status = 'type={}\n{}'.format(stype, status)

    def on_pause(self):
        gps.stop()
        return True

    def on_resume(self):
        gps.start(1000, 0)

    # *** lat lon driver ***
    # def get_gps_latitude(self):
    #     self.lat = round(random.uniform(35.000000, 39.000000), 6)
    #     self.latitude = str(self.lat)
    #     return self.latitude # rounding

    # def get_gps_longitude(self):
    #     self.lon = round(random.uniform(135.000000, 139.000000), 6)
    #     self.longitude = str(self.lon)
    #     return self.longitude

    # def update(self, _):
    #     self.latitude = self.get_gps_latitude()
    #     self.longitude = self.get_gps_longitude()

    #     # print(f"lat={self.lat} lon={self.lon}")
    #     self.root.map_view.center_on(self.lat, self.lon)
    #     if self.my_marker is not None:
    #         self.root.map_view.remove_marker(self.my_marker)
    #     self.my_marker = MapMarkerPopup(lon=self.lon, lat=self.lat)
    #     self.root.map_view.add_marker(self.my_marker)
        
    # def on_start(self):
    #     Clock.schedule_interval(self.update, 5)

    # REST_API
    def rest_success(self, req, result):
        print('success')

    def rest_fail(self, req, result):
        print(result)
        print('fail')

    def rest_error(self, req, result):
        print('error')

    def rest_progress(self, req, result, chunk):
        print('loading')
        # self.set_status('loading')

    def rest_get(self):
        # values = {'name':'hoge',}
        # converted data to json type
        # params = json.dumps(values)

        headers = {'Content-type': 'application/json',
                'Accept': 'application/json'}

        req = UrlRequest('https://morning-plateau-62909.herokuapp.com/api/positions/',
                        on_success=self.rest_success, on_failure=self.rest_fail,
                        on_error=self.rest_error, on_progress=self.rest_progress,
                        req_headers=headers, method='GET', timeout=30)
        req.wait()

        print(req.result)

        self.get_result = req.result

        # layer = ClusteredMarkerLayer()
        # for p in req.result:
        #     lon = float(p['longitude'])
        #     lat = float(p['latitude'])
        #     layer.add_marker(lon=lon, lat=lat, cls=MyMapMarker)

        # layer.add_marker(lat=self.lat, lon=self.lon)

        # self.root.map_view.add_widget(layer)
        # self.root.map_view.center_on(self.lat, self.lon)
        # self.set_status(str(req.result))


    def rest_post(self):
        print('post')
        values = {'uuid': self.UUID,
                  'name': self.root.name_input_text,
                  'latitude': self.lat,
                  'longitude': self.lon,
                  'male_status': False if self.root.male_check_status == 'normal' else True,
                  'female_status': False if self.root.female_check_status == 'normal' else True,
                  'japanese_status': self.root.japanese_check_status,
                  'english_status': self.root.english_check_status,
                  'chinese_status': self.root.chinese_check_status,
                  'korean_status': self.root.korean_check_status,
                  'comment': self.root.comment_input_text,
                  'update': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        params = json.dumps(values)

        headers = {'Content-type': 'application/json',
                'Accept': 'application/json'}

        req = UrlRequest('https://morning-plateau-62909.herokuapp.com/api/positions/',
                        on_success=self.rest_success, on_failure=self.rest_fail,
                        on_error=self.rest_error, on_progress=self.rest_progress,
                        req_headers=headers, req_body=params, method='POST', timeout=30)
        req.wait()

        print(req.result)
        
        self.gps_status = str(req.result)

    def rest_put(self):
        print('put')
        values = {'uuid': self.UUID,
                  'name': self.root.name_input_text,
                  'latitude': self.lat,
                  'longitude': self.lon,
                  'male_status': False if self.root.male_check_status == 'normal' else True,
                  'female_status': False if self.root.female_check_status == 'normal' else True,
                  'japanese_status': self.root.japanese_check_status,
                  'english_status': self.root.english_check_status,
                  'chinese_status': self.root.chinese_check_status,
                  'korean_status': self.root.korean_check_status,
                  'comment': self.root.comment_input_text,
                  'update': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        params = json.dumps(values)

        headers = {'Content-type': 'application/json',
                'Accept': 'application/json'}

        req = UrlRequest('https://morning-plateau-62909.herokuapp.com/api/positions/{}/'.format(self.UUID),
                        on_success=self.rest_success, on_failure=self.rest_fail,
                        on_error=self.rest_error, on_progress=self.rest_progress,
                        req_headers=headers, req_body=params, method='PUT', timeout=30)
        req.wait()

        print(req.result)
        self.gps_status = str(req.result)

    def put_marker(self):
        [os.remove(f) for f in glob.glob('tmp_*.png')]
        self.rest_get()
        if self.layer is not None:
            self.root.map_view.remove_layer(self.layer)
        self.layer = ClusteredMarkerLayer()
        for i, p in enumerate(self.get_result):
            lon = float(p['longitude'])
            lat = float(p['latitude'])
            if not p['uuid'] == self.UUID:
                tmp_img = self.CARD_IMG.copy()
                if p['japanese_status']:
                    tmp_img.paste(self.JPN_IMG, (4, 5))
                if p['english_status']:
                    tmp_img.paste(self.USA_IMG, (22, 5))
                if p['chinese_status']:
                    tmp_img.paste(self.CHI_IMG, (40, 5))
                if p['korean_status']:
                    tmp_img.paste(self.KOR_IMG, (58, 5))

                draw = ImageDraw.Draw(tmp_img)
                # comment = p['comment'] if len(p['comment']) < 11 else p['comment'][:10] + "\n" + p['comment'][10:]
                # draw.text((4, 17), '{}\n{}'.format(p['name'], comment),
                #           fill=(0, 0, 0), font=self.FONT)
                draw.text((4, 17), p['name'], fill=(0, 0, 0), font=self.FONT)
                draw.text((4, 29), p['comment'][:10], fill=(0, 0, 0), font=self.FONT)
                draw.text((4, 41), p['comment'][10:], fill=(0, 0, 0), font=self.FONT)
                tmp_png = os.path.join(self.AP_DIR, "tmp_{}.png".format(i))
                tmp_img.save(tmp_png)

                # self.layer.add_marker(lon=lon, lat=lat, cls=MyMapMarker)
                cls = type("MyMapMarker_{}".format(i), (MapMarker,), {"source": tmp_png})
                self.layer.add_marker(lon=lon, lat=lat, cls=cls)

        self.layer.add_marker(lat=self.lat, lon=self.lon)

        self.root.map_view.add_widget(self.layer)
        self.root.map_view.center_on(self.lat, self.lon)

    def rest_update(self):
        # self.rest_get()
        for p in self.get_result:
            if p['uuid'] == self.UUID:
                self.rest_put()
                break
        else:
            self.rest_post()
       
    def set_status(self, s=''):
        self.gps_status = s
    
    def name_print(self):
        print('text: {}, male_status: {}, female_status: {}, japanese: {}'
            .format(self.root.name_input_text,
                self.root.male_check_status,
                self.root.female_check_status,
                self.root.japanese_check_status))


class MyMapMarker(MapMarker):
    source = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'blue_marker.png')

# class MyMapMarker(MapMarker):
#     def __init__(self, source=os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'blue_marker.png'),
#                  *args, **kwargs):
#         super().__init__(source, *args, **kwargs)


if __name__ == '__main__':
    GpsApp().run()
