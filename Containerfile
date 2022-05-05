FROM python:3
ADD app.py /
ADD constring.py /
ADD assets /
ADD grColor_hist.png /
ADD lcamp_hist.png /
ADD obs_hist.png /
ADD lc_hist.png /
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
CMD [ "python3", "app.py" ]
