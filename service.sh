#!/bin/bash

/bin/su -c "cd /home/pi/Project/eDashboard && python3 -m pipenv run python edashboard.py" - pi
