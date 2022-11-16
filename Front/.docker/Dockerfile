FROM node:16.17-buster-slim

ENV CONTAINER_PATH /opt/alloxentric
ENV NODE_OPTIONS --max_old_space_size=4096

WORKDIR /opt/alloxentric

COPY ./package*.json .
RUN npm install

COPY . .
EXPOSE 8000

CMD [ "npm", "run", "serve" ]
#CMD [ "sleep", "infinity" ]