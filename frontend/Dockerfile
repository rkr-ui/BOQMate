# Use Node.js 18 Alpine for smaller image
FROM node:18-alpine

# Set work directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Install serve for production
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Start the application
CMD ["serve", "-s", "out", "-l", "3000"]