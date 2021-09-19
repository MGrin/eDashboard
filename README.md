# eDashboard

Small script to display a clock / date / weather dashboard on your RPi 2in13bc ePaper screen.

![How it looks like](./Example.jpg?raw=true)

## Dependencies:
* pipenv
* python 3.8

## How to run
* clone this repo
* inside the repo copy `.env.example` to `.env`
* fill all env variables inside the `.env` file:
  * `LAT` is the lattitude of you location
  * `LON` is the longitude of your location
  * `WB_API_KEY` is your [weatherbit.io](weatherbit.io) API key
  * `LOCALE` is the locale you want to see date on your screen
* run `pipenv install`
* run `pipenv run ./edashboard.py`