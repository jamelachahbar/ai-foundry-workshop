# FinOpsHubs UI

A web application for the FinOps Expert with Bing Grounding.

## Directory Structure

```
finopshubs-ui/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   └── finops.py  # API routes for FinOps Expert
│   │   └── main.py        # FastAPI app
│   ├── finops_expert_with_bing_grounding.py  # FinOps Expert module
│   ├── requirements.txt    # Backend dependencies
│   ├── test_server.py      # Script to run the backend server
│   └── test_finops_expert.py  # Script to test the FinOps Expert module
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── FinOpsExpert.tsx  # React component for FinOps Expert UI
│   │   └── ...
│   ├── package.json        # Frontend dependencies
│   └── vite.config.ts      # Vite configuration
├── start-app.bat           # Start both frontend and backend
└── test-finops-expert.bat  # Test FinOps Expert module directly
```

## Setup

1. Make sure you have Node.js and Python installed.
2. Create a `.env` file in the backend directory with your Azure credentials:
   ```
   PROJECT_CONNECTION_STRING=your-connection-string
   EMBEDDING_MODEL_DEPLOYMENT_NAME=your-model-name
   BING_CONNECTION_NAME=your-bing-name
   BING_SEARCH_KEY=your-bing-key
   AZURE_INFERENCE_ENDPOINT=your-endpoint
   AZURE_INFERENCE_KEY=your-key
   ```
3. Install backend dependencies:
   ```
   cd finopshubs-ui/backend
   pip install -r requirements.txt
   ```
4. Install frontend dependencies:
   ```
   cd finopshubs-ui/frontend
   npm install
   ```

## Running the Application

### Option 1: Using the Batch File

1. Run the `start-app.bat` file:
   ```
   finopshubs-ui\start-app.bat
   ```

### Option 2: Manual Start

1. Start the backend:
   ```
   cd finopshubs-ui/backend
   python test_server.py
   ```

2. In a new terminal, start the frontend:
   ```
   cd finopshubs-ui/frontend
   npm run dev
   ```

## Testing

### Testing the Complete API

Run the API test script:
```
cd finopshubs-ui
python test-api.py
```

### Testing the FinOps Expert Module Directly

Run the FinOps Expert test script:
```
cd finopshubs-ui
test-finops-expert.bat
```
Or manually:
```
cd finopshubs-ui/backend
python test_finops_expert.py
```

## Troubleshooting

1. **Missing Module Error**: Make sure the `finops_expert_with_bing_grounding.py` file is in the correct location (backend directory).

2. **API Connection Error**: Ensure the backend server is running on port 8000.

3. **Bing Connection Error**: Check your `.env` file to make sure your Azure credentials are correct.

4. **Frontend Not Loading**: Make sure you've installed all frontend dependencies with `npm install`.

5. **CORS Error**: If you see CORS errors in the browser console, make sure the backend CORS configuration includes your frontend URL.

## Features

- Ask questions about Microsoft's FinOps toolkit
- Search for the latest information using Bing grounding
- View conversation history with the FinOps Expert
- Test the Bing connection to ensure it's working properly

## Environment Variables

### Backend

- `PORT`: The port on which the backend server will run (default: 8000)

### Frontend

- `VITE_API_URL`: The URL of the backend API (default: http://localhost:8000)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Microsoft FinOps Toolkit
- Azure AI Studio 