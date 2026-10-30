# imagem leve com Node
FROM node:20-alpine

WORKDIR /app

# instala as dependencias primeiro (aproveita o cache do Docker)
COPY package*.json ./
RUN npm install --omit=dev

# copia o resto do codigo
COPY . .

EXPOSE 3000
CMD ["node", "server.js"]
