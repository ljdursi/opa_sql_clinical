FROM python:3
LABEL Maintainer "CanDIG Project"

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt
RUN python setup.py install

EXPOSE 5000

# Run the model service server
# provide some explicit defaults if no arugments are given
ENTRYPOINT [ "analytics_service", "--port", "5000"]
CMD [ "--logfile", "analytics_service.log" ]
