FROM python:3.8-slim

WORKDIR /app

# Copy shared package files
COPY . .

# Install the shared package
RUN pip install .

# Create a simple health check
RUN echo '#!/bin/bash\necho "Shared package installed successfully"' > /healthcheck.sh && \
    chmod +x /healthcheck.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /healthcheck.sh

# This image is meant to be used as a base for other services
# or for testing the shared package
CMD ["python", "-c", "import stock_portfolio_shared; print('Shared package ready')"] 