@echo off
echo ========================================
echo  DynamoDB Agent Server for Electron App
echo ========================================
echo.
echo Starting DynamoDB natural language interface...
echo Your Electron app can now chat with DynamoDB!
echo.
echo Server will be available at: http://localhost:5000
echo Test interface available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python dynamodb_web_server.py

pause