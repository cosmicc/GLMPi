FROM python:3.7m

ADD glmpi.py /

CMD [ "python", "./my_script.py" ]
