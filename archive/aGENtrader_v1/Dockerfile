# Build stage
FROM node:20-slim AS builder

# Set working directory
WORKDIR /app

# Copy package files for better layer caching
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:20-slim AS runner

# Set production environment
ENV NODE_ENV=production

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --only=production

# Copy built assets from builder stage - keep all files in their original structure
COPY --from=builder /app/dist ./dist

# Create a non-root user
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 tradingbot \
    && chown -R tradingbot:nodejs /app

# Switch to non-root user
USER tradingbot

# Expose port 5000 (matches server configuration)
EXPOSE 5000

# Start the production server
CMD ["npm", "run", "start"]