FROM python:3
LABEL Maintainer "CanDIG Project"

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt
RUN python setup.py install

EXPOSE 4000

# Run the model service server
# provide some explicit defaults if no arugments are given
ENTRYPOINT [ "clinical_service", "--port", "4000"]
CMD [ "--logfile", "clinical_service.log" ]
