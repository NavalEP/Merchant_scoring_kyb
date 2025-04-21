# KYB Merchant Scoring Frontend

## Environment Variables

For the application to work correctly, you need to set up the following environment variables:

### Development

Create a `.env` file in the root directory with:

```
VITE_API_BASE_URL=http://localhost:8000
```

### Production

When deploying to Netlify, add the following environment variable in the Netlify dashboard:

- `VITE_API_BASE_URL`: Your production API URL (e.g., https://your-backend-api.com)

## Deployment to Netlify

### Via GitHub

1. Push your code to GitHub
2. Go to Netlify Dashboard and click "New site from Git"
3. Select GitHub and choose your repository
4. Configure build settings:
   - Base directory: `Frontend_kyb`
   - Build command: `npm run build`
   - Publish directory: `dist`
5. Add environment variables:
   - Key: `VITE_API_BASE_URL`
   - Value: Your backend API URL
6. Click "Deploy site"

The application is already configured with the proper `netlify.toml` file and will redirect all routes to support React Router. 