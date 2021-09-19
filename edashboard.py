#!/usr/bin/env python3

##
# edashboard.py - smart clock / system monitor and more
#
# Copyright (C) mgrin<mr6r1n@gmail.com> 2021
#
# Released under the Apache License, Version 2.0
##

import sys
import os

libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib/')
resdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources/')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from datetime import datetime
import time
from waveshare_epd import epd2in13bc
from PIL import Image,ImageDraw,ImageFont
import locale

import requests, json

from dotenv import Dotenv

dotenv = Dotenv(".env")

logging.basicConfig(level=logging.DEBUG)

DATEFORMAT = "%a %x"
TIMEFORMAT = "%H:%M"
FONT = os.path.join(resdir, 'FreeMono.ttf')
FONTBOLD = os.path.join(resdir, 'FreeMonoBold.ttf')

GMAIL_LOGO = Image.open(os.path.join(resdir, 'gmail.png')).convert("RGBA").resize((40, 40))

LAT = dotenv.get('LAT')
LON = dotenv.get('LON')
WB_API_KEY = dotenv.get('WB_API_KEY')
LOCALE = dotenv.get('LOCALE').strip()
WEATHER_REQUEST_INTERVAL = 60 * 15

localeForWeather = LOCALE[:2]

WEATHER_URL = f"http://api.weatherbit.io/v2.0/current?lat={LAT}&lon={LON}&lang={localeForWeather}&key={WB_API_KEY}"
WEATHER_ICONS_URL = f"	https://www.weatherbit.io/static/img/icons"

# WEATHER_MOCK = {
# "rh": 86,
# "pod": "n",
# "lon": 37.57,
# "pres": 996.8,
# "timezone": "Europe/Moscow",
# "ob_time": "2021-09-19 15:32",
# "country_code": "RU",
# "clouds": 100,
# "ts": 1632065561,
# "solar_rad": 0,
# "state_code": "48",
# "city_name": "Leninskiye Gory",
# "wind_spd": 8,
# "wind_cdir_full": "east",
# "wind_cdir": "E",
# "slp": 1018,
# "vis": 2,
# "h_angle": 90,
# "sunset": "15:37",
# "dni": 0,
# "dewpt": 3.8,
# "snow": 0,
# "uv": 0,
# "precip": 1,
# "wind_dir": 100,
# "sunrise": "03:11",
# "ghi": 0,
# "dhi": 0,
# "aqi": 26,
# "lat": 55.7,
# "weather": {
# "icon": "r01n",
# "code": 500,
# "description": "Light rain"
# },
# "datetime": "2021-09-19:15",
# "temp": 6,
# "station": "UUMO",
# "elev_angle": -4.23,
# "app_temp": 1.5
# }
class Fonts:
  def __init__(self, timefont_size, datefont_size, infofont_size, smallfont_size):
    self.timefont = ImageFont.truetype(FONTBOLD, timefont_size)
    self.datefont = ImageFont.truetype(FONTBOLD, datefont_size)
    self.infofont = ImageFont.truetype(FONTBOLD, infofont_size)
    self.smallfont = ImageFont.truetype(FONT, smallfont_size)

class EDashboard:
  epd = None
  fonts = None
  weather = None
  # weather = WEATHER_MOCK
  last_weather_request_timestamp = None

  def __init__(self):
    locale.setlocale(locale.LC_ALL, LOCALE)
    self.fonts = Fonts(timefont_size = 45, datefont_size = 20, infofont_size = 22, smallfont_size=18)    
    self.epd = epd2in13bc.EPD()
    self.epd.init()

  def start(self):
    while True:
      self.draw()
      self.sleep_until_next_min()

  def draw(self):
    BlackImage = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
    RedImage = Image.new('1', (self.epd.height, self.epd.width), 255)  # 298*126  ryimage: red or yellow image 

    BlackDraw = ImageDraw.Draw(BlackImage)
    RedDraw = ImageDraw.Draw(RedImage)

    self.attach_clock_data(BlackDraw)
    self.attach_weather_data(BlackDraw)
    self.attach_emails_data(RedDraw)
    self.epd.display(self.epd.getbuffer(BlackImage), self.epd.getbuffer(RedImage))

  def sleep_until_next_min(self):
    now = datetime.now()
    seconds_until_next_minute = 60 - now.time().second
    time.sleep(seconds_until_next_minute)

  def attach_clock_data(self, draw):
    datetime_now = datetime.now()
    datestring = datetime_now.strftime(DATEFORMAT).capitalize()
    timestring = datetime_now.strftime(TIMEFORMAT)

    draw.text((0, 0), timestring, font = self.fonts.timefont, fill = 0)
    draw.text((4, 43), datestring, font = self.fonts.datefont, fill = 0)

  def attach_weather_data(self, draw):
    shouldRequest = self.last_weather_request_timestamp is None or datetime.now().timestamp() - self.last_weather_request_timestamp > WEATHER_REQUEST_INTERVAL
    # shouldRequest = False

    if shouldRequest:
      response = requests.get(WEATHER_URL)
      data = response.json()
      if 'data' in data:
        self.last_weather_request_timestamp = datetime.now().timestamp()
        self.weather = data['data'][0]

    if self.weather is not None:
      windSpeed = self.weather['wind_spd']
      temperature = self.weather['temp']
      feelsLikeTemperature = self.weather['app_temp']
      humidity = self.weather['rh']
      iconCode = self.weather['weather']['icon']
      description = self.weather['weather']['description']

      draw.line((0, 65, self.epd.height, 65), fill=0)
      draw.text((4, 67), f"{temperature}°({feelsLikeTemperature}°)", font = self.fonts.infofont, fill = 0)
      draw.text((4, self.epd.width - 18), f"Wind: {windSpeed}ms", font = self.fonts.smallfont, fill = 0)

      icon_path = self.get_weather_icon_path(iconCode)
      icon = Image.open(icon_path).convert("RGBA").resize((50, 50))
      draw.bitmap((160, -5), icon, fill=None)

  def attach_emails_data(self, draw):
      draw.bitmap((168, 65), GMAIL_LOGO, fill=None)

  def get_weather_icon_path(self, code):
    icon = os.path.join(resdir, f'weather_icons/{code}.png')

    if not os.path.exists(icon):
      icon_data = requests.get(f"{WEATHER_ICONS_URL}/{code}.png").content
      with open(icon, 'wb') as f:
        f.write(icon_data)

    return icon

if __name__ == '__main__':
  eDashboard = EDashboard()
  eDashboard.start()