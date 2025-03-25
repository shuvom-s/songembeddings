# Deploying to Netlify

This guide will walk you through the process of deploying your Song Lyrics Embedding Visualization to Netlify.

## Preparation

1. **Prepare your data**
   
   Before deploying, make sure `data.json` is generated and placed in the `web/` directory:
   ```bash
   python src/prepare_data.py
   ```

2. **Use placeholder lyrics**
   
   To ensure no copyright issues, switch to placeholder lyrics:
   ```bash
   python src/lyrics_manager.py use-placeholder
   ```

3. **Check your .gitignore**
   
   Make sure `.gitignore` is properly set up to exclude large data files and real lyrics.

## Deployment Steps

### Option 1: Deploy with Git

1. **Create a Git repository** (if you haven't already)
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Netlify deployment"
   ```

2. **Push to GitHub** (or GitLab/Bitbucket)
   ```bash
   # Create a new repository on GitHub first
   git remote add origin https://github.com/yourusername/your-repo-name.git
   git push -u origin main
   ```

3. **Connect to Netlify**
   - Log in to Netlify (https://app.netlify.com/)
   - Click "New site from Git"
   - Choose your Git provider (GitHub/GitLab/Bitbucket)
   - Select your repository
   - In the build settings:
     - Build command: leave empty (pre-built)
     - Publish directory: `web/`
   - Click "Deploy site"

### Option 2: Deploy with Netlify CLI

1. **Install Netlify CLI**
   ```bash
   npm install netlify-cli -g
   ```

2. **Login to Netlify**
   ```bash
   netlify login
   ```

3. **Initialize and deploy**
   ```bash
   netlify init
   # Follow the prompts to create a new site or connect to an existing one
   netlify deploy --prod
   # When asked for the publish directory, enter: web/
   ```

### Option 3: Drag and Drop Deployment

1. **Log in to Netlify** (https://app.netlify.com/)

2. **Drag and drop your `web/` folder** to the Netlify dashboard

## Post-Deployment

After deployment, Netlify will give you a URL like `https://your-site-name.netlify.app`. You can customize this in the Netlify dashboard:

1. Go to "Site settings"
2. Under "Site details", click "Change site name"

## Custom Domain (Optional)

To use a custom domain:

1. Go to "Domain settings" in the Netlify dashboard
2. Click "Add custom domain"
3. Follow the instructions to set up DNS records

## Troubleshooting

### Issue: Missing data.json
If your visualization doesn't load data, check if `data.json` is in your repository. It might be excluded by `.gitignore`.

**Solution**: Make sure your `web/data.json` file is not gitignored by adding a specific exception rule in `.gitignore`:
```
!web/data.json
```

### Issue: CORS errors
If you see CORS errors in the console, check your Content Security Policy.

**Solution**: Update the CSP in `netlify.toml` to include any external domains your app needs to access.

### Issue: Placeholder lyrics not showing
If you're seeing "No lyrics available" in your deployed version, make sure you've properly generated placeholder lyrics.

**Solution**: Run the lyrics manager again:
```bash
python src/lyrics_manager.py use-placeholder
python src/prepare_data.py
```

## Best Practices

1. **Always test locally** before deploying:
   ```bash
   python web/server.py
   ```

2. **Use "Deploy Preview"** in Netlify to test changes before merging to your main branch.

3. **Set environment variables** in Netlify dashboard if needed (for API keys, etc.).

4. **Enable HTTPS** (automatic with Netlify).

5. **Set up continuous deployment** for automatic updates when you push changes.

## Resources

- [Netlify Documentation](https://docs.netlify.com/)
- [Netlify CLI Documentation](https://cli.netlify.com/)
- [Netlify Forms](https://docs.netlify.com/forms/setup/) (if you want to add contact forms)
- [Netlify Functions](https://docs.netlify.com/functions/overview/) (if you need serverless functions) 