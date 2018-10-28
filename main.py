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
from kivy.garden.mapview import MapMarkerPopup, MapView
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.properties import (BooleanProperty, NumericProperty, ObjectProperty,
                             StringProperty)
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from plyer import gps

from mapview.clustered_marker_layer import ClusteredMarkerLayer
from mapview.view import MapMarker

from PIL import Image, ImageDraw, ImageFont

# kivy.require('1.10.1')

REST_URL = 'https://morning-plateau-62909.herokuapp.com/api/positions/'
REST_HEADER = {'Content-type': 'application/json', 'Accept': 'application/json'}

class GpsApp(App):
    ID_FILE = "id.txt"
    AP_DIR = os.path.dirname(os.path.abspath(__file__))
    CARD = os.path.join(AP_DIR, 'comment.png')
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

    lat = NumericProperty()
    lon = NumericProperty()

    gps_status = StringProperty('booting')
    name_input_text = StringProperty('')
    comment_input_text = StringProperty('')
    let_help_check_status = StringProperty('normal')
    need_help_check_status = StringProperty('down')
    male_check_status = StringProperty('normal')
    female_check_status = StringProperty('normal')
    japanese_check_status = BooleanProperty(False)
    english_check_status = BooleanProperty(False)
    chinese_check_status = BooleanProperty(False)
    korean_check_status = BooleanProperty(False)

    male_search_status = StringProperty('normal')
    female_search_status = StringProperty('normal')
    japanese_search_status = BooleanProperty(True)
    english_search_status = BooleanProperty(True)
    chinese_search_status = BooleanProperty(True)
    korean_search_status = BooleanProperty(True)
    update_interval = NumericProperty(60)
    update_interval_label = StringProperty('60')

    my_marker = None
    get_result = None
    layer = None

    def build(self):
        self.title = "VSA"
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
            self.lat = 35.653437
            self.lon = 139.762607
            Clock.schedule_once(self.my_callback, 1)
            self.interval_callback = Clock.schedule_interval(self.my_callback, self.update_interval)
        self.start(minTime=self.update_interval * 1000)

        self.rest_get()
        for p in self.get_result:
            if self.UUID == p['uuid']:
               print('match! name -> {}'.format(p['name']))
               if p['need_help'] == True:
                   self.let_help_check_status = 'normal'
                   self.need_help_check_status = 'down'
               else:
                   self.let_help_check_status = 'down'
                   self.need_help_check_status = 'normal'
               self.name_input_text = p['name']
               self.male_check_status = 'down' if p['male_status'] == True else 'normal'
               self.female_check_status = 'down' if p['female_status'] == True else 'normal'
               self.japanese_check_status = p['japanese_status']
               self.english_check_status = p['english_status']
               self.chinese_check_status = p['chinese_status']
               self.korean_check_status = p['korean_status']
               self.comment_input_text = p['comment']
               break
        else:
            self.name_input_text = self.UUID[:8]

        return Builder.load_file('gps.kv')

    def my_callback(self, dt):
        # self.put_marker()
        self.name_check()

    def start(self, minTime=10000, minDistance=0):
        try:
            gps.start(minTime, minDistance)
        except NotImplementedError:
            self.gps_status = 'GPS is not implemented for your platform'

    def stop(self):
        try:
            gps.stop()
        except NotImplementedError:
            self.gps_status = 'GPS is not implemented for your platform'

    @mainthread
    def on_location(self, **kwargs):
        self.longitude = str(kwargs['lon'])
        self.latitude = str(kwargs['lat'])

        self.lon = float('{:.6f}'.format(kwargs['lon']))
        self.lat = float('{:.6f}'.format(kwargs['lat']))
        self.name_check()

    @mainthread
    def on_status(self, stype, status):
        self.gps_status = 'type={}\n{}'.format(stype, status)

    def on_pause(self):
        gps.stop()
        return True

    def on_resume(self):
        gps.start(self.update_interval, 0)

    # REST_API
    def rest_success(self, req, result):
        print('success')

    def rest_fail(self, req, result):
        print('fail')

    def rest_error(self, req, result):
        print('error')

    def rest_progress(self, req, result, chunk):
        print('loading')

    def rest_get(self):

        req = UrlRequest(REST_URL,
                        on_success=self.rest_success, on_failure=self.rest_fail,
                        on_error=self.rest_error, on_progress=self.rest_progress,
                        req_headers=REST_HEADER, method='GET', timeout=30)
        req.wait()

        print(req.result)

        self.get_result = req.result

    def rest_post(self):
        print('post')
        values = {'uuid': self.UUID,
                  'need_help': False if self.root.need_help_check_status == 'normal' else True,
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

        req = UrlRequest(REST_URL,
                        on_success=self.rest_success, on_failure=self.rest_fail,
                        on_error=self.rest_error, on_progress=self.rest_progress,
                        req_headers=REST_HEADER, req_body=params, method='POST', timeout=30)
        req.wait()

        print(req.result)
        
        self.gps_status = str(req.result)

    def rest_put(self):
        print('put')
        values = {'uuid': self.UUID,
                  'need_help': False if self.root.need_help_check_status == 'normal' else True,
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

        req = UrlRequest('{}{}/'.format(REST_URL, self.UUID),
                        on_success=self.rest_success, on_failure=self.rest_fail,
                        on_error=self.rest_error, on_progress=self.rest_progress,
                        req_headers=REST_HEADER, req_body=params, method='PUT', timeout=30)
        req.wait()

        print(req.result)
        self.gps_status = str(req.result)

    def put_marker(self):
        [os.remove(f) for f in glob.glob('tmp_*.png')]
        help_flg = True if self.root.need_help_check_status == 'down' else False
        self.rest_get()
        search_set = set()
        if self.root.japanese_search_status:
            search_set.add('J')
        if self.root.english_search_status:
            search_set.add('E')
        if self.root.chinese_search_status:
            search_set.add('C')
        if self.root.korean_search_status:
            search_set.add('K')
        
        if self.layer is not None:
            self.root.map_view.remove_layer(self.layer)
        self.layer = ClusteredMarkerLayer()
        for i, p in enumerate(self.get_result):
            lon = float(p['longitude'])
            lat = float(p['latitude'])
            if (help_flg == p['need_help']) and (not self.UUID == p['uuid']):
                if self.root.male_search_status == 'down':
                    if not p['male_status'] == True:
                        continue
                if self.root.female_search_status == 'down':
                    if not p['female_status'] == True:
                        continue
                target_set = set()
                if p['japanese_status']:
                    target_set.add('J')
                if p['english_status']:
                    target_set.add('E')
                if p['chinese_status']:
                    target_set.add('C')
                if p['korean_status']:
                    target_set.add('K')
                print(i, search_set, target_set)
                if len(search_set & target_set) == 0:
                    continue

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
                draw.text((4, 17), p['name'], fill=(0, 0, 0), font=self.FONT)
                draw.text((4, 29), p['comment'][:10], fill=(0, 0, 0), font=self.FONT)
                draw.text((4, 41), p['comment'][10:], fill=(0, 0, 0), font=self.FONT)
                tmp_png = os.path.join(self.AP_DIR, "tmp_{}.png".format(i))
                tmp_img.save(tmp_png)

                cls = type("MyMapMarker_{}".format(i), (MapMarker,), {"source": tmp_png})
                self.layer.add_marker(lon=lon, lat=lat, cls=cls)

        self.layer.add_marker(lat=self.lat, lon=self.lon)

        self.root.map_view.add_widget(self.layer)
        self.root.map_view.trigger_update(True)

    def current_place(self):
        self.root.map_view.center_on(self.lat, self.lon)

    def name_check(self):
        if not self.root.name_input_text:
            popup = Popup(title='WARN',
                        content=Label(text='name must input'),
                        size_hint=(None, None), size=(400, 400))

            popup.open()
        else:
            self.rest_update()
            self.put_marker()
            self.switch_map_tab()

    def rest_update(self):
        # self.rest_get()
        if self.root.name_input_text:
            if not self.root.comment_input_text:
                self.root.comment_input_text = "None"
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

    def change_interval(self):
        try:
            gps.stop()
            gps.start(minTime=self.update_interval * 1000)
        except NotImplementedError:
            self.gps_status = 'GPS is not implemented for your platform'
            print('exception interval -> {}'.format(self.root.interval_slider.value))
            self.interval_callback.cancel()
            Clock.schedule_once(self.my_callback, 0)
            self.interval_callback = Clock.schedule_interval(self.my_callback,
                                                             self.root.interval_slider.value)

    def switch_map_tab(self):
        self.root.switch_to(self.root.tab_list[len(self.root.tab_list) - 2])


class MyMapMarker(MapMarker):
    source = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'blue_marker.png')


class MyTextInput(TextInput):
    max_charactors = NumericProperty(0)
    def insert_text(self, substring, from_undo=False):
        if len(self.text) > (self.max_characters - 1) and self.max_characters > 0:
            substring = ""
        TextInput.insert_text(self, substring, from_undo)


if __name__ == '__main__':
    GpsApp().run()
