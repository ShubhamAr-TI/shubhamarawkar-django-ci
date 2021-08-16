FROM python:3
ENV PYTHONUNBUFFERED=1 
WORKDIR /code 
COPY requirements.txt /code/ 
RUN pip3 install -r requirements.txt
COPY . /code/
# RUN rm /code/db.sqlite3
RUN python3 manage.py makemigrations
RUN python3 manage.py migrate
CMD sh entrypoint.sh