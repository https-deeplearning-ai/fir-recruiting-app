# Heroku Deployment Guide

This guide will walk you through deploying your LinkedIn Assessor app to Heroku.

## Prerequisites

1. A Heroku account (sign up at https://heroku.com)
2. Heroku CLI installed (https://devcenter.heroku.com/articles/heroku-cli)
3. Git installed
4. Your API keys ready:
   - Anthropic API Key
   - CoreSignal API Key
   - Supabase URL and Key

## Step 1: Install Heroku CLI

If you haven't already, install the Heroku CLI:

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Or download from: https://devcenter.heroku.com/articles/heroku-cli
```

## Step 2: Login to Heroku

```bash
heroku login
```

This will open your browser to complete the login process.

## Step 3: Create a Heroku App

Navigate to your project directory and create a new Heroku app:

```bash
cd /Users/yilingzhao/Desktop/linkedin-assessor
heroku create your-app-name
```

Replace `your-app-name` with your desired app name (must be unique across Heroku). If you omit the name, Heroku will generate one for you.

## Step 4: Set Environment Variables

Set all required environment variables on Heroku:

```bash
# Anthropic API Key
heroku config:set ANTHROPIC_API_KEY=your_anthropic_api_key_here

# CoreSignal API Key
heroku config:set CORESIGNAL_API_KEY=your_coresignal_api_key_here

# Supabase Configuration
heroku config:set SUPABASE_URL=your_supabase_url_here
heroku config:set SUPABASE_KEY=your_supabase_anon_key_here
```

To verify your environment variables are set:

```bash
heroku config
```

## Step 5: Initialize Git (if not already done)

If your project isn't already a git repository:

```bash
git init
git add .
git commit -m "Initial commit for Heroku deployment"
```

If you already have a git repository, make sure all changes are committed:

```bash
git add .
git commit -m "Prepare for Heroku deployment"
```

## Step 6: Deploy to Heroku

Push your code to Heroku:

```bash
git push heroku main
```

If your default branch is `master` instead of `main`:

```bash
git push heroku master
```

## Step 7: Scale Your App

Make sure at least one web dyno is running:

```bash
heroku ps:scale web=1
```

## Step 8: Open Your App

```bash
heroku open
```

This will open your deployed app in your browser!

## Troubleshooting

### View Logs

If something goes wrong, check the logs:

```bash
heroku logs --tail
```

### Common Issues

1. **Build fails**: Check that all dependencies in `requirements.txt` are correct
2. **App crashes on startup**: Check environment variables are set correctly with `heroku config`
3. **Timeout errors**: The free Heroku dyno sleeps after 30 minutes of inactivity. First request may be slow.
4. **API rate limits**: Consider upgrading your Anthropic/CoreSignal API plans if you hit rate limits

### Restart Your App

If needed, restart your Heroku app:

```bash
heroku restart
```

### Check App Status

```bash
heroku ps
```

## Updating Your App

When you make changes to your code:

1. Commit your changes:
   ```bash
   git add .
   git commit -m "Your commit message"
   ```

2. Push to Heroku:
   ```bash
   git push heroku main
   ```

## Monitoring and Maintenance

### View App Info
```bash
heroku info
```

### View App Configuration
```bash
heroku config
```

### Update Environment Variables
```bash
heroku config:set VARIABLE_NAME=new_value
```

## Cost Considerations

- Heroku free tier includes 550-1000 free dyno hours per month
- App will sleep after 30 minutes of inactivity
- Consider upgrading to a paid plan for:
  - No sleep
  - Better performance
  - Custom domains
  - More dyno hours

## Additional Resources

- Heroku Python Documentation: https://devcenter.heroku.com/categories/python-support
- Heroku CLI Commands: https://devcenter.heroku.com/articles/heroku-cli-commands
- Heroku Pricing: https://www.heroku.com/pricing

## Security Notes

- Never commit API keys or `.env` files to git
- Keep your API keys secure
- Rotate keys periodically
- Monitor your API usage to prevent unexpected charges

