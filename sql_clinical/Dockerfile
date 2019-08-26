FROM python:3
LABEL Maintainer "CanDIG Project"

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt \
    && python setup.py install

EXPOSE 3000

# Run the model service server
# provide some explicit defaults if no arugments are given
ENTRYPOINT [ "sql_clinical", "--port", "3000"]
CMD [ "--logfile", "clinical_service.log",\
      "--database", "/clinical_service.sqlite" ]
