FROM oven/bun:1

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .

EXPOSE 5173

# Modo dev de Vite: suficiente para el demo del hackatón, sin pelear con
# el target de build (nitro/cloudflare) que usa Lovable para producción.
CMD ["bun", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
