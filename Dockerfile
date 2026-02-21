# Step 1: Use an official Python image
FROM python:3.12-slim

# Step 2: Set the working directory
WORKDIR /app

# Step 3: Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 4: Create the 'static' directory and set proper permissions
RUN mkdir -p /app/static && chmod -R 777 /app/static

# Step 5: Copy the rest of the application
COPY . .

# Step 6: Expose port
EXPOSE 8080

# Step 7: Run the application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
