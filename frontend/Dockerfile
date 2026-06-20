FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build Next.js application
RUN npm run build

# Stage 2: Serve the application
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

# Copy necessary files from builder
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Expose NextJS port
EXPOSE 3000

CMD ["npm", "run", "start"]
